import pytest
from fastapi.testclient import TestClient

from backend.main import app
from scripts.e2e_slope_demo import run_case


def test_e2e_slope_cases():
    client = TestClient(app)
    cases = ["pushed", "wrong_height", "ok", "occluded"]
    results = {c: run_case(client, c) for c in cases}

    assert results["pushed"]["verdict"] == "discrepancy"
    assert "release_check" in results["pushed"]["candidates"]

    assert results["wrong_height"]["verdict"] == "discrepancy"
    assert "dimension_check" in results["wrong_height"]["candidates"]

    assert results["ok"]["verdict"] == "consistent"

    assert results["occluded"]["verdict"] == "discrepancy"
    assert len(results["occluded"]["candidates"]) == 0
    assert any("start of the slide is not visible" in s for s in results["occluded"]["can_still_say"])
