"""scripts/measure_30s_hevc_perf.py: Performance measurement for T53.

Measures elapsed time for a 30-second 1080p iPhone HEVC video through /api/audits.
Target: < 20 seconds.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app

CLIP_PATH = ROOT / "data" / "bench_1080p_hevc_30s.mp4"


def ensure_benchmark_clip():
    if not CLIP_PATH.exists():
        src = ROOT / "data" / "gate" / "clips" / "meta_clip1.mp4"
        assert src.exists(), f"Source clip not found at {src}"
        print(f"Generating 30s 1080p HEVC clip from {src}...")
        subprocess.run(
            [
                "ffmpeg", "-y", "-stream_loop", "2", "-i", str(src),
                "-vf", "scale=1920:1080",
                "-c:v", "libx265", "-tag:v", "hvc1", "-preset", "fast", "-crf", "24",
                "-t", "30.0",
                str(CLIP_PATH)
            ],
            check=True,
            capture_output=True,
        )


def run_benchmark():
    ensure_benchmark_clip()
    client = TestClient(app)

    print(f"=== T53 30s 1080p iPhone HEVC Performance Benchmark ===")
    print(f"Testing clip: {CLIP_PATH} (1080p, 30.0s, HEVC/H.265)")

    # 1. Color tracking
    print("\n[Run 1] Color Tracking (object_name='orange ball')...")
    t0 = time.perf_counter()
    with open(CLIP_PATH, "rb") as f:
        resp_color = client.post(
            "/api/audits",
            data={
                "t_start": "0.0",
                "t_end": "5.0",
                "camera_static": "true",
                "object_size_m": "0.10",
                "object_name": "orange ball",
                "assumed_model": "free_flight",
            },
            files={"file": ("bench_1080p_hevc_30s.mp4", f, "video/mp4")},
        )
    elapsed_color = time.perf_counter() - t0
    data_color = resp_color.json()
    print(f"   Status: {resp_color.status_code}")
    print(f"   Track Source: {data_color.get('track_source')}")
    print(f"   Verdict: {data_color.get('verdict')}")
    print(f"   Points tracked: {len(data_color.get('points', []))}")
    print(f"   Elapsed Time: {elapsed_color:.2f} seconds")

    # 2. Frame differencing
    print("\n[Run 2] Frame Differencing Tracking (object_name='box')...")
    t0 = time.perf_counter()
    with open(CLIP_PATH, "rb") as f:
        resp_fd = client.post(
            "/api/audits",
            data={
                "t_start": "0.0",
                "t_end": "5.0",
                "camera_static": "true",
                "object_size_m": "0.10",
                "object_name": "box",
                "assumed_model": "free_flight",
            },
            files={"file": ("bench_1080p_hevc_30s.mp4", f, "video/mp4")},
        )
    elapsed_fd = time.perf_counter() - t0
    data_fd = resp_fd.json()
    print(f"   Status: {resp_fd.status_code}")
    print(f"   Track Source: {data_fd.get('track_source')}")
    print(f"   Verdict: {data_fd.get('verdict')}")
    print(f"   Points tracked: {len(data_fd.get('points', []))}")
    print(f"   Elapsed Time: {elapsed_fd:.2f} seconds")

    print("\n=== Summary ===")
    print(f"- 30s 1080p HEVC (Color Tracking): {elapsed_color:.2f} s (Target: < 20 s) -> {'PASS' if elapsed_color <= 20 else 'EXCEEDED'}")
    print(f"- 30s 1080p HEVC (Frame Differencing): {elapsed_fd:.2f} s (Target: < 20 s) -> {'PASS' if elapsed_fd <= 20 else 'EXCEEDED'}")

    return {
        "elapsed_color": elapsed_color,
        "elapsed_fd": elapsed_fd,
        "color_source": data_color.get("track_source"),
        "fd_source": data_fd.get("track_source"),
    }


if __name__ == "__main__":
    run_benchmark()
