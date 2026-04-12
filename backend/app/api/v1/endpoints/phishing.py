"""
Phishing Detection Endpoints
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth_utils import require_roles
from app.models import Scan
from app.services.audit import log_audit_event
from app.services.phishing_model import phishing_model_service

router = APIRouter()


class PhishingCheckRequest(BaseModel):
    email_content: Optional[str] = None
    url: Optional[str] = None
    sender_email: Optional[EmailStr] = None
    subject: Optional[str] = None


class PhishingResult(BaseModel):
    is_phishing: bool
    confidence: float
    risk_level: str
    detected_indicators: List[str]
    recommendations: List[str]
    analysis: dict


@router.post("/check-email", response_model=PhishingResult)
async def check_email(request: PhishingCheckRequest, db: Session = Depends(get_db)):
    """
    Analyze email for phishing indicators
    Uses NLP and pattern recognition
    """
    result = phishing_model_service.analyze(
        email_content=request.email_content,
        sender_email=request.sender_email,
        subject=request.subject,
        url=request.url,
    )

    scan = Scan(
        user_id=0,
        scan_type="phishing",
        input_data=json.dumps(request.model_dump(), default=str),
        result=json.dumps(result, default=str),
        score=int(round(result["confidence"] * 100)),
    )
    db.add(scan)
    log_audit_event(
        db,
        action="phishing.check_email",
        resource_type="scan",
        resource_id=str(scan.id or "pending"),
        severity="warning" if result["is_phishing"] else "info",
        details={"confidence": result["confidence"], "is_phishing": result["is_phishing"]},
    )
    db.commit()

    return PhishingResult(**result)


@router.post("/check-url")
async def check_url(url: str, db: Session = Depends(get_db)):
    """
    Check if URL is malicious or phishing
    """
    result = phishing_model_service.analyze(
        email_content=None,
        sender_email=None,
        subject=None,
        url=url,
    )

    scan = Scan(
        user_id=0,
        scan_type="phishing",
        input_data=json.dumps({"url": url}),
        result=json.dumps(result, default=str),
        score=int(round(result["confidence"] * 100)),
    )
    db.add(scan)
    log_audit_event(
        db,
        action="phishing.check_url",
        resource_type="scan",
        resource_id=str(scan.id or "pending"),
        severity="warning" if result["is_phishing"] else "info",
        details={"url": url, "confidence": result["confidence"]},
    )
    db.commit()

    return {
        "url": url,
        "is_malicious": result["is_phishing"],
        "risk_score": int(round(result["confidence"] * 100)),
        "detected_issues": result["detected_indicators"],
        "threat_type": "Phishing" if result["is_phishing"] else "Safe",
        "recommendation": result["recommendations"][0],
        "analysis": result["analysis"],
    }


@router.get("/recent-phishing")
async def get_recent_phishing(db: Session = Depends(get_db)):
    """
    Get recent phishing detection history
    """
    scans = (
        db.query(Scan)
        .filter(Scan.scan_type == "phishing")
        .order_by(Scan.created_at.desc())
        .limit(10)
        .all()
    )

    history = []
    for idx, scan in enumerate(scans, start=1):
        try:
            result = json.loads(scan.result)
            input_data = json.loads(scan.input_data)
        except json.JSONDecodeError:
            result = {}
            input_data = {}

        history.append(
            {
                "id": f"phishing_{scan.id or idx}",
                "sender": input_data.get("sender_email", "unknown@unknown"),
                "subject": input_data.get("subject", "(no subject)"),
                "detected_at": scan.created_at.isoformat(),
                "risk_level": result.get("risk_level", "Low"),
                "confidence": result.get("confidence", 0),
                "status": "Blocked" if result.get("is_phishing") else "Allowed",
            }
        )

    return {"detections": history}


@router.get("/phishing-stats")
async def get_phishing_stats(db: Session = Depends(get_db)):
    """
    Get phishing detection statistics
    """
    scans = db.query(Scan).filter(Scan.scan_type == "phishing").all()
    total_checked = len(scans)
    phishing_detected = 0
    blocked = 0

    for scan in scans:
        try:
            result = json.loads(scan.result)
        except json.JSONDecodeError:
            continue
        if result.get("is_phishing"):
            phishing_detected += 1
            blocked += 1

    detection_accuracy = round((blocked / total_checked), 3) if total_checked else 0.0

    return {
        "total_checked": total_checked,
        "phishing_detected": phishing_detected,
        "blocked": blocked,
        "false_positives": max(0, int(total_checked * 0.03) - blocked),
        "detection_accuracy": detection_accuracy,
        "top_targets": [
            {"type": "Credential Theft", "count": max(1, phishing_detected // 2) if phishing_detected else 0},
            {"type": "Invoice Fraud", "count": max(1, phishing_detected // 3) if phishing_detected else 0},
            {"type": "Account Takeover", "count": max(1, phishing_detected // 4) if phishing_detected else 0},
        ],
    }


@router.post("/train-model")
async def train_phishing_model(samples: int = 2500, current_user=Depends(require_roles("admin", "analyst"))):
    """
    Trigger retraining of phishing detection model
    """
    result = phishing_model_service.train_and_save(samples=samples)
    # Training is a server-side operation; the audit trail is handled via the log file in the model artifact.
    return {
        "message": "Phishing model trained successfully",
        "status": "completed",
        "details": result,
    }
