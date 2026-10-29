"""Voice setup dictation (T24): transcribe speech, extract setup fields.

`transcribe()` sends audio to muse-voice-transcribe-1.0 (file endpoint
POST /v1/asr/transcribe, WAV only) and returns the transcript plus the
billed audio seconds. `extract_setup_fields()` has Spark pull the slope
length, height, and release notes out of the transcript as JSON.
`answer_interview_voice()` (T109) does the same for spoken answers to the
audit interview questions.

The extracted numbers are the user's own dictated values and MUST be shown
for user confirmation before use; they are never treated as measurements.
Unit conversion (cm/mm to m) is done by the program, never the model.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from . import client as _client
from .client import BASE_URL, MAX_RETRIES, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import AuthError, MediaError, MetaClientError, ModelOutputError
from .spark import _check_priced, _text_format, _usage_to_dict

VOICE_MODEL = "muse-voice-transcribe-1.0"
VOICE_TIMEOUT_S = 300.0
TRANSCRIBE_URL = f"{BASE_URL}/asr/transcribe"

SETUP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "slope_length_m": {"type": ["number", "null"]},
        "slope_height_m": {"type": ["number", "null"]},
        "release_notes": {"type": "string"},
    },
    "required": ["slope_length_m", "slope_height_m", "release_notes"],
    "additionalProperties": False,
}

SETUP_PROMPT = (
    "Read this spoken setup dictation for a slope experiment and extract the "
    "setup values into JSON: slope_length_m (slope surface length in meters), "
    "slope_height_m (vertical height in meters), release_notes (how the user "
    "says they will release the slider, as plain words). Use null for any "
    "value the speaker did not state; never guess or convert units beyond "
    "what was said. Return JSON only, with exactly these keys: "
    '"slope_length_m", "slope_height_m", "release_notes".'
)


def _to_wav(src: Path) -> Path:
    """Transcode to 24 kHz mono WAV; caller deletes the result."""
    tmp = tempfile.NamedTemporaryFile(prefix="voice24k_", suffix=".wav", delete=False)
    tmp.close()
    dst = Path(tmp.name)
    try:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "24000",
             "-c:a", "pcm_s16le", "-map_metadata", "-1", str(dst)],
            capture_output=True, text=True, timeout=_client.UPLOAD_TIMEOUT_S, check=False,
        )
    except FileNotFoundError as exc:
        dst.unlink(missing_ok=True)
        raise MediaError("ffmpeg not found; install ffmpeg (T02) for voice input.") from exc
    if proc.returncode != 0 or not dst.is_file():
        dst.unlink(missing_ok=True)
        raise MediaError(f"ffmpeg wav transcode failed: {proc.stderr.strip()[-300:]}")
    return dst


class _RetryableStatus(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status}")
        self.status = status


def _post_transcribe(audio: Path, timeout: float) -> dict[str, Any]:
    """POST one file to /v1/asr/transcribe with retry; returns parsed JSON."""
    api_key = os.environ.get("MODEL_API_KEY")
    if not api_key:
        raise AuthError("MODEL_API_KEY is not set; put the key in .env (never in code).")

    def _do() -> httpx.Response:
        with open(audio, "rb") as f:
            resp = httpx.post(
                TRANSCRIBE_URL,
                headers={"Authorization": "Bearer " + api_key, "Accept": "application/json"},
                data={"request": json.dumps({"model": VOICE_MODEL,
                                                   "audioEncoding": "WAV"})},
                files={"audio": (audio.name, f, "audio/wav")},
                timeout=timeout,
            )
        if resp.status_code == 401:
            raise AuthError("Meta API rejected the key (401); check MODEL_API_KEY.")
        if resp.status_code == 400:
            raise ModelOutputError(f"transcribe rejected the audio (400): {resp.text[:200]}")
        if resp.status_code == 429 or resp.status_code >= 500:
            raise _RetryableStatus(resp.status_code)
        if resp.status_code != 200:
            raise MetaClientError(f"transcribe failed ({resp.status_code}): {resp.text[:200]}")
        return resp

    last: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = _do()
            break
        except (_RetryableStatus, httpx.TimeoutException, httpx.ConnectError) as exc:
            last = exc
            if attempt >= MAX_RETRIES:
                raise MetaClientError(f"transcribe failed after retries: {exc}") from exc
            time.sleep(_client.RETRY_BACKOFF_S[min(attempt, len(_client.RETRY_BACKOFF_S) - 1)])
    try:
        data = resp.json()
    except ValueError as exc:
        raise ModelOutputError("transcribe returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise ModelOutputError("transcribe returned a non-object response")
    return data


def transcribe(
    audio_path: Path | str,
    *,
    timeout: float = VOICE_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Transcribe one recording. Returns transcript + billed audio seconds."""
    src = Path(audio_path)
    if not src.is_file():
        raise MediaError(f"audio file not found: {src}")
    tracker = tracker or get_tracker()
    tracker.check()
    wav: Path | None = None
    try:
        wav = _to_wav(src)
        data = _post_transcribe(wav, timeout)
    finally:
        if wav is not None:
            wav.unlink(missing_ok=True)
    transcript = data.get("transcript")
    if not isinstance(transcript, str) or not transcript.strip():
        raise ModelOutputError("transcribe returned an empty transcript")
    duration_ms = data.get("audioDurationMs", 0)
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)):
        raise ModelOutputError("transcribe returned a bad audioDurationMs")
    seconds = max(0.0, float(duration_ms) / 1000)
    tracker.record(VOICE_MODEL, "voice.transcribe", audio_seconds=seconds)
    return {"transcript": transcript.strip(), "audio_seconds": seconds,
            "source": VOICE_MODEL}


