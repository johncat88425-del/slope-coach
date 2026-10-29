#!/usr/bin/env python3
"""Evaluate Spark's motion-segment suggestions vs human labels (T46).

For each row of data/gate/manifest.csv, calls
spark.suggest_motion_segment on the clip and compares the suggested object,
model, and time window with john's manual labels. Prints a table plus a
markdown block to paste into STATUS; --out saves the full JSON.

Face safety: clips listed in --faces are NEVER sent. The contributor model
additionally requires --i-confirm-no-faces. Real spend lands in
data/cost_log.csv via the normal tracker. --mock runs everything with
canned suggestions (no API calls) for tests.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from meta_client.cost import get_tracker  # noqa: E402
from meta_client.spark import suggest_motion_segment  # noqa: E402

MANIFEST_COLUMNS = (
    "clip",
    "source",
    "assumed_model",
    "t_start",
    "t_end",
    "camera_static",
    "object",
    "object_size_m",
)


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _mock_suggest(row: dict[str, str]) -> dict[str, Any]:
    """Deterministic canned suggestion derived from the label (mock only)."""
    return {
        "object": row["object"],
        "assumed_model": row["assumed_model"],
        "candidate_t_start": float(row["t_start"]) + 0.1,
        "candidate_t_end": float(row["t_end"]) - 0.1,
        "reason": "mock suggestion",
    }


def _score(row: dict[str, str], suggestion: dict[str, Any]) -> dict[str, Any]:
    start_err = (
        None
        if suggestion["candidate_t_start"] is None
        else suggestion["candidate_t_start"] - float(row["t_start"])
    )
    end_err = (
        None
        if suggestion["candidate_t_end"] is None
        else suggestion["candidate_t_end"] - float(row["t_end"])
    )
    return {
        "clip": row["clip"],
        "object_match": _norm(suggestion["object"]) == _norm(row["object"]),
        "model_match": suggestion["assumed_model"] == row["assumed_model"],
        "start_err_s": start_err,
        "end_err_s": end_err,
        "suggested": suggestion,
    }


def run_eval(
    manifest: Path,
    clips_dir: Path,
    *,
    faces: set[str],
    model: str,
    mock: bool,
    tracker=None,
) -> dict[str, Any]:
    with open(manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in MANIFEST_COLUMNS if c not in (rows[0] if rows else MANIFEST_COLUMNS)]
    if missing:
        raise ValueError(f"manifest missing columns: {missing}")
    report: dict[str, Any] = {"mock": mock, "model": model, "clips": [], "summary": {}}
    for row in rows:
        if row["clip"] in faces:
            report["clips"].append({"clip": row["clip"], "sent": False, "reason": "has face"})
            continue
        video = clips_dir / row["clip"]
        if not video.is_file():
            report["clips"].append({"clip": row["clip"], "sent": False, "reason": "file missing"})
            continue
        if mock:
            suggestion, cost = _mock_suggest(row), 0.0
        else:
            before = tracker.total_usd()
            try:
                suggestion = suggest_motion_segment(video, model=model, tracker=tracker)
            except Exception as exc:  # noqa: BLE001 - batch runner records and continues
                report["clips"].append(
                    {"clip": row["clip"], "sent": True, "failed": f"{type(exc).__name__}: {exc}"[:200],
                     "cost_usd": tracker.total_usd() - before}
                )
                continue
            cost = tracker.total_usd() - before
        scored = _score(row, suggestion)
        scored.update({"sent": True, "cost_usd": cost})
        report["clips"].append(scored)
    sent = [c for c in report["clips"] if c.get("sent") and "start_err_s" in c]
    abs_errs = [
        abs(e)
        for c in sent
        for e in (c["start_err_s"], c["end_err_s"])
        if e is not None
    ]
    report["summary"] = {
        "n_clips": len(rows),
        "n_sent": len(sent),
        "n_skipped": len(rows) - len(sent),
        "object_match_rate": (sum(c["object_match"] for c in sent) / len(sent)) if sent else None,
        "model_match_rate": (sum(c["model_match"] for c in sent) / len(sent)) if sent else None,
        "mean_abs_time_err_s": (sum(abs_errs) / len(abs_errs)) if abs_errs else None,
        "total_cost_usd": sum(c.get("cost_usd", 0.0) for c in report["clips"] if c.get("sent")),
    }
    return report


def _print_report(report: dict[str, Any]) -> None:
    s = report["summary"]
    print(f"clips: {s['n_clips']}, sent: {s['n_sent']}, skipped: {s['n_skipped']}")
    for c in report["clips"]:
        if not c.get("sent"):
            print(f"  SKIP {c['clip']}: {c.get('reason', c.get('failed'))}")
            continue
        if "start_err_s" not in c:
            print(f"  FAIL {c['clip']}: {c['failed']}")
            continue
        print(
            f"  {c['clip']}: object_match={c['object_match']} model_match={c['model_match']} "
            f"start_err={c['start_err_s']} end_err={c['end_err_s']} ${c['cost_usd']:.6f}"
        )
    print(
        "summary: object_match_rate={} model_match_rate={} mean_abs_time_err_s={} "
        "total_cost=${:.6f}".format(
            s["object_match_rate"], s["model_match_rate"],
            s["mean_abs_time_err_s"], s["total_cost_usd"],
        )
    )
    print("--- paste into STATUS ---")
    print(f"| 模型 | 送出/總數 | 物體一致率 | 模型一致率 | 平均時間誤差(秒) | 花費 |")
    print(f"| spark | {s['n_sent']}/{s['n_clips']} | {s['object_match_rate']} | "
          f"{s['model_match_rate']} | {s['mean_abs_time_err_s']} | {s['total_cost_usd']:.4f} |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate spark segment suggestions.")
    parser.add_argument("--manifest", type=Path, default=Path("data/gate/manifest.csv"))
    parser.add_argument("--clips", type=Path, default=Path("/mnt/project-files/gate"))
    parser.add_argument("--faces", type=Path, default=None, help="newline list of clips with faces")
    parser.add_argument("--model", default="muse-spark-1.3")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--i-confirm-no-faces", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if "contributor" in args.model and not args.i_confirm_no_faces:
        print("contributor model needs --i-confirm-no-faces", file=sys.stderr)
        return 2
    if not args.manifest.is_file():
        print(f"manifest not found: {args.manifest}", file=sys.stderr)
        return 2
    faces: set[str] = set()
    if args.faces is not None:
        if not args.faces.is_file():
            print(f"faces file not found: {args.faces}", file=sys.stderr)
            return 2
        faces = {l.strip() for l in args.faces.read_text().splitlines() if l.strip()}
    tracker = None if args.mock else get_tracker()
    try:
        report = run_eval(
            args.manifest, args.clips, faces=faces, model=args.model,
            mock=args.mock, tracker=tracker,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_report(report)
    if args.out is not None:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
