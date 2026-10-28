"""Turn per-frame detections (from SAM or manual clicks) into quality-flagged s(t) samples."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum

from .calibration import Calibration


class Quality(str, Enum):
    OK = "ok"
    MISSING = "missing"  # target not detected in this frame
    AREA_JUMP = "area_jump"  # mask area far from the clip median
    POSITION_JUMP = "position_jump"  # implausible displacement between frames
    OFF_PATH = "off_path"  # too far from the confirmed path line


@dataclass(frozen=True)
class Detection:
    t_s: float  # media timestamp of the actual frame
    centroid_px: tuple[float, float] | None
    area_px: float | None = None
    source: str = "sam"  # "sam" | "manual"


@dataclass(frozen=True)
class Sample:
    t_s: float
    s_m: float | None
    quality: Quality
    source: str
    flags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def usable(self) -> bool:
        return self.quality is Quality.OK and self.s_m is not None


def to_samples(
    detections: list[Detection],
    calib: Calibration,
    *,
    max_speed_m_s: float = 5.0,
    off_path_tol_m: float = 0.03,
    area_tol: float = 0.5,
) -> list[Sample]:
    """Project detections onto the path and flag unusable frames. Never interpolates."""
    dets = sorted(detections, key=lambda d: d.t_s)
    areas = [d.area_px for d in dets if d.area_px]
    median_area = statistics.median(areas) if areas else None

    out: list[Sample] = []
    last_ok: tuple[float, float] | None = None  # (t, s)
    for d in dets:
        if d.centroid_px is None:
            out.append(Sample(d.t_s, None, Quality.MISSING, d.source))
            continue
        s, perp = calib.to_path(d.centroid_px)
        quality = Quality.OK
        if abs(perp) > off_path_tol_m:
            quality = Quality.OFF_PATH
        elif median_area and d.area_px and abs(d.area_px - median_area) > area_tol * median_area:
            quality = Quality.AREA_JUMP
        elif last_ok is not None:
            dt = d.t_s - last_ok[0]
            if dt > 0 and abs(s - last_ok[1]) / dt > max_speed_m_s:
                quality = Quality.POSITION_JUMP
        out.append(Sample(d.t_s, s, quality, d.source))
        if quality is Quality.OK:
            last_ok = (d.t_s, s)
    return out


def usable_fraction(samples: list[Sample]) -> float:
    return sum(s.usable for s in samples) / len(samples) if samples else 0.0
