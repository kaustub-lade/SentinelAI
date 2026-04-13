from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pymongo.database import Database


def _serialize_details(details: Any) -> str:
    if details is None:
        return "{}"
    if isinstance(details, str):
        return details
    return json.dumps(details, default=str)


def log_audit_event(
    db: Database,
    *,
    action: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    status: str = "success",
    severity: str = "info",
    details: Any = None,
) -> None:
    db["audit_logs"].insert_one(
        {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "severity": severity,
            "details": _serialize_details(details),
            "created_at": datetime.now(timezone.utc),
        }
    )
