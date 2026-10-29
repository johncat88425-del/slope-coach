import pytest

from backend.model_hooks import TrackingUnavailable
from meta_client import explain, headline, hooks, sam, spark
from meta_client.exceptions import MediaError, ModelOutputError


def test_check_scene_maps_to_schema(monkeypatch, tmp_path):
    monkeypatch.setattr(
        spark, "describe_scene",
        lambda path: {
            "has_ruler": True, "has_slope": True, "has_slider": False,
            "is_side_view": True, "needs_retake": False, "retake_reasons": [],
        },
    )
    out = hooks.MetaHooks().check_scene(tmp_path / "p.jpg")
    assert out.source == "model"
    assert out.has_slider is False


def test_suggest_release_time_maps_to_schema(monkeypatch, tmp_path):
    monkeypatch.setattr(
        spark, "suggest_release_time",
        lambda path: {"candidate_t0_s": 2.0, "reason": "block starts moving"},
    )
    out = hooks.MetaHooks().suggest_release_time(tmp_path / "c.mp4")
    assert out.source == "model"
    assert out.candidate_t0_s == 2.0


def test_track_slider_dense_timeline_with_missing_markers(monkeypatch, tmp_path):
    def det(frame, centroid, area=100.0, oid=0):
        return sam.FrameDetection(frame, frame / 15.0, oid, (0, 0, 2, 2),
                                  (10, 10), centroid, area)

    result = sam.TrackResult(
        detections=[det(0, (5.0, 5.0)), det(2, None, 0.0)],  # frame 1 absent
        fps=15.0, n_frames=3, billed_frames=50, cost_usd=0.01,
    )
    monkeypatch.setattr(sam, "track", lambda path, prompt: result)
    dets = hooks.MetaHooks().track_slider(tmp_path / "c.mp4", "block")
    assert len(dets) == 3
    assert [d.t_s for d in dets] == pytest.approx([0.0, 1 / 15.0, 2 / 15.0])
    assert dets[0].centroid_px == (5.0, 5.0)
    assert dets[0].area_px == 100.0
    assert dets[1].centroid_px is None  # explicit gap, not interpolated
    assert dets[2].centroid_px is None  # empty mask stays missing
    assert all(d.source == "sam" for d in dets)


def test_track_slider_selects_main_object(tmp_path, monkeypatch):
    def det(oid, frame):
        return sam.FrameDetection(frame, frame / 15.0, oid, (0, 0, 2, 2),
                                  (10, 10), (float(oid), 0.0), 10.0)

    result = sam.TrackResult(
        detections=[det(7, 0), det(3, 0), det(3, 1)],
        fps=15.0, n_frames=2, billed_frames=50, cost_usd=0.01,
    )
    monkeypatch.setattr(sam, "track", lambda path, prompt: result)
    dets = hooks.MetaHooks().track_slider(tmp_path / "c.mp4", "block")
    assert [d.centroid_px[0] for d in dets] == [3.0, 3.0]


def test_track_slider_failure_becomes_501_signal(tmp_path, monkeypatch):
    def boom(path, prompt):
        raise MediaError("ffmpeg not found")

    monkeypatch.setattr(sam, "track", boom)
    with pytest.raises(TrackingUnavailable, match="ffmpeg"):
        hooks.MetaHooks().track_slider(tmp_path / "c.mp4", "block")


def test_track_object_passes_window_and_offsets_time(tmp_path, monkeypatch):
    seen = {}

    def det(frame, centroid, area=100.0):
        return sam.FrameDetection(frame, 1.0 + frame / 15.0, 0, (0, 0, 2, 2),
                                  (10, 10), centroid, area)

    result = sam.TrackResult(
        detections=[det(0, (5.0, 5.0)), det(2, None, 0.0)],
        fps=15.0, n_frames=3, billed_frames=50, cost_usd=0.01,
    )

    def fake_track(path, prompt, **kwargs):
        seen.update(kwargs)
        return result

    monkeypatch.setattr(sam, "track", fake_track)
    dets = hooks.MetaHooks().track_object(tmp_path / "c.mp4", "ball", 1.0, 2.0)
    assert seen == {"t_start": 1.0, "t_end": 2.0}
    assert [d.t_s for d in dets] == pytest.approx([1.0, 1.0 + 1 / 15.0, 1.0 + 2 / 15.0])
    # API v0.5: centroid normalised to 0..1, area as a frame fraction
    assert dets[0].centroid_px == (0.5, 0.5)
    assert dets[0].area_px == pytest.approx(1.0)
    assert dets[1].centroid_px is None
    assert dets[2].centroid_px is None


def test_track_object_failure_becomes_501_signal(tmp_path, monkeypatch):
    def boom(path, prompt, **kwargs):
        raise MediaError("ffmpeg not found")

    monkeypatch.setattr(sam, "track", boom)
    with pytest.raises(TrackingUnavailable, match="ffmpeg"):
        hooks.MetaHooks().track_object(tmp_path / "c.mp4", "ball", 0.0, 1.0)


def test_explain_audit_extracts_text_and_none_on_failure(monkeypatch):
    seen = {}
    def fake_explain(result, *, kind="comparison", **kwargs):
        seen["kind"] = kind
        return {"explanation": "motion matches"}
    monkeypatch.setattr(explain, "explain_result", fake_explain)
    assert hooks.MetaHooks().explain_audit({"verdict": "consistent"}) == "motion matches"
    assert seen == {"kind": "audit"}
    def boom(result, **kwargs):
        raise ModelOutputError("bad")
    monkeypatch.setattr(explain, "explain_result", boom)
    assert hooks.MetaHooks().explain_audit({"verdict": "consistent"}) is None


def test_headline_audit_passes_through(monkeypatch):
    monkeypatch.setattr(headline, "write_headline",
                        lambda audit, **kw: {"headline": "falls like the Moon",
                                             "source": "muse-spark-1.3"})
    assert hooks.MetaHooks().headline_audit({}) == "falls like the Moon"
    monkeypatch.setattr(headline, "write_headline", lambda audit, **kw: None)
    assert hooks.MetaHooks().headline_audit({}) is None
