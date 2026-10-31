import json
import time

import pytest

from meta_client import explain
from meta_client.cost import CostTracker
from meta_client.exceptions import ModelOutputError
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


PAYLOAD = {
    "verdict": "discrepancy",
    "arrival_error_rel": 0.25,
    "tolerance_rel": 0.15,
    "reasons": ["arrival differs"],
    "numbers": {"g_apparent_m_s2": 9.81},
}


def _setup(monkeypatch, tmp_path, text):
    fake = FakeClient([fake_response(json.dumps({"explanation": text}), fake_usage())])
    monkeypatch.setattr(explain, "get_client", lambda: fake)
    monkeypatch.setattr(explain, "get_tracker", lambda: _tracker(tmp_path))
    return fake


def test_explain_success_grounds_numbers(tmp_path, monkeypatch):
    fake = _setup(monkeypatch, tmp_path, "到達時間誤差 25%，超過容忍 15%，與假設不一致。")
    tracker = _tracker(tmp_path)
    out = explain.explain_result(PAYLOAD, tracker=tracker)
    assert "不一致" in out["explanation"]
    call = fake.responses.calls[0]
    assert call["text"]["type"] == "json_schema"
    assert isinstance(call["input"], str)
    assert "9.81" in call["input"]  # payload is in the prompt
    assert tracker.total_usd() > 0


def test_explain_audit_kind(tmp_path, monkeypatch):
    fake = _setup(monkeypatch, tmp_path, "與假設一致。")
    out = explain.explain_result({"verdict": "consistent"}, kind="audit")
    assert out == {"explanation": "與假設一致。", "source": "muse-spark-1.3"}
    assert fake.responses.calls[0]["model"] == "muse-spark-1.3"


