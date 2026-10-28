"""End-to-end API flow with synthetic detections (no model calls)."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import store
from physics.calibration import SlopeGeometry
from physics.experiments import slope

client = TestClient(app)
GEOM = SlopeGeometry(1.0, 0.3)
CAL = dict(ruler_px=[[0, 0], [1000, 0]], ruler_length_m=1.0, path_start_px=[100, 500], path_end_px=[1100, 500],
           slope_length_m=1.0, slope_height_m=0.3)


def dets(a, v0=0.0, t0=0.5, s0=0.05):
    out = []
    for i in range(60):
        t = i / 30
        tt = max(t - t0, 0)
        s = s0 + v0 * tt + 0.5 * a * tt * tt
        if s > 0.95:
            break
        out.append({"t_s": t, "centroid_px": [100 + s * 1000, 500], "area_px": 400})
    return out


def trial(eid, kind, detections, t0=0.5):
    tid = client.post(f"/api/experiments/{eid}/trials", data={"kind": kind, "calibration_version": 1}).json()["trial_id"]
    client.put(f"/api/trials/{tid}/detections", json={"detections": detections})
    client.put(f"/api/trials/{tid}/release-time", json={"t0_s": t0})
    return tid


@pytest.fixture(autouse=True)
def clean():
    store.reset()


def setup_experiment():
    eid = client.post("/api/experiments", json={}).json()["experiment_id"]
    assert client.post(f"/api/experiments/{eid}/calibrations", json=CAL).status_code == 201
    a = slope.acceleration(GEOM, 0.15)
    bids = [trial(eid, "baseline", dets(a * k)) for k in (0.99, 1.0, 1.01)]
    r = client.post(f"/api/experiments/{eid}/baselines", json={"trial_ids": bids, "calibration_version": 1})
    assert r.status_code == 201, r.text
    p = client.post(f"/api/experiments/{eid}/predictions",
                    json={"calibration_version": 1, "baseline_version": 1, "distance_m": 0.8})
    assert p.status_code == 201, p.text
    return eid, p.json()["prediction_id"], a


def test_full_loop_release_check():
    eid, pid, a = setup_experiment()
    tid = trial(eid, "test", dets(a, v0=0.6))
    c = client.post(f"/api/experiments/{eid}/comparisons", json={"prediction_id": pid, "trial_id": tid}).json()
    assert c["verdict"] == "discrepancy"
    assert "release_check" in {e["candidate"] for e in c["evidence"]}
    i = client.post(f"/api/experiments/{eid}/interventions",
                    json={"comparison_id": c["comparison_id"], "check_type": "release_check"})
    assert i.status_code == 201
    rid = trial(eid, "intervention", dets(a))
    assert client.patch(f"/api/interventions/{i.json()['intervention_id']}", json={"result_trial_id": rid}).status_code == 200
    md = client.get(f"/api/experiments/{eid}/report.md").text
    assert "release_check" in md and "locked" in md
    assert client.get(f"/api/experiments/{eid}/report.csv").text.startswith("trial_id,")


def test_unsupported_check_rejected():
    eid, pid, a = setup_experiment()
    tid = trial(eid, "test", dets(a))
    c = client.post(f"/api/experiments/{eid}/comparisons", json={"prediction_id": pid, "trial_id": tid}).json()
    assert c["verdict"] == "consistent"
    r = client.post(f"/api/experiments/{eid}/interventions",
                    json={"comparison_id": c["comparison_id"], "check_type": "release_check"})
    assert r.status_code == 422


def test_prediction_must_precede_trial():
    eid = client.post("/api/experiments", json={}).json()["experiment_id"]
    client.post(f"/api/experiments/{eid}/calibrations", json=CAL)
    a = slope.acceleration(GEOM, 0.15)
    early = trial(eid, "test", dets(a))
    bids = [trial(eid, "baseline", dets(a * k)) for k in (0.99, 1.0, 1.01)]
    client.post(f"/api/experiments/{eid}/baselines", json={"trial_ids": bids, "calibration_version": 1})
    pid = client.post(f"/api/experiments/{eid}/predictions",
                      json={"calibration_version": 1, "baseline_version": 1, "distance_m": 0.8}).json()["prediction_id"]
    r = client.post(f"/api/experiments/{eid}/comparisons", json={"prediction_id": pid, "trial_id": early})
    assert r.status_code == 409


def test_predictions_are_immutable_and_bad_geometry_rejected():
    eid, pid, _ = setup_experiment()
    assert client.patch(f"/api/experiments/{eid}/predictions/{pid}", json={}).status_code == 405
    bad = dict(CAL, slope_height_m=1.2)
    assert client.post(f"/api/experiments/{eid}/calibrations", json=bad).status_code == 422


def test_tracking_not_connected_returns_501():
    eid, _, _ = setup_experiment()
    r = client.post(f"/api/experiments/{eid}/trials", data={"kind": "test", "calibration_version": 1},
                    files={"file": ("clip.mp4", b"fake", "video/mp4")})
    assert client.post(f"/api/trials/{r.json()['trial_id']}/track").status_code == 501


def test_model_rationale_is_checked():
    eid, pid, a = setup_experiment()
    tid = trial(eid, "test", dets(a, v0=0.6))
    c = client.post(f"/api/experiments/{eid}/comparisons", json={"prediction_id": pid, "trial_id": tid}).json()
    v0 = c["fit"]["v0_m_s"]
    bad = client.post(f"/api/experiments/{eid}/interventions",
                      json={"comparison_id": c["comparison_id"], "check_type": "release_check",
                            "model_rationale": "This proves the block was pushed at 3.9 m/s."})
    assert bad.status_code == 422
    good = client.post(f"/api/experiments/{eid}/interventions",
                       json={"comparison_id": c["comparison_id"], "check_type": "release_check",
                             "model_rationale": f"The fit is consistent with a release speed of about {v0:.2f} m/s."})
    assert good.status_code == 201, good.text


def test_store_snapshot_roundtrip(tmp_path, monkeypatch):
    import backend.store as st
    eid, pid, _ = setup_experiment()
    monkeypatch.setattr(st, "STORE_PATH", str(tmp_path / "store.pkl"))
    store.save()
    store.reset()
    assert eid not in store.experiments
    store.load()
    assert pid in store.experiments[eid].predictions


def test_uploads_are_served_under_media():
    eid = client.post("/api/experiments", json={}).json()["experiment_id"]
    photo = client.post(f"/api/experiments/{eid}/scene-photo", files={"file": ("scene.jpg", b"fake-jpeg", "image/jpeg")}).json()
    assert photo["photo_url"] == f"/media/{eid}/{photo['photo_id']}.jpg"
    assert client.get(photo["photo_url"]).content == b"fake-jpeg"
    assert client.get(f"/media/{eid}/../../store.pkl").status_code == 404
