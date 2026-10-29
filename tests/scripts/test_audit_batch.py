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
