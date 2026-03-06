"""
Dashboard Endpoints - Overview and Analytics
"""

from fastapi import APIRouter
from typing import List, Dict
from datetime import datetime, timedelta
import random

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """
    Get overall security statistics for dashboard
    """
    return {
        "total_threats_today": random.randint(10, 20),
        "critical_alerts": random.randint(1, 5),
        "phishing_attempts": random.randint(5, 15),
        "malware_detected": random.randint(2, 8),
        "vulnerabilities_found": random.randint(15, 30),
        "risk_score": random.randint(60, 85),
        "last_updated": datetime.now().isoformat()
    }


@router.get("/recent-threats")
async def get_recent_threats():
    """
    Get recent threat detections
    """
    threat_types = ["Malware", "Phishing", "Suspicious Activity", "Vulnerability"]
    severities = ["Critical", "High", "Medium", "Low"]
    
    threats = []
    for i in range(10):
        threats.append({
            "id": f"threat_{i+1}",
            "type": random.choice(threat_types),
            "severity": random.choice(severities),
            "description": f"Detected {random.choice(threat_types).lower()} attempt",
            "source_ip": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat(),
            "status": random.choice(["Blocked", "Quarantined", "Under Investigation"])
        })
    
    return {"threats": threats}


@router.get("/threat-timeline")
async def get_threat_timeline():
    """
    Get threat detection timeline for charts
    """
    timeline = []
    for i in range(24):
        hour = datetime.now() - timedelta(hours=23-i)
        timeline.append({
            "timestamp": hour.isoformat(),
            "malware": random.randint(0, 5),
            "phishing": random.randint(0, 8),
            "vulnerabilities": random.randint(0, 3),
            "other": random.randint(0, 2)
        })
    
    return {"timeline": timeline}


@router.get("/threat-distribution")
async def get_threat_distribution():
    """
    Get threat type distribution for pie charts
    """
    return {
        "distribution": [
            {"name": "Phishing", "value": random.randint(30, 40), "color": "#ef4444"},
            {"name": "Malware", "value": random.randint(20, 30), "color": "#f59e0b"},
            {"name": "Vulnerabilities", "value": random.randint(15, 25), "color": "#eab308"},
            {"name": "Suspicious Activity", "value": random.randint(10, 20), "color": "#3b82f6"}
        ]
    }


@router.get("/geographic-threats")
async def get_geographic_threats():
    """
    Get geographic distribution of threats
    """
    countries = ["USA", "China", "Russia", "Brazil", "India", "Germany", "UK"]
    
    geo_data = []
    for country in countries:
        geo_data.append({
            "country": country,
            "threat_count": random.randint(5, 50),
            "severity": random.choice(["High", "Medium", "Low"])
        })
    
    return {"geographic_data": geo_data}


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
