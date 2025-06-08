"""
Configuration management for Grainchain integration.

This module handles configuration loading, validation, and management
for the Grainchain integration system.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import SandboxProvider, QualityGateType


@dataclass
class ProviderConfig:
    """Configuration for a specific sandbox provider."""
    enabled: bool = True
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    template: Optional[str] = None
    image_id: Optional[str] = None
    workspace_template: Optional[str] = None
    timeout: int = 1800
    memory_limit: str = "2GB"
    cpu_limit: float = 2.0
    max_concurrent: int = 5
    cost_per_hour: Optional[float] = None
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityGateConfig:
    """Configuration for quality gates."""
    enabled: bool = True
    parallel_execution: bool = True
    timeout: int = 3600
    fail_fast: bool = True
    gates: List[QualityGateType] = field(default_factory=lambda: [
        QualityGateType.CODE_QUALITY,
        QualityGateType.UNIT_TESTS,
        QualityGateType.INTEGRATION_TESTS,
        QualityGateType.SECURITY_SCAN
    ])
    thresholds: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SnapshotConfig:
    """Configuration for snapshot management."""
    enabled: bool = True
    retention_days: int = 30
    cleanup_enabled: bool = True
    delta_snapshots: bool = True
    compression: bool = True
    max_snapshots_per_project: int = 100
    auto_cleanup_failed: bool = True
    storage_optimization: bool = True


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and metrics."""
    enabled: bool = True
    metrics_retention_days: int = 90
    health_check_interval: int = 300  # 5 minutes
    cost_alerts_enabled: bool = True
    cost_threshold_monthly: float = 1000.0
    performance_monitoring: bool = True
    log_level: str = "INFO"


