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
