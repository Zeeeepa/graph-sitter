"""
Dashboard Extension Configuration Management

Comprehensive configuration system for the Dashboard extension with support for
environment variables, validation, security, and integration with all Contexten services.
"""

import os
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"


class CacheType(Enum):
    """Supported cache types"""
    REDIS = "redis"
    MEMORY = "memory"
    FILE = "file"


class SecurityLevel(Enum):
    """Security levels for API key encryption"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"


@dataclass
class DashboardAPIConfig:
    """Dashboard API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    request_timeout: int = 30
    max_request_size: int = 10485760  # 10MB
    api_prefix: str = "/api/dashboard"
    docs_enabled: bool = True
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"


@dataclass
class DashboardUIConfig:
    """Dashboard UI configuration"""
    enabled: bool = True
    build_path: str = "dist"
    static_path: str = "/static"
    index_file: str = "index.html"
    theme: str = "default"
    auto_refresh_interval: int = 30
    max_projects_per_page: int = 20
    max_tasks_per_page: int = 50
    real_time_updates: bool = True
    websocket_enabled: bool = True
    websocket_path: str = "/ws"
    notification_timeout: int = 5000
    chart_animation: bool = True
    responsive_breakpoints: Dict[str, int] = field(default_factory=lambda: {
        "mobile": 768,
        "tablet": 1024,
        "desktop": 1200
    })


@dataclass
class DashboardDatabaseConfig:
    """Dashboard database configuration"""
    type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = "localhost"
    port: int = 5432
    database: str = "contexten_dashboard"
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    connection_pool_size: int = 10
    connection_pool_max: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    auto_migrate: bool = True
    backup_enabled: bool = True
    backup_interval: int = 86400  # 24 hours
    backup_retention: int = 604800  # 7 days


@dataclass
class DashboardCacheConfig:
    """Dashboard cache configuration"""
    type: CacheType = CacheType.REDIS
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl_enabled: bool = False
    connection_pool_size: int = 10
    default_ttl: int = 3600  # 1 hour
    max_memory: str = "256mb"
    eviction_policy: str = "allkeys-lru"
    key_prefix: str = "dashboard:"
    compression_enabled: bool = True


@dataclass
class DashboardSecurityConfig:
    """Dashboard security configuration"""
    encryption_enabled: bool = True
    encryption_key: Optional[str] = None
    security_level: SecurityLevel = SecurityLevel.STANDARD
    api_key_encryption: bool = True
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    password_min_length: int = 8
    password_require_special: bool = True
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    csrf_protection: bool = True
    secure_cookies: bool = True
    audit_logging: bool = True


@dataclass
class DashboardIntegrationConfig:
    """Dashboard integration configuration"""
    # GitHub Integration
    github_enabled: bool = True
    github_api_key: Optional[str] = None
    github_webhook_secret: Optional[str] = None
    github_app_id: Optional[str] = None
    github_private_key: Optional[str] = None
    
    # Linear Integration
    linear_enabled: bool = True
    linear_api_key: Optional[str] = None
    linear_webhook_secret: Optional[str] = None
    
    # Slack Integration
    slack_enabled: bool = True
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    # CircleCI Integration
    circleci_enabled: bool = True
    circleci_api_key: Optional[str] = None
    circleci_webhook_secret: Optional[str] = None
    
    # Codegen SDK Integration
    codegen_enabled: bool = True
    codegen_org_id: Optional[str] = None
    codegen_api_token: Optional[str] = None
    codegen_base_url: str = "https://api.codegen.com"
    
    # PostgreSQL Integration
    postgresql_enabled: bool = True
    postgresql_connection_string: Optional[str] = None
    
    # Integration Health Checks
    health_check_interval: int = 300  # 5 minutes
    health_check_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5


@dataclass
class DashboardMonitoringConfig:
    """Dashboard monitoring configuration"""
    enabled: bool = True
    metrics_enabled: bool = True
    metrics_interval: int = 60
    metrics_retention: int = 604800  # 7 days
    health_checks_enabled: bool = True
    health_check_interval: int = 60
    performance_monitoring: bool = True
    error_tracking: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    log_rotation: bool = True
    log_max_size: str = "100MB"
    log_backup_count: int = 5
    alerting_enabled: bool = True
    alert_channels: List[str] = field(default_factory=lambda: ["slack", "email"])
    alert_thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "error_rate": 0.05,
        "response_time": 5.0,
        "memory_usage": 0.8,
        "cpu_usage": 0.8,
        "disk_usage": 0.9
    })


