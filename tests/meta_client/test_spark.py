import json
import time

import pytest

from meta_client import spark
from meta_client.cost import CostTracker
from meta_client.exceptions import MediaError, ModelOutputError, SpendLimitExceeded
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage

SCENE_OK = {
    "has_ruler": True,
    "has_slope": True,
    "has_slider": True,
    "is_side_view": True,
    "needs_retake": False,
    "retake_reasons": [],
}


def _tracker(tmp_path, limit=120.0):
    return CostTracker(tmp_path / "cost.csv", limit_usd=limit)


def test_describe_scene_success_and_cost(tmp_path, monkeypatch):
    photo = tmp_path / "setup.jpg"
    photo.write_bytes(b"\xff\xd8fake-jpeg")
    usage = fake_usage(input_tokens=1000, output_tokens=200, cached_tokens=100)
    fake = FakeClient([fake_response(json.dumps(SCENE_OK), usage)])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    tracker = _tracker(tmp_path)
    monkeypatch.setattr(spark, "get_tracker", lambda: tracker)

    out = spark.describe_scene(photo, tracker=tracker)
    assert out == {**SCENE_OK, "source": "muse-spark-1.3"}

    call = fake.responses.calls[0]
    assert call["model"] == "muse-spark-1.3"
    assert call["text"]["type"] == "json_schema"
    parts = call["input"][0]["content"]
    assert parts[0]["type"] == "input_text"
    assert parts[1]["type"] == "input_image"
    assert parts[1]["image_url"].startswith("data:image/jpeg;base64,")
    assert tracker.total_usd() == pytest.approx(
        (900 * 1.25 + 100 * 0.15 + 200 * 4.25) / 1e6
    )


