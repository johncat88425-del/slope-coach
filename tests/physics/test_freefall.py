import math

import pytest

from physics.errors import PhysicsInputError
from physics.experiments.freefall import G, check_flight, fit_flight, gravity_ruler

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
    # 10 cm wobble (rms ~3% of the path). T247 measures scatter against the path length; 5 cm (1.7%) was only
    # flagged before because start-to-end distance understated how far the ball moved.
    wobbly = check_flight(fit_flight(throw(wobble=0.1)))
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


def test_gravity_ruler_reads_metres_without_any_scale():
    # Thrown up at 2 m/s and sideways at 1 m/s; no ruler is given, g itself sets the scale.
    r = gravity_ruler(fit_flight(throw()))
    T = 39 / 60
    t_peak = 2.0 / G
    rise = 2.0 * t_peak - 0.5 * G * t_peak**2
    drop_end = -2.0 * T + 0.5 * G * T * T
    assert r.flight_time_s == pytest.approx(T)
    assert r.vertical_extent_m == pytest.approx(rise + drop_end, rel=1e-6)
    assert r.launch_speed_m_s == pytest.approx(math.sqrt(5), rel=1e-6)
    assert r.launch_angle_deg == pytest.approx(math.degrees(math.atan2(2, 1)), rel=1e-6)


def test_gravity_ruler_drop_from_rest_and_slow_motion_inflates_heights():
    r = gravity_ruler(fit_flight(throw(vx=0.0, vy=0.0)))
    assert r.vertical_extent_m == pytest.approx(0.5 * G * r.flight_time_s**2, rel=1e-6)
    # A 2x slow-motion clip of the same drop reads a 4x too large height: the assumption matters.
    slow = gravity_ruler(fit_flight([(2 * t, x, y) for t, x, y in throw(vx=0.0, vy=0.0)]))
    assert slow.vertical_extent_m == pytest.approx(4 * r.vertical_extent_m, rel=1e-6)



def test_scatter_is_judged_against_the_path_not_start_to_end():
    """T247: a full up-and-down toss ends near its start; a clean track of it must not fail the scatter check.
    Shaped like the real Pexels clip: ~130 px up and back down in 0.64 s, 3.6 px tracking noise."""
    import numpy as np
    rng = np.random.default_rng(0)
    a = 2 * 130 / 0.32 ** 2  # px/s^2: rises 130 px in 0.32 s, back down by 0.64 s
    v = -(2 * a * 130) ** 0.5
    pts = [(t, 300 + 60 * t + rng.normal(0, 3.6 / 2 ** 0.5), 400 + v * t + 0.5 * a * t * t + rng.normal(0, 3.6 / 2 ** 0.5))
           for t in np.arange(0, 0.645, 1 / 30)]
    fit = fit_flight(pts)
    chord = float(np.hypot(pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2]))
    assert fit.travel_px > 3 * chord
    assert check_flight(fit).verdict == "consistent"
