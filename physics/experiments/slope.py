"""Slider on a straight incline with an effective kinetic friction parameter mu.

a = g (sin(theta) - mu cos(theta)). mu is an effective parameter for this rig,
estimated from baseline trials; it is not a material constant read from a photo.
Static friction (whether sliding starts) is out of scope: only trials that slide are analysed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..calibration import SlopeGeometry
from ..errors import PhysicsInputError

G = 9.81


def acceleration(geom: SlopeGeometry, mu: float, g: float = G) -> float:
    th = geom.angle_rad
    return g * (math.sin(th) - mu * math.cos(th))


def mu_from_acceleration(geom: SlopeGeometry, a: float, g: float = G) -> float:
    th = geom.angle_rad
    return (g * math.sin(th) - a) / (g * math.cos(th))


@dataclass(frozen=True)
class PredictedCurve:
    a_m_s2: float
    v0_m_s: float
    s0_m: float
    distance_m: float  # where the curve stops (end of the slide)
    t_end_s: float
    points: tuple[tuple[float, float], ...]  # (t since release, s)

    def s_at(self, t: float) -> float | None:
        if t < 0 or t > self.t_end_s:
            return None
        return self.s0_m + self.v0_m_s * t + 0.5 * self.a_m_s2 * t * t


def predict(
    geom: SlopeGeometry,
    mu: float,
    distance_m: float,
    *,
    v0_m_s: float = 0.0,
    s0_m: float = 0.0,
    dt: float = 1 / 30,
) -> PredictedCurve:
    """Predict s(t) from release until the slider has travelled distance_m. Never past the end."""
    if distance_m <= 0 or distance_m > geom.length_m:
        raise PhysicsInputError("distance_m must be in (0, slope length]")
    a = acceleration(geom, mu)
    t_end = time_to_distance(a, v0_m_s, distance_m)
    if t_end is None:
        raise PhysicsInputError(
            f"with mu={mu:.3f} the slider would not reach {distance_m} m (a={a:.3f} m/s^2); "
            "the kinetic model does not apply"
        )
    n = max(int(math.ceil(t_end / dt)), 1)
    pts = []
    for i in range(n + 1):
        t = min(i * dt, t_end)
        pts.append((t, s0_m + v0_m_s * t + 0.5 * a * t * t))
    return PredictedCurve(a, v0_m_s, s0_m, distance_m, t_end, tuple(pts))


def time_to_distance(a: float, v0: float, d: float) -> float | None:
    """Smallest t >= 0 with v0 t + a t^2 / 2 = d, or None if never reached."""
    if abs(a) < 1e-12:
        return d / v0 if v0 > 0 else None
    disc = v0 * v0 + 2 * a * d
    if disc < 0:
        return None
    roots = [(-v0 + math.sqrt(disc)) / a, (-v0 - math.sqrt(disc)) / a]
    pos = [r for r in roots if r >= 0]
    return min(pos) if pos else None
