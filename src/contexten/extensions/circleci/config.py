"""
CircleCI Integration Configuration

Comprehensive configuration management for CircleCI integration with:
- Environment variable support
- Validation and security
- Default values and overrides
- Integration settings for GitHub, Codegen SDK, etc.
"""

import os
from datetime import timedelta
from typing import Dict, Any, Optional, List, Set
from pydantic import BaseModel, Field, validator, SecretStr
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class APIConfig(BaseModel):
    """CircleCI API configuration"""
    api_token: SecretStr
    api_base_url: str = "https://circleci.com/api"
    request_timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    rate_limit_requests_per_minute: int = Field(default=300, ge=1, le=1000)
    
    @validator('api_base_url')
    def validate_api_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('API base URL must start with http:// or https://')
        return v.rstrip('/')


class WebhookConfig(BaseModel):
    """Webhook processing configuration"""
    webhook_secret: Optional[SecretStr] = None
    webhook_signature_header: str = "circleci-signature"
    webhook_event_types: Set[str] = Field(default_factory=lambda: {
        "workflow-completed", "job-completed"
    })
    webhook_timeout: int = Field(default=30, ge=1, le=300)
    
    # Security settings
    validate_signatures: bool = True
    validate_timestamps: bool = True
    timestamp_tolerance: int = Field(default=300, ge=60, le=3600)  # seconds
    
    # Processing settings
    max_queue_size: int = Field(default=1000, ge=1, le=10000)
    processing_timeout: int = Field(default=60, ge=1, le=600)
    retry_failed_events: bool = True
    max_event_retries: int = Field(default=3, ge=0, le=10)
    
    # Event filtering
    ignore_ping_events: bool = False
    filter_branches: Optional[List[str]] = None  # Only process these branches
    ignore_branches: Optional[List[str]] = None  # Ignore these branches


class FailureAnalysisConfig(BaseModel):
    """Failure analysis configuration"""
    enabled: bool = True
    
    # Analysis depth
    log_analysis_depth: str = Field(default="deep", regex="^(shallow|medium|deep)$")
    max_log_lines: int = Field(default=10000, ge=100, le=100000)
    pattern_matching_enabled: bool = True
    similarity_search_enabled: bool = True
    
    # Caching
    cache_analyses: bool = True
    cache_duration: timedelta = Field(default=timedelta(hours=24))
    max_cache_size: int = Field(default=1000, ge=10, le=10000)
    
    # Learning
    pattern_learning_enabled: bool = True
    learn_from_successful_fixes: bool = True
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Analysis timeouts
    analysis_timeout: int = Field(default=300, ge=30, le=1800)  # seconds
    log_fetch_timeout: int = Field(default=60, ge=10, le=300)


class AutoFixConfig(BaseModel):
    """Auto-fix generation configuration"""
    enabled: bool = True
    
    # Fix generation
    fix_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_fixes_per_failure: int = Field(default=3, ge=1, le=10)
    fix_generation_timeout: int = Field(default=600, ge=60, le=3600)  # seconds
    
    # Fix types
    enable_code_fixes: bool = True
    enable_config_fixes: bool = True
    enable_dependency_fixes: bool = True
    
    # Validation
    validate_fixes: bool = True
    run_tests_after_fix: bool = True
    test_timeout: int = Field(default=1800, ge=60, le=7200)  # seconds
    
    # Safety
    require_human_approval: bool = False
    max_fix_attempts_per_day: int = Field(default=10, ge=1, le=100)
    blacklist_patterns: List[str] = Field(default_factory=list)


class WorkflowConfig(BaseModel):
    """Workflow automation configuration"""
    enabled: bool = True
    
    # Task management
    auto_start_tasks: bool = True
    auto_update_status: bool = True
    task_timeout: int = Field(default=3600, ge=300, le=14400)  # seconds
    max_concurrent_tasks: int = Field(default=5, ge=1, le=20)
    
    # Progress tracking
    progress_update_interval: int = Field(default=30, ge=10, le=300)  # seconds
    send_progress_notifications: bool = True
    
    # Workflow coordination
    coordinate_with_github: bool = True
    coordinate_with_linear: bool = False
    coordinate_with_slack: bool = False


class GitHubIntegrationConfig(BaseModel):
    """GitHub integration configuration"""
    enabled: bool = True
    github_token: Optional[SecretStr] = None
    
    # PR settings
    auto_create_prs: bool = True
    pr_auto_merge: bool = False
    pr_branch_prefix: str = "circleci-fix"
    pr_title_template: str = "🔧 Fix CircleCI build failure: {failure_type}"
    pr_description_template: str = """
## CircleCI Build Fix

**Failure Type**: {failure_type}
**Root Cause**: {root_cause}
**Confidence**: {confidence}

### Changes Made
{changes_description}

### Validation
{validation_results}

---
*This PR was automatically generated by the CircleCI integration.*
"""
    
    # Review settings
    request_reviews: bool = False
    default_reviewers: List[str] = Field(default_factory=list)
    assign_to_author: bool = True
    
    # Labels and metadata
    add_labels: bool = True
    default_labels: List[str] = Field(default_factory=lambda: [
        "circleci", "automated-fix", "ci-fix"
    ])


