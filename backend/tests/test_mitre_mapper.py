from app.services.mitre_mapper import map_features


def test_map_features_empty():
    features = {"pe": {"sections": [], "imports": {}}}
    res = map_features(features)
    assert isinstance(res, list)


def test_map_features_detects_packed():
    features = {"high_entropy": True, "suspected_packed": True, "pe": {"sections": ["UPX0"]}}
    res = map_features(features)
    assert any(isinstance(r.get("technique_id"), str) for r in res)
