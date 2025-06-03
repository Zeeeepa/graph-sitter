"""
Main settings configuration for the comprehensive CI/CD system.
"""

import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment configuration
    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Application environment"
    )
    
    # Application settings
    app_name: str = Field(default="contexten-cicd", description="Application name")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of API workers")
    
    # Performance settings
    max_concurrent_operations: int = Field(
        default=1000,
        description="Maximum concurrent operations target"
    )
    response_timeout_seconds: float = Field(
        default=2.0,
        description="Maximum response time target in seconds"
    )
    
    # Security settings
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for encryption"
    )
    
    # Temporary directory for operations
    tmp_dir: str = Field(default="/tmp/contexten", description="Temporary directory")
    
    # Feature flags
    enable_continuous_learning: bool = Field(
        default=True,
        description="Enable continuous learning features"
    )
    enable_performance_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring"
    )
    enable_analytics: bool = Field(
        default=True,
        description="Enable analytics collection"
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

