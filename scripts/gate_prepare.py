"""Help john label gate clips (T79): for every video in a folder, print its frame rate, length and
size, write a contact sheet (one thumbnail every 0.1 s, each stamped with its time) so the time
window can be read off by eye, and add a manifest row with the labels left blank.

    python -m scripts.gate_prepare /mnt/project-files/gate --sheets data/gate/sheets --manifest data/gate/manifest.csv

Labels are human-only (STATUS, 可行性關卡): this script never fills t_start, t_end, camera_static
or object_size_m, and never calls a model.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

from scripts.gate_run import COLUMNS

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".avi"}


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return {"fps": round(num / den, 2), "duration_s": round(float(j["format"]["duration"]), 2),
            "size": f"{s['width']}x{s['height']}"}


def contact_sheet(path: Path, out: Path, step_s: float = 0.1, cols: int = 10, max_tiles: int = 100) -> float:
    """Thumbnails every step_s seconds (wider for long clips, at most max_tiles) with the timestamp
    burnt in, tiled cols across. Returns the spacing used."""
    dur = probe(path)["duration_s"]
    step_s = max(step_s, round(dur / max_tiles, 2))
    rows = max(1, int(dur / step_s / cols) + 1)
    vf = (f"fps={1 / step_s},scale=192:-2,"
          "drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=14:fontcolor=yellow:box=1:boxcolor=black@0.6,"
          f"tile={cols}x{rows}")
    res = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", vf, "-frames:v", "1", str(out)],
                         capture_output=True)
    if res.returncode != 0:
        vf_fallback = f"fps={1 / step_s},scale=192:-2,tile={cols}x{rows}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", vf_fallback, "-frames:v", "1", str(out)],
                       check=True)
    return step_s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--sheets", default="data/gate/sheets")
    ap.add_argument("--manifest", default="data/gate/manifest.csv")
    a = ap.parse_args()
    sheets, manifest = Path(a.sheets), Path(a.manifest)
    sheets.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(manifest.open(encoding="utf-8"))) if manifest.exists() else []
    known = {r["clip"] for r in rows}
    for clip in sorted(p for p in Path(a.folder).iterdir() if p.suffix.lower() in VIDEO_EXT):
        info = probe(clip)
        step = contact_sheet(clip, sheets / f"{clip.stem}_sheet.png")
        flag = "  <- slow-motion frame rate, check the clip plays in real time" if info["fps"] > 90 else ""
        print(f"{clip.name}: {info['fps']} fps, {info['duration_s']} s, {info['size']}, sheet every {step} s{flag}")
        if clip.name not in known:
            rows.append({k: "" for k in COLUMNS} | {"clip": clip.name, "assumed_model": "free_flight"})
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLUMNS})
    print(f"manifest: {manifest} ({len(rows)} rows; fill the blank labels by hand)")


if __name__ == "__main__":
    main()
