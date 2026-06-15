from fastapi import APIRouter, Depends
from pymongo.database import Database
from bson import ObjectId
from app.core.database import get_db
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/")
async def get_alerts(
    db: Database = Depends(get_db)
):
    alerts = list(
        db["alerts"]
        .find()
        .sort("created_at", -1)
        .limit(50)
    )

    results = []

    for alert in alerts:

        results.append(
            {
                "id": str(alert["_id"]),
                "severity": alert["severity"],
                "title": alert["title"],
                "description": alert["description"],
                "source": alert["source"],
                "status": alert["status"],
                "created_at": alert["created_at"],
            }
        )

    return {
        "alerts": results
    }

@router.get("/summary")
async def get_alert_summary(
    db: Database = Depends(get_db)
):
    return {
        "total": db["alerts"].count_documents({}),
        "critical": db["alerts"].count_documents(
            {"severity": "Critical"}
        ),
        "high": db["alerts"].count_documents(
            {"severity": "High"}
        ),
        "open": db["alerts"].count_documents(
            {"status": "Open"}
        ),
    }

@router.get("/trends")
async def get_alert_trends(
    db: Database = Depends(get_db)
):
    trend_data = []

    for i in range(6, -1, -1):

        date = (
            datetime.utcnow()
            - timedelta(days=i)
        )

        start = datetime(
            date.year,
            date.month,
            date.day
        )

        end = start + timedelta(days=1)

        count = db["alerts"].count_documents(
            {
                "created_at": {
                    "$gte": start,
                    "$lt": end
                }
            }
        )

        trend_data.append(
            {
                "date": start.strftime("%d %b"),
                "alerts": count
            }
        )

    return {
        "trend": trend_data
    }

@router.put("/{alert_id}/status")
async def update_alert_status(
    alert_id: str,
    status: str,
    db: Database = Depends(get_db)
):
    status_map = {
        "open": "Open",
        "investigating": "Investigating",
        "resolved": "Resolved",
        "false positive": "False Positive",
    }

    status = status_map.get(
        status.lower().strip()
    )

    if not status:
        return {
            "success": False,
            "message": "Invalid status"
        }

    result = db["alerts"].update_one(
        {
            "_id": ObjectId(alert_id)
        },
        {
            "$set": {
                "status": status
            }
        }
    )

    return {
        "success": result.modified_count > 0,
        "status": status
    }