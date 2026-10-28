"""Object persistence along a track: does the tracked object vanish, change size abruptly or jump?

Works on raw per-frame detections (SAM masks or the gate's frame differencing) in pixels. It only
reports events with their times; deciding whether an event is a tracking error or something in the
video is left to a person looking at the overlay.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from .tracking import Detection


@dataclass(frozen=True)
class PersistenceEvent:
    kind: str  # "vanished" | "size_jump" | "position_jump"
    t_s: float
    detail: str


def persistence_events(
    detections: list[Detection],
    *,
    max_gap_frames: int = 2,
    size_ratio: float = 2.0,
    jump_factor: float = 4.0,
) -> list[PersistenceEvent]:
    """Gaps inside the track longer than max_gap_frames, mask area off the median by more than
    size_ratio, and steps longer than jump_factor times the median step. Gaps at the ends are ignored."""
    dets = sorted(detections, key=lambda d: d.t_s)
    seen = [i for i, d in enumerate(dets) if d.centroid_px is not None]
    if len(seen) < 3:
        return []
    events: list[PersistenceEvent] = []

    for a, b in zip(seen, seen[1:]):
        if b - a - 1 > max_gap_frames:
            events.append(PersistenceEvent(
                "vanished", dets[a + 1].t_s, f"missing for {b - a - 1} frames until t={dets[b].t_s:.3f}s"))

    areas = [dets[i].area_px for i in seen if dets[i].area_px]
    if areas:
        med = statistics.median(areas)
        for i in seen:
            ar = dets[i].area_px
            if ar and med > 0 and (ar > size_ratio * med or ar < med / size_ratio):
                events.append(PersistenceEvent("size_jump", dets[i].t_s, f"area {ar:.0f} px vs median {med:.0f} px"))

    steps = []
    for a, b in zip(seen, seen[1:]):
        (x0, y0), (x1, y1) = dets[a].centroid_px, dets[b].centroid_px
        steps.append(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / (b - a))
    med_step = statistics.median(steps)
    if med_step > 0:
        for (a, b), st in zip(zip(seen, seen[1:]), steps):
            if st > jump_factor * med_step:
                events.append(PersistenceEvent(
                    "position_jump", dets[b].t_s, f"step {st:.0f} px/frame vs median {med_step:.0f}"))
    return sorted(events, key=lambda e: e.t_s)


def size_trend(times: list[float], sizes: list[float]) -> float | None:
    """Relative change of object size over the track from a straight-line fit (end / start - 1).
    A large steady change means the object moves towards or away from the camera, which a 2D
    check cannot handle. None when there is too little data."""
    if len(times) < 3 or len(times) != len(sizes):
        return None
    n = len(times)
    mt, ms = sum(times) / n, sum(sizes) / n
    var = sum((t - mt) ** 2 for t in times)
    if var == 0 or ms <= 0:
        return None
    slope = sum((t - mt) * (z - ms) for t, z in zip(times, sizes)) / var
    start = ms + slope * (min(times) - mt)
    end = ms + slope * (max(times) - mt)
    if start <= 0:
        return None
    return end / start - 1
