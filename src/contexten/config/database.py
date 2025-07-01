"""
Database configuration for the comprehensive CI/CD system.
"""

import os
from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Database connection settings
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="contexten_cicd", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")
    
    # SQLite settings (for development)
    sqlite_path: str = Field(
        default="./contexten_cicd.db",
        description="SQLite database file path"
    )
    
    # Connection pool settings
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Maximum pool overflow")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    
    # Query settings
    echo_sql: bool = Field(default=False, description="Echo SQL queries to logs")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    
    # Migration settings
    migration_timeout: int = Field(default=300, description="Migration timeout in seconds")
    
    @computed_field
    @property
    def database_url(self) -> str:
        """Generate the database URL based on configuration."""
        # Use SQLite for development/testing
        if os.getenv("DB_USE_SQLITE", "true").lower() == "true":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        
        # Use PostgreSQL for production
        if self.password:
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql+asyncpg://{self.user}@{self.host}:{self.port}/{self.name}"
    
    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Generate the synchronous database URL for migrations."""
        # Use SQLite for development/testing
        if os.getenv("DB_USE_SQLITE", "true").lower() == "true":
            return f"sqlite:///{self.sqlite_path}"
        
        # Use PostgreSQL for production
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}"


# Global database config instance
_database_config: Optional[DatabaseConfig] = None


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance."""
    global _database_config
    if _database_config is None:
        _database_config = DatabaseConfig()
    return _database_config

