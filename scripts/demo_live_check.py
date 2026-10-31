"""scripts/demo_live_check.py: freeze-time live check of the reviewer flow (T189).

Runs four demo cases through the full paid path against the real Meta API:
Spark interview + suggestion -> SAM track -> audit -> Spark explanation ->
headline. Prints each step's result, spend, and whether the model-source
labels ("model" / "muse-spark-1.3" / sam) are present. Stops early if this
run's own spend passes SPEND_CAP_USD.

Uses TestClient (same ASGI app, no port needed). Needs MODEL_API_KEY in the
environment. Clips stay outside the repo: gate clips from data/gate/clips,
own + car clips from ~/slope-own-clips (or SLOPE_OWN_CLIPS).
"""
from __future__ import annotations

import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

SPEND_CAP_USD = 0.50
OWN_CLIPS = pathlib.Path(
    os.environ.get("SLOPE_OWN_CLIPS", os.path.expanduser("~/slope-own-clips")))

CASES = [
    {"name": "own consistent", "clip": OWN_CLIPS / "own_2_IMG_8429.mov",
     "t_start": 0.2, "t_end": 0.8, "object_size_m": 0.11,
     "object_name": "orange ball", "expect": "consistent"},
    {"name": "meta_clip4 inconsistent",
     "clip": ROOT / "data/gate/clips/meta_clip4.mp4",
     "t_start": 0.0, "t_end": 2.5, "object_size_m": 0.24,
     "object_name": "orange basketball", "expect": "inconsistent"},
    {"name": "meta_clip2 toward-camera refusal",
     "clip": ROOT / "data/gate/clips/meta_clip2.mp4",
     "t_start": 0.5, "t_end": 3.0, "object_size_m": 0.24,
     "object_name": "orange basketball", "expect": "insufficient_data"},
    {"name": "T184 best car (side, refused at 0.47s gate)",
     "clip": OWN_CLIPS / "car_side_1_clean.mp4",
     "t_start": 1.0, "t_end": 1.5, "object_size_m": None,
     "object_name": "car", "assumed_model": "vehicle",
     "expect": "insufficient_data"},
]


def main() -> int:
    if not os.environ.get("MODEL_API_KEY"):
        print("MODEL_API_KEY is not set; refusing a live run.")
        return 2
    missing = [c["name"] for c in CASES if not c["clip"].is_file()]
    if missing:
        print("missing clips:", ", ".join(missing))
        return 2
    client = TestClient(app)
    start = client.get("/api/spend").json()["spent_usd"]
    print(f"spend at start: ${start:.4f} (this run stops past ${SPEND_CAP_USD:.2f})")
    failures = 0
    for case in CASES:
        if client.get("/api/spend").json()["spent_usd"] - start > SPEND_CAP_USD:
            print("SPEND CAP REACHED, stopping.")
            failures += 1
            break
        failures += run_case(client, case)
    delta = client.get("/api/spend").json()["spent_usd"] - start
    print(f"\nrun spend: ${delta:.4f} / ${SPEND_CAP_USD:.2f} cap")
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


def run_case(client: TestClient, case: dict) -> int:
    print(f"\n=== {case['name']} (expect {case['expect']}) ===")
    t0 = time.time()
    s0 = client.get("/api/spend").json()["spent_usd"]
    with open(case["clip"], "rb") as f:
        draft = client.post("/api/audit-drafts",
                            files={"file": (case["clip"].name, f, "video/mp4")})
    if draft.status_code != 201:
        print(f"draft FAILED: {draft.status_code} {draft.text[:200]}")
        return 1
    body = draft.json()
    iv, sug = body["interview"], body.get("suggestion") or {}
    print(f"interview.source={iv['source']} "
          f"questions={[q['field'] for q in iv['questions']]}")
    print(f"suggestion by {sug.get('source')}: {sug.get('object_name')}")
    form: dict[str, str] = {
        "draft_id": body["draft_id"], "t_start": str(case["t_start"]),
        "t_end": str(case["t_end"]), "camera_static": "true",
        "object_name": case["object_name"],
        "assumed_model": case.get("assumed_model", "free_flight"),
    }
    if case["object_size_m"] is not None:
        form["object_size_m"] = str(case["object_size_m"])
    audit = client.post("/api/audits", data=form)
    if audit.status_code not in (200, 201):
        print(f"audit FAILED: {audit.status_code} {audit.text[:200]}")
        return 1
    a = audit.json()
    n = a["numbers"]
    key_numbers = {k: round(n[k], 3) for k in
                   ("g_apparent_m_s2", "speed_km_h", "accel_g") if k in n}
    print(f"verdict={a['verdict']} track_source={a['track_source']} "
          f"numbers={key_numbers}")
    print(f"reasons={a['reasons']}")
    exp, head = a.get("explanation") or {}, a.get("headline")
    print(f"explanation.source={exp.get('source')} "
          f"headline={head['source'] if head else None}")
    ok = (a["verdict"] == case["expect"] and a["track_source"] == "sam"
          and iv["source"] == "model" and exp.get("source") == "model")
    print(f"case {'PASS' if ok else 'FAIL'} "
          f"({time.time() - t0:.0f}s, "
          f"${client.get('/api/spend').json()['spent_usd'] - s0:.4f})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
