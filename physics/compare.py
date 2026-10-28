"""Compare a locked prediction with a measured trial, and decide what can and cannot be said."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from .baseline import BaselineEstimate
from .errors import PhysicsInputError
from .experiments.slope import PredictedCurve, time_to_distance
from .fit import FitResult, fit_constant_acceleration
from .tracking import Sample, usable_fraction

MIN_USABLE_FRACTION = 0.8
KEY_SEGMENT_FRACTION = 0.2  # first 20% of the predicted travel: needed to judge release speed
MIN_KEY_SEGMENT_POINTS = 3
MAX_FIT_RMS_M = 0.01
DEFAULT_TOLERANCE_REL = 0.15


class Verdict(str, Enum):
    CONSISTENT = "consistent"
    DISCREPANCY = "discrepancy"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str
    blocking: bool = True


@dataclass(frozen=True)
class Comparison:
    verdict: Verdict
    checks: tuple[Check, ...]
    fit: FitResult | None = None
    predicted_arrival_s: float | None = None
    observed_arrival_s: float | None = None
    arrival_error_rel: float | None = None
    tolerance_rel: float = DEFAULT_TOLERANCE_REL
    residuals: tuple[tuple[float, float], ...] = field(default_factory=tuple)  # (t since release, obs - pred)
    can_still_say: tuple[str, ...] = field(default_factory=tuple)


def compare(
    prediction: PredictedCurve,
    samples: list[Sample],
    *,
    t0_s: float | None,
    calibration_ok: bool,
    baseline: BaselineEstimate | None = None,
) -> Comparison:
    checks: list[Check] = []
    checks.append(Check("calibration", calibration_ok, "calibration confirmed" if calibration_ok else "calibration not confirmed"))
    checks.append(Check("release_time", t0_s is not None, "release time confirmed by user" if t0_s is not None else "release time not confirmed"))
    frac = usable_fraction(samples)
    checks.append(Check("usable_fraction", frac >= MIN_USABLE_FRACTION, f"{frac:.0%} of frames usable", blocking=False))

    fit: FitResult | None = None
    if t0_s is not None:
        try:
            fit = fit_constant_acceleration(samples, t0_s)
            checks.append(Check("observations", True, f"{fit.n} usable samples after release"))
        except PhysicsInputError as e:
            checks.append(Check("observations", False, str(e)))
    if fit is not None:
        checks.append(Check("fit_applicability", fit.rms_residual_m <= MAX_FIT_RMS_M,
                            f"rms residual {fit.rms_residual_m * 1000:.1f} mm (limit {MAX_FIT_RMS_M * 1000:.0f} mm)"))
        key_end = fit.s0_m + KEY_SEGMENT_FRACTION * prediction.distance_m
        key_pts = [s for s in samples if s.usable and s.t_s >= t0_s and s.s_m <= key_end]
        checks.append(Check("key_segment", len(key_pts) >= MIN_KEY_SEGMENT_POINTS,
                            f"{len(key_pts)} usable samples in the first {KEY_SEGMENT_FRACTION:.0%} of travel",
                            blocking=False))

    tol = DEFAULT_TOLERANCE_REL
    if baseline is not None and baseline.accel_mean_m_s2 > 0:
        # relative arrival-time spread is about half the relative acceleration spread
        tol = max(tol, 2 * 0.5 * baseline.accel_spread_m_s2 / baseline.accel_mean_m_s2)

    blocking_failed = [c for c in checks if c.blocking and not c.passed]
    if blocking_failed or fit is None:
        said = ["the prediction was saved before this trial and is unchanged"]
        if fit is not None and fit.rms_residual_m > MAX_FIT_RMS_M:
            said.append("the motion does not look like constant acceleration in this clip")
        return Comparison(Verdict.INSUFFICIENT_DATA, tuple(checks), fit, tolerance_rel=tol, can_still_say=tuple(said))

    t_pred = prediction.t_end_s
    t_obs = time_to_distance(fit.a_m_s2, fit.v0_m_s, prediction.distance_m)
    residuals = tuple(
        (s.t_s - t0_s, s.s_m - fit.s0_m - p)
        for s in samples
        if s.usable and s.t_s >= t0_s and (p := prediction.s_at(s.t_s - t0_s)) is not None
    )
    if t_obs is None:
        return Comparison(Verdict.DISCREPANCY, tuple(checks), fit, t_pred, None, None, tol, residuals,
                          ("the measured motion would not cover the predicted distance",))
    err = (t_obs - t_pred) / t_pred
    verdict = Verdict.DISCREPANCY if abs(err) > tol else Verdict.CONSISTENT
    return Comparison(verdict, tuple(checks), fit, t_pred, t_obs, err, tol, residuals)


def rel(a: float, b: float) -> float:
    return (a - b) / b if b else math.inf
