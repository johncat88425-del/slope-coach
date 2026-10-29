import json
import time
from types import SimpleNamespace

import pytest

from meta_client import agent
from meta_client.cost import CostTracker
from meta_client.exceptions import ModelOutputError
from tests.meta_client.helpers import FakeClient, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


COMPARISON = {
    "verdict": "discrepancy",
    "evidence": [
        {
            "candidate": "release_check",
            "finding": "fitted v0 differs from zero",
            "numbers": {"v0_m_s": 0.35},
            "cannot_distinguish": "push vs timing offset",
        },
        {
            "candidate": "dimension_check",
            "finding": "acceleration differs",
            "numbers": {"a_err": 0.2},
            "cannot_distinguish": "angle vs friction",
        },
    ],
}


def _call(name, args, call_id="c1"):
    return SimpleNamespace(
        type="function_call", name=name, arguments=json.dumps(args), call_id=call_id
    )


def _resp(*items, usage=None):
    return SimpleNamespace(output=list(items), usage=usage or fake_usage())


def _setup(monkeypatch, tmp_path, responses):
    fake = FakeClient(responses)
    monkeypatch.setattr(agent, "get_client", lambda: fake)
    monkeypatch.setattr(agent, "get_tracker", lambda: _tracker(tmp_path))
    return fake


def test_choose_intervention_success(tmp_path, monkeypatch):
    fake = _setup(
        monkeypatch,
        tmp_path,
        [
            _resp(_call("get_evidence", {}, "c1")),
            _resp(_call("propose_check", {
                "check_type": "release_check",
                "rationale": "初速度 0.35，與假設不一致。",
            }, "c2")),
        ],
    )
    tracker = _tracker(tmp_path)
    out = agent.choose_intervention(COMPARISON, tracker=tracker)
    assert out["choice"] == "release_check"
    assert "不一致" in out["rationale"]
    assert out["source"] == "muse-spark-1.3"
    first = fake.responses.calls[0]
    assert first["tools"][0]["name"] == "get_evidence"
    assert len(fake.responses.calls) == 2
    assert tracker.total_usd() > 0  # both steps recorded in one row


def test_empty_evidence_returns_insufficient_without_call(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "get_tracker", lambda: _tracker(tmp_path))
    out = agent.choose_intervention({"verdict": "insufficient_data", "evidence": []})
    assert out == {"choice": None, "rationale": "目前證據不足"}


def test_rejects_choice_outside_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    get_ev = _resp(_call("get_evidence", {}, "c1"))
    propose_bad = _resp(_call("propose_check", {
        "check_type": "bounce_check", "rationale": "換個花樣。",
    }, "c2"))
    fake = _setup(monkeypatch, tmp_path, [get_ev, propose_bad] * 3)
    with pytest.raises(ModelOutputError, match="not among"):
        agent.choose_intervention(COMPARISON)
    assert len(fake.responses.calls) == 6  # 2 steps x 3 runs


def test_rejects_ungrounded_rationale(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    _setup(
        monkeypatch,
        tmp_path,
        [
            _resp(_call("get_evidence", {}, "c1")),
            _resp(_call("propose_check", {
                "check_type": "release_check", "rationale": "初速度 99，差很多。",
            }, "c2")),
        ],
    )
    with pytest.raises(ModelOutputError, match="output check failed"):
        agent.choose_intervention(COMPARISON)


def test_rejects_unknown_evidence_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "get_tracker", lambda: _tracker(tmp_path))
    bad = {"evidence": [{"candidate": "bounce_check", "numbers": {}}]}
    with pytest.raises(ModelOutputError, match="unknown evidence"):
        agent.choose_intervention(bad)
