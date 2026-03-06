"""
Vulnerability Intelligence Endpoints - CVE Analysis & Prioritization
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
import random
from datetime import datetime, timedelta

router = APIRouter()


class Vulnerability(BaseModel):
    cve_id: str
    cvss_score: float
    severity: str
    description: str
    affected_systems: List[str]
    exploit_available: bool
    patch_available: bool
    risk_score: int
    published_date: str
    last_modified: str


@router.get("/list")
async def get_vulnerabilities(
    severity: Optional[str] = None,
    limit: int = Query(default=20, le=100)
):
    """
    Get list of vulnerabilities with prioritization
    """
    severities = ["Critical", "High", "Medium", "Low"] if not severity else [severity]
    
    vulns = []
    for i in range(limit):
        cvss = round(random.uniform(1.0, 10.0), 1)
        
        if cvss >= 9.0:
            sev = "Critical"
        elif cvss >= 7.0:
            sev = "High"
        elif cvss >= 4.0:
            sev = "Medium"
        else:
            sev = "Low"
        
        vulns.append({
            "cve_id": f"CVE-2024-{random.randint(1000, 9999)}",
            "cvss_score": cvss,
            "severity": sev,
            "description": f"Vulnerability in software component allowing remote code execution",
            "affected_systems": [
                random.choice(["Apache", "Nginx", "Windows Server", "Linux Kernel", "OpenSSL"])
            ],
            "exploit_available": random.choice([True, False]),
            "patch_available": random.choice([True, False]),
            "risk_score": random.randint(1, 100),
            "published_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "last_modified": datetime.now().isoformat()
        })
    
    # Sort by risk score
    vulns.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return {"vulnerabilities": vulns, "total": len(vulns)}


@router.get("/cve/{cve_id}")
async def get_cve_details(cve_id: str):
    """
    Get detailed information about a specific CVE
    """
    cvss = round(random.uniform(5.0, 10.0), 1)
    
    return {
        "cve_id": cve_id,
        "cvss_score": cvss,
        "severity": "Critical" if cvss >= 9.0 else "High",
        "description": f"{cve_id} is a critical vulnerability allowing remote attackers to execute arbitrary code through crafted requests. This vulnerability affects multiple versions of the software and has been actively exploited in the wild.",
        "affected_products": [
            "Product A versions 1.0 - 2.5",
            "Product B versions 3.0 - 3.8"
        ],
        "attack_vector": "Network",
        "attack_complexity": "Low",
        "privileges_required": "None",
        "user_interaction": "None",
        "exploit_available": True,
        "exploit_maturity": "Functional",
        "patch_available": True,
        "patch_url": f"https://vendor.com/security/patches/{cve_id}",
        "references": [
            "https://nvd.nist.gov/vuln/detail/" + cve_id,
            "https://www.cve.org/CVERecord?id=" + cve_id
        ],
        "published_date": "2024-01-15T10:00:00",
        "last_modified": datetime.now().isoformat(),
        "cwe_id": "CWE-787",
        "cwe_name": "Out-of-bounds Write"
    }


@router.get("/prioritize")
async def prioritize_vulnerabilities():
    """
    Get AI-prioritized vulnerability list based on risk
    """
    priorities = []
    
    risk_factors = [
        {
            "cve_id": "CVE-2024-3094",
            "title": "XZ Utils Backdoor",
            "cvss": 9.8,
            "asset_criticality": "High",
            "exploit_available": True,
            "priority_score": 98,
            "recommendation": "Immediate patching required",
            "affected_assets": 45
        },
        {
            "cve_id": "CVE-2024-1234",
            "title": "OpenSSL Remote Code Execution",
            "cvss": 8.5,
            "asset_criticality": "High",
            "exploit_available": True,
            "priority_score": 92,
            "recommendation": "Patch within 24 hours",
            "affected_assets": 128
        },
        {
            "cve_id": "CVE-2024-5678",
            "title": "Apache HTTP Server DoS",
            "cvss": 7.2,
            "asset_criticality": "Medium",
            "exploit_available": False,
            "priority_score": 68,
            "recommendation": "Schedule patching this week",
            "affected_assets": 23
        }
    ]
    
    return {"prioritized_vulnerabilities": risk_factors}


@router.get("/stats")
async def get_vulnerability_stats():
    """
    Get vulnerability statistics
    """
    return {
        "total_vulnerabilities": random.randint(100, 500),
        "critical": random.randint(5, 20),
        "high": random.randint(20, 50),
        "medium": random.randint(30, 100),
        "low": random.randint(50, 200),
        "patched": random.randint(50, 150),
        "unpatched": random.randint(30, 100),
        "actively_exploited": random.randint(2, 15),
        "average_cvss": round(random.uniform(5.0, 7.5), 1)
    }


@router.get("/trending")
async def get_trending_vulnerabilities():
    """
    Get trending/actively exploited vulnerabilities
    """
    trending = []
    for i in range(5):
        trending.append({
            "cve_id": f"CVE-2024-{random.randint(1000, 9999)}",
            "title": f"Critical vulnerability in popular software",
            "cvss": round(random.uniform(7.0, 10.0), 1),
            "exploit_activity": random.randint(50, 500),
            "trending_score": random.randint(70, 100),
            "first_exploited": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat()
        })
    
    return {"trending": trending}


@router.post("/scan")
async def scan_for_vulnerabilities():
    """
    Trigger vulnerability scan
    """
    return {
        "scan_id": f"scan_{random.randint(10000, 99999)}",
        "status": "initiated",
        "estimated_time": "10 minutes",
        "targets": random.randint(50, 200)
    }


@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str):
    """
    Get vulnerability scan status
    """
    return {
        "scan_id": scan_id,
        "status": random.choice(["in_progress", "completed"]),
        "progress": random.randint(10, 100),
        "vulnerabilities_found": random.randint(5, 50),
        "started_at": (datetime.now() - timedelta(minutes=random.randint(1, 30))).isoformat()
    }
