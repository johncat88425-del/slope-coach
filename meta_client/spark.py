"""Muse Spark calls (Responses API): scene check + release-time suggestion.

Rules enforced here (AGENTS.md):
- the model never produces measurement numbers: describe_scene returns only
  booleans + short reason strings; suggest_release_time returns one candidate
  timestamp + a number-free reason (the user still confirms t0 in the app).
- every output passes schema/range validation; failures retry at most
  MAX_RETRIES times, then raise ModelOutputError.
"""
from __future__ import annotations

import base64
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from backend.output_check import check_model_text

from . import client as _client
from . import sam as _sam
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import TOKEN_PRICES, CostTracker, get_tracker
from .exceptions import MediaError, ModelOutputError

SCENE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "has_ruler": {"type": "boolean"},
        "has_slope": {"type": "boolean"},
        "has_slider": {"type": "boolean"},
        "is_side_view": {"type": "boolean"},
        "needs_retake": {"type": "boolean"},
        "retake_reasons": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "has_ruler",
        "has_slope",
        "has_slider",
        "is_side_view",
        "needs_retake",
        "retake_reasons",
    ],
    "additionalProperties": False,
}

SCENE_PROMPT = (
    "Look at this experiment photo. Answer with JSON only, matching the schema: "
    "has_ruler (a straight ruler or tape in view), has_slope (one straight ramp), "
    "has_slider (the sliding block), is_side_view (camera roughly perpendicular to "
    "the motion plane, whole path visible, no strong perspective). Set needs_retake "
    "when the photo cannot be used for measurement (missing ruler, moving camera, "
    "heavy perspective, path cut off) and list each problem as a short phrase in "
    "retake_reasons. Describe only what is visible; do not claim proof or causes "
    "(no 'proves', 'confirms', 'must be', 'caused by'). "
    "Do not output any measurements, coordinates, or numbers. "
    "Use exactly these JSON keys: has_ruler, has_slope, has_slider, "
    "is_side_view, needs_retake, retake_reasons."
)

RELEASE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "candidate_t0_s": {"type": ["number", "null"]},
        "reason": {"type": "string"},
    },
    "required": ["candidate_t0_s", "reason"],
    "additionalProperties": False,
}

RELEASE_PROMPT = (
    "Watch this clip of a block on a slope, starting before the release. "
    "Return JSON only: candidate_t0_s is the number of seconds from the start "
    "of the clip when the block first starts moving, or null when the release "
    "moment is not visible or unclear. reason describes only what is visibly "
    "happening (for example 'hand lifts away, then the block moves') and must "
    "not contain any other numbers: no frame numbers, coordinates, distances, "
    "speeds, or time ranges. One candidate moment plus a plain-language reason. "
    "Do not claim proof or causes (no 'proves', 'confirms', 'must be'). "
    'Use exactly these JSON keys: "candidate_t0_s", "reason".'
)

_MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _usage_to_dict(usage: Any) -> dict[str, int]:
    """Extract token counts from an SDK usage object, defensively."""
    if usage is None:
        return {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0}
    if isinstance(usage, dict):
        data = usage
    elif hasattr(usage, "model_dump"):
        data = usage.model_dump()
    else:
        data = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
        }
    details = data.get("input_tokens_details") or {}
    if not isinstance(details, dict):
        details = {}
    return {
        "input_tokens": int(data.get("input_tokens") or 0),
        "cached_tokens": int(details.get("cached_tokens") or 0),
        "output_tokens": int(data.get("output_tokens") or 0),
    }


def _check_priced(model: str) -> None:
    if model not in TOKEN_PRICES:
        raise ValueError(
            f"refusing to call {model!r}: no official per-token price recorded; "
            "add it to cost.TOKEN_PRICES first so spend stays accountable."
        )


