"""Video physics audit (T37): does an object's motion in an uploaded clip violate the assumed model?

The answer is only ever "consistent", "inconsistent" or "insufficient_data" relative to the assumed
model. Never a judgement on whether the video is real or generated. Tracking is model-free frame
differencing until SAM is wired in; all numbers come from physics/.
"""
from __future__ import annotations

import os

import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from physics.errors import PhysicsInputError
from physics.experiments.pendulum import check_pendulum
from physics.experiments.vehicle import VEHICLE_CLASS_LENGTH_M, check_drive, fit_drive
from physics.experiments.freefall import (check_bounces, check_flight, fit_flight, ghost_track, gravity_ruler,
                                         nearest_body, suggest_flight_windows)
from physics.persistence import persistence_events, size_trend
from physics.tracking import Detection

from . import schemas as S
from .explain import explain_audit
from .model_hooks import MOCK_QUESTIONS, TrackingUnavailable, get_hooks
from .output_check import check_model_text, extract_numbers
from .store import UPLOAD_ROOT, UploadTooLarge, copy_limited, new_id, now, store
from physics.camera_motion import compensate, measure_camera_motion

from .video import (LONG_SIDE_PX, clip_duration, color_for, held_fps, probe_fps, read_frames, read_frames_rgb,
                    save_overlay, shrink_video, track_color, track_with_sizes)

router = APIRouter()

MIN_TRACKED_FRACTION = 0.8  # same value as the frozen gate rule
EARTH_HEADLINE_BAND = (0.85, 1.15)  # g_vs_earth inside this reads as "Earth-like" in a headline
MAX_CAMERA_SHIFT = 0.15  # a moving camera is corrected only up to 15% of the frame width
MIN_CAMERA_SHIFT_PX = 1.0  # below this the camera counts as still: no correction, results unchanged
MAX_WINDOW_S = 60.0  # SAM's own per-request limit; long windows are read at a lower frame rate (T243)
MAX_SIZE_TREND = 0.3  # object size may change by at most 30% along the track (perspective)
SIZE_ERROR = 0.3  # assumed worst-case error of the object's pixel size, same as gate question 2
MODELS = ("free_flight", "bounce", "pendulum", "vehicle")
LIMITS = [
    "Without SAM, tracking is model-free (colour + motion when the object name gives a colour, otherwise frame "
    "differencing); frame differencing can lock onto other moving things.",
    "Perspective is not modelled: motion towards or away from the camera is not reliable.",
    "The time window and camera state are confirmed by the user.",
]


MAX_QUESTIONS = 3


def _model_view(rec: dict) -> dict:
    """What the model sees of a result: verdict, reasons and the program's numbers, never the raw track."""
    return {k: v for k, v in rec.items() if k not in ("audit_id", "created_at", "points", "ghost_points", "events", "video_url", "overlay_url")}


def _number_sources(view: dict) -> list:
    """The result plus each number rounded to 0-4 decimals, so a model sentence may quote a rounded value.
    Numbers inside the program's own sentences (e.g. the 8.34-11.28 range in a reason) count too (T115): they
    come from physics/, not from the model."""
    rounded = {f"{k}_r{d}": round(v, d) for k, v in view.get("numbers", {}).items() for d in range(5)}
    in_text = [v for r in view.get("reasons", []) if isinstance(r, str) for _, v, _ in extract_numbers(r)]
    return [view, rounded, {"reason_numbers": in_text}]


def _model_text(hook_name: str, view: dict) -> str | None:
    """Ask the connected Meta model (T143) for text about a finished audit. Any failure, a missing hook, or
    text that fails the backend's own check (unfound numbers, banned wording) gives None, so the caller keeps
    the fixed template (AGENTS.md rule 5). The verdict and numbers never come from here."""
    hook = getattr(get_hooks(), hook_name, None)
    if hook is None or os.environ.get("SLOPE_MODEL_TEXT") == "0":  # batch runs skip paid text calls
        return None
    try:
        text = hook(dict(view))
    except Exception:  # budget cap, network, validation: a model failure must never break the audit
        return None
    if not isinstance(text, str) or not text.strip() or not check_model_text(text, _number_sources(view)).ok:
        return None
    return text.strip()