class CodegenIntegrationConfig(BaseModel):
    """Codegen SDK integration configuration"""
    enabled: bool = True
    codegen_api_token: Optional[SecretStr] = None
    codegen_org_id: Optional[str] = None
    codegen_base_url: str = "https://api.codegen.com"
    
    # Task settings
    default_task_timeout: int = Field(default=1800, ge=300, le=7200)  # seconds
    max_task_retries: int = Field(default=2, ge=0, le=5)
    
    # Prompt settings
    use_enhanced_prompts: bool = True
    include_context: bool = True
    context_max_lines: int = Field(default=500, ge=50, le=2000)


class NotificationConfig(BaseModel):
    """Notification configuration"""
    enabled: bool = True
    
    # Notification types
    notify_on_failure: bool = True
    notify_on_fix_generated: bool = True
    notify_on_fix_applied: bool = True
    notify_on_fix_success: bool = True
    notify_on_fix_failure: bool = True
    
    # Channels
    slack_enabled: bool = False
    slack_webhook_url: Optional[SecretStr] = None
    slack_channel: Optional[str] = None
    
    email_enabled: bool = False
    email_recipients: List[str] = Field(default_factory=list)
    
    # Rate limiting
    max_notifications_per_hour: int = Field(default=10, ge=1, le=100)


class MonitoringConfig(BaseModel):
    """Monitoring and metrics configuration"""
    enabled: bool = True
    
    # Metrics collection
    collect_metrics: bool = True
    metrics_retention_days: int = Field(default=30, ge=1, le=365)
    
    # Health checks
    health_check_interval: int = Field(default=300, ge=60, le=3600)  # seconds
    health_check_timeout: int = Field(default=30, ge=5, le=300)
    
    # Alerting
    alert_on_failures: bool = True
    alert_threshold_failure_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    alert_threshold_response_time: float = Field(default=30.0, ge=1.0, le=300.0)  # seconds


class SecurityConfig(BaseModel):
    """Security configuration"""
    # Credential management
    use_environment_variables: bool = True
    credential_rotation_enabled: bool = False
    credential_rotation_interval: timedelta = Field(default=timedelta(days=90))
    
    # Access control
    allowed_organizations: Optional[List[str]] = None
    allowed_projects: Optional[List[str]] = None
    blocked_projects: List[str] = Field(default_factory=list)
    
    # Audit logging
    audit_logging_enabled: bool = True
    audit_log_retention_days: int = Field(default=90, ge=1, le=365)
    
    # Rate limiting
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = Field(default=100, ge=1, le=1000)


