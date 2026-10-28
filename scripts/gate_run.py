"""Run the feasibility gate (docs/STATUS.md, section 可行性關卡) on every clip in a manifest with one fixed rule set.

    python -m scripts.gate_run data/gate/manifest.csv --clips /mnt/project-files/gate --out data/gate/results.md

The only per-clip inputs are john's human labels in the manifest. Thresholds live in GATE_RULES
and in physics defaults; changing either after the first run must be recorded in docs/STATUS.md (規則變更紀錄).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from physics.errors import PhysicsInputError
from physics.experiments.freefall import check_flight, fit_flight

from backend.video import read_frames, save_overlay, track

# Frozen 2026-10-28 before any gate clip was seen. Do not tune per clip.
GATE_RULES = {
    "diff_threshold": 30.0,  # grey levels, frame differencing
    "min_tracked_fraction": 0.8,  # of frames in the labelled window
    "g_tolerance": 0.15,  # passed to check_flight
    "max_tilt_deg": 15.0,
    "max_rms_fraction": 0.02,
}

COLUMNS = ["clip", "source", "assumed_model", "t_start", "t_end", "camera_static", "object", "object_size_m"]


def run_clip(row: dict, clips_dir: Path, overlay_dir: Path | None = None) -> dict:
    out = {k: row.get(k, "") for k in ("clip", "source", "assumed_model", "object")}
    if row["assumed_model"] != "free_flight":
        return out | {"result": "refused", "why": f"model '{row['assumed_model']}' not checked by this gate"}
    if row["camera_static"].strip().lower() not in ("yes", "y", "1", "true"):
        return out | {"result": "refused", "why": "camera not static (human label)"}
    start, end = float(row["t_start"]), float(row["t_end"])
    frames, fps = read_frames(str(clips_dir / row["clip"]), start, end)
    pts, size_px = track(frames, fps, start, GATE_RULES["diff_threshold"])
    if overlay_dir is not None:
        overlay_dir.mkdir(parents=True, exist_ok=True)
        save_overlay(frames, pts, start, fps, str(overlay_dir / f"{Path(row['clip']).stem}_track.png"))
    frac = len(pts) / max(len(frames), 1)
    out |= {"frames": len(frames), "tracked_fraction": round(frac, 2)}
    if frac < GATE_RULES["min_tracked_fraction"]:
        return out | {"result": "refused", "why": f"object tracked in only {frac:.0%} of frames"}
    m_per_px = float(row["object_size_m"]) / size_px if row.get("object_size_m") and size_px else None
    try:
        fit = fit_flight(pts)
        chk = check_flight(fit, m_per_px=m_per_px, object_size_px=size_px,
                           g_tolerance=GATE_RULES["g_tolerance"], max_tilt_deg=GATE_RULES["max_tilt_deg"],
                           max_rms_fraction=GATE_RULES["max_rms_fraction"])
    except PhysicsInputError as e:
        return out | {"result": "refused", "why": str(e)}
    return out | {
        "result": chk.verdict,
        "why": "; ".join(chk.reasons),
        "g_apparent": None if chk.g_apparent_m_s2 is None else round(chk.g_apparent_m_s2, 2),
        "time_factor": None if chk.implied_time_factor is None else round(chk.implied_time_factor, 2),
        "implied_size_m": None if chk.implied_object_size_m is None else round(chk.implied_object_size_m, 3),
        "tilt_deg": round(fit.tilt_deg, 1),
        "rms_over_travel": round(fit.rms_residual_px / fit.travel_px, 3) if fit.travel_px else None,
    }


def to_markdown(rows: list[dict]) -> str:
    keys = ["clip", "source", "assumed_model", "result", "why", "g_apparent", "time_factor",
            "implied_size_m", "tilt_deg", "rms_over_travel", "tracked_fraction"]
    lines = ["| " + " | ".join(keys) + " |", "|" + " --- |" * len(keys)]
    for r in rows:
        lines.append("| " + " | ".join("" if r.get(k) is None else str(r.get(k, "")) for k in keys) + " |")
    refused = sum(r["result"] == "refused" for r in rows)
    lines.append("")
    lines.append(f"Rules: {GATE_RULES}. Refused {refused}/{len(rows)}.")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--overlays", default=None, help="folder for track overlay PNGs (human check)")
    a = ap.parse_args()
    ov = Path(a.overlays) if a.overlays else None
    with open(a.manifest, newline="", encoding="utf-8") as f:
        rows = [run_clip(r, Path(a.clips), ov) for r in csv.DictReader(f)]
    md = to_markdown(rows)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
