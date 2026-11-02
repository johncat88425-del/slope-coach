"""T251: a throw that also moves towards the camera is put back to one distance from the object's own size."""
import numpy as np
import pytest

from physics.depth import rescale_for_depth
from physics.errors import PhysicsInputError
from physics.experiments.freefall import check_flight, fit_flight

F, D, W, H = 900.0, 0.24, 1280, 720  # focal length px, ball diameter m, frame


def project(vz, size_noise=0.0, seed=0, g=9.81):
    rng = np.random.default_rng(seed)
    pts, sizes = [], []
    for t in np.arange(0, 0.8, 1 / 30):
        X, Y, Z = -1.0 + 2.0 * t, -0.3 - 3.5 * t + 0.5 * g * t * t, 4.0 + vz * t  # Y down, level camera
        pts.append((t, W / 2 + F * X / Z, H / 2 + F * Y / Z))
        sizes.append(F * D / Z * (1 + rng.normal(0, size_noise)))
    return pts, sizes


def g_of(points, size_px):
    return check_flight(fit_flight(points), m_per_px=D / size_px).g_apparent_m_s2


def test_motion_towards_the_camera_recovers_earth_g():
    pts, sizes = project(vz=-2.5, size_noise=0.03)
    assert sizes[-1] / sizes[0] > 1.5  # would have been refused as a >30% size change
    raw = g_of(pts, float(np.median(sizes)))
    dr = rescale_for_depth(pts, sizes, W, H)
    assert abs(raw - 9.81) > 0.8  # the uncorrected track is about 10% off
    assert g_of(list(dr.points), dr.ref_size_px) == pytest.approx(9.81, rel=0.08)


def test_slow_gravity_stays_slow_after_correction():
    pts, sizes = project(vz=2.0, size_noise=0.03, g=9.81 / 4)
    dr = rescale_for_depth(pts, sizes, W, H)
    assert g_of(list(dr.points), dr.ref_size_px) == pytest.approx(9.81 / 4, rel=0.1)


def test_noisy_or_too_few_sizes_are_refused():
    pts, sizes = project(vz=-2.5, size_noise=0.25)
    with pytest.raises(PhysicsInputError, match="jumps around"):
        rescale_for_depth(pts, sizes, W, H)
    with pytest.raises(PhysicsInputError):
        rescale_for_depth(pts[:4], sizes[:4], W, H)
