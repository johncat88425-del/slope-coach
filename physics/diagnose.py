"""Deterministic evidence for the two supported next checks. The model may only choose among these."""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .baseline import BaselineEstimate
from .compare import Comparison, Verdict
from .experiments.slope import PredictedCurve

MIN_V0_M_S = 0.05


class CheckType(str, Enum):
    DIMENSION_CHECK = "dimension_check"  # re-measure height and slope length
    RELEASE_CHECK = "release_check"  # repeat with a simple gate release, same angle and start


@dataclass(frozen=True)
class Evidence:
    candidate: CheckType
    finding: str  # what the numbers show, phrased as consistency, never as cause
    numbers: dict[str, float]
    cannot_distinguish: str


def evidence_for_next_check(
    comparison: Comparison,
    prediction: PredictedCurve,
    baseline: BaselineEstimate | None,
    key_segment_ok: bool,
) -> list[Evidence]:
    """Empty list means: current evidence is insufficient to suggest either check."""
    if comparison.verdict is not Verdict.DISCREPANCY or comparison.fit is None:
        return []
    fit = comparison.fit
    out: list[Evidence] = []

    if key_segment_ok and fit.v0_m_s > max(2 * fit.v0_stderr, MIN_V0_M_S):
        out.append(Evidence(
            CheckType.RELEASE_CHECK,
            "the fitted curve is consistent with a non-zero speed at release",
            {"v0_m_s": fit.v0_m_s, "v0_stderr": fit.v0_stderr},
            "a release-time offset can also look like an initial speed",
        ))

    spread = baseline.accel_spread_m_s2 if baseline else 0.0
    a_band = 2 * math.hypot(fit.a_stderr, spread)
    if abs(fit.a_m_s2 - prediction.a_m_s2) > a_band:
        out.append(Evidence(
            CheckType.DIMENSION_CHECK,
            "the measured acceleration differs from the predicted acceleration beyond the measurement band",
            {"a_measured": fit.a_m_s2, "a_predicted": prediction.a_m_s2, "band": a_band},
            "an angle error and a change in friction both change acceleration; this clip alone cannot tell them apart",
        ))
    return out
