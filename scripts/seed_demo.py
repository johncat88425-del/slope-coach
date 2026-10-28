"""Create a demo experiment with synthetic tracking, so the frontend can be tested without real video.

Usage (backend running): python -m scripts.seed_demo [--base http://localhost:8000] [--case pushed|wrong_height|ok|occluded]
The data is synthetic and every trial is labelled as such in its detections' source ("manual").
"""
from __future__ import annotations

import argparse
import json
import urllib.request
import uuid

from physics.calibration import SlopeGeometry
from physics.experiments import slope

TRUE_MU = 0.15
CAL = dict(ruler_px=[[0, 0], [1000, 0]], ruler_length_m=1.0, path_start_px=[100, 500], path_end_px=[1100, 500],
           slope_length_m=1.0, slope_height_m=0.3, reason="synthetic demo")


def _req(base: str, method: str, path: str, body=None, form=None):
    headers = {}
    data = None
    if form is not None:
        boundary = uuid.uuid4().hex
        parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n' for k, v in form.items()]
        data = ("".join(parts) + f"--{boundary}--\r\n").encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read() or b"null")


def _dets(a, v0=0.0, t0=0.5, s0=0.05, hide_start=False):
    out = []
    for i in range(75):
        t = i / 30
        tt = max(t - t0, 0)
        s = s0 + v0 * tt + 0.5 * a * tt * tt
        if s > 0.95:
            break
        hidden = hide_start and t >= t0 and s < 0.3
        out.append({"t_s": t, "centroid_px": None if hidden else [100 + s * 1000, 500], "area_px": 400, "source": "manual"})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--case", default="pushed", choices=["pushed", "wrong_height", "ok", "occluded"])
    args = ap.parse_args()
    b = args.base

    exp = _req(b, "POST", "/api/experiments", {"title": f"Synthetic demo: {args.case}"})
    eid = exp["experiment_id"]
    _req(b, "POST", f"/api/experiments/{eid}/calibrations", CAL)
    a = slope.acceleration(SlopeGeometry(1.0, 0.3), TRUE_MU)

    def trial(kind, dets):
        t = _req(b, "POST", f"/api/experiments/{eid}/trials", form={"kind": kind, "calibration_version": 1})
        _req(b, "PUT", f"/api/trials/{t['trial_id']}/detections", {"detections": dets})
        _req(b, "PUT", f"/api/trials/{t['trial_id']}/release-time", {"t0_s": 0.5})
        return t["trial_id"]

    bids = [trial("baseline", _dets(a * k)) for k in (0.98, 1.0, 1.02)]
    _req(b, "POST", f"/api/experiments/{eid}/baselines", {"trial_ids": bids, "calibration_version": 1})
    pred = _req(b, "POST", f"/api/experiments/{eid}/predictions",
                {"calibration_version": 1, "baseline_version": 1, "distance_m": 0.8})

    if args.case == "wrong_height":
        test = _dets(slope.acceleration(SlopeGeometry(1.0, 0.4), TRUE_MU))  # real slope was steeper than typed
    else:
        test = _dets(a, v0=0.6 if args.case in ("pushed", "occluded") else 0.0, hide_start=args.case == "occluded")
    tid = trial("test", test)
    cmp = _req(b, "POST", f"/api/experiments/{eid}/comparisons", {"prediction_id": pred["prediction_id"], "trial_id": tid})
    print(json.dumps({"experiment_id": eid, "verdict": cmp["verdict"],
                      "candidates": [e["candidate"] for e in cmp["evidence"]]}, indent=2))


if __name__ == "__main__":
    main()
