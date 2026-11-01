"""Track re-check (T203): Spark looks at 4 circled frames and judges whether
SAM tracked the same object throughout.

`check_track(video_path, points, object_name)` picks 4 evenly spaced tracked
times, extracts each frame scaled to the backend's 480 px-wide frame, draws a
red ring at the tracked position, and asks Spark whether the circled thing is
the same object in all four. Points use the AuditOut convention: (t_s, x, y)
with x/y in the 480 px-wide frame.

Returns {"same_object", "note", "source"}, or None when there is nothing to
check (fewer than 4 tracked points), the model output fails validation after
retries, or the API call itself fails. None means "not checked", never a
verdict. Numbers or authenticity language in the note fail validation.
"""
from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from backend.output_check import check_model_text

from . import client as _client
from . import sam as _sam
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import MediaError, ModelOutputError, SpendLimitExceeded
from .explain import AUTHENTICITY_BANNED
from .spark import _check_priced, _text_format, _usage_to_dict

N_STILLS = 4
FRAME_WIDTH = 480
RING_RADIUS = 14
RING_WIDTH = 3
MAX_NOTE_CHARS = 200

TRACK_CHECK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "same_object": {"type": "boolean"},
        "note": {"type": "string"},
    },
    "required": ["same_object", "note"],
    "additionalProperties": False,
}

TRACK_CHECK_PROMPT = (
    "You see {n} stills from one video clip, in time order. In each still a "
    "red ring marks where a tracker says the {name} is. Answer with JSON "
    "only, matching the schema. same_object is true when the ringed thing "
    "looks like the same {name} in every still the ring is visible, false "
    "when the tracker clearly jumped to a different object or the background "
    "(a ring on empty background with the object elsewhere counts as jumped). "
    "note is one short English phrase saying what you saw. Describe only "
    "what is visible; do not claim proof or causes (no 'proves', 'confirms', "
    "'must be'). Do not output any numbers at all. Use exactly these JSON "
    'keys: "same_object" and "note".'
)


def _pick_times(points: Sequence[Sequence[float]]) -> list[tuple[float, float, float]]:
    """Evenly spaced (t, x, y) picks across the track; needs 4+ points."""
    usable = [(float(p[0]), float(p[1]), float(p[2]))
              for p in points
              if len(p) >= 3 and p[0] is not None and p[1] is not None and p[2] is not None]
    if len(usable) < N_STILLS:
        return []
    usable.sort(key=lambda p: p[0])
    last = len(usable) - 1
    return [usable[round(i * last / (N_STILLS - 1))] for i in range(N_STILLS)]


def _frame_rgb(video: Path, t: float) -> np.ndarray:
    # Byte-mode subprocess: _sam._run_cmd decodes text and crashes on binary
    # frame data (found live in T206; unit tests had mocked this away).
    try:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(video),
             "-frames:v", "1", "-vf", f"scale={FRAME_WIDTH}:-2",
             "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
            capture_output=True, check=False,
            timeout=_client.UPLOAD_TIMEOUT_S,
        )
    except FileNotFoundError as exc:
        raise MediaError("ffmpeg not found; install ffmpeg to enable tracking.") from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaError(f"ffmpeg timed out at t={t:g}") from exc
    if proc.returncode != 0 or not proc.stdout:
        raise MediaError(f"frame extraction failed at t={t:g}")
    raw = proc.stdout
    # Height from the byte count (width is fixed at FRAME_WIDTH, RGB).
    px = len(raw) // (FRAME_WIDTH * 3)
    if px * FRAME_WIDTH * 3 != len(raw) or px <= 0:
        raise MediaError(f"frame extraction failed at t={t:g}: {len(raw)} bytes")
    return np.frombuffer(raw, np.uint8).reshape(px, FRAME_WIDTH, 3).copy()


def _draw_ring(frame: np.ndarray, x: float, y: float) -> np.ndarray:
    h, w = frame.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    ring = np.abs(dist - RING_RADIUS) <= RING_WIDTH / 2
    frame[ring] = (255, 0, 0)
    return frame


def _to_png_bytes(frame: np.ndarray) -> bytes:
    h, w = frame.shape[:2]
    proc = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{w}x{h}", "-i", "-", "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        input=frame.tobytes(), capture_output=True, check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise MediaError("frame PNG encoding failed")
    return proc.stdout


def _circled_stills(video: Path, picks: list[tuple[float, float, float]]) -> list[str]:
    """Extract + ring each pick; returns base64 PNG data URIs."""
    uris = []
    for t, x, y in picks:
        frame = _draw_ring(_frame_rgb(video, t), x, y)
        uris.append("data:image/png;base64,"
                    + base64.b64encode(_to_png_bytes(frame)).decode("ascii"))
    return uris


def _validate_track_check(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ModelOutputError("track check must be a JSON object")
    same = data.get("same_object")
    if type(same) is not bool:
        raise ModelOutputError("same_object must be boolean")
    note = data.get("note")
    if not isinstance(note, str) or not note.strip():
        raise ModelOutputError("note must be a non-empty string")
    note = note.strip()
    if len(note) > MAX_NOTE_CHARS:
        raise ModelOutputError("note must be under 200 characters")
    if any(c.isdigit() for c in note):
        raise ModelOutputError("note must not contain numbers")
    checked = check_model_text(note, [])
    if not checked.ok:
        raise ModelOutputError("note failed checks: " + "; ".join(checked.problems))
    bad = [w for w in AUTHENTICITY_BANNED if w.lower() in note.lower()]
    if bad:
        raise ModelOutputError("forbidden authenticity language: " + ", ".join(bad))
    return {"same_object": same, "note": note}


def check_track(
    video_path: Path | str,
    points: Sequence[Sequence[float]],
    object_name: str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any] | None:
    """Ask Spark whether 4 ringed frames show the same object (T203).

    Returns {"same_object", "note", "source"}, or None when there are fewer
    than 4 tracked points or the check fails (bad output after retries, API
    error, timeout). MediaError (unreadable video) and SpendLimitExceeded
    still raise; everything model-side degrades to None.
    """
    path = Path(video_path)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    if not object_name or not object_name.strip():
        raise ValueError("object_name must be a non-empty noun phrase")
    picks = _pick_times(points)
    if not picks:
        return None
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    uris = _circled_stills(path, picks)
    prompt = TRACK_CHECK_PROMPT.format(n=N_STILLS, name=object_name.strip())
    images = [{"type": "input_image", "image_url": uri} for uri in uris]
    sdk = get_client()
    for _ in range(MAX_RETRIES + 1):
        try:
            response = call_with_retry(
                lambda: sdk.responses.create(
                    model=resolved,
                    input=[{
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}, *images],
                    }],
                    text=_text_format("track_check", TRACK_CHECK_SCHEMA),
                    timeout=timeout,
                ),
                op="spark.check_track",
            )
        except (MediaError, SpendLimitExceeded, ValueError):
            raise
        except Exception:
            continue  # transport/API failure: no check, not a verdict
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.check_track",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_track_check(json.loads(response.output_text or ""))
            out["source"] = resolved
            return out
        except (json.JSONDecodeError, ModelOutputError, ValueError):
            continue
    return None
