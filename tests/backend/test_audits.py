import shutil

import pytest
from fastapi.testclient import TestClient

from backend.main import app
import subprocess

import numpy as np

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
    assert r["nearest_body"] == "Earth" and len(r["ghost_points"]) == len(r["points"])
    slow = post(tmp_path / "slow.mp4").json()
    assert slow["verdict"] == "inconsistent" and slow["reasons"]
    assert slow["nearest_body"] in ("Moon", "Mars") and slow["numbers"]["g_vs_earth"] < 0.5
    assert abs(slow["ghost_points"][-1][2] - slow["points"][-1][2]) > 20
    assert slow["numbers"]["g_verdict_robust"] == 1.0 and slow["numbers"]["g_apparent_high"] < 9.81 * 0.85


def test_audit_refuses_moving_camera_and_bad_input(tmp_path):
    write_clip(tmp_path / "real.mp4", 9.81)
    moving = post(tmp_path / "real.mp4", camera_static="false").json()
    assert moving["verdict"] == "insufficient_data" and "camera" in moving["reasons"][0]
    assert post(tmp_path / "real.mp4", t_start="1", t_end="0.5").status_code == 422
    assert post(tmp_path / "real.mp4", assumed_model="spring").status_code == 422
    assert client.get("/api/audits/aud_nope").status_code == 404


def write_frames(path, positions, sizes, fps=60, w=640, h=480):
    frames = []
    for (x, y), b in zip(positions, sizes):
        f = np.full((h, w), 255, np.uint8)
        f[int(y):int(y) + b, int(x):int(x) + b] = 0
        frames.append(f)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
                    "-r", str(fps), "-i", "-", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-qp", "0", str(path)],
                   input=b"".join(f.tobytes() for f in frames), check=True)


def test_audit_refuses_object_moving_towards_camera(tmp_path):
    n = 36
    write_frames(tmp_path / "toward.mp4", [(100 + 5 * i, 100 + 0.2 * i * i) for i in range(n)],
                 [int(16 + 0.8 * i) for i in range(n)])
    r = post(tmp_path / "toward.mp4").json()
    assert r["verdict"] == "insufficient_data" and "towards or away" in r["reasons"][0]


def test_audit_bounce_mode(tmp_path):
    from tests.physics.test_persistence_bounce import bouncing
    fps = 60
    def pos(gain_at):
        pts = bouncing(fps=fps, gain_at=gain_at, g=1500.0, h0=250.0)
        return [(x, y) for _, x, y in pts][: fps * 2]
    write_frames(tmp_path / "ok.mp4", pos(None), [16] * (fps * 2))
    write_frames(tmp_path / "gain.mp4", pos(1), [16] * (fps * 2))
    ok = post(tmp_path / "ok.mp4", assumed_model="bounce", t_end="1.9").json()
    gain = post(tmp_path / "gain.mp4", assumed_model="bounce", t_end="1.9").json()
    assert ok["verdict"] == "consistent", ok["reasons"]
    assert gain["verdict"] == "inconsistent", gain


def test_audit_pendulum_period_and_length(tmp_path):
    import math
    fps, L = 60, 0.25
    w = math.sqrt(9.81 / L)
    n = int(3.5 * fps)
    pos = [(300 + 120 * math.sin(w * i / fps), 200 + 15 * (1 - math.cos(w * i / fps))) for i in range(n)]
    write_frames(tmp_path / "pend.mp4", pos, [20] * n, fps=fps)
    r = post(tmp_path / "pend.mp4", assumed_model="pendulum", t_end="3.4", length_m=str(L)).json()
    assert r["verdict"] == "consistent", r
    assert r["numbers"]["period_s"] == pytest.approx(2 * math.pi / w, rel=0.03)
    assert r["numbers"]["implied_length_m"] == pytest.approx(L, rel=0.06)
    wrong = post(tmp_path / "pend.mp4", assumed_model="pendulum", t_end="3.4", length_m="1.0").json()
    assert wrong["verdict"] == "inconsistent"


def test_interview_draft_then_audit_and_slow_motion_refusal(tmp_path):
    write_clip(tmp_path / "real.mp4", 9.81)
    with open(tmp_path / "real.mp4", "rb") as f:
        d = client.post("/api/audit-drafts", files={"file": ("clip.mp4", f, "video/mp4")}).json()
    assert d["interview"]["source"] == "mock" and len(d["interview"]["questions"]) == 3
    form = {"draft_id": d["draft_id"], "t_start": "0", "t_end": "0.6", "camera_static": "true", "object_size_m": "0.06"}
    r = client.post("/api/audits", data=form).json()
    assert r["verdict"] == "consistent" and r["video_url"] == d["video_url"]
    assert client.post("/api/audits", data=form).status_code == 404  # a draft is used once
    with open(tmp_path / "real.mp4", "rb") as f:
        d2 = client.post("/api/audit-drafts", files={"file": ("clip.mp4", f, "video/mp4")}).json()
    slow = client.post("/api/audits", data=form | {"draft_id": d2["draft_id"], "slow_motion": "true"}).json()
    assert slow["verdict"] == "insufficient_data" and "slow motion" in slow["reasons"][0]
    assert client.post("/api/audits", data={k: v for k, v in form.items() if k != "draft_id"}).status_code == 422


def test_model_questions_with_numbers_fall_back_to_fixed_ones():
    from backend import schemas as S
    from backend.audits import checked_interview
    bad = S.AuditInterview(source="model", questions=[
        S.AuditQuestion(field="object_size_m", text="Is the ball 6.7 cm wide?")])
    assert checked_interview(bad).source == "mock"
    fake = S.AuditInterview(source="model", questions=[
        S.AuditQuestion(field="camera_static", text="Is this a fake video?")])
    assert checked_interview(fake).source == "mock"
    ok = S.AuditInterview(source="model", questions=[
        S.AuditQuestion(field="slow_motion", text="Was slow motion on when you recorded this?")])
    assert checked_interview(ok).source == "model"
