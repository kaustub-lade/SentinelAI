"""LightGBM malware classifier trained on the EMBER-2018 benchmark.

The model file is a LightGBM text model (``ember_model.txt``) produced by
``backend/scripts/train_ember_model.py``. If it is missing the app simply
falls back to the legacy heuristic scorer, so deployments never hard-fail.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

_MODEL_PATH = Path(
    os.getenv("EMBER_MODEL_PATH")
    or (Path(__file__).resolve().parent.parent / "ml" / "ember_model.txt")
)

_lock = threading.Lock()
_booster = None
_extractor = None
_load_attempted = False


def _load() -> None:
    global _booster, _load_attempted
    if _load_attempted:
        return
    with _lock:
        if _load_attempted:
            return
        _load_attempted = True
        if not _MODEL_PATH.exists():
            return
        try:
            import lightgbm as lgb

            _booster = lgb.Booster(model_file=str(_MODEL_PATH))
        except Exception:  # missing lightgbm, corrupt file, version mismatch
            _booster = None


def warmup() -> None:
    """Load the model eagerly (call at startup so the first upload is fast)."""
    _load()


def available() -> bool:
    _load()
    return _booster is not None


def model_path() -> str:
    return str(_MODEL_PATH)


def _get_extractor():
    global _extractor
    if _extractor is None:
        # Imported lazily: pulls in lief, which is only present in deployments
        # that ship the EMBER model.
        from .ember_features import PEFeatureExtractor

        _extractor = PEFeatureExtractor(print_feature_warning=False)
    return _extractor


def predict(data: bytes) -> Optional[Dict[str, Any]]:
    """Score a PE file with the EMBER model. Returns None when not applicable."""
    if not available():
        return None
    # EMBER was built from Windows PE files only.
    if len(data) < 64 or data[:2] != b"MZ":
        return None
    try:
        vector = _get_extractor().feature_vector(data)
    except Exception:
        return None

    try:
        probability = float(_booster.predict([vector])[0])
    except Exception:
        return None

    return {
        "probability": probability,
        "engine": "ember-lightgbm-v2",
        "feature_version": 2,
        "feature_count": int(len(vector)),
    }
