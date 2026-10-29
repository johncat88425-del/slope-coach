"""scripts/e2e_slope_demo.py: End-to-end verification of the Slope Coach workflow (T14).

Runs all 4 synthetic test cases through the slope backend API:
1. pushed: slider given an initial push -> verdict: discrepancy, candidate: release_check
2. wrong_height: slope height entered incorrectly -> verdict: discrepancy, candidate: dimension_check
3. ok: normal slider run -> verdict: consistent
4. occluded: release obscured by hand -> verdict: discrepancy, evidence: empty, can_still_say notes key segment missing

Generates a summary report in docs/screenshots/slope_seed_demo_report.md.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from physics.calibration import SlopeGeometry
from physics.experiments import slope

SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
TRUE_MU = 0.15
CAL = dict(
    ruler_px=[[0, 0], [1000, 0]],
    ruler_length_m=1.0,
    path_start_px=[100, 500],
    path_end_px=[1100, 500],
    slope_length_m=1.0,
    slope_height_m=0.3,
    reason="synthetic demo",
)


def _dets(a, v0=0.0, t0=0.5, s0=0.05, hide_start=False):
    out = []
    for i in range(75):
        t = i / 30
        tt = max(t - t0, 0)
        s = s0 + v0 * tt + 0.5 * a * tt * tt
        if s > 0.95:
            break
        hidden = hide_start and t >= t0 and s < 0.3
        out.append({
            "t_s": t,
            "centroid_px": None if hidden else [100 + s * 1000, 500],
            "area_px": 400,
            "source": "manual",
        })
    return out


def run_case(client: TestClient, case_name: str) -> dict:
    exp = client.post("/api/experiments", json={"title": f"Synthetic demo: {case_name}"}).json()
    eid = exp["experiment_id"]
    client.post(f"/api/experiments/{eid}/calibrations", json=CAL)
    a = slope.acceleration(SlopeGeometry(1.0, 0.3), TRUE_MU)

    def trial(kind, dets):
        t = client.post(f"/api/experiments/{eid}/trials", data={"kind": kind, "calibration_version": 1}).json()
        tid = t["trial_id"]
        client.put(f"/api/trials/{tid}/detections", json={"detections": dets})
        client.put(f"/api/trials/{tid}/release-time", json={"t0_s": 0.5})
        return tid

    bids = [trial("baseline", _dets(a * k)) for k in (0.98, 1.0, 1.02)]
    client.post(f"/api/experiments/{eid}/baselines", json={"trial_ids": bids, "calibration_version": 1})
    pred = client.post(
        f"/api/experiments/{eid}/predictions",
        json={"calibration_version": 1, "baseline_version": 1, "distance_m": 0.8},
    ).json()

    if case_name == "wrong_height":
        test = _dets(slope.acceleration(SlopeGeometry(1.0, 0.4), TRUE_MU))
    else:
        test = _dets(a, v0=0.6 if case_name in ("pushed", "occluded") else 0.0, hide_start=case_name == "occluded")

    tid = trial("test", test)
    cmp = client.post(
        f"/api/experiments/{eid}/comparisons",
        json={"prediction_id": pred["prediction_id"], "trial_id": tid},
    ).json()

    candidates = [e["candidate"] for e in cmp.get("evidence", [])]
    return {
        "case": case_name,
        "experiment_id": eid,
        "verdict": cmp["verdict"],
        "candidates": candidates,
        "can_still_say": cmp.get("can_still_say", []),
        "comparison": cmp,
    }


def main():
    print("=== T14 Slope Coach End-to-End Demo Run ===")
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)

    results = []
    cases = ["pushed", "wrong_height", "ok", "occluded"]
    for c in cases:
        r = run_case(client, c)
        print(f"[{c.upper()}] verdict: {r['verdict']}, candidates: {r['candidates']}, can_still_say: {r['can_still_say']}")
        results.append(r)

    # Verify expected outcomes
    assert results[0]["verdict"] == "discrepancy" and "release_check" in results[0]["candidates"]
    assert results[1]["verdict"] == "discrepancy" and "dimension_check" in results[1]["candidates"]
    assert results[2]["verdict"] == "consistent"
    assert results[3]["verdict"] == "discrepancy" and len(results[3]["candidates"]) == 0
    assert any("start of the slide is not visible" in s for s in results[3]["can_still_say"])

    # Write report
    report_file = SCREENSHOT_DIR / "slope_seed_demo_report.md"
    content = f"""# Slope Coach E2E Synthetic Demo Verification (T14)

Automated E2E run of the 4 primary slope inquiry scenarios:

| Case | Scenario | Expected Verdict | Actual Verdict | Candidates | Remarks |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **pushed** | Accidental hand push during release ($v_0 > 0$) | discrepancy | `{results[0]['verdict']}` | `{results[0]['candidates']}` | Recommends barrier release intervention |
| **wrong_height** | Incline measured inaccurately ($h_{{real}} > h_{{typed}}$) | discrepancy | `{results[1]['verdict']}` | `{results[1]['candidates']}` | Recommends dimension re-measurement |
| **ok** | Clean release matching theoretical parameters | consistent | `{results[2]['verdict']}` | `{results[2]['candidates']}` | Close alignment with theoretical model |
| **occluded** | Critical release frames obscured by hand | discrepancy | `{results[3]['verdict']}` | None (refused to guess $v_0$) | `{results[3]['can_still_say'][0]}` |

All 4 scenario cases completed successfully with exact scientific guardrails.
"""
    report_file.write_text(content, encoding="utf-8")
    print(f"\nSaved slope demo E2E report to {report_file}")
    print("=== All T14 Slope Coach E2E Checks Passed! ===")


if __name__ == "__main__":
    main()
