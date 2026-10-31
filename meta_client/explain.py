"""Result explanation layer (T28): Spark turns a comparison or audit result
into a user-facing Traditional Chinese explanation.

The model only rephrases numbers the deterministic tools produced: every
explanation passes backend.output_check.check_model_text() before it is
returned, plus a T28-specific ban on real-vs-generated language. Anything
that fails is retried at most MAX_RETRIES times, then ModelOutputError.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from backend.output_check import check_model_text, extract_numbers

from . import client as _client
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import ModelOutputError
from .spark import _check_priced, _text_format, _usage_to_dict

EXPLAIN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"explanation": {"type": "string"}},
    "required": ["explanation"],
    "additionalProperties": False,
}

# Words that frame the result as real-vs-generated detection. Never allowed,
# on top of the causal-overclaim list in backend/output_check.py.
AUTHENTICITY_BANNED = (
    "真影片",
    "假影片",
    "假的",
    "真偽",
    "AI生成",
    "AI 生成",
    "AI影片",
    "AI 影片",
    "AI 偵測",
    "deepfake",
    "fake video",
    "real video",
    "ai-generated",
    "generated video",
)

# Bulky arrays that prose must never cite point-by-point; dropped from the
# prompt view (and therefore from the allowed numbers) before calling Spark.
_DROPPED_KEYS = ("curve", "overlay_px", "residuals", "points")

_PROMPTS = {
    "comparison": (
        "You explain a physics experiment result to a non-expert user in "
        "Traditional Chinese. Read this locked comparison between a saved "
        "prediction and a real trial, then write a short explanation: what "
        "was compared, whether the result is 一致, 不一致, or 無法判斷, and "
        "which checks or evidence support that. "
    ),
    "audit": (
        "You explain a video physics audit to a non-expert user in "
        "Traditional Chinese. Read this audit of one clip against its "
        "assumed motion model, then write a short explanation: what was "
        "checked, whether the motion is 一致, 不一致, or 無法判斷 relative to "
        "the assumed model, and which numbers or reasons support that. "
    ),
}

_RULES = (
    "Rules. Use only numbers that appear in the payload below, including "
    "numbers inside its reason sentences (such as thresholds); never invent, "
    "convert units, or add precision. Quote each number rounded to at most 2 "
    "decimal places (e.g. 1.71, not 1.705999). Never write frame rates, "
    "frame counts, or percentages you compute yourself. Say 與假設一致 or 目前無法"
    "區分 where appropriate; never claim proof or causes (no 證實, 真因, "
    "一定是, proves, confirms, must be). Never frame this as real-vs-"
    "generated video detection: do not write 真影片, 假影片, AI生成, or any "
    'equivalent. Return JSON only, matching the schema: exactly one key, "explanation".'
)

_PROMPTS_EN = {
    "comparison": (
        "You explain a physics experiment result to a non-expert judge in "
        "English. Read this locked comparison between a saved prediction "
        "and a real trial, then write a short explanation: what was "
        "compared, whether the result is consistent, inconsistent, or "
        "inconclusive, and which checks or evidence support that. "
    ),
    "audit": (
        "You explain a video physics audit to a non-expert judge in English. "
        "Read this audit of one clip against its assumed motion model, then "
        "write a short explanation: what was checked, whether the motion is "
        "consistent, inconsistent, or inconclusive relative to the assumed "
        "model, and which numbers or reasons support that. "
    ),
}

_RULES_EN = (
    "Rules. Use only numbers that appear in the payload below, including "
    "numbers inside its reason sentences (such as thresholds); never invent, "
    "convert units, or add precision. Quote each number rounded to at most 2 "
    "decimal places (e.g. 1.71, not 1.705999). Never write frame rates, "
    "frame counts, or percentages you compute yourself. Say consistent with the "
    "assumption or cannot yet distinguish where appropriate; never claim "
    "proof or causes (no proves, confirms, must be, caused by). Never frame "
    "this as real-vs-generated video detection: do not write real video, "
    "fake video, AI-generated, or any equivalent. Return JSON only, matching "
    'the schema: exactly one key, "explanation".'
)

# Extra guidance when the audit assumes a car driving past side-on (T187).
# The fitted acceleration and the tyre-grip screening limit both live in the
# payload (numbers + reason sentences), so the model may quote them; it must
# never frame the result as fake/real video.
_VEHICLE_RULES = (
    "This audit assumes a car driving past side-on. When the verdict is 不一致, "
    "state the fitted acceleration in g and compare it with the tyre-grip "
    "screening limit stated in the payload reasons, phrased as 加速度約 X g，"
    "超過一般輪胎抓地力上限，與正常路上行駛不一致, quoting both numbers from "
    "the payload. Never write 假的, AI生成, or 證實."
)

_VEHICLE_RULES_EN = (
    "This audit assumes a car driving past side-on. When the verdict is "
    "inconsistent, state the fitted acceleration in g and compare it with "
    "the tyre-grip screening limit stated in the payload reasons, quoting "
    "both numbers from the payload. Never write fake video, AI-generated, "
    "or any claim of proof."
)


def _summary_view(result: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ModelOutputError("result must be a mapping")
    return {k: v for k, v in result.items() if k not in _DROPPED_KEYS}


def _string_numbers(view: Mapping[str, Any]) -> list[float]:
    """Numbers inside the payload's own sentences (T115).

    Thresholds such as 8.34-11.28 live in reason strings, not numeric
    fields. The prompt allows quoting payload numbers, so the check must
    accept them too. Parsed deterministically by the program; the backend
    checker itself is untouched.
    """
    out: list[float] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            out.extend(value for _, value, _ in extract_numbers(node))
        elif isinstance(node, Mapping):
            for value in node.values():
                walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value)

    walk(view)
    return out


def _find_authenticity_words(text: str) -> list[str]:
    low = text.lower()
    return [w for w in AUTHENTICITY_BANNED if w.lower() in low]


def explain_result(
    result: Mapping[str, Any],
    *,
    kind: str = "comparison",
    lang: str = "zh",
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, str]:
    """Explain a comparison or audit result (T28 Chinese, T47 English).

    Returns {"explanation", "source"}. Raises ModelOutputError when the text does
    not pass the output checks after retries; raises ValueError for a bad
    kind or lang without calling the API.
    """
    if kind not in _PROMPTS:
        raise ValueError("kind must be 'comparison' or 'audit'")
    if lang not in ("zh", "en"):
        raise ValueError("lang must be 'zh' or 'en'")
    view = _summary_view(result)
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    lead, rules = (_PROMPTS[kind], _RULES) if lang == "zh" else (_PROMPTS_EN[kind], _RULES_EN)
    if kind == "audit" and view.get("assumed_model") == "vehicle":
        rules += _VEHICLE_RULES if lang == "zh" else _VEHICLE_RULES_EN
    prompt = lead + rules + "\nPayload:\n" + json.dumps(view, ensure_ascii=False, default=str)
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=prompt,
                text=_text_format("explanation", EXPLAIN_SCHEMA),
                timeout=timeout,
            ),
            op="spark.explain_result",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.explain_result",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            data = json.loads(response.output_text or "")
            if not isinstance(data, dict) or not isinstance(
                data.get("explanation"), str
            ):
                raise ModelOutputError("explanation must be a JSON string field")
            text = data["explanation"].strip()
            if not text:
                raise ModelOutputError("explanation must be non-empty")
            checked = check_model_text(
                text, [view, {"payload_sentence_numbers": _string_numbers(view)}]
            )
            if not checked.ok:
                raise ModelOutputError("output check failed: " + "; ".join(checked.problems))
            bad_words = _find_authenticity_words(text)
            if bad_words:
                raise ModelOutputError(
                    "forbidden authenticity language: " + ", ".join(bad_words)
                )
            return {"explanation": text, "source": resolved}
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"explanation failed validation: {last_error}")