def test_describe_scene_accepts_bytes_and_contributor_model(tmp_path, monkeypatch):
    fake = FakeClient([fake_response(json.dumps(SCENE_OK), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    tracker = _tracker(tmp_path)
    out = spark.describe_scene(
        b"raw-bytes", model="muse-spark-1.3-contributor", tracker=tracker
    )
    assert out["has_ruler"] is True
    assert fake.responses.calls[0]["model"] == "muse-spark-1.3-contributor"
    assert tracker.total_usd() == pytest.approx((100 * 0.10 + 50 * 0.20) / 1e6)


def test_describe_scene_retries_bad_json_then_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    photo = tmp_path / "s.png"
    photo.write_bytes(b"fake-png")
    fake = FakeClient([fake_response("not json", fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(ModelOutputError):
        spark.describe_scene(photo)
    assert len(fake.responses.calls) == 3  # initial + 2 retries


def test_describe_scene_rejects_wrong_types(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    bad = dict(SCENE_OK, has_ruler="yes")
    fake = FakeClient([fake_response(json.dumps(bad), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(ModelOutputError, match="boolean"):
        spark.describe_scene(tmp_path / "x.jpg" if False else b"x")


def test_describe_scene_retake_consistency(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    inconsistent = dict(SCENE_OK, needs_retake=True, retake_reasons=[])
    fake = FakeClient([fake_response(json.dumps(inconsistent), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    with pytest.raises(ModelOutputError, match="retake"):
        spark.describe_scene(b"x")
    flipped = dict(SCENE_OK, needs_retake=False, retake_reasons=["blurry"])
    fake2 = FakeClient([fake_response(json.dumps(flipped), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake2)
    with pytest.raises(ModelOutputError, match="retake"):
        spark.describe_scene(b"x")


def test_describe_scene_media_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(MediaError, match="not found"):
        spark.describe_scene(tmp_path / "missing.jpg")
    bad = tmp_path / "a.gif"
    bad.write_bytes(b"gif")
    with pytest.raises(MediaError, match="unsupported"):
        spark.describe_scene(bad)


def test_unpriced_model_refused_before_call(monkeypatch, tmp_path):
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(ValueError, match="no official per-token price"):
        spark.describe_scene(b"x", model="muse-spark-9.9")


def test_spend_limit_checked_before_call(tmp_path, monkeypatch):
    tracker = _tracker(tmp_path, limit=0.0)
    with pytest.raises(SpendLimitExceeded):
        spark.describe_scene(b"x", tracker=tracker)


def test_suggest_release_time_success(tmp_path, monkeypatch):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"fake-video")
    payload = {"candidate_t0_s": 1.5, "reason": "hand lifts away, then the block moves"}
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-9")
    tracker = _tracker(tmp_path)
    out = spark.suggest_release_time(clip, tracker=tracker)
    assert out == {"candidate_t0_s": 1.5, "reason": payload["reason"],
                     "source": "muse-spark-1.3"}
    parts = fake.responses.calls[0]["input"][0]["content"]
    assert parts[1] == {"type": "input_file", "file_id": "file-9"}
    assert tracker.total_usd() > 0


def test_release_reason_may_repeat_candidate_but_no_other_numbers(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-9")
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"v")
    ok = {"candidate_t0_s": 1.5, "reason": "motion starts at about 1.5"}
    fake = FakeClient([fake_response(json.dumps(ok), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    assert spark.suggest_release_time(clip)["candidate_t0_s"] == 1.5

    bad = {"candidate_t0_s": 1.5, "reason": "between frame 30 and 45 it moves"}
    fake2 = FakeClient([fake_response(json.dumps(bad), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake2)
    with pytest.raises(ModelOutputError, match="must not contain"):
        spark.suggest_release_time(clip)

    null_bad = {"candidate_t0_s": None, "reason": "unclear, maybe 2 seconds in"}
    fake3 = FakeClient([fake_response(json.dumps(null_bad), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake3)
    with pytest.raises(ModelOutputError, match="must not contain"):
        spark.suggest_release_time(clip)


def test_release_negative_candidate_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-9")
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"v")
    bad = {"candidate_t0_s": -1, "reason": "moving already"}
    fake = FakeClient([fake_response(json.dumps(bad), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    with pytest.raises(ModelOutputError, match=">= 0"):
        spark.suggest_release_time(clip)


def _segment_setup(tmp_path, monkeypatch, payload):
    clip = tmp_path / "seg.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-9")
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    return clip, fake


def test_suggest_motion_segment_success(tmp_path, monkeypatch):
    payload = {
        "object": "tennis ball",
        "assumed_model": "free_flight",
        "candidate_t_start": 1.0,
        "candidate_t_end": 2.5,
        "reason": "a ball leaves the hand and arcs down to the floor",
    }
    clip, fake = _segment_setup(tmp_path, monkeypatch, payload)
    tracker = _tracker(tmp_path)
    out = spark.suggest_motion_segment(clip, tracker=tracker)
    assert out == {**payload, "source": "muse-spark-1.3"}
    call = fake.responses.calls[0]
    assert call["model"] == "muse-spark-1.3"
    assert call["text"]["type"] == "json_schema"
    assert fake.responses.calls[0]["input"][0]["content"][1]["type"] == "input_file"
    assert tracker.total_usd() > 0


def test_suggest_motion_segment_none_model(tmp_path, monkeypatch):
    payload = {
        "object": "crowd",
        "assumed_model": "none",
        "candidate_t_start": None,
        "candidate_t_end": None,
        "reason": "several people walking, no single moving object",
    }
    clip, _ = _segment_setup(tmp_path, monkeypatch, payload)
    out = spark.suggest_motion_segment(clip)
    assert out["assumed_model"] == "none"
    assert out["candidate_t_start"] is None


def test_suggest_motion_segment_rejects_bad_shapes(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    base = {
        "object": "ball",
        "assumed_model": "slide",
        "candidate_t_start": 0.5,
        "candidate_t_end": 2.0,
        "reason": "block slides down",
    }
    cases = [
        (dict(base, assumed_model="orbit"), "assumed_model"),
        (dict(base, candidate_t_start=-1), ">= 0"),
        (dict(base, candidate_t_end=0.5), "after candidate_t_start"),
        (dict(base, object=""), "non-empty"),
        (dict(base, object="ball 3 of 5"), "must not contain"),
        (dict(base, reason="moves between 1 and 2 seconds"), "must not contain"),
        (dict(base, assumed_model="none"), "null timestamps"),
    ]
    for payload, match in cases:
        clip, _ = _segment_setup(tmp_path, monkeypatch, payload)
        with pytest.raises(ModelOutputError, match=match):
            spark.suggest_motion_segment(clip)


def test_suggest_motion_segment_reason_may_repeat_candidates(tmp_path, monkeypatch):
    payload = {
        "object": "ball",
        "assumed_model": "free_flight",
        "candidate_t_start": 1.0,
        "candidate_t_end": 2.5,
        "reason": "flight from 1.0 to 2.5",
    }
    clip, _ = _segment_setup(tmp_path, monkeypatch, payload)
    out = spark.suggest_motion_segment(clip)
    assert out["candidate_t_end"] == 2.5


def test_suggest_motion_segment_retries_bad_json(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    clip = tmp_path / "s.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-9")
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    fake = FakeClient([fake_response("oops", fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    with pytest.raises(ModelOutputError):
        spark.suggest_motion_segment(clip)
    assert len(fake.responses.calls) == 3


def test_suggest_motion_segment_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(MediaError, match="not found"):
        spark.suggest_motion_segment(tmp_path / "missing.mp4")


def _capture_setup(tmp_path, monkeypatch, payload):
    clip = tmp_path / "cap.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-9")
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    return clip, fake


def test_check_capture_conditions_success(tmp_path, monkeypatch):
    payload = {
        "object": "tennis ball",
        "camera_static": True,
        "is_side_view": True,
        "object_visible_throughout": True,
        "reasons": [],
    }
    clip, fake = _capture_setup(tmp_path, monkeypatch, payload)
    tracker = _tracker(tmp_path)
    out = spark.check_capture_conditions(clip, tracker=tracker)
    assert out == {**payload, "source": "muse-spark-1.3"}
    assert fake.responses.calls[0]["text"]["type"] == "json_schema"
    assert tracker.total_usd() > 0


def test_check_capture_conditions_hint_and_failure(tmp_path, monkeypatch):
    payload = {
        "object": "ball",
        "camera_static": False,
        "is_side_view": True,
        "object_visible_throughout": False,
        "reasons": ["camera shakes", "ball leaves the frame at the end"],
    }
    clip, fake = _capture_setup(tmp_path, monkeypatch, payload)
    out = spark.check_capture_conditions(clip, object_hint="tennis ball")
    assert out["camera_static"] is False
    assert len(out["reasons"]) == 2
    assert "tennis ball" in fake.responses.calls[0]["input"][0]["content"][0]["text"]


def test_check_capture_conditions_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    base = {
        "object": "ball",
        "camera_static": True,
        "is_side_view": True,
        "object_visible_throughout": True,
        "reasons": [],
    }
    cases = [
        (dict(base, camera_static="yes"), "must be boolean"),
        (dict(base, reasons=["fine"]), "must be empty"),
        (dict(base, camera_static=False, reasons=[]), "at least one reason"),
        (dict(base, object="ball 2"), "must not contain"),
        (dict(base, camera_static=False, reasons=["shakes for 3 seconds"]), "must not contain"),
    ]
    for payload, match in cases:
        clip, _ = _capture_setup(tmp_path, monkeypatch, payload)
        with pytest.raises(ModelOutputError, match=match):
            spark.check_capture_conditions(clip)


def test_check_capture_conditions_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(MediaError, match="not found"):
        spark.check_capture_conditions(tmp_path / "missing.mp4")


def _object_setup(tmp_path, monkeypatch, payloads):
    clip = tmp_path / "obj.mp4"
    clip.write_bytes(b"v")
    stills = []
    for i in range(2):
        p = tmp_path / f"s{i}.jpg"
        p.write_bytes(b"fake-jpeg")
        stills.append(p)
    monkeypatch.setattr(spark._sam, "_probe_clip",
                        lambda path: {"fps": 30.0, "n_frames": 300,
                                      "width": 640, "height": 480})
    monkeypatch.setattr(spark, "_start_stills", lambda video, dur: stills)
    fake = FakeClient([fake_response(json.dumps(p), fake_usage()) for p in payloads])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    return clip, fake


def test_suggest_object_success(tmp_path, monkeypatch):
    payload = {"object_name": "orange basketball",
               "camera_looks_static": True,
               "reason": "ball on the floor, background identical in both stills"}
    clip, fake = _object_setup(tmp_path, monkeypatch, [payload])
    tracker = _tracker(tmp_path)
    out = spark.suggest_object(clip, tracker=tracker)
    assert out == {**payload, "source": "muse-spark-1.3"}
    parts = fake.responses.calls[0]["input"][0]["content"]
    assert parts[0]["type"] == "input_text"
    assert sum(p["type"] == "input_image" for p in parts) == 2
    assert tracker.total_usd() > 0


def test_suggest_object_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    good = {"object_name": "orange basketball", "camera_looks_static": True,
            "reason": "background identical in both stills"}
    cases = [
        ({**good, "camera_looks_static": "yes"}, "boolean"),
        ({**good, "object_name": "ball number 42"}, "failed checks"),
        ({**good, "reason": "moved 30 meters"}, "failed checks"),
        ({**good, "reason": "this proves a tripod"}, "failed checks"),
        ({**good, "reason": "x" * 201}, "200 characters"),
        ({"suggestion": good}, None),  # envelope alias accepted
    ]
    n_calls = spark.MAX_RETRIES + 1 if hasattr(spark, "MAX_RETRIES") else 3
    for payload, match in cases:
        clip, fake = _object_setup(tmp_path, monkeypatch, [payload] * n_calls)
        if match is None:
            assert spark.suggest_object(clip) == {**good, "source": "muse-spark-1.3"}
        else:
            with pytest.raises(ModelOutputError, match=match):
                spark.suggest_object(clip)


def test_suggest_object_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(spark, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(MediaError, match="not found"):
        spark.suggest_object(tmp_path / "missing.mp4")
