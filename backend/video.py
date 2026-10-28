"""Video frame I/O and a model-free tracker (frame differencing). Used by the audit endpoint and the
gate scripts until SAM tracking is connected. Gaps are never interpolated."""
from __future__ import annotations

import subprocess

import numpy as np

WIDTH = 480


def read_frames(path: str, start: float, end: float) -> tuple[np.ndarray, float]:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    num, den = map(int, probe.split(",")[0].split("/"))
    fps = num / den
    # ffmpeg applies the rotation tag, so frames come out the way the clip plays
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-to", str(end), "-i", path,
         "-vf", f"scale={WIDTH}:-2,format=gray", "-f", "rawvideo", "-"],
        capture_output=True, check=True).stdout
    probe_h = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-frames:v", "1",
         "-vf", f"scale={WIDTH}:-2", "-f", "image2pipe", "-vcodec", "ppm", "-"],
        capture_output=True, check=True).stdout
    h = int(probe_h.split(b"\n")[1].split()[1])
    frames = np.frombuffer(raw, np.uint8).reshape(-1, h, WIDTH).astype(np.float32)
    return frames, fps


def track(frames: np.ndarray, fps: float, start: float, thresh: float = 30.0, min_px: int = 20):
    bg = np.median(frames, axis=0)
    pts, sizes = [], []
    for i, f in enumerate(frames):
        mask = np.abs(f - bg) > thresh
        if mask.sum() < min_px:
            continue  # gap, never interpolated
        ys, xs = np.nonzero(mask)
        pts.append((start + i / fps, float(xs.mean()), float(ys.mean())))
        sizes.append(float(np.sqrt(mask.sum())))
    return pts, (float(np.median(sizes)) if sizes else None)


def save_overlay(frames: np.ndarray, pts, start: float, fps: float, path: str) -> None:
    """Darkest-pixel composite of the window with tracked points as red dots, for a human to confirm
    that the track sits on the object."""
    comp = frames.min(axis=0).astype(np.uint8)
    rgb = np.stack([comp] * 3, axis=-1)
    h, w = comp.shape
    for t, x, y in pts:
        xi, yi = int(round(x)), int(round(y))
        rgb[max(yi - 2, 0):min(yi + 3, h), max(xi - 2, 0):min(xi + 3, w)] = (255, 0, 0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                    "-i", "-", path], input=rgb.tobytes(), check=True)
