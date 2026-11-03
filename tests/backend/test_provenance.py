from backend.provenance import camera_from_tags, parse_manifest_store, read_provenance


def store(source="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"):
    return {"active_manifest": "urn:a", "manifests": {
        "urn:a": {"claim_generator_info": [{"name": "Meta AI"}], "signature_info": {"issuer": "Meta Platforms"},
                  "assertions": [{"label": "c2pa.actions.v2", "data": {"actions": [
                      {"action": "c2pa.created", "digitalSourceType": source}]}}]},
        "urn:old": {"claim_generator": "another tool", "assertions": []}}}


def test_active_manifest_that_declares_trained_algorithmic_media():
    out = parse_manifest_store(store(), "Valid")
    assert out == {"present": True, "declares_ai_generated": True, "digital_source_type": "trainedAlgorithmicMedia",
                   "generator": "Meta AI", "signer": "Meta Platforms", "signature_valid": True}


def test_camera_capture_manifest_and_invalid_signature():
    out = parse_manifest_store(store("http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture"), "Invalid")
    assert out["declares_ai_generated"] is False and out["signature_valid"] is False
    assert parse_manifest_store({"manifests": {}}) is None


def test_camera_tags_never_include_location():
    tags = {"com.apple.quicktime.make": "Apple", "com.apple.quicktime.model": "iPhone 15 Pro Max",
            "com.apple.quicktime.creationdate": "2026-10-29T10:00:00+0800",
            "com.apple.quicktime.location.ISO6709": "+25.0+121.5/"}
    assert camera_from_tags(tags) == {"make": "Apple", "model": "iPhone 15 Pro Max",
                                      "created": "2026-10-29T10:00:00+0800"}
    assert camera_from_tags({"creation_time": "2026-10-29"}) is None  # every encoder writes a time


def test_plain_encoded_clip_has_no_provenance(tmp_path):
    from tests.backend.test_audits import write_clip
    write_clip(tmp_path / "c.mp4", 9.81)
    assert read_provenance(tmp_path / "c.mp4") == {"c2pa": None, "camera": None}
