"""
Application configuration settings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # Project info
    PROJECT_NAME: str = "Deployment Validator"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Standalone deployment validation system with GitHub integration"
    
    # API configuration
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CALLBACK_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Redis (for session management)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Encryption
    ENCRYPTION_KEY: str
    
    # Sandbox
    SANDBOX_BASE_PATH: str = "/tmp/sandboxes"
    MAX_SANDBOX_AGE_DAYS: int = 7
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

settings = Settings()

