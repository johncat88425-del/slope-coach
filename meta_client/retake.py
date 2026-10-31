"""Reshoot tips (T204): when an audit is insufficient_data, Spark reads the
reasons and writes 1-3 concrete tips for filming again.

The model only rephrases what the deterministic refusal already says: every
tip passes backend.output_check.check_model_text() with the reasons' own
numbers as the only allowed numbers, plus the authenticity ban. Anything
that fails is retried at most MAX_RETRIES times, then None (the frontend
falls back to its fixed tips).
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
from .explain import AUTHENTICITY_BANNED
from .spark import _check_priced, _text_format, _usage_to_dict

RETAKE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"tips": {"type": "array", "items": {"type": "string"},
                            "minItems": 1, "maxItems": 3}},
    "required": ["tips"],
    "additionalProperties": False,
}

MAX_TIP_CHARS = 80

_PROMPTS = {
    "zh": (
        "一位使用者的影片物理稽核結果是無法判斷，原因如下。請寫 1 到 3 條具體的重拍建議，"
        "告訴使用者下次怎麼拍才量得到（例如球往鏡頭飛：請站到球飛行路線的正側面）。每條不超過 "
        "80 個字，只能用原因裡出現過的數字，不准自己發明數字。不要寫證明或因果（不准證實、真因、"
        "一定是），不要寫真假影片或 AI 生成。只回傳 JSON，恰好一個鍵 \"tips\"。"
    ),
    "en": (
        "A user's video physics audit came back inconclusive for the reasons "
        "below. Write 1 to 3 concrete reshoot tips telling them how to film "
        "next time so the motion can be measured (e.g. the ball flew toward "
        "the camera: stand exactly side-on to its flight path). Each tip "
        "under 80 characters; use only numbers that appear in the reasons, "
        "never invent any. No proof or cause claims, no real/fake video "
        "framing. Return JSON only with exactly one key, \"tips\"."
    ),
}


def _reason_numbers(reasons: list[str]) -> list[float]:
    return [value for r in reasons for _, value, _ in extract_numbers(r)]


def _validate_tips(data: Any, reasons: list[str]) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("tips"), list):
        raise ModelOutputError("retake tips must be a JSON object with tips[]")
    tips = data["tips"]
    if not 1 <= len(tips) <= 3:
        raise ModelOutputError("retake tips need 1 to 3 entries")
    allowed = [{"reason_numbers": _reason_numbers(reasons)}]
    cleaned = []
    for tip in tips:
        if not isinstance(tip, str) or not tip.strip():
            raise ModelOutputError("each tip must be a non-empty string")
        tip = tip.strip()
        if len(tip) > MAX_TIP_CHARS:
            raise ModelOutputError("each tip must be under 80 characters")
        checked = check_model_text(tip, allowed)
        if not checked.ok:
            raise ModelOutputError("tip failed checks: " + "; ".join(checked.problems))
        bad = [w for w in AUTHENTICITY_BANNED if w.lower() in tip.lower()]
        if bad:
            raise ModelOutputError("forbidden authenticity language: " + ", ".join(bad))
        cleaned.append(tip)
    return cleaned


def write_retake_tips(
    audit: Mapping[str, Any],
    lang: str = "zh",
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any] | None:
    """Write 1-3 reshoot tips for a refused audit (T204).

    Returns {"tips", "source"}, or None when the audit is not refused or no
    valid tips pass after retries. Raises ValueError for a bad lang without
    calling the API.
    """
    if lang not in _PROMPTS:
        raise ValueError("lang must be 'zh' or 'en'")
    if not isinstance(audit, Mapping):
        raise ModelOutputError("audit must be a mapping")
    if audit.get("verdict") != "insufficient_data":
        return None
    reasons = audit.get("reasons") or []
    if not reasons:
        return None
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    payload = {"assumed_model": audit.get("assumed_model"), "reasons": list(reasons)}
    prompt = _PROMPTS[lang] + "\nReasons:\n" + json.dumps(payload, ensure_ascii=False)
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=prompt,
                text=_text_format("retake_tips", RETAKE_SCHEMA),
                timeout=timeout,
            ),
            op="spark.write_retake_tips",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.write_retake_tips",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            tips = _validate_tips(json.loads(response.output_text or ""), list(reasons))
            return {"tips": tips, "source": resolved}
        except (json.JSONDecodeError, ModelOutputError, ValueError):
            continue
    return None
