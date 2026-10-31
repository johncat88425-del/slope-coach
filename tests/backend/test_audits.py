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
    data = {k: v for k, v in data.items() if v is not None}  # None leaves a default field out
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


def test_sam_track_used_when_connected(tmp_path):
    from backend import schemas as S
    from backend.model_hooks import MockHooks, get_hooks, set_hooks

    class FakeSam(MockHooks):
        def track_object(self, video_path, text_prompt, t_start, t_end):
            # same motion as write_clip(9.81), normalised to the 640x480 frame
            out = []
            for i in range(36):
                t = i / 60
                x = (40 + t / 0.003 + 10) / 640
                y = (300 - 2.0 / 0.003 * t + 0.5 * 9.81 / 0.003 * t * t + 10) / 480
                out.append(S.DetectionIn(t_s=t, centroid_px=(x, y) if i != 5 else None, area_px=400 / (640 * 480)))
            return out

    write_clip(tmp_path / "real.mp4", 9.81)
    old = get_hooks()
    set_hooks(FakeSam())
    try:
        r = post(tmp_path / "real.mp4", object_name="black square").json()
    finally:
        set_hooks(old)
    assert r["track_source"] == "sam" and r["verdict"] == "consistent", r
    assert r["numbers"]["g_apparent_m_s2"] == pytest.approx(9.81, rel=0.05)
    assert len(r["points"]) == 35  # the missed frame stays a gap


def test_sam_at_15_fps_is_not_refused_for_tracking_on_a_60_fps_clip(tmp_path):
    """SAM samples at 15 fps; the tracked fraction counts SAM's samples, not the clip's 60 fps frames."""
    from backend import schemas as S
    from backend.model_hooks import MockHooks, get_hooks, set_hooks

    class FakeSam15(MockHooks):
        def track_object(self, video_path, text_prompt, t_start, t_end):
            out = []
            for i in range(9):  # 0 .. 0.53 s at 15 fps, every sample found
                t = i / 15
                x = (40 + t / 0.003 + 10) / 640
                y = (300 - 2.0 / 0.003 * t + 0.5 * 9.81 / 0.003 * t * t + 10) / 480
                out.append(S.DetectionIn(t_s=t, centroid_px=(x, y), area_px=400 / (640 * 480)))
            return out

    write_clip(tmp_path / "real.mp4", 9.81)
    old = get_hooks()
    set_hooks(FakeSam15())
    try:
        r = post(tmp_path / "real.mp4", object_name="black square").json()
    finally:
        set_hooks(old)
    assert r["track_source"] == "sam" and r["numbers"]["tracked_fraction"] == pytest.approx(1.0), r
    assert r["verdict"] == "consistent", r


def test_colour_named_object_uses_colour_tracker_when_sam_is_absent(tmp_path):
    from tests.scripts.test_gate_run import write_orange_clip

    write_orange_clip(tmp_path / "ball.mp4", 9.81)
    r = post(tmp_path / "ball.mp4", object_name="orange ball").json()
    assert r["track_source"] == "color" and r["verdict"] == "consistent", r
    plain = post(tmp_path / "ball.mp4", object_name="ball").json()
    assert plain["track_source"] == "frame_diff"


def test_template_explanation_quotes_program_numbers_only(tmp_path):
    from backend.output_check import find_banned_phrases

    write_clip(tmp_path / "real.mp4", 9.81)
    write_clip(tmp_path / "slow.mp4", 9.81 / 4)
    real = post(tmp_path / "real.mp4").json()
    slow = post(tmp_path / "slow.mp4").json()
    assert real["explanation"]["source"] == "template"
    assert "consistent with that model" in real["explanation"]["text"]
    assert f"{real['numbers']['g_apparent_m_s2']:.1f}" in real["explanation"]["text"]
    s = slow["explanation"]["text"]
    assert f"{slow['numbers']['g_apparent_m_s2']:.2f}" in s and slow["nearest_body"] in s
    assert not find_banned_phrases(s) and not find_banned_phrases(real["explanation"]["text"])
    refused = post(tmp_path / "real.mp4", camera_static="false").json()
    assert refused["explanation"]["text"].startswith("This clip cannot be judged")


