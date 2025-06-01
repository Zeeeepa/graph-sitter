"""
Configuration Management for Prefect Orchestration

This module provides centralized configuration management for the orchestration
system, including environment-based settings and validation.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class CodegenConfig:
    """Configuration for Codegen SDK integration"""
    org_id: str
    token: str
    api_url: Optional[str] = None
    timeout_seconds: int = 3600
    max_retries: int = 3


@dataclass
class PrefectConfig:
    """Configuration for Prefect server"""
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    workspace: Optional[str] = None
    deployment_concurrency: int = 10
    flow_run_timeout: int = 7200  # 2 hours


@dataclass
class GitHubConfig:
    """Configuration for GitHub integration"""
    token: Optional[str] = None
    repository: Optional[str] = None
    webhook_secret: Optional[str] = None
    api_timeout: int = 30


@dataclass
class SlackConfig:
    """Configuration for Slack notifications"""
    webhook_url: Optional[str] = None
    channel: str = "#ci-cd-alerts"
    username: str = "Autonomous CI/CD"
    icon_emoji: str = ":robot_face:"


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and health checks"""
    enabled: bool = True
    health_check_interval: int = 300  # 5 minutes
    performance_history_size: int = 1000
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "cpu_usage_percent": 80,
        "memory_usage_percent": 85,
        "error_rate_percent": 10,
        "response_time_ms": 5000,
        "health_score": 70
    })


@dataclass
class RecoveryConfig:
    """Configuration for recovery management"""
    enabled: bool = True
    max_concurrent_recoveries: int = 3
    recovery_timeout: int = 1800  # 30 minutes
    escalation_threshold: int = 3
    auto_restart_enabled: bool = False


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""
    default_timeout: int = 3600  # 1 hour
    max_concurrent_workflows: int = 5
    retry_delay_seconds: int = 60
    max_retries: int = 3
    resource_limits: Dict[str, str] = field(default_factory=lambda: {
        "memory": "2GB",
        "cpu": "1"
    })


