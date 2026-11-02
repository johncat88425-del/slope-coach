"""FastAPI app. Run: uvicorn backend.main:app --reload"""
from __future__ import annotations

import dataclasses
import math
import os
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from physics.baseline import BaselineEstimate, estimate_baseline
from physics.calibration import Calibration, SlopeGeometry
from physics.compare import compare
from physics.diagnose import evidence_for_next_check
from physics.errors import PhysicsInputError
from physics.experiments import slope
from physics.fit import fit_constant_acceleration
from physics.tracking import Detection, to_samples, usable_fraction

from . import report, schemas as S
from .audits import router as audits_router
from .interventions import CATALOG
from .model_hooks import TrackingUnavailable, get_hooks, set_hooks
from .output_check import check_model_text
from .store import UPLOAD_ROOT, ExperimentRecord, TrialRecord, UploadTooLarge, copy_limited, new_id, now, store

def _wire_model_hooks() -> str:
    """Use real Meta hooks when a key is configured; else stay on mocks.

    Returns "meta" or "mock". Never raises: a missing key, a missing
    meta_client, or a missing SDK all fall back to MockHooks, so the app and
    the test suite run without credentials. Import is lazy so backend never
    hard-depends on the OpenAI SDK.
    """
    if not os.environ.get("MODEL_API_KEY"):
        return "mock"
    try:
        from meta_client.hooks import MetaHooks
    except ImportError:
        return "mock"
    set_hooks(MetaHooks())
    return "meta"


HOOKS_SOURCE = _wire_model_hooks()

app = FastAPI(title="Slope Coach API", version="0.1.0")


@app.middleware("http")
async def persist_after_writes(request, call_next):
    response = await call_next(request)
    if request.method != "GET" and response.status_code < 400:
        store.save()
    return response


# Extra origins (comma separated) for a hosted frontend, e.g. the GitHub Pages site (T228).
_ORIGINS = ["http://localhost:5173"] + [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_ORIGINS, allow_methods=["*"], allow_headers=["*"])

# Public demo guard (T228). With PUBLIC_DEMO=1 each visitor IP may start a limited number of paid
# steps (new drafts and audits) per hour, and uploads are capped smaller. The spend ceiling still applies
# (set SPEND_LIMIT_USD on the host; the image starts with an empty cost log).
PUBLIC_DEMO = os.environ.get("PUBLIC_DEMO") == "1"
PUBLIC_MAX_PER_HOUR = int(os.environ.get("PUBLIC_MAX_PER_HOUR", "10"))
PUBLIC_MAX_GLOBAL_PER_HOUR = int(os.environ.get("PUBLIC_MAX_GLOBAL_PER_HOUR", "30"))  # ~$1.70/h worst case
PUBLIC_MAX_UPLOAD_BYTES = int(os.environ.get("PUBLIC_MAX_UPLOAD_MB", "80")) * 1024 * 1024
_PAID_PATHS = ("/api/audit-drafts", "/api/audits")
_hits: dict[tuple[str, str], list[float]] = {}