@dataclass
class DashboardWorkflowConfig:
    """Dashboard workflow configuration"""
    max_concurrent_flows: int = 10
    flow_timeout: int = 7200  # 2 hours
    task_timeout: int = 1800  # 30 minutes
    retry_attempts: int = 3
    retry_delay: int = 60
    auto_start_flows: bool = True
    auto_resume_flows: bool = True
    flow_persistence: bool = True
    progress_update_interval: int = 30
    quality_gates_enabled: bool = True
    quality_gate_timeout: int = 600  # 10 minutes
    notification_enabled: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["slack", "email"])


@dataclass
class DashboardConfig:
    """Comprehensive Dashboard configuration"""
    enabled: bool = True
    environment: str = "development"
    debug: bool = False
    
    # Component configurations
    api: DashboardAPIConfig = field(default_factory=DashboardAPIConfig)
    ui: DashboardUIConfig = field(default_factory=DashboardUIConfig)
    database: DashboardDatabaseConfig = field(default_factory=DashboardDatabaseConfig)
    cache: DashboardCacheConfig = field(default_factory=DashboardCacheConfig)
    security: DashboardSecurityConfig = field(default_factory=DashboardSecurityConfig)
    integrations: DashboardIntegrationConfig = field(default_factory=DashboardIntegrationConfig)
    monitoring: DashboardMonitoringConfig = field(default_factory=DashboardMonitoringConfig)
    workflow: DashboardWorkflowConfig = field(default_factory=DashboardWorkflowConfig)

    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Create configuration from environment variables"""
        
        # API configuration
        api_config = DashboardAPIConfig(
            host=os.getenv("DASHBOARD_API_HOST", "0.0.0.0"),
            port=int(os.getenv("DASHBOARD_API_PORT", "8000")),
            debug=os.getenv("DASHBOARD_API_DEBUG", "false").lower() == "true",
            cors_enabled=os.getenv("DASHBOARD_CORS_ENABLED", "true").lower() == "true",
            cors_origins=os.getenv("DASHBOARD_CORS_ORIGINS", "*").split(","),
            rate_limit_enabled=os.getenv("DASHBOARD_RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("DASHBOARD_RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("DASHBOARD_RATE_LIMIT_WINDOW", "60")),
            request_timeout=int(os.getenv("DASHBOARD_REQUEST_TIMEOUT", "30")),
            max_request_size=int(os.getenv("DASHBOARD_MAX_REQUEST_SIZE", "10485760")),
            api_prefix=os.getenv("DASHBOARD_API_PREFIX", "/api/dashboard"),
            docs_enabled=os.getenv("DASHBOARD_DOCS_ENABLED", "true").lower() == "true"
        )

        # UI configuration
        ui_config = DashboardUIConfig(
            enabled=os.getenv("DASHBOARD_UI_ENABLED", "true").lower() == "true",
            build_path=os.getenv("DASHBOARD_UI_BUILD_PATH", "dist"),
            theme=os.getenv("DASHBOARD_UI_THEME", "default"),
            auto_refresh_interval=int(os.getenv("DASHBOARD_AUTO_REFRESH_INTERVAL", "30")),
            max_projects_per_page=int(os.getenv("DASHBOARD_MAX_PROJECTS_PER_PAGE", "20")),
            max_tasks_per_page=int(os.getenv("DASHBOARD_MAX_TASKS_PER_PAGE", "50")),
            real_time_updates=os.getenv("DASHBOARD_REAL_TIME_UPDATES", "true").lower() == "true",
            websocket_enabled=os.getenv("DASHBOARD_WEBSOCKET_ENABLED", "true").lower() == "true"
        )

        # Database configuration
        db_type_str = os.getenv("DASHBOARD_DATABASE_TYPE", "postgresql").lower()
        db_type = DatabaseType.POSTGRESQL
        if db_type_str in [e.value for e in DatabaseType]:
            db_type = DatabaseType(db_type_str)
            
        database_config = DashboardDatabaseConfig(
            type=db_type,
            host=os.getenv("DASHBOARD_DATABASE_HOST", "localhost"),
            port=int(os.getenv("DASHBOARD_DATABASE_PORT", "5432")),
            database=os.getenv("DASHBOARD_DATABASE_NAME", "contexten_dashboard"),
            username=os.getenv("DASHBOARD_DATABASE_USERNAME"),
            password=os.getenv("DASHBOARD_DATABASE_PASSWORD"),
            ssl_enabled=os.getenv("DASHBOARD_DATABASE_SSL_ENABLED", "false").lower() == "true",
            connection_pool_size=int(os.getenv("DASHBOARD_DATABASE_POOL_SIZE", "10")),
            auto_migrate=os.getenv("DASHBOARD_DATABASE_AUTO_MIGRATE", "true").lower() == "true"
        )

        # Cache configuration
        cache_type_str = os.getenv("DASHBOARD_CACHE_TYPE", "redis").lower()
        cache_type = CacheType.REDIS
        if cache_type_str in [e.value for e in CacheType]:
            cache_type = CacheType(cache_type_str)
            
        cache_config = DashboardCacheConfig(
            type=cache_type,
            host=os.getenv("DASHBOARD_CACHE_HOST", "localhost"),
            port=int(os.getenv("DASHBOARD_CACHE_PORT", "6379")),
            database=int(os.getenv("DASHBOARD_CACHE_DATABASE", "0")),
            password=os.getenv("DASHBOARD_CACHE_PASSWORD"),
            default_ttl=int(os.getenv("DASHBOARD_CACHE_DEFAULT_TTL", "3600"))
        )

        # Security configuration
        security_level_str = os.getenv("DASHBOARD_SECURITY_LEVEL", "standard").lower()
        security_level = SecurityLevel.STANDARD
        if security_level_str in [e.value for e in SecurityLevel]:
            security_level = SecurityLevel(security_level_str)
            
        security_config = DashboardSecurityConfig(
            encryption_enabled=os.getenv("DASHBOARD_ENCRYPTION_ENABLED", "true").lower() == "true",
            encryption_key=os.getenv("DASHBOARD_ENCRYPTION_KEY"),
            security_level=security_level,
            api_key_encryption=os.getenv("DASHBOARD_API_KEY_ENCRYPTION", "true").lower() == "true",
            session_timeout=int(os.getenv("DASHBOARD_SESSION_TIMEOUT", "3600")),
            jwt_secret=os.getenv("DASHBOARD_JWT_SECRET"),
            audit_logging=os.getenv("DASHBOARD_AUDIT_LOGGING", "true").lower() == "true"
        )

        # Integration configuration
        integration_config = DashboardIntegrationConfig(
            # GitHub
            github_enabled=os.getenv("DASHBOARD_GITHUB_ENABLED", "true").lower() == "true",
            github_api_key=os.getenv("GITHUB_API_KEY") or os.getenv("GITHUB_TOKEN"),
            github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
            github_app_id=os.getenv("GITHUB_APP_ID"),
            github_private_key=os.getenv("GITHUB_PRIVATE_KEY"),
            
            # Linear
            linear_enabled=os.getenv("DASHBOARD_LINEAR_ENABLED", "true").lower() == "true",
            linear_api_key=os.getenv("LINEAR_API_KEY") or os.getenv("LINEAR_ACCESS_TOKEN"),
            linear_webhook_secret=os.getenv("LINEAR_WEBHOOK_SECRET"),
            
            # Slack
            slack_enabled=os.getenv("DASHBOARD_SLACK_ENABLED", "true").lower() == "true",
            slack_bot_token=os.getenv("SLACK_BOT_TOKEN"),
            slack_app_token=os.getenv("SLACK_APP_TOKEN"),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            
            # CircleCI
            circleci_enabled=os.getenv("DASHBOARD_CIRCLECI_ENABLED", "true").lower() == "true",
            circleci_api_key=os.getenv("CIRCLECI_API_KEY") or os.getenv("CIRCLECI_TOKEN"),
            circleci_webhook_secret=os.getenv("CIRCLECI_WEBHOOK_SECRET"),
            
            # Codegen SDK
            codegen_enabled=os.getenv("DASHBOARD_CODEGEN_ENABLED", "true").lower() == "true",
            codegen_org_id=os.getenv("CODEGEN_ORG_ID"),
            codegen_api_token=os.getenv("CODEGEN_API_TOKEN"),
            codegen_base_url=os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com"),
            
            # PostgreSQL
            postgresql_enabled=os.getenv("DASHBOARD_POSTGRESQL_ENABLED", "true").lower() == "true",
            postgresql_connection_string=os.getenv("POSTGRESQL_CONNECTION_STRING") or os.getenv("DATABASE_URL")
        )

        # Monitoring configuration
        monitoring_config = DashboardMonitoringConfig(
            enabled=os.getenv("DASHBOARD_MONITORING_ENABLED", "true").lower() == "true",
            metrics_enabled=os.getenv("DASHBOARD_METRICS_ENABLED", "true").lower() == "true",
            health_checks_enabled=os.getenv("DASHBOARD_HEALTH_CHECKS_ENABLED", "true").lower() == "true",
            log_level=os.getenv("DASHBOARD_LOG_LEVEL", "INFO"),
            log_format=os.getenv("DASHBOARD_LOG_FORMAT", "json"),
            alerting_enabled=os.getenv("DASHBOARD_ALERTING_ENABLED", "true").lower() == "true"
        )

        # Workflow configuration
        workflow_config = DashboardWorkflowConfig(
            max_concurrent_flows=int(os.getenv("DASHBOARD_MAX_CONCURRENT_FLOWS", "10")),
            flow_timeout=int(os.getenv("DASHBOARD_FLOW_TIMEOUT", "7200")),
            task_timeout=int(os.getenv("DASHBOARD_TASK_TIMEOUT", "1800")),
            auto_start_flows=os.getenv("DASHBOARD_AUTO_START_FLOWS", "true").lower() == "true",
            quality_gates_enabled=os.getenv("DASHBOARD_QUALITY_GATES_ENABLED", "true").lower() == "true"
        )

        return cls(
            enabled=os.getenv("DASHBOARD_ENABLED", "true").lower() == "true",
            environment=os.getenv("DASHBOARD_ENVIRONMENT", "development"),
            debug=os.getenv("DASHBOARD_DEBUG", "false").lower() == "true",
            api=api_config,
            ui=ui_config,
            database=database_config,
            cache=cache_config,
            security=security_config,
            integrations=integration_config,
            monitoring=monitoring_config,
            workflow=workflow_config
        )

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if not self.enabled:
            return errors

        # API validation
        if self.api.port < 1 or self.api.port > 65535:
            errors.append("DASHBOARD_API_PORT must be between 1 and 65535")

        if self.api.rate_limit_requests <= 0:
            errors.append("DASHBOARD_RATE_LIMIT_REQUESTS must be positive")

        # Database validation
        if not self.database.username and self.database.type != DatabaseType.SQLITE:
            errors.append("DASHBOARD_DATABASE_USERNAME is required for non-SQLite databases")

        if not self.database.password and self.database.type != DatabaseType.SQLITE:
            errors.append("DASHBOARD_DATABASE_PASSWORD is required for non-SQLite databases")

        # Security validation
        if self.security.encryption_enabled and not self.security.encryption_key:
            errors.append("DASHBOARD_ENCRYPTION_KEY is required when encryption is enabled")

        if len(self.security.encryption_key or "") < 32:
            errors.append("DASHBOARD_ENCRYPTION_KEY should be at least 32 characters long")

        if not self.security.jwt_secret:
            errors.append("DASHBOARD_JWT_SECRET is required")

        # Integration validation
        if self.integrations.github_enabled and not self.integrations.github_api_key:
            errors.append("GITHUB_API_KEY is required when GitHub integration is enabled")

        if self.integrations.linear_enabled and not self.integrations.linear_api_key:
            errors.append("LINEAR_API_KEY is required when Linear integration is enabled")

        if self.integrations.codegen_enabled:
            if not self.integrations.codegen_org_id:
                errors.append("CODEGEN_ORG_ID is required when Codegen integration is enabled")
            if not self.integrations.codegen_api_token:
                errors.append("CODEGEN_API_TOKEN is required when Codegen integration is enabled")

        # Workflow validation
        if self.workflow.max_concurrent_flows <= 0:
            errors.append("DASHBOARD_MAX_CONCURRENT_FLOWS must be positive")

        if self.workflow.flow_timeout <= 0:
            errors.append("DASHBOARD_FLOW_TIMEOUT must be positive")

        return errors

    def to_dict(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        def mask_value(value: Optional[str]) -> Optional[str]:
            if not mask_secrets or not value:
                return value
            return "***" if len(value) > 0 else None

        return {
            "enabled": self.enabled,
            "environment": self.environment,
            "debug": self.debug,
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "debug": self.api.debug,
                "cors_enabled": self.api.cors_enabled,
                "rate_limit_enabled": self.api.rate_limit_enabled,
                "rate_limit_requests": self.api.rate_limit_requests,
                "docs_enabled": self.api.docs_enabled
            },
            "ui": {
                "enabled": self.ui.enabled,
                "theme": self.ui.theme,
                "real_time_updates": self.ui.real_time_updates,
                "websocket_enabled": self.ui.websocket_enabled
            },
            "database": {
                "type": self.database.type.value,
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                "password": mask_value(self.database.password),
                "ssl_enabled": self.database.ssl_enabled,
                "auto_migrate": self.database.auto_migrate
            },
            "cache": {
                "type": self.cache.type.value,
                "host": self.cache.host,
                "port": self.cache.port,
                "password": mask_value(self.cache.password),
                "default_ttl": self.cache.default_ttl
            },
            "security": {
                "encryption_enabled": self.security.encryption_enabled,
                "encryption_key": mask_value(self.security.encryption_key),
                "security_level": self.security.security_level.value,
                "api_key_encryption": self.security.api_key_encryption,
                "jwt_secret": mask_value(self.security.jwt_secret),
                "audit_logging": self.security.audit_logging
            },
            "integrations": {
                "github_enabled": self.integrations.github_enabled,
                "github_api_key": mask_value(self.integrations.github_api_key),
                "linear_enabled": self.integrations.linear_enabled,
                "linear_api_key": mask_value(self.integrations.linear_api_key),
                "slack_enabled": self.integrations.slack_enabled,
                "slack_bot_token": mask_value(self.integrations.slack_bot_token),
                "circleci_enabled": self.integrations.circleci_enabled,
                "circleci_api_key": mask_value(self.integrations.circleci_api_key),
                "codegen_enabled": self.integrations.codegen_enabled,
                "codegen_org_id": self.integrations.codegen_org_id,
                "codegen_api_token": mask_value(self.integrations.codegen_api_token),
                "postgresql_enabled": self.integrations.postgresql_enabled
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "metrics_enabled": self.monitoring.metrics_enabled,
                "health_checks_enabled": self.monitoring.health_checks_enabled,
                "log_level": self.monitoring.log_level,
                "alerting_enabled": self.monitoring.alerting_enabled
            },
            "workflow": {
                "max_concurrent_flows": self.workflow.max_concurrent_flows,
                "auto_start_flows": self.workflow.auto_start_flows,
                "quality_gates_enabled": self.workflow.quality_gates_enabled
            }
        }


def get_dashboard_config() -> DashboardConfig:
    """Get Dashboard configuration from environment"""
    config = DashboardConfig.from_env()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.warning(f"Dashboard configuration validation errors: {errors}")
        for error in errors:
            logger.warning(f"  - {error}")
    
    logger.info("Dashboard configuration loaded successfully")
    return config


def create_config_template() -> str:
    """Create a configuration template with all available options"""
    return """
