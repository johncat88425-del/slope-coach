"""Feasibility probe for the flight check: no model, no SAM.

Tracks the largest moving blob with frame differencing against a median background, then runs
physics.experiments.freefall on it. Good enough to tell whether a clip is worth a real run.

    python -m scripts.flight_probe clip.mp4 --start 1.0 --end 2.2 [--m-per-px 0.002]
"""
from __future__ import annotations

import argparse
import json
from physics.errors import PhysicsInputError
from physics.experiments.freefall import check_flight, fit_flight

from backend.video import WIDTH, read_frames, save_overlay, track


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--m-per-px", type=float, default=None, help=f"user-confirmed scale at {WIDTH}px width")
    ap.add_argument("--thresh", type=float, default=30.0)
    ap.add_argument("--overlay", default=None, help="write a PNG with the tracked points")
    a = ap.parse_args()
    frames, fps = read_frames(a.video, a.start, a.end)
    pts, size_px = track(frames, fps, a.start, a.thresh)
    if a.overlay:
        save_overlay(frames, pts, a.start, fps, a.overlay)
    out = {"fps": fps, "frames": len(frames), "tracked": len(pts)}
    try:
        fit = fit_flight(pts)
        chk = check_flight(fit, m_per_px=a.m_per_px, object_size_px=size_px)
        out |= {"a_px_s2": fit.a_px_s2, "tilt_deg": fit.tilt_deg, "rms_px": fit.rms_residual_px,
                "travel_px": fit.travel_px, **chk.__dict__}
    except PhysicsInputError as e:
        out["refused"] = str(e)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
