"""T15: the system must say what it cannot judge instead of guessing (PLAN section 25)."""
from physics.compare import Verdict, compare
from physics.diagnose import CheckType, evidence_for_next_check
from physics.experiments import slope
from physics.tracking import Detection, Quality, to_samples
from tests.physics.helpers import CALIB, GEOM, synthetic_detections

MU = 0.15


def _pred():
    return slope.predict(GEOM, MU, distance_m=0.8)


def _key_ok(c):
    return any(ch.name == "key_segment" and ch.passed for ch in c.checks)


def test_occluded_start_blocks_release_judgement():
    a = slope.acceleration(GEOM, MU)
    dets = synthetic_detections(a=a, v0=0.6, duration=2.0)
    # hand covers the slider from release until it has moved 25 cm
    dets = [Detection(d.t_s, None) if d.t_s >= 0.5 and d.centroid_px[0] - 100 < 300 else d for d in dets]
    c = compare(_pred(), to_samples(dets, CALIB), t0_s=0.5, calibration_ok=True)
    assert not _key_ok(c)
    assert any("release speed" in s for s in c.can_still_say)
    kinds = {e.candidate for e in evidence_for_next_check(c, _pred(), None, key_segment_ok=_key_ok(c))}
    assert CheckType.RELEASE_CHECK not in kinds


def test_high_tracking_ratio_but_missing_start_still_refuses_v0():
    a = slope.acceleration(GEOM, MU)
    dets = synthetic_detections(a=a, v0=0.6, duration=2.0, s0=0.05)
    first_moving = [i for i, d in enumerate(dets) if d.t_s >= 0.5][:5]
    for i in first_moving:
        dets[i] = Detection(dets[i].t_s, None)
    samples = to_samples(dets, CALIB)
    usable = sum(s.usable for s in samples) / len(samples)
    assert usable > 0.8  # most frames are fine...
    c = compare(_pred(), samples, t0_s=0.5, calibration_ok=True)
    assert not _key_ok(c)  # ...but the part needed for the release speed is missing


def test_jumpy_tracking_is_not_used_as_data():
    a = slope.acceleration(GEOM, MU)
    dets = synthetic_detections(a=a, duration=2.0)
    for i in range(20, len(dets), 3):
        x, y = dets[i].centroid_px
        dets[i] = Detection(dets[i].t_s, (x, y + 80), area_px=400)  # 8 cm off the path
    samples = to_samples(dets, CALIB)
    assert sum(s.quality is Quality.OFF_PATH for s in samples) >= 5
    c = compare(_pred(), samples, t0_s=0.5, calibration_ok=True)
    assert c.verdict is Verdict.CONSISTENT  # flagged frames are excluded, not averaged in


def test_slider_that_never_moves_is_insufficient():
    still = [Detection(i / 30, (150, 500), area_px=400) for i in range(45)]
    c = compare(_pred(), to_samples(still, CALIB), t0_s=0.5, calibration_ok=True)
    assert c.verdict in (Verdict.INSUFFICIENT_DATA, Verdict.DISCREPANCY)
    assert evidence_for_next_check(c, _pred(), None, key_segment_ok=_key_ok(c)) == [] or c.verdict is Verdict.DISCREPANCY
