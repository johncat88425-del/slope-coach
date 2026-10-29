"""Next-check selection agent (T11): Spark picks one verification from the
evidence candidates using tool calls.

The agent may only choose from the candidates physics produced
(`physics/diagnose.py` via `ComparisonOut.evidence`); it cannot invent new
checks. Every number in its rationale must come from tool outputs
(`backend/output_check.py`), and with no candidates it answers
目前證據不足 without calling the API at all.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from backend.interventions import CATALOG
from backend.output_check import check_choice, check_model_text, fill_numbers
from physics.errors import PhysicsInputError
from physics.experiments.freefall import check_bounces, check_flight, fit_flight
from physics.persistence import persistence_events
from physics.tracking import Detection

from . import client as _client
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import ModelOutputError
from .spark import _check_priced, _usage_to_dict

MAX_AGENT_STEPS = 4

INSUFFICIENT = "目前證據不足"

SYSTEM = (
    "You help a user pick the next verification for a slope experiment. "
    "First call get_evidence to read the candidate checks physics produced. "
    "Then call propose_check exactly once with your choice and a short "
    "Traditional Chinese rationale. Rules. Choose only a candidate from "
    "get_evidence; never invent another check. Base the rationale only on "
    "the evidence findings and their numbers; never invent, round, or "
    "convert numbers. Say 與假設一致 or 目前無法區分 where appropriate; "
    "never claim proof or causes (no 證實, 真因, 一定是, proves, confirms, "
    "must be). If the evidence cannot support any candidate, propose "
    "nothing and answer 目前證據不足."
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_evidence",
        "description": "Read the candidate next checks with their findings and numbers.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function",
        "name": "propose_check",
        "description": "Propose one candidate check with a rationale. Call exactly once.",
        "parameters": {
            "type": "object",
            "properties": {
                "check_type": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": ["check_type", "rationale"],
            "additionalProperties": False,
        },
    },
]


def _item_to_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return {
        "type": getattr(item, "type", None),
        "name": getattr(item, "name", None),
        "arguments": getattr(item, "arguments", None),
        "call_id": getattr(item, "call_id", None),
    }


def _function_calls(response: Any) -> list[dict[str, Any]]:
    calls = []
    for item in getattr(response, "output", None) or []:
        data = _item_to_dict(item)
        if data.get("type") == "function_call":
            calls.append(data)
    return calls


def _evidence_view(comparison: Mapping[str, Any]) -> list[dict[str, Any]]:
    evidence = comparison.get("evidence") or []
    if not isinstance(evidence, list):
        raise ModelOutputError("comparison evidence must be a list")
    view = []
    for item in evidence:
        if not isinstance(item, Mapping):
            raise ModelOutputError("comparison evidence items must be mappings")
        candidate = item.get("candidate")
        if candidate not in CATALOG:
            raise ModelOutputError(f"unknown evidence candidate {candidate!r}")
        view.append(
            {
                "candidate": candidate,
                "finding": item.get("finding"),
                "numbers": item.get("numbers") or {},
                "cannot_distinguish": item.get("cannot_distinguish"),
                "catalog": CATALOG[candidate],
            }
        )
    return view


def choose_intervention(
    comparison: Mapping[str, Any],
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Pick one next check from the evidence candidates.

    Returns {"choice": check_type | None, "rationale": str}. With no
    candidates, returns insufficient-evidence without an API call.
    """
    if not isinstance(comparison, Mapping):
        raise ModelOutputError("comparison must be a mapping")
    evidence = _evidence_view(comparison)
    if not evidence:
        return {"choice": None, "rationale": INSUFFICIENT}
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    candidates = [e["candidate"] for e in evidence]

    def run_once() -> dict[str, Any]:
        inputs: list[Any] = [
            {"type": "message", "role": "user", "content": [{"type": "input_text", "text": SYSTEM}]}
        ]
        totals = {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0}
        try:
            for _ in range(MAX_AGENT_STEPS):
                response = call_with_retry(
                    lambda: sdk.responses.create(
                        model=resolved, input=inputs, tools=TOOLS, timeout=timeout
                    ),
                    op="spark.choose_intervention",
                )
                usage = _usage_to_dict(getattr(response, "usage", None))
                for key in totals:
                    totals[key] += usage[key]
                calls = _function_calls(response)
                raw_output = getattr(response, "output", None) or []
                inputs.extend(_item_to_dict(i) for i in raw_output)
                if not calls:
                    raise ModelOutputError("agent stopped without proposing a check")
                for call in calls:
                    name = call.get("name")
                    args = json.loads(call.get("arguments") or "{}")
                    if name == "get_evidence":
                        inputs.append(
                            {
                                "type": "function_call_output",
                                "call_id": call.get("call_id"),
                                "output": json.dumps(evidence, ensure_ascii=False),
                            }
                        )
                    elif name == "propose_check":
                        choice = args.get("check_type")
                        rationale = args.get("rationale")
                        if not isinstance(rationale, str) or not rationale.strip():
                            raise ModelOutputError("rationale must be a non-empty string")
                        if choice is None:
                            raise ModelOutputError("propose_check requires check_type")
                        choice_check = check_choice(choice, candidates)
                        if not choice_check.ok:
                            raise ModelOutputError("; ".join(choice_check.problems))
                        text_check = check_model_text(rationale, [comparison])
                        if not text_check.ok:
                            raise ModelOutputError(
                                "output check failed: " + "; ".join(text_check.problems)
                            )
                        return {"choice": choice, "rationale": rationale.strip()}
                    else:
                        raise ModelOutputError(f"unknown tool call {name!r}")
            raise ModelOutputError("agent exceeded the step limit without deciding")
        finally:
            tracker.record(
                resolved,
                "spark.choose_intervention",
                input_tokens=totals["input_tokens"],
                cached_tokens=totals["cached_tokens"],
                output_tokens=totals["output_tokens"],
            )

    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        try:
            return run_once()
        except (ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"agent failed validation: {last_error}")


