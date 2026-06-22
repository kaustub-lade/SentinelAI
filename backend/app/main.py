import logging
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing app modules
# so that Settings picks up .env values at instantiation time
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.limiter import limiter
from app.api.v1.endpoints import alerts

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import ensure_indexes, is_db_available
from app.core.logger import get_logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)
log = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SentinelAI API",
    description="Autonomous Cyber Defense Platform - AI-Powered Threat Detection & Response",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach rate limiter middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse({"detail": "Rate limit exceeded"}, status_code=429))


@app.on_event("startup")
def on_startup():
    config_issues = []

    if settings.ENVIRONMENT.lower() == "production":
        config_issues = settings.validate_production()

    if config_issues:
        joined = "; ".join(config_issues)
        logger.error(
            "Production configuration validation failed: %s",
            joined,
        )
        raise RuntimeError(
            f"Production configuration validation failed: {joined}"
        )

    if not ensure_indexes():
        logger.warning(
            "Database initialization failed during startup. "
            "The API will still start, but DB-backed endpoints "
            "may return 503 until MongoDB is reachable."
        )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"https://[a-z0-9-]+(?:-[a-z0-9-]+)*\.vercel\.app$",
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
    db_ok = is_db_available()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "SentinelAI API",
        "version": "1.0.0",
        "database": "connected" if db_ok else "unavailable",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (basic)."""
    resp = generate_latest()
    return JSONResponse(content=resp, media_type=CONTENT_TYPE_LATEST)


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["Alerts"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
