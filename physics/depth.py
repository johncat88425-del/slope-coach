"""Motion towards or away from the camera (T251).

A thrown ball that also moves along the camera axis changes its apparent size. Under a pinhole camera a rigid
object of true size D at distance Z appears s = f * D / Z pixels wide, and an image offset u from the image
centre maps to a real offset U = u * Z / f = u * D / s. The focal length cancels: each tracked position can be
put back into metres (or into pixels at one reference distance) from the object's own apparent size.

With a level camera, gravity has no component along the camera axis, so Z changes linearly in time during free
flight and 1/s = Z / (f D) is a straight line in t. That line is fitted to the measured sizes (smoothing their
noise) and must fit well; otherwise the size changes are not steady motion along the camera axis (mask noise,
a rotating or deforming object, a pitched camera) and the caller must refuse. Pure numpy, no model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .errors import PhysicsInputError

MAX_SIZE_FIT_RESIDUAL = 0.12  # rms of (measured size / fitted size - 1); masks are noisier than this only when wrong
MAX_SIZE_RATIO = 3.0  # nearest vs farthest apparent size over the window
MIN_SIZES = 6


@dataclass(frozen=True)
class DepthRescale:
    points: tuple[tuple[float, float, float], ...]  # (t, x, y) in pixels at the reference distance
    ref_size_px: float  # fitted apparent size at the reference (median) time; m_per_px = true size / this
    size_ratio: float  # largest / smallest fitted apparent size over the window
    size_fit_residual: float


def rescale_for_depth(points: list[tuple[float, float, float]], sizes: list[float], frame_w: int,
                      frame_h: int) -> DepthRescale:
    """points and sizes are per tracked frame (same order). Raises PhysicsInputError when the sizes do not
    describe steady motion along the camera axis."""
    if len(points) != len(sizes) or len(points) < MIN_SIZES:
        raise PhysicsInputError("too few frames with a measured object size to correct for motion towards the camera")
    t = np.array([p[0] for p in points], dtype=float)
    s = np.array(sizes, dtype=float)
    if np.any(s <= 0) or np.ptp(t) <= 0:
        raise PhysicsInputError("object size could not be measured in every tracked frame")
    X = np.column_stack([np.ones_like(t), t])
    coef, *_ = np.linalg.lstsq(X, 1.0 / s, rcond=None)
    inv = X @ coef
    if np.any(inv <= 0):
        raise PhysicsInputError("object size changes do not fit steady motion towards or away from the camera")
    s_fit = 1.0 / inv
    resid = float(np.sqrt(np.mean((s / s_fit - 1.0) ** 2)))
    ratio = float(s_fit.max() / s_fit.min())
    if resid > MAX_SIZE_FIT_RESIDUAL:
        raise PhysicsInputError(f"object size jumps around (±{resid:.0%}) instead of changing steadily, so motion "
                                "towards the camera cannot be corrected")
    if ratio > MAX_SIZE_RATIO:
        raise PhysicsInputError(f"object size changes {ratio:.1f}x along the track, too much to correct reliably")
    t_ref = float(np.median(t))
    s_ref = 1.0 / float(coef[0] + coef[1] * t_ref)
    cx, cy = frame_w / 2.0, frame_h / 2.0
    k = s_ref / s_fit
    out = tuple((float(ti), float(cx + (x - cx) * ki), float(cy + (y - cy) * ki))
                for (ti, x, y), ki in zip(points, k))
    return DepthRescale(out, s_ref, ratio, resid)
