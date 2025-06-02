"""
Linear Integration Configuration Management

Comprehensive configuration system for Linear integration with support for
environment variables, validation, and default values.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class LinearAPIConfig:
    """Linear API configuration"""
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    cache_ttl: int = 300
    base_url: str = "https://api.linear.app/graphql"


@dataclass
class LinearWebhookConfig:
    """Linear webhook configuration"""
    webhook_secret: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 5
    max_payload_size: int = 1048576  # 1MB
    signature_header: str = "Linear-Signature"
    timestamp_tolerance: int = 300  # 5 minutes


@dataclass
class LinearBotConfig:
    """Linear bot configuration"""
    bot_user_id: Optional[str] = None
    bot_email: Optional[str] = None
    bot_names: List[str] = field(default_factory=lambda: ["codegen", "openalpha", "bot"])


@dataclass
class LinearAssignmentConfig:
    """Linear assignment detection configuration"""
    auto_assign_labels: List[str] = field(default_factory=lambda: ["ai", "automation", "codegen"])
    auto_assign_keywords: List[str] = field(default_factory=lambda: ["generate", "evolve", "optimize", "automate"])
    max_assignments_per_hour: int = 10
    assignment_cooldown: int = 300  # 5 minutes


@dataclass
class LinearWorkflowConfig:
    """Linear workflow automation configuration"""
    auto_start_tasks: bool = True
    auto_update_status: bool = True
    progress_update_interval: int = 60
    status_sync_interval: int = 300
    task_timeout: int = 3600  # 1 hour


@dataclass
class LinearEventConfig:
    """Linear event management configuration"""
    queue_size: int = 1000
    batch_size: int = 10
    processing_interval: int = 5
    retry_interval: int = 60
    persistence_enabled: bool = True
    persistence_file: str = "linear_events.json"
    max_event_age: int = 86400  # 24 hours


@dataclass
class LinearMonitoringConfig:
    """Linear monitoring configuration"""
    enabled: bool = True
    monitoring_interval: int = 60
    health_check_interval: int = 300
    metrics_retention: int = 86400  # 24 hours
    alert_on_failures: bool = True


@dataclass
class LinearIntegrationConfig:
    """Comprehensive Linear integration configuration"""
    enabled: bool = True
    api: LinearAPIConfig = field(default_factory=LinearAPIConfig)
    webhook: LinearWebhookConfig = field(default_factory=LinearWebhookConfig)
    bot: LinearBotConfig = field(default_factory=LinearBotConfig)
    assignment: LinearAssignmentConfig = field(default_factory=LinearAssignmentConfig)
    workflow: LinearWorkflowConfig = field(default_factory=LinearWorkflowConfig)
    events: LinearEventConfig = field(default_factory=LinearEventConfig)
    monitoring: LinearMonitoringConfig = field(default_factory=LinearMonitoringConfig)

    @classmethod
    def from_env(cls) -> "LinearIntegrationConfig":
        """Create configuration from environment variables"""
        
        # API configuration
        api_config = LinearAPIConfig(
            api_key=os.getenv("LINEAR_API_KEY") or os.getenv("LINEAR_ACCESS_TOKEN"),
            timeout=int(os.getenv("LINEAR_API_TIMEOUT", "30")),
            max_retries=int(os.getenv("LINEAR_API_MAX_RETRIES", "3")),
            rate_limit_requests=int(os.getenv("LINEAR_RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("LINEAR_RATE_LIMIT_WINDOW", "60")),
            cache_ttl=int(os.getenv("LINEAR_CACHE_TTL", "300")),
            base_url=os.getenv("LINEAR_API_BASE_URL", "https://api.linear.app/graphql")
        )

        # Webhook configuration
        webhook_config = LinearWebhookConfig(
            webhook_secret=os.getenv("LINEAR_WEBHOOK_SECRET"),
            max_retries=int(os.getenv("LINEAR_WEBHOOK_MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("LINEAR_WEBHOOK_RETRY_DELAY", "5")),
            max_payload_size=int(os.getenv("LINEAR_WEBHOOK_MAX_PAYLOAD_SIZE", "1048576")),
            signature_header=os.getenv("LINEAR_WEBHOOK_SIGNATURE_HEADER", "Linear-Signature"),
            timestamp_tolerance=int(os.getenv("LINEAR_WEBHOOK_TIMESTAMP_TOLERANCE", "300"))
        )

        # Bot configuration
        bot_names = os.getenv("LINEAR_BOT_NAMES", "codegen,openalpha,bot").split(",")
        bot_config = LinearBotConfig(
            bot_user_id=os.getenv("LINEAR_BOT_USER_ID"),
            bot_email=os.getenv("LINEAR_BOT_EMAIL"),
            bot_names=[name.strip() for name in bot_names if name.strip()]
        )

        # Assignment configuration
        auto_assign_labels = os.getenv("LINEAR_AUTO_ASSIGN_LABELS", "ai,automation,codegen").split(",")
        auto_assign_keywords = os.getenv("LINEAR_AUTO_ASSIGN_KEYWORDS", "generate,evolve,optimize,automate").split(",")
        assignment_config = LinearAssignmentConfig(
            auto_assign_labels=[label.strip() for label in auto_assign_labels if label.strip()],
            auto_assign_keywords=[keyword.strip() for keyword in auto_assign_keywords if keyword.strip()],
            max_assignments_per_hour=int(os.getenv("LINEAR_MAX_ASSIGNMENTS_PER_HOUR", "10")),
            assignment_cooldown=int(os.getenv("LINEAR_ASSIGNMENT_COOLDOWN", "300"))
        )

        # Workflow configuration
        workflow_config = LinearWorkflowConfig(
            auto_start_tasks=os.getenv("LINEAR_AUTO_START_TASKS", "true").lower() == "true",
            auto_update_status=os.getenv("LINEAR_AUTO_UPDATE_STATUS", "true").lower() == "true",
            progress_update_interval=int(os.getenv("LINEAR_PROGRESS_UPDATE_INTERVAL", "60")),
            status_sync_interval=int(os.getenv("LINEAR_STATUS_SYNC_INTERVAL", "300")),
            task_timeout=int(os.getenv("LINEAR_TASK_TIMEOUT", "3600"))
        )

        # Event configuration
        events_config = LinearEventConfig(
            queue_size=int(os.getenv("LINEAR_EVENT_QUEUE_SIZE", "1000")),
            batch_size=int(os.getenv("LINEAR_EVENT_BATCH_SIZE", "10")),
            processing_interval=int(os.getenv("LINEAR_EVENT_PROCESSING_INTERVAL", "5")),
            retry_interval=int(os.getenv("LINEAR_EVENT_RETRY_INTERVAL", "60")),
            persistence_enabled=os.getenv("LINEAR_EVENT_PERSISTENCE_ENABLED", "true").lower() == "true",
            persistence_file=os.getenv("LINEAR_EVENT_PERSISTENCE_FILE", "linear_events.json"),
            max_event_age=int(os.getenv("LINEAR_MAX_EVENT_AGE", "86400"))
        )

        # Monitoring configuration
        monitoring_config = LinearMonitoringConfig(
            enabled=os.getenv("LINEAR_MONITORING_ENABLED", "true").lower() == "true",
            monitoring_interval=int(os.getenv("LINEAR_MONITORING_INTERVAL", "60")),
            health_check_interval=int(os.getenv("LINEAR_HEALTH_CHECK_INTERVAL", "300")),
            metrics_retention=int(os.getenv("LINEAR_METRICS_RETENTION", "86400")),
            alert_on_failures=os.getenv("LINEAR_ALERT_ON_FAILURES", "true").lower() == "true"
        )

        return cls(
            enabled=os.getenv("LINEAR_ENABLED", "true").lower() == "true",
            api=api_config,
            webhook=webhook_config,
            bot=bot_config,
            assignment=assignment_config,
            workflow=workflow_config,
            events=events_config,
            monitoring=monitoring_config
        )

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if self.enabled:
            if not self.api.api_key:
                errors.append("LINEAR_API_KEY is required when Linear integration is enabled")

            if self.webhook.webhook_secret and len(self.webhook.webhook_secret) < 16:
                errors.append("LINEAR_WEBHOOK_SECRET should be at least 16 characters long")

            if self.api.timeout <= 0:
                errors.append("LINEAR_API_TIMEOUT must be positive")

            if self.api.max_retries < 0:
                errors.append("LINEAR_API_MAX_RETRIES must be non-negative")

            if self.api.rate_limit_requests <= 0:
                errors.append("LINEAR_RATE_LIMIT_REQUESTS must be positive")

            if self.assignment.max_assignments_per_hour <= 0:
                errors.append("LINEAR_MAX_ASSIGNMENTS_PER_HOUR must be positive")

            if self.events.queue_size <= 0:
                errors.append("LINEAR_EVENT_QUEUE_SIZE must be positive")

            if self.events.batch_size <= 0:
                errors.append("LINEAR_EVENT_BATCH_SIZE must be positive")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "enabled": self.enabled,
            "api": {
                "api_key": "***" if self.api.api_key else None,
                "timeout": self.api.timeout,
                "max_retries": self.api.max_retries,
                "rate_limit_requests": self.api.rate_limit_requests,
                "rate_limit_window": self.api.rate_limit_window,
                "cache_ttl": self.api.cache_ttl,
                "base_url": self.api.base_url
            },
            "webhook": {
                "webhook_secret": "***" if self.webhook.webhook_secret else None,
                "max_retries": self.webhook.max_retries,
                "retry_delay": self.webhook.retry_delay,
                "max_payload_size": self.webhook.max_payload_size,
                "signature_header": self.webhook.signature_header,
                "timestamp_tolerance": self.webhook.timestamp_tolerance
            },
            "bot": {
                "bot_user_id": self.bot.bot_user_id,
                "bot_email": self.bot.bot_email,
                "bot_names": self.bot.bot_names
            },
            "assignment": {
                "auto_assign_labels": self.assignment.auto_assign_labels,
                "auto_assign_keywords": self.assignment.auto_assign_keywords,
                "max_assignments_per_hour": self.assignment.max_assignments_per_hour,
                "assignment_cooldown": self.assignment.assignment_cooldown
            },
            "workflow": {
                "auto_start_tasks": self.workflow.auto_start_tasks,
                "auto_update_status": self.workflow.auto_update_status,
                "progress_update_interval": self.workflow.progress_update_interval,
                "status_sync_interval": self.workflow.status_sync_interval,
                "task_timeout": self.workflow.task_timeout
            },
            "events": {
                "queue_size": self.events.queue_size,
                "batch_size": self.events.batch_size,
                "processing_interval": self.events.processing_interval,
                "retry_interval": self.events.retry_interval,
                "persistence_enabled": self.events.persistence_enabled,
                "persistence_file": self.events.persistence_file,
                "max_event_age": self.events.max_event_age
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "monitoring_interval": self.monitoring.monitoring_interval,
                "health_check_interval": self.monitoring.health_check_interval,
                "metrics_retention": self.monitoring.metrics_retention,
                "alert_on_failures": self.monitoring.alert_on_failures
            }
        }


def get_linear_config() -> LinearIntegrationConfig:
    """Get Linear integration configuration from environment"""
    config = LinearIntegrationConfig.from_env()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.warning(f"Linear configuration validation errors: {errors}")
        for error in errors:
            logger.warning(f"  - {error}")
    
    logger.info("Linear integration configuration loaded")
    return config


def create_config_template() -> str:
    """Create a configuration template with all available options"""
    return """
