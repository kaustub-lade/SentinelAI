"""
Vulnerability Intelligence Endpoints - CVE Analysis & Prioritization
"""

from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.core.auth_utils import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.services.audit import log_audit_event

router = APIRouter()


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
    db: Database = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Fetch latest CVEs from NVD and cache/update in database."""
    return await _fetch_cves_from_nvd(limit=limit, db=db, user_id=current_user["id"])


async def _fetch_cves_from_nvd(limit: int, db: Database, user_id: str | None = None):
    """Internal CVE fetch helper used by refresh and scan routes."""
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

        db["cve_records"].update_one(
            {"cve_id": cve_id},
            {
                "$set": {
                    "description": description,
                    "severity": severity,
                    "cvss_score": cvss_score,
                    "affected_systems": affected_systems,
                    "exploit_available": "exploit" in description.lower(),
                    "patch_available": True,
                    "risk_score": risk_score,
                    "published_date": _to_datetime(cve_obj.get("published")),
                    "last_modified": _to_datetime(cve_obj.get("lastModified")),
                }
            },
            upsert=True,
        )
        upserted += 1

    log_audit_event(
        db,
        action="vulnerabilities.fetch_nvd",
        resource_type="cve_cache",
        user_id=user_id,
        status="success",
        severity="info",
        details={"fetched": len(vulnerabilities), "upserted": upserted},
    )

    return {
        "fetched": len(vulnerabilities),
        "upserted": upserted,
        "total_cached": db["cve_records"].count_documents({}),
    }


@router.get("/list")
def get_vulnerabilities(
    severity: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Database = Depends(get_db),
):
    """Get vulnerabilities cached in DB (fetched from NVD)."""
    filters = {"severity": severity} if severity else {}
    records = list(db["cve_records"].find(filters).sort("risk_score", -1).limit(limit))
    vulns = [
        {
            "cve_id": rec.get("cve_id"),
            "cvss_score": rec.get("cvss_score"),
            "severity": rec.get("severity"),
            "description": rec.get("description"),
            "affected_systems": (rec.get("affected_systems") or "").split(", ") if rec.get("affected_systems") else [],
            "exploit_available": rec.get("exploit_available", False),
            "patch_available": rec.get("patch_available", False),
            "risk_score": rec.get("risk_score", 0),
            "published_date": rec.get("published_date").isoformat() if rec.get("published_date") else None,
            "last_modified": rec.get("last_modified").isoformat() if rec.get("last_modified") else None,
        }
        for rec in records
    ]
    return {"vulnerabilities": vulns, "total": db["cve_records"].count_documents(filters)}


@router.get("/cve/{cve_id}")
def get_cve_details(cve_id: str, db: Database = Depends(get_db)):
    """Get detailed information for a specific cached CVE."""
    record = db["cve_records"].find_one({"cve_id": cve_id})
    if record is None:
        raise HTTPException(status_code=404, detail="CVE not found in cache")

    return {
        "cve_id": record.get("cve_id"),
        "cvss_score": record.get("cvss_score"),
        "severity": record.get("severity"),
        "description": record.get("description"),
        "affected_products": (record.get("affected_systems") or "").split(", ") if record.get("affected_systems") else [],
        "attack_vector": "Network",
        "attack_complexity": "Unknown",
        "privileges_required": "Unknown",
        "user_interaction": "Unknown",
        "exploit_available": record.get("exploit_available", False),
        "exploit_maturity": "Unknown",
        "patch_available": record.get("patch_available", False),
        "patch_url": None,
        "references": [
            f"https://nvd.nist.gov/vuln/detail/{record.get('cve_id')}",
            f"https://www.cve.org/CVERecord?id={record.get('cve_id')}",
        ],
        "published_date": record.get("published_date").isoformat() if record.get("published_date") else None,
        "last_modified": record.get("last_modified").isoformat() if record.get("last_modified") else None,
        "cwe_id": "Unknown",
        "cwe_name": "Unknown",
    }


@router.get("/prioritize")
def prioritize_vulnerabilities(db: Database = Depends(get_db)):
    """Return highest-risk cached CVEs for remediation ordering."""
    records = list(db["cve_records"].find().sort("risk_score", -1).limit(10))
    prioritized = []
    for rec in records:
        risk_score = rec.get("risk_score", 0)
        if risk_score >= 90:
            recommendation = "Immediate patching required"
            asset_criticality = "High"
        elif risk_score >= 70:
            recommendation = "Patch within 24-48 hours"
            asset_criticality = "High"
        elif risk_score >= 40:
            recommendation = "Patch this week"
            asset_criticality = "Medium"
        else:
            recommendation = "Schedule in maintenance window"
            asset_criticality = "Low"

        prioritized.append(
            {
                "cve_id": rec.get("cve_id"),
                "title": (rec.get("description") or "")[:120] + ("..." if len(rec.get("description") or "") > 120 else ""),
                "cvss": rec.get("cvss_score"),
                "asset_criticality": asset_criticality,
                "exploit_available": rec.get("exploit_available", False),
                "priority_score": risk_score,
                "recommendation": recommendation,
                "affected_assets": max(1, len((rec.get("affected_systems") or "").split(", ")) if rec.get("affected_systems") else 1),
            }
        )

    return {"prioritized_vulnerabilities": prioritized}


@router.get("/stats")
def get_vulnerability_stats(db: Database = Depends(get_db)):
    """Get vulnerability statistics based on cached CVE data."""
    total = db["cve_records"].count_documents({})
    critical = db["cve_records"].count_documents({"severity": "Critical"})
    high = db["cve_records"].count_documents({"severity": "High"})
    medium = db["cve_records"].count_documents({"severity": "Medium"})
    low = db["cve_records"].count_documents({"severity": "Low"})
    patched = db["cve_records"].count_documents({"patch_available": True})
    unpatched = max(0, total - patched)
    actively_exploited = db["cve_records"].count_documents({"exploit_available": True})
    cvss_values = [rec.get("cvss_score", 0.0) for rec in db["cve_records"].find({}, {"cvss_score": 1})]
    avg_cvss = (sum(cvss_values) / len(cvss_values)) if cvss_values else 0.0

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
def get_trending_vulnerabilities(db: Database = Depends(get_db)):
    """Get recent high-risk CVEs as trending vulnerabilities."""
    records = list(db["cve_records"].find().sort([("published_date", -1), ("risk_score", -1)]).limit(5))

    trending = [
        {
            "cve_id": rec.get("cve_id"),
            "title": (rec.get("description") or "")[:100] + ("..." if len(rec.get("description") or "") > 100 else ""),
            "cvss": rec.get("cvss_score"),
            "exploit_activity": rec.get("risk_score", 0),
            "trending_score": rec.get("risk_score", 0),
            "first_exploited": rec.get("published_date").isoformat() if rec.get("published_date") else None,
        }
        for rec in records
    ]

    return {"trending": trending}


@router.post("/scan")
async def scan_for_vulnerabilities(
    db: Database = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Trigger CVE refresh scan from NVD."""
    result = await _fetch_cves_from_nvd(limit=50, db=db, user_id=current_user["id"])
    scan_id = f"scan_{int(datetime.utcnow().timestamp())}"
    log_audit_event(
        db,
        action="vulnerabilities.scan",
        resource_type="scan",
        resource_id=scan_id,
        user_id=current_user["id"],
        severity="info",
        details={"fetched": result["fetched"], "upserted": result["upserted"]},
    )
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
