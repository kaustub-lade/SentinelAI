"""
SentinelAI - Main Application Entry Point
AI-Powered Cybersecurity Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from app.api.v1.router import api_router
from app.core.config import settings

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="SentinelAI API",
    description="Autonomous Cyber Defense Platform - AI-Powered Threat Detection & Response",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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
