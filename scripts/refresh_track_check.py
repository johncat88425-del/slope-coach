"""scripts/refresh_track_check.py: re-run only the track check on demo JSONs (T224).

Reads each demo record's stored points, runs the current
meta_client.track_check.check_track, and overwrites ONLY the track_check
field. Every other field must come back byte-identical or the script aborts
before writing that file. Total spend guard: SPEND_CAP_USD.

Clip lookup: the record's "clip" name plus data/gate/manifest.csv for the
object prompt; john's own clips come from SLOPE_OWN_CLIPS (or
~/slope-own-clips), gate clips from data/gate/clips.

  python -m scripts.refresh_track_check            # refresh the 10 SAM records
  python -m scripts.refresh_track_check --reverse  # reverse control only
                                                   # (own_2 shifted 120 px,
                                                   # writes nothing)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from meta_client.cost import CostTracker, get_tracker  # noqa: E402
from meta_client.hooks import MetaHooks  # noqa: E402

SPEND_CAP_USD = 0.15
OWN_CLIPS = pathlib.Path(
    os.environ.get("SLOPE_OWN_CLIPS", os.path.expanduser("~/slope-own-clips")))
FILES = ([f"real_own_{n}.json" for n in (1, 2, 3)]
         + [f"generated_meta_clip{n}.json" for n in range(1, 7)]
         + ["generated_manus_clip1.json"])


def manifest_objects() -> dict[str, str]:
    out = {}
    with open(ROOT / "data/gate/manifest.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("object") or "").strip():
                out[row["clip"]] = row["object"].strip()
    return out


def clip_path(clip: str) -> pathlib.Path:
    name = pathlib.Path(clip).name
    if name.startswith("own_"):
        return OWN_CLIPS / name
    return ROOT / "data/gate/clips" / name


def checked_write(path: pathlib.Path, old_text: str, old: dict,
                  result: dict | None) -> None:
    """Write result into track_check after proving nothing else changes."""
    if json.dumps(old, indent=1) != old_text:
        raise SystemExit(f"REFUSING {path.name}: on-disk formatting is not "
                         f"plain indent=1; rewriting would reformat the file.")
    if "track_check" not in old:
        raise SystemExit(f"REFUSING {path.name}: no track_check key to replace.")
    new = dict(old)
    new["track_check"] = result
    if any(new[k] != old[k] for k in old if k != "track_check"):
        raise SystemExit(f"REFUSING {path.name}: a non-track_check field changed.")
    path.write_text(json.dumps(new, indent=1), encoding="utf-8")


def run_check(clip: str, points: list, obj: str) -> dict | None:
    video = clip_path(clip)
    if not video.is_file():
        raise SystemExit(f"missing clip file: {video}")
    return MetaHooks().track_check(video, points, obj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-dir", default=str(ROOT / "data/demo"))
    ap.add_argument("--reverse", action="store_true",
                    help="reverse control only: own_2 shifted 120 px, no writes")
    a = ap.parse_args()
    if not os.environ.get("MODEL_API_KEY"):
        print("MODEL_API_KEY is not set; refusing a live run.")
        return 2
    demo = pathlib.Path(a.demo_dir)
    objects = manifest_objects()
    tracker: CostTracker = get_tracker()
    start = tracker.total_usd()

    def over_cap() -> bool:
        return tracker.total_usd() - start > SPEND_CAP_USD

    if a.reverse:
        path = demo / "real_own_2.json"
        rec = json.loads(path.read_text(encoding="utf-8"))
        shifted = [[p[0], p[1] + 120.0, p[2]] for p in rec["points"]]
        out = run_check(rec["clip"], shifted, objects[rec["clip"]])
        print("reverse control (own_2 +120px):", out)
        print(f"spend: ${tracker.total_usd() - start:.4f}")
        return 0 if out is not None and out["same_object"] is False else 1

    failures = 0
    for name in FILES:
        if over_cap():
            print("SPEND CAP REACHED, stopping.")
            return 1
        path = demo / name
        old_text = path.read_text(encoding="utf-8")
        old = json.loads(old_text)
        out = run_check(old["clip"], old["points"], objects[old["clip"]])
        old_tc = (old.get("track_check") or {}).get("same_object")
        new_tc = (out or {}).get("same_object") if out else None
        print(f"{name}: {old_tc} -> {new_tc} "
              f"({(out or {}).get('note', 'NO CHECK')})")
        # Store the backend shape (backend/audits.py _track_check relabels
        # the model id to "model"); the hook's raw dict would not match API.
        stored = (None if out is None else
                  {"same_object": out["same_object"], "note": out["note"],
                   "source": "model"})
        checked_write(path, old_text, old, stored)
        if out is None:
            failures += 1
    print(f"\nrun spend: ${tracker.total_usd() - start:.4f} / ${SPEND_CAP_USD:.2f}")
    return 1 if failures or over_cap() else 0


if __name__ == "__main__":
    raise SystemExit(main())
