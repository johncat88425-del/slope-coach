"""Keyframe observations (T269): Spark looks at 3 full stills (takeoff, apex,
landing) and lists anomalies visible to the eye — warping, interpenetration,
a mismatched shadow, appearing/disappearing — without touching the verdict.

`observe_keyframes(video_path, points, object_name)` picks the earliest
tracked time (takeoff), the highest point (apex, smallest y), and the latest
time (landing); each still is sent full-frame at 480 px wide with a red ring
at the tracked spot, so shadows and surroundings stay visible. Points use the
AuditOut convention: (t_s, x, y) with x/y in the 480 px-wide frame.

Returns {"label", "observations", "source"} with one {frame, note} per still,
or None when there is nothing to observe (fewer than 3 tracked points), the
model output fails validation after retries, or the API call itself fails.
None means "not observed", never a verdict: the return carries no verdict
field by construction, and every note passes the banned-phrase check, so
"real", "fake", and "AI" language is rejected, not shown.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Sequence

from backend.output_check import check_model_text

from . import client as _client
from .client import MAX_RETRIES, SPARK_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker
from .exceptions import MediaError, ModelOutputError, SpendLimitExceeded
from .explain import AUTHENTICITY_BANNED
from .spark import _check_priced, _text_format, _usage_to_dict
from .track_check import _draw_ring, _frame_rgb, _to_png_bytes

KEYFRAME_LABELS = ("takeoff", "apex", "landing")
N_KEYFRAMES = 3
RING_RADIUS = 20
RING_WIDTH = 4
MAX_NOTE_CHARS = 200
CLEAN_NOTE = "nothing unusual visible"
# Lone "real"/"AI" slip past the compound-only ban lists but still judge
# authenticity, so they are rejected as whole words ("really" stays allowed).
_LONE_WORD_BANNED = (r"\breal\b", r"\bai\b")

OBSERVATIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "frame": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["frame", "note"],
                "additionalProperties": False,
            },
            "minItems": N_KEYFRAMES,
            "maxItems": N_KEYFRAMES,
        },
    },
    "required": ["observations"],
    "additionalProperties": False,
}

OBSERVATIONS_PROMPT = (
    "You see {n} full stills from one video clip, in time order: takeoff, "
    "highest point, landing. Each has a red ring at the tracked spot of the "
    "{name}. For EACH still in order, report anomalies visible to the eye: "
    "the object warping or changing shape, passing through another surface, "
    "a shadow that does not match the object, or the object appearing or "
    "disappearing. Answer with JSON only, matching the schema: observations "
    "has one entry per still in order, each with frame (takeoff, apex, or "
    "landing) and note (one short English phrase saying what you saw, or "
    f"'{CLEAN_NOTE}'). Describe only what is visible; do not judge whether "
    "the clip is real or say what made it (no 'real', 'fake', 'AI', "
    "'generated', 'proves', 'confirms'). Do not output any numbers at all."
)


def _pick_keyframes(
    points: Sequence[Sequence[float]],
) -> list[tuple[str, float, float, float]]:
    """Takeoff (first), apex (highest), landing (last); needs 3+ points."""
    usable = [(float(p[0]), float(p[1]), float(p[2]))
              for p in points
              if len(p) >= 3 and p[0] is not None and p[1] is not None and p[2] is not None]
    if len(usable) < N_KEYFRAMES:
        return []
    usable.sort(key=lambda p: p[0])
    apex = min(range(len(usable)), key=lambda i: usable[i][1])
    idx = [0, apex, len(usable) - 1]
    if len(set(idx)) < N_KEYFRAMES:  # monotonic fall/rise: spread evenly
        last = len(usable) - 1
        idx = [round(i * last / (N_KEYFRAMES - 1)) for i in range(N_KEYFRAMES)]
    return [(KEYFRAME_LABELS[k],) + usable[i] for k, i in enumerate(idx)]


def _ringed_stills(
    video: Path, picks: list[tuple[str, float, float, float]]
) -> list[str]:
    """Extract each pick full-frame and ring the tracked spot."""
    import base64

    uris = []
    for _, t, x, y in picks:
        frame = _draw_ring(_frame_rgb(video, t), x, y,
                           radius=RING_RADIUS, width=RING_WIDTH)
        uris.append("data:image/png;base64,"
                    + base64.b64encode(_to_png_bytes(frame)).decode("ascii"))
    return uris


def _validate_observations(data: Any) -> list[dict[str, str]]:
    if not isinstance(data, dict):
        raise ModelOutputError("observations must be a JSON object")
    items = data.get("observations")
    if not isinstance(items, list) or len(items) != N_KEYFRAMES:
        raise ModelOutputError(f"observations must have {N_KEYFRAMES} entries")
    out = []
    for item, want in zip(items, KEYFRAME_LABELS):
        if not isinstance(item, dict) or item.get("frame") != want:
            raise ModelOutputError(
                f"observation frames must be {list(KEYFRAME_LABELS)} in order"
            )
        note = item.get("note")
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
        lone = [p for p in _LONE_WORD_BANNED if re.search(p, note.lower())]
        if lone:
            raise ModelOutputError("forbidden authenticity language: lone real/AI")
        out.append({"frame": want, "note": note})
    return out


def observe_keyframes(
    video_path: Path | str,
    points: Sequence[Sequence[float]],
    object_name: str,
    *,
    model: str | None = None,
    timeout: float = _client.SPARK_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> dict[str, Any] | None:
    """Ask Spark to list visible anomalies on 3 keyframe stills (T269).

    Returns {"label", "observations", "source"}, or None when there are fewer
    than 3 tracked points or the observation fails (bad output after retries,
    API error, timeout). MediaError (unreadable video) and SpendLimitExceeded
    still raise; everything model-side degrades to None.
    """
    path = Path(video_path)
    if not path.is_file():
        raise MediaError(f"video file not found: {path}")
    if not object_name or not object_name.strip():
        raise ValueError("object_name must be a non-empty noun phrase")
    picks = _pick_keyframes(points)
    if not picks:
        return None
    resolved = model or SPARK_MODEL
    _check_priced(resolved)
    tracker = tracker or get_tracker()
    tracker.check()
    uris = _ringed_stills(path, picks)
    prompt = OBSERVATIONS_PROMPT.format(n=N_KEYFRAMES, name=object_name.strip())
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
                    text=_text_format("observations", OBSERVATIONS_SCHEMA),
                    timeout=timeout,
                ),
                op="spark.observe_keyframes",
            )
        except (MediaError, SpendLimitExceeded, ValueError):
            raise
        except Exception:
            continue  # transport/API failure: no observation, not a verdict
        usage = _usage_to_dict(getattr(response, "usage", None))
        tracker.record(
            resolved,
            "spark.observe_keyframes",
            input_tokens=usage["input_tokens"],
            cached_tokens=usage["cached_tokens"],
            output_tokens=usage["output_tokens"],
        )
        try:
            out = _validate_observations(json.loads(response.output_text or ""))
            return {"label": "觀察", "observations": out, "source": resolved}
        except (json.JSONDecodeError, ModelOutputError, ValueError):
            continue
    return None
