import json
import time

import pytest

from meta_client import voice
from meta_client.cost import CostTracker
from meta_client.exceptions import (
    AuthError,
    MediaError,
    MetaClientError,
    ModelOutputError,
)
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


class _Resp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _patch_wav(monkeypatch, tmp_path):
    def fake_wav(src):
        wav = tmp_path / "in.wav"
        wav.write_bytes(b"fake-wav")
        return wav

    monkeypatch.setattr(voice, "_to_wav", fake_wav)


def test_transcribe_success_and_cost(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    _patch_wav(monkeypatch, tmp_path)
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert "request" in kwargs["data"]
        # T166: batch endpoint requires audioEncoding "WAV" for our RIFF/WAVE upload
        assert json.loads(kwargs["data"]["request"])["audioEncoding"] == "WAV"
        return _Resp(200, {"transcript": "斜坡長一米", "audioDurationMs": 5900})

    monkeypatch.setattr(voice.httpx, "post", fake_post)
    tracker = _tracker(tmp_path)
    clip = tmp_path / "rec.m4a"
    clip.write_bytes(b"fake-audio")
    out = voice.transcribe(clip, tracker=tracker)
    assert out == {"transcript": "斜坡長一米", "audio_seconds": 5.9,
                     "source": "muse-voice-transcribe-1.0"}
    assert calls[0][0].endswith("/asr/transcribe")
    assert tracker.total_usd() == pytest.approx(5 / 3600 * 0.18)  # whole seconds
    assert not (tmp_path / "in.wav").exists()  # transcribe deletes the converted wav


def test_transcribe_retries_then_gives_up(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setenv("MODEL_API_KEY", "k")
    _patch_wav(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(
        voice.httpx, "post",
        lambda *a, **k: (calls.append(1), _Resp(500, text="boom"))[1],
    )
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    clip = tmp_path / "r.m4a"
    clip.write_bytes(b"v")
    with pytest.raises(MetaClientError, match="after retries"):
        voice.transcribe(clip)
    assert len(calls) == 3


def test_transcribe_no_retry_on_400_and_401(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "k")
    _patch_wav(monkeypatch, tmp_path)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    clip = tmp_path / "r.m4a"
    clip.write_bytes(b"v")
    monkeypatch.setattr(voice.httpx, "post", lambda *a, **k: _Resp(400, text="bad wav"))
    with pytest.raises(ModelOutputError, match="400"):
        voice.transcribe(clip)
    monkeypatch.setattr(voice.httpx, "post", lambda *a, **k: _Resp(401, text="no"))
    with pytest.raises(AuthError):
        voice.transcribe(clip)


def test_transcribe_validates_response(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "k")
    _patch_wav(monkeypatch, tmp_path)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    clip = tmp_path / "r.m4a"
    clip.write_bytes(b"v")
    monkeypatch.setattr(
        voice.httpx, "post", lambda *a, **k: _Resp(200, {"transcript": "  "})
    )
    with pytest.raises(ModelOutputError, match="empty transcript"):
        voice.transcribe(clip)
    monkeypatch.setattr(
        voice.httpx, "post",
        lambda *a, **k: _Resp(200, {"transcript": "hi", "audioDurationMs": "long"}),
    )
    with pytest.raises(ModelOutputError, match="audioDurationMs"):
        voice.transcribe(clip)


def test_transcribe_missing_key_and_file(tmp_path, monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    clip = tmp_path / "r.m4a"
    clip.write_bytes(b"v")
    _patch_wav(monkeypatch, tmp_path)
    with pytest.raises(AuthError):
        voice.transcribe(clip)
    with pytest.raises(MediaError, match="not found"):
        voice.transcribe(tmp_path / "missing.m4a")


def test_extract_setup_fields_success(tmp_path, monkeypatch):
    payload = {"slope_length_m": 1.0, "slope_height_m": 0.3,
               "release_notes": "擋片放開"}
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(voice, "get_client", lambda: fake)
    tracker = _tracker(tmp_path)
    out = voice.extract_setup_fields("斜坡長一公尺高三十公分，擋片放開", tracker=tracker)
    assert out == {**payload, "source": "muse-spark-1.3"}
    assert fake.responses.calls[0]["text"]["type"] == "json_schema"
    assert tracker.total_usd() > 0


def test_extract_setup_fields_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    cases = [
        ({"slope_length_m": -1, "slope_height_m": 0.3, "release_notes": "x"}, ">= 0"),
        ({"slope_length_m": "long", "slope_height_m": None, "release_notes": "x"}, "number or null"),
        ({"slope_length_m": None, "slope_height_m": None, "release_notes": 5}, "must be a string"),
    ]
    for payload, match in cases:
        fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
        monkeypatch.setattr(voice, "get_client", lambda: fake)
        with pytest.raises(ModelOutputError, match=match):
            voice.extract_setup_fields("something")
    with pytest.raises(ValueError, match="non-empty"):
        voice.extract_setup_fields("  ")


ANSWER_OK = {
    "camera_static": True,
    "slow_motion": False,
    "object_size": {"value": 11, "unit": "cm"},
    "length": None,
    "time_window": {"t_start_s": 0.5, "t_end_s": 3.0},
    "assumed_model": "free_flight",
}


def test_extract_interview_fields_success(tmp_path, monkeypatch):
    fake = FakeClient([fake_response(json.dumps(ANSWER_OK), fake_usage())])
    monkeypatch.setattr(voice, "get_client", lambda: fake)
    tracker = _tracker(tmp_path)
    out = voice.extract_interview_fields(
        "camera on tripod, no slow motion, ball eleven centimeters", tracker=tracker)
    assert out["object_size"] == {"value": 11.0, "unit": "cm"}
    assert out["camera_static"] is True
    assert out["source"] == "muse-spark-1.3"
    assert tracker.total_usd() > 0


def test_extract_interview_fields_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    bad_unit = dict(ANSWER_OK, object_size={"value": 11, "unit": "inch"})
    bad_size = dict(ANSWER_OK, object_size={"value": -2, "unit": "cm"})
    bad_window = dict(ANSWER_OK, time_window={"t_start_s": 3.0, "t_end_s": 1.0})
    bad_model = dict(ANSWER_OK, assumed_model="orbit")
    bad_bool = dict(ANSWER_OK, camera_static="yes")
    cases = [
        (bad_unit, "m, cm, or mm"),
        (bad_size, "out of range"),
        (bad_window, "end after it starts"),
        (bad_model, "free_flight, bounce, pendulum, vehicle, or null"),
        (bad_bool, "boolean or null"),
    ]
    for payload, match in cases:
        fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
        monkeypatch.setattr(voice, "get_client", lambda: fake)
        with pytest.raises(ModelOutputError, match=match):
            voice.extract_interview_fields("something")


def test_extract_interview_fields_accepts_loose_shapes(tmp_path, monkeypatch):
    payload = dict(ANSWER_OK, object_size="11 centimeters",
                   time_window=[0.5, 3.0])
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(voice, "get_client", lambda: fake)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    out = voice.extract_interview_fields("ball eleven centimeters")
    assert out["object_size"] == {"value": 11.0, "unit": "cm"}
    assert out["time_window"] == {"t_start_s": 0.5, "t_end_s": 3.0}
    bad = dict(ANSWER_OK, object_size="eleven centimeters")
    fake2 = FakeClient([fake_response(json.dumps(bad), fake_usage())])
    monkeypatch.setattr(voice, "get_client", lambda: fake2)
    with pytest.raises(ModelOutputError, match="number.*unit"):
        voice.extract_interview_fields("ball eleven centimeters")


def test_answer_interview_voice_converts_and_marks_unconfirmed(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(voice, "transcribe",
                        lambda path, **kw: {"transcript": "ball eleven cm", "audio_seconds": 2.0})
    monkeypatch.setattr(voice, "extract_interview_fields", lambda text, **kw: ANSWER_OK)
    out = voice.answer_interview_voice(tmp_path / "a.m4a")
    assert out["mock"] is False
    assert out["fields"]["object_size_m"] == {"value": 0.11, "confirmed": False}
    assert out["fields"]["camera_static"] == {"value": True, "confirmed": False}
    assert "length_m" not in out["fields"]
    assert out["source"] == {"transcript": "muse-voice-transcribe-1.0",
                             "fields": "muse-spark-1.3"}


def test_answer_interview_voice_vehicle_car_length(tmp_path, monkeypatch):
    transcript = "it's a car driving past, about four and a half metres long"
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(voice, "transcribe",
                        lambda path, **kw: {"transcript": transcript, "audio_seconds": 4.0})
    payload = {"camera_static": None, "slow_motion": None,
               "object_size": {"value": 4.5, "unit": "m"}, "length": None,
               "time_window": None, "assumed_model": "vehicle"}
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(voice, "get_client", lambda: fake)
    monkeypatch.setattr(voice, "get_tracker", lambda: _tracker(tmp_path))
    out = voice.answer_interview_voice(tmp_path / "a.m4a")
    assert out["transcript"] == transcript
    assert out["fields"]["assumed_model"] == {"value": "vehicle", "confirmed": False}
    assert out["fields"]["object_size_m"] == {"value": 4.5, "confirmed": False}


def test_answer_interview_voice_mock_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    out = voice.answer_interview_voice(tmp_path / "missing.m4a")
    assert out == {"transcript": voice.MOCK_NO_KEY_TRANSCRIPT, "fields": {}, "mock": True,
                   "source": {"transcript": "mock", "fields": "mock"}}