def _text_format(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {"type": "json_schema", "name": name, "strict": True, "schema": schema}


def _image_data_url(image: Path | str | bytes) -> str:
    if isinstance(image, bytes):
        return "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii")
    path = Path(image)
    if not path.is_file():
        raise MediaError(f"image file not found: {path}")
    mime = _MIME_BY_SUFFIX.get(path.suffix.lower())
    if mime is None:
        raise MediaError(f"unsupported image suffix {path.suffix!r} (use jpg/png/webp)")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _validate_scene(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("scene check must be a JSON object")
    out: dict[str, Any] = {}
    for key in (
        "has_ruler",
        "has_slope",
        "has_slider",
        "is_side_view",
        "needs_retake",
    ):
        value = data.get(key)
        if type(value) is not bool:
            raise ModelOutputError(f"scene check field {key!r} must be boolean")
        out[key] = value
    reasons = data.get("retake_reasons")
    if not isinstance(reasons, list) or not all(
        isinstance(r, str) for r in reasons
    ):
        raise ModelOutputError("scene check field 'retake_reasons' must be string[]")
    out["retake_reasons"] = reasons
    if out["needs_retake"] and not reasons:
        raise ModelOutputError("needs_retake=true requires at least one retake reason")
    if not out["needs_retake"] and reasons:
        raise ModelOutputError("retake reasons given but needs_retake=false")
    return out


def _validate_release(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("release suggestion must be a JSON object")
    candidate = data.get("candidate_t0_s")
    if candidate is not None and (
        isinstance(candidate, bool) or not isinstance(candidate, (int, float))
    ):
        raise ModelOutputError("candidate_t0_s must be a number or null")
    if isinstance(candidate, (int, float)) and candidate < 0:
        raise ModelOutputError("candidate_t0_s must be >= 0")
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ModelOutputError("reason must be a non-empty string")
    _reject_extra_numbers(reason, [candidate], "reason")
    return {"candidate_t0_s": candidate, "reason": reason.strip()}


def _reject_extra_numbers(
    text: str, allowed: list[float | None], field: str
) -> None:
    """Reject numbers in free text unless they repeat a candidate value.

    Candidate timestamps are suggestions the user must confirm, never
    measurements; every other digit sequence in model prose is refused.
    """
    for token in _NUMBER_RE.findall(text):
        if not any(
            a is not None and abs(float(token) - float(a)) <= 1e-6 for a in allowed
        ):
            raise ModelOutputError(
                f"{field} must not contain measurement numbers; "
                "the candidate timestamps are the only numbers allowed"
            )


SEGMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "object": {"type": "string"},
        "assumed_model": {"type": "string", "enum": ["free_flight", "slide", "none"]},
        "candidate_t_start": {"type": ["number", "null"]},
        "candidate_t_end": {"type": ["number", "null"]},
        "reason": {"type": "string"},
    },
    "required": ["object", "assumed_model", "candidate_t_start", "candidate_t_end", "reason"],
    "additionalProperties": False,
}

SEGMENT_PROMPT = (
    "Watch this clip. Identify the one main moving object and pick the motion "
    "model that best describes its visible motion: 'free_flight' for an object "
    "flying or falling freely through the air (a thrown ball, a drop), 'slide' "
    "for an object sliding along a slope or ramp, or 'none' when there is no "
    "clear single-object motion. Return JSON only: object is a short noun "
    "phrase naming the object; assumed_model is one of the three labels; "
    "candidate_t_start and candidate_t_end are seconds from the clip start "
    "bracketing the suggested motion segment (for free_flight: release to "
    "landing; for slide: motion start to stop), or null when assumed_model is "
    "'none' or a boundary is unclear. reason describes only visible cues and "
    "must not contain any other numbers: no frame numbers, coordinates, "
    "distances, speeds, or extra times. The times are suggestions a user must "
    "confirm, never measurements. Do not claim proof or causes "
    "(no 'proves', 'confirms', 'must be'). Use exactly these JSON keys: "
    '"object", "assumed_model", "candidate_t_start", "candidate_t_end", "reason".'
)


def _validate_segment(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("motion segment must be a JSON object")
    object_name = data.get("object")
    if not isinstance(object_name, str) or not object_name.strip():
        raise ModelOutputError("object must be a non-empty string")
    assumed = data.get("assumed_model")
    if assumed not in ("free_flight", "slide", "none"):
        raise ModelOutputError("assumed_model must be free_flight, slide, or none")
    times = []
    for key in ("candidate_t_start", "candidate_t_end"):
        value = data.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise ModelOutputError(f"{key} must be a number or null")
        if isinstance(value, (int, float)) and value < 0:
            raise ModelOutputError(f"{key} must be >= 0")
        times.append(value)
    t_start, t_end = times
    if assumed == "none":
        if t_start is not None or t_end is not None:
            raise ModelOutputError("assumed_model 'none' requires null timestamps")
    elif (
        t_start is not None
        and t_end is not None
        and t_end <= t_start
    ):
        raise ModelOutputError("candidate_t_end must be after candidate_t_start")
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ModelOutputError("reason must be a non-empty string")
    _reject_extra_numbers(object_name, [t_start, t_end], "object")
    _reject_extra_numbers(reason, [t_start, t_end], "reason")
    return {
        "object": object_name.strip(),
        "assumed_model": assumed,
        "candidate_t_start": t_start,
        "candidate_t_end": t_end,
        "reason": reason.strip(),
    }


def describe_scene(
    image: Path | str | bytes,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Check one setup photo. Returns the 6 fixed schema fields as a dict."""
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    data_url = _image_data_url(image)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": SCENE_PROMPT},
                            {"type": "input_image", "image_url": data_url},
                        ],
                    }
                ],
                text=_text_format("scene_check", SCENE_SCHEMA),
                timeout=timeout,
            ),
            op="spark.describe_scene",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.describe_scene",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_scene(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"scene check failed validation: {last_error}")


def suggest_release_time(
    video_clip: Path | str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_VIDEO_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Suggest the release moment of a clip. Returns candidate + reason only.

    candidate_t0_s is seconds from the clip start, or None when the release
    is not visible. It is a suggestion the user must confirm, never a
    measurement: no coordinates, distances, or other numbers are returned.
    """
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    path = Path(video_clip)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    tracker = tracker or get_tracker()
    tracker.check()
    file_id = _client.upload_file(path)
    sdk = get_client()
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": RELEASE_PROMPT},
                            {"type": "input_file", "file_id": file_id},
                        ],
                    }
                ],
                text=_text_format("release_suggestion", RELEASE_SCHEMA),
                timeout=timeout,
            ),
            op="spark.suggest_release_time",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.suggest_release_time",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_release(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"release suggestion failed validation: {last_error}")