AUDIT_CHECKS = ("free_flight", "bounce", "persistence")

AUDIT_SYSTEM = (
    "You plan a video physics audit. Call run_check with names from "
    "[free_flight, bounce, persistence] to see what each deterministic check "
    "says about the tracked motion, then call propose_plan exactly once with "
    "the checks worth keeping and a short Traditional Chinese rationale. "
    "Rules. Only propose checks from the fixed list; never invent another. "
    "Write the rationale as a TEMPLATE: never write digits yourself; cite "
    "numbers only as {check_key} slots exactly as named in the tool "
    "outputs, prefixed by the check name (for example "
    "{free_flight_g_apparent_m_s2:2} or {persistence_n_events}), with an "
    "optional :decimals suffix. The program fills the slots and rejects "
    "unknown ones. Say 與假設一致 or 目前無法區分 where appropriate; "
    "never claim proof or causes (no 證實, 真因, 一定是, proves, confirms, "
    "must be). Never frame this as real-vs-generated video detection."
)

AUDIT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "run_check",
        "description": "Run one deterministic check on the tracked motion.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "propose_plan",
        "description": ("Propose the final check list with a rationale TEMPLATE "
                        "(numbers only as {check_key} slots). Call exactly once."),
        "parameters": {
            "type": "object",
            "properties": {
                "selected": {"type": "array", "items": {"type": "string"}},
                "rationale_template": {"type": "string"},
            },
            "required": ["selected", "rationale_template"],
            "additionalProperties": False,
        },
    },
]


def _audit_points(audit: Mapping[str, Any]) -> list[tuple[float, float, float]]:
    points = audit.get("points")
    if not isinstance(points, list):
        raise ModelOutputError("audit points must be a list of [t, x, y]")
    out = []
    for item in points:
        if (
            not isinstance(item, (list, tuple))
            or len(item) != 3
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in item)
        ):
            raise ModelOutputError("audit points must be a list of [t, x, y]")
        out.append((float(item[0]), float(item[1]), float(item[2])))
    return out


def _finite_dict(values: dict[str, Any]) -> dict[str, float]:
    import math

    return {
        k: float(v)
        for k, v in values.items()
        if isinstance(v, (int, float))
        and not isinstance(v, bool)
        and v is not None
        and math.isfinite(float(v))
    }


