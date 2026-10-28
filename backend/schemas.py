"""Request/response models. Keep in sync with docs/API.md."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

Point = tuple[float, float]


class TrialKind(str, Enum):
    baseline = "baseline"
    test = "test"
    intervention = "intervention"


class SceneCheck(BaseModel):
    source: Literal["model", "mock"]
    has_ruler: bool | None = None
    has_slope: bool | None = None
    has_slider: bool | None = None
    is_side_view: bool | None = None
    needs_retake: bool = False
    retake_reasons: list[str] = []


class ScenePhotoOut(BaseModel):
    photo_id: str
    photo_url: str | None = None  # None only for records saved before T30
    scene_check: SceneCheck


class CalibrationIn(BaseModel):
    ruler_px: tuple[Point, Point]
    ruler_length_m: float
    path_start_px: Point
    path_end_px: Point
    slope_length_m: float = Field(description="L, measured along the slope surface, user-confirmed")
    slope_height_m: float = Field(description="h, vertical rise, user-confirmed")
    reason: str = "initial"  # e.g. "dimension_check" when the user re-measured


class CalibrationOut(CalibrationIn):
    version: int
    m_per_px: float
    angle_deg: float
    created_at: datetime


class DetectionIn(BaseModel):
    t_s: float
    centroid_px: Point | None
    area_px: float | None = None
    source: Literal["sam", "manual"] = "sam"


class DetectionsIn(BaseModel):
    detections: list[DetectionIn]


class SampleOut(BaseModel):
    t_s: float
    s_m: float | None
    quality: str
    source: str


class ReleaseTimeIn(BaseModel):
    t0_s: float


class ReleaseSuggestion(BaseModel):
    source: Literal["model", "mock"]
    candidate_t0_s: float | None
    reason: str


class TrialOut(BaseModel):
    trial_id: str
    kind: TrialKind
    calibration_version: int
    uploaded_at: datetime
    video_url: str | None
    t0_s: float | None
    t0_source: Literal["user"] | None
    samples: list[SampleOut]
    usable_fraction: float
    manual_frames: int


class BaselineIn(BaseModel):
    trial_ids: list[str]
    calibration_version: int


class BaselineOut(BaseModel):
    version: int
    calibration_version: int
    trial_ids: list[str]
    mu_eff: float
    mu_spread: float
    accel_mean_m_s2: float
    accel_spread_m_s2: float
    created_at: datetime


class PredictionIn(BaseModel):
    calibration_version: int
    baseline_version: int
    distance_m: float
    assumes_release_from_rest: bool = True


class PredictionOut(BaseModel):
    prediction_id: str
    calibration_version: int
    baseline_version: int
    created_at: datetime
    locked: Literal[True] = True
    params: dict[str, float]
    assumptions: list[str]
    curve: list[tuple[float, float]]  # (t since release, s along path from release point)
    overlay_px: list[tuple[float, float, float]]  # (t since release, x_px, y_px)


class ComparisonIn(BaseModel):
    prediction_id: str
    trial_id: str


class CheckOut(BaseModel):
    name: str
    passed: bool
    detail: str
    blocking: bool


class EvidenceOut(BaseModel):
    candidate: Literal["dimension_check", "release_check"]
    finding: str
    numbers: dict[str, float]
    cannot_distinguish: str


class ComparisonOut(BaseModel):
    comparison_id: str
    prediction_id: str
    trial_id: str
    verdict: Literal["consistent", "discrepancy", "insufficient_data"]
    checks: list[CheckOut]
    fit: dict[str, float] | None
    predicted_arrival_s: float | None
    observed_arrival_s: float | None
    arrival_error_rel: float | None
    tolerance_rel: float
    residuals: list[tuple[float, float]]
    can_still_say: list[str]
    evidence: list[EvidenceOut]
    created_at: datetime


class InterventionIn(BaseModel):
    comparison_id: str
    check_type: Literal["dimension_check", "release_check"]
    chosen_by: Literal["user"] = "user"
    model_rationale: str | None = None


class InterventionPatch(BaseModel):
    result_trial_id: str


class InterventionOut(BaseModel):
    intervention_id: str
    comparison_id: str
    check_type: str
    instructions: dict[str, list[str] | str]
    chosen_by: str
    model_rationale: str | None
    result_trial_id: str | None
    created_at: datetime


class ExperimentIn(BaseModel):
    title: str = "Slope experiment"


class ExperimentOut(BaseModel):
    experiment_id: str
    title: str
    created_at: datetime
    scene_photos: list[ScenePhotoOut]
    calibrations: list[CalibrationOut]
    trials: list[TrialOut]
    baselines: list[BaselineOut]
    predictions: list[PredictionOut]
    comparisons: list[ComparisonOut]
    interventions: list[InterventionOut]


class PersistenceEventOut(BaseModel):
    kind: str
    t_s: float
    detail: str


class AuditOut(BaseModel):
    """Video physics audit. verdict is relative to assumed_model only; never real vs generated."""
    audit_id: str
    created_at: datetime
    assumed_model: Literal["free_flight", "bounce"]
    t_start: float
    t_end: float
    camera_static: bool
    object_size_m: float | None
    video_url: str
    overlay_url: str | None
    track_source: Literal["frame_diff", "sam", "manual"]
    verdict: Literal["consistent", "inconsistent", "insufficient_data"]
    reasons: list[str]
    numbers: dict[str, float]
    points: list[tuple[float, float, float]]  # [t_s, x_px, y_px] at 480 px frame width
    ghost_points: list[tuple[float, float, float]] = []  # same start and velocity, falling at 9.81; needs object_size_m
    nearest_body: str | None = None  # body whose surface gravity is closest to the apparent g
    events: list[PersistenceEventOut]
    limits: list[str]
