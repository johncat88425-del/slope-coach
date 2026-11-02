"""T252 probe: print the background drift ratio for clips (no model calls, no uploads).

usage: python -m scripts.background_probe CLIP [CLIP ...]   (optionally --start S --seconds N)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.video import read_frames
from physics.background import background_drift


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--seconds", type=float, default=2.0)
    a = ap.parse_args()
    for clip in a.clips:
        frames, fps = read_frames(clip, a.start, a.start + a.seconds, 30.0)
        try:
            d = background_drift(frames, long_lag=max(2, round(0.5 * fps)))
            print(json.dumps({"clip": Path(clip).name, "fps": fps, "frames": int(frames.shape[0]), **d.__dict__}))
        except ValueError as e:
            print(json.dumps({"clip": Path(clip).name, "error": str(e)}))


if __name__ == "__main__":
    main()
