"""Camera shake / small pan correction (T244).

A hand-held or slightly bumped camera moves the whole background in the image, and that motion is added to
the tracked object's path: a real throw then fails the constant-acceleration check. Here the background's
image shift relative to the first frame is measured with phase correlation (object area masked out) and can
be subtracted from the tracked points.

Only a pure translation (side-to-side / up-down shift) is corrected. The shift is measured separately in the
left, right, top and bottom halves of the frame; if they disagree the camera rotated or zoomed, which a 2D
shift cannot undo, and the caller must refuse. Low-texture backgrounds (a plain wall) give no reliable shift;
then nothing is corrected and the caller must not claim a correction. Pure numpy, no model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MIN_PEAK = 0.08  # phase-correlation peak height below this: background too plain to measure a shift
MAX_HALF_DISAGREE_PX = 3.0  # halves disagreeing by more than this: rotation or zoom, not a shift


@dataclass(frozen=True)
class CameraMotion:
    shifts: tuple[tuple[float, float], ...]  # background (dx, dy) in px per requested frame, vs the first
    reliable: bool  # every shift measured on enough texture
    translational: bool  # halves agree: a 2D shift explains the background motion
    max_shift_px: float
    max_half_disagree_px: float


def _hann(h: int, w: int) -> np.ndarray:
    return np.outer(np.hanning(h), np.hanning(w))


def _phase_shift(ref: np.ndarray, cur: np.ndarray) -> tuple[float, float, float]:
    """(dx, dy, peak): how far the content of cur moved relative to ref, with sub-pixel refinement."""
    win = _hann(*ref.shape)
    a = np.fft.fft2((ref - ref.mean()) * win)
    b = np.fft.fft2((cur - cur.mean()) * win)
    r = b * np.conj(a)
    r /= np.abs(r) ** 0.5 + 1e-9  # half whitening: sharp peak without letting the masked patches' edges dominate
    corr = np.fft.ifft2(r).real
    iy, ix = np.unravel_index(int(np.argmax(corr)), corr.shape)
    peak = float(corr[iy, ix])
    h, w = corr.shape

    def refine(c_m: float, c_0: float, c_p: float) -> float:
        den = c_m - 2 * c_0 + c_p
        return 0.0 if abs(den) < 1e-12 else 0.5 * (c_m - c_p) / den

    dy = iy + refine(corr[(iy - 1) % h, ix], corr[iy, ix], corr[(iy + 1) % h, ix])
    dx = ix + refine(corr[iy, (ix - 1) % w], corr[iy, ix], corr[iy, (ix + 1) % w])
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    return float(dx), float(dy), peak


def _masked(frame: np.ndarray, centres: list[tuple[float, float]], radius: float) -> np.ndarray:
    out = frame.astype(np.float64, copy=True)
    if radius <= 0 or not centres:
        return out
    yy, xx = np.mgrid[0:frame.shape[0], 0:frame.shape[1]]
    keep = np.ones(out.shape, dtype=bool)
    for cx, cy in centres:
        keep &= (xx - cx) ** 2 + (yy - cy) ** 2 > radius ** 2
    out[~keep] = float(out[keep].mean()) if keep.any() else 0.0  # flat at the mean: no contrast to match
    return out


def measure_camera_motion(frames: np.ndarray, idx: list[int], obj_xy: list[tuple[float, float]],
                          mask_radius_px: float) -> CameraMotion:
    """frames: (n, h, w) grey; idx: frame index of each tracked point; obj_xy: the tracked object position in
    that frame (masked out, together with its position in the reference frame, so the object's own motion
    does not count as camera motion). Shifts are relative to frame idx[0]."""
    if not idx:
        return CameraMotion((), False, False, 0.0, 0.0)
    if frames.shape[2] > 260:  # work at half size (4x fewer pixels, ~5x faster on the 0.1-CPU host); shifts x2
        used = sorted(set(idx))
        small = {i: frames[i, : frames.shape[1] // 2 * 2, : frames.shape[2] // 2 * 2].reshape(
            frames.shape[1] // 2, 2, frames.shape[2] // 2, 2).mean(axis=(1, 3)) for i in used}
        stack = np.zeros((max(used) + 1, *next(iter(small.values())).shape))
        for i, f in small.items():
            stack[i] = f
        half = measure_camera_motion(stack, idx, [(x / 2, y / 2) for x, y in obj_xy], mask_radius_px / 2)
        return CameraMotion(tuple((2 * dx, 2 * dy) for dx, dy in half.shifts), half.reliable, half.translational,
                            2 * half.max_shift_px, 2 * half.max_half_disagree_px)
    h, w = frames.shape[1], frames.shape[2]
    ref_i, ref_xy = idx[0], obj_xy[0]
    halves = [(slice(0, h), slice(0, w // 2)), (slice(0, h), slice(w // 2, w)),
              (slice(0, h // 2), slice(0, w)), (slice(h // 2, h), slice(0, w))]
    shifts, reliable, worst_dis = [], True, 0.0
    for i, xy in zip(idx, obj_xy):
        ref = _masked(frames[ref_i], [ref_xy, xy], mask_radius_px)
        cur = _masked(frames[i], [ref_xy, xy], mask_radius_px)
        dx, dy, peak = _phase_shift(ref, cur)
        if i != ref_i and peak < MIN_PEAK:
            reliable = False
        parts = [_phase_shift(ref[s], cur[s])[:2] for s in halves]
        dis = max(float(np.hypot(px - dx, py - dy)) for px, py in parts)
        worst_dis = max(worst_dis, dis)
        shifts.append((dx, dy))
    max_shift = max(float(np.hypot(dx, dy)) for dx, dy in shifts)
    return CameraMotion(tuple(shifts), reliable, worst_dis <= MAX_HALF_DISAGREE_PX, max_shift, worst_dis)


def compensate(points: list[tuple[float, float, float]], motion: CameraMotion) -> list[tuple[float, float, float]]:
    """Subtract the background shift from each tracked (t, x, y)."""
    return [(t, x - dx, y - dy) for (t, x, y), (dx, dy) in zip(points, motion.shifts)]