def _validate_setup(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("setup fields must be a JSON object")
    out: dict[str, Any] = {}
    for key in ("slope_length_m", "slope_height_m"):
        value = data.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise ModelOutputError(f"{key} must be a number or null")
        if isinstance(value, (int, float)) and value < 0:
            raise ModelOutputError(f"{key} must be >= 0")
        out[key] = value
    notes = data.get("release_notes")
    if not isinstance(notes, str):
        raise ModelOutputError("release_notes must be a string")
    out["release_notes"] = notes.strip()
    return out


def extract_setup_fields(
    transcript: str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Extract slope setup fields from a transcript (T24).

    Numbers are the user's dictated values for on-screen confirmation only.
    """
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("transcript must be a non-empty string")
    resolved = model or _client.SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    prompt = SETUP_PROMPT + "\nDictation:\n" + transcript.strip()
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=prompt,
                text=_text_format("setup_fields", SETUP_SCHEMA),
                timeout=timeout,
            ),
            op="spark.extract_setup_fields",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.extract_setup_fields",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_setup(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"setup fields failed validation: {last_error}")


ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "camera_static": {"type": ["boolean", "null"]},
        "slow_motion": {"type": ["boolean", "null"]},
        "object_size": {
            "type": ["object", "null"],
            "properties": {
                "value": {"type": "number"},
                "unit": {"type": "string", "enum": ["m", "cm", "mm"]},
            },
            "required": ["value", "unit"],
            "additionalProperties": False,
        },
        "length": {
            "type": ["object", "null"],
            "properties": {
                "value": {"type": "number"},
                "unit": {"type": "string", "enum": ["m", "cm", "mm"]},
            },
            "required": ["value", "unit"],
            "additionalProperties": False,
        },
        "time_window": {
            "type": ["object", "null"],
            "properties": {
                "t_start_s": {"type": ["number", "null"]},
                "t_end_s": {"type": ["number", "null"]},
            },
            "required": ["t_start_s", "t_end_s"],
            "additionalProperties": False,
        },
        "assumed_model": {
            "type": ["string", "null"],
            "enum": ["free_flight", "bounce", "pendulum", None],
        },
    },
    "required": ["camera_static", "slow_motion", "object_size", "length",
                 "time_window", "assumed_model"],
    "additionalProperties": False,
}

ANSWER_PROMPT = (
    "Read this spoken answer to video-audit questions and extract what the "
    "speaker stated into JSON: camera_static (did they say the camera stayed "
    "still), slow_motion (did they say slow motion was on), object_size (the "
    "object's size exactly as stated, as an object like {\"value\": 11, "
    "\"unit\": \"cm\"} with digits, or a short string like \"11 cm\"), length "
    "(pendulum string length the same way), time_window (the motion's start "
    "and end times in seconds), assumed_model (free_flight, bounce, or "
    "pendulum if named). Convert spoken numbers to digits exactly as stated "
    "(eleven → 11, half a second → 0.5, three → 3); use null only when the "
    "speaker truly did not state it, never guess, never convert units, "
    "never invent values. Return JSON only, with "
    "exactly these keys: camera_static, slow_motion, object_size, length, "
    "time_window, assumed_model."
)

_UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}

_UNIT_WORDS = {
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "centimetre": "cm", "centimetres": "cm",
    "mm": "mm", "millimeter": "mm", "millimeters": "mm",
    "millimetre": "mm", "millimetres": "mm",
}

_SIZE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([a-z]+)\s*$", re.IGNORECASE)


def _parse_spoken_size(text: str, key: str) -> dict[str, Any]:
    """Parse '11 cm' style strings deterministically (program, not model)."""
    match = _SIZE_RE.match(text)
    if not match:
        raise ModelOutputError(f"{key} must be an object or a '<number> <unit>' string")
    unit = _UNIT_WORDS.get(match.group(2).lower())
    if unit is None:
        raise ModelOutputError(f"{key}.unit must be m, cm, or mm")
    return {"value": float(match.group(1)), "unit": unit}

MOCK_NO_KEY_TRANSCRIPT = "(mock answer: MODEL_API_KEY is not set, nothing was transcribed)"


def _validate_size(data: Any, key: str) -> dict[str, Any] | None:
    if data is None:
        return None
    if isinstance(data, str):
        data = _parse_spoken_size(data, key)
    if not isinstance(data, dict):
        raise ModelOutputError(f"{key} must be an object or null")
    value, unit = data.get("value"), data.get("unit")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelOutputError(f"{key}.value must be a number")
    if value <= 0 or value >= 10000:
        raise ModelOutputError(f"{key}.value out of range")
    if unit not in _UNIT_TO_M:
        raise ModelOutputError(f"{key}.unit must be m, cm, or mm")
    return {"value": float(value), "unit": unit}


def _validate_answer(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("answer fields must be a JSON object")
    out: dict[str, Any] = {}
    for key in ("camera_static", "slow_motion"):
        value = data.get(key)
        if value is not None and type(value) is not bool:
            raise ModelOutputError(f"{key} must be a boolean or null")
        out[key] = value
    out["object_size"] = _validate_size(data.get("object_size"), "object_size")
    out["length"] = _validate_size(data.get("length"), "length")
    window = data.get("time_window")
    if isinstance(window, (list, tuple)) and len(window) == 2:
        window = {"t_start_s": window[0], "t_end_s": window[1]}
    if window is not None:
        if not isinstance(window, dict):
            raise ModelOutputError("time_window must be an object or null")
        for key in ("t_start_s", "t_end_s"):
            value = window.get(key)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
            ):
                raise ModelOutputError(f"time_window.{key} must be a number or null")
            if isinstance(value, (int, float)) and value < 0:
                raise ModelOutputError(f"time_window.{key} must be >= 0")
        t0, t1 = window.get("t_start_s"), window.get("t_end_s")
        if t0 is not None and t1 is not None and t1 <= t0:
            raise ModelOutputError("time_window must end after it starts")
    out["time_window"] = window
    model = data.get("assumed_model")
    if model not in ("free_flight", "bounce", "pendulum", None):
        raise ModelOutputError("assumed_model must be free_flight, bounce, pendulum, or null")
    out["assumed_model"] = model
    return out


def extract_interview_fields(
    transcript: str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Extract stated interview answers from a transcript (T109).

    Sizes come back as raw value+unit exactly as spoken; the caller
    converts to meters. Everything is unconfirmed until the user says so.
    """
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("transcript must be a non-empty string")
    resolved = model or _client.SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    sdk = get_client()
    prompt = ANSWER_PROMPT + "\nAnswer:\n" + transcript.strip()
    last_error: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=resolved,
                input=prompt,
                text=_text_format("answer_fields", ANSWER_SCHEMA),
                timeout=timeout,
            ),
            op="spark.extract_interview_fields",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.extract_interview_fields",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_answer(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"answer fields failed validation: {last_error}")


def answer_interview_voice(
    audio_path: Path | str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Transcribe a spoken interview answer and extract its fields (T109).

    Returns {"transcript", "fields", "mock", "source"} where each field is
    {"value", "confirmed": False}: the UI must show every value for
    confirmation and only submits confirmed ones. "source" names the model
    behind each part. Without MODEL_API_KEY returns a mock with no fields
    and no API call.
    """
    if not os.environ.get("MODEL_API_KEY"):
        return {"transcript": MOCK_NO_KEY_TRANSCRIPT, "fields": {}, "mock": True,
                "source": {"transcript": "mock", "fields": "mock"}}
    spoken = transcribe(audio_path, timeout=VOICE_TIMEOUT_S, tracker=tracker)
    raw = extract_interview_fields(spoken["transcript"], model=model,
                                   timeout=timeout, tracker=tracker)
    fields: dict[str, Any] = {}
    if raw["camera_static"] is not None:
        fields["camera_static"] = {"value": raw["camera_static"], "confirmed": False}
    if raw["slow_motion"] is not None:
        fields["slow_motion"] = {"value": raw["slow_motion"], "confirmed": False}
    if raw["object_size"] is not None:
        size = raw["object_size"]
        fields["object_size_m"] = {
            "value": size["value"] * _UNIT_TO_M[size["unit"]], "confirmed": False}
    if raw["length"] is not None:
        length = raw["length"]
        fields["length_m"] = {
            "value": length["value"] * _UNIT_TO_M[length["unit"]], "confirmed": False}
    if raw["time_window"] is not None:
        fields["time_window"] = {"value": raw["time_window"], "confirmed": False}
    if raw["assumed_model"] is not None:
        fields["assumed_model"] = {"value": raw["assumed_model"], "confirmed": False}
    return {"transcript": spoken["transcript"], "fields": fields, "mock": False,
            "source": {"transcript": VOICE_MODEL,
                       "fields": model or _client.SPARK_MODEL}}