def _run_check(name: str, audit: Mapping[str, Any]) -> dict[str, Any]:
    """Run one deterministic audit check; tool errors become outputs."""
    import statistics

    if name not in AUDIT_CHECKS:
        return {"check": name, "error": f"unknown check {name!r}; use {list(AUDIT_CHECKS)}"}
    pts = _audit_points(audit)
    sizes = [float(s) for s in (audit.get("sizes") or []) if isinstance(s, (int, float))]
    if name == "free_flight":
        try:
            fit = fit_flight(pts)
            size_px = statistics.median(sizes) if sizes else None
            osm = audit.get("object_size_m")
            m_per_px = (
                float(osm) / size_px
                if isinstance(osm, (int, float)) and size_px
                else None
            )
            chk = check_flight(fit, m_per_px=m_per_px, object_size_px=size_px)
        except PhysicsInputError as exc:
            return {"check": name, "verdict": "insufficient_data",
                    "reasons": [str(exc)], "numbers": {}}
        return {
            "check": name,
            "verdict": chk.verdict,
            "reasons": list(chk.reasons),
            "numbers": _finite_dict({
                "a_px_s2": fit.a_px_s2,
                "tilt_deg": fit.tilt_deg,
                "rms_residual_px": fit.rms_residual_px,
                "travel_px": fit.travel_px,
                "g_apparent_m_s2": chk.g_apparent_m_s2,
                "implied_time_factor": chk.implied_time_factor,
                "implied_object_size_m": chk.implied_object_size_m,
                "n_points": fit.n,
            }),
        }
    if name == "bounce":
        chk = check_bounces(pts)
        return {
            "check": name,
            "verdict": chk.verdict,
            "reasons": list(chk.reasons),
            "numbers": _finite_dict(
                {f"rebound_ratio_{i + 1}": e * e for i, e in enumerate(chk.restitution)}
            ),
        }
    dets = [
        Detection(
            t,
            (x, y),
            (sizes[i] ** 2 if i < len(sizes) else None),
        )
        for i, (t, x, y) in enumerate(pts)
    ]
    events = persistence_events(dets)
    return {
        "check": name,
        "events": [{"kind": e.kind, "t_s": e.t_s, "detail": e.detail} for e in events],
        "numbers": {"n_events": len(events)},
    }


def plan_audit_checks(
    audit: Mapping[str, Any],
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Plan which audit checks to keep, with a grounded rationale (T45).

    Returns {"selected": [...], "rationale": str}. With no tracked points,
    returns an empty plan without an API call.
    """
    if not isinstance(audit, Mapping):
        raise ModelOutputError("audit must be a mapping")
    points = _audit_points(audit)
    if not points:
        return {"selected": [], "rationale": INSUFFICIENT}
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()

    def run_once() -> dict[str, Any]:
        inputs: list[Any] = [
            {"type": "message", "role": "user",
             "content": [{"type": "input_text", "text": AUDIT_SYSTEM}]}
        ]
        tool_outputs: list[dict[str, Any]] = []
        totals = {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0}
        try:
            for _ in range(MAX_AGENT_STEPS):
                response = call_with_retry(
                    lambda: sdk.responses.create(
                        model=resolved, input=inputs, tools=AUDIT_TOOLS, timeout=timeout
                    ),
                    op="spark.plan_audit_checks",
                )
                usage = _usage_to_dict(getattr(response, "usage", None))
                for key in totals:
                    totals[key] += usage[key]
                calls = _function_calls(response)
                raw_output = getattr(response, "output", None) or []
                inputs.extend(_item_to_dict(i) for i in raw_output)
                if not calls:
                    raise ModelOutputError("agent stopped without proposing a plan")
                for call in calls:
                    cname = call.get("name")
                    args = json.loads(call.get("arguments") or "{}")
                    if cname == "run_check":
                        output = _run_check(args.get("name"), audit)
                        tool_outputs.append(output)
                        inputs.append(
                            {
                                "type": "function_call_output",
                                "call_id": call.get("call_id"),
                                "output": json.dumps(output, ensure_ascii=False, default=str),
                            }
                        )
                    elif cname == "propose_plan":
                        selected = args.get("selected")
                        template = args.get("rationale_template")
                        if not isinstance(selected, list) or not selected:
                            raise ModelOutputError("propose_plan requires a non-empty selected list")
                        if any(s not in AUDIT_CHECKS for s in selected):
                            raise ModelOutputError(
                                f"selected must be a subset of {list(AUDIT_CHECKS)}"
                            )
                        if not isinstance(template, str) or not template.strip():
                            raise ModelOutputError("rationale_template must be a non-empty string")
                        slots: dict[str, float] = {}
                        for output in tool_outputs:
                            for key, value in (output.get("numbers") or {}).items():
                                slots[f"{output.get('check')}_{key}"] = value
                        filled, fill_check = fill_numbers(template, slots)
                        if not fill_check.ok:
                            raise ModelOutputError(
                                "rationale slots failed: " + "; ".join(fill_check.problems)
                            )
                        assert filled is not None
                        text_check = check_model_text(filled, [audit, *tool_outputs])
                        if not text_check.ok:
                            raise ModelOutputError(
                                "output check failed: " + "; ".join(text_check.problems)
                            )
                        return {
                            "selected": list(dict.fromkeys(selected)),
                            "rationale": filled,
                        }
                    else:
                        raise ModelOutputError(f"unknown tool call {cname!r}")
            raise ModelOutputError("agent exceeded the step limit without deciding")
        finally:
            tracker.record(
                resolved,
                "spark.plan_audit_checks",
                input_tokens=totals["input_tokens"],
                cached_tokens=totals["cached_tokens"],
                output_tokens=totals["output_tokens"],
            )

    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        try:
            return run_once()
        except (ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"agent failed validation: {last_error}")
