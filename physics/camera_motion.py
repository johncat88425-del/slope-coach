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
    # T256: (tx, ty, a, b) per frame: content at offset c from the image centre moved by t + a*c + b*J*c
    # (a = zoom - 1, b = roll in radians, J*c = (-cy, cx)). similar: that model explains all four halves.
    similarity: tuple[tuple[float, float, float, float], ...] = ()
    similar: bool = False
    max_zoom: float = 0.0  # largest |a|
    max_roll_deg: float = 0.0


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


class _HalfSize:
    """Half-resolution view made one frame at a time (T249). Building a float stack of every frame up to the
    last tracked one took ~600 MB for a 5 s window at 1080p and restarted the 512 MB host."""

    def __init__(self, frames: np.ndarray):
        self.frames = frames
        self.shape = (frames.shape[0], frames.shape[1] // 2, frames.shape[2] // 2)

    def __getitem__(self, i: int) -> np.ndarray:
        h, w = self.shape[1], self.shape[2]
        f = self.frames[i]  # the source may itself be a half-size view (wide clips are halved more than once)
        return f[: 2 * h, : 2 * w].reshape(h, 2, w, 2).mean(axis=(1, 3), dtype=np.float32)


def measure_camera_motion(frames: np.ndarray, idx: list[int], obj_xy: list[tuple[float, float]],
                          mask_radius_px: float) -> CameraMotion:
    """frames: (n, h, w) grey; idx: frame index of each tracked point; obj_xy: the tracked object position in
    that frame (masked out, together with its position in the reference frame, so the object's own motion
    does not count as camera motion). Shifts are relative to frame idx[0]."""
    if not idx:
        return CameraMotion((), False, False, 0.0, 0.0)
    if frames.shape[2] > 260:  # work at half size (4x fewer pixels, ~5x faster on the 0.1-CPU host); shifts x2
        half = measure_camera_motion(_HalfSize(frames), idx, [(x / 2, y / 2) for x, y in obj_xy], mask_radius_px / 2)
        return CameraMotion(tuple((2 * dx, 2 * dy) for dx, dy in half.shifts), half.reliable, half.translational,
                            2 * half.max_shift_px, 2 * half.max_half_disagree_px,
                            tuple((2 * tx, 2 * ty, a, b) for tx, ty, a, b in half.similarity), half.similar,
                            half.max_zoom, half.max_roll_deg)
    h, w = frames.shape[1], frames.shape[2]
    ref_i, ref_xy = idx[0], obj_xy[0]
    halves = [(slice(0, h), slice(0, w // 2)), (slice(0, h), slice(w // 2, w)),
              (slice(0, h // 2), slice(0, w)), (slice(h // 2, h), slice(0, w))]
    centres = [(-w / 4, 0.0), (w / 4, 0.0), (0.0, -h / 4), (0.0, h / 4)]
    A = np.array([row for cx, cy in centres for row in ((1, 0, cx, -cy), (0, 1, cy, cx))], dtype=float)
    shifts, sims, reliable, worst_dis, worst_sim = [], [], True, 0.0, 0.0
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
        d = np.array([v for part in parts for v in part], dtype=float)
        sim, *_ = np.linalg.lstsq(A, d, rcond=None)
        resid = (A @ sim - d).reshape(-1, 2)
        worst_sim = max(worst_sim, float(np.hypot(resid[:, 0], resid[:, 1]).max()))
        sims.append(tuple(float(v) for v in sim))
    max_shift = max(float(np.hypot(dx, dy)) for dx, dy in shifts)
    return CameraMotion(tuple(shifts), reliable, worst_dis <= MAX_HALF_DISAGREE_PX, max_shift, worst_dis,
                        tuple(sims), worst_sim <= MAX_HALF_DISAGREE_PX,
                        max(abs(a) for _, _, a, _ in sims), float(np.degrees(max(abs(b) for *_, b in sims))))


def compensate(points: list[tuple[float, float, float]], motion: CameraMotion) -> list[tuple[float, float, float]]:
    """Subtract the background shift from each tracked (t, x, y)."""
    return [(t, x - dx, y - dy) for (t, x, y), (dx, dy) in zip(points, motion.shifts)]


def compensate_similarity(points: list[tuple[float, float, float]], sizes: list[float], motion: CameraMotion,
                          frame_w: int, frame_h: int) -> tuple[list[tuple[float, float, float]], list[float]]:
    """Undo a camera roll / zoom / shift (T256): map each tracked point back to where it would sit in the first
    frame, and divide its apparent size by the zoom. Small-angle model, matching how it was measured."""
    cx0, cy0 = frame_w / 2.0, frame_h / 2.0
    out_p, out_s = [], []
    for (t, x, y), size, (tx, ty, a, b) in zip(points, sizes, motion.similarity):
        m = np.array([[1 + a, -b], [b, 1 + a]])  # p_now - centre = m @ (p_ref - centre) + t
        rx, ry = np.linalg.solve(m, np.array([x - cx0 - tx, y - cy0 - ty]))
        out_p.append((t, float(rx + cx0), float(ry + cy0)))
        out_s.append(size / float(np.hypot(1 + a, b)))
    return out_p, out_s
