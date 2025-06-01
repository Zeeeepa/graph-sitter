"""
Prefect Configuration for Autonomous CI/CD

Provides configuration management for Prefect workflows and autonomous operations.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class PrefectConfig(BaseSettings):
    """Configuration for Prefect integration"""
    
    # Prefect API Configuration
    api_key: Optional[str] = Field(default=None, env="PREFECT_API_KEY")
    api_url: str = Field(default="https://api.prefect.cloud/api/accounts", env="PREFECT_API_URL")
    workspace: Optional[str] = Field(default=None, env="PREFECT_WORKSPACE")
    
    # Autonomous CI/CD Settings
    auto_fix_confidence_threshold: float = Field(default=0.75, env="AUTO_FIX_CONFIDENCE_THRESHOLD")
    max_auto_fixes_per_day: int = Field(default=10, env="MAX_AUTO_FIXES_PER_DAY")
    performance_regression_threshold: float = Field(default=20.0, env="PERFORMANCE_REGRESSION_THRESHOLD")
    
    # Workflow Scheduling
    maintenance_schedule: str = Field(default="0 2 * * *", env="MAINTENANCE_SCHEDULE")  # Daily at 2 AM
    security_scan_schedule: str = Field(default="0 */6 * * *", env="SECURITY_SCAN_SCHEDULE")  # Every 6 hours
    performance_check_schedule: str = Field(default="*/30 * * * *", env="PERFORMANCE_CHECK_SCHEDULE")  # Every 30 min
    
    # Integration Settings
    codegen_org_id: Optional[str] = Field(default=None, env="CODEGEN_ORG_ID")
    codegen_token: Optional[str] = Field(default=None, env="CODEGEN_TOKEN")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    linear_api_key: Optional[str] = Field(default=None, env="LINEAR_API_KEY")
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Monitoring and Alerting
    enable_slack_notifications: bool = Field(default=True, env="ENABLE_SLACK_NOTIFICATIONS")
    enable_email_notifications: bool = Field(default=False, env="ENABLE_EMAIL_NOTIFICATIONS")
    notification_email: Optional[str] = Field(default=None, env="NOTIFICATION_EMAIL")
    
    # Safety Settings
    enable_auto_fixes: bool = Field(default=True, env="ENABLE_AUTO_FIXES")
    enable_auto_deployments: bool = Field(default=False, env="ENABLE_AUTO_DEPLOYMENTS")
    require_human_approval: bool = Field(default=True, env="REQUIRE_HUMAN_APPROVAL")
    
    # Performance Settings
    max_concurrent_workflows: int = Field(default=5, env="MAX_CONCURRENT_WORKFLOWS")
    workflow_timeout_minutes: int = Field(default=60, env="WORKFLOW_TIMEOUT_MINUTES")
    task_retry_attempts: int = Field(default=3, env="TASK_RETRY_ATTEMPTS")
    
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

