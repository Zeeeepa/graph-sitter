"""
Database Configuration Management

Handles database connection configuration, environment variables,
and connection pooling settings for the graph-sitter database system.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    
    # Connection settings
    url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/graph_sitter"
    ))
    
    # Connection pool settings
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "20")))
    max_overflow: int = field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "30")))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30")))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "3600")))
    
    # Query settings
    echo: bool = field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")
    echo_pool: bool = field(default_factory=lambda: os.getenv("DB_ECHO_POOL", "false").lower() == "true")
    
    # Performance settings
    query_timeout: int = field(default_factory=lambda: int(os.getenv("DB_QUERY_TIMEOUT", "30")))
    statement_timeout: int = field(default_factory=lambda: int(os.getenv("DB_STATEMENT_TIMEOUT", "60")))
    
    # Feature flags
    enable_query_monitoring: bool = field(default_factory=lambda: os.getenv("DB_ENABLE_QUERY_MONITORING", "true").lower() == "true")
    enable_slow_query_logging: bool = field(default_factory=lambda: os.getenv("DB_ENABLE_SLOW_QUERY_LOGGING", "true").lower() == "true")
    slow_query_threshold_ms: int = field(default_factory=lambda: int(os.getenv("DB_SLOW_QUERY_THRESHOLD_MS", "1000")))
    
    # Migration settings
    auto_migrate: bool = field(default_factory=lambda: os.getenv("DB_AUTO_MIGRATE", "false").lower() == "true")
    migration_timeout: int = field(default_factory=lambda: int(os.getenv("DB_MIGRATION_TIMEOUT", "300")))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_url()
        self._validate_pool_settings()
        self._validate_timeouts()
    
    def _validate_url(self):
        """Validate database URL format."""
        try:
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.hostname:
                raise ValueError("Invalid database URL format")
            if parsed.scheme not in ["postgresql", "postgres"]:
                logger.warning(f"Unexpected database scheme: {parsed.scheme}")
        except Exception as e:
            raise ValueError(f"Invalid database URL: {e}")
    
    def _validate_pool_settings(self):
        """Validate connection pool settings."""
        if self.pool_size <= 0:
            raise ValueError("Pool size must be positive")
        if self.max_overflow < 0:
            raise ValueError("Max overflow cannot be negative")
        if self.pool_timeout <= 0:
            raise ValueError("Pool timeout must be positive")
        if self.pool_recycle <= 0:
            raise ValueError("Pool recycle must be positive")
    
    def _validate_timeouts(self):
        """Validate timeout settings."""
        if self.query_timeout <= 0:
            raise ValueError("Query timeout must be positive")
        if self.statement_timeout <= 0:
            raise ValueError("Statement timeout must be positive")
        if self.slow_query_threshold_ms <= 0:
            raise ValueError("Slow query threshold must be positive")
    
    @property
    def connection_args(self) -> Dict[str, Any]:
        """Get SQLAlchemy connection arguments."""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "connect_args": {
                "options": f"-c statement_timeout={self.statement_timeout}s"
            }
        }
    
    @property
    def database_name(self) -> str:
        """Extract database name from URL."""
        parsed = urlparse(self.url)
        return parsed.path.lstrip("/") if parsed.path else "graph_sitter"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            "enable_query_monitoring": self.enable_query_monitoring,
            "enable_slow_query_logging": self.enable_slow_query_logging,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "query_timeout": self.query_timeout,
        }


# Global configuration instance
_config: Optional[DatabaseConfig] = None


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance."""
    global _config
    if _config is None:
        _config = DatabaseConfig()
        logger.info(f"Initialized database config for: {_config.database_name}")
    return _config


def set_database_config(config: DatabaseConfig) -> None:
    """Set the global database configuration instance."""
    global _config
    _config = config
    logger.info(f"Updated database config for: {config.database_name}")


def reset_database_config() -> None:
    """Reset the global database configuration instance."""
    global _config
    _config = None
    logger.info("Reset database configuration")


# Environment-specific configurations
def get_test_config() -> DatabaseConfig:
    """Get configuration for testing environment."""
    return DatabaseConfig(
        url=os.getenv("TEST_DATABASE_URL", "postgresql://postgres:password@localhost:5432/graph_sitter_test"),
        pool_size=5,
        max_overflow=10,
        echo=True,
        auto_migrate=True,
    )


def get_development_config() -> DatabaseConfig:
    """Get configuration for development environment."""
    return DatabaseConfig(
        url=os.getenv("DEV_DATABASE_URL", "postgresql://postgres:password@localhost:5432/graph_sitter_dev"),
        pool_size=10,
        max_overflow=20,
        echo=True,
        enable_query_monitoring=True,
        enable_slow_query_logging=True,
    )


def get_production_config() -> DatabaseConfig:
    """Get configuration for production environment."""
    return DatabaseConfig(
        url=os.getenv("PROD_DATABASE_URL", "postgresql://postgres:password@localhost:5432/graph_sitter"),
        pool_size=50,
        max_overflow=100,
        echo=False,
        enable_query_monitoring=True,
        enable_slow_query_logging=True,
        slow_query_threshold_ms=500,
    )


def configure_for_environment(environment: str = None) -> DatabaseConfig:
    """Configure database for specific environment."""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    environment = environment.lower()
    
    if environment == "test":
        config = get_test_config()
    elif environment == "development":
        config = get_development_config()
    elif environment == "production":
        config = get_production_config()
    else:
        logger.warning(f"Unknown environment '{environment}', using development config")
        config = get_development_config()
    
    set_database_config(config)
    return config

