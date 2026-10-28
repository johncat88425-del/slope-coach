"""Where Meta model calls plug in. meta_client (Muse Code, T05/T11) provides the real implementation.

The backend only depends on this interface. The default MockHooks never calls a network
service, so the backend and frontend can be developed and tested without an API key.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .schemas import DetectionIn, ReleaseSuggestion, SceneCheck


class TrackingUnavailable(RuntimeError):
    pass


class ModelHooks(Protocol):
    def check_scene(self, photo_path: Path) -> SceneCheck: ...
    def track_slider(self, video_path: Path, text_prompt: str) -> list[DetectionIn]: ...
    def suggest_release_time(self, video_path: Path) -> ReleaseSuggestion: ...


class MockHooks:
    def check_scene(self, photo_path: Path) -> SceneCheck:
        return SceneCheck(source="mock", needs_retake=False)

    def track_slider(self, video_path: Path, text_prompt: str) -> list[DetectionIn]:
        raise TrackingUnavailable("SAM tracking is not connected yet; upload detections manually")

    def suggest_release_time(self, video_path: Path) -> ReleaseSuggestion:
        return ReleaseSuggestion(source="mock", candidate_t0_s=None, reason="model not connected")


_hooks: ModelHooks = MockHooks()


def get_hooks() -> ModelHooks:
    return _hooks


def set_hooks(hooks: ModelHooks) -> None:
    global _hooks
    _hooks = hooks
