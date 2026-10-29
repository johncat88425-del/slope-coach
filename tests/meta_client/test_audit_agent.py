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


def _audit(n=20, fps=60.0):
    pts = []
    for i in range(n):
        t = i / fps
        pts.append([t, 100 + 50 * t, 100 + 300 * t + 0.5 * 1500 * t * t])
    return {"points": pts, "sizes": [20.0] * n, "object_size_m": 0.06}


def _call(name, args, call_id="c1"):
    return SimpleNamespace(
        type="function_call", name=name, arguments=json.dumps(args), call_id=call_id
    )


def _resp(*items):
    return SimpleNamespace(output=list(items), usage=fake_usage())


def test_run_check_free_flight_numbers():
    out = agent._run_check("free_flight", _audit())
    assert out["verdict"] in ("consistent", "inconsistent", "insufficient_data")
    assert out["numbers"]["g_apparent_m_s2"] == pytest.approx(4.5, rel=0.05)
    assert out["numbers"]["n_points"] == 20


def test_run_check_bounce_and_persistence_shapes():
    bounce = agent._run_check("bounce", _audit())
    assert set(bounce) == {"check", "verdict", "reasons", "numbers"}
    persist = agent._run_check("persistence", _audit())
    assert persist["numbers"] == {"n_events": 0}


def test_run_check_unknown_and_too_few():
    assert "error" in agent._run_check("orbit", _audit())
    out = agent._run_check("free_flight", {"points": [[0.0, 1.0, 2.0]]})
    assert out["verdict"] == "insufficient_data"


def test_plan_audit_checks_success(tmp_path, monkeypatch):
    g = agent._run_check("free_flight", _audit())["numbers"]["g_apparent_m_s2"]
    fake = FakeClient([
        _resp(_call("run_check", {"name": "free_flight"}, "c1")),
        _resp(_call("propose_plan", {
            "selected": ["free_flight"],
            "rationale": f"視在重力 {g:.2f}，與假設不一致。",
        }, "c2")),
    ])
    monkeypatch.setattr(agent, "get_client", lambda: fake)
    tracker = _tracker(tmp_path)
    out = agent.plan_audit_checks(_audit(), tracker=tracker)
    assert out["selected"] == ["free_flight"]
    assert "不一致" in out["rationale"]
    assert tracker.total_usd() > 0


def test_plan_rejects_unknown_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    run = _resp(_call("propose_plan", {"selected": ["orbit"], "rationale": "x"}, "c1"))
    fake = FakeClient([run, run, run])
    monkeypatch.setattr(agent, "get_client", lambda: fake)
    monkeypatch.setattr(agent, "get_tracker", lambda: _tracker(tmp_path))
    with pytest.raises(ModelOutputError, match="subset"):
        agent.plan_audit_checks(_audit())
    assert len(fake.responses.calls) == 3


def test_plan_empty_points_without_call(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "get_tracker", lambda: _tracker(tmp_path))
    out = agent.plan_audit_checks({"points": []})
    assert out == {"selected": [], "rationale": "目前證據不足"}
    with pytest.raises(ModelOutputError, match="must be a list"):
        agent.plan_audit_checks({"points": "nope"})
