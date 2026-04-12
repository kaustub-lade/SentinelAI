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
    ALLOWED_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:3000"
    )

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinelai.db")

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
    
settings = Settings()
