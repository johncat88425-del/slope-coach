"""T228: public deployment helpers (same-origin frontend, per-IP guard)."""
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_main_after(monkeypatch):
    """Reloading backend.main rewrites its globals in place; put them back so later tests see a normal app."""
    yield
    monkeypatch.undo()
    import backend.main as m
    importlib.reload(m)
    m._hits.clear()


def _app(monkeypatch, tmp_path, **env):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>shell</html>")
    (dist / "assets" / "a.js").write_text("x")
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    monkeypatch.setenv("SLOPE_STORE_PATH", "")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import backend.main as m
    return importlib.reload(m)


def test_frontend_served_and_missing_files_404(monkeypatch, tmp_path):
    m = _app(monkeypatch, tmp_path)
    c = TestClient(m.app)
    assert c.get("/").text == "<html>shell</html>"
    assert c.get("/check").text == "<html>shell</html>"  # client-side route
    assert c.get("/assets/a.js").text == "x"
    assert c.get("/store.pkl").status_code == 404
    assert c.get("/api/spend").status_code == 200


def test_public_guard_limits_paid_posts_per_ip(monkeypatch, tmp_path):
    m = _app(monkeypatch, tmp_path, PUBLIC_DEMO="1", PUBLIC_MAX_PER_HOUR="2", PUBLIC_MAX_UPLOAD_MB="1")
    c = TestClient(m.app)
    big = c.post("/api/audit-drafts", content=b"x" * (2 * 1024 * 1024),
                 headers={"content-type": "application/octet-stream"})
    assert big.status_code == 413
    codes = [c.post("/api/audits", headers={"x-forwarded-for": "9.9.9.9"}).status_code for _ in range(3)]
    assert codes[:2] != [429, 429] and codes[2] == 429
    assert c.post("/api/audits", headers={"x-forwarded-for": "8.8.8.8"}).status_code != 429


def test_public_demo_refuses_long_windows_before_any_model_call(monkeypatch, tmp_path):
    m = _app(monkeypatch, tmp_path, PUBLIC_DEMO="1")
    c = TestClient(m.app)
    with open("data/samples/synthetic_toss_earth_g.mp4", "rb") as f:
        r = c.post("/api/audits", data={"t_start": "0", "t_end": "5.36", "camera_static": "true",
                                        "slow_motion": "false", "assumed_model": "free_flight"},
                   files={"file": ("v.mp4", f, "video/mp4")})
    assert r.status_code == 422 and "at most 3 s" in r.json()["detail"]


def test_public_demo_refuses_4k_uploads(monkeypatch, tmp_path):
    import subprocess
    clip = tmp_path / "big.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=3840x2160:d=0.2",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    m = _app(monkeypatch, tmp_path, PUBLIC_DEMO="1")
    c = TestClient(m.app)
    with clip.open("rb") as f:
        r = c.post("/api/audit-drafts", files={"file": ("big.mp4", f, "video/mp4")})
    assert r.status_code == 413 and "1080p" in r.json()["detail"]
    with open("data/samples/synthetic_toss_earth_g.mp4", "rb") as f:
        assert c.post("/api/audit-drafts", files={"file": ("ok.mp4", f, "video/mp4")}).status_code == 201


def test_public_guard_has_a_site_wide_hourly_ceiling(monkeypatch, tmp_path):
    m = _app(monkeypatch, tmp_path, PUBLIC_DEMO="1", PUBLIC_MAX_PER_HOUR="5", PUBLIC_MAX_GLOBAL_PER_HOUR="3")
    c = TestClient(m.app)
    codes = [c.post("/api/audits", headers={"x-forwarded-for": f"1.1.1.{i}"}).status_code for i in range(4)]
    assert 429 not in codes[:3] and codes[3] == 429
