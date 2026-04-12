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
from sqlalchemy.orm import Session

from app.core.auth_utils import require_roles
from app.core.database import get_db
from app.models import AssistantMessage, AuditLog, CveRecord, Scan

router = APIRouter()


def _csv_bytes(headers: list[str], rows: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in headers})
    return buffer.getvalue().encode("utf-8")


def _build_rows_for_cves(db: Session) -> list[dict]:
    records = db.query(CveRecord).order_by(CveRecord.risk_score.desc(), CveRecord.id.desc()).all()
    return [
        {
            "cve_id": record.cve_id,
            "severity": record.severity,
            "cvss_score": record.cvss_score,
            "risk_score": record.risk_score,
            "exploit_available": record.exploit_available,
            "patch_available": record.patch_available,
            "published_date": record.published_date.isoformat() if record.published_date else "",
            "last_modified": record.last_modified.isoformat() if record.last_modified else "",
            "description": record.description,
            "affected_systems": record.affected_systems,
        }
        for record in records
    ]


def _build_rows_for_phishing(db: Session) -> list[dict]:
    scans = (
        db.query(Scan)
        .filter(Scan.scan_type == "phishing")
        .order_by(Scan.created_at.desc(), Scan.id.desc())
        .all()
    )

    rows: list[dict] = []
    for scan in scans:
        try:
            result = json.loads(scan.result)
            input_data = json.loads(scan.input_data)
        except json.JSONDecodeError:
            result = {}
            input_data = {}

        rows.append(
            {
                "scan_id": scan.id,
                "created_at": scan.created_at.isoformat(),
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


def _build_rows_for_assistant(db: Session) -> list[dict]:
    messages = db.query(AssistantMessage).order_by(AssistantMessage.created_at.desc(), AssistantMessage.id.desc()).all()
    return [
        {
            "message_id": message.id,
            "conversation_id": message.conversation_id,
            "user_id": message.user_id,
            "role": message.role,
            "created_at": message.created_at.isoformat(),
            "content": message.content,
        }
        for message in messages
    ]


def _build_rows_for_audit(db: Session) -> list[dict]:
    events = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).all()
    return [
        {
            "event_id": event.id,
            "created_at": event.created_at.isoformat(),
            "user_id": event.user_id,
            "action": event.action,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "status": event.status,
            "severity": event.severity,
            "details": event.details,
        }
        for event in events
    ]


@router.get("/export")
async def export_reports(
    scope: str = Query(default="all", pattern="^(all|cves|phishing|assistant|audit)$"),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Export security reports as a ZIP bundle of CSV files."""
    export_timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "scope": scope,
        "counts": {
            "cves": db.query(CveRecord).count(),
            "phishing_scans": db.query(Scan).filter(Scan.scan_type == "phishing").count(),
            "assistant_messages": db.query(AssistantMessage).count(),
            "audit_events": db.query(AuditLog).count(),
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
