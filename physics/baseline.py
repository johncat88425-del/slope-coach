"""Estimate the rig's effective mu from repeated baseline trials. Locked before any test trial."""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from .calibration import SlopeGeometry
from .errors import PhysicsInputError
from .experiments import slope
from .fit import FitResult

MIN_BASELINE_TRIALS = 3


@dataclass(frozen=True)
class BaselineEstimate:
    mu_eff: float
    mu_spread: float  # sample standard deviation across trials
    accel_mean_m_s2: float
    accel_spread_m_s2: float
    n_trials: int


def estimate_baseline(geom: SlopeGeometry, fits: list[FitResult]) -> BaselineEstimate:
    if len(fits) < MIN_BASELINE_TRIALS:
        raise PhysicsInputError(f"need {MIN_BASELINE_TRIALS} usable baseline trials, got {len(fits)}")
    accels = [f.a_m_s2 for f in fits]
    if any(a <= 0 for a in accels):
        raise PhysicsInputError("a baseline trial did not accelerate down the slope; re-record it")
    mus = [slope.mu_from_acceleration(geom, a) for a in accels]
    return BaselineEstimate(
        mu_eff=statistics.mean(mus),
        mu_spread=statistics.stdev(mus),
        accel_mean_m_s2=statistics.mean(accels),
        accel_spread_m_s2=statistics.stdev(accels),
        n_trials=len(fits),
    )
