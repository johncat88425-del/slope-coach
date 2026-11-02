"""Does the still background stay still? (T252, prototype)

With a fixed camera, a real recording's static background changes from frame to frame only by sensor and
compression noise, and that noise does not grow with the time between frames: a wall 0.5 s later looks as
different as a wall 1 frame later. A background whose texture slowly drifts or "boils" changes more the
further apart the frames are. The drift ratio compares the median background change at a long lag with
the change at a lag of one frame, after removing global brightness changes (auto exposure). Moving things are
masked out as the pixels that change most. Pure numpy, no model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BackgroundDrift:
    drift_ratio: float  # long-lag change / one-frame change on the still background; ~1 for a still scene
    short_change: float  # median absolute grey-level change at lag 1 (noise level)
    long_change: float
    still_fraction: float  # share of pixels used as still background


def _norm(f: np.ndarray) -> np.ndarray:
    f = f.astype(np.float32)
    return (f - f.mean()) / (f.std() + 1e-6)  # removes auto-exposure gain and offset


def background_drift(frames: np.ndarray, long_lag: int, *, keep_fraction: float = 0.6) -> BackgroundDrift:
    """frames: (n, h, w) grey, fixed or stabilised camera; long_lag in frames (about 0.5 s)."""
    n = frames.shape[0]
    if n < long_lag + 2 or long_lag < 2:
        raise ValueError("clip too short for the background drift check")
    f = np.stack([_norm(x) for x in frames])
    motion = np.abs(np.diff(f, axis=0)).max(axis=0)  # anything that ever moved
    still = motion <= np.quantile(motion, keep_fraction)
    s = [np.median(np.abs(f[i + 1] - f[i])[still]) for i in range(n - 1)]
    lg = [np.median(np.abs(f[i + long_lag] - f[i])[still]) for i in range(n - long_lag)]
    short, long = float(np.median(s)), float(np.median(lg))
    return BackgroundDrift(long / max(short, 1e-6), short, long, float(still.mean()))
