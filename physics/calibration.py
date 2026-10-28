"""Pixel-to-metre calibration along a confirmed slope path (near side-on view only)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import PhysicsInputError

Point = tuple[float, float]


@dataclass(frozen=True)
class SlopeGeometry:
    length_m: float  # along the slope surface, L
    height_m: float  # vertical rise, h

    def __post_init__(self) -> None:
        for name, v in (("length_m", self.length_m), ("height_m", self.height_m)):
            if not math.isfinite(v) or v <= 0:
                raise PhysicsInputError(f"{name} must be a positive number of metres, got {v}")
        if self.height_m >= self.length_m:
            raise PhysicsInputError(
                f"height_m ({self.height_m}) must be smaller than length_m ({self.length_m})"
            )

    @property
    def angle_rad(self) -> float:
        return math.asin(self.height_m / self.length_m)


@dataclass(frozen=True)
class Calibration:
    """Maps image pixels to metres along the slope path.

    ruler_px: two pixel points the user clicked on the ruler ends.
    ruler_length_m: the real distance between those points.
    path_start_px / path_end_px: user-confirmed start and end of the slider path.
    """

    ruler_px: tuple[Point, Point]
    ruler_length_m: float
    path_start_px: Point
    path_end_px: Point

    def __post_init__(self) -> None:
        if not math.isfinite(self.ruler_length_m) or self.ruler_length_m <= 0:
            raise PhysicsInputError("ruler_length_m must be a positive number of metres")
        if _dist(*self.ruler_px) < 10:
            raise PhysicsInputError("ruler points are less than 10 px apart; click the ruler ends again")
        if _dist(self.path_start_px, self.path_end_px) < 10:
            raise PhysicsInputError("path start and end are less than 10 px apart")

    @property
    def m_per_px(self) -> float:
        return self.ruler_length_m / _dist(*self.ruler_px)

    @property
    def path_unit(self) -> Point:
        (x0, y0), (x1, y1) = self.path_start_px, self.path_end_px
        d = _dist(self.path_start_px, self.path_end_px)
        return ((x1 - x0) / d, (y1 - y0) / d)

    @property
    def path_length_m(self) -> float:
        return _dist(self.path_start_px, self.path_end_px) * self.m_per_px

    def to_path(self, p: Point) -> tuple[float, float]:
        """Return (s_m along the path from start, perpendicular offset in metres)."""
        ux, uy = self.path_unit
        dx, dy = p[0] - self.path_start_px[0], p[1] - self.path_start_px[1]
        along = (dx * ux + dy * uy) * self.m_per_px
        perp = (-dx * uy + dy * ux) * self.m_per_px
        return along, perp

    def to_pixels(self, s_m: float) -> Point:
        """Inverse of to_path for points on the path; used for the video overlay."""
        ux, uy = self.path_unit
        d_px = s_m / self.m_per_px
        return (self.path_start_px[0] + ux * d_px, self.path_start_px[1] + uy * d_px)


def _dist(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])
