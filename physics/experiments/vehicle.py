"""A road vehicle seen side-on by a fixed camera, driving across the frame.

The car's own length is the ruler: the user confirms how long the car is (metres) and the tracker
gives its length in pixels, so speeds and accelerations come out in metres and seconds. The physical
check is grip: an ordinary road car on tyres cannot speed up, brake or swerve harder than about
1 g, so a track that needs more than MAX_ACCEL_G is inconsistent with a car driving on a road.
Without a confirmed length the check uses the shortest and longest ordinary cars (3-6 m) and only
judges when both give the same answer.

Perspective, slow motion and a moving camera are refused upstream; the verdict only says whether the
track is consistent with a car on tyres, never whether a video is real or fake.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..errors import PhysicsInputError

G = 9.81
MIN_POINTS = 8
MIN_SPAN_S = 0.5
MAX_ACCEL_G = 1.2  # beyond hard braking of ordinary road cars on dry asphalt (about 0.8-1.1 g)
TYPICAL_LENGTH_M = (3.0, 6.0)  # shortest city car to longest pickup or van
WIDTH_AGREEMENT = 0.1  # widths within 10% of the median count as the whole car in view


@dataclass(frozen=True)
class DriveFit:
    v_px_s: float  # speed along the direction of travel at the first tracked point
    a_px_s2: float  # acceleration along the direction of travel; negative = slowing down
    a_stderr_px_s2: float
    rms_residual_px: float  # distance of the track from the fitted smooth path
    travel_px: float
    n: int
    t_span_s: float


def car_length_px(widths_px: list[float]) -> float:
    """Car length in pixels from per-frame box widths: the median of the widths that agree with the overall
    median. Frames where the car is cut by the frame edge (narrower) or merged with a shadow or a
    background ghost (wider) are left out, as long as they are a minority."""
    w = np.array([x for x in widths_px if x and x > 0], dtype=float)
    if len(w) == 0:
        raise PhysicsInputError("no car widths in pixels")
    mid = float(np.median(w))
    steady = w[np.abs(w - mid) <= WIDTH_AGREEMENT * mid]
    if len(steady) < len(w) / 2:
        raise PhysicsInputError("car length in pixels changes too much along the track to use as a ruler")
    return float(np.median(steady))


def fit_drive(points: list[tuple[float, float, float]]) -> DriveFit:
    """points: (t_s, x_px, y_px) of the car's centre; gaps are left as gaps."""
    if len(points) < MIN_POINTS:
        raise PhysicsInputError(f"need at least {MIN_POINTS} tracked frames, got {len(points)}")
    arr = np.array(sorted(points), dtype=float)
    t = arr[:, 0] - arr[0, 0]
    span = float(t[-1])
    if span < MIN_SPAN_S:
        raise PhysicsInputError(f"track covers only {span:.2f} s; need at least {MIN_SPAN_S} s")
    xy = arr[:, 1:] - arr[:, 1:].mean(axis=0)
    _, vecs = np.linalg.eigh(np.cov(xy.T))
    axis = vecs[:, -1]  # direction of travel
    if axis @ (xy[-1] - xy[0]) < 0:
        axis = -axis
    s = xy @ axis
    X = np.column_stack([np.ones_like(t), t, 0.5 * t**2])
    c, *_ = np.linalg.lstsq(X, s, rcond=None)
    side = xy @ np.array([-axis[1], axis[0]])
    r2 = (s - X @ c) ** 2 + (side - side.mean()) ** 2  # squared distance from the fitted path
    sigma2 = float(np.sum((s - X @ c) ** 2)) / max(len(t) - 3, 1)
    a_se = math.sqrt(sigma2 * np.linalg.inv(X.T @ X)[2, 2])
    return DriveFit(v_px_s=float(c[1]), a_px_s2=float(c[2]), a_stderr_px_s2=a_se,
                    rms_residual_px=float(np.sqrt(np.mean(r2))), travel_px=float(s.max() - s.min()),
                    n=len(t), t_span_s=span)


@dataclass(frozen=True)
class DriveCheck:
    verdict: str  # "consistent" | "inconsistent" | "insufficient_data"
    reasons: tuple[str, ...]
    length_px: float
    speed_lengths_s: float  # car lengths per second; needs no metres at all
    accel_lengths_s2: float
    length_for_max_accel_m: float  # car length at which this track would need exactly MAX_ACCEL_G
    speed_m_s: float | None  # only with a user-confirmed car length
    accel_m_s2: float | None
    accel_g: float | None


def check_drive(fit: DriveFit, widths_px: list[float], *, car_length_m: float | None = None,
                max_accel_g: float = MAX_ACCEL_G, max_rms_fraction: float = 0.03) -> DriveCheck:
    """car_length_m must come from the user (a known model or a tape), never from a model."""
    if car_length_m is not None and car_length_m <= 0:
        raise PhysicsInputError("car_length_m must be positive")
    L_px = car_length_px(widths_px)
    if fit.travel_px < L_px:
        raise PhysicsInputError("car moves less than its own length in the window; pick a longer window")
    a = abs(fit.a_px_s2)
    limit = max_accel_g * G
    length_for_limit = limit * L_px / a if a > 0 else math.inf
    reasons: list[str] = []
    if fit.rms_residual_px > max_rms_fraction * fit.travel_px:
        reasons.append("track jumps or wobbles; it does not follow a smooth speed change")

    speed = accel = accel_g = None
    if car_length_m is not None:
        m_per_px = car_length_m / L_px
        speed, accel = fit.v_px_s * m_per_px, fit.a_px_s2 * m_per_px
        accel_g = abs(accel) / G
        if accel_g > max_accel_g:
            reasons.append(f"needs {accel_g:.1f} g of {'braking' if accel < 0 else 'acceleration'}; "
                           f"road cars on tyres stay under about {max_accel_g:.1f} g")
    else:
        lo_m, hi_m = TYPICAL_LENGTH_M
        if a * lo_m / L_px > limit:
            reasons.append(f"even a {lo_m:.0f} m car would need {a * lo_m / L_px / G:.1f} g; "
                           f"road cars on tyres stay under about {max_accel_g:.1f} g")
        elif a * hi_m / L_px > limit and not reasons:
            return DriveCheck("insufficient_data", ("car length not confirmed and the answer depends on it",),
                              L_px, fit.v_px_s / L_px, fit.a_px_s2 / L_px, length_for_limit, None, None, None)

    return DriveCheck("inconsistent" if reasons else "consistent", tuple(reasons), L_px, fit.v_px_s / L_px,
                      fit.a_px_s2 / L_px, length_for_limit, speed, accel, accel_g)
