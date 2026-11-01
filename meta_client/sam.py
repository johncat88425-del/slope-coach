"""SAM 3.1 video tracking (Responses API, non-streaming).

Pipeline for track(video_path, text_prompt):
  1. ffprobe the clip, transcode a 15 fps + faststart copy with ffmpeg.
  2. Upload the copy once (Files API, purpose=user_data).
  3. One responses.create(model="sam-3.1") with a concept prompt and the
     file_id; masks requested in the compact one_bit encoding.
  4. Parse the "<Nf>id<|box|><|mask|>" wire format with the official
     meta-sam-parser package and decode each mask to centroid + area.

Wire format reference: https://dev.meta.ai/docs/sam/reading-segmentation
(billing: $0.20 per 1,000 frames, minimum 50 frames per request).

Frame N of the transcoded clip maps to t = N / 15 s. Masks decode at their
own HxW raster size and are scaled to source pixels; the scale step is marked
clearly so it can be re-checked against real footage (T04).
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from . import client as _client
from .client import SAM_MODEL, call_with_retry, get_client
from .cost import CostTracker, get_tracker, sam_video_cost_usd
from .exceptions import MediaError, TrackingError

TARGET_FPS = 15.0
MASK_ENCODING = "one_bit"
_FFMPEG_TIMEOUT_S = 300.0
# Hard per-request cap (T181): 15 fps x 60 s. Longer clips must be windowed
# first — one uncapped request could otherwise bill tens of dollars.
MAX_SAM_FRAMES = 900


@dataclass(frozen=True)
class FrameDetection:
    frame: int
    t_s: float
    object_id: int
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in source pixels
    frame_size: tuple[int, int]  # (w, h) of the source frame
    centroid_px: tuple[float, float] | None  # None when the mask is empty
    area_px: float
    mask: bytes = b""  # row-major 0/1 raster, mask_size (w*h) entries
    mask_size: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class TrackResult:
    detections: list[FrameDetection] = field(default_factory=list)
    fps: float = TARGET_FPS
    n_frames: int = 0
    billed_frames: int = 0
    cost_usd: float = 0.0
    source: str = SAM_MODEL

    def object_ids(self) -> list[int]:
        return sorted({d.object_id for d in self.detections})


def select_main_track(detections: list[FrameDetection]) -> int | None:
    """Pick the object id with the most frames (ties: largest total area).

    The slope rig has a single slider; when the concept prompt matches extra
    objects, the longest-lived track is the slider. Returns None when there
    are no detections at all.
    """
    if not detections:
        return None
    counts: dict[int, list[int]] = {}
    areas: dict[int, float] = {}
    for d in detections:
        counts.setdefault(d.object_id, []).append(d.frame)
        areas[d.object_id] = areas.get(d.object_id, 0.0) + d.area_px
    return max(counts, key=lambda oid: (len(counts[oid]), areas[oid]))


def _run_cmd(cmd: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:
        raise MediaError(
            f"{cmd[0]} not found; install ffmpeg (T02) to enable tracking."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaError(f"{cmd[0]} timed out after {timeout:g}s") from exc


def _probe_clip(path: Path) -> dict[str, Any]:
    proc = _run_cmd(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=avg_frame_rate,nb_frames,width,height,duration",
            "-of",
            "json",
            str(path),
        ],
        _FFMPEG_TIMEOUT_S,
    )
    if proc.returncode != 0:
        raise MediaError(f"ffprobe failed on {path.name}: {proc.stderr.strip()[-300:]}")
    try:
        stream = json.loads(proc.stdout)["streams"][0]
        fps = float(Fraction(stream["avg_frame_rate"]))
        n_frames = int(stream.get("nb_frames") or 0)
        if n_frames <= 0:
            n_frames = max(1, round(float(stream["duration"]) * fps))
        return {
            "fps": fps,
            "n_frames": n_frames,
            "width": int(stream["width"]),
            "height": int(stream["height"]),
        }
    except (KeyError, IndexError, ValueError, ZeroDivisionError) as exc:
        raise MediaError(f"could not read video info from {path.name}") from exc


def _transcode_to_15fps(
    src: Path, t_start: float | None = None, t_end: float | None = None
) -> Path:
    """Transcode to constant 15 fps + faststart; caller deletes the result.

    With a window, only [t_start, t_end) is transcoded (seek, then duration;
    output timestamps reset to zero, so frame N of the result maps to
    t_start + N / 15 in the source clip).
    """
    tmp = tempfile.NamedTemporaryFile(
        prefix="slope15fps_", suffix=".mp4", delete=False
    )
    tmp.close()
    dst = Path(tmp.name)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if t_start is not None and t_end is not None:
        cmd += ["-ss", str(t_start), "-i", str(src), "-t", str(t_end - t_start)]
    else:
        cmd += ["-i", str(src)]
    cmd += [
        # fps filter, not -r: after -ss, -r dropped frames unevenly at the window start, so frame N was
        # not at t_start + N/15 and every real throw came out tilted about 24 degrees (found 10/29, T114).
        "-vf", "fps=15", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(dst),
    ]
    proc = _run_cmd(cmd, _FFMPEG_TIMEOUT_S)
    if proc.returncode != 0 or not dst.is_file():
        dst.unlink(missing_ok=True)
        raise MediaError(f"ffmpeg 15fps transcode failed: {proc.stderr.strip()[-300:]}")
    return dst


# SAM's frame_index k is frame k + 1 of the 15 fps clip we upload. Found 11/01 by matching SAM points against
# the decoded transcode (manus_clip1: median 18 px off at k, 0.7 px at k + 1), which also put Spark's re-check
# rings beside fast objects. A constant time shift leaves the fitted acceleration (g) unchanged.
SAM_FRAME_OFFSET = 1

_BOX_SIZE_RE = re.compile(r"<\|box;[^|]*?w=(\d+);h=(\d+)")


def _parse_records(output_text: str) -> tuple[list[dict[str, Any]], tuple[int, int]]:
    """Parse SAM wire lines into joined box+mask dicts plus the wire frame size.

    Box records from meta-sam-parser carry coordinates only (right/bottom are
    converted to exclusive bounds); the frame w/h come from the wire tokens
    and must match the transcoded clip, checked by the caller.
    """
    try:
        from meta_sam_parser import CompletedOutcome, video_segmentation_format
    except ImportError as exc:
        raise TrackingError(
            "the meta-sam-parser package is required to decode SAM output "
            "(pip install meta-sam-parser); see STATUS proposal."
        ) from exc
    try:
        parser = video_segmentation_format().create_parser()
        list(parser.push(output_text))
        if not output_text.endswith("\n"):
            list(parser.push("\n"))
        result = parser.finish(CompletedOutcome()).result
    except Exception as exc:
        raise TrackingError(f"could not parse SAM response: {exc}") from exc
    boxes: dict[tuple[int, str], Any] = {}
    masks: dict[tuple[int, str], Any] = {}
    for record in result.records:
        frame = getattr(record, "frame", None)
        if frame is None or getattr(record, "object_id", None) is None:
            raise TrackingError("SAM record missing frame or object id")
        key = (int(frame.frame_index), str(record.object_id))
        if getattr(record, "kind", None) == "box":
            boxes[key] = record
        elif getattr(record, "kind", None) == "mask":
            masks[key] = record
    if output_text.strip() and not boxes and not masks:
        raise TrackingError("SAM response contained no parseable records")
    joined = []
    for key, box in boxes.items():
        mask = masks.get(key)
        if mask is None:
            raise TrackingError(f"SAM record {key} has a box but no mask")
        joined.append({"key": key, "box": box, "mask": mask})
    sizes = {(int(w), int(h)) for w, h in _BOX_SIZE_RE.findall(output_text)}
    if len(sizes) != 1:
        raise TrackingError(f"SAM records disagree on frame size: {sorted(sizes)}")
    return joined, sizes.pop()


def _raster_stats(raster: bytes, w: int, h: int) -> tuple[float, float, int]:
    """Return (centroid_x, centroid_y, count) in raster pixels."""
    sx = sy = count = 0
    for j in range(h):
        row = j * w
        for i in range(w):
            if raster[row + i]:
                sx += i
                sy += j
                count += 1
    if count == 0:
        return (0.0, 0.0, 0)
    return (sx / count, sy / count, count)


def _detections_from_records(
    joined: list[dict[str, Any]],
    fps: float,
    frame_size: tuple[int, int],
    t_offset: float = 0.0,
) -> list[FrameDetection]:
    from meta_sam_parser import decode_mask_to_raster

    fw, fh = frame_size
    detections = []
    for item in joined:
        frame_index, object_id = item["key"]
        box = item["box"]
        mask_record = item["mask"].mask
        bounds = item["mask"].bounds
        try:
            raster = decode_mask_to_raster(mask_record)
        except Exception as exc:
            raise TrackingError(f"mask decode failed on frame {frame_index}: {exc}") from exc
        mw, mh = int(mask_record.width), int(mask_record.height)
        cx, cy, count = _raster_stats(bytes(raster), mw, mh)
        if count == 0:
            centroid = None
            area = 0.0
        else:
            # Box-local raster: pixel-center mapping into the bounds rect,
            # which is already in source pixels (half-open, like the box).
            bw = bounds.right - bounds.left
            bh = bounds.bottom - bounds.top
            centroid = (
                bounds.left + (cx + 0.5) * bw / mw,
                bounds.top + (cy + 0.5) * bh / mh,
            )
            area = count * (bw / mw) * (bh / mh)
        detections.append(
            FrameDetection(
                frame=frame_index,
                t_s=t_offset + (frame_index + SAM_FRAME_OFFSET) / fps,
                object_id=int(object_id),
                box=(float(box.left), float(box.top), float(box.right), float(box.bottom)),
                frame_size=(fw, fh),
                centroid_px=centroid,
                area_px=area,
                mask=bytes(raster),
                mask_size=(mw, mh),
            )
        )
    detections.sort(key=lambda d: (d.frame, d.object_id))
    return detections


def _billed_frames(usage: Any, n_frames: int) -> int:
    if usage is not None:
        if hasattr(usage, "model_dump"):
            data = usage.model_dump()
        elif isinstance(usage, dict):
            data = usage
        else:
            data = {"video_frames_processed": getattr(usage, "video_frames_processed", None)}
        value = data.get("video_frames_processed")
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
    return n_frames  # min-50 rule is applied by sam_video_cost_usd


def track(
    video_path: Path | str,
    text_prompt: str,
    *,
    t_start: float | None = None,
    t_end: float | None = None,
    timeout: float = _client.SAM_TIMEOUT_S,
    tracker: CostTracker | None = None,
) -> TrackResult:
    """Track a concept through a clip. Returns one entry per (frame, object).

    With t_start/t_end, only that window is sent and frame N maps to
    t_start + N / 15. Frames where the object is absent simply have no entry;
    callers that need a dense timeline (backend DetectionIn) must emit
    explicit missing markers instead of interpolating (see hooks).
    """
    if not text_prompt or not text_prompt.strip():
        raise ValueError("text_prompt must be a non-empty noun phrase")
    if "," in text_prompt or " and " in text_prompt.lower():
        raise ValueError("one concept per request; comma/and lists match nothing")
    if (t_start is None) != (t_end is None):
        raise ValueError("t_start and t_end must be given together")
    if t_start is not None and t_end is not None and not 0 <= t_start < t_end:
        raise ValueError("need 0 <= t_start < t_end")
    src = Path(video_path)
    if not src.is_file():
        raise MediaError(f"video file not found: {src}")
    tracker = tracker or get_tracker()
    tracker.check()

    prepared: Path | None = None
    try:
        prepared = _transcode_to_15fps(src, t_start, t_end)
        info = _probe_clip(prepared)
        fps = TARGET_FPS  # constant-frame-rate transcode above
        n_frames = info["n_frames"]
        if n_frames > MAX_SAM_FRAMES:
            raise MediaError(
                f"影片超過 60 秒（{n_frames} 格），請先選時間窗"
            )
        # Pre-book the estimate so one long-enough call can't jump the
        # ceiling between tracker.check() at entry and record() at exit.
        tracker.check(sam_video_cost_usd(n_frames))
        file_id = _client.upload_file(prepared)
        sdk = get_client()
        response = call_with_retry(
            lambda: sdk.responses.create(
                model=SAM_MODEL,
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": text_prompt.strip()},
                            {"type": "input_video", "file_id": file_id},
                        ],
                    }
                ],
                metadata={"mask_encoding": MASK_ENCODING},
                timeout=timeout,
            ),
            op="sam.track",
        )
    finally:
        if prepared is not None:
            prepared.unlink(missing_ok=True)

    billed = _billed_frames(getattr(response, "usage", None), n_frames)
    cost = tracker.record(SAM_MODEL, "sam.track", frames=billed)
    text = (response.output_text or "").strip()
    if not text:
        return TrackResult([], fps, n_frames, billed, cost)  # zero matches: valid
    joined, wire_size = _parse_records(text + "\n")
    if wire_size != (info["width"], info["height"]):
        raise TrackingError(
            f"SAM reports {wire_size[0]}x{wire_size[1]} frames but the clip is "
            f"{info['width']}x{info['height']}; refusing to map pixels."
        )
    detections = _detections_from_records(joined, fps, wire_size, t_start or 0.0)
    return TrackResult(detections, fps, n_frames, billed, cost)
