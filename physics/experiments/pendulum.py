"""Simple pendulum seen side-on by a fixed camera.

Small-angle model: T = 2*pi*sqrt(L/g), independent of amplitude. The period is measured from the
bob's horizontal position alone, so no pixel scale is needed; the user-confirmed length (if given)
is compared with the length the measured period implies.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..errors import PhysicsInputError

G = 9.81


def periods_from_track(times: list[float], xs: list[float]) -> list[float]:
    """Full periods between successive upward crossings of the mean x (linear interpolation)."""
    if len(times) != len(xs) or len(times) < 8:
        raise PhysicsInputError("need at least 8 tracked frames with matching times")
    mean = sum(xs) / len(xs)
    crossings = []
    for (t0, x0), (t1, x1) in zip(zip(times, xs), zip(times[1:], xs[1:])):
        if x0 < mean <= x1 and x1 != x0:
            crossings.append(t0 + (mean - x0) / (x1 - x0) * (t1 - t0))
    return [b - a for a, b in zip(crossings, crossings[1:])]


@dataclass(frozen=True)
class PendulumCheck:
    verdict: str  # "consistent" | "inconsistent" | "insufficient_data"
    reasons: tuple[str, ...]
    period_s: float | None
    period_spread: float | None  # (max - min) / mean over measured periods
    implied_length_m: float | None
    predicted_period_s: float | None  # from the user-confirmed length


def check_pendulum(times: list[float], xs: list[float], *, length_m: float | None = None,
                   tolerance: float = 0.1) -> PendulumCheck:
    if length_m is not None and length_m <= 0:
        raise PhysicsInputError("length_m must be positive")
    periods = periods_from_track(times, xs)
    if len(periods) < 2:
        return PendulumCheck("insufficient_data", ("fewer than two full swings tracked",), None, None, None, None)
    T = sum(periods) / len(periods)
    spread = (max(periods) - min(periods)) / T
    implied = G * T * T / (4 * math.pi ** 2)
    reasons = []
    if spread > tolerance:
        reasons.append(f"period varies by {spread:.0%} between swings")
    pred = None
    if length_m is not None:
        pred = 2 * math.pi * math.sqrt(length_m / G)
        if abs(T - pred) > tolerance * pred:
            reasons.append(f"measured period {T:.2f} s vs {pred:.2f} s expected for the confirmed length")
    return PendulumCheck("inconsistent" if reasons else "consistent", tuple(reasons), T, spread, implied, pred)
