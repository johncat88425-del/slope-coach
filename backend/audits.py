"""Video physics audit (T37): does an object's motion in an uploaded clip violate the assumed model?

The answer is only ever "consistent", "inconsistent" or "insufficient_data" relative to the assumed
model. Never a judgement on whether the video is real or generated. Tracking is model-free frame
differencing until SAM is wired in; all numbers come from physics/.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from physics.errors import PhysicsInputError
from physics.experiments.pendulum import check_pendulum
from physics.experiments.freefall import check_bounces, check_flight, fit_flight, ghost_track, nearest_body
from physics.persistence import persistence_events, size_trend
from physics.tracking import Detection

from . import schemas as S
from .model_hooks import MOCK_QUESTIONS, TrackingUnavailable, get_hooks
from .output_check import check_model_text
from .store import UPLOAD_ROOT, new_id, now, store
from .video import read_frames, save_overlay, track_with_sizes

router = APIRouter()

MIN_TRACKED_FRACTION = 0.8  # same value as the frozen gate rule
MAX_SIZE_TREND = 0.3  # object size may change by at most 30% along the track (perspective)
SIZE_ERROR = 0.3  # assumed worst-case error of the object's pixel size, same as gate question 2
MODELS = ("free_flight", "bounce", "pendulum")
LIMITS = [
    "Tracking uses frame differencing, not a model; motion blur inflates the object size.",
    "Perspective is not modelled: motion towards or away from the camera is not reliable.",
    "The time window and camera state are confirmed by the user.",
]


MAX_QUESTIONS = 3


def _save_upload(file: UploadFile, d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    suffix = "".join(c for c in (file.filename or "").rsplit(".", 1)[-1:] if c.isalnum())[:5] or "bin"
    video = d / f"video.{suffix}"
    with video.open("wb") as out:
        out.write(file.file.read())
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


def track_points(video: Path, frames, fps: float, t_start: float, t_end: float, object_name: str):
    """SAM 3.1 when connected, otherwise frame differencing. SAM output is normalised and converted
    here to the same 480 px frame the rest of the audit uses; frames SAM misses stay gaps."""
    h, w = frames.shape[1], frames.shape[2]
    try:
        dets = get_hooks().track_object(video, object_name, t_start, t_end)
    except TrackingUnavailable:
        dets = None
    except Exception:  # a model failure falls back to the model-free tracker, never blocks the audit
        dets = None
    if dets:
        pts, sizes = [], []
        for d in sorted(dets, key=lambda d: d.t_s):
            if d.centroid_px is None or not t_start <= d.t_s <= t_end:
                continue
            x, y = d.centroid_px
            if not (0 <= x <= 1 and 0 <= y <= 1):
                continue  # outside the contract: drop rather than guess
            pts.append((d.t_s, x * w, y * h))
            sizes.append(((d.area_px or 0) * w * h) ** 0.5)
        if pts:
            return pts, sizes, "sam"
    pts, sizes = track_with_sizes(frames, fps, t_start)
    return pts, sizes, "frame_diff"


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
    return {"draft_id": did, "video_url": f"/media/audits/{did}/{video.name}", "interview": iv}


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
):
    if assumed_model not in MODELS:
        raise HTTPException(422, f"assumed_model must be one of {MODELS}")
    if not 0 <= t_start < t_end:
        raise HTTPException(422, "need 0 <= t_start < t_end")
    if object_size_m is not None and object_size_m <= 0:
        raise HTTPException(422, "object_size_m must be positive")
    if length_m is not None and length_m <= 0:
        raise HTTPException(422, "length_m must be positive")

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
        "length_m": length_m,
        "slow_motion": slow_motion, "video_url": f"{media}/{video.name}", "overlay_url": None,
        "track_source": "frame_diff", "verdict": "insufficient_data", "reasons": [], "numbers": {},
        "points": [], "ghost_points": [], "nearest_body": None, "events": [], "limits": LIMITS,
    }
    if not camera_static:
        rec["reasons"] = ["camera is not static; this check needs a fixed camera"]
        store.audits[aid] = rec
        return rec

    try:
        frames, fps = read_frames(str(video), t_start, t_end)
    except Exception:
        raise HTTPException(422, "could not read video frames in that window")
    pts, sizes, source = track_points(video, frames, fps, t_start, t_end, object_name)
    rec["track_source"] = source
    size_px = sorted(sizes)[len(sizes) // 2] if sizes else None
    save_overlay(frames, pts, t_start, fps, str(d / "overlay.png"))
    rec["overlay_url"] = f"{media}/overlay.png"
    rec["points"] = [[t, x, y] for t, x, y in pts]
    by_t = {round(t, 4): (x, y) for t, x, y in pts}
    dets = [Detection(t_start + i / fps, by_t.get(round(t_start + i / fps, 4))) for i in range(len(frames))]
    rec["events"] = [e.__dict__ for e in persistence_events(dets)]
    frac = len(pts) / max(len(frames), 1)
    rec["numbers"]["tracked_fraction"] = frac
    if frac < MIN_TRACKED_FRACTION:
        rec["reasons"] = [f"object tracked in only {frac:.0%} of frames"]
        store.audits[aid] = rec
        return rec

    trend = size_trend([p[0] for p in pts], sizes)
    if trend is not None:
        rec["numbers"]["size_trend"] = trend
        if abs(trend) > MAX_SIZE_TREND:
            rec["reasons"] = [f"object size changes {trend:+.0%} along the track; it moves towards or away "
                              "from the camera, which this 2D check cannot judge"]
            store.audits[aid] = rec
            return rec

    if slow_motion and assumed_model in ("free_flight", "pendulum"):
        rec["reasons"] = ["the user says the clip is slow motion, so its timing is not real time and "
                          f"the {assumed_model} timing check cannot be judged"]
        store.audits[aid] = rec
        return rec

    if assumed_model == "pendulum":
        try:
            p = check_pendulum([q[0] for q in pts], [q[1] for q in pts], length_m=length_m)
        except PhysicsInputError as e:
            rec["reasons"] = [str(e)]
            store.audits[aid] = rec
            return rec
        rec["verdict"], rec["reasons"] = p.verdict, list(p.reasons)
        rec["numbers"] |= {"period_s": p.period_s, "period_spread": p.period_spread,
                           "implied_length_m": p.implied_length_m, "predicted_period_s": p.predicted_period_s}
        rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v is not None}
        store.audits[aid] = rec
        return rec

    if assumed_model == "bounce":
        b = check_bounces(pts)
        rec["verdict"], rec["reasons"] = b.verdict, list(b.reasons)
        rec["numbers"] |= {f"rebound_ratio_{i + 1}": e * e for i, e in enumerate(b.restitution)}
        rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v == v and abs(v) != float("inf")}
        store.audits[aid] = rec
        return rec

    m_per_px = object_size_m / size_px if object_size_m and size_px else None
    try:
        fit = fit_flight(pts)
        chk = check_flight(fit, m_per_px=m_per_px, object_size_px=size_px)
    except PhysicsInputError as e:
        rec["reasons"] = [str(e)]
        store.audits[aid] = rec
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
    rec["numbers"] |= {
        "a_px_s2": fit.a_px_s2, "tilt_deg": fit.tilt_deg, "rms_over_travel": fit.rms_residual_px / fit.travel_px,
        "g_apparent_m_s2": chk.g_apparent_m_s2, "implied_time_factor": chk.implied_time_factor,
        "implied_object_size_m": chk.implied_object_size_m, "n_points": fit.n,
    }
    rec["numbers"] = {k: v for k, v in rec["numbers"].items() if v is not None and v == v and abs(v) != float("inf")}
    store.audits[aid] = rec
    return rec


@router.get("/api/audits/{aid}", response_model=S.AuditOut)
def get_audit(aid: str):
    if aid not in store.audits:
        raise HTTPException(404, f"audit {aid} not found")
    return store.audits[aid]
