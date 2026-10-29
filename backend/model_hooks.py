"""Where Meta model calls plug in. meta_client (Muse Code, T05/T11) provides the real implementation.

The backend only depends on this interface. The default MockHooks never calls a network
service, so the backend and frontend can be developed and tested without an API key.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .schemas import AuditInterview, AuditQuestion, DetectionIn, ReleaseSuggestion, SceneCheck


class TrackingUnavailable(RuntimeError):
    pass


class ModelHooks(Protocol):
    def check_scene(self, photo_path: Path) -> SceneCheck: ...
    def track_slider(self, video_path: Path, text_prompt: str) -> list[DetectionIn]: ...
    def suggest_release_time(self, video_path: Path) -> ReleaseSuggestion: ...
    def interview_audit(self, video_path: Path) -> AuditInterview: ...
    def track_object(self, video_path: Path, text_prompt: str, t_start: float, t_end: float) -> list[DetectionIn]:
        """SAM 3.1 track of one object between t_start and t_end (seconds of the clip).
        Coordinates are NORMALISED to the frame as it plays (after rotation): centroid x/width and
        y/height in 0..1, area as a fraction of width*height. One detection per frame, centroid None
        where the object is not found. Raise TrackingUnavailable when SAM is not connected."""
        ...
    # Optional (T143); the backend looks them up with getattr, so hooks without them still work.
    # Both get the finished audit (verdict, reasons, numbers) and return checked text or None.
    #   def explain_audit(self, audit: dict) -> str | None: ...   plain-language explanation
    #   def headline_audit(self, audit: dict) -> str | None: ...  one-line headline
    #   def suggest_object(self, video_path: Path) -> dict: ...     {object_name, camera_looks_static, reason, source}
    #   def answer_voice(self, audio_path: Path) -> dict: ...       {transcript, fields: {name: {value}}, source}


# Asked when no model is connected, or when the model's questions fail the output checks.
MOCK_QUESTIONS = [
    AuditQuestion(field="slow_motion", text="Was this clip recorded or played back in slow motion?"),
    AuditQuestion(field="camera_static", text="Did the camera stay completely still for the whole clip?"),
    AuditQuestion(field="object_size_m", text="Do you know the real size of the moving object? If so, enter its diameter."),
]


class MockHooks:
    def check_scene(self, photo_path: Path) -> SceneCheck:
        return SceneCheck(source="mock", needs_retake=False)

    def track_slider(self, video_path: Path, text_prompt: str) -> list[DetectionIn]:
        raise TrackingUnavailable("SAM tracking is not connected yet; upload detections manually")

    def suggest_release_time(self, video_path: Path) -> ReleaseSuggestion:
        return ReleaseSuggestion(source="mock", candidate_t0_s=None, reason="model not connected")

    def track_object(self, video_path: Path, text_prompt: str, t_start: float, t_end: float) -> list[DetectionIn]:
        raise TrackingUnavailable("SAM tracking is not connected yet; using frame differencing")

    def interview_audit(self, video_path: Path) -> AuditInterview:
        return AuditInterview(source="mock", questions=MOCK_QUESTIONS, note="model not connected")


_hooks: ModelHooks = MockHooks()


def get_hooks() -> ModelHooks:
    return _hooks


def set_hooks(hooks: ModelHooks) -> None:
    global _hooks
    _hooks = hooks
