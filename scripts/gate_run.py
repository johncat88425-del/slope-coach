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

import numpy as np

from backend.video import color_for, probe_fps, read_frames, read_frames_rgb, save_overlay, track, track_color

# Frozen 2026-10-28 before any gate clip was seen. Do not tune per clip.
GATE_RULES = {
    "diff_threshold": 30.0,  # grey levels, frame differencing
    "min_tracked_fraction": 0.8,  # of frames in the labelled window
    "g_tolerance": 0.15,  # passed to check_flight
    "max_tilt_deg": 15.0,
    "max_rms_fraction": 0.02,
    # Added 2026-10-29 (T87, 規則變更紀錄): when the human label names a colour ("orange ball"), track
    # colour + motion instead of plain frame differencing. --tracker frame_diff reproduces the old rule.
    "tracker": "color_when_named",
}

COLUMNS = ["clip", "source", "assumed_model", "t_start", "t_end", "camera_static", "object", "object_size_m",
           "track_ok"]  # track_ok: john's yes/no after looking at the overlay; blank until he has
RESULTS = ("consistent", "inconsistent", "insufficient_data", "refused")


def run_clip(row: dict, clips_dir: Path, overlay_dir: Path | None = None, tracker: str | None = None) -> dict:
    out = {k: row.get(k, "") for k in ("clip", "source", "assumed_model", "object")}
    out["track_ok"] = (row.get("track_ok") or "").strip().lower()
    missing = [k for k in ("source", "t_start", "t_end", "camera_static") if not (row.get(k) or "").strip()]
    if missing:
        return out | {"result": "unlabelled", "why": "waiting for john's labels: " + ", ".join(missing)}
    if row["assumed_model"] != "free_flight":
        return out | {"result": "refused", "why": f"model '{row['assumed_model']}' not checked by this gate"}
    if row["camera_static"].strip().lower() not in ("yes", "y", "1", "true"):
        return out | {"result": "refused", "why": "camera not static (human label)"}
    start, end = float(row["t_start"]), float(row["t_end"])
    path = str(clips_dir / row["clip"])
    color = color_for(row.get("object", "")) if (tracker or GATE_RULES["tracker"]) != "frame_diff" else None
    if color:
        rgb = read_frames_rgb(path, start, end)
        fps = probe_fps(path)
        pts, sizes = track_color(rgb, fps, start, color, GATE_RULES["diff_threshold"])
        size_px = float(np.median(sizes)) if sizes else None
        frames = rgb.mean(axis=-1)
    else:
        frames, fps = read_frames(path, start, end)
        pts, size_px = track(frames, fps, start, GATE_RULES["diff_threshold"])
    out["tracker"] = f"color:{color}" if color else "frame_diff"
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


def _yes(v) -> bool:
    return str(v).strip().lower() in ("yes", "y", "1", "true")


def strong_anomaly(r: dict) -> bool:
    """An inconsistent verdict that survives a 30% error in the object size (gate question 2)."""
    if r.get("result") != "inconsistent":
        return False
    if (r.get("tilt_deg") or 0) > GATE_RULES["max_tilt_deg"]:
        return True
    if (r.get("rms_over_travel") or 0) > GATE_RULES["max_rms_fraction"]:
        return True
    g = r.get("g_apparent")
    return g is not None and abs(g / 9.81 - 1) > 0.5