def test_window_suggestions_for_a_draft(tmp_path):
    from tests.scripts.test_gate_run import write_orange_clip

    write_orange_clip(tmp_path / "ball.mp4", 9.81)
    with open(tmp_path / "ball.mp4", "rb") as f:
        d = client.post("/api/audit-drafts", files={"file": ("ball.mp4", f, "video/mp4")}).json()
    r = client.post(f"/api/audit-drafts/{d['draft_id']}/windows", data={"object_name": "orange ball"}).json()
    assert r["source"] == "physics" and r["track_source"] == "color"
    assert r["windows"] and r["windows"][0]["t_start"] < 0.1 and r["windows"][0]["t_end"] > 0.5
    assert client.post("/api/audit-drafts/drf_nope/windows").status_code == 404


def test_model_explanation_and_headline_used_only_when_they_pass_checks(tmp_path):
    from backend.model_hooks import MockHooks, get_hooks, set_hooks

    class FakeSpark(MockHooks):
        def __init__(self, explanation, headline):
            self.explanation, self.headline = explanation, headline

        def explain_audit(self, audit):
            assert "points" not in audit and "numbers" in audit  # the model never gets the raw track
            return self.explanation.format(g=audit["numbers"]["g_apparent_m_s2"])

        def headline_audit(self, audit):
            if self.headline is None:
                raise RuntimeError("spend cap reached")
            return self.headline

    write_clip(tmp_path / "slow.mp4", 9.81 / 4)
    old = get_hooks()
    try:
        set_hooks(FakeSpark("The ball falls at {g:.2f} m/s², consistent with nothing on Earth.", "Falls like on Mars"))
        good = post(tmp_path / "slow.mp4").json()
        set_hooks(FakeSpark("The ball falls at 3.33 m/s², so this is a fake video.", None))
        bad = post(tmp_path / "slow.mp4").json()
    finally:
        set_hooks(old)
    assert good["explanation"]["source"] == "model"
    assert good["headline"] == {"source": "model", "text": "Falls like on Mars"}
    assert bad["explanation"]["source"] == "template"  # unfound number and banned wording -> fixed template
    assert bad["headline"] is None  # a failing model call never breaks the audit
    assert good["verdict"] == bad["verdict"]


def test_batch_switch_skips_paid_model_text(tmp_path, monkeypatch):
    from backend.model_hooks import MockHooks, get_hooks, set_hooks

    calls = []

    class CountingSpark(MockHooks):
        def explain_audit(self, audit):
            calls.append("explain")
            return "unused"

        def headline_audit(self, audit):
            calls.append("headline")
            return "unused"

    write_clip(tmp_path / "real.mp4", 9.81)
    monkeypatch.setenv("SLOPE_MODEL_TEXT", "0")  # what scripts/audit_batch.py sets unless --explain
    old = get_hooks()
    try:
        set_hooks(CountingSpark())
        out = post(tmp_path / "real.mp4").json()
    finally:
        set_hooks(old)
    assert calls == [] and out["explanation"]["source"] == "template" and out["headline"] is None


def test_object_suggestion_and_voice_answers_are_checked_and_never_confirmed(tmp_path):
    from backend.model_hooks import MockHooks, get_hooks, set_hooks

    write_clip(tmp_path / "real.mp4", 9.81)
    c = TestClient(app)

    def draft():
        with open(tmp_path / "real.mp4", "rb") as f:
            return c.post("/api/audit-drafts", files={"file": ("real.mp4", f, "video/mp4")}).json()

    plain = draft()
    assert plain["suggestion"] is None  # no model connected
    v = c.post(f"/api/audit-drafts/{plain['draft_id']}/voice", files={"audio": ("a.webm", b"x", "audio/webm")}).json()
    assert v == {"source": {"transcript": "mock", "fields": "mock"}, "transcript": "", "fields": {}}

    class FakeMuse(MockHooks):
        def __init__(self, name):
            self.name = name

        def suggest_object(self, video_path):
            return {"object_name": self.name, "camera_looks_static": True, "reason": "one ball moves", "source": "muse-spark-1.3"}

        def answer_voice(self, audio_path):
            return {"transcript": "no slow motion, the ball is eleven centimetres", "source": {"transcript": "muse-voice-transcribe-1.0", "fields": "muse-spark-1.3"},
                    "fields": {"slow_motion": {"value": False, "confirmed": True}, "object_size_m": {"value": 0.11},
                               "camera_static": {"value": "yes"}, "length_m": {"value": -1}, "bogus": {"value": 1}}}

    old = get_hooks()
    try:
        set_hooks(FakeMuse("orange basketball"))
        good = draft()
        v = c.post(f"/api/audit-drafts/{good['draft_id']}/voice", files={"audio": ("a.webm", b"x", "audio/webm")}).json()
        set_hooks(FakeMuse("ball 11 cm wide"))
        bad = draft()
    finally:
        set_hooks(old)
    assert good["suggestion"]["object_name"] == "orange basketball" and good["suggestion"]["source"] == "muse-spark-1.3"
    assert bad["suggestion"] is None  # a size in the name would look like a measurement
    assert v["fields"] == {"slow_motion": {"value": False, "confirmed": False},
                           "object_size_m": {"value": 0.11, "confirmed": False}}  # wrong types and unknown fields dropped
    assert c.post("/api/audit-drafts/nope/voice", files={"audio": ("a.webm", b"x", "audio/webm")}).status_code == 404


