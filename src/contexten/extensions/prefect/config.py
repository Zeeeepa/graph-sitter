"""
Prefect Configuration for Autonomous CI/CD

Provides configuration management for Prefect workflows and autonomous operations.
"""

from typing import Optional, Dict, Any
import os

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class PrefectConfig(BaseSettings):
    """Configuration for Prefect integration"""
    
    # Prefect API Configuration
    api_key: Optional[str] = None
    api_url: str = "https://api.prefect.cloud/api/accounts"
    workspace: Optional[str] = None
    
    # Autonomous CI/CD Settings
    auto_fix_confidence_threshold: float = 0.75
    max_auto_fixes_per_day: int = 10
    performance_regression_threshold: float = 20.0
    
    # Workflow Scheduling
    maintenance_schedule: str = "0 2 * * *"  # Daily at 2 AM
    security_scan_schedule: str = "0 */6 * * *"  # Every 6 hours
    performance_check_schedule: str = "*/30 * * * *"  # Every 30 min
    
    # Integration Settings
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    github_token: Optional[str] = None
    linear_api_key: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    # Monitoring and Alerting
    enable_slack_notifications: bool = True
    enable_email_notifications: bool = False
    notification_email: Optional[str] = None
    
    # Safety Settings
    enable_auto_fixes: bool = True
    enable_auto_deployments: bool = False
    require_human_approval: bool = True
    
    # Performance Settings
    max_concurrent_workflows: int = 5
    workflow_timeout_minutes: int = 60
    task_retry_attempts: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class WorkflowConfig(BaseModel):
    """Configuration for individual workflows"""
    
    name: str
    description: str
    schedule: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout_minutes: int = 60
    retry_attempts: int = 3
    enable_notifications: bool = True


class TaskConfig(BaseModel):
    """Configuration for individual tasks"""
    
    name: str
    description: str
    timeout_minutes: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 60
    cache_expiration_minutes: Optional[int] = None
    tags: list[str] = Field(default_factory=list)


# Predefined workflow configurations
AUTONOMOUS_MAINTENANCE_CONFIG = WorkflowConfig(
    name="autonomous-maintenance",
    description="Daily autonomous maintenance workflow",
    schedule="0 2 * * *",  # Daily at 2 AM UTC
    tags=["autonomous", "maintenance", "daily"],
    timeout_minutes=120,
    parameters={
        "include_security_scan": True,
        "include_performance_check": True,
        "include_dependency_update": True,
    }
)

FAILURE_ANALYSIS_CONFIG = WorkflowConfig(
    name="failure-analysis",
    description="Analyze and fix CI/CD failures",
    tags=["autonomous", "failure", "analysis"],
    timeout_minutes=60,
    parameters={
        "auto_fix_enabled": True,
        "confidence_threshold": 0.75,
    }
)

DEPENDENCY_UPDATE_CONFIG = WorkflowConfig(
    name="dependency-update",
    description="Smart dependency updates with testing",
    schedule="0 6 * * 1",  # Weekly on Monday at 6 AM
    tags=["autonomous", "dependencies", "security"],
    timeout_minutes=90,
    parameters={
        "update_strategy": "smart",
        "security_priority": "high",
        "run_tests": True,
    }
)

PERFORMANCE_OPTIMIZATION_CONFIG = WorkflowConfig(
    name="performance-optimization",
    description="Monitor and optimize system performance",
    schedule="*/30 * * * *",  # Every 30 minutes
    tags=["autonomous", "performance", "monitoring"],
    timeout_minutes=30,
    parameters={
        "regression_threshold": 20.0,
        "auto_optimize": True,
    }
)


def get_config() -> PrefectConfig:
    """Get the current Prefect configuration"""
    return PrefectConfig()


def validate_config(config: PrefectConfig) -> tuple[bool, list[str]]:
    """Validate the Prefect configuration"""
    errors = []
    
    # Check required fields for autonomous operation
    if not config.codegen_org_id:
        errors.append("CODEGEN_ORG_ID is required for autonomous operations")
    
    if not config.codegen_token:
        errors.append("CODEGEN_TOKEN is required for autonomous operations")
    
    if not config.github_token:
        errors.append("GITHUB_TOKEN is required for GitHub integration")
    
    # Validate thresholds
    if config.auto_fix_confidence_threshold < 0.5 or config.auto_fix_confidence_threshold > 1.0:
        errors.append("AUTO_FIX_CONFIDENCE_THRESHOLD must be between 0.5 and 1.0")
    
    if config.performance_regression_threshold <= 0:
        errors.append("PERFORMANCE_REGRESSION_THRESHOLD must be positive")
    
    if config.max_auto_fixes_per_day <= 0:
        errors.append("MAX_AUTO_FIXES_PER_DAY must be positive")
    
    # Validate notification settings
    if config.enable_slack_notifications and not config.slack_webhook_url:
        errors.append("SLACK_WEBHOOK_URL is required when Slack notifications are enabled")
    
    if config.enable_email_notifications and not config.notification_email:
        errors.append("NOTIFICATION_EMAIL is required when email notifications are enabled")
    
    return len(errors) == 0, errors


def get_workflow_configs() -> Dict[str, WorkflowConfig]:
    """Get all predefined workflow configurations"""
    return {
        "autonomous_maintenance": AUTONOMOUS_MAINTENANCE_CONFIG,
        "failure_analysis": FAILURE_ANALYSIS_CONFIG,
        "dependency_update": DEPENDENCY_UPDATE_CONFIG,
        "performance_optimization": PERFORMANCE_OPTIMIZATION_CONFIG,
    }
