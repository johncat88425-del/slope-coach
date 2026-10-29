"""Muse interview (T66): Spark looks at a few frames and asks the user up
to 3 questions before an audit.

The questions clarify `camera_static`, `slow_motion`, `object_size_m`,
`time_window`, `assumed_model`, or `length_m`. The user's answers become
confirmed inputs; Spark itself never fills in numbers. Validation mirrors
backend/audits.py checked_interview exactly (1-3 questions, unique fields,
check_model_text per question, 200-char cap), so anything returned here
passes the backend check as well.
"""
from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path
from typing import Any

from backend.output_check import check_model_text

from . import client as _client
from . import sam as _sam
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import MediaError, ModelOutputError
from .spark import _check_priced, _text_format, _usage_to_dict

FIELDS = (
    "camera_static",
    "slow_motion",
    "object_size_m",
    "time_window",
    "assumed_model",
    "length_m",
)
MAX_QUESTIONS = 3
N_FRAMES = 3
FRAME_FRACTIONS = (0.1, 0.5, 0.9)

INTERVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": list(FIELDS)},
                    "text": {"type": "string"},
                },
                "required": ["field", "text"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "maxItems": MAX_QUESTIONS,
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

INTERVIEW_PROMPT = (
    "These are frames from a video the user wants to audit for physics. "
    "Before judging anything, ask the user what you need to know. Return "
    "JSON with 1 to 3 questions, each naming a different field: "
    "camera_static (did the camera stay completely still), slow_motion "
    "(was this recorded or played back in slow motion), object_size_m (does "
    "the user know the object's real size), time_window (which segment to "
    "check), assumed_model (which motion the user assumes: free fall, "
    "bounce, or pendulum), length_m (pendulum string length, if relevant). "
    "Ask only what the frames leave unclear; skip what is obvious. Each "
    "question text must be plain words under 200 characters: no numbers "
    "except small counting integers, no claims about real vs generated "
    "video, no proof or cause claims. Each question object has exactly two "
    'keys: "field" and "text" — no other key names.'
)


def _extract_frames(video: Path, duration_s: float) -> list[Path]:
    """Extract JPEG stills at fixed fractions; caller deletes them."""
    tmpdir = Path(tempfile.mkdtemp(prefix="interview_frames_"))
    paths = []
    for i, frac in enumerate(FRAME_FRACTIONS[:N_FRAMES]):
        dst = tmpdir / f"frame{i}.jpg"
        proc = _sam._run_cmd(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(duration_s * frac),
             "-i", str(video), "-frames:v", "1", "-q:v", "4", str(dst)],
            _client.UPLOAD_TIMEOUT_S,
        )
        if proc.returncode != 0 or not dst.is_file():
            raise MediaError(f"frame extraction failed: {proc.stderr.strip()[-200:]}")
        paths.append(dst)
    return paths


def _validate_interview(data: Any) -> list[dict[str, str]]:
    # Observed 10/29: the API ignores strict json_schema, so the envelope
    # varies run to run ({"questions": [...]} vs bare [...]). Accept both;
    # stay strict about the questions themselves.
    if isinstance(data, dict):
        data = data.get("questions")
    if not isinstance(data, list):
        raise ModelOutputError("interview must be a questions array or an object with questions[]")
    questions = data
    if not 1 <= len(questions) <= MAX_QUESTIONS:
        raise ModelOutputError("interview needs 1 to 3 questions")
    fields = []
    for q in questions:
        if not isinstance(q, dict):
            raise ModelOutputError("each question must be an object")
        if q.get("field") not in FIELDS:
            raise ModelOutputError(f"unknown question field {q.get('field')!r}")
        # Observed 10/29: the API does not enforce json_schema strictly and
        # Spark systematically writes "question" instead of "text". Accept
        # the alias; anything else still fails.
        text = q.get("text", q.get("question"))
        if not isinstance(text, str) or not text.strip():
            raise ModelOutputError("question text must be a non-empty string")
        if len(text) > 200:
            raise ModelOutputError("question text must be under 200 characters")
        fields.append(q["field"])
    if len(set(fields)) != len(fields):
        raise ModelOutputError("question fields must be unique")
    cleaned = []
    for q in questions:
        text = q.get("text", q.get("question")).strip()
        checked = check_model_text(text, [])
        if not checked.ok:
            raise ModelOutputError("question failed checks: " + "; ".join(checked.problems))
        cleaned.append({"field": q["field"], "text": text})
    return cleaned


def interview_audit(
    video_path: Path | str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any]:
    """Ask up to 3 clarification questions about a clip (T66).

    Returns {"questions": [{field, text}], "source": model}. Raises ModelOutputError when no
    valid set passes after retries; the backend falls back to fixed mock
    questions in that case.
    """
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    path = Path(video_path)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    tracker = tracker or get_tracker()
    tracker.check()
    info = _sam._probe_clip(path)
    if info["fps"] <= 0 or info["n_frames"] <= 0:
        raise MediaError(f"could not read video info from {path.name}")
    duration_s = info["n_frames"] / info["fps"]
    frame_paths = _extract_frames(path, duration_s)
    try:
        images = [
            {"type": "input_image",
             "image_url": "data:image/jpeg;base64,"
             + base64.b64encode(p.read_bytes()).decode("ascii")}
            for p in frame_paths
        ]
    finally:
        for p in frame_paths:
            p.unlink(missing_ok=True)
        try:
            frame_paths[0].parent.rmdir()  # the temp dir; no-op elsewhere
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
                    "content": [{"type": "input_text", "text": INTERVIEW_PROMPT}, *images],
                }],
                text=_text_format("interview", INTERVIEW_SCHEMA),
                timeout=timeout,
            ),
            op="spark.interview_audit",
        )
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.interview_audit",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            return {
                "questions": _validate_interview(json.loads(response.output_text or "")),
                "source": resolved,
            }
        except (json.JSONDecodeError, ModelOutputError, ValueError) as exc:
            last_error = exc
    raise ModelOutputError(f"interview failed validation: {last_error}")
