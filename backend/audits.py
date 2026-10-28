"""Video physics audit (T37): does an object's motion in an uploaded clip violate the assumed model?

The answer is only ever "consistent", "inconsistent" or "insufficient_data" relative to the assumed
model. Never a judgement on whether the video is real or generated. Tracking is model-free frame
differencing until SAM is wired in; all numbers come from physics/.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from physics.errors import PhysicsInputError
from physics.experiments.pendulum import check_pendulum
from physics.experiments.freefall import check_bounces, check_flight, fit_flight, ghost_track, nearest_body
from physics.persistence import persistence_events, size_trend
from physics.tracking import Detection

from . import schemas as S
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


@router.post("/api/audits", response_model=S.AuditOut, status_code=201)
def create_audit(
    file: UploadFile = File(...),
    t_start: float = Form(...),
    t_end: float = Form(...),
    camera_static: bool = Form(...),
    assumed_model: str = Form("free_flight"),
    object_size_m: float | None = Form(None),
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
        "length_m": length_m,
        "video_url": f"/media/audits/{aid}/{video.name}", "overlay_url": None,
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
    pts, sizes = track_with_sizes(frames, fps, t_start)
    size_px = sorted(sizes)[len(sizes) // 2] if sizes else None
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

    trend = size_trend([p[0] for p in pts], sizes)
    if trend is not None:
        rec["numbers"]["size_trend"] = trend
        if abs(trend) > MAX_SIZE_TREND:
            rec["reasons"] = [f"object size changes {trend:+.0%} along the track; it moves towards or away "
                              "from the camera, which this 2D check cannot judge"]
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
