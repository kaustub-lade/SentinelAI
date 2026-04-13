"""
Report Export Endpoints - Download security reports as CSV/ZIP bundles.
"""

import csv
import io
import json
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pymongo.database import Database

from app.core.auth_utils import require_roles
from app.core.database import get_db

router = APIRouter()


def _csv_bytes(headers: list[str], rows: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in headers})
    return buffer.getvalue().encode("utf-8")


def _build_rows_for_cves(db: Database) -> list[dict]:
    records = list(db["cve_records"].find().sort("risk_score", -1))
    return [
        {
            "cve_id": record.get("cve_id"),
            "severity": record.get("severity"),
            "cvss_score": record.get("cvss_score"),
            "risk_score": record.get("risk_score"),
            "exploit_available": record.get("exploit_available"),
            "patch_available": record.get("patch_available"),
            "published_date": record.get("published_date").isoformat() if record.get("published_date") else "",
            "last_modified": record.get("last_modified").isoformat() if record.get("last_modified") else "",
            "description": record.get("description"),
            "affected_systems": record.get("affected_systems"),
        }
        for record in records
    ]


def _build_rows_for_phishing(db: Database) -> list[dict]:
    scans = list(db["scans"].find({"scan_type": "phishing"}).sort("created_at", -1))

    rows: list[dict] = []
    for scan in scans:
        try:
            result = json.loads(scan.get("result", "{}"))
            input_data = json.loads(scan.get("input_data", "{}"))
        except json.JSONDecodeError:
            result = {}
            input_data = {}

        rows.append(
            {
                "scan_id": str(scan.get("_id")),
                "created_at": scan.get("created_at").isoformat() if scan.get("created_at") else "",
                "sender_email": input_data.get("sender_email", ""),
                "subject": input_data.get("subject", ""),
                "url": input_data.get("url", ""),
                "risk_level": result.get("risk_level", ""),
                "confidence": result.get("confidence", ""),
                "is_phishing": result.get("is_phishing", ""),
                "indicators": "; ".join(result.get("detected_indicators", [])) if isinstance(result.get("detected_indicators"), list) else "",
            }
        )

    return rows


def _build_rows_for_assistant(db: Database) -> list[dict]:
    messages = list(db["assistant_messages"].find().sort("created_at", -1))
    return [
        {
            "message_id": str(message.get("_id")),
            "conversation_id": message.get("conversation_id"),
            "user_id": message.get("user_id"),
            "role": message.get("role"),
            "created_at": message.get("created_at").isoformat() if message.get("created_at") else "",
            "content": message.get("content"),
        }
        for message in messages
    ]


def _build_rows_for_audit(db: Database) -> list[dict]:
    events = list(db["audit_logs"].find().sort("created_at", -1))
    return [
        {
            "event_id": str(event.get("_id")),
            "created_at": event.get("created_at").isoformat() if event.get("created_at") else "",
            "user_id": event.get("user_id"),
            "action": event.get("action"),
            "resource_type": event.get("resource_type"),
            "resource_id": event.get("resource_id"),
            "status": event.get("status"),
            "severity": event.get("severity"),
            "details": event.get("details"),
        }
        for event in events
    ]


@router.get("/export")
async def export_reports(
    scope: str = Query(default="all", pattern="^(all|cves|phishing|assistant|audit)$"),
    db: Database = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Export security reports as a ZIP bundle of CSV files."""
    export_timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "scope": scope,
        "counts": {
            "cves": db["cve_records"].count_documents({}),
            "phishing_scans": db["scans"].count_documents({"scan_type": "phishing"}),
            "assistant_messages": db["assistant_messages"].count_documents({}),
            "audit_events": db["audit_logs"].count_documents({}),
        },
    }

    datasets = {
        "cves.csv": (
            ["cve_id", "severity", "cvss_score", "risk_score", "exploit_available", "patch_available", "published_date", "last_modified", "description", "affected_systems"],
            _build_rows_for_cves(db),
        ),
        "phishing_scans.csv": (
            ["scan_id", "created_at", "sender_email", "subject", "url", "risk_level", "confidence", "is_phishing", "indicators"],
            _build_rows_for_phishing(db),
        ),
        "assistant_messages.csv": (
            ["message_id", "conversation_id", "user_id", "role", "created_at", "content"],
            _build_rows_for_assistant(db),
        ),
        "audit_logs.csv": (
            ["event_id", "created_at", "user_id", "action", "resource_type", "resource_id", "status", "severity", "details"],
            _build_rows_for_audit(db),
        ),
    }

    selected_files = datasets.keys() if scope == "all" else {
        "cves": ["cves.csv"],
        "phishing": ["phishing_scans.csv"],
        "assistant": ["assistant_messages.csv"],
        "audit": ["audit_logs.csv"],
    }[scope]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in selected_files:
            headers, rows = datasets[filename]
            archive.writestr(filename, _csv_bytes(headers, rows))
        archive.writestr("summary.json", json.dumps(summary, indent=2, default=str))

    zip_buffer.seek(0)
    filename = f"sentinelai-reports-{export_timestamp}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
