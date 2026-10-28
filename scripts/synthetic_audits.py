"""Real /api/audits results on synthetic clips, for building and testing the audit screens before
john's footage exists (T73). Every clip is drawn by this script from a known motion, so the files
are labelled "synthetic" and must never be presented as a real or generated video in a demo.

    python -m scripts.synthetic_audits --out data/demo
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from backend.main import app

FPS, W, H, BOX = 60, 640, 480, 20
M_PER_PX = 0.003  # a 20 px box is then 0.06 m


def render(path: Path, positions: list[tuple[float, float]]) -> None:
    frames = []
    for x, y in positions:
        f = np.full((H, W), 255, np.uint8)
        f[int(y):int(y) + BOX, int(x):int(x) + BOX] = 0
        frames.append(f.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                    "-r", str(FPS), "-i", "-", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-qp", "0", str(path)],
                   input=b"".join(frames), check=True)


def toss(g: float, seconds: float = 0.7):
    return [(40 + t / M_PER_PX, 300 - 2.0 / M_PER_PX * t + 0.5 * g / M_PER_PX * t * t)
            for t in (i / FPS for i in range(int(seconds * FPS)))]


def bounce(gain: float):
    """Drop from rest; each rebound reaches `gain` times the previous height."""
    floor, h, out, y, v = 440.0, 300.0, [], 140.0, 0.0
    a = 9.81 / M_PER_PX
    for i in range(int(2.4 * FPS)):
        v += a / FPS
        y += v / FPS
        if y >= floor:
            y, h = floor, h * gain
            v = -math.sqrt(2 * a * h)
        out.append((60 + 2 * i, y))
    return out


def pendulum(length_m: float):
    w = math.sqrt(9.81 / length_m)
    return [(300 + 120 * math.sin(w * i / FPS), 200 + 15 * (1 - math.cos(w * i / FPS)))
            for i in range(int(3.5 * FPS))]


CASES = [
    ("toss_normal_g", toss(9.81), {"t_end": "0.6", "object_size_m": "0.06"}),
    ("toss_quarter_g", toss(9.81 / 4), {"t_end": "0.6", "object_size_m": "0.06"}),
    ("toss_moving_camera", toss(9.81), {"t_end": "0.6", "object_size_m": "0.06", "camera_static": "false"}),
    ("bounce_losing_height", bounce(0.6), {"t_end": "2.3", "assumed_model": "bounce"}),
    ("bounce_gaining_height", bounce(1.4), {"t_end": "2.3", "assumed_model": "bounce"}),
    ("pendulum_25cm", pendulum(0.25), {"t_end": "3.4", "assumed_model": "pendulum", "length_m": "0.25"}),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/demo")
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    summary = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, pos, form in CASES:
            clip = Path(tmp) / f"{name}.mp4"
            render(clip, pos)
            data = {"t_start": "0", "camera_static": "true", **form}
            with clip.open("rb") as f:
                r = client.post("/api/audits", data=data, files={"file": (clip.name, f, "video/mp4")})
            r.raise_for_status()
            rec = r.json() | {"synthetic": True, "synthetic_case": name}
            (out / f"synthetic_{name}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
            summary.append(f"{name}: {rec['verdict']} {rec['reasons'][:1]}")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
