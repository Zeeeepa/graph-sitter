"""
Configuration classes for CircleCI extension
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APIConfig:
    """CircleCI API configuration"""
    api_token: str
    api_url: str = "https://circleci.com/api/v2"
    timeout: int = 30


@dataclass
class WebhookConfig:
    """CircleCI webhook configuration"""
    webhook_secret: str
    validate_signatures: bool = True
    max_queue_size: int = 100
    ignore_ping_events: bool = True


@dataclass
class AutoFixConfig:
    """Auto-fix configuration"""
    enabled: bool = False
    fix_confidence_threshold: float = 0.8
    max_attempts: int = 3
    dry_run: bool = True


@dataclass
class FailureAnalysisConfig:
    """Failure analysis configuration"""
    enabled: bool = True
    analysis_timeout: int = 60
    max_log_size: int = 10000
    store_analysis_results: bool = True


@dataclass
class WorkflowAutomationConfig:
    """Workflow automation configuration"""
    enabled: bool = False
    auto_retry_failed_jobs: bool = False
    max_retries: int = 3
    retry_delay: int = 300


@dataclass
class NotificationConfig:
    """Notification configuration"""
    enabled: bool = False
    slack_webhook_url: Optional[str] = None
    email_notifications: bool = False
    notification_level: str = "error"


@dataclass
class GitHubConfig:
    """GitHub integration configuration"""
    enabled: bool = False
    token: Optional[str] = None
    create_issues: bool = True
    auto_assign: bool = True


@dataclass
class CodegenConfig:
    """Codegen integration configuration"""
    enabled: bool = False
    api_token: Optional[str] = None
    auto_fix: bool = True


@dataclass
class CircleCIIntegrationConfig:
    """Main CircleCI integration configuration"""
    api: APIConfig
    webhook: WebhookConfig
    auto_fix: AutoFixConfig = field(default_factory=AutoFixConfig)
    failure_analysis: FailureAnalysisConfig = field(default_factory=FailureAnalysisConfig)
    workflow_automation: WorkflowAutomationConfig = field(default_factory=WorkflowAutomationConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    codegen: CodegenConfig = field(default_factory=CodegenConfig)
    debug_mode: bool = False
    dry_run_mode: bool = False

    @property
    def is_production_ready(self) -> bool:
        """Check if configuration is ready for production use"""
        return not (self.debug_mode or self.dry_run_mode)

    def validate_configuration(self) -> list[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # API validation
        if not self.api.api_token or len(self.api.api_token) < 32:
            issues.append("Invalid API token")

        # Webhook validation
        if self.webhook.validate_signatures and not self.webhook.webhook_secret:
            issues.append("Webhook secret required when signature validation is enabled")

        # Integration validation
        if self.github.enabled and not self.github.token:
            issues.append("GitHub token required when GitHub integration is enabled")

        if self.codegen.enabled and not self.codegen.api_token:
            issues.append("Codegen API token required when Codegen integration is enabled")

        if self.notifications.enabled and not self.notifications.slack_webhook_url:
            issues.append("Slack webhook URL required when notifications are enabled")

        return issues

    @property
    def summary(self) -> dict:
        """Get configuration summary"""
        return {
            "api_configured": bool(self.api.api_token),
            "webhook_configured": bool(self.webhook.webhook_secret),
            "debug_mode": self.debug_mode,
            "production_ready": self.is_production_ready,
            "integrations": {
                "github": self.github.enabled,
                "codegen": self.codegen.enabled,
                "notifications": self.notifications.enabled
            },
            "features": {
                "auto_fix": self.auto_fix.enabled,
                "failure_analysis": self.failure_analysis.enabled,
                "workflow_automation": self.workflow_automation.enabled
            }
        }