@dataclass
class CIIntegrationConfig:
    """Configuration for CI/CD integration."""
    enabled: bool = True
    auto_pr_environments: bool = True
    auto_cleanup_merged_prs: bool = True
    pr_environment_timeout: int = 86400  # 24 hours
    pipeline_timeout: int = 7200  # 2 hours
    artifact_retention_days: int = 7
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class GrainchainIntegrationConfig:
    """Main configuration for Grainchain integration."""
    # Core settings
    default_provider: SandboxProvider = SandboxProvider.E2B
    fallback_providers: List[SandboxProvider] = field(default_factory=lambda: [
        SandboxProvider.LOCAL, SandboxProvider.E2B
    ])
    
    # Provider configurations
    providers: Dict[SandboxProvider, ProviderConfig] = field(default_factory=dict)
    
    # Feature configurations
    quality_gates: QualityGateConfig = field(default_factory=QualityGateConfig)
    snapshots: SnapshotConfig = field(default_factory=SnapshotConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    ci_integration: CIIntegrationConfig = field(default_factory=CIIntegrationConfig)
    
    # Advanced settings
    auto_scaling: bool = False
    cost_optimization: bool = True
    performance_benchmarking: bool = True
    debug_mode: bool = False
    
    # Integration settings
    contexten_integration: bool = True
    event_bus_enabled: bool = True
    webhook_enabled: bool = False
    webhook_secret: Optional[str] = None
    
    # Custom settings
    custom_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default provider configurations."""
        if not self.providers:
            self.providers = self._create_default_provider_configs()

    def _create_default_provider_configs(self) -> Dict[SandboxProvider, ProviderConfig]:
        """Create default configurations for all providers."""
        return {
            SandboxProvider.LOCAL: ProviderConfig(
                enabled=True,
                timeout=300,
                memory_limit="4GB",
                cpu_limit=4.0,
                cost_per_hour=0.0
            ),
            SandboxProvider.E2B: ProviderConfig(
                enabled=True,
                api_key=os.getenv("E2B_API_KEY"),
                template="python-data-science",
                timeout=1800,
                memory_limit="2GB",
                cpu_limit=2.0,
                cost_per_hour=0.50
            ),
            SandboxProvider.DAYTONA: ProviderConfig(
                enabled=True,
                api_key=os.getenv("DAYTONA_API_KEY"),
                workspace_template="python-dev",
                timeout=3600,
                memory_limit="4GB",
                cpu_limit=4.0,
                cost_per_hour=1.20
            ),
            SandboxProvider.MORPH: ProviderConfig(
                enabled=True,
                api_key=os.getenv("MORPH_API_KEY"),
                image_id="morphvm-minimal",
                timeout=1800,
                memory_limit="2GB",
                cpu_limit=2.0,
                cost_per_hour=0.80
            ),
            SandboxProvider.DOCKER: ProviderConfig(
                enabled=False,  # Not implemented yet
                timeout=1800,
                memory_limit="2GB",
                cpu_limit=2.0,
                cost_per_hour=0.10
            )
        }

    def get_provider_config(self, provider: SandboxProvider) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider)

    def is_provider_enabled(self, provider: SandboxProvider) -> bool:
        """Check if a provider is enabled and configured."""
        config = self.get_provider_config(provider)
        if not config or not config.enabled:
            return False
        
        # Check if required credentials are available
        if provider in [SandboxProvider.E2B, SandboxProvider.DAYTONA, SandboxProvider.MORPH]:
            return config.api_key is not None
        
        return True

    def get_enabled_providers(self) -> List[SandboxProvider]:
        """Get list of enabled and configured providers."""
        return [
            provider for provider in SandboxProvider
            if self.is_provider_enabled(provider)
        ]

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check if at least one provider is enabled
        enabled_providers = self.get_enabled_providers()
        if not enabled_providers:
            issues.append("No providers are enabled and configured")
        
        # Check if default provider is enabled
        if not self.is_provider_enabled(self.default_provider):
            issues.append(f"Default provider {self.default_provider.value} is not enabled or configured")
        
        # Validate provider configurations
        for provider, config in self.providers.items():
            if config.enabled:
                if provider in [SandboxProvider.E2B, SandboxProvider.DAYTONA, SandboxProvider.MORPH]:
                    if not config.api_key:
                        issues.append(f"Provider {provider.value} is enabled but missing API key")
        
        # Validate quality gate configuration
        if self.quality_gates.enabled and not self.quality_gates.gates:
            issues.append("Quality gates are enabled but no gates are configured")
        
        # Validate monitoring configuration
        if self.monitoring.cost_threshold_monthly <= 0:
            issues.append("Cost threshold must be positive")
        
        return issues


def load_config_from_file(config_path: Path) -> GrainchainIntegrationConfig:
    """Load configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return _dict_to_config(config_data)


def load_config_from_env() -> GrainchainIntegrationConfig:
    """Load configuration from environment variables."""
    config = GrainchainIntegrationConfig()
    
    # Override with environment variables
    if default_provider := os.getenv("GRAINCHAIN_DEFAULT_PROVIDER"):
        try:
            config.default_provider = SandboxProvider(default_provider)
        except ValueError:
            pass
    
    # Load provider API keys
    for provider in SandboxProvider:
        env_key = f"{provider.value.upper()}_API_KEY"
        if api_key := os.getenv(env_key):
            if provider not in config.providers:
                config.providers[provider] = ProviderConfig()
            config.providers[provider].api_key = api_key
    
    # Load other settings
    if debug_mode := os.getenv("GRAINCHAIN_DEBUG_MODE"):
        config.debug_mode = debug_mode.lower() in ("true", "1", "yes")
    
    if cost_threshold := os.getenv("GRAINCHAIN_COST_THRESHOLD"):
        try:
            config.monitoring.cost_threshold_monthly = float(cost_threshold)
        except ValueError:
            pass
    
    return config


def get_grainchain_config() -> GrainchainIntegrationConfig:
    """Get Grainchain configuration from file or environment."""
    # Try to load from file first
    config_path = Path(os.getenv("GRAINCHAIN_CONFIG_PATH", "grainchain_config.yaml"))
    
    if config_path.exists():
        try:
            return load_config_from_file(config_path)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
    
    # Fall back to environment variables
    return load_config_from_env()


def create_config_template(output_path: Path) -> None:
    """Create a template configuration file."""
    template_config = {
        "default_provider": "e2b",
        "fallback_providers": ["local", "e2b"],
        
        "providers": {
            "local": {
                "enabled": True,
                "timeout": 300,
                "memory_limit": "4GB",
                "cpu_limit": 4.0,
                "cost_per_hour": 0.0
            },
            "e2b": {
                "enabled": True,
                "api_key": "${E2B_API_KEY}",
                "template": "python-data-science",
                "timeout": 1800,
                "memory_limit": "2GB",
                "cpu_limit": 2.0,
                "cost_per_hour": 0.50
            },
            "daytona": {
                "enabled": True,
                "api_key": "${DAYTONA_API_KEY}",
                "workspace_template": "python-dev",
                "timeout": 3600,
                "memory_limit": "4GB",
                "cpu_limit": 4.0,
                "cost_per_hour": 1.20
            },
            "morph": {
                "enabled": True,
                "api_key": "${MORPH_API_KEY}",
                "image_id": "morphvm-minimal",
                "timeout": 1800,
                "memory_limit": "2GB",
                "cpu_limit": 2.0,
                "cost_per_hour": 0.80
            }
        },
        
        "quality_gates": {
            "enabled": True,
            "parallel_execution": True,
            "timeout": 3600,
            "fail_fast": True,
            "gates": ["code_quality", "unit_tests", "integration_tests", "security_scan"],
            "thresholds": {
                "code_coverage": 80,
                "security_issues": 0,
                "performance_regression": 10
            }
        },
        
        "snapshots": {
            "enabled": True,
            "retention_days": 30,
            "cleanup_enabled": True,
            "delta_snapshots": True,
            "compression": True,
            "max_snapshots_per_project": 100
        },
        
        "monitoring": {
            "enabled": True,
            "metrics_retention_days": 90,
            "health_check_interval": 300,
            "cost_alerts_enabled": True,
            "cost_threshold_monthly": 1000.0,
            "performance_monitoring": True,
            "log_level": "INFO"
        },
        
        "ci_integration": {
            "enabled": True,
            "auto_pr_environments": True,
            "auto_cleanup_merged_prs": True,
            "pr_environment_timeout": 86400,
            "pipeline_timeout": 7200,
            "artifact_retention_days": 7,
            "notification_channels": ["#dev-alerts"]
        },
        
        "advanced": {
            "auto_scaling": False,
            "cost_optimization": True,
            "performance_benchmarking": True,
            "debug_mode": False
        },
        
        "integration": {
            "contexten_integration": True,
            "event_bus_enabled": True,
            "webhook_enabled": False,
            "webhook_secret": "${GRAINCHAIN_WEBHOOK_SECRET}"
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(template_config, f, default_flow_style=False, indent=2)
    
    print(f"Configuration template created at: {output_path}")


def _dict_to_config(config_data: Dict[str, Any]) -> GrainchainIntegrationConfig:
    """Convert dictionary to configuration object."""
    # This is a simplified implementation
    # In a real implementation, you'd want more sophisticated parsing
    config = GrainchainIntegrationConfig()
    
    # Parse basic settings
    if "default_provider" in config_data:
        try:
            config.default_provider = SandboxProvider(config_data["default_provider"])
        except ValueError:
            pass
    
    # Parse providers
    if "providers" in config_data:
        for provider_name, provider_data in config_data["providers"].items():
            try:
                provider = SandboxProvider(provider_name)
                config.providers[provider] = ProviderConfig(**provider_data)
            except (ValueError, TypeError):
                continue
    
    # Parse other sections
    if "quality_gates" in config_data:
        config.quality_gates = QualityGateConfig(**config_data["quality_gates"])
    
    if "snapshots" in config_data:
        config.snapshots = SnapshotConfig(**config_data["snapshots"])
    
    if "monitoring" in config_data:
        config.monitoring = MonitoringConfig(**config_data["monitoring"])
    
    if "ci_integration" in config_data:
        config.ci_integration = CIIntegrationConfig(**config_data["ci_integration"])
    
    return config