# Linear Integration Configuration

# Core Settings
LINEAR_ENABLED=true
LINEAR_API_KEY=your_linear_api_key_here
LINEAR_WEBHOOK_SECRET=your_webhook_secret_here

# Bot Configuration
LINEAR_BOT_USER_ID=your_bot_user_id
LINEAR_BOT_EMAIL=your_bot_email
LINEAR_BOT_NAMES=codegen,openalpha,bot

# API Configuration
LINEAR_API_TIMEOUT=30
LINEAR_API_MAX_RETRIES=3
LINEAR_RATE_LIMIT_REQUESTS=100
LINEAR_RATE_LIMIT_WINDOW=60
LINEAR_CACHE_TTL=300

# Webhook Configuration
LINEAR_WEBHOOK_MAX_RETRIES=3
LINEAR_WEBHOOK_RETRY_DELAY=5
LINEAR_WEBHOOK_MAX_PAYLOAD_SIZE=1048576
LINEAR_WEBHOOK_TIMESTAMP_TOLERANCE=300

# Assignment Configuration
LINEAR_AUTO_ASSIGN_LABELS=ai,automation,codegen
LINEAR_AUTO_ASSIGN_KEYWORDS=generate,evolve,optimize,automate
LINEAR_MAX_ASSIGNMENTS_PER_HOUR=10
LINEAR_ASSIGNMENT_COOLDOWN=300

# Workflow Configuration
LINEAR_AUTO_START_TASKS=true
LINEAR_AUTO_UPDATE_STATUS=true
LINEAR_PROGRESS_UPDATE_INTERVAL=60
LINEAR_STATUS_SYNC_INTERVAL=300
LINEAR_TASK_TIMEOUT=3600

# Event Management
LINEAR_EVENT_QUEUE_SIZE=1000
LINEAR_EVENT_BATCH_SIZE=10
LINEAR_EVENT_PROCESSING_INTERVAL=5
LINEAR_EVENT_RETRY_INTERVAL=60
LINEAR_EVENT_PERSISTENCE_ENABLED=true
LINEAR_EVENT_PERSISTENCE_FILE=linear_events.json
LINEAR_MAX_EVENT_AGE=86400

# Monitoring
LINEAR_MONITORING_ENABLED=true
LINEAR_MONITORING_INTERVAL=60
LINEAR_HEALTH_CHECK_INTERVAL=300
LINEAR_METRICS_RETENTION=86400
LINEAR_ALERT_ON_FAILURES=true
"""