def _track_check(video: Path, points: list, object_name: str) -> dict | None:
    """Muse Spark looks at 4 ringed frames of the SAM track (T203/T207). Only a yes/no and a short note come
    back; a failure, a missing hook or a malformed answer means no check (None), never a changed number."""
    hook = getattr(get_hooks(), "track_check", None)
    if hook is None or os.environ.get("SLOPE_MODEL_TEXT") == "0":
        return None
    try:
        out = hook(video, points, object_name)
    except Exception:
        return None
    if not isinstance(out, dict) or not isinstance(out.get("same_object"), bool):
        return None
    note = out.get("note") if isinstance(out.get("note"), str) else ""
    if note and not check_model_text(note, []).ok:
        note = ""
    return {"same_object": out["same_object"], "note": note, "source": "model"}


def _model_list(hook_name: str, view: dict) -> list[str] | None:
    """Like _model_text, for a hook that returns a few short lines (retake tips); every line must pass."""
    hook = getattr(get_hooks(), hook_name, None)
    if hook is None or os.environ.get("SLOPE_MODEL_TEXT") == "0":
        return None
    try:
        lines = hook(dict(view))
    except Exception:
        return None
    if not isinstance(lines, list) or not lines or not all(isinstance(x, str) and x.strip() for x in lines):
        return None
    if not all(check_model_text(x, _number_sources(view)).ok for x in lines):
        return None
    return [x.strip() for x in lines[:3]]


def _finish(rec: dict) -> dict:
    rec["explanation"] = explain_audit(rec)
    rec.setdefault("track_check", None)
    view = _model_view(rec)
    # A one-line "how Earth-like is g" headline only when it cannot contradict the verdict (T241): live testing
    # showed "looks like Earth, 1.06x" above an Inconsistent verdict caused by a scattered track.
    g_ratio = (rec.get("numbers") or {}).get("g_vs_earth")
    earth_like = g_ratio is not None and EARTH_HEADLINE_BAND[0] <= g_ratio <= EARTH_HEADLINE_BAND[1]
    show = rec["verdict"] == "consistent" or (rec["verdict"] == "inconsistent" and not earth_like)
    wants_tips = rec["verdict"] == "insufficient_data"
    wants_fit = rec["verdict"] == "inconsistent" and rec["assumed_model"] == "free_flight"
    # Each text is its own model call; one after another they took most of a check's wait (T243).
    with ThreadPoolExecutor(max_workers=3) as pool:
        tips = pool.submit(_model_list, "retake_tips", view) if wants_tips else None
        fit = pool.submit(_model_text, "what_would_fit", view) if wants_fit else None
        text = pool.submit(_model_text, "explain_audit", view)
        headline = pool.submit(_model_text, "headline_audit", view) if show else None
    rec["retake_tips"] = tips.result() if tips else None
    fit_text = fit.result() if fit else None
    rec["what_would_fit"] = {"source": "model", "text": fit_text} if fit_text else None
    if text.result():
        rec["explanation"] = {"source": "model", "text": text.result()}
    headline_text = headline.result() if headline else None
    rec["headline"] = {"source": "model", "text": headline_text} if headline_text else None
    return rec


