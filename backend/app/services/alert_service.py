from datetime import datetime

def create_alert(
    db,
    severity: str,
    title: str,
    description: str,
    source: str,
):
    alert = {
        "severity": severity,
        "title": title,
        "description": description,
        "source": source,
        "status": "Open",
        "created_at": datetime.utcnow(),
    }

    db["alerts"].insert_one(alert)

