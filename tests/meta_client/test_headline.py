import json
import time

from meta_client import headline
from meta_client.client import MAX_RETRIES
from meta_client.cost import CostTracker
from tests.meta_client.helpers import FakeClient, fake_response, fake_usage


def _tracker(tmp_path):
    return CostTracker(tmp_path / "cost.csv", limit_usd=120)


def _audit(**over):
    audit = {
        "verdict": "inconsistent",
        "numbers": {"g_vs_earth": 0.0122},
        "nearest_body": "月球",
    }
    audit.update(over)
    return audit


def _setup(monkeypatch, tmp_path, payloads):
    fake = FakeClient([fake_response(json.dumps(p), fake_usage()) for p in payloads])
    monkeypatch.setattr(headline, "get_client", lambda: fake)
    monkeypatch.setattr(headline, "get_tracker", lambda: _tracker(tmp_path))
    return fake


def test_headline_success_fills_slots(tmp_path, monkeypatch):
    payload = {"headline_template": "這顆球落得像在{nearest_body}上：表觀重力只有地球的{g_vs_earth:2}倍"}
    fake = _setup(monkeypatch, tmp_path, [payload])
    tracker = _tracker(tmp_path)
    out = headline.write_headline(_audit(), tracker=tracker)
    assert out == {"headline": "這顆球落得像在月球上：表觀重力只有地球的0.01倍",
                     "source": "muse-spark-1.3"}
    assert fake.responses.calls[0]["text"]["name"] == "headline"
    assert tracker.total_usd() > 0


def test_headline_rejects_and_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    cases = [
        {"headline_template": "這顆球落得像在月球上：只有地球的0.01倍"},  # raw digits, no slots
        {"headline_template": "這顆球{unknown_slot}很奇怪"},  # unknown slot
        {"headline_template": "這顆球落得像在{nearest_body}上：有{g_vs_earth:2}倍，證實有問題"},  # causal
        {"headline_template": "這支{nearest_body}假影片只有{g_vs_earth:2}倍"},  # 假 banned
        {"headline_template": "x" * 201},  # too long
        {"headline": "missing key"},  # wrong key
    ]
    for payload in cases:
        fake = _setup(monkeypatch, tmp_path, [payload] * (MAX_RETRIES + 1))
        assert headline.write_headline(_audit()) is None
        assert len(fake.responses.calls) == MAX_RETRIES + 1


def test_headline_none_without_gravity_numbers(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    fake = _setup(monkeypatch, tmp_path, [])
    assert headline.write_headline(_audit(verdict="insufficient_data")) is None
    assert headline.write_headline({"verdict": "inconsistent", "numbers": {}}) is None
    assert headline.write_headline(_audit(nearest_body=None)) is None
    assert fake.responses.calls == []  # no API call spent


def test_rounded_number_sources_cover_display_rounding():
    sources = headline.rounded_number_sources({"g_vs_earth": 0.0122})
    assert sources["g_vs_earth_r2"] == 0.01
    assert sources["g_vs_earth_r0"] == 0.0