def _save_upload(file: UploadFile, d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    suffix = "".join(c for c in (file.filename or "").rsplit(".", 1)[-1:] if c.isalnum())[:5] or "bin"
    video = d / f"video.{suffix}"
    try:
        copy_limited(file.file, video)
    except UploadTooLarge as e:
        raise HTTPException(413, str(e))
    if os.environ.get("PUBLIC_DEMO") == "1" and max(_frame_size(video)) > LONG_SIDE_PX:
        small = d / "video_small.mp4"
        try:
            shrink_video(str(video), str(small))  # a 4K clip crashed the 512 MB public host (T240, T243)
        except (subprocess.SubprocessError, OSError):
            raise HTTPException(422, "could not read this video; is it a complete video file?")
        video.unlink(missing_ok=True)
        return small
    return video


def _frame_size(video: Path) -> tuple[int, int]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout.strip().splitlines()
    try:
        w, h = (int(v) for v in out[0].split(",")[:2])
    except (IndexError, ValueError):
        raise HTTPException(422, "could not read the video size; is this a video file?")
    return w, h


def checked_interview(iv: S.AuditInterview) -> S.AuditInterview:
    """Model questions may not carry numbers or banned wording, at most one per field and three in all.
    Anything else falls back to the fixed questions (AGENTS.md rule 5)."""
    fields = [q.field for q in iv.questions]
    problems = []
    if not 1 <= len(iv.questions) <= MAX_QUESTIONS or len(set(fields)) != len(fields):
        problems.append("question count or duplicate fields")
    for q in iv.questions:
        problems += check_model_text(q.text, []).problems
    if problems:
        return S.AuditInterview(source="mock", questions=MOCK_QUESTIONS,
                                note="model questions failed checks: " + "; ".join(problems))
    return iv


def track_points(video: Path, frames, fps: float, t_start: float, t_end: float, object_name: str,
                 widths: list | None = None):
    """SAM 3.1 when connected; otherwise colour + motion when the object name gives a colour (T88, same
    tracker as the gate), otherwise frame differencing. SAM output is normalised and converted here to the
    same 480 px frame the rest of the audit uses; frames SAM misses stay gaps.

    Also returns the sample times the tracker looked at: SAM samples at its own rate (15 fps), so the tracked
    fraction and the gap events are counted against SAM's samples, not the video's frames (T146 fix: counting
    against 24 or 30 fps frames capped every SAM track at 15/24 = 62% and refused every clip).

    With widths, also appends each tracked frame's box width in the same 480 px frame (vehicle check); SAM
    frames without a width leave it out."""
    h, w = frames.shape[1], frames.shape[2]
    try:
        dets = get_hooks().track_object(video, object_name, t_start, t_end)
    except TrackingUnavailable:
        dets = None
    except Exception:  # a model failure falls back to the model-free tracker, never blocks the audit
        dets = None
    if dets:
        pts, sizes, times = [], [], []
        for d in sorted(dets, key=lambda d: d.t_s):
            if not t_start <= d.t_s <= t_end:
                continue
            times.append(d.t_s)
            if d.centroid_px is None:
                continue
            x, y = d.centroid_px
            if not (0 <= x <= 1 and 0 <= y <= 1):
                continue  # outside the contract: drop rather than guess
            pts.append((d.t_s, x * w, y * h))
            sizes.append(((d.area_px or 0) * w * h) ** 0.5)
            if widths is not None and d.width_px:
                widths.append(d.width_px * w)
        if pts:
            return pts, sizes, "sam", times
    times = [t_start + i / fps for i in range(len(frames))]
    color = color_for(object_name)
    if color:
        pts, sizes = track_color(read_frames_rgb(str(video), t_start, t_end, fps), fps, t_start, color, widths=widths)
        return pts, sizes, "color", times
    pts, sizes = track_with_sizes(frames, fps, t_start, widths=widths)
    return pts, sizes, "frame_diff", times


@router.post("/api/audit-drafts", response_model=S.AuditDraftOut, status_code=201)
def create_draft(file: UploadFile = File(...)):
    """Step 1 of the Muse interview: store the clip and let the model ask what it needs to know."""
    did = new_id("drf")
    return _start_draft(did, _save_upload(file, UPLOAD_ROOT / "audits" / did))


# Clips a visitor can try without their own video (T234). Each label says what the clip is; the
# verdict is still computed live by the same pipeline, never stored here.
SAMPLES: dict[str, dict] = {
    "meta_ai_ball_4": {"path": "data/gate/clips/meta_clip4.mp4", "kind": "generated",
                       "label": "Ball clip made with the Meta AI app"},
    "meta_ai_ball_2": {"path": "data/gate/clips/meta_clip2.mp4", "kind": "generated",
                       "label": "Another Meta AI app ball clip (camera angle changes)"},
    "synthetic_toss": {"path": "data/samples/synthetic_toss_earth_g.mp4", "kind": "synthetic",
                       "label": "Synthetic test clip: a 6 cm square thrown under Earth gravity, drawn by code"},
}


@router.get("/api/samples")
def list_samples():
    return [{"name": k, "kind": v["kind"], "label": v["label"]} for k, v in SAMPLES.items() if Path(v["path"]).is_file()]


@router.post("/api/samples/{name}/draft", response_model=S.AuditDraftOut, status_code=201)
def create_sample_draft(name: str):
    """Start the same interview flow from a bundled sample clip."""
    sample = SAMPLES.get(name)
    if sample is None or not Path(sample["path"]).is_file():
        raise HTTPException(404, f"sample {name} not found")
    did = new_id("drf")
    d = UPLOAD_ROOT / "audits" / did
    d.mkdir(parents=True, exist_ok=True)
    video = d / "video.mp4"
    shutil.copyfile(sample["path"], video)
    return _start_draft(did, video)


def _start_draft(did: str, video: Path) -> dict:
    store.audit_drafts[did] = str(video)
    try:
        iv = checked_interview(get_hooks().interview_audit(video))
    except Exception as e:  # a model failure must not block the audit
        iv = S.AuditInterview(source="mock", questions=MOCK_QUESTIONS, note=f"model unavailable: {type(e).__name__}")
    return {"draft_id": did, "video_url": f"/media/audits/{did}/{video.name}", "interview": iv,
            "suggestion": checked_suggestion(video)}


def checked_suggestion(video: Path) -> S.ObjectSuggestion | None:
    """Muse Spark's object-name guess (T147). Dropped unless it is a short name with no digits (a size in the
    name would look like a measurement) and the reason passes the banned-phrase check."""
    hook = getattr(get_hooks(), "suggest_object", None)
    if hook is None:
        return None
    try:
        raw = hook(video)
        sug = S.ObjectSuggestion(**raw)
    except Exception:
        return None
    name = sug.object_name.strip()
    if not name or len(name) > 60 or any(c.isdigit() for c in name + sug.reason):
        return None
    if not check_model_text(f"{name}. {sug.reason}", []).ok:
        return None
    return sug


VOICE_FIELDS = {"camera_static": bool, "slow_motion": bool, "object_size_m": float, "length_m": float,
                "assumed_model": str, "time_window": list}
MAX_AUDIO_BYTES = 10 * 1024 * 1024


def checked_voice_fields(fields: dict) -> dict:
    """Keep only known fields with the right type and a sane value; the user still confirms each one."""
    out = {}
    for name, f in (fields or {}).items():
        kind, v = VOICE_FIELDS.get(name), (f or {}).get("value")
        if kind is bool and isinstance(v, bool):
            out[name] = {"value": v}
        elif kind is float and isinstance(v, (int, float)) and not isinstance(v, bool) and 0 < v <= 100:
            out[name] = {"value": float(v)}
        elif kind is str and v in MODELS:
            out[name] = {"value": v}
        elif kind is list and isinstance(v, list) and len(v) == 2 and all(
                isinstance(x, (int, float)) and not isinstance(x, bool) and x >= 0 for x in v) and v[0] < v[1]:
            out[name] = {"value": [float(v[0]), float(v[1])]}
    return out


@router.post("/api/audit-drafts/{did}/voice", response_model=S.VoiceAnswerOut)
def voice_answer(did: str, audio: UploadFile = File(...)):
    """Spoken answer to the interview (T147): Voice Transcribe turns it into text, Spark pulls out fields.
    Nothing is applied: every field comes back unconfirmed for the user to check on screen."""
    if did not in store.audit_drafts:
        raise HTTPException(404, f"draft {did} not found")
    data = audio.file.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "audio is larger than 10 MB")
    hook = getattr(get_hooks(), "answer_voice", None)
    if hook is None:
        return {"source": {"transcript": "mock", "fields": "mock"}, "transcript": "", "fields": {}}
    d = Path(store.audit_drafts[did]).parent
    suffix = "".join(c for c in (audio.filename or "").rsplit(".", 1)[-1:] if c.isalnum())[:5] or "webm"
    path = d / f"voice.{suffix}"
    path.write_bytes(data)
    try:
        raw = hook(path)
    except Exception as e:
        raise HTTPException(502, f"voice model unavailable: {type(e).__name__}")
    src = raw.get("source") or {}
    return {"source": {"transcript": str(src.get("transcript", "model")), "fields": str(src.get("fields", "model"))},
            "transcript": str(raw.get("transcript", ""))[:2000], "fields": checked_voice_fields(raw.get("fields"))}


