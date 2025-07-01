"""
Configuration management for the orchestration system.

This module provides configuration classes and utilities for managing
the autonomous CI/CD orchestration system settings.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class OrchestrationConfig:
    """
    Configuration for the autonomous orchestration system.
    
    This class contains all configuration options for the orchestrator,
    including credentials, system settings, and operational parameters.
    """
    
    # Core Credentials
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    github_token: Optional[str] = None
    linear_api_key: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    # Prefect Configuration
    prefect_api_url: Optional[str] = None
    prefect_workspace: Optional[str] = None
    prefect_work_pool: str = "default-agent-pool"
    
    # System Configuration
    max_concurrent_workflows: int = 5
    default_timeout_minutes: int = 30
    auto_recovery_enabled: bool = True
    monitoring_enabled: bool = True
    
    # Health Check Configuration
    health_check_interval_minutes: int = 15
    performance_monitoring_interval_minutes: int = 60
    dependency_check_interval_hours: int = 24
    
    # Alert Configuration
    alert_thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "cpu_usage_percent": 80,
        "memory_usage_percent": 80,
        "disk_usage_percent": 90,
        "api_response_time_seconds": 30,
        "error_rate_percent": 10
    })
    
    # Workflow Configuration
    workflow_retry_attempts: int = 3
    workflow_retry_delay_seconds: int = 60
    enable_workflow_caching: bool = True
    
    # Integration Configuration
    linear_team_id: Optional[str] = None
    github_repository: Optional[str] = None
    slack_channel: Optional[str] = None
    
    # Advanced Configuration
    enable_predictive_maintenance: bool = False
    enable_autonomous_refactoring: bool = False
    enable_intelligent_deployment: bool = False
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file_path: Optional[str] = None
    enable_structured_logging: bool = True
    
    def __post_init__(self):
        """Post-initialization to load from environment variables if not set"""
        self._load_from_environment()
        self._validate_configuration()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            "codegen_org_id": "CODEGEN_ORG_ID",
            "codegen_token": "CODEGEN_TOKEN",
            "github_token": "GITHUB_TOKEN",
            "linear_api_key": "LINEAR_API_KEY",
            "slack_webhook_url": "SLACK_WEBHOOK_URL",
            "prefect_api_url": "PREFECT_API_URL",
            "prefect_workspace": "PREFECT_WORKSPACE",
            "linear_team_id": "LINEAR_TEAM_ID",
            "github_repository": "GITHUB_REPOSITORY",
            "slack_channel": "SLACK_CHANNEL"
        }
        
        for attr_name, env_var in env_mappings.items():
            if getattr(self, attr_name) is None:
                env_value = os.getenv(env_var)
                if env_value:
                    setattr(self, attr_name, env_value)
        
        # Load boolean configurations
        bool_env_mappings = {
            "auto_recovery_enabled": "AUTO_RECOVERY_ENABLED",
            "monitoring_enabled": "MONITORING_ENABLED",
            "enable_predictive_maintenance": "ENABLE_PREDICTIVE_MAINTENANCE",
            "enable_autonomous_refactoring": "ENABLE_AUTONOMOUS_REFACTORING",
            "enable_intelligent_deployment": "ENABLE_INTELLIGENT_DEPLOYMENT"
        }
        
        for attr_name, env_var in bool_env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                setattr(self, attr_name, env_value.lower() in ("true", "1", "yes", "on"))
        
        # Load integer configurations
        int_env_mappings = {
            "max_concurrent_workflows": "MAX_CONCURRENT_WORKFLOWS",
            "default_timeout_minutes": "DEFAULT_TIMEOUT_MINUTES",
            "health_check_interval_minutes": "HEALTH_CHECK_INTERVAL_MINUTES",
            "workflow_retry_attempts": "WORKFLOW_RETRY_ATTEMPTS"
        }
        
        for attr_name, env_var in int_env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    setattr(self, attr_name, int(env_value))
                except ValueError:
                    pass  # Keep default value if conversion fails
    
    def _validate_configuration(self):
        """Validate the configuration"""
        errors = []
        
        # Check required credentials
        if not self.codegen_org_id:
            errors.append("codegen_org_id is required")
        if not self.codegen_token:
            errors.append("codegen_token is required")
        
        # Validate numeric ranges
        if self.max_concurrent_workflows < 1:
            errors.append("max_concurrent_workflows must be at least 1")
        if self.default_timeout_minutes < 1:
            errors.append("default_timeout_minutes must be at least 1")
        if self.health_check_interval_minutes < 1:
            errors.append("health_check_interval_minutes must be at least 1")
        
        # Validate alert thresholds
        for threshold_name, threshold_value in self.alert_thresholds.items():
            if isinstance(threshold_value, (int, float)) and threshold_value < 0:
                errors.append(f"alert_threshold {threshold_name} must be non-negative")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "OrchestrationConfig":
        """Create configuration from dictionary"""
        return cls(**config_dict)
    
    @classmethod
    def from_file(cls, config_path: Path) -> "OrchestrationConfig":
        """Load configuration from file"""
        import json
        import yaml
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ('.yml', '.yaml'):
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        return cls.from_dict(config_data)
    
    def save_to_file(self, config_path: Path, format: str = "yaml"):
        """Save configuration to file"""
        import json
        import yaml
        
        config_path = Path(config_path)
        config_data = self.to_dict()
        
        # Remove None values for cleaner output
        config_data = {k: v for k, v in config_data.items() if v is not None}
        
        with open(config_path, 'w') as f:
            if format.lower() in ('yml', 'yaml'):
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            elif format.lower() == 'json':
                json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def get_prefect_settings(self) -> Dict[str, str]:
        """Get Prefect-specific settings as environment variables"""
        settings = {}
        
        if self.prefect_api_url:
            settings["PREFECT_API_URL"] = self.prefect_api_url
        if self.prefect_workspace:
            settings["PREFECT_WORKSPACE"] = self.prefect_workspace
        
        return settings
    
    def get_integration_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get integration-specific settings"""
        return {
            "codegen": {
                "org_id": self.codegen_org_id,
                "token": self.codegen_token
            },
            "github": {
                "token": self.github_token,
                "repository": self.github_repository
            },
            "linear": {
                "api_key": self.linear_api_key,
                "team_id": self.linear_team_id
            },
            "slack": {
                "webhook_url": self.slack_webhook_url,
                "channel": self.slack_channel
            }
        }
    
    def is_integration_enabled(self, integration_name: str) -> bool:
        """Check if a specific integration is enabled"""
        integration_checks = {
            "codegen": self.codegen_org_id and self.codegen_token,
            "github": self.github_token,
            "linear": self.linear_api_key,
            "slack": self.slack_webhook_url
        }
        
        return integration_checks.get(integration_name, False)
    
    def get_enabled_integrations(self) -> List[str]:
        """Get list of enabled integrations"""
        return [
            integration for integration in ["codegen", "github", "linear", "slack"]
            if self.is_integration_enabled(integration)
        ]


def load_default_config() -> OrchestrationConfig:
    """Load default configuration with environment variable overrides"""
    return OrchestrationConfig()


def load_config_from_file(config_path: str) -> OrchestrationConfig:
    """Load configuration from a file"""
    return OrchestrationConfig.from_file(Path(config_path))


def create_sample_config_file(output_path: str = "orchestration_config.yaml"):
    """Create a sample configuration file"""
    sample_config = OrchestrationConfig(
        codegen_org_id="your-org-id-here",
        codegen_token="your-token-here",
        github_token="your-github-token-here",
        linear_api_key="your-linear-api-key-here",
        slack_webhook_url="your-slack-webhook-url-here"
    )
    
    sample_config.save_to_file(Path(output_path))
    print(f"Sample configuration file created: {output_path}")
    print("Please update the credentials and settings as needed.")

