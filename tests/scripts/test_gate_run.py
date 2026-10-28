import shutil
import subprocess

import numpy as np
import pytest

from scripts.gate_run import run_clip

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")

FPS, W, H, BOX = 60, 640, 480, 20
M_PER_PX = 0.003  # box is 20 px == 0.06 m


def write_clip(path, g):
    frames = []
    for i in range(int(0.7 * FPS)):
        t = i / FPS
        x = 40 + (1.0 / M_PER_PX) * t
        y = 300 - (2.0 / M_PER_PX) * t + 0.5 * (g / M_PER_PX) * t * t
        f = np.full((H, W), 255, np.uint8)
        f[int(y):int(y) + BOX, int(x):int(x) + BOX] = 0
        frames.append(f)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                    "-r", str(FPS), "-i", "-", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-qp", "0", str(path)],
                   input=b"".join(f.tobytes() for f in frames), check=True)


def row(clip, static="yes"):
    return {"clip": clip, "source": "synthetic", "assumed_model": "free_flight", "t_start": "0",
            "t_end": "0.6", "camera_static": static, "object": "box", "object_size_m": "0.06"}


def test_gate_flags_wrong_gravity_and_passes_real_one(tmp_path):
    write_clip(tmp_path / "real.mp4", 9.81)
    write_clip(tmp_path / "slow.mp4", 9.81 / 4)
    real = run_clip(row("real.mp4"), tmp_path)
    slow = run_clip(row("slow.mp4"), tmp_path)
    assert real["result"] == "consistent", real
    assert real["g_apparent"] == pytest.approx(9.81, rel=0.15)
    assert slow["result"] == "inconsistent" and slow["time_factor"] == pytest.approx(2.0, rel=0.15)
    assert run_clip(row("real.mp4", static="no"), tmp_path)["result"] == "refused"
