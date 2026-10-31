import csv

import pytest

from meta_client import cost
from meta_client.exceptions import SpendLimitExceeded


def test_spark_standard_pricing():
    # 1M fresh input + 1M output == 1.25 + 4.25
    assert cost.token_cost_usd("muse-spark-1.3", 1_000_000, 1_000_000) == pytest.approx(5.50)


def test_cached_tokens_use_cached_rate():
    full = cost.token_cost_usd("muse-spark-1.3", 1000, 0)
    cached = cost.token_cost_usd("muse-spark-1.3", 1000, 0, cached_tokens=1000)
    assert full == pytest.approx(0.00125)
    assert cached == pytest.approx(0.00015)


def test_contributor_pricing():
    assert cost.token_cost_usd(
        "muse-spark-1.3-contributor", 1_000_000, 1_000_000
    ) == pytest.approx(0.30)


def test_wonder_pricing():
    assert cost.token_cost_usd("muse-wonder-1.0", 1_000_000, 1_000_000) == pytest.approx(24.0)


def test_unknown_model_refuses_to_price():
    with pytest.raises(ValueError, match="no recorded price"):
        cost.token_cost_usd("gpt-6", 10, 10)


def test_sam_video_minimum_50_frames():
    assert cost.sam_video_cost_usd(10) == pytest.approx(50 * 0.20 / 1000)
    assert cost.sam_video_cost_usd(150) == pytest.approx(150 * 0.20 / 1000)


def test_sam_image_and_voice():
    assert cost.sam_image_cost_usd(4) == pytest.approx(4 * 2.50 / 1000)
    assert cost.voice_cost_usd(59.9) == pytest.approx(59 / 3600 * 0.18)


def test_tracker_appends_and_totals(tmp_path):
    tracker = cost.CostTracker(tmp_path / "cost_log.csv", limit_usd=120)
    assert tracker.total_usd() == 0.0
    c1 = tracker.record("muse-spark-1.3", "spark.describe_scene",
                        input_tokens=1000, output_tokens=500)
    c2 = tracker.record("sam-3.1", "sam.track", frames=150)
    assert c1 == pytest.approx(1000 * 1.25 / 1e6 + 500 * 4.25 / 1e6)
    assert c2 == pytest.approx(150 * 0.20 / 1000)
    assert tracker.total_usd() == pytest.approx(c1 + c2)
    with open(tmp_path / "cost_log.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["model"] == "muse-spark-1.3"
    assert rows[1]["frames"] == "150"


def test_tracker_refuses_at_limit_without_logging(tmp_path):
    # Refusal triggers once the CUMULATIVE total reaches the ceiling: calls
    # already made are always logged (the money was spent), later calls stop.
    tracker = cost.CostTracker(tmp_path / "cost_log.csv", limit_usd=0.01)
    tracker.record("muse-spark-1.3", "over", input_tokens=1_000_000, output_tokens=0)
    with pytest.raises(SpendLimitExceeded, match="refusing new paid calls"):
        tracker.record("muse-spark-1.3", "next", input_tokens=100, output_tokens=0)
    with open(tmp_path / "cost_log.csv", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 1  # refused call left no row


def test_tracker_respects_env_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("SPEND_LIMIT_USD", "0.000001")
    tracker = cost.CostTracker(tmp_path / "cost_log.csv")
    tracker.record("muse-spark-1.3", "first", input_tokens=100, output_tokens=0)
    with pytest.raises(SpendLimitExceeded):
        tracker.record("muse-spark-1.3", "x", input_tokens=100, output_tokens=0)


def test_tracker_tolerates_missing_and_corrupt_log(tmp_path):
    tracker = cost.CostTracker(tmp_path / "cost_log.csv", limit_usd=120)
    assert tracker.total_usd() == 0.0
    (tmp_path / "cost_log.csv").write_text("timestamp_utc,cost_usd\nx,not-a-number\n")
    assert tracker.total_usd() == 0.0
