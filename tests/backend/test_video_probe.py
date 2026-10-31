import subprocess

from backend import video


def test_probe_fps_reads_first_line_when_ffprobe_prints_the_stream_twice(monkeypatch):
    # Pexels clips carry a tmcd track; ffprobe 7+ then prints r_frame_rate once per stream group
    out = subprocess.CompletedProcess([], 0, stdout="24000/1001\n24000/1001\n", stderr="")
    monkeypatch.setattr(video.subprocess, "run", lambda *a, **k: out)
    assert abs(video.probe_fps("clip.mp4") - 23.976) < 0.001
