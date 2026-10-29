#!/usr/bin/env python3
"""Measure one real Spark call + one real SAM call (T05).

john provides one photo and one ~10s clip; this script calls each endpoint
once and prints tokens/frames and USD. Usage is also appended to
data/cost_log.csv by the normal cost tracker.

Nothing here prints MODEL_API_KEY. Run from the repo root:

    source .venv/bin/activate
    python scripts/measure_cost.py --image data/raw/xxx.jpg \\
        --video data/raw/xxx.mp4 --prompt "sliding block"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from meta_client import sam, spark  # noqa: E402
from meta_client.cost import get_tracker  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure real Meta API cost (1+1 calls).")
    parser.add_argument("--image", required=True, type=Path, help="setup photo")
    parser.add_argument("--video", required=True, type=Path, help="~10s clip")
    parser.add_argument("--prompt", default="sliding block", help="SAM concept prompt")
    parser.add_argument("--spark-model", default=None, help="override SPARK_MODEL")
    args = parser.parse_args()

    if not args.image.is_file():
        print(f"image not found: {args.image}", file=sys.stderr)
        return 2
    if not args.video.is_file():
        print(f"video not found: {args.video}", file=sys.stderr)
        return 2

    tracker = get_tracker()
    print(f"spend before: ${tracker.total_usd():.4f} (limit ${tracker.limit_usd:.2f})")

    scene = spark.describe_scene(args.image, model=args.spark_model)
    print("scene:", json.dumps(scene, ensure_ascii=False))

    result = sam.track(args.video, args.prompt)
    present = sum(1 for d in result.detections if d.centroid_px is not None)
    print(
        f"track: {result.n_frames} frames at {result.fps:g} fps, "
        f"{len(result.detections)} detections ({present} with mask), "
        f"objects {result.object_ids()}, billed {result.billed_frames} frames, "
        f"${result.cost_usd:.6f}"
    )

    print(f"spend after:  ${tracker.total_usd():.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
