"""
Configuration settings for SentinelAI
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SentinelAI"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse ALLOWED_ORIGINS from environment variable (comma-separated)
        origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if origins_env:
            self.ALLOWED_ORIGINS = [origin.strip() for origin in origins_env.split(",")]
        else:
            # Default origins for local development
            self.ALLOWED_ORIGINS = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000"
            ]
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sentinelai.db")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
