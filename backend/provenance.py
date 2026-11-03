"""What the video file says about where it came from (T275). Read-only facts, never a verdict.

Two sources, both written into the file by whoever made it:
- C2PA content credentials (a signed manifest). Meta AI, OpenAI Sora and Runway add one that declares the media
  "trainedAlgorithmicMedia" (made by a trained model). Only the active manifest is reported.
- Camera tags (make, model, creation time) that phones write into the container.

Absence means nothing: credentials and tags are stripped by downloads, re-encodes and screen recordings, so "no
information" is never evidence either way. GPS and other location tags are never read or returned.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

AI_SOURCE_TYPES = ("trainedAlgorithmicMedia", "compositeWithTrainedAlgorithmicMedia", "trainedAlgorithmicData")
CAMERA_KEYS = {
    "make": ("com.apple.quicktime.make", "com.android.manufacturer", "make"),
    "model": ("com.apple.quicktime.model", "com.android.model", "model"),
    "created": ("com.apple.quicktime.creationdate", "creation_time"),
}
MAX_TEXT = 80


def _short(v) -> str | None:
    return str(v).strip()[:MAX_TEXT] or None if v is not None else None


def parse_manifest_store(store: dict, validation_state: str | None = None) -> dict | None:
    """Summary of the active C2PA manifest, or None when there is none."""
    label = store.get("active_manifest")
    m = (store.get("manifests") or {}).get(label) if label else None
    if not m:
        return None
    info = m.get("claim_generator_info") or []
    gen = info[0].get("name") if info and isinstance(info[0], dict) else m.get("claim_generator")
    sig = m.get("signature_info") or {}
    sources = []
    for a in m.get("assertions") or []:
        if str(a.get("label", "")).startswith("c2pa.actions"):
            for act in (a.get("data") or {}).get("actions") or []:
                if act.get("digitalSourceType"):
                    sources.append(str(act["digitalSourceType"]).rsplit("/", 1)[-1])
    state = validation_state or store.get("validation_state")
    return {
        "present": True,
        "declares_ai_generated": any(s in AI_SOURCE_TYPES for s in sources),
        "digital_source_type": _short(sources[0]) if sources else None,
        "generator": _short(gen),
        "signer": _short(sig.get("issuer") or sig.get("common_name")),
        "signature_valid": None if state is None else str(state).lower() in ("valid", "trusted"),
    }


def read_c2pa(video: Path) -> dict | None:
    try:
        import c2pa
    except ImportError:
        return None
    try:
        with c2pa.Reader(str(video)) as r:
            store = json.loads(r.json())
            try:
                state = r.get_validation_state()
            except Exception:
                state = None
    except Exception:  # no manifest, or a format the library does not read: report nothing
        return None
    return parse_manifest_store(store, state)


def camera_from_tags(tags: dict) -> dict | None:
    low = {str(k).lower(): v for k, v in (tags or {}).items()}
    out = {}
    for field, keys in CAMERA_KEYS.items():
        for k in keys:
            if low.get(k):
                out[field] = _short(low[k])
                break
    if "make" not in out and "model" not in out:
        return None  # a creation time alone is written by every encoder, it says nothing about a camera
    return out


def read_camera(video: Path) -> dict | None:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags", "-of", "json", str(video)],
                         capture_output=True, text=True, timeout=30).stdout
    try:
        tags = json.loads(out or "{}").get("format", {}).get("tags", {})
    except ValueError:
        return None
    return camera_from_tags(tags)


def read_provenance(video: Path) -> dict:
    return {"c2pa": read_c2pa(video), "camera": read_camera(video)}
