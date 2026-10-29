import pytest

from meta_client import sam
from meta_client.cost import CostTracker
from meta_client.exceptions import MediaError, TrackingError
from tests.meta_client.helpers import FakeClient, fake_response

# Real wire example from the meta-sam-parser docs: frame 0, 320x334 source,
# one 60x27 lossless mask. Decodes to 1539 set pixels out of 1620.
DOC_LINE = (
    "<0f>0<|box;x1=211;y1=228;x2=270;y2=254;w=320;h=334|>"
    "<|mask;x=0;y=0;data=27,60,"
    "~!!!!M!0c[0o91w?q1!pIH4pPRVp2B3'7`e.ioeAf6-k/#Xd8%dX9x(|>"
)
PROBE = {"fps": 15.0, "n_frames": 150, "width": 320, "height": 334}


def _patch_media(monkeypatch, tmp_path, probe=None):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"fake-video")
    prepared = tmp_path / "prepared.mp4"
    prepared.write_bytes(b"fake-15fps")
    monkeypatch.setattr(sam, "_transcode_to_15fps", lambda src, *a: prepared)
    monkeypatch.setattr(sam, "_probe_clip", lambda path: dict(probe or PROBE))
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-1")
    return clip


def test_track_success(tmp_path, monkeypatch):
    clip = _patch_media(monkeypatch, tmp_path)
    fake = FakeClient([fake_response(DOC_LINE, usage=None)])
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    tracker = CostTracker(tmp_path / "cost.csv", limit_usd=120)

    result = sam.track(clip, "sliding block", tracker=tracker)

    call = fake.responses.calls[0]
    assert call["model"] == "sam-3.1"
    assert call["metadata"] == {"mask_encoding": "one_bit"}
    parts = call["input"][0]["content"]
    assert parts[0] == {"type": "input_text", "text": "sliding block"}
    assert parts[1] == {"type": "input_video", "file_id": "file-1"}

    assert result.n_frames == 150
    assert result.fps == 15.0
    assert len(result.detections) == 1
    det = result.detections[0]
    assert det.frame == 0
    assert det.t_s == 0.0
    assert det.object_id == 0
    assert det.box == (211.0, 228.0, 271.0, 255.0)  # parser: exclusive bounds
    assert det.frame_size == (320, 334)
    assert det.mask_size == (60, 27)
    assert len(det.mask) == 60 * 27
    # centroid inside the box, scaled to source pixels
    assert 211.0 <= det.centroid_px[0] <= 271.0
    assert 228.0 <= det.centroid_px[1] <= 255.0
    # box-local raster 60x27 maps 1:1 onto the 60x27 source box here
    assert det.area_px == pytest.approx(1539.0)
    assert result.billed_frames == 150
    assert result.source == "sam-3.1"
    assert result.cost_usd == pytest.approx(150 * 0.20 / 1000)
    assert tracker.total_usd() == pytest.approx(result.cost_usd)


def test_track_zero_matches_is_valid(tmp_path, monkeypatch):
    clip = _patch_media(monkeypatch, tmp_path)
    fake = FakeClient([fake_response("", usage=None)])
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    tracker = CostTracker(tmp_path / "cost.csv", limit_usd=120)
    result = sam.track(clip, "yellow school bus", tracker=tracker)
    assert result.detections == []
    assert result.n_frames == 150
    assert result.cost_usd == pytest.approx(150 * 0.20 / 1000)


def test_track_short_clip_bills_minimum_50(tmp_path, monkeypatch):
    probe = dict(PROBE, n_frames=10)
    clip = _patch_media(monkeypatch, tmp_path, probe=probe)
    fake = FakeClient([fake_response("", usage=None)])
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    tracker = CostTracker(tmp_path / "cost.csv", limit_usd=120)
    result = sam.track(clip, "block", tracker=tracker)
    assert result.billed_frames == 10
    assert result.cost_usd == pytest.approx(50 * 0.20 / 1000)


def test_track_honors_usage_billed_frames(tmp_path, monkeypatch):
    clip = _patch_media(monkeypatch, tmp_path)
    fake = FakeClient(
        [fake_response("", usage={"video_frames_processed": 200})]
    )
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    tracker = CostTracker(tmp_path / "cost.csv", limit_usd=120)
    result = sam.track(clip, "block", tracker=tracker)
    assert result.billed_frames == 200
    assert result.cost_usd == pytest.approx(200 * 0.20 / 1000)


def test_track_rejects_wire_size_mismatch(tmp_path, monkeypatch):
    probe = dict(PROBE, width=640, height=480)
    clip = _patch_media(monkeypatch, tmp_path, probe=probe)
    fake = FakeClient([fake_response(DOC_LINE, usage=None)])
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    monkeypatch.setattr(sam, "get_tracker", lambda: CostTracker(tmp_path / "c.csv"))
    with pytest.raises(TrackingError, match="refusing to map pixels"):
        sam.track(clip, "block")


