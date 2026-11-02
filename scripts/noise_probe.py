"""T255 probe (not used by the product): does the fine-grain noise on the still background look like fresh
camera-sensor noise each frame? Prints the noise level and its frame-to-frame correlation. No model calls.

usage: python -m scripts.noise_probe CLIP [CLIP ...] [--start S] [--seconds N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from backend.video import read_frames


def _highpass(f: np.ndarray) -> np.ndarray:
    f = f.astype(np.float32)
    p = np.pad(f, 1, mode="edge")
    box = sum(p[i:i + f.shape[0], j:j + f.shape[1]] for i in range(3) for j in range(3)) / 9.0
    return f - box


def probe(frames: np.ndarray) -> dict:
    hp = np.stack([_highpass(f) for f in frames])
    motion = np.abs(np.diff(frames.astype(np.float32), axis=0)).max(axis=0)
    texture = np.abs(hp).mean(axis=0)
    still = (motion <= np.quantile(motion, 0.5)) & (texture <= np.quantile(texture, 0.5))  # flat and still
    r = hp[:, still]
    r = r - r.mean(axis=0, keepdims=True)  # remove the fixed texture: keep only what changes frame to frame
    def corr(a, b):
        return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))
    c1 = [corr(r[i], r[i + 1]) for i in range(len(r) - 1)]
    c2 = [corr(r[i], r[i + 2]) for i in range(len(r) - 2)]
    return {"noise_std": float(r.std()), "corr_lag1": float(np.median(c1)), "corr_lag2": float(np.median(c2)),
            "zero_change_fraction": float((np.abs(np.diff(frames[:, still].astype(np.int16), axis=0)) == 0).mean())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--seconds", type=float, default=2.0)
    a = ap.parse_args()
    for clip in a.clips:
        frames, fps = read_frames(clip, a.start, a.start + a.seconds, 30.0)
        print(json.dumps({"clip": Path(clip).name, "fps": fps, "frames": int(frames.shape[0]), **probe(frames)}))


if __name__ == "__main__":
    main()
