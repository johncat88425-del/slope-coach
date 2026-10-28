import math

import pytest

from physics.errors import PhysicsInputError
from physics.fit import fit_constant_acceleration
from physics.tracking import Detection, Quality, to_samples, usable_fraction
from tests.physics.helpers import CALIB, synthetic_detections


def test_fit_recovers_parameters():
    samples = to_samples(synthetic_detections(a=1.2, v0=0.1), CALIB)
    fit = fit_constant_acceleration(samples, t0_s=0.5)
    assert math.isclose(fit.a_m_s2, 1.2, rel_tol=1e-6)
    assert math.isclose(fit.v0_m_s, 0.1, abs_tol=1e-6)
    assert math.isclose(fit.s0_m, 0.05, abs_tol=1e-6)


def test_missing_frames_are_flagged_not_interpolated():
    dets = synthetic_detections(a=1.0)
    dets[20] = Detection(dets[20].t_s, None)
    samples = to_samples(dets, CALIB)
    assert samples[20].quality is Quality.MISSING and samples[20].s_m is None
    assert usable_fraction(samples) < 1.0


def test_position_jump_and_off_path_flagged():
    dets = synthetic_detections(a=1.0)
    t = dets[25].t_s
    dets[25] = Detection(t, (100 + 900, 500), area_px=400)  # teleports 0.9 m in one frame
    dets[26] = Detection(dets[26].t_s, (dets[26].centroid_px[0], 560), area_px=400)  # 6 cm off the path
    samples = to_samples(dets, CALIB)
    assert samples[25].quality is Quality.POSITION_JUMP
    assert samples[26].quality is Quality.OFF_PATH


def test_area_jump_flagged():
    dets = synthetic_detections(a=1.0)
    dets[10] = Detection(dets[10].t_s, dets[10].centroid_px, area_px=2000)
    assert to_samples(dets, CALIB)[10].quality is Quality.AREA_JUMP


def test_too_few_points_refused():
    samples = to_samples(synthetic_detections(a=1.0)[:18], CALIB)  # only 3 frames after release
    with pytest.raises(PhysicsInputError):
        fit_constant_acceleration(samples, t0_s=0.5)
