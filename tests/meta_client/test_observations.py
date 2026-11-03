import json

import numpy as np

from meta_client import observations
from meta_client.cost import CostTracker
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


POINTS = [(i / 10, 100.0 + i * 5, 50.0 + (i - 4) ** 2) for i in range(10)]


def _setup(monkeypatch, tmp_path, results):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr(
        observations, "_frame_rgb",
        lambda video, t: np.zeros((8, 480, 3), dtype=np.uint8))
    monkeypatch.setattr(observations, "_to_png_bytes", lambda frame: b"fake-png")
    fake = FakeClient(results)
    monkeypatch.setattr(observations, "get_client", lambda: fake)
    monkeypatch.setattr(observations, "get_tracker", lambda: _tracker(tmp_path))
    return clip, fake


def _payload(*notes):
    return {"observations": [
        {"frame": label, "note": note}
        for label, note in zip(observations.KEYFRAME_LABELS, notes)
    ]}


def test_observe_keyframes_success(tmp_path, monkeypatch):
    payload = _payload("ball leaves hand cleanly",
                       "nothing unusual visible",
                       "shadow sits under the ball")
    clip, fake = _setup(monkeypatch, tmp_path,
                        [fake_response(json.dumps(payload), fake_usage())])
    tracker = _tracker(tmp_path)
    out = observations.observe_keyframes(clip, POINTS, "orange ball",
                                         tracker=tracker)
    assert out == {"label": "觀察", "observations": payload["observations"],
                   "source": "muse-spark-1.3"}
    assert "verdict" not in out  # T269: observations never carry a verdict
    parts = fake.responses.calls[0]["input"][0]["content"]
    assert parts[0]["type"] == "input_text"
    assert "orange ball" in parts[0]["text"]
    assert sum(p["type"] == "input_image" for p in parts) == 3
    assert tracker.total_usd() > 0


def test_observe_keyframes_picks_takeoff_apex_landing(tmp_path, monkeypatch):
    payload = _payload("a", "b", "c")
    clip, fake = _setup(monkeypatch, tmp_path,
                        [fake_response(json.dumps(payload), fake_usage())])
    seen = []
    monkeypatch.setattr(observations, "_frame_rgb",
                        lambda video, t: seen.append(t) or np.zeros((8, 480, 3),
                                                                   dtype=np.uint8))
    observations.observe_keyframes(clip, POINTS, "orange ball")
    # takeoff = first, apex = highest (min y at i=4), landing = last
    assert seen == [0.0, 0.4, 0.9]


def test_observe_keyframes_too_few_points(tmp_path, monkeypatch):
    clip, fake = _setup(monkeypatch, tmp_path, [])
    assert observations.observe_keyframes(clip, POINTS[:2], "ball") is None
    assert fake.responses.calls == []


def test_observe_keyframes_rejects_digits(tmp_path, monkeypatch):
    payload = _payload("ball crosses 3 lines", "b", "c")
    clip, _ = _setup(monkeypatch, tmp_path,
                     [fake_response(json.dumps(payload), fake_usage())] * 3)
    assert observations.observe_keyframes(clip, POINTS, "ball") is None


def test_observe_keyframes_rejects_authenticity_words(tmp_path, monkeypatch):
    for note in ("looks fake", "looks real", "made by AI", "AI生成的球"):
        payload = _payload(note, "b", "c")
        clip, _ = _setup(
            monkeypatch, tmp_path,
            [fake_response(json.dumps(payload), fake_usage())] * 3)
        assert observations.observe_keyframes(clip, POINTS, "ball") is None


def test_observe_keyframes_rejects_wrong_frames(tmp_path, monkeypatch):
    payload = {"observations": [
        {"frame": "takeoff", "note": "a"},
        {"frame": "takeoff", "note": "b"},
        {"frame": "landing", "note": "c"},
    ]}
    clip, _ = _setup(monkeypatch, tmp_path,
                     [fake_response(json.dumps(payload), fake_usage())] * 3)
    assert observations.observe_keyframes(clip, POINTS, "ball") is None
