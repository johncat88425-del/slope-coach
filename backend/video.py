"""Video frame I/O and two model-free trackers (frame differencing, colour + motion). Used by the audit
endpoint and the gate scripts until SAM tracking is connected. Gaps are never interpolated."""
from __future__ import annotations

import subprocess

import numpy as np
from scipy import ndimage

WIDTH = 480


def probe_fps(path: str) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    # ffprobe 7+ can print the stream twice when the file has a timecode (tmcd) track; use the first line
    num, den = map(int, probe.splitlines()[0].split(",")[0].split("/"))
    return num / den


def read_frames(path: str, start: float, end: float) -> tuple[np.ndarray, float]:
    fps = probe_fps(path)
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


def read_frames_rgb(path: str, start: float, end: float) -> np.ndarray:
    """Same frames as read_frames() but in colour, shape (n, h, WIDTH, 3), values 0..255."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-to", str(end), "-i", path,
         "-vf", f"scale={WIDTH}:-2", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        capture_output=True, check=True).stdout
    probe_h = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-frames:v", "1",
         "-vf", f"scale={WIDTH}:-2", "-f", "image2pipe", "-vcodec", "ppm", "-"],
        capture_output=True, check=True).stdout
    h = int(probe_h.split(b"\n")[1].split()[1])
    return np.frombuffer(raw, np.uint8).reshape(-1, h, WIDTH, 3).astype(np.float32)


# Hue ranges in degrees for objects named by colour in the human label. Added 2026-10-29 (T87) after the
# first real clips showed frame differencing locks onto the arm; see docs/STATUS.md 規則變更紀錄.
COLOR_HUES = {"orange": (15.0, 45.0)}
# Added 2026-10-29 (T128) for clips filmed after the gate; the gate results were not rerun with them.
# A range with lo > hi wraps around 0 degrees (red).
COLOR_HUES |= {"yellow": (45.0, 70.0), "green": (75.0, 160.0), "blue": (190.0, 250.0), "red": (345.0, 15.0)}
MIN_SATURATION = 0.4
MIN_VALUE = 0.4


def color_for(object_name: str) -> str | None:
    words = (object_name or "").lower().split()
    return next((c for c in COLOR_HUES if c in words), None)


def _hsv(rgb: np.ndarray):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, (mx - mn) / (mx + 1e-9), mx / 255.0


def blob_diameter(ys: np.ndarray, xs: np.ndarray) -> float:
    """Diameter of a round object from its pixel blob: the blob's width across its minor axis.
    Motion blur stretches the blob along the motion only, so the minor axis keeps the true size."""
    if len(xs) < 3:
        return float(2 * np.sqrt(len(xs) / np.pi))
    pts = np.vstack([xs, ys]).astype(float)
    _, vecs = np.linalg.eigh(np.cov(pts))
    across = vecs[:, 0] @ pts
    return float(across.max() - across.min() + 1)


def track_color(rgb_frames: np.ndarray, fps: float, start: float, color: str, thresh: float = 30.0,
                min_px: int = 15, widths: list | None = None):
    """Pixels that have the object's colour AND differ from the median background; the largest connected
    blob per frame is the object. Static things of the same colour (furniture, floor) drop out because
    they do not move; a moving arm drops out because it is not that colour. Returns points and per-frame
    diameters (px). With widths, also appends each tracked blob's box width (px), for the vehicle check."""
    lo, hi = COLOR_HUES[color]
    bg = np.median(rgb_frames, axis=0)
    pts, sizes = [], []
    for i, f in enumerate(rgb_frames):
        mask = np.abs(f - bg).max(-1) > thresh  # moving pixels first; colour is only tested on those (T145)
        h, s, v = _hsv(f[mask])
        in_hue = (h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)
        mask[mask] = in_hue & (s >= MIN_SATURATION) & (v >= MIN_VALUE)
        lab, n = ndimage.label(mask)
        if n == 0:
            continue
        area = ndimage.sum(mask, lab, range(1, n + 1))
        k = int(np.argmax(area))
        if area[k] < min_px:
            continue  # gap, never interpolated
        ys, xs = np.nonzero(lab == k + 1)
        pts.append((start + i / fps, float(xs.mean()), float(ys.mean())))
        sizes.append(blob_diameter(ys, xs))
        if widths is not None:
            widths.append(float(xs.max() - xs.min() + 1))
    return pts, sizes


def track(frames: np.ndarray, fps: float, start: float, thresh: float = 30.0, min_px: int = 20):
    pts, sizes = track_with_sizes(frames, fps, start, thresh, min_px)
    return pts, (float(np.median(sizes)) if sizes else None)


def track_with_sizes(frames: np.ndarray, fps: float, start: float, thresh: float = 30.0, min_px: int = 20,
                     widths: list | None = None):
    """Same tracker as track(), also returning the per-frame object size (sqrt of mask area, px). With widths,
    also appends each frame's moving-pixel box width (px), for the vehicle check."""
    bg = np.median(frames, axis=0)
    pts, sizes = [], []
    for i, f in enumerate(frames):
        mask = np.abs(f - bg) > thresh
        if mask.sum() < min_px:
            continue  # gap, never interpolated
        ys, xs = np.nonzero(mask)
        pts.append((start + i / fps, float(xs.mean()), float(ys.mean())))
        sizes.append(float(np.sqrt(mask.sum())))
        if widths is not None:
            widths.append(float(xs.max() - xs.min() + 1))
    return pts, sizes


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
