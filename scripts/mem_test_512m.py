"""scripts/mem_test_512m.py: Memory and latency benchmark for 512 MB Render / container constraint (T231).

Tests 3 clips under production demo settings:
1. meta_clip4 (inconsistent g=0.14)
2. meta_clip2 (refusal: size change > 30%)
3. Synthetic toss normal g (consistent g=9.81)

Measures:
- Elapsed seconds
- Server process + ffmpeg child process peak RSS memory (MB)
- Verification against 480 MB warning threshold and 512 MB ceiling.
"""
from __future__ import annotations

import os
import sys
import time
import pathlib
import subprocess
import threading
import urllib.request
import urllib.error
import json

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env without printing any keys
env_path = ROOT / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Enforce T231 environment variables
os.environ["PUBLIC_DEMO"] = "1"
os.environ["SPEND_LIMIT_USD"] = "25"
os.environ["PUBLIC_MAX_UPLOAD_MB"] = "50"
os.environ["PORT"] = "8000"


def get_process_tree_rss_kb(pid: int) -> int:
    """Return total RSS in KB of process and all its children."""
    total_kb = 0
    try:
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)], stderr=subprocess.DEVNULL)
        val = out.decode().strip()
        if val and val.isdigit():
            total_kb += int(val)
    except Exception:
        return 0

    try:
        children_out = subprocess.check_output(["pgrep", "-P", str(pid)], stderr=subprocess.DEVNULL)
        for child_pid in children_out.decode().split():
            if child_pid.isdigit():
                total_kb += get_process_tree_rss_kb(int(child_pid))
    except Exception:
        pass

    return total_kb


class MemorySampler(threading.Thread):
    def __init__(self, pid: int, interval: float = 0.02):
        super().__init__(daemon=True)
        self.pid = pid
        self.interval = interval
        self.running = True
        self.peak_kb = 0
        self.samples: list[int] = []

    def run(self):
        while self.running:
            rss = get_process_tree_rss_kb(self.pid)
            if rss > self.peak_kb:
                self.peak_kb = rss
            self.samples.append(rss)
            time.sleep(self.interval)

    def stop(self) -> int:
        self.running = False
        return self.peak_kb

    def reset_peak(self) -> int:
        cur = get_process_tree_rss_kb(self.pid)
        self.peak_kb = cur
        self.samples.clear()
        return cur


