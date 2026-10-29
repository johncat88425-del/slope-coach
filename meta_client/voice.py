"""Voice setup dictation (T24): transcribe speech, extract setup fields.

`transcribe()` sends audio to muse-voice-transcribe-1.0 (file endpoint
POST /v1/asr/transcribe, WAV only) and returns the transcript plus the
billed audio seconds. `extract_setup_fields()` has Spark pull the slope
length, height, and release notes out of the transcript as JSON.

The extracted numbers are the user's own dictated values and MUST be shown
for user confirmation before use; they are never treated as measurements.
"""
from __future__ import annotations

import json
import os
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
                data={"request": json.dumps({"model": VOICE_MODEL})},
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
    return {"transcript": transcript.strip(), "audio_seconds": seconds}


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
            return _validate_setup(json.loads(response.output_text or ""))
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"setup fields failed validation: {last_error}")
