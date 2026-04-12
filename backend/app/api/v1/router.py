"""
Main API Router - Includes all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    malware,
    phishing,
    vulnerabilities,
    security_assistant,
    dashboard,
    reports,
    auth
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(malware.router, prefix="/malware", tags=["Malware Detection"])
api_router.include_router(phishing.router, prefix="/phishing", tags=["Phishing Detection"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerability Intelligence"])
api_router.include_router(security_assistant.router, prefix="/assistant", tags=["Security Assistant"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
