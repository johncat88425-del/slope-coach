import math

import pytest

from physics.calibration import Calibration, SlopeGeometry
from physics.errors import PhysicsInputError
from tests.physics.helpers import CALIB


def test_angle_from_height_and_length():
    g = SlopeGeometry(length_m=1.0, height_m=0.5)
    assert math.isclose(g.angle_rad, math.pi / 6)


@pytest.mark.parametrize("L,h", [(1.0, 1.0), (1.0, 1.2), (0, 0.1), (1.0, 0), (-1, 0.2), (1.0, float("nan"))])
def test_invalid_geometry_rejected(L, h):
    with pytest.raises(PhysicsInputError):
        SlopeGeometry(length_m=L, height_m=h)


def test_pixel_to_path_roundtrip():
    s, perp = CALIB.to_path((600, 500))
    assert math.isclose(s, 0.5) and math.isclose(perp, 0.0, abs_tol=1e-12)
    x, y = CALIB.to_pixels(0.5)
    assert math.isclose(x, 600) and math.isclose(y, 500)


def test_perpendicular_offset_in_metres():
    _, perp = CALIB.to_path((600, 520))
    assert math.isclose(abs(perp), 0.02)


def test_degenerate_clicks_rejected():
    with pytest.raises(PhysicsInputError):
        Calibration(((0, 0), (3, 0)), 1.0, (0, 0), (100, 0))
    with pytest.raises(PhysicsInputError):
        Calibration(((0, 0), (100, 0)), 0.0, (0, 0), (100, 0))
