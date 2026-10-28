"""Constant-acceleration fit s(t) = s0 + v0*t + 0.5*a*t^2 on usable samples after release."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .errors import PhysicsInputError
from .tracking import Sample

MIN_POINTS = 6


@dataclass(frozen=True)
class FitResult:
    a_m_s2: float
    v0_m_s: float
    s0_m: float
    a_stderr: float
    v0_stderr: float
    s0_stderr: float
    rms_residual_m: float
    n: int
    t_span_s: float


def fit_constant_acceleration(samples: list[Sample], t0_s: float) -> FitResult:
    """t0_s is the confirmed release time; samples before it are ignored."""
    pts = [(s.t_s - t0_s, s.s_m) for s in samples if s.usable and s.t_s >= t0_s]
    if len(pts) < MIN_POINTS:
        raise PhysicsInputError(f"need at least {MIN_POINTS} usable samples after release, got {len(pts)}")
    t = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    span = float(t.max() - t.min())
    if span <= 0:
        raise PhysicsInputError("usable samples cover zero time span")
    X = np.column_stack([np.ones_like(t), t, 0.5 * t**2])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    dof = max(len(t) - 3, 1)
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    return FitResult(
        a_m_s2=float(coef[2]),
        v0_m_s=float(coef[1]),
        s0_m=float(coef[0]),
        a_stderr=float(se[2]),
        v0_stderr=float(se[1]),
        s0_stderr=float(se[0]),
        rms_residual_m=float(np.sqrt(np.mean(resid**2))),
        n=len(t),
        t_span_s=span,
    )
