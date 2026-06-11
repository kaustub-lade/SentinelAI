import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.core.auth_utils import require_roles
from app.core.database import get_db

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: Database = Depends(get_db),
):
    """
    Get overall security statistics for dashboard
    """

    total_scans = db["scans"].count_documents({})

    malware_detected = db["scans"].count_documents(
        {
            "scan_type": "malware",
            "verdict": {"$in": ["Malicious", "Suspicious"]},
        }
    )

    critical_alerts = db["scans"].count_documents(
        {
            "threat_level": {"$in": ["Critical", "High"]},
        }
    )

    risk_score = min(
        100,
        malware_detected * 10 + critical_alerts * 5,
    )

    phishing_attempts = db["scans"].count_documents(
    {"scan_type": "phishing"}
    )

    vulnerabilities_found = db["cve_records"].count_documents({})

    return {
        "total_threats_today": total_scans,
        "critical_alerts": critical_alerts,
        "phishing_attempts": phishing_attempts,
        "vulnerabilities_found": vulnerabilities_found,
        "malware_detected": malware_detected,
        "risk_score": risk_score,
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/recent-threats")
async def get_recent_threats( 
    db: Database = Depends(get_db),
):
    """
    Get recent threat detections
    """

    scans = list(
        db["scans"]
        .find()
        .sort("created_at", -1)
        .limit(20)
    )

    threats = []

    for scan in scans:
        created_at = scan.get("created_at")

        threat_type = (
            "Phishing"
            if scan.get("scan_type") == "phishing"
            else "Malware"
        )

        verdict = str(scan.get("verdict", "")).lower()

        if "malicious" in verdict:
            severity = "Critical"
        elif "suspicious" in verdict:
            severity = "High"
        else:
            severity = "Low"

        threats.append(
            {
                "id": str(scan.get("_id")),
                "type": threat_type,
                "severity": severity,
                "description": f"{threat_type} analysis completed",
                "source_ip": "N/A",
                "timestamp": (
                    created_at.isoformat()
                    if hasattr(created_at, "isoformat")
                    else str(created_at)
                ),
                "status": (
                    "Blocked"
                    if severity in ["Critical", "High"]
                    else "Allowed"
                ),
            }
        )

    return {"threats": threats}


@router.get("/threat-timeline")
async def get_threat_timeline(
    db: Database = Depends(get_db),
):
    """
    Get threat detection timeline for charts
    """

    timeline = []

    for i in range(7):

        day_start = (
            datetime.now()
            - timedelta(days=6 - i)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        day_end = day_start + timedelta(days=1)

        malware_count = db["scans"].count_documents(
            {
                "scan_type": "malware",
                "created_at": {
                    "$gte": day_start,
                    "$lt": day_end,
                },
            }
        )

        phishing_count = db["scans"].count_documents(
            {
                "scan_type": "phishing",
                "created_at": {
                    "$gte": day_start,
                    "$lt": day_end,
                },
            }
        )

        timeline.append(
            {
                "timestamp": day_start.strftime("%Y-%m-%d"),
                "malware": malware_count,
                "phishing": phishing_count,
                "vulnerabilities": 0,
                "other": 0,
            }
        )

    return {"timeline": timeline}


@router.get("/threat-distribution")
async def get_threat_distribution(
    db: Database = Depends(get_db),
):
    """
    Get threat type distribution for pie charts
    """

    critical_count = db["scans"].count_documents(
    {"threat_level": "Critical"}
    )

    high_count = db["scans"].count_documents(
        {"threat_level": "High"}
    )

    medium_count = db["scans"].count_documents(
        {"threat_level": "Medium"}
    )

    low_count = db["scans"].count_documents(
        {"threat_level": "Low"}
    )

    return {
        "distribution": [
            {
                "name": "Critical",
                "value": critical_count,
                "color": "#dc2626",
            },
            {
                "name": "High",
                "value": high_count,
                "color": "#ea580c",
            },
            {
                "name": "Medium",
                "value": medium_count,
                "color": "#ca8a04",
            },
            {
                "name": "Low",
                "value": low_count,
                "color": "#16a34a",
            },
        ]
    }


@router.get("/geographic-threats")
async def get_geographic_threats(
    db: Database = Depends(get_db),
):
    return {
        "geographic_data": [
            {
                "country": "Critical",
                "threat_count": db["scans"].count_documents(
                    {"threat_level": "Critical"}
                ),
                "severity": "Critical",
            },
            {
                "country": "High",
                "threat_count": db["scans"].count_documents(
                    {"threat_level": "High"}
                ),
                "severity": "High",
            },
            {
                "country": "Medium",
                "threat_count": db["scans"].count_documents(
                    {"threat_level": "Medium"}
                ),
                "severity": "Medium",
            },
            {
                "country": "Low",
                "threat_count": db["scans"].count_documents(
                    {"threat_level": "Low"}
                ),
                "severity": "Low",
            },
        ]
    }


@router.get("/system-health")
async def get_system_health():
    """
    Get system health metrics
    """
    return {
        "detection_engine": "operational",
        "ai_models": "operational",
        "database": "operational",
        "api_services": "operational",
        "uptime_percentage": 99.8,
        "last_scan": datetime.now().isoformat()
    }


@router.get("/activity")
async def get_recent_activity(
    db: Database = Depends(get_db),
    current_user=Depends(require_roles("admin", "analyst")),
):
    """Get recent audit events for the dashboard."""
    events = list(db["audit_logs"].find().sort("created_at", -1).limit(8))

    activity = []
    for event in events:
        created_at = event.get("created_at")
        activity.append({
            "id": str(event.get("_id")),
            "action": event.get("action"),
            "resource_type": event.get("resource_type"),
            "resource_id": event.get("resource_id"),
            "status": event.get("status"),
            "severity": event.get("severity"),
            "details": event.get("details"),
            "timestamp": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
        })

    return {"activity": activity}
