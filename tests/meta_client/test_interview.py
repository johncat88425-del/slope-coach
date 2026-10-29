import json
import time

import pytest

from meta_client import interview
from meta_client.cost import CostTracker
from meta_client.exceptions import MediaError, ModelOutputError
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


def _setup(monkeypatch, tmp_path, payload):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"v")
    frames = []
    for i in range(3):
        p = tmp_path / f"f{i}.jpg"
        p.write_bytes(b"fake-jpeg")
        frames.append(p)
    monkeypatch.setattr(interview._sam, "_probe_clip",
                        lambda path: {"fps": 30.0, "n_frames": 150,
                                      "width": 640, "height": 480})
    monkeypatch.setattr(interview, "_extract_frames", lambda path, dur: frames)
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(interview, "get_client", lambda: fake)
    monkeypatch.setattr(interview, "get_tracker", lambda: _tracker(tmp_path))
    return clip, fake


def test_interview_success(tmp_path, monkeypatch):
    payload = {"questions": [
        {"field": "slow_motion", "text": "Was this clip recorded in slow motion?"},
        {"field": "object_size_m", "text": "Do you know the real size of the ball?"},
    ]}
    clip, fake = _setup(monkeypatch, tmp_path, payload)
    tracker = _tracker(tmp_path)
    out = interview.interview_audit(clip, tracker=tracker)
    assert out == payload
    parts = fake.responses.calls[0]["input"][0]["content"]
    assert parts[0]["type"] == "input_text"
    assert sum(p["type"] == "input_image" for p in parts) == 3
    assert tracker.total_usd() > 0


def test_interview_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    q = lambda field, text: {"field": field, "text": text}  # noqa: E731
    cases = [
        ({"questions": []}, "1 to 3"),
        ({"questions": [q("slow_motion", "a?")] * 4}, "1 to 3"),
        ({"questions": [q("orbit", "Which orbit?")]}, "unknown question field"),
        ({"questions": [q("slow_motion", "a?"), q("slow_motion", "b?")]}, "unique"),
        ({"questions": [q("time_window", "Check 30 seconds in?")]}, "failed checks"),
        ({"questions": [q("assumed_model", "This proves free fall.")]}, "failed checks"),
        ({"questions": [q("length_m", "x" * 201)]}, "200 characters"),
    ]
    for payload, match in cases:
        clip, _ = _setup(monkeypatch, tmp_path, payload)
        with pytest.raises(ModelOutputError, match=match):
            interview.interview_audit(clip)


def test_interview_accepts_question_alias(tmp_path, monkeypatch):
    # live 10/29: the API ignores strict schema and Spark writes "question"
    payload = {"questions": [
        {"field": "slow_motion", "question": "Was this slow motion?"},
    ]}
    clip, _ = _setup(monkeypatch, tmp_path, payload)
    out = interview.interview_audit(clip)
    assert out == {"questions": [
        {"field": "slow_motion", "text": "Was this slow motion?"},
    ]}


def test_interview_accepts_bare_array(tmp_path, monkeypatch):
    payload = [
        {"field": "slow_motion", "text": "Was this slow motion?"},
        {"field": "camera_static", "question": "Did the camera stay still?"},
    ]
    clip, _ = _setup(monkeypatch, tmp_path, payload)
    out = interview.interview_audit(clip)
    assert out == {"questions": [
        {"field": "slow_motion", "text": "Was this slow motion?"},
        {"field": "camera_static", "text": "Did the camera stay still?"},
    ]}


def test_interview_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(interview, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(MediaError, match="not found"):
        interview.interview_audit(tmp_path / "missing.mp4")