def _client_ip(request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


@app.middleware("http")
async def public_demo_guard(request, call_next):
    if PUBLIC_DEMO and request.method == "POST" and (request.url.path in _PAID_PATHS
                                                    or request.url.path.startswith("/api/samples/")):
        size = request.headers.get("content-length")
        if size and size.isdigit() and int(size) > PUBLIC_MAX_UPLOAD_BYTES:
            return JSONResponse({"detail": f"This public demo accepts uploads up to {PUBLIC_MAX_UPLOAD_BYTES // 1048576} MB. "
                                           "Trim the clip to the few seconds that matter."}, status_code=413)
        now = time.time()
        # Separate buckets (T241): preparing a clip and running the check each get PUBLIC_MAX_PER_HOUR, so a
        # visitor can finish that many full checks an hour instead of being stopped after about five.
        key = (_client_ip(request), "audit" if request.url.path == "/api/audits" else "draft")
        recent = [t for t in _hits.get(key, []) if now - t < 3600]
        if len(recent) >= PUBLIC_MAX_PER_HOUR:
            wait_min = max(1, int((3600 - (now - min(recent))) // 60) + 1)
            return JSONResponse({"detail": f"This public demo allows {PUBLIC_MAX_PER_HOUR} checks per visitor each hour. "
                                           f"Please try again in about {wait_min} minutes, or run it locally (see README)."},
                                status_code=429)
        if key[1] == "audit":
            # Site-wide ceiling (T244): the host's spend log restarts empty after a sleep or crash, so the
            # money a stranger can burn is bounded by rate instead: at most this many checks per hour in total.
            everyone = [t for (ip, kind), ts in _hits.items() if kind == "audit" for t in ts if now - t < 3600]
            if len(everyone) >= PUBLIC_MAX_GLOBAL_PER_HOUR:
                return JSONResponse({"detail": "This public demo is busy: the hourly limit for all visitors is reached. "
                                               "Please try again later, or run it locally (see README)."}, status_code=429)
        _hits[key] = recent + [now]
    return await call_next(request)

# Uploaded videos and photos, served as /media/<eid>/<file>. File names are generated server-side.
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=UPLOAD_ROOT), name="media")
app.include_router(audits_router)


# ---------- helpers ----------

def _exp(eid: str) -> ExperimentRecord:
    if eid not in store.experiments:
        raise HTTPException(404, f"experiment {eid} not found")
    return store.experiments[eid]


def _trial(tid: str) -> TrialRecord:
    if tid not in store.trials:
        raise HTTPException(404, f"trial {tid} not found")
    return store.trials[tid]


def _calib(exp: ExperimentRecord, version: int) -> dict:
    if not 1 <= version <= len(exp.calibrations):
        raise HTTPException(404, f"calibration version {version} not found")
    return exp.calibrations[version - 1]


def _calib_objects(c: dict) -> tuple[Calibration, SlopeGeometry]:
    return (
        Calibration(tuple(map(tuple, c["ruler_px"])), c["ruler_length_m"], tuple(c["path_start_px"]), tuple(c["path_end_px"])),
        SlopeGeometry(c["slope_length_m"], c["slope_height_m"]),
    )


def _physics_error(e: PhysicsInputError) -> HTTPException:
    return HTTPException(422, str(e))


def _save_upload(eid: str, f: UploadFile, prefix: str):
    d = UPLOAD_ROOT / eid
    d.mkdir(parents=True, exist_ok=True)
    suffix = "".join(c for c in (f.filename or "").rsplit(".", 1)[-1:] if c.isalnum())[:5]
    path = d / f"{new_id(prefix)}.{suffix or 'bin'}"
    try:
        copy_limited(f.file, path)
    except UploadTooLarge as e:
        raise HTTPException(413, str(e))
    return path


def _media_url(eid: str, path) -> str:
    return f"/media/{eid}/{path.name}"


def _trial_out(t: TrialRecord) -> S.TrialOut:
    return S.TrialOut(
        trial_id=t.trial_id, kind=t.kind, calibration_version=t.calibration_version, uploaded_at=t.uploaded_at,
        video_url=_media_url(t.experiment_id, t.video_path) if t.video_path else None,
        t0_s=t.t0_s, t0_source="user" if t.t0_s is not None else None,
        samples=[S.SampleOut(t_s=s.t_s, s_m=s.s_m, quality=s.quality.value, source=s.source) for s in t.samples],
        usable_fraction=usable_fraction(t.samples),
        manual_frames=sum(s.source == "manual" for s in t.samples),
    )


def _baseline_obj(b: dict) -> BaselineEstimate:
    return BaselineEstimate(b["mu_eff"], b["mu_spread"], b["accel_mean_m_s2"], b["accel_spread_m_s2"], len(b["trial_ids"]))


def _finite(d: dict) -> dict:
    return {k: v for k, v in d.items() if isinstance(v, (int, float)) and math.isfinite(v)}


# ---------- experiments ----------

@app.post("/api/experiments", response_model=S.ExperimentOut, status_code=201)
def create_experiment(body: S.ExperimentIn):
    eid = new_id("exp")
    store.experiments[eid] = ExperimentRecord(eid, body.title, now())
    return get_experiment(eid)


@app.get("/api/experiments/{eid}", response_model=S.ExperimentOut)
def get_experiment(eid: str):
    exp = _exp(eid)
    return S.ExperimentOut(
        experiment_id=eid, title=exp.title, created_at=exp.created_at,
        scene_photos=exp.scene_photos, calibrations=exp.calibrations,
        trials=[_trial_out(store.trials[t]) for t in exp.trial_ids],
        baselines=exp.baselines, predictions=list(exp.predictions.values()),
        comparisons=list(exp.comparisons.values()), interventions=list(exp.interventions.values()),
    )


@app.post("/api/experiments/{eid}/scene-photo", response_model=S.ScenePhotoOut)
def upload_scene_photo(eid: str, file: UploadFile = File(...)):
    exp = _exp(eid)
    path = _save_upload(eid, file, "photo")
    out = {"photo_id": path.stem, "photo_url": _media_url(eid, path), "scene_check": get_hooks().check_scene(path)}
    exp.scene_photos.append(out)
    return out


# ---------- calibration ----------

@app.post("/api/experiments/{eid}/calibrations", response_model=S.CalibrationOut, status_code=201)
def create_calibration(eid: str, body: S.CalibrationIn):
    exp = _exp(eid)
    data = body.model_dump()
    try:
        calib, geom = _calib_objects(data)
    except PhysicsInputError as e:
        raise _physics_error(e)
    data.update(version=len(exp.calibrations) + 1, m_per_px=calib.m_per_px,
                angle_deg=math.degrees(geom.angle_rad), created_at=now())
    exp.calibrations.append(data)
    return data


# ---------- trials ----------

@app.post("/api/experiments/{eid}/trials", response_model=S.TrialOut, status_code=201)
def upload_trial(eid: str, kind: S.TrialKind = Form(...), calibration_version: int = Form(...),
                 file: UploadFile | None = File(None)):
    exp = _exp(eid)
    _calib(exp, calibration_version)
    tid = new_id("trial")
    path = _save_upload(eid, file, "video") if file else None
    store.trials[tid] = TrialRecord(tid, eid, kind.value, calibration_version, now(), path)
    exp.trial_ids.append(tid)
    return _trial_out(store.trials[tid])


@app.get("/api/trials/{tid}", response_model=S.TrialOut)
def get_trial(tid: str):
    return _trial_out(_trial(tid))


def _set_detections(t: TrialRecord, dets: list[S.DetectionIn]) -> None:
    calib, _ = _calib_objects(_calib(store.experiments[t.experiment_id], t.calibration_version))
    t.samples = to_samples([Detection(d.t_s, d.centroid_px, d.area_px, d.source) for d in dets], calib)


@app.post("/api/trials/{tid}/track", response_model=S.TrialOut)
def track_trial(tid: str, text_prompt: str = "sliding block"):
    t = _trial(tid)
    if t.video_path is None:
        raise HTTPException(409, "trial has no video")
    try:
        dets = get_hooks().track_slider(t.video_path, text_prompt)
    except TrackingUnavailable as e:
        raise HTTPException(501, str(e))
    _set_detections(t, dets)
    return _trial_out(t)


@app.put("/api/trials/{tid}/detections", response_model=S.TrialOut)
def put_detections(tid: str, body: S.DetectionsIn):
    """Replace detections, e.g. manual rescue clicks. Manual frames stay marked as manual."""
    t = _trial(tid)
    _set_detections(t, body.detections)
    return _trial_out(t)


@app.get("/api/trials/{tid}/release-suggestion", response_model=S.ReleaseSuggestion)
def release_suggestion(tid: str):
    t = _trial(tid)
    if t.video_path is None:
        raise HTTPException(409, "trial has no video")
    return get_hooks().suggest_release_time(t.video_path)


@app.put("/api/trials/{tid}/release-time", response_model=S.TrialOut)
def set_release_time(tid: str, body: S.ReleaseTimeIn):
    t = _trial(tid)
    t.t0_s = body.t0_s
    return _trial_out(t)


# ---------- baseline and prediction ----------

@app.post("/api/experiments/{eid}/baselines", response_model=S.BaselineOut, status_code=201)
def create_baseline(eid: str, body: S.BaselineIn):
    exp = _exp(eid)
    _, geom = _calib_objects(_calib(exp, body.calibration_version))
    fits = []
    for tid in body.trial_ids:
        t = _trial(tid)
        if t.experiment_id != eid or t.kind != "baseline":
            raise HTTPException(422, f"{tid} is not a baseline trial of this experiment")
        if t.t0_s is None:
            raise HTTPException(422, f"{tid} has no confirmed release time")
        try:
            fits.append(fit_constant_acceleration(t.samples, t.t0_s))
        except PhysicsInputError as e:
            raise HTTPException(422, f"{tid}: {e}")
    try:
        est = estimate_baseline(geom, fits)
    except PhysicsInputError as e:
        raise _physics_error(e)
    data = dict(version=len(exp.baselines) + 1, calibration_version=body.calibration_version,
                trial_ids=body.trial_ids, created_at=now(),
                **{k: v for k, v in dataclasses.asdict(est).items() if k != "n_trials"})
    exp.baselines.append(data)
    return data


@app.post("/api/experiments/{eid}/predictions", response_model=S.PredictionOut, status_code=201)
def create_prediction(eid: str, body: S.PredictionIn):
    exp = _exp(eid)
    c = _calib(exp, body.calibration_version)
    if not 1 <= body.baseline_version <= len(exp.baselines):
        raise HTTPException(404, f"baseline version {body.baseline_version} not found")
    b = exp.baselines[body.baseline_version - 1]
    calib, geom = _calib_objects(c)
    try:
        curve = slope.predict(geom, b["mu_eff"], body.distance_m)
    except PhysicsInputError as e:
        raise _physics_error(e)
    pid = new_id("pred")
    data = dict(
        prediction_id=pid, calibration_version=body.calibration_version, baseline_version=body.baseline_version,
        created_at=now(), locked=True,
        params=dict(a_m_s2=curve.a_m_s2, v0_m_s=curve.v0_m_s, mu_eff=b["mu_eff"], angle_deg=c["angle_deg"],
                    distance_m=curve.distance_m, t_end_s=curve.t_end_s),
        assumptions=["released from rest", "constant effective kinetic friction from the locked baseline",
                     "slider keeps sliding (static friction not modelled)", "near side-on camera"],
        curve=list(curve.points),
        # overlay positions are relative to the path start; the frontend adds the release offset s0
        overlay_px=[(t, *calib.to_pixels(s)) for t, s in curve.points],
    )
    exp.predictions[pid] = data
    return data


@app.api_route("/api/experiments/{eid}/predictions/{pid}", methods=["PUT", "PATCH", "DELETE"])
def predictions_are_immutable(eid: str, pid: str):
    raise HTTPException(405, "predictions are locked; create a new calibration or baseline version instead")


# ---------- comparison and next check ----------

@app.post("/api/experiments/{eid}/comparisons", response_model=S.ComparisonOut, status_code=201)
def create_comparison(eid: str, body: S.ComparisonIn):
    exp = _exp(eid)
    p = exp.predictions.get(body.prediction_id) or _raise(404, "prediction not found")
    t = _trial(body.trial_id)
    if t.experiment_id != eid:
        raise HTTPException(422, "trial belongs to another experiment")
    if t.kind == "baseline":
        raise HTTPException(422, "baseline trials calibrate the rig and are not scored against predictions")
    if p["created_at"] >= t.uploaded_at:
        raise HTTPException(409, "the prediction must be saved before the trial video is uploaded")
    c = _calib(exp, p["calibration_version"])
    _, geom = _calib_objects(c)
    b = exp.baselines[p["baseline_version"] - 1]
    curve = slope.predict(geom, b["mu_eff"], p["params"]["distance_m"])
    baseline = _baseline_obj(b)
    cmp = compare(curve, t.samples, t0_s=t.t0_s, calibration_ok=t.calibration_version == p["calibration_version"],
                  baseline=baseline)
    key_ok = any(ch.name == "key_segment" and ch.passed for ch in cmp.checks)
    evidence = evidence_for_next_check(cmp, curve, baseline, key_segment_ok=key_ok)
    cid = new_id("cmp")
    data = dict(
        comparison_id=cid, prediction_id=p["prediction_id"], trial_id=t.trial_id, verdict=cmp.verdict.value,
        checks=[dataclasses.asdict(ch) for ch in cmp.checks],
        fit=_finite(dataclasses.asdict(cmp.fit)) if cmp.fit else None,
        predicted_arrival_s=cmp.predicted_arrival_s, observed_arrival_s=cmp.observed_arrival_s,
        arrival_error_rel=cmp.arrival_error_rel, tolerance_rel=cmp.tolerance_rel,
        residuals=list(cmp.residuals), can_still_say=list(cmp.can_still_say),
        evidence=[dict(candidate=e.candidate.value, finding=e.finding, numbers=e.numbers,
                       cannot_distinguish=e.cannot_distinguish) for e in evidence],
        created_at=now(),
    )
    exp.comparisons[cid] = data
    return data


@app.post("/api/experiments/{eid}/interventions", response_model=S.InterventionOut, status_code=201)
def create_intervention(eid: str, body: S.InterventionIn):
    exp = _exp(eid)
    cmp = exp.comparisons.get(body.comparison_id) or _raise(404, "comparison not found")
    allowed = {e["candidate"] for e in cmp["evidence"]}
    if body.check_type not in allowed:
        raise HTTPException(422, f"{body.check_type} is not supported by the evidence (allowed: {sorted(allowed) or 'none'})")
    if body.model_rationale:
        trial = store.trials[cmp["trial_id"]]
        result = check_model_text(body.model_rationale, [cmp, exp.predictions[cmp["prediction_id"]]["params"],
                                                         {"t0_s": trial.t0_s}])
        if not result.ok:
            raise HTTPException(422, {"error": "model_rationale failed output checks", "problems": result.problems})
    iid = new_id("int")
    data = dict(intervention_id=iid, comparison_id=body.comparison_id, check_type=body.check_type,
                instructions=CATALOG[body.check_type], chosen_by=body.chosen_by,
                model_rationale=body.model_rationale, result_trial_id=None, created_at=now())
    exp.interventions[iid] = data
    store.intervention_owner[iid] = eid
    return data


@app.patch("/api/interventions/{iid}", response_model=S.InterventionOut)
def link_intervention_result(iid: str, body: S.InterventionPatch):
    eid = store.intervention_owner.get(iid) or _raise(404, "intervention not found")
    data = store.experiments[eid].interventions[iid]
    t = _trial(body.result_trial_id)
    if t.experiment_id != eid or t.kind != "intervention":
        raise HTTPException(422, "result trial must be an intervention trial of this experiment")
    data["result_trial_id"] = t.trial_id
    return data


# ---------- report ----------

@app.get("/api/experiments/{eid}/report.md", response_class=PlainTextResponse)
def report_md(eid: str):
    return report.to_markdown(_exp(eid))


@app.get("/api/experiments/{eid}/report.csv", response_class=PlainTextResponse)
def report_csv(eid: str):
    return PlainTextResponse(report.to_csv(_exp(eid)), media_type="text/csv")


@app.get("/api/version")
def version():
    """Which commit is live (T241): Render sets RENDER_GIT_COMMIT; elsewhere it is "local"."""
    return {"commit": os.environ.get("RENDER_GIT_COMMIT", "local")[:12], "public_demo": PUBLIC_DEMO}


@app.get("/api/spend")
def spend():
    """Cumulative Meta API spend and the hard ceiling, for display (T110).

    meta_client stays an optional dependency: without it the backend has
    spent nothing. Every paid meta_client call checks this same ceiling
    before touching the API and refuses past it.
    """
    try:
        from meta_client.cost import get_tracker
    except ImportError:
        return {"spent_usd": 0.0, "limit_usd": 120.0, "at_limit": False}
    tracker = get_tracker()
    spent = tracker.total_usd()
    return {
        "spent_usd": round(spent, 4),
        "limit_usd": tracker.limit_usd,
        "at_limit": spent >= tracker.limit_usd,
    }


def _raise(code: int, msg: str):
    raise HTTPException(code, msg)


# Serve the built frontend from the same origin when it exists (T228: one public URL, no CORS).
# Registered last so every /api and /media route above wins.
_DIST = Path(os.environ.get("FRONTEND_DIST", "frontend/dist"))
if (_DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        target = (_DIST / path).resolve()
        if path and target.is_file() and _DIST.resolve() in target.parents:
            return FileResponse(target)
        if path.startswith(("api/", "media/")) or "." in path.rsplit("/", 1)[-1]:
            raise HTTPException(404, "not found")  # a missing file is a 404, not the app shell
        return FileResponse(_DIST / "index.html")
