#!/usr/bin/env python3
"""A/B: muse-spark-1.3 vs muse-wonder-1.0 on result explanations (T16).

Both models explain the same cases (comparison/audit payloads); each output
passes through the same validators T28 uses. Reports pass rate and cost per
arm. Small samples only answer "worth a closer look", never superiority.

--mock runs the whole comparison with canned outputs (no API calls, no
spend). Real runs stop before spending more than --budget-usd (default
1.00); real spend lands in data/cost_log.csv via the normal tracker.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from meta_client.cost import get_tracker, token_cost_usd  # noqa: E402
from meta_client.explain import explain_result  # noqa: E402

ARMS = ("muse-spark-1.3", "muse-wonder-1.0")

# Fixed mock token counts per (model): deterministic, mock-only.
MOCK_TOKENS = {"muse-spark-1.3": (200, 80), "muse-wonder-1.0": (200, 90)}


def _sample_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": "sample-comparison",
            "kind": "comparison",
            "result": {
                "verdict": "discrepancy",
                "arrival_error_rel": 0.25,
                "tolerance_rel": 0.15,
                "reasons": ["arrival differs"],
            },
        },
        {
            "id": "sample-audit",
            "kind": "audit",
            "result": {
                "verdict": "consistent",
                "numbers": {"g_apparent_m_s2": 9.81},
                "reasons": ["g within tolerance"],
            },
        },
    ]


def _mock_explain(model: str, case: dict[str, Any]) -> dict[str, Any]:
    from backend.output_check import check_model_text

    payload = case["result"]
    nums = []

    def _walk(o):
        if isinstance(o, bool):
            return
        if isinstance(o, (int, float)):
            nums.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                _walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                _walk(v)

    _walk(payload)
    first = nums[0] if nums else ""
    text = f"verdict 為{payload.get('verdict')}；引用數字 {first}。"
    checked = check_model_text(text, [payload])
    in_tok, out_tok = MOCK_TOKENS[model]
    return {
        "pass": checked.ok,
        "problems": checked.problems,
        "cost_usd": token_cost_usd(model, in_tok, out_tok),
    }


def _real_explain(model: str, case: dict[str, Any], tracker) -> dict[str, Any]:
    before = tracker.total_usd()
    try:
        explain_result(case["result"], kind=case["kind"], model=model, tracker=tracker)
        return {"pass": True, "problems": [], "cost_usd": tracker.total_usd() - before}
    except Exception as exc:  # noqa: BLE001 - batch runner records and continues
        return {
            "pass": False,
            "problems": [f"{type(exc).__name__}: {exc}"[:200]],
            "cost_usd": tracker.total_usd() - before,
        }


def run_ab(
    cases: list[dict[str, Any]], *, mock: bool, budget_usd: float, tracker=None
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "mock": mock,
        "budget_usd": budget_usd,
        "stopped_early": False,
        "arms": {m: {"passed": 0, "total": 0, "cost_usd": 0.0, "cases": []} for m in ARMS},
    }
    spent = 0.0
    for case in cases:
        if spent >= budget_usd:
            report["stopped_early"] = True
            break
        for model in ARMS:
            if mock:
                outcome = _mock_explain(model, case)
            else:
                outcome = _real_explain(model, case, tracker)
            arm = report["arms"][model]
            arm["total"] += 1
            arm["passed"] += 1 if outcome["pass"] else 0
            arm["cost_usd"] += outcome["cost_usd"]
            arm["cases"].append({"id": case.get("id"), **outcome})
            spent += outcome["cost_usd"]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A/B spark vs wonder on explanations.")
    parser.add_argument("--input", type=Path, default=None, help="cases JSON file")
    parser.add_argument("--mock", action="store_true", help="no API calls")
    parser.add_argument("--budget-usd", type=float, default=1.0)
    parser.add_argument("--out", type=Path, default=None, help="write JSON report")
    args = parser.parse_args(argv)

    if args.input is not None:
        if not args.input.is_file():
            print(f"cases file not found: {args.input}", file=sys.stderr)
            return 2
        cases = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        cases = _sample_cases()
    tracker = None if args.mock else get_tracker()
    report = run_ab(cases, mock=args.mock, budget_usd=args.budget_usd, tracker=tracker)
    for model, arm in report["arms"].items():
        print(f"{model}: {arm['passed']}/{arm['total']} passed, ${arm['cost_usd']:.6f}")
    if report["stopped_early"]:
        print(f"stopped early: budget ${args.budget_usd:.2f} reached")
    if args.out is not None:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
