"""Video physics audit (T37): does an object's motion in an uploaded clip violate the assumed model?

The answer is only ever "consistent", "inconsistent" or "insufficient_data" relative to the assumed
model. Never a judgement on whether the video is real or generated. Tracking is model-free frame
differencing until SAM is wired in; all numbers come from physics/.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from physics.errors import PhysicsInputError
from physics.experiments.freefall import check_flight, fit_flight
from physics.persistence import persistence_events
from physics.tracking import Detection

from . import schemas as S
from .store import UPLOAD_ROOT, new_id, now, store
from .video import read_frames, save_overlay, track

router = APIRouter()

MIN_TRACKED_FRACTION = 0.8  # same value as the frozen gate rule
LIMITS = [
    "Tracking uses frame differencing, not a model; motion blur inflates the object size.",
    "Perspective is not modelled: motion towards or away from the camera is not reliable.",
    "The time window and camera state are confirmed by the user.",
]


@router.post("/api/audits", response_model=S.AuditOut, status_code=201)
def create_audit(
    file: UploadFile = File(...),
    t_start: float = Form(...),
    t_end: float = Form(...),
    camera_static: bool = Form(...),
    assumed_model: str = Form("free_flight"),
    object_size_m: float | None = Form(None),
):
    if assumed_model != "free_flight":
        raise HTTPException(422, "only assumed_model=free_flight is supported")
    if not 0 <= t_start < t_end:
        raise HTTPException(422, "need 0 <= t_start < t_end")
    if object_size_m is not None and object_size_m <= 0:
        raise HTTPException(422, "object_size_m must be positive")

    aid = new_id("aud")
    d = UPLOAD_ROOT / "audits" / aid
    d.mkdir(parents=True, exist_ok=True)
    suffix = "".join(c for c in (file.filename or "").rsplit(".", 1)[-1:] if c.isalnum())[:5] or "bin"
    video = d / f"video.{suffix}"
    with video.open("wb") as out:
        out.write(file.file.read())

    rec = {
        "audit_id": aid, "created_at": now(), "assumed_model": assumed_model,
        "t_start": t_start, "t_end": t_end, "camera_static": camera_static, "object_size_m": object_size_m,
        "video_url": f"/media/audits/{aid}/{video.name}", "overlay_url": None,
        "track_source": "frame_diff", "verdict": "insufficient_data", "reasons": [], "numbers": {},
        "points": [], "events": [], "limits": LIMITS,
    }
    if not camera_static:
        rec["reasons"] = ["camera is not static; this check needs a fixed camera"]
        store.audits[aid] = rec
        return rec

    try:
        frames, fps = read_frames(str(video), t_start, t_end)
    except Exception:
        raise HTTPException(422, "could not read video frames in that window")
    pts, size_px = track(frames, fps, t_start)
    save_overlay(frames, pts, t_start, fps, str(d / "overlay.png"))
    rec["overlay_url"] = f"/media/audits/{aid}/overlay.png"
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