SCAN_MAX_FPS = 30.0  # window suggestions look at the whole clip, at most 30 frames a second (T240, T243)


@router.post("/api/audit-drafts/{did}/windows", response_model=S.FlightWindowsOut)
def suggest_windows(did: str, object_name: str = Form("ball", max_length=60)):
    """Candidate flight windows for the user to pick from (T141). Model-free; the audit still uses only
    the window the user confirms."""
    if did not in store.audit_drafts:
        raise HTTPException(404, f"draft {did} not found")
    video = store.audit_drafts[did]
    color = color_for(object_name)
    try:
        seconds = clip_duration(str(video))
        fps = min(SCAN_MAX_FPS, held_fps(str(video), seconds, 3 if color else 1))
        frames, fps = ((read_frames_rgb(str(video), 0.0, seconds, fps), fps) if color
                       else read_frames(video, 0.0, seconds, fps))
    except Exception:
        raise HTTPException(422, "could not read video frames")
    pts, _ = track_color(frames, fps, 0.0, color) if color else track_with_sizes(frames, fps, 0.0)
    wins = suggest_flight_windows(pts)
    return {"draft_id": did, "track_source": "color" if color else "frame_diff",
            "windows": [{"t_start": a, "t_end": b} for a, b in wins],
            "scanned_until_s": len(frames) / fps}


