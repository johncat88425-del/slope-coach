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
    t0_s: float = 0.0  # time of the first tracked point; positions below are at t0_s
    x0_px: float = 0.0
    y0_px: float = 0.0

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
        t0_s=float(arr[0, 0]), x0_px=float(coefs[0][0]), y0_px=float(coefs[1][0]),
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


@dataclass(frozen=True)
class BounceCheck:
    verdict: str  # "consistent" | "inconsistent" | "insufficient_data"
    reasons: tuple[str, ...]
    heights_px: tuple[float, ...]  # peak height above the lowest tracked point, per flight segment
    restitution: tuple[float, ...]  # sqrt(h[k+1] / h[k]); must be <= 1 for a passive ball


def check_bounces(points: list[tuple[float, float, float]], *, tolerance: float = 0.05,
                  min_points_per_segment: int = 4) -> BounceCheck:
    """points: (t_s, x_px, y_px), image y down, camera static. Splits the track at impacts (lowest
    points) and checks that each rebound peaks no higher than the one before."""
    pts = sorted(points)
    if len(pts) < 2 * min_points_per_segment:
        return BounceCheck("insufficient_data", ("too few tracked frames for a bounce check",), (), ())
    ys = [p[2] for p in pts]
    floor = max(ys)
    span = floor - min(ys)
    if span <= 0:
        return BounceCheck("insufficient_data", ("object does not move vertically",), (), ())
    # impacts: local maxima of y close to the floor
    impacts = [i for i in range(1, len(ys) - 1)
               if ys[i] >= ys[i - 1] and ys[i] >= ys[i + 1] and floor - ys[i] < 0.1 * span]
    merged: list[int] = []
    for i in impacts:
        if merged and i - merged[-1] < min_points_per_segment:
            if ys[i] > ys[merged[-1]]:
                merged[-1] = i
        else:
            merged.append(i)
    bounds = [0, *merged, len(ys) - 1]
    heights = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a + 1 >= min_points_per_segment:
            heights.append(floor - min(ys[a:b + 1]))
    if len(heights) < 2:
        return BounceCheck("insufficient_data", ("fewer than two flight segments",), tuple(heights), ())
    e = tuple(math.sqrt(h1 / h0) if h0 > 0 else math.inf for h0, h1 in zip(heights, heights[1:]))
    reasons = tuple(
        f"rebound {k + 1} peaks {h1 / h0:.2f}x the previous height"
        for k, (h0, h1) in enumerate(zip(heights, heights[1:])) if h1 > h0 * (1 + tolerance)
    )
    return BounceCheck("inconsistent" if reasons else "consistent", reasons, tuple(heights), e)


# Surface gravity in m/s^2, used only to put an apparent g into words a viewer can picture.
# Venus, Saturn and Neptune are left out: they sit within measurement error of Earth.
BODIES = (("Pluto", 0.62), ("Moon", 1.62), ("Mars", 3.71), ("Earth", 9.81), ("Jupiter", 24.79))


def nearest_body(g_m_s2: float) -> tuple[str, float]:
    """The body whose surface gravity is closest to g on a log scale, and g as a multiple of Earth's."""
    if g_m_s2 <= 0:
        raise PhysicsInputError("g must be positive")
    name = min(BODIES, key=lambda b: abs(math.log(g_m_s2 / b[1])))[0]
    return name, g_m_s2 / G


def ghost_track(fit: FlightFit, times: list[float], m_per_px: float) -> list[tuple[float, float, float]]:
    """Where the object would be at each time if it left the same point with the same velocity but
    fell at exactly G straight down the image. Drawn next to the real track it shows the gap between
    what the clip shows and what constant-g flight predicts. Needs a user-confirmed scale."""
    if m_per_px <= 0:
        raise PhysicsInputError("m_per_px must be positive")
    a = G / m_per_px
    out = []
    for t in times:
        dt = t - fit.t0_s
        out.append((t, fit.x0_px + fit.vx_px_s * dt, fit.y0_px + fit.vy_px_s * dt + 0.5 * a * dt * dt))
    return out
