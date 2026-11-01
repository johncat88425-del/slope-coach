"""T228: public deployment helpers (same-origin frontend, per-IP guard)."""
import importlib

from fastapi.testclient import TestClient


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
