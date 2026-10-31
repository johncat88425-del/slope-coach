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

# physics returns English body names; the Chinese headline reads better
# with Chinese names. Display-only mapping inside this module.
BODY_ZH = {
    "Pluto": "冥王星",
    "Moon": "月球",
    "Mars": "火星",
    "Earth": "地球",
    "Jupiter": "木星",
}

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

HEADLINE_PROMPT_EN = (
    "You write ONE memorable headline in English for a video physics "
    "audit. The clip's apparent gravity is {g_vs_earth:2} times Earth's, "
    "closest to {nearest_body} among known bodies. Write the headline as "
    "a TEMPLATE: copy those two slots exactly as written (names and "
    "braces), never write any digits yourself. Example shape: This ball "
    "falls as if on {nearest_body}, at {g_vs_earth:2} times Earth's "
    "gravity. Rules. One sentence, under 200 characters, about how the "
    "motion compares to the model; never claim proof or causes (no "
    "proves, confirms, must be). Never write real video, fake video, "
    "AI-generated, or any equivalent: this is about motion matching a "
    "model, not about whether the video is real. Return JSON only, "
    'matching the schema: exactly one key, "headline_template".'
)

VEHICLE_PROMPT = (
    "You write ONE memorable headline in Traditional Chinese for a video "
    "physics audit of a car driving past side-on. The car reached "
    "{speed_km_h:0} km/h with acceleration {accel_g:1} g. Write the "
    "headline as a TEMPLATE: copy those slots exactly as written (names "
    "and braces), never write any digits yourself, and use no other "
    "{...} slots. Example shape: 這台車在{accel_g:1}g下煞車，比賽車還猛. "
    "Rules. One sentence, under 200 characters, about how the car moved; "
    "never claim proof or causes (no 證實, 真因, 一定是). Never write the "
    "characters 真 or 假 anywhere, and never write AI生成 or any "
    "equivalent: this is about motion matching a model, not about whether "
    "the video is real. Return JSON only, matching the schema: exactly "
    'one key, "headline_template".'
)

VEHICLE_PROMPT_EN = (
    "You write ONE memorable headline in English for a video physics "
    "audit of a car driving past side-on. The car reached {speed_km_h:0} "
    "km/h with acceleration {accel_g:1} g. Write the headline as a "
    "TEMPLATE: copy those slots exactly as written (names and braces), "
    "never write any digits yourself, and use no other {...} slots. "
    "Example shape: This car braked at {accel_g:1} g, harder than a race "
    "car. Rules. One sentence, under 200 characters, about how the car "
    "moved; never claim proof or causes (no proves, confirms, must be). "
    "Never write real video, fake video, AI-generated, or any equivalent: "
    "this is about motion matching a model, not about whether the video "
    "is real. Return JSON only, matching the schema: exactly one key, "
    '"headline_template".'
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


def _template_text(raw: Any) -> str:
    if not isinstance(raw, dict):
        raise ModelOutputError("headline must be a JSON object")
    template = raw.get("headline_template")
    if not isinstance(template, str) or not template.strip():
        raise ModelOutputError("headline_template must be a non-empty string")
    template = template.strip()
    if len(template) > MAX_HEADLINE_CHARS:
        raise ModelOutputError("headline_template must be under 200 characters")
    return template


def _check_filled(filled: str, audit: dict[str, Any], slots: dict[str, float]) -> str:
    bad_words = [w for w in AUTHENTICITY_BANNED if w in filled]
    if "真" in filled or "假" in filled:
        bad_words += [c for c in ("真", "假") if c in filled]
    if bad_words:
        raise ModelOutputError("forbidden authenticity language: " + ", ".join(bad_words))
    sources: list[dict[str, Any]] = [audit, dict(slots), rounded_number_sources(slots)]
    text_check = check_model_text(filled, sources)
    if not text_check.ok:
        raise ModelOutputError("headline failed checks: " + "; ".join(text_check.problems))
    return filled


def _validate_headline(raw: Any, audit: dict[str, Any], *, lang: str = "zh") -> str:
    template = _template_text(raw)
    numbers = audit.get("numbers") or {}
    g_vs_earth = numbers.get("g_vs_earth")
    body = audit.get("nearest_body")
    if not isinstance(g_vs_earth, (int, float)) or not body:
        raise ModelOutputError("audit has no gravity numbers for a headline")
    if not isinstance(body, str):
        raise ModelOutputError("nearest_body must be a string")
    if _STRING_SLOT.search(template) is None:
        raise ModelOutputError("headline must use the {nearest_body} slot")
    name = BODY_ZH.get(body, body) if lang == "zh" else body
    with_body = _STRING_SLOT.sub(name, template)
    filled, fill_check = fill_numbers(with_body, {"g_vs_earth": g_vs_earth})
    if not fill_check.ok:
        raise ModelOutputError("headline slots failed: " + "; ".join(fill_check.problems))
    assert filled is not None
    return _check_filled(filled, audit, {"g_vs_earth": g_vs_earth})


def _validate_vehicle_headline(raw: Any, audit: dict[str, Any], *, lang: str = "zh") -> str:
    """Vehicle headlines (T176): only {speed_km_h} and {accel_g} slots."""
    _ = lang  # same slot rules in both languages; the prompt sets the wording
    template = _template_text(raw)
    numbers = audit.get("numbers") or {}
    slots = {k: numbers[k] for k in ("speed_km_h", "accel_g")
             if isinstance(numbers.get(k), (int, float))}
    if not slots:
        raise ModelOutputError("audit has no vehicle numbers for a headline")
    if "{speed_km_h" not in template and "{accel_g" not in template:
        raise ModelOutputError("vehicle headline must use a {speed_km_h} or {accel_g} slot")
    filled, fill_check = fill_numbers(template, slots)
    if not fill_check.ok:
        raise ModelOutputError("headline slots failed: " + "; ".join(fill_check.problems))
    assert filled is not None
    return _check_filled(filled, audit, slots)


def write_headline(
    audit: dict[str, Any],
    *,
    lang: str = "zh",
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, str] | None:
    """Write one headline template for an audit, filled and verified.

    Returns {"headline", "source"}, or None when the audit has no usable
    numbers (insufficient_data, pendulum, vehicle without speed) or no
    valid headline passes after retries (caller must not display
    anything then). Vehicle audits use the speed/accel slots (T176).
    """
    if lang not in ("zh", "en"):
        raise ValueError("lang must be 'zh' or 'en'")
    numbers = audit.get("numbers") or {}
    g_vs_earth = numbers.get("g_vs_earth")
    if audit.get("verdict") == "insufficient_data":
        return None
    vehicle = (
        audit.get("assumed_model") == "vehicle"
        and isinstance(numbers.get("speed_km_h"), (int, float))
    )
    if vehicle:
        prompt = VEHICLE_PROMPT if lang == "zh" else VEHICLE_PROMPT_EN
        validate = _validate_vehicle_headline
    else:
        if not isinstance(g_vs_earth, (int, float)) or not audit.get("nearest_body"):
            return None
        prompt = HEADLINE_PROMPT if lang == "zh" else HEADLINE_PROMPT_EN
        validate = _validate_headline
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
                    "content": [{"type": "input_text", "text": prompt}],
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
            filled = validate(
                json.loads(response.output_text or ""), audit, lang=lang)
            return {"headline": filled, "source": resolved}
        except (json.JSONDecodeError, ModelOutputError, ValueError):
            continue
    return None
