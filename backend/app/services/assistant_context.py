import re
import json
from datetime import datetime
from typing import Any

from pymongo.database import Database


def _safe_json_loads(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def get_security_summary(db: Database) -> dict[str, Any]:
    total_cves = db["cve_records"].count_documents({})
    critical_cves = db["cve_records"].count_documents({"severity": "Critical"})
    high_cves = db["cve_records"].count_documents({"severity": "High"})
    phishing_scans = db["scans"].count_documents({"scan_type": "phishing"})
    malware_scans = db["scans"].count_documents({"scan_type": "malware"})

    latest_cves = list(db["cve_records"].find().sort("risk_score", -1).limit(3))
    latest_phishing = list(db["scans"].find({"scan_type": "phishing"}).sort("created_at", -1).limit(3))

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cve": {
            "total": total_cves,
            "critical": critical_cves,
            "high": high_cves,
            "top": [
                {
                    "cve_id": cve.get("cve_id"),
                    "severity": cve.get("severity"),
                    "risk_score": cve.get("risk_score"),
                    "summary": (cve.get("description") or "")[:160]
                    + ("..." if len(cve.get("description") or "") > 160 else ""),
                }
                for cve in latest_cves
            ],
        },
        "scans": {
            "phishing_total": phishing_scans,
            "malware_total": malware_scans,
            "recent_phishing": [
                {
                    "score": scan.get("score"),
                    "created_at": scan.get("created_at").isoformat()
                    if hasattr(scan.get("created_at"), "isoformat")
                    else str(scan.get("created_at")),
                    "result": _safe_json_loads(scan.get("result")),
                }
                for scan in latest_phishing
            ],
        },
    }


def build_security_response(message: str, db: Database) -> tuple[str, list[str]]:
    text = message.lower().strip()
    summary = get_security_summary(db)

    match = re.search(
        r"(CVE-\d{4}-\d+)",
        message,
        re.IGNORECASE
    )

    if match and any(
        word in text
        for word in ["explain", "details", "describe", "tell me about"]
    ):
        cve_id = match.group(1).upper()

        cve = db["cve_records"].find_one({
            "cve_id": cve_id
        })
        print("MATCHED CVE:", cve_id)
        print("FOUND:", cve)

        if cve:
            response = f"""{cve_id}

            Severity: {cve.get('severity')}

            CVSS Score: {cve.get('cvss_score')}

            Risk Score: {cve.get('risk_score')}

            Description:
            {cve.get('description')}

            Recommendation:
            Apply available patches immediately and review affected systems.
            """

            return (
                response,
                [
                    "What should I patch first?",
                    "Show top critical CVEs",
                    "Summarize vulnerabilities"
                ]
            )
        else:
            return (
                f"{cve_id} was not found in the local CVE cache.",
                [
                    "Show top critical CVEs",
                    "What should I patch first?",
                    "Summarize vulnerabilities"
                ]
            )

    if "patch" in text:
            top_cves = list(
                db["cve_records"]
                .find()
                .sort("risk_score", -1)
                .limit(5)
            )

            lines = [
                "**Patch Priority List**",
                ""
            ]

            for i, cve in enumerate(top_cves, 1):
                lines.append(
                    f"{i}. {cve.get('cve_id')} "
                    f"(CVSS {cve.get('cvss_score')}, "
                    f"Risk {cve.get('risk_score')})"
                )

            return (
                "\n".join(lines),
                [
                    "Explain top CVE",
                    "Show critical vulnerabilities",
                    "Security summary"
                ]
            )

    if any(token in text for token in ["cve", "vulnerability"]):
        top = summary["cve"]["top"]
        if top:
            lines = ["**Vulnerability Analysis**", ""]
            for index, item in enumerate(top, start=1):
                lines.extend(
                    [
                        f"{index}. **{item['cve_id']}** ({item['severity']}, risk {item['risk_score']})",
                        f"   - {item['summary']}",
                    ]
                )
            lines.extend(
                [
                    "",
                    "**Recommendation**: Prioritize the top critical/high-risk CVEs and patch exposed systems first.",
                ]
            )
            suggestions = [
                f"Explain {top[0]['cve_id']} in simple terms",
                "What should I patch first?",
                "Show me the top 3 vulnerabilities",
            ]
            return "\n".join(lines), suggestions

        return (
            "No CVE data is cached yet. Use the vulnerability dashboard to fetch from NVD first.",
            ["Fetch latest CVEs", "Show me how to refresh the dashboard"],
        )
    
    if any(token in text for token in [
        "malware",
        "virus",
        "trojan",
        "ransomware"
    ]):
        scans = list(
            db["scans"]
            .find({"scan_type": "malware"})
            .sort("created_at", -1)
            .limit(5)
        )

        lines = [
            "**Malware Analysis Summary**",
            ""
        ]

        for scan in scans:

            lines.append(
                f"- {scan.get('file_name')} | "
                f"{scan.get('verdict')} | "
                f"{scan.get('threat_level')}"
            )

        return (
            "\n".join(lines),
            [
                "Show recent malware detections",
                "How many malicious files were found?",
                "Give security summary"
            ]
        )

    if any(token in text for token in ["phishing", "email", "url"]):
        total = summary["scans"]["phishing_total"]
        recent = summary["scans"]["recent_phishing"]
        blocked = sum(1 for scan in recent if scan.get("result", {}).get("is_phishing"))
        lines = [
            "**Phishing Detection Summary**",
            "",
            f"- Total phishing scans stored: {total}",
            f"- Recent blocked detections: {blocked}",
            "- Model-driven analysis with explainable indicators",
            "",
            "**Recent Examples:**",
        ]
        for item in recent[:3]:
            result = item.get("result") or {}
            lines.append(
                f"- Score {item.get('score', 0)}% | {result.get('risk_level', 'Low')} | {result.get('detected_indicators', [])[:2]}"
            )
        suggestions = [
            "Analyze this email for phishing",
            "Show my recent phishing scans",
            "How does the phishing model explain detections?",
        ]
        return "\n".join(lines), suggestions

    if any(token in text for token in [
        "threat",
        "risk",
        "summary",
        "secure",
        "security posture"
    ]):
        rating = "Low Risk"

        if summary["cve"]["critical"] > 0:
            rating = "High Risk"

        elif summary["cve"]["high"] > 3:
            rating = "Moderate Risk"

        lines = [
            "**Security Posture Assessment**",
            "",
            f"Critical CVEs: {summary['cve']['critical']}",
            f"High CVEs: {summary['cve']['high']}",
            f"Malware Scans: {summary['scans']['malware_total']}",
            f"Phishing Scans: {summary['scans']['phishing_total']}",
            "",
            f"Overall Rating: {rating}",
            "",
            "Recommendations:",
            "- Patch critical CVEs",
            "- Review malware detections",
            "- Monitor phishing activity",
        ]
        suggestions = [
            "Show me top critical CVEs",
            "Summarize recent phishing scans",
            "What should I patch first?",
        ]
        return "\n".join(lines), suggestions

    return (
        "I can summarize cached CVEs, recent phishing scans, and remediation priorities. Ask me about CVEs, phishing, or your threat summary.",
        [
            "Show me the security summary",
            "Explain the top CVEs",
            "Summarize recent phishing detections",
        ],
    )