# Dashboard Extension Configuration Template

# Core Settings
DASHBOARD_ENABLED=true
DASHBOARD_ENVIRONMENT=development
DASHBOARD_DEBUG=false

# API Configuration
DASHBOARD_API_HOST=0.0.0.0
DASHBOARD_API_PORT=8000
DASHBOARD_API_DEBUG=false
DASHBOARD_CORS_ENABLED=true
DASHBOARD_CORS_ORIGINS=*
DASHBOARD_RATE_LIMIT_ENABLED=true
DASHBOARD_RATE_LIMIT_REQUESTS=100
DASHBOARD_RATE_LIMIT_WINDOW=60
DASHBOARD_REQUEST_TIMEOUT=30
DASHBOARD_MAX_REQUEST_SIZE=10485760
DASHBOARD_API_PREFIX=/api/dashboard
DASHBOARD_DOCS_ENABLED=true

# UI Configuration
DASHBOARD_UI_ENABLED=true
DASHBOARD_UI_BUILD_PATH=dist
DASHBOARD_UI_THEME=default
DASHBOARD_AUTO_REFRESH_INTERVAL=30
DASHBOARD_MAX_PROJECTS_PER_PAGE=20
DASHBOARD_MAX_TASKS_PER_PAGE=50
DASHBOARD_REAL_TIME_UPDATES=true
DASHBOARD_WEBSOCKET_ENABLED=true

