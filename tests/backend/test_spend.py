"""T110: GET /api/spend reports cumulative spend and the hard ceiling."""
from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from meta_client import spark
from meta_client.cost import CostTracker
from meta_client.exceptions import SpendLimitExceeded
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path, limit=120.0):
    return CostTracker(tmp_path / "cost.csv", limit_usd=limit)


def _spent(tracker):
    tracker.record("muse-spark-1.3", "test.op",
                   input_tokens=1000, output_tokens=100)
    return tracker.total_usd()


def test_spend_reports_total_and_limit(tmp_path, monkeypatch):
    tracker = _tracker(tmp_path)
    spent = _spent(tracker)
    monkeypatch.setattr("meta_client.cost.get_tracker", lambda: tracker)
    r = TestClient(app).get("/api/spend")
    assert r.status_code == 200
    assert r.json() == {"spent_usd": round(spent, 4), "limit_usd": 120.0,
                        "at_limit": False}


def test_spend_at_limit_when_ceiling_reached(tmp_path, monkeypatch):
    tracker = _tracker(tmp_path, limit=0.001)
    _spent(tracker)  # ~$0.0017, over the tiny test ceiling
    assert tracker.total_usd() >= 0.001
    monkeypatch.setattr("meta_client.cost.get_tracker", lambda: tracker)
    body = TestClient(app).get("/api/spend").json()
    assert body["at_limit"] is True
    assert body["limit_usd"] == 0.001


def test_spend_without_meta_client_reports_zero(monkeypatch):
    monkeypatch.setitem(sys.modules, "meta_client.cost", None)
    assert TestClient(app).get("/api/spend").json() == {
        "spent_usd": 0.0, "limit_usd": 120.0, "at_limit": False}


def test_paid_call_refused_at_limit_without_api_call(tmp_path, monkeypatch):
    tracker = _tracker(tmp_path, limit=0.001)
    _spent(tracker)
    photo = tmp_path / "setup.jpg"
    photo.write_bytes(b"\xff\xd8fake-jpeg")
    fake = FakeClient([fake_response("{}", fake_usage())])
    monkeypatch.setattr(spark, "get_client", lambda: fake)
    with pytest.raises(SpendLimitExceeded):
        spark.describe_scene(photo, tracker=tracker)
    assert fake.responses.calls == []