@dataclass
class OrchestrationConfig:
    """Complete orchestration system configuration"""
    
    # Core integrations
    codegen: CodegenConfig
    prefect: PrefectConfig = field(default_factory=PrefectConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    
    # System components
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    recovery: RecoveryConfig = field(default_factory=RecoveryConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    
    # Environment
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    
    # Storage
    data_directory: Path = field(default_factory=lambda: Path.home() / ".contexten" / "orchestration")
    
    @classmethod
    def from_environment(cls) -> "OrchestrationConfig":
        """Create configuration from environment variables"""
        
        # Required Codegen configuration
        codegen_org_id = os.environ.get("CODEGEN_ORG_ID")
        codegen_token = os.environ.get("CODEGEN_TOKEN")
        
        if not codegen_org_id or not codegen_token:
            raise ValueError("CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables are required")
        
        codegen_config = CodegenConfig(
            org_id=codegen_org_id,
            token=codegen_token,
            api_url=os.environ.get("CODEGEN_API_URL"),
            timeout_seconds=int(os.environ.get("CODEGEN_TIMEOUT", "3600")),
            max_retries=int(os.environ.get("CODEGEN_MAX_RETRIES", "3"))
        )
        
        # Prefect configuration
        prefect_config = PrefectConfig(
            api_url=os.environ.get("PREFECT_API_URL"),
            api_key=os.environ.get("PREFECT_API_KEY"),
            workspace=os.environ.get("PREFECT_WORKSPACE"),
            deployment_concurrency=int(os.environ.get("PREFECT_DEPLOYMENT_CONCURRENCY", "10")),
            flow_run_timeout=int(os.environ.get("PREFECT_FLOW_RUN_TIMEOUT", "7200"))
        )
        
        # GitHub configuration
        github_config = GitHubConfig(
            token=os.environ.get("GITHUB_TOKEN"),
            repository=os.environ.get("GITHUB_REPOSITORY"),
            webhook_secret=os.environ.get("GITHUB_WEBHOOK_SECRET"),
            api_timeout=int(os.environ.get("GITHUB_API_TIMEOUT", "30"))
        )
        
        # Slack configuration
        slack_config = SlackConfig(
            webhook_url=os.environ.get("SLACK_WEBHOOK_URL"),
            channel=os.environ.get("SLACK_CHANNEL", "#ci-cd-alerts"),
            username=os.environ.get("SLACK_USERNAME", "Autonomous CI/CD"),
            icon_emoji=os.environ.get("SLACK_ICON_EMOJI", ":robot_face:")
        )
        
        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            enabled=os.environ.get("MONITORING_ENABLED", "true").lower() == "true",
            health_check_interval=int(os.environ.get("HEALTH_CHECK_INTERVAL", "300")),
            performance_history_size=int(os.environ.get("PERFORMANCE_HISTORY_SIZE", "1000"))
        )
        
        # Recovery configuration
        recovery_config = RecoveryConfig(
            enabled=os.environ.get("RECOVERY_ENABLED", "true").lower() == "true",
            max_concurrent_recoveries=int(os.environ.get("MAX_CONCURRENT_RECOVERIES", "3")),
            recovery_timeout=int(os.environ.get("RECOVERY_TIMEOUT", "1800")),
            escalation_threshold=int(os.environ.get("ESCALATION_THRESHOLD", "3")),
            auto_restart_enabled=os.environ.get("AUTO_RESTART_ENABLED", "false").lower() == "true"
        )
        
        # Workflow configuration
        workflow_config = WorkflowConfig(
            default_timeout=int(os.environ.get("WORKFLOW_DEFAULT_TIMEOUT", "3600")),
            max_concurrent_workflows=int(os.environ.get("MAX_CONCURRENT_WORKFLOWS", "5")),
            retry_delay_seconds=int(os.environ.get("WORKFLOW_RETRY_DELAY", "60")),
            max_retries=int(os.environ.get("WORKFLOW_MAX_RETRIES", "3"))
        )
        
        # Data directory
        data_dir = os.environ.get("ORCHESTRATION_DATA_DIR")
        if data_dir:
            data_directory = Path(data_dir)
        else:
            data_directory = Path.home() / ".contexten" / "orchestration"
        
        return cls(
            codegen=codegen_config,
            prefect=prefect_config,
            github=github_config,
            slack=slack_config,
            monitoring=monitoring_config,
            recovery=recovery_config,
            workflow=workflow_config,
            environment=os.environ.get("ENVIRONMENT", "production"),
            debug=os.environ.get("DEBUG", "false").lower() == "true",
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            data_directory=data_directory
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        
        issues = []
        
        # Validate required fields
        if not self.codegen.org_id:
            issues.append("Codegen org_id is required")
        
        if not self.codegen.token:
            issues.append("Codegen token is required")
        
        # Validate timeouts
        if self.workflow.default_timeout <= 0:
            issues.append("Workflow default timeout must be positive")
        
        if self.monitoring.health_check_interval <= 0:
            issues.append("Health check interval must be positive")
        
        # Validate concurrency limits
        if self.workflow.max_concurrent_workflows <= 0:
            issues.append("Max concurrent workflows must be positive")
        
        if self.recovery.max_concurrent_recoveries <= 0:
            issues.append("Max concurrent recoveries must be positive")
        
        # Validate data directory
        try:
            self.data_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create data directory {self.data_directory}: {e}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        
        def _convert_dataclass(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: _convert_dataclass(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: _convert_dataclass(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_convert_dataclass(item) for item in obj]
            else:
                return obj
        
        return _convert_dataclass(self)
    
    def save_to_file(self, file_path: Path):
        """Save configuration to file"""
        
        import json
        
        config_dict = self.to_dict()
        
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {file_path}")
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> "OrchestrationConfig":
        """Load configuration from file"""
        
        import json
        
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        # This would need more sophisticated deserialization
        # For now, prefer environment-based configuration
        logger.warning("File-based configuration loading not fully implemented, using environment")
        return cls.from_environment()


def get_default_config() -> OrchestrationConfig:
    """Get default configuration from environment"""
    
    try:
        config = OrchestrationConfig.from_environment()
        
        # Validate configuration
        issues = config.validate()
        if issues:
            logger.warning(f"Configuration issues found: {issues}")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def create_sample_config_file(file_path: Path):
    """Create a sample configuration file"""
    
    sample_config = {
        "environment_variables": {
            "CODEGEN_ORG_ID": "your-org-id-here",
            "CODEGEN_TOKEN": "your-token-here",
            "GITHUB_TOKEN": "your-github-token-here",
            "SLACK_WEBHOOK_URL": "your-slack-webhook-url-here",
            "PREFECT_API_URL": "http://localhost:4200/api",
            "MONITORING_ENABLED": "true",
            "RECOVERY_ENABLED": "true",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO"
        },
        "description": "Sample configuration for Autonomous CI/CD Orchestration",
        "instructions": [
            "1. Copy this file to .env in your project root",
            "2. Replace placeholder values with your actual credentials",
            "3. Set environment variables or source the .env file",
            "4. Run the orchestration system"
        ]
    }
    
    import json
    
    with open(file_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info(f"Sample configuration created at {file_path}")


if __name__ == "__main__":
    # Create sample configuration
    sample_path = Path("orchestration-config-sample.json")
    create_sample_config_file(sample_path)
    
    # Try to load configuration from environment
    try:
        config = get_default_config()
        print("✅ Configuration loaded successfully")
        print(f"Environment: {config.environment}")
        print(f"Debug: {config.debug}")
        print(f"Monitoring enabled: {config.monitoring.enabled}")
        print(f"Recovery enabled: {config.recovery.enabled}")
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        print("Please set required environment variables (CODEGEN_ORG_ID, CODEGEN_TOKEN)")