# Database Configuration
DASHBOARD_DATABASE_TYPE=postgresql
DASHBOARD_DATABASE_HOST=localhost
DASHBOARD_DATABASE_PORT=5432
DASHBOARD_DATABASE_NAME=contexten_dashboard
DASHBOARD_DATABASE_USERNAME=your_db_username
DASHBOARD_DATABASE_PASSWORD=your_db_password
DASHBOARD_DATABASE_SSL_ENABLED=false
DASHBOARD_DATABASE_POOL_SIZE=10
DASHBOARD_DATABASE_AUTO_MIGRATE=true

# Cache Configuration
DASHBOARD_CACHE_TYPE=redis
DASHBOARD_CACHE_HOST=localhost
DASHBOARD_CACHE_PORT=6379
DASHBOARD_CACHE_DATABASE=0
DASHBOARD_CACHE_PASSWORD=your_cache_password
DASHBOARD_CACHE_DEFAULT_TTL=3600

# Security Configuration
DASHBOARD_ENCRYPTION_ENABLED=true
DASHBOARD_ENCRYPTION_KEY=your_32_character_encryption_key_here
DASHBOARD_SECURITY_LEVEL=standard
DASHBOARD_API_KEY_ENCRYPTION=true
DASHBOARD_SESSION_TIMEOUT=3600
DASHBOARD_JWT_SECRET=your_jwt_secret_here
DASHBOARD_AUDIT_LOGGING=true

