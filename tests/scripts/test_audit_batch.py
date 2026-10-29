import shutil

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from scripts.audit_batch import audit_row, to_markdown
from tests.scripts.test_gate_run import row, write_orange_clip

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def test_batch_reports_website_verdicts_and_unlabelled_rows(tmp_path):
    write_orange_clip(tmp_path / "ball.mp4", 9.81)
    c = TestClient(app)
    good = audit_row(c, row("ball.mp4") | {"object": "orange ball"}, tmp_path)
    blank = audit_row(c, {"clip": "x.mp4", "source": "", "assumed_model": "free_flight"}, tmp_path)
    assert good["verdict"] == "consistent" and good["track_source"] == "color" and good["nearest_body"] == "Earth"
    assert blank["verdict"] == "unlabelled"
    md = to_markdown([good, blank])
    assert "ball.mp4" in md and "x.mp4" in md and "unlabelled" in md
    missing = audit_row(c, row("not_here.mp4"), tmp_path)
    assert missing["verdict"] == "missing"


def test_generated_gate_clips_are_in_the_repo():
    from pathlib import Path

    names = {p.name for p in Path("data/gate/clips").glob("*.mp4")}
    assert {f"meta_clip{i}.mp4" for i in range(1, 7)} | {"manus_clip1.mp4"} <= names
    assert not any(n.startswith("own_") for n in names)  # john's own clips never go in git


def test_json_dir_saves_demo_records_without_media(tmp_path):
    import json

    write_orange_clip(tmp_path / "own_1_ball.mp4", 9.81)
    c = TestClient(app)
    r = row("own_1_ball.mp4") | {"object": "orange ball", "source": "own"}
    audit_row(c, r, tmp_path, tmp_path / "demo")
    rec = json.loads((tmp_path / "demo" / "real_own_1.json").read_text())
    assert rec["real_clip"] is True and rec["video_url"] == "" and rec["overlay_url"] is None
    assert rec["verdict"] == "consistent" and rec["points"] and rec["clip"] == "own_1_ball.mp4"
