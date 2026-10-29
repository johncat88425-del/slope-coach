import json

from scripts.ab_spark_wonder import main, run_ab


def test_mock_run_both_arms_pass(tmp_path):
    out = tmp_path / "rep.json"
    assert main(["--mock", "--out", str(out)]) == 0
    report = json.loads(out.read_text())
    assert report["mock"] is True
    assert report["stopped_early"] is False
    for model, arm in report["arms"].items():
        assert arm["total"] == 2
        assert arm["passed"] == 2
        assert arm["cost_usd"] > 0
    assert (
        report["arms"]["muse-wonder-1.0"]["cost_usd"]
        > report["arms"]["muse-spark-1.3"]["cost_usd"]
    )


def test_budget_stops_before_first_case():
    report = run_ab(
        [{"id": "c1", "kind": "audit", "result": {"verdict": "consistent"}}],
        mock=True,
        budget_usd=0.0,
    )
    assert report["stopped_early"] is True
    assert report["arms"]["muse-spark-1.3"]["total"] == 0


def test_missing_input_file(tmp_path):
    assert main(["--mock", "--input", str(tmp_path / "nope.json")]) == 2


def test_malformed_case_fails_gracefully():
    report = run_ab(
        [{"id": "bad", "kind": "orbit", "result": {}}], mock=True, budget_usd=1.0
    )
    # mock path builds text from the payload regardless of kind; unknown kinds
    # still produce a checked (passing) mock outcome, never a crash
    assert report["arms"]["muse-spark-1.3"]["total"] == 1
