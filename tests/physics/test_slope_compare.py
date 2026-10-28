import math

import pytest

from physics.baseline import estimate_baseline
from physics.compare import Verdict, compare
from physics.diagnose import CheckType, evidence_for_next_check
from physics.errors import PhysicsInputError
from physics.experiments import slope
from physics.fit import fit_constant_acceleration
from physics.tracking import to_samples
from tests.physics.helpers import CALIB, GEOM, synthetic_detections

MU = 0.15


def _pred():
    return slope.predict(GEOM, MU, distance_m=0.8)


def test_mu_roundtrip():
    a = slope.acceleration(GEOM, MU)
    assert math.isclose(slope.mu_from_acceleration(GEOM, a), MU)


def test_prediction_stops_at_distance():
    p = _pred()
    t_last, s_last = p.points[-1]
    assert math.isclose(s_last, 0.8) and math.isclose(t_last, p.t_end_s)
    assert p.s_at(p.t_end_s + 0.1) is None


def test_prediction_refuses_when_slider_would_not_reach():
    with pytest.raises(PhysicsInputError):
        slope.predict(GEOM, mu=0.5, distance_m=0.8)  # a < 0


def test_baseline_needs_three_trials():
    fits = [fit_constant_acceleration(to_samples(synthetic_detections(a=a), CALIB), 0.5) for a in (1.5, 1.52, 1.48)]
    b = estimate_baseline(GEOM, fits)
    assert b.n_trials == 3 and b.mu_spread > 0
    with pytest.raises(PhysicsInputError):
        estimate_baseline(GEOM, fits[:2])


def test_matching_trial_is_consistent():
    a = slope.acceleration(GEOM, MU)
    samples = to_samples(synthetic_detections(a=a, duration=2.0), CALIB)
    c = compare(_pred(), samples, t0_s=0.5, calibration_ok=True)
    assert c.verdict is Verdict.CONSISTENT
    assert abs(c.arrival_error_rel) < 1e-6


def test_pushed_release_points_to_release_check():
    a = slope.acceleration(GEOM, MU)
    samples = to_samples(synthetic_detections(a=a, v0=0.6, duration=2.0), CALIB)
    c = compare(_pred(), samples, t0_s=0.5, calibration_ok=True)
    assert c.verdict is Verdict.DISCREPANCY
    ev = evidence_for_next_check(c, _pred(), None, key_segment_ok=True)
    assert CheckType.RELEASE_CHECK in {e.candidate for e in ev}


def test_wrong_height_points_to_dimension_check():
    true_geom = slope.SlopeGeometry(length_m=1.0, height_m=0.4)  # user typed 0.3
    a = slope.acceleration(true_geom, MU)
    samples = to_samples(synthetic_detections(a=a, duration=2.0, noise=[0.0005, -0.0005]), CALIB)
    c = compare(_pred(), samples, t0_s=0.5, calibration_ok=True)
    assert c.verdict is Verdict.DISCREPANCY
    ev = evidence_for_next_check(c, _pred(), None, key_segment_ok=True)
    kinds = {e.candidate for e in ev}
    assert CheckType.DIMENSION_CHECK in kinds and CheckType.RELEASE_CHECK not in kinds


def test_missing_release_time_refuses():
    a = slope.acceleration(GEOM, MU)
    samples = to_samples(synthetic_detections(a=a, duration=2.0), CALIB)
    c = compare(_pred(), samples, t0_s=None, calibration_ok=True)
    assert c.verdict is Verdict.INSUFFICIENT_DATA
    assert evidence_for_next_check(c, _pred(), None, key_segment_ok=True) == []
