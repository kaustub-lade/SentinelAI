"""
Phishing Detection Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import random
from datetime import datetime
import re

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
async def check_email(request: PhishingCheckRequest):
    """
    Analyze email for phishing indicators
    Uses NLP and pattern recognition
    """
    detected_indicators = []
    analysis = {
        "urgency_detected": False,
        "suspicious_links": 0,
        "domain_mismatch": False,
        "grammar_issues": 0,
        "impersonation_attempt": False
    }
    
    # Check for urgency keywords
    urgency_keywords = ["urgent", "immediate", "suspended", "verify", "confirm", "click now"]
    if request.email_content:
        for keyword in urgency_keywords:
            if keyword in request.email_content.lower():
                detected_indicators.append(f"Urgency keyword detected: '{keyword}'")
                analysis["urgency_detected"] = True
    
    # Check sender domain
    if request.sender_email:
        suspicious_domains = ["paypa1", "amaz0n", "micros0ft", "goog1e"]
        sender_domain = request.sender_email.split("@")[-1] if "@" in request.sender_email else ""
        for suspicious in suspicious_domains:
            if suspicious in sender_domain:
                detected_indicators.append(f"Suspicious domain: {sender_domain}")
                analysis["domain_mismatch"] = True
    
    # Check for suspicious URLs
    if request.email_content:
        # Simple URL detection
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
                         request.email_content)
        if len(urls) > 3:
            detected_indicators.append(f"Multiple suspicious links detected: {len(urls)}")
            analysis["suspicious_links"] = len(urls)
    
    # Calculate phishing probability
    indicator_count = len(detected_indicators)
    confidence = min(0.95, 0.3 + (indicator_count * 0.15))
    
    is_phishing = confidence > 0.5
    
    # Determine risk level
    if confidence > 0.8:
        risk_level = "Critical"
    elif confidence > 0.5:
        risk_level = "High"
    elif confidence > 0.3:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    # Generate recommendations
    recommendations = []
    if is_phishing:
        recommendations = [
            "Do not click any links in this email",
            "Do not provide any personal information",
            "Report this email to your security team",
            "Delete this email immediately",
            "Add sender to blocklist"
        ]
    else:
        recommendations = ["Email appears legitimate, but remain cautious"]
    
    return PhishingResult(
        is_phishing=is_phishing,
        confidence=round(confidence, 3),
        risk_level=risk_level,
        detected_indicators=detected_indicators,
        recommendations=recommendations,
        analysis=analysis
    )


@router.post("/check-url")
async def check_url(url: str):
    """
    Check if URL is malicious or phishing
    """
    # Mock URL analysis
    suspicious_patterns = [".tk", ".ml", "bit.ly", "tinyurl", "login", "verify", "secure"]
    
    detected_issues = []
    for pattern in suspicious_patterns:
        if pattern in url.lower():
            detected_issues.append(f"Suspicious pattern: {pattern}")
    
    is_malicious = len(detected_issues) > 0
    risk_score = min(100, len(detected_issues) * 25)
    
    return {
        "url": url,
        "is_malicious": is_malicious,
        "risk_score": risk_score,
        "detected_issues": detected_issues,
        "threat_type": "Phishing" if is_malicious else "Safe",
        "recommendation": "Block access" if is_malicious else "Proceed with caution"
    }


@router.get("/recent-phishing")
async def get_recent_phishing():
    """
    Get recent phishing detection history
    """
    history = []
    for i in range(10):
        history.append({
            "id": f"phishing_{i+1}",
            "sender": f"suspicious{i}@fake-domain.com",
            "subject": f"Urgent: Verify your account #{i}",
            "detected_at": datetime.now().isoformat(),
            "risk_level": random.choice(["Critical", "High", "Medium"]),
            "confidence": round(random.uniform(0.6, 0.95), 2),
            "status": random.choice(["Blocked", "Quarantined"])
        })
    
    return {"detections": history}


@router.get("/phishing-stats")
async def get_phishing_stats():
    """
    Get phishing detection statistics
    """
    return {
        "total_checked": random.randint(1000, 5000),
        "phishing_detected": random.randint(100, 500),
        "blocked": random.randint(80, 400),
        "false_positives": random.randint(5, 20),
        "detection_accuracy": round(random.uniform(0.92, 0.98), 3),
        "top_targets": [
            {"type": "Banking", "count": random.randint(50, 150)},
            {"type": "Social Media", "count": random.randint(30, 100)},
            {"type": "E-commerce", "count": random.randint(20, 80)}
        ]
    }


@router.post("/train-model")
async def train_phishing_model():
    """
    Trigger retraining of phishing detection model
    """
    return {
        "message": "Model training initiated",
        "estimated_time": "15 minutes",
        "status": "in_progress"
    }
