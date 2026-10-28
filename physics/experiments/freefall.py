"""Object in flight (dropped or thrown) seen by a fixed camera roughly perpendicular to its plane.

Works in image pixels first, so it can check a clip with no ruler at all:
- the fitted acceleration should be constant and point the same way the whole flight;
- with a user-confirmed scale it gives an apparent g to compare with 9.81 m/s^2;
- without a scale it gives the scale (and so the object size) that g = 9.81 would require,
  which a person can judge ("for this to be real the ball would have to be 2.4 m wide").

Air drag, spin and perspective are not modelled; the verdict only says whether the track is
consistent with constant-g flight, never whether a video is real or fake.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..errors import PhysicsInputError

G = 9.81
MIN_POINTS = 6


@dataclass(frozen=True)
class FlightFit:
    ax_px_s2: float
    ay_px_s2: float  # image y grows downward, so a real drop gives ay > 0 on an upright camera
    vx_px_s: float
    vy_px_s: float
    a_stderr_px_s2: float  # stderr of the acceleration magnitude
    rms_residual_px: float
    travel_px: float
    n: int
    t_span_s: float

    @property
    def a_px_s2(self) -> float:
        return math.hypot(self.ax_px_s2, self.ay_px_s2)

    @property
    def tilt_deg(self) -> float:
        """Angle between the fitted acceleration and image-down; 0 means straight down."""
        return math.degrees(math.atan2(self.ax_px_s2, self.ay_px_s2))


def fit_flight(points: list[tuple[float, float, float]]) -> FlightFit:
    """points: (t_s, x_px, y_px) for frames where the object was tracked; gaps are left as gaps."""
    if len(points) < MIN_POINTS:
        raise PhysicsInputError(f"need at least {MIN_POINTS} tracked frames in flight, got {len(points)}")
    arr = np.array(sorted(points), dtype=float)
    t = arr[:, 0] - arr[0, 0]
    span = float(t[-1])
    if span <= 0:
        raise PhysicsInputError("tracked frames cover zero time span")
    X = np.column_stack([np.ones_like(t), t, 0.5 * t**2])
    XtX_inv = np.linalg.inv(X.T @ X)
    coefs, resids = [], []
    for col in (1, 2):
        c, *_ = np.linalg.lstsq(X, arr[:, col], rcond=None)
        coefs.append(c)
        resids.append(arr[:, col] - X @ c)
    r = np.concatenate(resids)
    dof = max(2 * len(t) - 6, 1)
    sigma2 = float(r @ r) / dof
    a_se = math.sqrt(sigma2 * XtX_inv[2, 2])
    travel = float(np.hypot(arr[-1, 1] - arr[0, 1], arr[-1, 2] - arr[0, 2]))
    return FlightFit(
        ax_px_s2=float(coefs[0][2]), ay_px_s2=float(coefs[1][2]),
        vx_px_s=float(coefs[0][1]), vy_px_s=float(coefs[1][1]),
        a_stderr_px_s2=a_se, rms_residual_px=float(np.sqrt(np.mean(r**2))),
        travel_px=travel, n=len(t), t_span_s=span,
    )


@dataclass(frozen=True)
class FlightCheck:
    verdict: str  # "consistent" | "inconsistent" | "insufficient_data"
    reasons: tuple[str, ...]
    g_apparent_m_s2: float | None  # only with a user-confirmed scale
    implied_m_per_px: float  # scale at which this track would fall at exactly G
    implied_object_size_m: float | None  # only when the object's pixel size is known
    implied_time_factor: float | None  # >1 means the clip plays slower than real time (slow motion)


def check_flight(
    fit: FlightFit,
    *,
    m_per_px: float | None = None,
    object_size_px: float | None = None,
    g_tolerance: float = 0.15,
    max_tilt_deg: float = 15.0,
    max_rms_fraction: float = 0.02,
) -> FlightCheck:
    """m_per_px must come from the user (a ruler or a confirmed object size), never from a model."""
    if m_per_px is not None and m_per_px <= 0:
        raise PhysicsInputError("m_per_px must be positive")
    if fit.a_px_s2 <= 3 * fit.a_stderr_px_s2 or fit.travel_px <= 0:
        return FlightCheck("insufficient_data", ("acceleration is not distinguishable from zero",),
                           None, math.inf, None, None)

    implied = G / fit.a_px_s2
    size = object_size_px * implied if object_size_px else None
    reasons: list[str] = []
    if abs(fit.tilt_deg) > max_tilt_deg:
        reasons.append(f"acceleration points {fit.tilt_deg:.0f} deg away from image-down")
    if fit.rms_residual_px > max_rms_fraction * fit.travel_px:
        reasons.append("track does not follow a constant-acceleration path")

    g_app = factor = None
    if m_per_px is not None:
        g_app = fit.a_px_s2 * m_per_px
        factor = math.sqrt(G / g_app)
        lo, hi = G * (1 - g_tolerance), G * (1 + g_tolerance)
        if not lo <= g_app <= hi:
            reasons.append(f"apparent g {g_app:.2f} m/s^2 is outside {lo:.2f}-{hi:.2f}")

    return FlightCheck("inconsistent" if reasons else "consistent", tuple(reasons), g_app, implied, size, factor)
