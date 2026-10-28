import shutil

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from tests.scripts.test_gate_run import write_clip

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
client = TestClient(app)


def post(path, **form):
    data = {"t_start": "0", "t_end": "0.6", "camera_static": "true", "object_size_m": "0.06", **form}
    with open(path, "rb") as f:
        return client.post("/api/audits", data=data, files={"file": ("clip.mp4", f, "video/mp4")})


def test_audit_consistent_and_inconsistent(tmp_path):
    write_clip(tmp_path / "real.mp4", 9.81)
    write_clip(tmp_path / "slow.mp4", 9.81 / 4)
    real = post(tmp_path / "real.mp4")
    assert real.status_code == 201, real.text
    r = real.json()
    assert r["verdict"] == "consistent"
    assert r["numbers"]["g_apparent_m_s2"] == pytest.approx(9.81, rel=0.15)
    assert client.get(r["overlay_url"]).status_code == 200
    assert client.get(f"/api/audits/{r['audit_id']}").json()["verdict"] == "consistent"
    slow = post(tmp_path / "slow.mp4").json()
    assert slow["verdict"] == "inconsistent" and slow["reasons"]


def test_audit_refuses_moving_camera_and_bad_input(tmp_path):
    write_clip(tmp_path / "real.mp4", 9.81)
    moving = post(tmp_path / "real.mp4", camera_static="false").json()
    assert moving["verdict"] == "insufficient_data" and "camera" in moving["reasons"][0]
    assert post(tmp_path / "real.mp4", t_start="1", t_end="0.5").status_code == 422
    assert post(tmp_path / "real.mp4", assumed_model="bounce").status_code == 422
    assert client.get("/api/audits/aud_nope").status_code == 404
