"""In-memory experiment store. Records are append-only: predictions, calibrations and baselines
are never edited, only superseded by new versions. Persistence can replace this module later."""
from __future__ import annotations

import os
import pickle
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_ROOT = Path(__file__).resolve().parent.parent / "data"
UPLOAD_ROOT = DATA_ROOT / "uploads"
# Set SLOPE_STORE_PATH="" to keep everything in memory (tests do this).
STORE_PATH = os.environ.get("SLOPE_STORE_PATH", str(DATA_ROOT / "store.pkl"))


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
        self.audits: dict[str, dict] = {}

    def reset(self) -> None:
        self.__init__()

    def save(self) -> None:
        """Snapshot the whole store after each write, so a restart keeps every experiment."""
        if not STORE_PATH:
            return
        path = Path(STORE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with tmp.open("wb") as f:
            pickle.dump((self.experiments, self.trials, self.intervention_owner, self.audits), f)
        tmp.replace(path)

    def load(self) -> None:
        # The snapshot is written only by this server; never point STORE_PATH at an uploaded file.
        if STORE_PATH and Path(STORE_PATH).exists():
            with open(STORE_PATH, "rb") as f:
                data = pickle.load(f)
            self.experiments, self.trials, self.intervention_owner = data[:3]
            self.audits = data[3] if len(data) > 3 else {}


store = Store()
store.load()
