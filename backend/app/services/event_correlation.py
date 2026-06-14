from datetime import datetime


def generate_attack_chains(db):
    attack_chains = []

    phishing_events = list(
        db["scans"].find(
            {"scan_type": "phishing"}
        ).sort("created_at", -1)
    )

    malware_events = list(
        db["scans"].find(
            {"scan_type": "malware"}
        ).sort("created_at", -1)
    )

    cves = list(
        db["cve_records"]
        .find({"severity": {"$in": ["Critical", "High"]}})
        .sort("risk_score", -1)
        .limit(20)
    )

    critical_cves = [
        cve for cve in cves
        if cve.get("severity") == "Critical"
    ]

    if (
        phishing_events
        and malware_events
        and critical_cves
    ):

        # Calculate dynamic risk score
        risk_score = 0

        risk_score += min(
            len(phishing_events) * 10,
            30
        )

        risk_score += min(
            len(malware_events) * 15,
            40
        )

        risk_score += min(
            len(critical_cves) * 5,
            30
        )

        risk_score = min(risk_score, 100)

        # Calculate severity
        if risk_score >= 80:
            severity = "Critical"
        elif risk_score >= 60:
            severity = "High"
        elif risk_score >= 40:
            severity = "Medium"
        else:
            severity = "Low"

        attack_chains.append(
        {
            "chain_id": "CHAIN-001",

            "risk_score": risk_score,
            "severity": severity,

            "phishing_count": len(phishing_events),
            "malware_count": len(malware_events),
            "critical_cve_count": len(critical_cves),

            "stages": [
                "Initial Access (Phishing)",
                "Execution (Malware)",
                "Vulnerability Exposure",
            ],

            "description": (
                "Correlated phishing, malware and vulnerability events indicate a potential attack path.",
            ),

            "created_at": datetime.utcnow().isoformat(),
        }
    )

    return attack_chains