import json
import time

import httpx
import numpy as np
import openai
import pytest

from meta_client import hooks, track_check
from meta_client.cost import CostTracker
from meta_client.exceptions import MediaError
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


POINTS = [(i / 10, 100.0 + i * 5, 50.0) for i in range(10)]


def _setup(monkeypatch, tmp_path, results):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr(
        track_check, "_frame_rgb",
        lambda video, t: np.zeros((8, 480, 3), dtype=np.uint8))
    monkeypatch.setattr(track_check, "_to_png_bytes", lambda frame: b"fake-png")
    fake = FakeClient(results)
    monkeypatch.setattr(track_check, "get_client", lambda: fake)
    monkeypatch.setattr(track_check, "get_tracker", lambda: _tracker(tmp_path))
    return clip, fake


def test_check_track_same_object(tmp_path, monkeypatch):
    payload = {"same_object": True, "note": "same orange ball in every still"}
    clip, fake = _setup(monkeypatch, tmp_path,
                        [fake_response(json.dumps(payload), fake_usage())])
    tracker = _tracker(tmp_path)
    out = track_check.check_track(clip, POINTS, "orange ball", tracker=tracker)
    assert out == {**payload, "source": "muse-spark-1.3"}
    parts = fake.responses.calls[0]["input"][0]["content"]
    assert parts[0]["type"] == "input_text"
    assert "orange ball" in parts[0]["text"]
    assert sum(p["type"] == "input_image" for p in parts) == 4
    assert tracker.total_usd() > 0


def test_check_track_switched_object(tmp_path, monkeypatch):
    payload = {"same_object": False, "note": "ring jumps from ball to wall"}
    clip, _ = _setup(monkeypatch, tmp_path,
                     [fake_response(json.dumps(payload), fake_usage())])
    out = track_check.check_track(clip, POINTS, "orange ball")
    assert out["same_object"] is False


def test_check_track_non_json_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    clip, fake = _setup(monkeypatch, tmp_path,
                        [fake_response("not json", fake_usage())])
    assert track_check.check_track(clip, POINTS, "ball") is None
    assert len(fake.responses.calls) == 3  # initial + 2 retries


def test_check_track_note_with_digit_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    payload = {"same_object": True, "note": "same ball in all 4 stills"}
    clip, fake = _setup(monkeypatch, tmp_path,
                        [fake_response(json.dumps(payload), fake_usage())])
    assert track_check.check_track(clip, POINTS, "ball") is None
    assert len(fake.responses.calls) == 3


def test_check_track_timeout_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    err = openai.APITimeoutError(
        request=httpx.Request("POST", "https://api.meta.ai/v1/responses"))
    clip, _ = _setup(monkeypatch, tmp_path, [err])
    assert track_check.check_track(clip, POINTS, "ball") is None


def test_check_track_too_few_points_skips_api(tmp_path, monkeypatch):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr(
        track_check, "get_client",
        lambda: (_ for _ in ()).throw(AssertionError("must not call API")))
    assert track_check.check_track(clip, POINTS[:3], "ball") is None


def test_track_check_hook_without_key_returns_none(tmp_path, monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    assert hooks.MetaHooks().track_check(tmp_path / "c.mp4", POINTS, "ball") is None


def test_check_track_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(track_check, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(MediaError, match="not found"):
        track_check.check_track(tmp_path / "missing.mp4", POINTS, "ball")


def test_check_track_real_ffmpeg_extraction(tmp_path, monkeypatch):
    # T206 regression: _frame_rgb must survive real binary ffmpeg output
    # (a text-mode pipe crashed live with UnicodeDecodeError). No API call.
    import subprocess

    clip = tmp_path / "src.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         "testsrc=size=640x480:rate=30:duration=1", "-pix_fmt", "yuv420p",
         str(clip)],
        check=True)
    payload = {"same_object": True, "note": "same test pattern throughout"}
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(track_check, "get_client", lambda: fake)
    monkeypatch.setattr(track_check, "get_tracker", lambda: _tracker(tmp_path))
    pts = [(i / 30, 240.0, 120.0) for i in range(30)]
    out = track_check.check_track(clip, pts, "pattern")
    assert out == {**payload, "source": "muse-spark-1.3"}
    parts = fake.responses.calls[0]["input"][0]["content"]
    assert sum(p["type"] == "input_image" for p in parts) == 4
