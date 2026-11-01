"""Video physics audit (T37): does an object's motion in an uploaded clip violate the assumed model?

The answer is only ever "consistent", "inconsistent" or "insufficient_data" relative to the assumed
model. Never a judgement on whether the video is real or generated. Tracking is model-free frame
differencing until SAM is wired in; all numbers come from physics/.
"""
from __future__ import annotations

import os

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
from .video import color_for, probe_fps, read_frames, read_frames_rgb, save_overlay, track_color, track_with_sizes

router = APIRouter()

MIN_TRACKED_FRACTION = 0.8  # same value as the frozen gate rule
MAX_WINDOW_S = 30.0  # every frame of the window is held in memory; real motions here last a few seconds
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
    rec["retake_tips"] = _model_list("retake_tips", view) if rec["verdict"] == "insufficient_data" else None
    fit = None
    if rec["verdict"] == "inconsistent" and rec["assumed_model"] == "free_flight":
        text = _model_text("what_would_fit", view)
        fit = {"source": "model", "text": text} if text else None
    rec["what_would_fit"] = fit
    text = _model_text("explain_audit", view)
    if text:
        rec["explanation"] = {"source": "model", "text": text}
    headline = _model_text("headline_audit", view)
    rec["headline"] = {"source": "model", "text": headline} if headline else None
    return rec


def _save_upload(file: UploadFile, d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    suffix = "".join(c for c in (file.filename or "").rsplit(".", 1)[-1:] if c.isalnum())[:5] or "bin"
    video = d / f"video.{suffix}"
    try:
        copy_limited(file.file, video)
    except UploadTooLarge as e:
        raise HTTPException(413, str(e))
    return video


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
        pts, sizes = track_color(read_frames_rgb(str(video), t_start, t_end), fps, t_start, color, widths=widths)
        return pts, sizes, "color", times
    pts, sizes = track_with_sizes(frames, fps, t_start, widths=widths)
    return pts, sizes, "frame_diff", times


@router.post("/api/audit-drafts", response_model=S.AuditDraftOut, status_code=201)
def create_draft(file: UploadFile = File(...)):
    """Step 1 of the Muse interview: store the clip and let the model ask what it needs to know."""
    did = new_id("drf")
    video = _save_upload(file, UPLOAD_ROOT / "audits" / did)
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


SCAN_LIMIT_S = 15.0  # window suggestions look at the first 15 s only


@router.post("/api/audit-drafts/{did}/windows", response_model=S.FlightWindowsOut)
def suggest_windows(did: str, object_name: str = Form("ball", max_length=60)):
    """Candidate flight windows for the user to pick from (T141). Model-free; the audit still uses only
    the window the user confirms."""
    if did not in store.audit_drafts:
        raise HTTPException(404, f"draft {did} not found")
    video = store.audit_drafts[did]
    color = color_for(object_name)
    try:
        frames, fps = ((read_frames_rgb(str(video), 0.0, SCAN_LIMIT_S), probe_fps(str(video))) if color
                       else read_frames(video, 0.0, SCAN_LIMIT_S))
    except Exception:
        raise HTTPException(422, "could not read video frames")
    pts, _ = track_color(frames, fps, 0.0, color) if color else track_with_sizes(frames, fps, 0.0)
    wins = suggest_flight_windows(pts)
    return {"draft_id": did, "track_source": "color" if color else "frame_diff",
            "windows": [{"t_start": a, "t_end": b} for a, b in wins],
            "scanned_until_s": min(SCAN_LIMIT_S, len(frames) / fps)}


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
    if not camera_static:
        rec["reasons"] = ["camera is not static; this check needs a fixed camera"]
        store.audits[aid] = _finish(rec)
        return rec

    try:
        frames, fps = read_frames(str(video), t_start, t_end)
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
