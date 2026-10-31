import math

import pytest

from physics.errors import PhysicsInputError
from physics.experiments.vehicle import TYPICAL_LENGTH_M, car_length_px, check_drive, fit_drive, length_range_for

L_PX = 120.0  # car drawn 120 px long; a 4.5 m car makes 1 px = 3.75 cm


def drive(v_m_s=13.9, a_m_s2=0.0, car_m=4.5, fps=30, seconds=2.0, tilt_deg=2.0, wobble_px=0.0, start=40.0):
    """Car centre crossing the frame left to right, on a road tilted tilt_deg in the image."""
    k = L_PX / car_m
    c, s = math.cos(math.radians(tilt_deg)), math.sin(math.radians(tilt_deg))
    pts = []
    for i in range(int(seconds * fps)):
        t = i / fps
        d = k * (v_m_s * t + 0.5 * a_m_s2 * t * t)
        side = wobble_px * (1 if i % 2 else -1)
        pts.append((t, start + d * c - side * s, 300 + d * s + side * c))
    return pts


def widths(n, partial=3):
    """Whole car most of the time, cut by the frame edge in the first few frames."""
    return [L_PX * (i + 1) / (partial + 1) for i in range(partial)] + [L_PX + (i % 3 - 1) for i in range(n - partial)]


def test_car_length_ignores_frames_cut_by_the_edge_or_merged_with_a_shadow():
    assert car_length_px(widths(30)) == pytest.approx(L_PX, abs=1)
    assert car_length_px(widths(30) + [2 * L_PX] * 5) == pytest.approx(L_PX, abs=1)
    with pytest.raises(PhysicsInputError):
        car_length_px([L_PX * (1 + 0.05 * i) for i in range(30)])  # keeps growing: not a usable ruler


def test_steady_50_kmh_car_is_consistent_and_speed_recovered():
    pts = drive()
    c = check_drive(fit_drive(pts), widths(len(pts)), car_length_m=4.5)
    assert c.verdict == "consistent", c.reasons
    assert c.speed_m_s == pytest.approx(13.9, rel=0.02)
    assert c.accel_g == pytest.approx(0.0, abs=0.02)
    assert c.speed_lengths_s == pytest.approx(13.9 / 4.5, rel=0.02)


def test_hard_braking_at_0_9_g_is_still_a_car():
    pts = drive(v_m_s=20.0, a_m_s2=-0.9 * 9.81, seconds=1.5)
    c = check_drive(fit_drive(pts), widths(len(pts)), car_length_m=4.5)
    assert c.verdict == "consistent", c.reasons
    assert c.accel_g == pytest.approx(0.9, rel=0.03) and c.accel_m_s2 < 0


def test_3_g_launch_is_inconsistent_with_tyres():
    pts = drive(v_m_s=2.0, a_m_s2=3 * 9.81, seconds=1.0)
    c = check_drive(fit_drive(pts), widths(len(pts)), car_length_m=4.5)
    assert c.verdict == "inconsistent" and "3.0 g" in c.reasons[0]


def test_without_length_judges_only_when_3_and_6_m_agree():
    pts = drive(v_m_s=2.0, a_m_s2=3 * 9.81, seconds=1.0)
    assert check_drive(fit_drive(pts), widths(len(pts))).verdict == "inconsistent"
    pts = drive()
    assert check_drive(fit_drive(pts), widths(len(pts))).verdict == "consistent"
    pts = drive(v_m_s=2.0, a_m_s2=1.0 * 9.81, seconds=1.5)  # 1 g at 4.5 m: 0.67 g at 3 m, 1.33 g at 6 m
    c = check_drive(fit_drive(pts), widths(len(pts)))
    assert c.verdict == "insufficient_data"
    assert c.length_for_max_accel_m == pytest.approx(4.5 * 1.2, rel=0.03)



def test_confirmed_vehicle_class_narrows_the_length_range():
    pts = drive(v_m_s=2.0, a_m_s2=1.0 * 9.81, seconds=1.5)  # undecided with 3-6 m (test above)
    c = check_drive(fit_drive(pts), widths(len(pts)), vehicle_class="sedan")  # 4.6-5.0 m: 1.02-1.11 g
    assert c.verdict == "consistent" and c.length_range_m == (4.6, 5.0)
    assert c.speed_m_s is None  # still no single metre value without an exact length
    pts = drive(v_m_s=2.0, a_m_s2=1.15 * 9.81, seconds=1.5)  # a pickup (5.3 m or more) would need 1.35 g
    c = check_drive(fit_drive(pts), widths(len(pts)), vehicle_class="pickup")
    assert c.verdict == "inconsistent" and "5.3 m" in c.reasons[0]
    assert length_range_for("unknown") == length_range_for(None) == TYPICAL_LENGTH_M
    assert check_drive(fit_drive(pts), widths(len(pts)), car_length_m=4.5).length_range_m is None


def test_jittery_track_is_flagged():
    pts = drive(wobble_px=30.0)  # centre jumps a quarter of a car length every frame
    c = check_drive(fit_drive(pts), widths(len(pts)), car_length_m=4.5)
    assert c.verdict == "inconsistent" and "smooth" in c.reasons[0]


def test_refuses_short_tracks_and_bad_input():
    with pytest.raises(PhysicsInputError):
        fit_drive(drive()[:5])
    with pytest.raises(PhysicsInputError):
        fit_drive(drive(seconds=0.4))
    pts = drive(v_m_s=0.5)  # 1 m in 2 s: less than its own length
    with pytest.raises(PhysicsInputError):
        check_drive(fit_drive(pts), widths(len(pts)), car_length_m=4.5)
    with pytest.raises(PhysicsInputError):
        check_drive(fit_drive(drive()), widths(60), car_length_m=0)
