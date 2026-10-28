import csv
import shutil
import subprocess
import sys

import pytest

from tests.scripts.test_gate_run import write_clip

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def test_prepare_writes_sheet_and_blank_labels(tmp_path):
    clips = tmp_path / "clips"
    clips.mkdir()
    write_clip(clips / "toss.mp4", 9.81)
    man = tmp_path / "manifest.csv"
    for _ in range(2):  # running twice must not duplicate rows
        subprocess.run([sys.executable, "-m", "scripts.gate_prepare", str(clips), "--sheets", str(tmp_path / "s"),
                        "--manifest", str(man)], check=True, capture_output=True)
    assert (tmp_path / "s" / "toss_sheet.png").stat().st_size > 0
    rows = list(csv.DictReader(man.open()))
    assert len(rows) == 1 and rows[0]["clip"] == "toss.mp4"
    assert rows[0]["t_start"] == rows[0]["camera_static"] == rows[0]["object_size_m"] == ""
