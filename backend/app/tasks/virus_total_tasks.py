from datetime import datetime
from typing import Any

from celery_app import celery

from app.services.virus_total import lookup_file_hash, lookup_url
from app.core.database import mongo_db


@celery.task(name="app.tasks.vt_lookup_file")
def vt_lookup_file(file_hash: str) -> dict:
    res = lookup_file_hash(file_hash)
    record = {
        "query": file_hash,
        "type": "file_hash",
        "result": res,
        "created_at": datetime.utcnow(),
    }
    try:
        mongo_db["vt_lookups"].insert_one(record)
    except Exception:
        pass
    return {"status": "ok", "query": file_hash}


@celery.task(name="app.tasks.vt_lookup_url")
def vt_lookup_url_task(target_url: str) -> dict:
    res = lookup_url(target_url)
    record = {
        "query": target_url,
        "type": "url",
        "result": res,
        "created_at": datetime.utcnow(),
    }
    try:
        mongo_db["vt_lookups"].insert_one(record)
    except Exception:
        pass
    return {"status": "ok", "query": target_url}
