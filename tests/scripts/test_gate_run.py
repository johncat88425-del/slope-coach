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
    real = run_clip(row("real.mp4"), tmp_path, tmp_path / "ov")
    assert (tmp_path / "ov" / "real_track.png").stat().st_size > 0
    slow = run_clip(row("slow.mp4"), tmp_path)
    assert real["result"] == "consistent", real
    assert real["g_apparent"] == pytest.approx(9.81, rel=0.15)
    assert slow["result"] == "inconsistent" and slow["time_factor"] == pytest.approx(2.0, rel=0.15)
    assert run_clip(row("real.mp4", static="no"), tmp_path)["result"] == "refused"


def _r(clip, source, result, track_ok="", g=None, tilt=0.0, rms=0.0, frac=1.0):
    return {"clip": clip, "source": source, "result": result, "track_ok": track_ok, "g_apparent": g,
            "tilt_deg": tilt, "rms_over_travel": rms, "tracked_fraction": frac}


def test_gate_summary_waits_for_overlay_checks_then_passes():
    from scripts.gate_run import gate_summary, summary_markdown
    rows = [_r("a", "own", "consistent", g=9.7), _r("b", "own", "consistent", g=10.1),
            _r("c", "own", "refused"), _r("d", "generated", "inconsistent", g=3.0)]
    s = gate_summary(rows)
    assert (s["q1"], s["q2"], s["q3"]) == ("pending", "pending", "pass")
    for r in rows:
        r["track_ok"] = "yes"
    s = gate_summary(rows)
    assert (s["q1"], s["q2"]) == ("pass", "pass")
    assert s["counts"]["own"]["refused"] == 1 and "d" in summary_markdown(s)


def test_gate_summary_rejects_weak_anomaly_and_too_many_refusals():
    from scripts.gate_run import gate_summary
    # g off by 30% would vanish with a 30% size error, so it is not a clear anomaly
    rows = [_r("x", "generated", "inconsistent", track_ok="yes", g=12.8),
            _r("y", "generated", "refused"), _r("z", "generated", "refused")]
    s = gate_summary(rows)
    assert s["q2"] == "fail" and s["q3"] == "fail" and s["q1"] == "pending"


def test_unlabelled_rows_are_not_counted(tmp_path):
    from scripts.gate_run import gate_summary
    blank = {"clip": "x.mp4", "source": "", "assumed_model": "free_flight", "t_start": "", "t_end": "",
             "camera_static": "", "object": "", "object_size_m": ""}
    r = run_clip(blank, tmp_path)
    assert r["result"] == "unlabelled"
    s = gate_summary([r, _r("a", "own", "consistent", g=9.8)])
    assert s["unlabelled"] == ["x.mp4"] and s["total"] == 1 and s["refused"] == 0


def write_orange_clip(path, g):
    """Orange 20 px ball thrown in front of a static orange block, with a grey 'arm' moving across."""
    yy, xx = np.mgrid[:H, :W]
    frames = []
    for i in range(int(0.7 * FPS)):
        t = i / FPS
        x = 40 + (1.0 / M_PER_PX) * t
        y = 300 - (2.0 / M_PER_PX) * t + 0.5 * (g / M_PER_PX) * t * t
        f = np.full((H, W, 3), 230, np.uint8)
        f[400:470, 500:620] = (240, 140, 40)
        f[50:250, 300 + 5 * i:360 + 5 * i] = (90, 90, 90)
        f[(xx - x) ** 2 + (yy - y) ** 2 <= 100] = (240, 140, 40)
        frames.append(f)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                    "-r", str(FPS), "-i", "-", "-pix_fmt", "yuv444p", "-c:v", "libx264", "-qp", "0", str(path)],
                   input=b"".join(f.tobytes() for f in frames), check=True)


def test_colour_label_switches_tracker_and_old_rule_is_reproducible(tmp_path):
    write_orange_clip(tmp_path / "ball.mp4", 9.81)
    r = row("ball.mp4") | {"object": "orange ball"}
    new = run_clip(r, tmp_path, tmp_path / "ov")
    assert new["tracker"] == "color:orange"
    assert new["result"] == "consistent", new
    old = run_clip(r, tmp_path, tracker="frame_diff")
    assert old["tracker"] == "frame_diff"
    assert old["result"] != "consistent", old
