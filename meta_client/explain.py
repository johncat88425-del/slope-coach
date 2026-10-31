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

from backend.output_check import check_model_text, extract_numbers, fill_numbers

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


WHAT_WOULD_FIT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"sentence_template": {"type": "string"}},
    "required": ["sentence_template"],
    "additionalProperties": False,
}

MAX_FIT_CHARS = 200

_FIT_PROMPTS = {
    "zh": (
        "一支影片的自由飛行稽核結果是不一致：球掉得太慢或太快，和地球重力對不上。"
        "程式已算出兩個反事實數字：如果影片其實被放慢 {implied_time_factor} 倍就會符合，"
        "或如果球其實有 {implied_object_size_m} 公尺寬就會符合。請寫一句話當樣板："
        "照抄至少一個槽位（含大括號和名稱），自己不准寫任何數字。例如：如果這支影片其實放慢了 "
        "{implied_time_factor} 倍，或球其實有 {implied_object_size_m} 公尺寬，才會和地球重力一致。"
        "規則：一句話，不超過 200 個字；不准寫「所以是假的」或任何因果字眼（不准證實、真因、"
        "一定是），不准寫真假影片或 AI 生成。只回傳 JSON，恰好一個鍵 \"sentence_template\"。"
    ),
    "en": (
        "A clip's free-flight audit came back inconsistent: the ball falls too "
        "slowly or too fast to match Earth gravity. The program computed two "
        "counterfactual numbers: the slowdown factor that would fit "
        "({implied_time_factor}) and the ball width that would fit "
        "({implied_object_size_m} metres). Write one sentence as a TEMPLATE: "
        "copy at least one slot exactly as written (braces and name), never "
        "write any digits yourself. Example shape: This would match Earth "
        "gravity if the clip were slowed by {implied_time_factor}x, or the "
        "ball were {implied_object_size_m} metres wide. Rules. One sentence, "
        "under 200 characters; never claim proof or causes, never frame this "
        "as real-vs-fake video. Return JSON only with exactly one key, "
        "\"sentence_template\"."
    ),
}


def _validate_fit_template(raw: Any, slots: dict[str, float]) -> str:
    if not isinstance(raw, dict):
        raise ModelOutputError("fit sentence must be a JSON object")
    template = raw.get("sentence_template")
    if not isinstance(template, str) or not template.strip():
        raise ModelOutputError("sentence_template must be a non-empty string")
    template = template.strip()
    if len(template) > MAX_FIT_CHARS:
        raise ModelOutputError("sentence_template must be under 200 characters")
    if "{implied_time_factor" not in template and "{implied_object_size_m" not in template:
        raise ModelOutputError("fit sentence must use an implied_* slot")
    filled, fill_check = fill_numbers(template, slots)
    if not fill_check.ok:
        raise ModelOutputError("fit slots failed: " + "; ".join(fill_check.problems))
    assert filled is not None
    text_check = check_model_text(filled, [dict(slots)])
    if not text_check.ok:
        raise ModelOutputError("fit sentence failed checks: " + "; ".join(text_check.problems))
    bad = _find_authenticity_words(filled)
    if bad:
        raise ModelOutputError("forbidden authenticity language: " + ", ".join(bad))
    return filled


def what_would_fit(
    audit: Mapping[str, Any],
    lang: str = "zh",
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, str] | None:
    """One counterfactual sentence for an inconsistent free flight (T205).

    Spark writes the sentence shape; the program fills {implied_time_factor}
    and {implied_object_size_m} from the audit numbers and verifies the
    result. Returns {"sentence", "source"}, or None when the audit is not an
    inconsistent free flight, the numbers are missing, or no valid sentence
    passes after retries. Raises ValueError for a bad lang without calling
    the API.
    """
    if lang not in _FIT_PROMPTS:
        raise ValueError("lang must be 'zh' or 'en'")
    if not isinstance(audit, Mapping):
        raise ModelOutputError("audit must be a mapping")
    if audit.get("verdict") != "inconsistent":
        return None
    if audit.get("assumed_model") != "free_flight":
        return None
    numbers = audit.get("numbers") or {}
    slots = {k: numbers[k] for k in ("implied_time_factor", "implied_object_size_m")
             if isinstance(numbers.get(k), (int, float))}
    if len(slots) < 2:
        return None
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=_FIT_PROMPTS[lang],
                text=_text_format("what_would_fit", WHAT_WOULD_FIT_SCHEMA),
                timeout=timeout,
            ),
            op="spark.what_would_fit",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.what_would_fit",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            filled = _validate_fit_template(
                json.loads(response.output_text or ""), slots)
            return {"sentence": filled, "source": resolved}
        except (json.JSONDecodeError, ModelOutputError, ValueError):
            continue
    return None


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