def test_model_text_may_quote_numbers_from_the_programs_own_reasons():
    from backend.audits import _number_sources
    from backend.output_check import check_model_text

    view = {"verdict": "inconsistent", "numbers": {"g_apparent_m_s2": 1.705},
            "reasons": ["apparent g 1.71 m/s^2 is outside 8.34-11.28"]}
    assert check_model_text("1.71 m/s² is outside the 8.34 to 11.28 range.", _number_sources(view)).ok
    assert not check_model_text("1.71 m/s² is far below 9.5.", _number_sources(view)).ok  # invented number


def write_car(path, v_m_s, a_m_s2, seconds=1.2, fps=30, car_px=120, car_m=4.5, w=640, h=480):
    """Dark 120 x 40 px box (a 4.5 m car side-on) driving left to right, whole car always in frame."""
    k = car_px / car_m
    frames = []
    for i in range(int(seconds * fps)):
        t = i / fps
        x = int(20 + k * (v_m_s * t + 0.5 * a_m_s2 * t * t))
        f = np.full((h, w), 255, np.uint8)
        f[300:340, x:x + car_px] = 0
        frames.append(f)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
                    "-r", str(fps), "-i", "-", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-qp", "0", str(path)],
                   input=b"".join(f.tobytes() for f in frames), check=True)


def test_audit_vehicle_speed_and_grip(tmp_path):
    write_car(tmp_path / "car.mp4", 13.9, 0.0)
    write_car(tmp_path / "rocket.mp4", 8.0, 3 * 9.81, seconds=0.8)
    car = post(tmp_path / "car.mp4", assumed_model="vehicle", t_end="1.15", object_size_m="4.5").json()
    assert car["verdict"] == "consistent", car
    assert car["numbers"]["speed_km_h"] == pytest.approx(50, rel=0.05)
    assert "km/h" in car["explanation"]["text"]
    rocket = post(tmp_path / "rocket.mp4", assumed_model="vehicle", t_end="0.75", object_size_m="4.5").json()
    assert rocket["verdict"] == "inconsistent" and " g" in rocket["reasons"][0]
    assert rocket["numbers"]["accel_g"] == pytest.approx(3, rel=0.1)
    slow = post(tmp_path / "car.mp4", assumed_model="vehicle", t_end="1.15", slow_motion="true").json()
    assert slow["verdict"] == "insufficient_data"
    sedan = post(tmp_path / "car.mp4", assumed_model="vehicle", t_end="1.15", vehicle_class="sedan", object_size_m=None).json()
    assert sedan["verdict"] == "consistent" and sedan["vehicle_class"] == "sedan"
    n = sedan["numbers"]
    assert (n["car_length_low_m"], n["car_length_high_m"]) == (4.6, 5.0) and "speed_km_h" not in n
    assert n["speed_km_h_low"] == pytest.approx(50 * 4.6 / 4.5, rel=0.05)
    assert post(tmp_path / "car.mp4", assumed_model="vehicle", t_end="1.15", vehicle_class="bus").status_code == 422


def test_audit_refuses_long_windows_and_oversized_uploads(tmp_path, monkeypatch):
    import io
    from backend import store as store_mod
    write_clip(tmp_path / "real.mp4", 9.81)
    assert post(tmp_path / "real.mp4", t_end="45").status_code == 422
    monkeypatch.setattr(store_mod, "MAX_UPLOAD_BYTES", 1000)
    monkeypatch.setattr(store_mod.copy_limited, "__defaults__", (1000,))
    r = client.post("/api/audits", data={"t_start": "0", "t_end": "0.6", "camera_static": "true"},
                    files={"file": ("big.mp4", io.BytesIO(b"x" * 5000), "video/mp4")})
    assert r.status_code == 413