def test_track_rejects_garbage_output(tmp_path, monkeypatch):
    clip = _patch_media(monkeypatch, tmp_path)
    fake = FakeClient([fake_response("definitely not sam output", usage=None)])
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    monkeypatch.setattr(sam, "get_tracker", lambda: CostTracker(tmp_path / "c.csv"))
    with pytest.raises(TrackingError):
        sam.track(clip, "block")


def test_track_validates_prompt_and_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sam, "get_tracker", lambda: CostTracker(tmp_path / "c.csv"))
    with pytest.raises(MediaError, match="not found"):
        sam.track(tmp_path / "missing.mp4", "block")
    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"v")
    with pytest.raises(ValueError, match="non-empty"):
        sam.track(clip, "   ")
    with pytest.raises(ValueError, match="one concept"):
        sam.track(clip, "block, ruler")


def test_select_main_track_prefers_longest_then_largest():
    def det(oid, frame, area):
        return sam.FrameDetection(frame, frame / 15, oid, (0, 0, 1, 1),
                                  (10, 10), (0.5, 0.5), area)

    assert sam.select_main_track([]) is None
    dets = [det(0, 0, 10.0), det(1, 0, 5.0), det(1, 1, 5.0)]
    assert sam.select_main_track(dets) == 1  # 2 frames beats 1
    tied = [det(0, 0, 1.0), det(1, 0, 9.0)]
    assert sam.select_main_track(tied) == 1  # tie: larger area wins


def test_raster_stats():
    cx, cy, count = sam._raster_stats(bytes([1, 0, 1, 1]), 2, 2)
    assert count == 3
    assert (cx, cy) == pytest.approx(((0 + 0 + 1) / 3, (0 + 1 + 1) / 3))
    assert sam._raster_stats(bytes(4), 2, 2) == (0.0, 0.0, 0)


def test_transcode_failure_raises_media_error(tmp_path, monkeypatch):
    import subprocess

    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"v")
    monkeypatch.setattr(
        sam.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 1, "", "boom"),
    )
    with pytest.raises(MediaError, match="transcode failed"):
        sam._transcode_to_15fps(clip)


def test_missing_ffmpeg_raises_media_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sam.subprocess, "run",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
    )
    with pytest.raises(MediaError, match="ffmpeg"):
        sam._run_cmd(["ffmpeg", "-version"], 10)


def test_track_window_slices_and_offsets_time(tmp_path, monkeypatch):
    seen = {}

    def fake_transcode(src, t_start=None, t_end=None):
        seen["window"] = (t_start, t_end)
        prepared = tmp_path / "prepared.mp4"
        prepared.write_bytes(b"fake-15fps")
        return prepared

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"fake-video")
    monkeypatch.setattr(sam, "_transcode_to_15fps", fake_transcode)
    monkeypatch.setattr(sam, "_probe_clip", lambda path: dict(PROBE))
    monkeypatch.setattr("meta_client.client.upload_file", lambda p, **k: "file-1")
    fake = FakeClient([fake_response(DOC_LINE, usage=None)])
    monkeypatch.setattr(sam, "get_client", lambda: fake)
    tracker = CostTracker(tmp_path / "cost.csv", limit_usd=120)
    result = sam.track(clip, "ball", t_start=1.0, t_end=2.0, tracker=tracker)
    assert seen["window"] == (1.0, 2.0)
    assert result.detections[0].t_s == pytest.approx(1.0)


def test_track_window_validates_bounds(tmp_path, monkeypatch):
    monkeypatch.setattr(sam, "get_tracker", lambda: CostTracker(tmp_path / "c.csv"))
    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"v")
    with pytest.raises(ValueError, match="together"):
        sam.track(clip, "ball", t_start=1.0)
    with pytest.raises(ValueError, match="t_start < t_end"):
        sam.track(clip, "ball", t_start=2.0, t_end=1.0)
    with pytest.raises(ValueError, match="t_start < t_end"):
        sam.track(clip, "ball", t_start=-1.0, t_end=1.0)


def test_transcode_window_uses_seek_and_duration(tmp_path, monkeypatch):
    import subprocess

    cmds = []
    monkeypatch.setattr(
        sam.subprocess, "run",
        lambda *a, **k: (cmds.append(a[0]), subprocess.CompletedProcess(a[0], 0, "", ""))[1],
    )
    dst = sam._transcode_to_15fps(tmp_path / "c.mp4", 1.0, 2.5)
    try:
        assert "-ss" in cmds[0] and "-t" in cmds[0]
        assert cmds[0][cmds[0].index("-t") + 1] == "1.5"
    finally:
        dst.unlink(missing_ok=True)