# GitHub Integration
DASHBOARD_GITHUB_ENABLED=true
GITHUB_API_KEY=your_github_api_key_here
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret
GITHUB_APP_ID=your_github_app_id
GITHUB_PRIVATE_KEY=your_github_private_key

# Linear Integration
DASHBOARD_LINEAR_ENABLED=true
LINEAR_API_KEY=your_linear_api_key_here
LINEAR_WEBHOOK_SECRET=your_linear_webhook_secret

# Slack Integration
DASHBOARD_SLACK_ENABLED=true
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token
SLACK_WEBHOOK_URL=your_slack_webhook_url

# CircleCI Integration
DASHBOARD_CIRCLECI_ENABLED=true
CIRCLECI_API_KEY=your_circleci_api_key
CIRCLECI_WEBHOOK_SECRET=your_circleci_webhook_secret

# Codegen SDK Integration
DASHBOARD_CODEGEN_ENABLED=true
CODEGEN_ORG_ID=your_codegen_org_id
CODEGEN_API_TOKEN=your_codegen_api_token
CODEGEN_BASE_URL=https://api.codegen.com

# PostgreSQL Integration
DASHBOARD_POSTGRESQL_ENABLED=true
POSTGRESQL_CONNECTION_STRING=postgresql://user:pass@localhost/db

# Monitoring Configuration
DASHBOARD_MONITORING_ENABLED=true
DASHBOARD_METRICS_ENABLED=true
DASHBOARD_HEALTH_CHECKS_ENABLED=true
DASHBOARD_LOG_LEVEL=INFO
DASHBOARD_LOG_FORMAT=json
DASHBOARD_ALERTING_ENABLED=true

# Workflow Configuration
DASHBOARD_MAX_CONCURRENT_FLOWS=10
DASHBOARD_FLOW_TIMEOUT=7200
DASHBOARD_TASK_TIMEOUT=1800
DASHBOARD_AUTO_START_FLOWS=true
DASHBOARD_QUALITY_GATES_ENABLED=true
"""

