import json
import time

import pytest

from meta_client import retake
from meta_client.cost import CostTracker
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


REFUSED = {
    "assumed_model": "free_flight",
    "verdict": "insufficient_data",
    "reasons": ["object size changes -48% along the track; it moves towards "
                "or away from the camera, which this 2D check cannot judge"],
}


def _setup(monkeypatch, tmp_path, payload):
    fake = FakeClient([fake_response(json.dumps(payload), fake_usage())])
    monkeypatch.setattr(retake, "get_client", lambda: fake)
    monkeypatch.setattr(retake, "get_tracker", lambda: _tracker(tmp_path))
    return fake


def test_retake_tips_success(tmp_path, monkeypatch):
    tips = {"tips": ["球往鏡頭飛：請站到球飛行路線的正側面再拍一次。",
                     "固定相機不要跟著球轉。"]}
    fake = _setup(monkeypatch, tmp_path, tips)
    tracker = _tracker(tmp_path)
    out = retake.write_retake_tips(REFUSED, tracker=tracker)
    assert out == {**tips, "source": "muse-spark-1.3"}
    assert "cannot judge" in fake.responses.calls[0]["input"]  # reasons in prompt
    assert tracker.total_usd() > 0


def test_retake_tips_may_quote_reason_numbers(tmp_path, monkeypatch):
    audit = {"assumed_model": "vehicle", "verdict": "insufficient_data",
             "reasons": ["track covers only 0.47 s; need at least 0.5 s"]}
    tips = {"tips": ["只錄到 0.47 秒，請把完整動作錄滿 0.5 秒以上。"]}
    _setup(monkeypatch, tmp_path, tips)
    out = retake.write_retake_tips(audit)
    assert out["tips"] == tips["tips"]


def test_retake_tips_rejects_sneaked_number(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    tips = {"tips": ["請站到 99 公尺外再拍一次。"]}
    fake = _setup(monkeypatch, tmp_path, tips)
    assert retake.write_retake_tips(REFUSED) is None
    assert len(fake.responses.calls) == 3


def test_retake_tips_rejects_banned_words(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    for tips in ({"tips": ["這證實了相機在動。"]},
                 {"tips": ["這支影片是假的。"]}):
        fake = _setup(monkeypatch, tmp_path, tips)
        assert retake.write_retake_tips(REFUSED) is None
        assert len(fake.responses.calls) == 3


def test_retake_tips_only_for_refused_audits(tmp_path, monkeypatch):
    monkeypatch.setattr(
        retake, "get_client",
        lambda: (_ for _ in ()).throw(AssertionError("must not call API")))
    monkeypatch.setattr(retake, "get_tracker", lambda: _tracker(tmp_path))
    audit = dict(REFUSED, verdict="consistent")
    assert retake.write_retake_tips(audit) is None
    assert retake.write_retake_tips({**audit, "reasons": []}) is None


def test_retake_tips_rejects_long_tip(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    fake = _setup(monkeypatch, tmp_path, {"tips": ["站側面。" * 30]})
    assert retake.write_retake_tips(REFUSED) is None
    assert len(fake.responses.calls) == 3


def test_retake_tips_bad_lang_without_call(tmp_path, monkeypatch):
    monkeypatch.setattr(
        retake, "get_client",
        lambda: (_ for _ in ()).throw(AssertionError("must not call API")))
    with pytest.raises(ValueError, match="lang"):
        retake.write_retake_tips(REFUSED, "fr")
