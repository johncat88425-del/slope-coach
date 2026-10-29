"""scripts/e2e_audit.py: End-to-end test and screenshot generator for the Audit flow (T42).

Generates synthetic video clips for:
1. Normal gravity (g = 9.81 m/s^2) -> Expected verdict: consistent
2. Low gravity (g = 9.81 / 4 m/s^2) -> Expected verdict: inconsistent

Submits both clips to POST /api/audits, verifies the verdicts and numbers,
and saves the overlay images and a comprehensive Markdown report with visuals to docs/screenshots/.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

# Ensure project root is in sys.path
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from tests.scripts.test_gate_run import write_clip

SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
TEMP_DIR = ROOT / "data" / "tmp_e2e"


def main():
    print("=== T42 Audit Flow End-to-End Test ===")
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    client = TestClient(app)

    # 1. Generate synthetic clips
    clip_normal = TEMP_DIR / "clip_normal_g.mp4"
    clip_slow = TEMP_DIR / "clip_slow_g4.mp4"

    print("1. Generating synthetic clips via ffmpeg...")
    write_clip(clip_normal, 9.81)
    print(f"   Created {clip_normal} (g = 9.81 m/s^2)")
    write_clip(clip_slow, 9.81 / 4.0)
    print(f"   Created {clip_slow} (g = 2.45 m/s^2)")

    # 2. Test Case A: Normal gravity (g = 9.81)
    print("\n2. Executing Audit Case A: Normal Gravity...")
    with open(clip_normal, "rb") as f:
        resp_a = client.post(
            "/api/audits",
            data={
                "t_start": "0.0",
                "t_end": "0.6",
                "camera_static": "true",
                "object_size_m": "0.06",
                "object_name": "box",
                "assumed_model": "free_flight",
            },
            files={"file": ("clip_normal_g.mp4", f, "video/mp4")},
        )
    assert resp_a.status_code == 201, f"Failed Case A: {resp_a.text}"
    res_a = resp_a.json()
    print(f"   Audit ID: {res_a['audit_id']}")
    print(f"   Verdict: {res_a['verdict']}")
    print(f"   Apparent g: {res_a['numbers'].get('g_apparent_m_s2')} m/s^2")
    print(f"   Nearest Body: {res_a.get('nearest_body')}")
    assert res_a["verdict"] == "consistent", f"Expected consistent, got {res_a['verdict']}"

    # Save Case A Overlay
    overlay_res_a = client.get(res_a["overlay_url"])
    overlay_path_a = SCREENSHOT_DIR / "audit_case_normal_g_overlay.png"
    overlay_path_a.write_bytes(overlay_res_a.content)
    print(f"   Saved overlay to {overlay_path_a}")

    # 3. Test Case B: Slow gravity (g/4)
    print("\n3. Executing Audit Case B: Slow Gravity (g/4)...")
    with open(clip_slow, "rb") as f:
        resp_b = client.post(
            "/api/audits",
            data={
                "t_start": "0.0",
                "t_end": "0.6",
                "camera_static": "true",
                "object_size_m": "0.06",
                "object_name": "box",
                "assumed_model": "free_flight",
            },
            files={"file": ("clip_slow_g4.mp4", f, "video/mp4")},
        )
    assert resp_b.status_code == 201, f"Failed Case B: {resp_b.text}"
    res_b = resp_b.json()
    print(f"   Audit ID: {res_b['audit_id']}")
    print(f"   Verdict: {res_b['verdict']}")
    print(f"   Apparent g: {res_b['numbers'].get('g_apparent_m_s2')} m/s^2")
    print(f"   Nearest Body: {res_b.get('nearest_body')}")
    print(f"   Reasons: {res_b.get('reasons')}")
    assert res_b["verdict"] == "inconsistent", f"Expected inconsistent, got {res_b['verdict']}"

    # Save Case B Overlay
    overlay_res_b = client.get(res_b["overlay_url"])
    overlay_path_b = SCREENSHOT_DIR / "audit_case_slow_g4_overlay.png"
    overlay_path_b.write_bytes(overlay_res_b.content)
    print(f"   Saved overlay to {overlay_path_b}")

    # 4. Generate visual markdown report in screenshots directory
    report_md = SCREENSHOT_DIR / "audit_e2e_report.md"
    report_content = f"""# E2E Audit Flow Verification Report (T42)

Generated automatically by `scripts/e2e_audit.py`.

## Summary
- **Case 1 (Normal Gravity g = 9.81 m/s²)**:
  - **Verdict**: `{res_a['verdict']}`
  - **Apparent Gravity**: `{res_a['numbers'].get('g_apparent_m_s2'):.2f} m/s²` (g_vs_earth: `{res_a['numbers'].get('g_vs_earth'):.2f}`)
  - **Matched Celestial Body**: `{res_a.get('nearest_body')}`
  - **Overlay Image**: ![Normal g Overlay](audit_case_normal_g_overlay.png)

## Case 2 (Slow Gravity g/4 = 2.45 m/s²)**:
  - **Verdict**: `{res_b['verdict']}`
  - **Apparent Gravity**: `{res_b['numbers'].get('g_apparent_m_s2'):.2f} m/s²` (g_vs_earth: `{res_b['numbers'].get('g_vs_earth'):.2f}`)
  - **Matched Celestial Body**: `{res_b.get('nearest_body')}`
  - **Reasons**: `{', '.join(res_b.get('reasons', []))}`
  - **Overlay Image**: ![Slow g/4 Overlay](audit_case_slow_g4_overlay.png)

Both test cases successfully verified the end-to-end audit API pipeline.
"""
    report_md.write_text(report_content, encoding="utf-8")
    print(f"\n4. Saved E2E audit report to {report_md}")

    # Clean up temp clips
    try:
        clip_normal.unlink()
        clip_slow.unlink()
    except Exception:
        pass

    print("\n=== All T42 E2E Checks Passed Successfully! ===")


if __name__ == "__main__":
    main()