def suggest_motion_segment(
    video: Path | str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_VIDEO_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Suggest which object to audit and which time window to check (T34).

    Returns object, assumed_model (free_flight/slide/none), candidate
    timestamps, and a number-free reason. The timestamps are suggestions the
    user must confirm, never measurements: no coordinates, distances, or
    other numbers are returned.
    """
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    path = Path(video)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    tracker = tracker or get_tracker()
    tracker.check()
    file_id = _client.upload_file(path)
    sdk = get_client()
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": SEGMENT_PROMPT},
                            {"type": "input_file", "file_id": file_id},
                        ],
                    }
                ],
                text=_text_format("motion_segment", SEGMENT_SCHEMA),
                timeout=timeout,
            ),
            op="spark.suggest_motion_segment",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.suggest_motion_segment",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_segment(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"motion segment failed validation: {last_error}")


CAPTURE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "object": {"type": "string"},
        "camera_static": {"type": "boolean"},
        "is_side_view": {"type": "boolean"},
        "object_visible_throughout": {"type": "boolean"},
        "reasons": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "object",
        "camera_static",
        "is_side_view",
        "object_visible_throughout",
        "reasons",
    ],
    "additionalProperties": False,
}

CAPTURE_PROMPT = (
    "Watch this clip{hint}. Answer with JSON only, matching the schema: "
    "object names the one main moving object as a short noun phrase; "
    "camera_static is true when the camera does not move during the clip; "
    "is_side_view is true when the camera looks at the motion roughly from "
    "the side with no strong perspective; object_visible_throughout is true "
    "when that object stays fully in frame for the whole clip. List every "
    "problem as a short phrase in reasons. Describe only what is visible; do "
    "not claim proof or causes (no 'proves', 'confirms', 'must be'). Do not "
    "output any numbers at all: no times, no frame numbers, no coordinates, "
    "no distances. Use exactly these JSON keys: object, camera_static, "
    "is_side_view, object_visible_throughout, reasons."
)


def _validate_capture(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("capture check must be a JSON object")
    object_name = data.get("object")
    if not isinstance(object_name, str) or not object_name.strip():
        raise ModelOutputError("object must be a non-empty string")
    out: dict[str, Any] = {"object": object_name.strip()}
    for key in ("camera_static", "is_side_view", "object_visible_throughout"):
        value = data.get(key)
        if type(value) is not bool:
            raise ModelOutputError(f"capture check field {key!r} must be boolean")
        out[key] = value
    reasons = data.get("reasons")
    if not isinstance(reasons, list) or not all(isinstance(r, str) for r in reasons):
        raise ModelOutputError("capture check field 'reasons' must be string[]")
    out["reasons"] = reasons
    if all((out["camera_static"], out["is_side_view"], out["object_visible_throughout"])):
        if reasons:
            raise ModelOutputError("reasons must be empty when all checks pass")
    elif not reasons:
        raise ModelOutputError("failing checks require at least one reason")
    _reject_extra_numbers(object_name, [], "object")
    for reason in reasons:
        _reject_extra_numbers(reason, [], "reasons")
    return out


def check_capture_conditions(
    video: Path | str,
    *,
    object_hint: str | None = None,
    model: str | None = None,
    timeout: float = _client.SPARK_VIDEO_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Check whether a clip meets the audit capture conditions (T39).

    Returns the object name, three booleans, and short reasons. The result
    goes to the user for confirmation; no numbers of any kind are returned.
    """
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    path = Path(video)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    tracker = tracker or get_tracker()
    tracker.check()
    file_id = _client.upload_file(path)
    sdk = get_client()
    prompt = CAPTURE_PROMPT.format(
        hint=f", paying attention to the {object_hint}" if object_hint else ""
    )
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_file", "file_id": file_id},
                        ],
                    }
                ],
                text=_text_format("capture_check", CAPTURE_SCHEMA),
                timeout=timeout,
            ),
            op="spark.check_capture_conditions",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.check_capture_conditions",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_capture(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"capture check failed validation: {last_error}")


OBJECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "object_name": {"type": "string"},
        "camera_looks_static": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["object_name", "camera_looks_static", "reason"],
    "additionalProperties": False,
}

OBJECT_PROMPT = (
    "You see two stills from the start of a clip: the very first frame, then "
    "one frame about a second later. Answer with JSON only, matching the "
    "schema. object_name names the one main moving object from the FIRST "
    "frame as a short lowercase English noun phrase (colour + kind, e.g. "
    "orange basketball); camera_looks_static is true when the background and "
    "frame edges look the same in both stills. reason is one short English "
    "phrase saying what you saw. Describe only what is visible; do not claim "
    "proof or causes (no 'proves', 'confirms', 'must be'). Do not output any "
    "numbers at all: no times, no frame numbers, no coordinates, no sizes. "
    "Use exactly these JSON keys: object_name, camera_looks_static, reason."
)

MAX_OBJECT_REASON_CHARS = 200


def _start_stills(video: Path, duration_s: float) -> list[Path]:
    """First frame plus one ~1s later; camera motion needs two views."""
    tmpdir = Path(tempfile.mkdtemp(prefix="object_stills_"))
    second = 1.0 if duration_s > 1.5 else duration_s / 2
    paths = []
    for i, stamp in enumerate((0.0, second)):
        dst = tmpdir / f"still{i}.jpg"
        proc = _sam._run_cmd(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(stamp),
             "-i", str(video), "-frames:v", "1", "-q:v", "4", str(dst)],
            _client.UPLOAD_TIMEOUT_S,
        )
        if proc.returncode != 0 or not dst.is_file():
            raise MediaError(f"frame extraction failed: {proc.stderr.strip()[-200:]}")
        paths.append(dst)
    return paths


def _validate_object(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and set(data) != {"object_name", "camera_looks_static", "reason"}:
        inner = data.get("suggestion", data.get("object_suggestion"))
        data = inner if isinstance(inner, dict) else data
    if not isinstance(data, dict):
        raise ModelOutputError("object suggestion must be a JSON object")
    name = data.get("object_name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ModelOutputError("object_name must be a non-empty string under 100 characters")
    static = data.get("camera_looks_static")
    if type(static) is not bool:
        raise ModelOutputError("camera_looks_static must be boolean")
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > MAX_OBJECT_REASON_CHARS:
        raise ModelOutputError("reason must be a non-empty string under 200 characters")
    for label, text in (("object_name", name), ("reason", reason)):
        checked = check_model_text(text, [])
        if not checked.ok:
            raise ModelOutputError(f"{label} failed checks: " + "; ".join(checked.problems))
    return {"object_name": name.strip(), "camera_looks_static": static, "reason": reason.strip()}


def suggest_object(
    video: Path | str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Suggest an object name and whether the camera looks static (T108).

    Spark names the main moving object from the first frame and judges the
    camera by comparing it with a frame ~1s later (one still cannot show
    motion). Suggestions only; the user confirms before anything is used.
    """
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    path = Path(video)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    tracker = tracker or get_tracker()
    tracker.check()
    info = _sam._probe_clip(path)
    if info["fps"] <= 0 or info["n_frames"] <= 0:
        raise MediaError(f"could not read video info from {path.name}")
    duration_s = info["n_frames"] / info["fps"]
    stills = _start_stills(path, duration_s)
    try:
        images = [
            {"type": "input_image",
             "image_url": "data:image/jpeg;base64,"
             + base64.b64encode(p.read_bytes()).decode("ascii")}
            for p in stills
        ]
    finally:
        for p in stills:
            p.unlink(missing_ok=True)
        try:
            stills[0].parent.rmdir()
        except OSError:
            pass
    sdk = get_client()
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=[{
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": OBJECT_PROMPT}, *images],
                }],
                text=_text_format("object_suggestion", OBJECT_SCHEMA),
                timeout=timeout,
            ),
            op="spark.suggest_object",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.suggest_object",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_object(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"object suggestion failed validation: {last_error}")
