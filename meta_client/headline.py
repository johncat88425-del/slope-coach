"""Physics headline (T67): Spark writes one memorable headline template for
an audit result, e.g. "this ball falls like it is on the moon".

Spark only writes slot positions ({g_vs_earth:2}, {nearest_body}); the
program fills them from the deterministic AuditOut numbers and the
physics-computed nearest body, then verifies the filled headline before
it may be displayed. No digits from the model, no authenticity language
(real/fake/AI video). Returns None instead of a headline whenever the
audit has no gravity numbers (e.g. insufficient_data, pendulum) or the
checks fail.
"""
from __future__ import annotations

import json
import re
from typing import Any

from backend.output_check import check_model_text, fill_numbers

from . import client as _client
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import ModelOutputError
from .explain import AUTHENTICITY_BANNED
from .spark import _check_priced, _text_format, _usage_to_dict

HEADLINE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"headline_template": {"type": "string"}},
    "required": ["headline_template"],
    "additionalProperties": False,
}

MAX_HEADLINE_CHARS = 200

_STRING_SLOT = re.compile(r"\{nearest_body(?::\d+)?\}")

HEADLINE_PROMPT = (
    "You write ONE memorable headline in Traditional Chinese for a video "
    "physics audit. The clip's apparent gravity is {g_vs_earth:2} times "
    "Earth's, closest to {nearest_body} among known bodies. Write the "
    "headline as a TEMPLATE: copy those two slots exactly as written "
    "(names and braces), never write any digits yourself. Example shape: "
    "這顆球落得像在{nearest_body}上：表觀重力只有地球的{g_vs_earth:2}倍. "
    "Rules. One sentence, under 200 characters, about how the motion "
    "compares to the model; never claim proof or causes (no 證實, 真因, "
    "一定是). Never write the characters 真 or 假 anywhere, and never "
    "write AI生成 or any equivalent: this is about motion matching a "
    "model, not about whether the video is real. Return JSON only, "
    'matching the schema: exactly one key, "headline_template".'
)


def rounded_number_sources(values: dict[str, float]) -> dict[str, float]:
    """Deterministic roundings of slot values, for the filled-text check.

    A filled headline shows e.g. 0.01 for a raw 0.0122; the rounded forms
    are honest allowlist entries so display rounding never fails the
    number check.
    """
    out: dict[str, float] = {}
    for key, value in values.items():
        for decimals in range(5):
            out[f"{key}_r{decimals}"] = round(value, decimals)
    return out


def _validate_headline(raw: Any, audit: dict[str, Any]) -> str:
    if not isinstance(raw, dict):
        raise ModelOutputError("headline must be a JSON object")
    template = raw.get("headline_template")
    if not isinstance(template, str) or not template.strip():
        raise ModelOutputError("headline_template must be a non-empty string")
    template = template.strip()
    if len(template) > MAX_HEADLINE_CHARS:
        raise ModelOutputError("headline_template must be under 200 characters")
    numbers = audit.get("numbers") or {}
    g_vs_earth = numbers.get("g_vs_earth")
    body = audit.get("nearest_body")
    if not isinstance(g_vs_earth, (int, float)) or not body:
        raise ModelOutputError("audit has no gravity numbers for a headline")
    if not isinstance(body, str):
        raise ModelOutputError("nearest_body must be a string")
    if _STRING_SLOT.search(template) is None:
        raise ModelOutputError("headline must use the {nearest_body} slot")
    with_body = _STRING_SLOT.sub(body, template)
    filled, fill_check = fill_numbers(with_body, {"g_vs_earth": g_vs_earth})
    if not fill_check.ok:
        raise ModelOutputError("headline slots failed: " + "; ".join(fill_check.problems))
    assert filled is not None
    bad_words = [w for w in AUTHENTICITY_BANNED if w in filled]
    if "真" in filled or "假" in filled:
        bad_words += [c for c in ("真", "假") if c in filled]
    if bad_words:
        raise ModelOutputError("forbidden authenticity language: " + ", ".join(bad_words))
    sources: list[dict[str, Any]] = [
        audit,
        {"g_vs_earth": g_vs_earth},
        rounded_number_sources({"g_vs_earth": g_vs_earth}),
    ]
    text_check = check_model_text(filled, sources)
    if not text_check.ok:
        raise ModelOutputError("headline failed checks: " + "; ".join(text_check.problems))
    return filled


def write_headline(
    audit: dict[str, Any],
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> str | None:
    """Write one headline template for an audit, filled and verified.

    Returns the filled headline, or None when the audit has no gravity
    numbers (insufficient_data, pendulum) or no valid headline passes
    after retries (caller must not display anything then).
    """
    numbers = audit.get("numbers") or {}
    g_vs_earth = numbers.get("g_vs_earth")
    if audit.get("verdict") == "insufficient_data":
        return None
    if not isinstance(g_vs_earth, (int, float)) or not audit.get("nearest_body"):
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
                input=[{
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": HEADLINE_PROMPT}],
                }],
                text=_text_format("headline", HEADLINE_SCHEMA),
                timeout=timeout,
            ),
            op="spark.write_headline",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.write_headline",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            return _validate_headline(json.loads(response.output_text or ""), audit)
        except (json.JSONDecodeError, ModelOutputError, ValueError):
            continue
    return None
