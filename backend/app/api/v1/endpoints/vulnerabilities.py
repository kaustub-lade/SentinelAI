"""
Vulnerability Intelligence Endpoints - CVE Analysis & Prioritization
"""

from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth_utils import require_roles
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.models import CveRecord
from app.services.audit import log_audit_event

router = APIRouter()


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)


def _severity_from_cvss(cvss_score: float) -> str:
    if cvss_score >= 9.0:
        return "Critical"
    if cvss_score >= 7.0:
        return "High"
    if cvss_score >= 4.0:
        return "Medium"
    return "Low"


def _to_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_cvss(cve_obj: dict) -> float:
    metrics = cve_obj.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if entries and isinstance(entries, list):
            cvss_data = entries[0].get("cvssData", {})
            score = cvss_data.get("baseScore")
            if isinstance(score, (float, int)):
                return float(score)
    return 0.0


def _extract_description(cve_obj: dict) -> str:
    descriptions = cve_obj.get("descriptions", [])
    for item in descriptions:
        if item.get("lang") == "en" and item.get("value"):
            return item["value"]
    if descriptions:
        return descriptions[0].get("value", "No description available")
    return "No description available"


def _extract_affected(cve_obj: dict) -> str:
    systems: list[str] = []
    for config in cve_obj.get("configurations", []):
        for node in config.get("nodes", []):
            for cpe in node.get("cpeMatch", []):
                criteria = cpe.get("criteria")
                if criteria:
                    systems.append(criteria)
    return ", ".join(systems[:10])


