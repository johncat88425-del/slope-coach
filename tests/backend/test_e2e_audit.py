import shutil
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from tests.scripts.test_gate_run import write_clip

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def test_e2e_audit_normal_and_slow_gravity(tmp_path):
    client = TestClient(app)
    clip_normal = tmp_path / "normal_g.mp4"
    clip_slow = tmp_path / "slow_g4.mp4"

    write_clip(clip_normal, 9.81)
    write_clip(clip_slow, 9.81 / 4.0)

    # 1. Normal Gravity
    with open(clip_normal, "rb") as f:
        res_a = client.post(
            "/api/audits",
            data={
                "t_start": "0.0",
                "t_end": "0.6",
                "camera_static": "true",
                "object_size_m": "0.06",
                "object_name": "box",
                "assumed_model": "free_flight",
            },
            files={"file": ("normal_g.mp4", f, "video/mp4")},
        ).json()
    assert res_a["verdict"] == "consistent"
    assert res_a["numbers"]["g_apparent_m_s2"] == pytest.approx(9.81, rel=0.15)
    assert res_a["nearest_body"] == "Earth"

    # 2. Slow Gravity
    with open(clip_slow, "rb") as f:
        res_b = client.post(
            "/api/audits",
            data={
                "t_start": "0.0",
                "t_end": "0.6",
                "camera_static": "true",
                "object_size_m": "0.06",
                "object_name": "box",
                "assumed_model": "free_flight",
            },
            files={"file": ("slow_g4.mp4", f, "video/mp4")},
        ).json()
    assert res_b["verdict"] == "inconsistent"
    assert res_b["numbers"]["g_apparent_m_s2"] == pytest.approx(2.45, rel=0.20)
    assert res_b["nearest_body"] in ("Moon", "Mars")