def test_explain_rejects_ungrounded_number(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    fake = _setup(monkeypatch, tmp_path, "誤差是 42%，與假設不一致。")
    with pytest.raises(ModelOutputError, match="output check failed"):
        explain.explain_result(PAYLOAD)
    assert len(fake.responses.calls) == 3


AUDIT_PAYLOAD = {
    "verdict": "inconsistent",
    "numbers": {"g_apparent_m_s2": 0.24, "g_vs_earth": 0.02},
    "reasons": ["apparent g 0.24 m/s^2 is outside 8.34-11.28"],
}


def test_explain_accepts_numbers_from_reason_sentences(tmp_path, monkeypatch):
    # T115: thresholds live in reason strings, not numeric fields; quoting
    # them must pass because the prompt allows payload numbers.
    fake = _setup(monkeypatch, tmp_path, "表觀重力約 0.24，低於 8.34 到 11.28，與假設不一致。")
    out = explain.explain_result(AUDIT_PAYLOAD, kind="audit")
    assert "不一致" in out["explanation"]
    assert len(fake.responses.calls) == 1  # no retry


def test_explain_still_rejects_absent_numbers(tmp_path, monkeypatch):
    # Strictness preserved: 9.81 and frame rates appear nowhere in this
    # payload, so quoting them still fails.
    monkeypatch.setattr(time, "sleep", lambda s: None)
    for text in ("表觀重力約 0.24，遠低於 9.81，與假設不一致。",
                 "以 15 fps 追蹤，表觀重力約 0.24，與假設不一致。"):
        fake = _setup(monkeypatch, tmp_path, text)
        with pytest.raises(ModelOutputError, match="output check failed"):
            explain.explain_result(AUDIT_PAYLOAD, kind="audit")
        assert len(fake.responses.calls) == 3


def test_explain_rejects_causal_overclaim(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    _setup(monkeypatch, tmp_path, "這證實了摩擦力是真因。")
    with pytest.raises(ModelOutputError, match="causal overclaim"):
        explain.explain_result(PAYLOAD)


def test_explain_rejects_authenticity_language(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    # backend check_model_text catches most of these first (T97 expanded list)
    for bad in ("這支假影片有問題。", "看起來像 AI 生成的。", "This fake video is off."):
        _setup(monkeypatch, tmp_path, bad)
        with pytest.raises(ModelOutputError, match="output check failed"):
            explain.explain_result(PAYLOAD)
    # bare 真偽 is only on the T28 extra list
    _setup(monkeypatch, tmp_path, "有真偽問題。")
    with pytest.raises(ModelOutputError, match="authenticity"):
        explain.explain_result(PAYLOAD)


VEHICLE_CONSISTENT = {
    "assumed_model": "vehicle",
    "verdict": "consistent",
    "numbers": {"speed_km_h": 49.0, "accel_g": 0.6, "car_length_px": 210.5},
    "reasons": [],
}

VEHICLE_INCONSISTENT = {
    "assumed_model": "vehicle",
    "verdict": "inconsistent",
    "numbers": {"speed_km_h": 30.0, "accel_g": 3.0},
    "reasons": ["needs 3.0 g of acceleration; road cars on tyres stay under about 1.2 g"],
}

VEHICLE_REFUSED = {
    "assumed_model": "vehicle",
    "verdict": "insufficient_data",
    "numbers": {"tracked_fraction": 0.73},
    "reasons": ["object tracked in only 73% of frames"],
}


def test_explain_vehicle_consistent(tmp_path, monkeypatch):
    fake = _setup(monkeypatch, tmp_path,
                  "車速約 49 公里每小時，加速度約 0.6 g，與正常路上行駛一致。")
    out = explain.explain_result(VEHICLE_CONSISTENT, kind="audit")
    assert out["source"] == "muse-spark-1.3"
    assert "tyre-grip" in fake.responses.calls[0]["input"]


def test_explain_vehicle_inconsistent_quotes_limit(tmp_path, monkeypatch):
    fake = _setup(monkeypatch, tmp_path,
                  "加速度約 3.0 g，超過一般輪胎抓地力上限 1.2 g，與正常路上行駛不一致。")
    out = explain.explain_result(VEHICLE_INCONSISTENT, kind="audit")
    assert "不一致" in out["explanation"]
    assert len(fake.responses.calls) == 1  # 1.2 comes from the reason sentence


def test_explain_vehicle_insufficient(tmp_path, monkeypatch):
    _setup(monkeypatch, tmp_path, "只追到 73%，目前無法判斷。")
    out = explain.explain_result(VEHICLE_REFUSED, kind="audit")
    assert "無法判斷" in out["explanation"]


def test_explain_vehicle_rejects_sneaked_number(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    fake = _setup(monkeypatch, tmp_path, "加速度約 99.9 g，與正常路上行駛不一致。")
    with pytest.raises(ModelOutputError, match="output check failed"):
        explain.explain_result(VEHICLE_INCONSISTENT, kind="audit")
    assert len(fake.responses.calls) == 3


def test_explain_vehicle_rejects_fake_word(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    _setup(monkeypatch, tmp_path, "這支影片是假的，與假設不一致。")
    with pytest.raises(ModelOutputError, match="authenticity"):
        explain.explain_result(VEHICLE_INCONSISTENT, kind="audit")


def test_explain_rejects_bad_kind_without_call(tmp_path, monkeypatch):
    monkeypatch.setattr(explain, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(ValueError, match="kind"):
        explain.explain_result(PAYLOAD, kind="orbit")
    with pytest.raises(ModelOutputError, match="mapping"):
        explain.explain_result(["not", "a", "dict"])


def test_explain_english_success(tmp_path, monkeypatch):
    fake = _setup(monkeypatch, tmp_path, "Arrival error is 25%, over the 15% tolerance: inconsistent.")
    out = explain.explain_result(PAYLOAD, lang="en")
    assert "inconsistent" in out["explanation"]
    assert "judge in English" in fake.responses.calls[0]["input"]


def test_explain_english_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    _setup(monkeypatch, tmp_path, "This proves friction did it.")
    with pytest.raises(ModelOutputError, match="causal overclaim"):
        explain.explain_result(PAYLOAD, lang="en")
    _setup(monkeypatch, tmp_path, "This looks AI-generated.")
    with pytest.raises(ModelOutputError, match="output check failed"):
        explain.explain_result(PAYLOAD, lang="en")
    with pytest.raises(ValueError, match="lang"):
        explain.explain_result(PAYLOAD, lang="fr")