def gate_summary(rows: list[dict]) -> dict:
    """Counts per source and the three gate questions, computed the same way for every clip.
    A question is 'pending' while it depends on overlay checks john has not made yet.
    Clips john has not labelled yet are left out of every count and listed separately."""
    unlabelled = [r["clip"] for r in rows if r["result"] == "unlabelled"]
    rows = [r for r in rows if r["result"] != "unlabelled"]
    counts: dict[str, dict[str, int]] = {}
    for r in rows:
        c = counts.setdefault(r.get("source") or "other", {k: 0 for k in RESULTS})
        c[r["result"]] = c.get(r["result"], 0) + 1

    own = [r for r in rows if r.get("source") == "own"]
    good = [r for r in own if r["result"] == "consistent" and r.get("g_apparent") is not None
            and abs(r["g_apparent"] / 9.81 - 1) <= GATE_RULES["g_tolerance"]]
    if len(own) < 3:
        q1 = "pending"
    elif len(good) < 2:
        q1 = "fail"
    elif sum(_yes(r.get("track_ok")) for r in good) >= 2:
        q1 = "pass"
    else:
        q1 = "pending" if any(not r.get("track_ok") for r in good) else "fail"

    cand = [r for r in rows if strong_anomaly(r) and (r.get("tracked_fraction") or 0) >= GATE_RULES["min_tracked_fraction"]]
    if any(_yes(r.get("track_ok")) for r in cand):
        q2 = "pass"
    elif any(not r.get("track_ok") for r in cand):
        q2 = "pending"
    else:
        q2 = "fail"

    refused = sum(r["result"] == "refused" for r in rows)
    q3 = "pending" if not rows else ("pass" if refused * 2 <= len(rows) else "fail")
    false_alarms = [r["clip"] for r in own if r["result"] == "inconsistent"]
    return {"counts": counts, "q1": q1, "q2": q2, "q3": q3, "refused": refused, "total": len(rows),
            "own_false_alarms": false_alarms, "strong_anomalies": [r["clip"] for r in cand],
            "unlabelled": unlabelled}


def summary_markdown(s: dict) -> str:
    lines = ["| source | " + " | ".join(RESULTS) + " |", "|" + " --- |" * (len(RESULTS) + 1)]
    for src, c in sorted(s["counts"].items()):
        lines.append(f"| {src} | " + " | ".join(str(c.get(k, 0)) for k in RESULTS) + " |")
    lines += ["", f"Q1 trustworthy tracks on own clips: {s['q1']}",
              f"Q2 clear anomaly not explained by tracking or size error: {s['q2']}"
              + (f" ({', '.join(s['strong_anomalies'])})" if s["strong_anomalies"] else ""),
              f"Q3 one rule set, at most half refused: {s['q3']} ({s['refused']}/{s['total']} refused)"]
    if s["unlabelled"]:
        lines.append(f"Not labelled yet (not counted): {', '.join(s['unlabelled'])}")
    if s["own_false_alarms"]:
        lines.append(f"False alarms on own clips (explain each): {', '.join(s['own_false_alarms'])}")
    lines.append("All clips in the manifest are listed; none are left out.")
    return "\n".join(lines) + "\n"


def to_markdown(rows: list[dict]) -> str:
    keys = ["clip", "source", "assumed_model", "result", "why", "g_apparent", "time_factor",
            "implied_size_m", "tilt_deg", "rms_over_travel", "tracked_fraction", "tracker", "track_ok"]
    lines = ["| " + " | ".join(keys) + " |", "|" + " --- |" * len(keys)]
    for r in rows:
        lines.append("| " + " | ".join("" if r.get(k) is None else str(r.get(k, "")) for k in keys) + " |")
    lines.append("")
    lines.append(f"Rules: {GATE_RULES}.")
    return "\n".join(lines) + "\n\n## Summary\n\n" + summary_markdown(gate_summary(rows))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--overlays", default=None, help="folder for track overlay PNGs (human check)")
    ap.add_argument("--tracker", default=None, choices=["frame_diff", "color_when_named"],
                    help="override GATE_RULES['tracker'], e.g. frame_diff to report the pre-T87 results")
    a = ap.parse_args()
    ov = Path(a.overlays) if a.overlays else None
    with open(a.manifest, newline="", encoding="utf-8") as f:
        rows = [run_clip(r, Path(a.clips), ov, a.tracker) for r in csv.DictReader(f)]
    md = to_markdown(rows)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
