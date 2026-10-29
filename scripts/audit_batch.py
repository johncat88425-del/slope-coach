"""Run every labelled clip in a gate manifest through the product endpoint (POST /api/audits) and write
one table of what the website itself says (T98). The website is stricter than the gate: it also refuses
when the object's size changes by more than 30% along the track. Demo and submission text quote this table.

    python -m scripts.audit_batch data/gate/manifest.csv --out data/gate/product_results.md

Clips are read from data/gate/clips/ (the generated clips are in git; john's own clips stay on his Mac and
are copied there by hand, never committed). A clip that is not there is listed as "missing", not skipped.
With MODEL_API_KEY set the backend tracks with SAM 3.1 instead of the model-free trackers.

Only john's labels go in; nothing is tuned per clip.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app

KEYS = ["clip", "source", "verdict", "g_apparent_m_s2", "nearest_body", "size_trend", "track_source", "reason"]


def demo_name(row: dict) -> str:
    """File name the frontend demo uses: real_own_<n> for john's clips, generated_<stem> for the rest."""
    stem = Path(row["clip"]).stem
    if row.get("source") == "own":
        return "real_own_" + stem.split("_")[1]
    return "generated_" + stem


def demo_record(row: dict, audit: dict) -> dict:
    """The full audit as the static demo shows it, without media links (john's clips never leave his Mac)."""
    rec = {k: v for k, v in audit.items() if k not in ("video_url", "overlay_url")}
    rec |= {"video_url": "", "overlay_url": None, "clip": row["clip"],
            "labels_by": "john (window, camera, object size)" if (row.get("object_size_m") or "").strip()
            else "john (window, camera)"}
    if row.get("source") == "own":
        rec["real_clip"] = True
    else:
        rec |= {"generated_clip": True, "source": row.get("source", "")}
    return rec


def audit_row(client: TestClient, row: dict, clips: Path, json_dir: Path | None = None) -> dict:
    out = {"clip": row["clip"], "source": row.get("source", "")}
    if not all((row.get(k) or "").strip() for k in ("source", "t_start", "t_end", "camera_static")):
        return out | {"verdict": "unlabelled"}
    data = {"t_start": row["t_start"], "t_end": row["t_end"], "assumed_model": row["assumed_model"],
            "camera_static": "true" if row["camera_static"].strip().lower() in ("yes", "y", "1", "true") else "false",
            "object_name": row.get("object") or "ball", "slow_motion": "false"}
    if (row.get("object_size_m") or "").strip():
        data["object_size_m"] = row["object_size_m"]
    if not (clips / row["clip"]).is_file():
        return out | {"verdict": "missing", "reason": f"not found in {clips}"}
    with open(clips / row["clip"], "rb") as f:
        r = client.post("/api/audits", data=data, files={"file": (row["clip"], f, "application/octet-stream")})
    if r.status_code != 201:
        return out | {"verdict": "error", "reason": r.text[:120]}
    a = r.json()
    if json_dir is not None:
        json_dir.mkdir(parents=True, exist_ok=True)
        (json_dir / f"{demo_name(row)}.json").write_text(json.dumps(demo_record(row, a), indent=1), encoding="utf-8")
    n = a["numbers"]
    return out | {"verdict": a["verdict"], "g_apparent_m_s2": n.get("g_apparent_m_s2"),
                  "nearest_body": a.get("nearest_body"), "size_trend": n.get("size_trend"),
                  "track_source": a["track_source"], "reason": (a["reasons"] or [""])[0]}


def to_markdown(rows: list[dict]) -> str:
    def fmt(v):
        return "" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v).replace("|", "/"))
    lines = ["| " + " | ".join(KEYS) + " |", "|" + " --- |" * len(KEYS)]
    lines += ["| " + " | ".join(fmt(r.get(k)) for k in KEYS) + " |" for r in rows]
    counts: dict[str, dict[str, int]] = {}
    for r in rows:
        c = counts.setdefault(r["source"] or "other", {})
        c[r["verdict"]] = c.get(r["verdict"], 0) + 1
    lines += ["", "Per source: " + "; ".join(f"{s}: {c}" for s, c in sorted(counts.items())),
              "Every clip in the manifest is listed. Results are relative to the assumed model only."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--clips", default="data/gate/clips")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json-dir", default=None, help="also save each full audit as demo JSON (no media links)")
    ap.add_argument("--explain", action="store_true",
                    help="also ask Muse Spark for explanation and headline text (paid; off by default)")
    a = ap.parse_args()
    if not a.explain:
        os.environ["SLOPE_MODEL_TEXT"] = "0"
    client = TestClient(app)
    with open(a.manifest, newline="", encoding="utf-8") as f:
        rows = [audit_row(client, r, Path(a.clips), Path(a.json_dir) if a.json_dir else None)
                for r in csv.DictReader(f)]
    md = to_markdown(rows)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