@router.post("/fetch")
async def fetch_cves_from_nvd(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Fetch latest CVEs from NVD and cache/update in database."""
    return await _fetch_cves_from_nvd(limit=limit, db=db, user_id=current_user.id)


async def _fetch_cves_from_nvd(limit: int, db: Session, user_id: int | None = None):
    """Internal CVE fetch helper used by refresh and scan routes."""
    _ensure_schema()
    headers = {}
    if settings.NVD_API_KEY:
        headers["apiKey"] = settings.NVD_API_KEY

    params = {
        "resultsPerPage": limit,
        "startIndex": 0,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params=params,
            headers=headers,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch CVEs from NVD")

    payload = response.json()
    vulnerabilities = payload.get("vulnerabilities", [])
    upserted = 0

    for item in vulnerabilities:
        cve_obj = item.get("cve", {})
        cve_id = cve_obj.get("id")
        if not cve_id:
            continue

        cvss_score = _extract_cvss(cve_obj)
        description = _extract_description(cve_obj)
        severity = _severity_from_cvss(cvss_score)
        affected_systems = _extract_affected(cve_obj)
        risk_score = int(min(100, round(cvss_score * 10)))

        record = db.query(CveRecord).filter(CveRecord.cve_id == cve_id).first()
        if record is None:
            record = CveRecord(cve_id=cve_id)
            db.add(record)

        record.description = description
        record.severity = severity
        record.cvss_score = cvss_score
        record.affected_systems = affected_systems
        record.exploit_available = "exploit" in description.lower()
        record.patch_available = True
        record.risk_score = risk_score
        record.published_date = _to_datetime(cve_obj.get("published"))
        record.last_modified = _to_datetime(cve_obj.get("lastModified"))
        upserted += 1

    db.commit()
    log_audit_event(
        db,
        action="vulnerabilities.fetch_nvd",
        resource_type="cve_cache",
        user_id=user_id,
        status="success",
        severity="info",
        details={"fetched": len(vulnerabilities), "upserted": upserted},
    )
    db.commit()

    return {
        "fetched": len(vulnerabilities),
        "upserted": upserted,
        "total_cached": db.query(CveRecord).count(),
    }


@router.get("/list")
def get_vulnerabilities(
    severity: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get vulnerabilities cached in DB (fetched from NVD)."""
    _ensure_schema()
    query = db.query(CveRecord)
    if severity:
        query = query.filter(CveRecord.severity == severity)

    records = query.order_by(CveRecord.risk_score.desc()).limit(limit).all()
    vulns = [
        {
            "cve_id": rec.cve_id,
            "cvss_score": rec.cvss_score,
            "severity": rec.severity,
            "description": rec.description,
            "affected_systems": rec.affected_systems.split(", ") if rec.affected_systems else [],
            "exploit_available": rec.exploit_available,
            "patch_available": rec.patch_available,
            "risk_score": rec.risk_score,
            "published_date": rec.published_date.isoformat() if rec.published_date else None,
            "last_modified": rec.last_modified.isoformat() if rec.last_modified else None,
        }
        for rec in records
    ]
    total_query = db.query(func.count(CveRecord.id))
    if severity:
        total_query = total_query.filter(CveRecord.severity == severity)

    return {"vulnerabilities": vulns, "total": total_query.scalar() or 0}


@router.get("/cve/{cve_id}")
def get_cve_details(cve_id: str, db: Session = Depends(get_db)):
    """Get detailed information for a specific cached CVE."""
    _ensure_schema()
    record = db.query(CveRecord).filter(CveRecord.cve_id == cve_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="CVE not found in cache")

    return {
        "cve_id": record.cve_id,
        "cvss_score": record.cvss_score,
        "severity": record.severity,
        "description": record.description,
        "affected_products": record.affected_systems.split(", ") if record.affected_systems else [],
        "attack_vector": "Network",
        "attack_complexity": "Unknown",
        "privileges_required": "Unknown",
        "user_interaction": "Unknown",
        "exploit_available": record.exploit_available,
        "exploit_maturity": "Unknown",
        "patch_available": record.patch_available,
        "patch_url": None,
        "references": [
            f"https://nvd.nist.gov/vuln/detail/{record.cve_id}",
            f"https://www.cve.org/CVERecord?id={record.cve_id}",
        ],
        "published_date": record.published_date.isoformat() if record.published_date else None,
        "last_modified": record.last_modified.isoformat() if record.last_modified else None,
        "cwe_id": "Unknown",
        "cwe_name": "Unknown",
    }


@router.get("/prioritize")
def prioritize_vulnerabilities(db: Session = Depends(get_db)):
    """Return highest-risk cached CVEs for remediation ordering."""
    _ensure_schema()
    records = db.query(CveRecord).order_by(CveRecord.risk_score.desc()).limit(10).all()
    prioritized = []
    for rec in records:
        if rec.risk_score >= 90:
            recommendation = "Immediate patching required"
            asset_criticality = "High"
        elif rec.risk_score >= 70:
            recommendation = "Patch within 24-48 hours"
            asset_criticality = "High"
        elif rec.risk_score >= 40:
            recommendation = "Patch this week"
            asset_criticality = "Medium"
        else:
            recommendation = "Schedule in maintenance window"
            asset_criticality = "Low"

        prioritized.append(
            {
                "cve_id": rec.cve_id,
                "title": rec.description[:120] + ("..." if len(rec.description) > 120 else ""),
                "cvss": rec.cvss_score,
                "asset_criticality": asset_criticality,
                "exploit_available": rec.exploit_available,
                "priority_score": rec.risk_score,
                "recommendation": recommendation,
                "affected_assets": max(1, len(rec.affected_systems.split(", ")) if rec.affected_systems else 1),
            }
        )

    return {"prioritized_vulnerabilities": prioritized}


@router.get("/stats")
def get_vulnerability_stats(db: Session = Depends(get_db)):
    """Get vulnerability statistics based on cached CVE data."""
    _ensure_schema()
    total = db.query(func.count(CveRecord.id)).scalar() or 0
    critical = db.query(func.count(CveRecord.id)).filter(CveRecord.severity == "Critical").scalar() or 0
    high = db.query(func.count(CveRecord.id)).filter(CveRecord.severity == "High").scalar() or 0
    medium = db.query(func.count(CveRecord.id)).filter(CveRecord.severity == "Medium").scalar() or 0
    low = db.query(func.count(CveRecord.id)).filter(CveRecord.severity == "Low").scalar() or 0
    patched = db.query(func.count(CveRecord.id)).filter(CveRecord.patch_available.is_(True)).scalar() or 0
    unpatched = max(0, total - patched)
    actively_exploited = db.query(func.count(CveRecord.id)).filter(CveRecord.exploit_available.is_(True)).scalar() or 0
    avg_cvss = db.query(func.avg(CveRecord.cvss_score)).scalar() or 0.0

    return {
        "total_vulnerabilities": total,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "patched": patched,
        "unpatched": unpatched,
        "actively_exploited": actively_exploited,
        "average_cvss": round(float(avg_cvss), 1),
    }


@router.get("/trending")
def get_trending_vulnerabilities(db: Session = Depends(get_db)):
    """Get recent high-risk CVEs as trending vulnerabilities."""
    _ensure_schema()
    records = (
        db.query(CveRecord)
        .order_by(CveRecord.published_date.desc(), CveRecord.risk_score.desc())
        .limit(5)
        .all()
    )

    trending = [
        {
            "cve_id": rec.cve_id,
            "title": rec.description[:100] + ("..." if len(rec.description) > 100 else ""),
            "cvss": rec.cvss_score,
            "exploit_activity": rec.risk_score,
            "trending_score": rec.risk_score,
            "first_exploited": rec.published_date.isoformat() if rec.published_date else None,
        }
        for rec in records
    ]

    return {"trending": trending}


@router.post("/scan")
async def scan_for_vulnerabilities(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Trigger CVE refresh scan from NVD."""
    result = await _fetch_cves_from_nvd(limit=50, db=db, user_id=current_user.id)
    scan_id = f"scan_{int(datetime.utcnow().timestamp())}"
    log_audit_event(
        db,
        action="vulnerabilities.scan",
        resource_type="scan",
        resource_id=scan_id,
        user_id=current_user.id,
        severity="info",
        details={"fetched": result["fetched"], "upserted": result["upserted"]},
    )
    db.commit()
    return {
        "scan_id": scan_id,
        "status": "completed",
        "fetched": result["fetched"],
        "upserted": result["upserted"],
        "targets": result["total_cached"],
    }


@router.get("/scan/{scan_id}")
def get_scan_status(scan_id: str):
    """Get vulnerability scan status."""
    return {
        "scan_id": scan_id,
        "status": "completed",
        "progress": 100,
        "vulnerabilities_found": 0,
        "started_at": datetime.utcnow().isoformat(),
    }