class CircleCIIntegrationConfig(BaseModel):
    """
    Comprehensive CircleCI integration configuration
    """
    
    # Core configuration sections
    api: APIConfig
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    failure_analysis: FailureAnalysisConfig = Field(default_factory=FailureAnalysisConfig)
    auto_fix: AutoFixConfig = Field(default_factory=AutoFixConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    github: GitHubIntegrationConfig = Field(default_factory=GitHubIntegrationConfig)
    codegen: CodegenIntegrationConfig = Field(default_factory=CodegenIntegrationConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Global settings
    debug_mode: bool = False
    dry_run_mode: bool = False
    
    # Project filtering
    monitor_all_projects: bool = True
    monitored_projects: List[str] = Field(default_factory=list)
    ignored_projects: List[str] = Field(default_factory=list)
    
    class Config:
        env_prefix = "CIRCLECI_"
        case_sensitive = False
    
    @classmethod
    def from_env(cls) -> "CircleCIIntegrationConfig":
        """Create configuration from environment variables"""
        
        # Required environment variables
        api_token = os.getenv("CIRCLECI_API_TOKEN")
        if not api_token:
            raise ValueError("CIRCLECI_API_TOKEN environment variable is required")
        
        # Build API config
        api_config = APIConfig(
            api_token=api_token,
            api_base_url=os.getenv("CIRCLECI_API_BASE_URL", "https://circleci.com/api"),
            request_timeout=int(os.getenv("CIRCLECI_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("CIRCLECI_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("CIRCLECI_RETRY_DELAY", "1.0")),
            rate_limit_requests_per_minute=int(os.getenv("CIRCLECI_RATE_LIMIT", "300"))
        )
        
        # Build webhook config
        webhook_config = WebhookConfig(
            webhook_secret=os.getenv("CIRCLECI_WEBHOOK_SECRET"),
            validate_signatures=os.getenv("CIRCLECI_VALIDATE_SIGNATURES", "true").lower() == "true",
            max_queue_size=int(os.getenv("CIRCLECI_WEBHOOK_QUEUE_SIZE", "1000"))
        )
        
        # Build GitHub config
        github_config = GitHubIntegrationConfig(
            enabled=os.getenv("CIRCLECI_GITHUB_ENABLED", "true").lower() == "true",
            github_token=os.getenv("GITHUB_TOKEN"),
            auto_create_prs=os.getenv("CIRCLECI_AUTO_CREATE_PRS", "true").lower() == "true"
        )
        
        # Build Codegen config
        codegen_config = CodegenIntegrationConfig(
            enabled=os.getenv("CIRCLECI_CODEGEN_ENABLED", "true").lower() == "true",
            codegen_api_token=os.getenv("CODEGEN_API_TOKEN"),
            codegen_org_id=os.getenv("CODEGEN_ORG_ID")
        )
        
        # Build main config
        config = cls(
            api=api_config,
            webhook=webhook_config,
            github=github_config,
            codegen=codegen_config,
            debug_mode=os.getenv("CIRCLECI_DEBUG", "false").lower() == "true",
            dry_run_mode=os.getenv("CIRCLECI_DRY_RUN", "false").lower() == "true"
        )
        
        logger.info("Configuration loaded from environment variables")
        return config
    
    @classmethod
    def from_file(cls, config_path: Path) -> "CircleCIIntegrationConfig":
        """Load configuration from file"""
        import yaml
        import json
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        logger.info(f"Configuration loaded from file: {config_path}")
        return cls(**data)
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required tokens
        if not self.api.api_token:
            issues.append("CircleCI API token is required")
        
        if self.github.enabled and not self.github.github_token:
            issues.append("GitHub token is required when GitHub integration is enabled")
        
        if self.codegen.enabled and not self.codegen.codegen_api_token:
            issues.append("Codegen API token is required when Codegen integration is enabled")
        
        if self.webhook.validate_signatures and not self.webhook.webhook_secret:
            issues.append("Webhook secret is required when signature validation is enabled")
        
        # Check logical constraints
        if self.auto_fix.enabled and not self.failure_analysis.enabled:
            issues.append("Failure analysis must be enabled when auto-fix is enabled")
        
        if self.workflow.coordinate_with_github and not self.github.enabled:
            issues.append("GitHub integration must be enabled for workflow coordination")
        
        # Check notification settings
        if self.notifications.slack_enabled and not self.notifications.slack_webhook_url:
            issues.append("Slack webhook URL is required when Slack notifications are enabled")
        
        if self.notifications.email_enabled and not self.notifications.email_recipients:
            issues.append("Email recipients are required when email notifications are enabled")
        
        return issues
    
    def get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration with resolved values"""
        config_dict = self.dict()
        
        # Resolve secret values for display (masked)
        def mask_secrets(obj):
            if isinstance(obj, dict):
                return {k: mask_secrets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [mask_secrets(item) for item in obj]
            elif isinstance(obj, SecretStr):
                return "***MASKED***"
            else:
                return obj
        
        return mask_secrets(config_dict)
    
    def save_to_file(self, config_path: Path, format: str = "yaml"):
        """Save configuration to file"""
        import yaml
        import json
        
        config_dict = self.get_effective_config()
        
        with open(config_path, 'w') as f:
            if format.lower() in ['yaml', 'yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif format.lower() == 'json':
                json.dump(config_dict, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Configuration saved to: {config_path}")
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in updates.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), BaseModel):
                    # Update nested config
                    getattr(self, key).update_from_dict(value)
                else:
                    setattr(self, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")
    
    @property
    def is_production_ready(self) -> bool:
        """Check if configuration is ready for production use"""
        issues = self.validate_configuration()
        return len(issues) == 0 and not self.debug_mode and not self.dry_run_mode
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "api_configured": bool(self.api.api_token),
            "webhook_configured": bool(self.webhook.webhook_secret),
            "github_enabled": self.github.enabled,
            "codegen_enabled": self.codegen.enabled,
            "auto_fix_enabled": self.auto_fix.enabled,
            "failure_analysis_enabled": self.failure_analysis.enabled,
            "workflow_enabled": self.workflow.enabled,
            "notifications_enabled": self.notifications.enabled,
            "monitoring_enabled": self.monitoring.enabled,
            "debug_mode": self.debug_mode,
            "dry_run_mode": self.dry_run_mode,
            "production_ready": self.is_production_ready
        }

