"""Background task to fetch MITRE ATT&CK enterprise JSON for mapping.

Downloads the JSON from the official CTI repository and stores it in the
backend data directory for `mitre_mapper` to load.
"""
import os
from datetime import datetime

import requests

from celery_app import celery

MITRE_URL = "https://raw.githubusercontent.com/mitre/cti/main/enterprise-attack/enterprise-attack.json"
OUT_PATH = os.getenv("MITRE_DATA_PATH", "./backend/app/data/enterprise-attack.json")


@celery.task(name="app.tasks.fetch_mitre")
def fetch_mitre_data() -> dict:
    try:
        r = requests.get(MITRE_URL, timeout=30)
        r.raise_for_status()
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        with open(OUT_PATH, "wb") as fh:
            fh.write(r.content)
        return {"status": "ok", "path": OUT_PATH, "fetched_at": datetime.utcnow().isoformat()}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
