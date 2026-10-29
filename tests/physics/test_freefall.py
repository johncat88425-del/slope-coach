import math

import pytest

from physics.errors import PhysicsInputError
from physics.experiments.freefall import G, check_flight, fit_flight

M_PER_PX = 0.002  # 500 px == 1 m


def throw(g=G, vx=1.0, vy=-2.0, fps=60, n=40, wobble=0.0, tilt_deg=0.0):
    """Projectile in metres, converted to image pixels (y down)."""
    ga = math.radians(tilt_deg)
    pts = []
    for i in range(n):
        t = i / fps
        x = vx * t + 0.5 * g * math.sin(ga) * t * t
        y = vy * t + 0.5 * g * math.cos(ga) * t * t + wobble * math.sin(40 * t)
        pts.append((t, 100 + x / M_PER_PX, 100 + y / M_PER_PX))
    return pts


def test_real_throw_is_consistent_and_recovers_g():
    fit = fit_flight(throw())
    check = check_flight(fit, m_per_px=M_PER_PX, object_size_px=120)
    assert check.verdict == "consistent"
    assert check.g_apparent_m_s2 == pytest.approx(G, rel=1e-6)
    assert check.implied_m_per_px == pytest.approx(M_PER_PX, rel=1e-6)
    assert check.implied_object_size_m == pytest.approx(0.24, rel=1e-6)
    assert check.implied_time_factor == pytest.approx(1.0, rel=1e-6)


def test_slow_motion_is_flagged_with_time_factor():
    fit = fit_flight(throw(g=G / 4))
    check = check_flight(fit, m_per_px=M_PER_PX)
    assert check.verdict == "inconsistent"
    assert check.implied_time_factor == pytest.approx(2.0, rel=1e-6)


def test_without_scale_gives_implied_size_only():
    check = check_flight(fit_flight(throw()), object_size_px=120)
    assert check.g_apparent_m_s2 is None and check.verdict == "consistent"
    assert check.implied_object_size_m == pytest.approx(0.24, rel=1e-6)


def test_sideways_gravity_and_wobbly_path_are_flagged():
    assert "image-down" in check_flight(fit_flight(throw(tilt_deg=40))).reasons[0]
    wobbly = check_flight(fit_flight(throw(wobble=0.05)))
    assert any("constant-acceleration" in r for r in wobbly.reasons)


def test_refuses_without_enough_data():
    with pytest.raises(PhysicsInputError):
        fit_flight(throw(n=5))
    still = [(i / 30, 10.0, 10.0 + 0.01 * (-1) ** i) for i in range(10)]
    assert check_flight(fit_flight(still)).verdict == "insufficient_data"
    with pytest.raises(PhysicsInputError):
        check_flight(fit_flight(throw()), m_per_px=0)


def test_ghost_matches_real_flight_and_diverges_on_slow_motion():
    from physics.experiments.freefall import ghost_track, nearest_body
    m = 0.003
    def pts(g):
        return [(i / 60, 40 + 300 * i / 60, 300 - 600 * i / 60 + 0.5 * (g / m) * (i / 60) ** 2) for i in range(40)]
    real = pts(9.81)
    fit = fit_flight(real)
    ghost = ghost_track(fit, [p[0] for p in real], m)
    assert max(abs(g[2] - p[2]) for g, p in zip(ghost, real)) < 1.0
    slow = pts(9.81 / 4)
    ghost = ghost_track(fit_flight(slow), [p[0] for p in slow], m)
    assert abs(ghost[-1][2] - slow[-1][2]) > 100
    assert nearest_body(1.7)[0] == "Moon" and nearest_body(9.5)[0] == "Earth"
    assert nearest_body(3.0)[0] == "Mars"


def test_suggest_flight_windows_splits_at_bounce_and_skips_hand_motion():
    from physics.experiments.freefall import suggest_flight_windows

    pts = []
    for i in range(10):  # held in the hand: moves sideways at constant speed, no fall
        pts.append((i / 60, 10 + i * 2.0, 100 + (i % 3) * 3.0))
    for i in range(30):  # flight 1, lands at y = 300
        t = i / 60
        pts.append((10 / 60 + t, 30 + 200 * t, 300 - 400 * t + 0.5 * 2700 * t * t))
    t1 = 40 / 60
    for i in range(1, 25):  # flight 2 after the bounce
        t = i / 60
        pts.append((t1 + t, 30 + 200 * (30 / 60) + 200 * t, pts[39][2] - 300 * t + 0.5 * 2700 * t * t))
    wins = suggest_flight_windows(pts)
    assert len(wins) >= 2
    assert abs(wins[0][0] - 10 / 60) < 0.05 and abs(wins[0][1] - (10 + 29) / 60) < 0.05
    assert wins == sorted(wins)
    assert suggest_flight_windows(pts[:5]) == []
