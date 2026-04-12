"""
SentinelAI - Main Application Entry Point
AI-Powered Cybersecurity Platform
"""

import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing app modules
# so that Settings picks up .env values at instantiation time
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401

# Create FastAPI app
app = FastAPI(
    title="SentinelAI API",
    description="Autonomous Cyber Defense Platform - AI-Powered Threat Detection & Response",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SentinelAI API",
        "version": "1.0.0",
        "description": "Autonomous Cyber Defense Platform",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "api": "/api/v1"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SentinelAI API",
        "version": "1.0.0"
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