@router.post("/api/audits", response_model=S.AuditOut, status_code=201)
def create_audit(
    file: UploadFile | None = File(None),
    draft_id: str | None = Form(None),
    slow_motion: bool | None = Form(None),
    t_start: float = Form(...),
    t_end: float = Form(...),
    camera_static: bool = Form(...),
    assumed_model: str = Form("free_flight"),
    object_size_m: float | None = Form(None),
    object_name: str = Form("ball", max_length=60),  # text prompt for SAM, e.g. "tennis ball"
    length_m: float | None = Form(None),  # pendulum only: user-measured string length to the bob centre
    vehicle_class: str | None = Form(None),  # vehicle only: user-confirmed class; sets the length range
):
    if assumed_model not in MODELS:
        raise HTTPException(422, f"assumed_model must be one of {MODELS}")
    if not 0 <= t_start < t_end:
        raise HTTPException(422, "need 0 <= t_start < t_end")
    if t_end - t_start > MAX_WINDOW_S:
        raise HTTPException(422, f"time window is longer than {MAX_WINDOW_S:.0f} s; pick the seconds where the motion happens")
    if object_size_m is not None and object_size_m <= 0:
        raise HTTPException(422, "object_size_m must be positive")
    if length_m is not None and length_m <= 0:
        raise HTTPException(422, "length_m must be positive")
    if vehicle_class is not None and vehicle_class not in (*VEHICLE_CLASS_LENGTH_M, "unknown"):
        raise HTTPException(422, f"vehicle_class must be one of {[*VEHICLE_CLASS_LENGTH_M, 'unknown']}")

    if (file is None) == (draft_id is None):
        raise HTTPException(422, "send either a file or a draft_id")
    aid = new_id("aud")
    if draft_id is not None:
        if draft_id not in store.audit_drafts:
            raise HTTPException(404, f"draft {draft_id} not found")
        video = Path(store.audit_drafts.pop(draft_id))
        d = video.parent
        media = f"/media/audits/{draft_id}"
    else:
        d = UPLOAD_ROOT / "audits" / aid
        video = _save_upload(file, d)
        media = f"/media/audits/{aid}"

    rec = {
        "audit_id": aid, "created_at": now(), "assumed_model": assumed_model,
        "t_start": t_start, "t_end": t_end, "camera_static": camera_static, "object_size_m": object_size_m,
        "length_m": length_m, "vehicle_class": vehicle_class,
        "slow_motion": slow_motion, "video_url": f"{media}/{video.name}", "overlay_url": None,
        "track_source": "frame_diff", "verdict": "insufficient_data", "reasons": [], "numbers": {},
        "points": [], "ghost_points": [], "nearest_body": None, "events": [], "limits": LIMITS,
    }
    if not camera_static and assumed_model == "vehicle":
        # A camera following a car pans by design; car length as the ruler needs a fixed view.
        rec["reasons"] = ["camera is not static; the vehicle check needs a fixed camera"]
        store.audits[aid] = _finish(rec)
        return rec

    try:
        frames, fps = read_frames(str(video), t_start, t_end, held_fps(str(video), t_end - t_start))
    except Exception:
        raise HTTPException(422, "could not read video frames in that window")
    widths: list[float] = []
    pts, sizes, source, times = track_points(video, frames, fps, t_start, t_end, object_name, widths)
    rec["track_source"] = source
    size_px = sorted(sizes)[len(sizes) // 2] if sizes else None
    save_overlay(frames, pts, t_start, fps, str(d / "overlay.png"))
    rec["overlay_url"] = f"{media}/overlay.png"
    rec["points"] = [[t, x, y] for t, x, y in pts]
    by_t = {round(t, 4): (x, y) for t, x, y in pts}
    dets = [Detection(t, by_t.get(round(t, 4))) for t in times]
    rec["events"] = [e.__dict__ for e in persistence_events(dets)]
    frac = len(pts) / max(len(times), 1)
    rec["numbers"]["tracked_fraction"] = frac
    if source == "sam" and frac >= MIN_TRACKED_FRACTION:
        # A warning only (11/01): the same clip got true on one run and false on the next, so a model answer
        # must not flip a verdict that one frozen rule set computed. The page shows the warning next to it.
        rec["track_check"] = _track_check(video, rec["points"], object_name)
    if frac < MIN_TRACKED_FRACTION:
        rec["reasons"] = [f"object tracked in only {frac:.0%} of frames"]
        store.audits[aid] = _finish(rec)
        return rec

    # Camera shake / small pan (T244): measure the background's shift and, when it is a reliable pure
    # translation, remove it from the track. A moving camera is judged only after that correction.
    if assumed_model != "vehicle" and pts:
        rad = 1.5 * size_px + 6 if size_px else 20.0
        idx = [min(len(frames) - 1, max(0, round((t - t_start) * fps))) for t, _, _ in pts]
        motion = measure_camera_motion(frames, idx, [(x, y) for _, x, y in pts], rad)
        rec["numbers"]["camera_shift_max_px"] = motion.max_shift_px
        movable = motion.reliable and motion.translational and motion.max_shift_px <= MAX_CAMERA_SHIFT * frames.shape[2]
        if not camera_static and not movable:
            why = ("the background is too plain to measure how the camera moved" if not motion.reliable else
                   "the camera rotated or zoomed, which a 2D correction cannot undo" if not motion.translational
                   else "the camera moved too far")
            rec["reasons"] = [f"camera is not static and {why}; this check needs a fixed or only slightly moving camera"]
            store.audits[aid] = _finish(rec)
            return rec
        if movable and motion.max_shift_px > MIN_CAMERA_SHIFT_PX:
            pts = compensate(pts, motion)
            rec["points"] = [[t, x, y] for t, x, y in pts]
            rec["numbers"]["camera_corrected"] = 1.0
            rec["limits"] = [*rec["limits"], f"The camera moved up to {motion.max_shift_px:.1f} px during the window; "
                             "the track was corrected for that shift (side-to-side / up-down only)."]

    trend = size_trend([p[0] for p in pts], sizes)
    if trend is not None:
        rec["numbers"]["size_trend"] = trend
        if abs(trend) > MAX_SIZE_TREND:
            rec["reasons"] = [f"object size changes {trend:+.0%} along the track; it moves towards or away "
                              "from the camera, which this 2D check cannot judge"]
            store.audits[aid] = _finish(rec)
            return rec

    if slow_motion and assumed_model in ("free_flight", "pendulum", "vehicle"):
        rec["reasons"] = ["the user says the clip is slow motion, so its timing is not real time and "
                          f"the {assumed_model} timing check cannot be judged"]
        store.audits[aid] = _finish(rec)
        return rec

    if assumed_model == "pendulum":
        try:
            p = check_pendulum([q[0] for q in pts], [q[1] for q in pts], length_m=length_m)
        except PhysicsInputError as e:
            rec["reasons"] = [str(e)]
            store.audits[aid] = _finish(rec)
            return rec
        rec["verdict"], rec["reasons"] = p.verdict, list(p.reasons)
        rec["numbers"] |= {"period_s": p.period_s, "period_spread": p.period_spread,
                           "implied_length_m": p.implied_length_m, "predicted_period_s": p.predicted_period_s}
        rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v is not None}
        store.audits[aid] = _finish(rec)
        return rec

    if assumed_model == "vehicle":
        try:
            v = check_drive(fit_drive(pts), widths, car_length_m=object_size_m, vehicle_class=vehicle_class)
        except PhysicsInputError as e:
            rec["reasons"] = [str(e)]
            store.audits[aid] = _finish(rec)
            return rec
        rec["verdict"], rec["reasons"] = v.verdict, list(v.reasons)
        rec["numbers"] |= {"car_length_px": v.length_px, "speed_car_lengths_s": v.speed_lengths_s,
                           "accel_car_lengths_s2": v.accel_lengths_s2, "car_length_for_max_accel_m": v.length_for_max_accel_m,
                           "speed_m_s": v.speed_m_s, "speed_km_h": v.speed_m_s * 3.6 if v.speed_m_s is not None else None,
                           "accel_m_s2": v.accel_m_s2, "accel_g": v.accel_g, "n_points": float(len(pts))}
        if v.length_range_m is not None:
            lo, hi = v.length_range_m
            rec["numbers"] |= {"car_length_low_m": lo, "car_length_high_m": hi,
                               "speed_km_h_low": v.speed_lengths_s * lo * 3.6, "speed_km_h_high": v.speed_lengths_s * hi * 3.6,
                               "accel_g_low": abs(v.accel_lengths_s2) * lo / 9.81, "accel_g_high": abs(v.accel_lengths_s2) * hi / 9.81}
        rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v is not None and v == v and abs(v) != float("inf")}
        store.audits[aid] = _finish(rec)
        return rec

    if assumed_model == "bounce":
        b = check_bounces(pts)
        rec["verdict"], rec["reasons"] = b.verdict, list(b.reasons)
        rec["numbers"] |= {f"rebound_ratio_{i + 1}": e * e for i, e in enumerate(b.restitution)}
        rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v == v and abs(v) != float("inf")}
        store.audits[aid] = _finish(rec)
        return rec

    m_per_px = object_size_m / size_px if object_size_m and size_px else None
    try:
        fit = fit_flight(pts)
        chk = check_flight(fit, m_per_px=m_per_px, object_size_px=size_px)
    except PhysicsInputError as e:
        rec["reasons"] = [str(e)]
        store.audits[aid] = _finish(rec)
        return rec
    rec["verdict"] = chk.verdict
    rec["reasons"] = list(chk.reasons)
    if m_per_px and chk.g_apparent_m_s2:
        rec["ghost_points"] = [list(p) for p in ghost_track(fit, [p[0] for p in pts], m_per_px)]
        rec["nearest_body"], rec["numbers"]["g_vs_earth"] = nearest_body(chk.g_apparent_m_s2)
        # If the measured pixel size of the object is off by 30% (motion blur, mask edges), does the g verdict hold?
        g = chk.g_apparent_m_s2
        lo, hi = g / (1 + SIZE_ERROR), g / (1 - SIZE_ERROR)
        inside = [9.81 * (1 - 0.15) <= v <= 9.81 * (1 + 0.15) for v in (lo, g, hi)]
        rec["numbers"] |= {"g_apparent_low": lo, "g_apparent_high": hi,
                           "g_verdict_robust": float(all(inside) or not any(inside))}
    # Gravity as a ruler (no size needed): metres and speeds *if* this is Earth gravity at normal speed.
    ruler = gravity_ruler(fit)
    rec["numbers"] |= {
        "if_earth_flight_time_s": ruler.flight_time_s, "if_earth_vertical_extent_m": ruler.vertical_extent_m,
        "if_earth_launch_speed_m_s": ruler.launch_speed_m_s, "if_earth_launch_angle_deg": ruler.launch_angle_deg,
    }
    rec["numbers"] |= {
        "a_px_s2": fit.a_px_s2, "tilt_deg": fit.tilt_deg, "rms_over_travel": fit.rms_residual_px / fit.travel_px,
        "g_apparent_m_s2": chk.g_apparent_m_s2, "implied_time_factor": chk.implied_time_factor,
        "implied_object_size_m": chk.implied_object_size_m, "n_points": fit.n,
    }
    rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v is not None and v == v and abs(v) != float("inf")}
    store.audits[aid] = _finish(rec)
    return rec


