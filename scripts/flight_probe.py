"""Feasibility probe for the flight check: no model, no SAM.

Tracks the largest moving blob with frame differencing against a median background, then runs
physics.experiments.freefall on it. Good enough to tell whether a clip is worth a real run.

    python -m scripts.flight_probe clip.mp4 --start 1.0 --end 2.2 [--m-per-px 0.002]
"""
from __future__ import annotations

import argparse
import json
import subprocess

import numpy as np

from physics.errors import PhysicsInputError
from physics.experiments.freefall import check_flight, fit_flight

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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--m-per-px", type=float, default=None, help=f"user-confirmed scale at {WIDTH}px width")
    ap.add_argument("--thresh", type=float, default=30.0)
    ap.add_argument("--overlay", default=None, help="write a PNG with the tracked points")
    a = ap.parse_args()
    frames, fps = read_frames(a.video, a.start, a.end)
    pts, size_px = track(frames, fps, a.start, a.thresh)
    if a.overlay:
        save_overlay(frames, pts, a.start, fps, a.overlay)
    out = {"fps": fps, "frames": len(frames), "tracked": len(pts)}
    try:
        fit = fit_flight(pts)
        chk = check_flight(fit, m_per_px=a.m_per_px, object_size_px=size_px)
        out |= {"a_px_s2": fit.a_px_s2, "tilt_deg": fit.tilt_deg, "rms_px": fit.rms_residual_px,
                "travel_px": fit.travel_px, **chk.__dict__}
    except PhysicsInputError as e:
        out["refused"] = str(e)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
