"""In-memory experiment store. Records are append-only: predictions, calibrations and baselines
are never edited, only superseded by new versions. Persistence can replace this module later."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "data" / "uploads"


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class TrialRecord:
    trial_id: str
    experiment_id: str
    kind: str
    calibration_version: int
    uploaded_at: datetime
    video_path: Path | None
    t0_s: float | None = None
    samples: list[Any] = field(default_factory=list)  # physics.tracking.Sample


@dataclass
class ExperimentRecord:
    experiment_id: str
    title: str
    created_at: datetime
    scene_photos: list[dict] = field(default_factory=list)
    calibrations: list[dict] = field(default_factory=list)  # index = version - 1
    baselines: list[dict] = field(default_factory=list)
    predictions: dict[str, dict] = field(default_factory=dict)
    comparisons: dict[str, dict] = field(default_factory=dict)
    interventions: dict[str, dict] = field(default_factory=dict)
    trial_ids: list[str] = field(default_factory=list)


class Store:
    def __init__(self) -> None:
        self.experiments: dict[str, ExperimentRecord] = {}
        self.trials: dict[str, TrialRecord] = {}
        self.intervention_owner: dict[str, str] = {}

    def reset(self) -> None:
        self.__init__()


store = Store()