def run_benchmark():
    print("=" * 60)
    print("=== T231: 512 MB Memory & Latency Benchmark ===")
    print("=" * 60)
    print("Environment:")
    print("  PUBLIC_DEMO          = 1")
    print("  SPEND_LIMIT_USD      = 25")
    print("  PUBLIC_MAX_UPLOAD_MB = 50")
    print("  Memory Limit Target  = 512 MB (Alert threshold: 480 MB)")
    print()

    # 1. Start uvicorn server as subprocess
    server_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "warning",
    ]
    server_env = os.environ.copy()
    server_proc = subprocess.Popen(
        server_cmd,
        cwd=str(ROOT),
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for server ready
        ready = False
        for _ in range(50):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/api/spend", timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.2)

        if not ready:
            print("ERROR: Server failed to start on port 8000 within 10s")
            server_proc.terminate()
            return

        sampler = MemorySampler(server_proc.pid, interval=0.015)
        sampler.start()
        time.sleep(0.5)

        baseline_mb = get_process_tree_rss_kb(server_proc.pid) / 1024.0
        print(f"Server ready. Baseline process RSS: {baseline_mb:.2f} MB")
        print()

        # Ensure synthetic clip exists
        clip_synthetic = ROOT / "data" / "tmp_e2e" / "clip_normal_g.mp4"
        if not clip_synthetic.exists():
            from tests.scripts.test_gate_run import write_clip
            clip_synthetic.parent.mkdir(parents=True, exist_ok=True)
            write_clip(clip_synthetic, 9.81)

        test_cases = [
            {
                "name": "meta_clip4 (Basketball drop)",
                "file": ROOT / "data" / "gate" / "clips" / "meta_clip4.mp4",
                "t_start": "0.0",
                "t_end": "2.5",
                "camera_static": "true",
                "object_name": "orange basketball",
                "object_size_m": "0.24",
                "assumed_model": "free_flight",
            },
            {
                "name": "meta_clip2 (Toward camera / Refusal)",
                "file": ROOT / "data" / "gate" / "clips" / "meta_clip2.mp4",
                "t_start": "0.5",
                "t_end": "3.0",
                "camera_static": "true",
                "object_name": "orange basketball",
                "object_size_m": "0.24",
                "assumed_model": "free_flight",
            },
            {
                "name": "synthetic_toss (Normal g=9.81 m/s²)",
                "file": clip_synthetic,
                "t_start": "0.0",
                "t_end": "0.6",
                "camera_static": "true",
                "object_name": "box",
                "object_size_m": "0.06",
                "assumed_model": "free_flight",
            },
        ]

        results = []

        import httpx  # in venv

        for tc in test_cases:
            print(f"--- Running Test: {tc['name']} ---")
            sampler.reset_peak()
            t0 = time.time()

            with open(tc["file"], "rb") as vf:
                resp = httpx.post(
                    "http://127.0.0.1:8000/api/audits",
                    data={
                        "t_start": tc["t_start"],
                        "t_end": tc["t_end"],
                        "camera_static": tc["camera_static"],
                        "object_name": tc["object_name"],
                        "object_size_m": tc["object_size_m"],
                        "assumed_model": tc["assumed_model"],
                    },
                    files={"file": (tc["file"].name, vf.read(), "video/mp4")},
                    timeout=180.0,
                )

            t_elapsed = time.time() - t0
            peak_mb = sampler.peak_kb / 1024.0

            if resp.status_code not in (200, 201):
                print(f"  FAILED: Status {resp.status_code}, {resp.text}")
                verdict = f"HTTP {resp.status_code}"
                reasons = [resp.text[:60]]
            else:
                data = resp.json()
                verdict = data.get("verdict", "unknown")
                reasons = data.get("reasons", [])
                g_val = data.get("numbers", {}).get("g_apparent_m_s2")
                track_source = data.get("track_source", "none")
                print(f"  Result: verdict={verdict}, g={g_val}, track={track_source}")
                print(f"  Elapsed: {t_elapsed:.2f} s")
                print(f"  Peak RSS: {peak_mb:.2f} MB (Margin to 512 MB: {512 - peak_mb:.2f} MB)")
                print(f"  Exceeds 480 MB: {'YES (ALERT)' if peak_mb > 480 else 'NO (SAFE)'}")

            results.append({
                "case": tc["name"],
                "file": tc["file"].name,
                "elapsed_s": t_elapsed,
                "peak_mb": peak_mb,
                "margin_to_512_mb": 512 - peak_mb,
                "verdict": verdict,
                "status": "PASS" if peak_mb <= 480 else "WARN (>480MB)",
            })
            print()

        sampler.stop()

        print("=" * 60)
        print("=== BENCHMARK SUMMARY ===")
        print("=" * 60)
        max_overall_mb = max(r["peak_mb"] for r in results)
        print(f"Overall Peak RSS: {max_overall_mb:.2f} MB / 512 MB (Limit)")
        print(f"Safety Margin to 480 MB alert: {480 - max_overall_mb:.2f} MB")
        print()

        for r in results:
            print(f"- {r['case']}: {r['elapsed_s']:.2f}s, Peak RSS: {r['peak_mb']:.2f} MB [{r['status']}] (Verdict: {r['verdict']})")

        # Save summary json
        summary_path = ROOT / "data" / "e2e" / "T231" / "memory_benchmark.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "baseline_mb": baseline_mb,
                "overall_peak_mb": max_overall_mb,
                "limit_mb": 512,
                "alert_threshold_mb": 480,
                "results": results,
            }, f, indent=2)
        print(f"\nSaved benchmark results to {summary_path}")

    finally:
        server_proc.terminate()
        server_proc.wait()


if __name__ == "__main__":
    run_benchmark()