@router.get("/api/audits/{aid}", response_model=S.AuditOut)
def get_audit(aid: str):
    if aid not in store.audits:
        raise HTTPException(404, f"audit {aid} not found")
    return store.audits[aid]


# ---------- background audits (T245) ----------
# A check on the free public host can take minutes; one long HTTP request then times out in the browser and the
# result is lost although it was computed and paid for. A job runs the same create_audit() in a thread and the
# page polls for it. The verdict and numbers are exactly those of POST /api/audits.
JOBS: dict[str, dict] = {}
_JOB_POOL = ThreadPoolExecutor(max_workers=int(os.environ.get("AUDIT_JOB_WORKERS", "2")))


def _run_job(jid: str, kwargs: dict) -> None:
    try:
        rec = create_audit(file=None, **kwargs)
        JOBS[jid] |= {"status": "done", "audit_id": rec["audit_id"], "finished_at": time.time()}
    except HTTPException as e:
        JOBS[jid] |= {"status": "failed", "error": str(e.detail), "status_code": e.status_code, "finished_at": time.time()}
    except Exception as e:  # never leave a job running forever
        JOBS[jid] |= {"status": "failed", "error": f"internal error: {type(e).__name__}", "status_code": 500,
                      "finished_at": time.time()}


@router.post("/api/audit-jobs", status_code=202)
def create_audit_job(
    file: UploadFile | None = File(None),
    draft_id: str | None = Form(None),
    slow_motion: bool | None = Form(None),
    t_start: float = Form(...),
    t_end: float = Form(...),
    camera_static: bool = Form(...),
    assumed_model: str = Form("free_flight"),
    object_size_m: float | None = Form(None),
    object_name: str = Form("ball", max_length=60),
    length_m: float | None = Form(None),
    vehicle_class: str | None = Form(None),
):
    """Same inputs as POST /api/audits; returns at once with a job id to poll at GET /api/audit-jobs/{id}."""
    if (file is None) == (draft_id is None):
        raise HTTPException(422, "send either a file or a draft_id")
    if file is not None:  # store the upload now: the request's file is closed once this handler returns
        draft_id = new_id("drf")
        store.audit_drafts[draft_id] = str(_save_upload(file, UPLOAD_ROOT / "audits" / draft_id))
    elif draft_id not in store.audit_drafts:
        raise HTTPException(404, f"draft {draft_id} not found")
    jid = new_id("job")
    JOBS[jid] = {"job_id": jid, "status": "running", "started_at": time.time()}
    _JOB_POOL.submit(_run_job, jid, dict(
        draft_id=draft_id, slow_motion=slow_motion, t_start=t_start, t_end=t_end, camera_static=camera_static,
        assumed_model=assumed_model, object_size_m=object_size_m, object_name=object_name, length_m=length_m,
        vehicle_class=vehicle_class))
    return {"job_id": jid, "status": "running"}


@router.get("/api/audit-jobs/{jid}")
def get_audit_job(jid: str):
    """status: running | done | failed. When done, `audit` is the same AuditOut as GET /api/audits/{id}."""
    job = JOBS.get(jid)
    if job is None:
        raise HTTPException(404, f"job {jid} not found (the free server may have restarted)")
    out = {k: job[k] for k in ("job_id", "status") if k in job}
    out["elapsed_s"] = round((job.get("finished_at") or time.time()) - job["started_at"], 1)
    if job["status"] == "done":
        out["audit"] = get_audit(job["audit_id"])
    elif job["status"] == "failed":
        out |= {"error": job["error"], "status_code": job["status_code"]}
    return out
