"""MetaHooks: backend ModelHooks implemented with meta_client (T05).

Wire it in at startup with::

    from backend.model_hooks import set_hooks
    from meta_client.hooks import MetaHooks

    set_hooks(MetaHooks())

SAM failures surface as backend.model_hooks.TrackingUnavailable so the API
keeps its documented 501 ("upload detections manually") behavior.
"""
from __future__ import annotations

from pathlib import Path

from backend.model_hooks import ModelHooks, TrackingUnavailable
from backend.schemas import (
    AuditInterview,
    AuditQuestion,
    DetectionIn,
    ReleaseSuggestion,
    SceneCheck,
)

from . import explain as _explain
from . import headline as _headline
from . import interview as _interview
from . import sam as _sam
from . import spark as _spark
from .exceptions import MetaClientError, ModelOutputError


def _dense_detections(
    result: _sam.TrackResult, t_base: float, *, normalized: bool = False
) -> list[DetectionIn]:
    """Dense timeline: every frame gets an entry; absent frames are explicit
    missing markers (centroid None), never interpolated. With normalized,
    centroids are 0..1 fractions and area is a fraction of the frame (the
    audit contract, API v0.5); otherwise source pixels (the slope flow)."""
    main = _sam.select_main_track(result.detections)
    by_frame = {d.frame: d for d in result.detections if d.object_id == main}
    detections = []
    for frame in range(result.n_frames):
        det = by_frame.get(frame)
        if det is None or det.centroid_px is None:
            detections.append(
                DetectionIn(t_s=t_base + frame / result.fps, centroid_px=None, source="sam")
            )
        else:
            cx, cy = det.centroid_px
            area = det.area_px
            if normalized:
                fw, fh = det.frame_size
                cx, cy, area = cx / fw, cy / fh, area / (fw * fh)
            detections.append(
                DetectionIn(t_s=det.t_s, centroid_px=(cx, cy), area_px=area, source="sam")
            )
    return detections


class MetaHooks(ModelHooks):
    def check_scene(self, photo_path: Path) -> SceneCheck:
        result = _spark.describe_scene(photo_path)
        return SceneCheck(source="model", **result)

    def track_slider(self, video_path: Path, text_prompt: str) -> list[DetectionIn]:
        try:
            result = _sam.track(video_path, text_prompt)
        except MetaClientError as exc:
            raise TrackingUnavailable(str(exc)) from exc
        return _dense_detections(result, 0.0)

    def track_object(
        self, video_path: Path, text_prompt: str, t_start: float, t_end: float
    ) -> list[DetectionIn]:
        try:
            result = _sam.track(video_path, text_prompt, t_start=t_start, t_end=t_end)
        except MetaClientError as exc:
            raise TrackingUnavailable(str(exc)) from exc
        return _dense_detections(result, t_start, normalized=True)

    def suggest_release_time(self, video_path: Path) -> ReleaseSuggestion:
        result = _spark.suggest_release_time(video_path)
        return ReleaseSuggestion(source="model", **result)

    def interview_audit(self, video_path: Path) -> AuditInterview:
        result = _interview.interview_audit(video_path)
        return AuditInterview(
            source="model",
            questions=[AuditQuestion(**q) for q in result["questions"]],
            note=None,
        )

    def explain_audit(self, audit: dict) -> str | None:
        """Plain-language explanation via Spark (T112); None keeps the fixed template."""
        try:
            return _explain.explain_result(audit, kind="audit")["explanation"]
        except ModelOutputError:
            return None

    def headline_audit(self, audit: dict) -> str | None:
        """One-line headline via Spark (T112); None shows no headline."""
        result = _headline.write_headline(audit)
        return result["headline"] if result else None
