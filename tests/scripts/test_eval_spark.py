import csv
import json

import pytest

from scripts.eval_spark import main, run_eval

HEADER = ["clip", "source", "assumed_model", "t_start", "t_end",
          "camera_static", "object", "object_size_m"]


def _manifest(tmp_path, rows):
    manifest = tmp_path / "manifest.csv"
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    return manifest


def test_mock_eval_scores_and_skips_faces(tmp_path):
    clips = tmp_path / "clips"
    clips.mkdir()
    (clips / "a.mp4").write_bytes(b"v")
    (clips / "b.mp4").write_bytes(b"v")
    manifest = _manifest(tmp_path, [
        ["a.mp4", "john", "free_flight", "1.0", "2.0", "true", "tennis ball", "0.07"],
        ["b.mp4", "john", "slide", "0.5", "3.0", "true", "block", ""],
    ])
    report = run_eval(manifest, clips, faces={"b.mp4"}, model="muse-spark-1.3", mock=True)
    assert report["summary"]["n_sent"] == 1
    sent = [c for c in report["clips"] if c.get("sent")][0]
    assert sent["object_match"] is True
    assert sent["model_match"] is True
    assert sent["start_err_s"] == pytest.approx(0.1)
    assert sent["end_err_s"] == pytest.approx(-0.1)
    skipped = [c for c in report["clips"] if not c.get("sent")][0]
    assert skipped["reason"] == "has face"
    assert report["summary"]["mean_abs_time_err_s"] == pytest.approx(0.1)


def test_missing_file_clip_skipped(tmp_path):
    clips = tmp_path / "clips"
    clips.mkdir()
    manifest = _manifest(tmp_path, [
        ["gone.mp4", "john", "free_flight", "1.0", "2.0", "true", "ball", ""],
    ])
    report = run_eval(manifest, clips, faces=set(), model="muse-spark-1.3", mock=True)
    assert report["clips"][0]["reason"] == "file missing"


def test_contributor_needs_face_confirmation(tmp_path):
    assert main(["--model", "muse-spark-1.3-contributor"]) == 2
    out = tmp_path / "rep.json"
    clips = tmp_path / "clips"
    clips.mkdir()
    manifest = _manifest(tmp_path, [])
    assert main(["--mock", "--manifest", str(manifest), "--clips", str(clips),
                 "--model", "muse-spark-1.3-contributor", "--i-confirm-no-faces",
                 "--out", str(out)]) == 0
    assert json.loads(out.read_text())["summary"]["n_clips"] == 0


def test_missing_manifest_and_faces(tmp_path):
    assert main(["--mock", "--manifest", str(tmp_path / "no.csv")]) == 2
    manifest = _manifest(tmp_path, [])
    assert main(["--mock", "--manifest", str(manifest),
                 "--faces", str(tmp_path / "no.txt")]) == 2
