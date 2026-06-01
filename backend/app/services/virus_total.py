"""Simple VirusTotal v3 client wrappers.

These helpers use the `VIRUSTOTAL_API_KEY` from settings. When the key
is not configured they return a stub response so callers can function in
demo mode.
"""
import time
from typing import Dict, Any

import requests

from app.core.config import settings


VT_BASE = "https://www.virustotal.com/api/v3"


def _headers():
    key = settings.VIRUSTOTAL_API_KEY
    if not key:
        return {}
    return {"x-apikey": key}


def lookup_file_hash(file_hash: str) -> Dict[str, Any]:
    """Lookup a file hash in VirusTotal. Returns parsed JSON or stub.
    """
    if not settings.VIRUSTOTAL_API_KEY:
        return {"error": "no_api_key", "detail": "VIRUSTOTAL_API_KEY not set"}

    url = f"{VT_BASE}/files/{file_hash}"
    resp = requests.get(url, headers=_headers(), timeout=20)
    if resp.status_code == 200:
        return resp.json()
    return {"error": "vt_error", "status_code": resp.status_code, "body": resp.text}


def lookup_url(target_url: str) -> Dict[str, Any]:
    """Submit and retrieve URL analysis. Returns the analysis JSON or stub.
    """
    if not settings.VIRUSTOTAL_API_KEY:
        return {"error": "no_api_key", "detail": "VIRUSTOTAL_API_KEY not set"}

    # Submit URL for analysis
    submit = requests.post(f"{VT_BASE}/urls", headers=_headers(), data={"url": target_url}, timeout=20)
    if submit.status_code not in (200, 201):
        return {"error": "vt_submit_failed", "status_code": submit.status_code, "body": submit.text}

    try:
        submit_json = submit.json()
        analysis_id = submit_json.get("data", {}).get("id")
    except Exception:
        return {"error": "invalid_response", "body": submit.text}

    # Poll the analysis endpoint once
    time.sleep(1)
    getr = requests.get(f"{VT_BASE}/urls/{analysis_id}", headers=_headers(), timeout=20)
    if getr.status_code == 200:
        return getr.json()
    return {"error": "vt_fetch_failed", "status_code": getr.status_code, "body": getr.text}
