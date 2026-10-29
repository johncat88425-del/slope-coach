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
