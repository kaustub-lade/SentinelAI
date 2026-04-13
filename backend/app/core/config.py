"""
Configuration settings for SentinelAI
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
import json


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
    )
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SentinelAI"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "https://sentinel-ai-flame.vercel.app"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    NVD_API_KEY: str = os.getenv("NVD_API_KEY", "")
    
    # Database
    MONGODB_URL: str = (
        os.getenv("MONGODB_URL")
        or os.getenv("MONGODB_URI")
        or os.getenv("MONGO_URI")
        or os.getenv("DATABASE_URL", "")
    )
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "sentinelai")

    @property
    def allowed_origins(self) -> List[str]:
        raw_origins = (self.ALLOWED_ORIGINS or "").strip()
        if not raw_origins:
            return []

        if raw_origins.startswith("["):
            try:
                parsed = json.loads(raw_origins)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
            except json.JSONDecodeError:
                pass

        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    def validate_production(self) -> List[str]:
        issues: List[str] = []

        secret_key = (self.SECRET_KEY or "").strip()
        if not secret_key:
            issues.append("SECRET_KEY is required")
        elif secret_key == "your-secret-key-change-in-production":
            issues.append("SECRET_KEY must not use the default value")
        elif len(secret_key) < 32:
            issues.append("SECRET_KEY must be at least 32 characters")

        mongo_url = (self.MONGODB_URL or "").strip()
        if not mongo_url:
            issues.append("MONGODB_URL (or MONGODB_URI/MONGO_URI/DATABASE_URL) is required")
        elif not (mongo_url.startswith("mongodb://") or mongo_url.startswith("mongodb+srv://")):
            issues.append("MONGODB_URL must start with mongodb:// or mongodb+srv://")

        origins = self.allowed_origins
        if not origins:
            issues.append("ALLOWED_ORIGINS must include at least one frontend origin")

        for origin in origins:
            lowered = origin.lower()
            if "localhost" in lowered or "127.0.0.1" in lowered:
                issues.append("ALLOWED_ORIGINS must not include localhost/127.0.0.1 in production")
            if not lowered.startswith("https://"):
                issues.append(f"ALLOWED_ORIGINS must use https in production: {origin}")

        return issues
    
settings = Settings()
