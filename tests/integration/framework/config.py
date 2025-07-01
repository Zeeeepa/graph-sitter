"""
Configuration for Comprehensive Integration Testing Framework

Provides configuration management for all testing components including
performance thresholds, validation rules, and workflow parameters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import os


@dataclass
class PerformanceThresholds:
    """Performance thresholds for regression detection."""
    max_execution_time_regression_percent: float = 20.0
    max_memory_regression_percent: float = 25.0
    max_cpu_regression_percent: float = 30.0
    baseline_update_threshold_percent: float = 5.0
    
    # Absolute thresholds
    max_execution_time_ms: float = 10000.0  # 10 seconds
    max_memory_usage_mb: float = 1000.0     # 1 GB
    max_peak_memory_mb: float = 1500.0      # 1.5 GB


@dataclass
class ValidationConfig:
    """Configuration for cross-component validation."""
    fail_on_critical_issues: bool = True
    fail_on_error_issues: bool = False
    max_allowed_critical_issues: int = 0
    max_allowed_error_issues: int = 5
    max_allowed_warning_issues: int = 20
    
    # Component-specific validation rules
    required_components: List[str] = field(default_factory=lambda: [
        "graph_sitter_core",
        "graph_sitter_python",
        "graph_sitter_typescript",
        "codegen_sdk"
    ])
    
    # Interface validation rules
    check_method_conflicts: bool = True
    check_class_conflicts: bool = True
    check_version_compatibility: bool = True


@dataclass
class WorkflowConfig:
    """Configuration for end-to-end workflow testing."""
    default_timeout_seconds: float = 300.0  # 5 minutes
    step_timeout_seconds: float = 60.0      # 1 minute
    max_retry_attempts: int = 2
    continue_on_failure: bool = True
    
    # Workflow execution settings
    parallel_execution: bool = False
    max_concurrent_workflows: int = 3
    
    # Success criteria
    min_workflow_success_rate: float = 0.7
    min_step_success_rate: float = 0.8


@dataclass
class ReportingConfig:
    """Configuration for test reporting."""
    output_directory: str = "test_reports"
    generate_html: bool = True
    generate_json: bool = True
    generate_markdown: bool = True
    
    # Report content settings
    include_detailed_logs: bool = True
    include_performance_charts: bool = False  # Requires additional dependencies
    include_trend_analysis: bool = False
    
    # File naming
    timestamp_format: str = "%Y%m%d_%H%M%S"
    report_prefix: str = "integration_test"


@dataclass
class IntegrationTestConfig:
    """Main configuration for the integration testing framework."""
    # Test execution settings
    run_integration_tests: bool = True
    run_performance_tests: bool = True
    run_validation_tests: bool = True
    run_workflow_tests: bool = True
    
    # Component configurations
    performance: PerformanceThresholds = field(default_factory=PerformanceThresholds)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    
    # Test data paths
    test_data_directory: str = "tests/data"
    baseline_data_file: str = "performance_baselines.json"
    
    # Environment settings
    log_level: str = "INFO"
    debug_mode: bool = False
    
    # CI/CD integration
    fail_on_regression: bool = True
    fail_on_critical_validation: bool = True
    fail_on_workflow_failure: bool = False
    
    @classmethod
    def from_environment(cls) -> "IntegrationTestConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if os.getenv("INTEGRATION_TEST_DEBUG"):
            config.debug_mode = os.getenv("INTEGRATION_TEST_DEBUG").lower() == "true"
        
        if os.getenv("INTEGRATION_TEST_LOG_LEVEL"):
            config.log_level = os.getenv("INTEGRATION_TEST_LOG_LEVEL")
        
        if os.getenv("INTEGRATION_TEST_OUTPUT_DIR"):
            config.reporting.output_directory = os.getenv("INTEGRATION_TEST_OUTPUT_DIR")
        
        if os.getenv("INTEGRATION_TEST_TIMEOUT"):
            config.workflow.default_timeout_seconds = float(os.getenv("INTEGRATION_TEST_TIMEOUT"))
        
        # Performance thresholds
        if os.getenv("PERF_MAX_EXECUTION_REGRESSION"):
            config.performance.max_execution_time_regression_percent = float(
                os.getenv("PERF_MAX_EXECUTION_REGRESSION")
            )
        
        if os.getenv("PERF_MAX_MEMORY_REGRESSION"):
            config.performance.max_memory_regression_percent = float(
                os.getenv("PERF_MAX_MEMORY_REGRESSION")
            )
        
        # CI/CD settings
        if os.getenv("CI_FAIL_ON_REGRESSION"):
            config.fail_on_regression = os.getenv("CI_FAIL_ON_REGRESSION").lower() == "true"
        
        if os.getenv("CI_FAIL_ON_CRITICAL"):
            config.fail_on_critical_validation = os.getenv("CI_FAIL_ON_CRITICAL").lower() == "true"
        
        return config
    
    @classmethod
    def from_file(cls, config_file: Path) -> "IntegrationTestConfig":
        """Load configuration from a JSON or YAML file."""
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        import json
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() == '.json':
                    data = json.load(f)
                elif config_file.suffix.lower() in ['.yml', '.yaml']:
                    try:
                        import yaml
                        data = yaml.safe_load(f)
                    except ImportError:
                        raise ImportError("PyYAML is required to load YAML configuration files")
                else:
                    raise ValueError(f"Unsupported configuration file format: {config_file.suffix}")
            
            # Create config with loaded data
            config = cls()
            
            # Update configuration with loaded data
            if "performance" in data:
                for key, value in data["performance"].items():
                    if hasattr(config.performance, key):
                        setattr(config.performance, key, value)
            
            if "validation" in data:
                for key, value in data["validation"].items():
                    if hasattr(config.validation, key):
                        setattr(config.validation, key, value)
            
            if "workflow" in data:
                for key, value in data["workflow"].items():
                    if hasattr(config.workflow, key):
                        setattr(config.workflow, key, value)
            
            if "reporting" in data:
                for key, value in data["reporting"].items():
                    if hasattr(config.reporting, key):
                        setattr(config.reporting, key, value)
            
            # Update top-level settings
            for key, value in data.items():
                if key not in ["performance", "validation", "workflow", "reporting"]:
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            return config
            
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_file}: {e}")
    
    def save_to_file(self, config_file: Path):
        """Save configuration to a JSON file."""
        import json
        from dataclasses import asdict
        
        config_data = asdict(self)
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_test_data_path(self) -> Path:
        """Get the test data directory path."""
        return Path(self.test_data_directory)
    
    def get_baseline_file_path(self) -> Path:
        """Get the performance baseline file path."""
        return self.get_test_data_path() / self.baseline_data_file
    
    def get_output_directory(self) -> Path:
        """Get the output directory for reports."""
        return Path(self.reporting.output_directory)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate performance thresholds
        if self.performance.max_execution_time_regression_percent < 0:
            issues.append("Performance execution time regression threshold must be positive")
        
        if self.performance.max_memory_regression_percent < 0:
            issues.append("Performance memory regression threshold must be positive")
        
        # Validate validation config
        if self.validation.max_allowed_critical_issues < 0:
            issues.append("Maximum allowed critical issues must be non-negative")
        
        # Validate workflow config
        if self.workflow.default_timeout_seconds <= 0:
            issues.append("Workflow timeout must be positive")
        
        if self.workflow.min_workflow_success_rate < 0 or self.workflow.min_workflow_success_rate > 1:
            issues.append("Workflow success rate must be between 0 and 1")
        
        # Validate paths
        try:
            test_data_path = self.get_test_data_path()
            if not test_data_path.parent.exists():
                issues.append(f"Test data parent directory does not exist: {test_data_path.parent}")
        except Exception as e:
            issues.append(f"Invalid test data path: {e}")
        
        return issues


# Default configuration instance
DEFAULT_CONFIG = IntegrationTestConfig()


def get_config() -> IntegrationTestConfig:
    """
    Get the current configuration.
    
    This function checks for configuration in the following order:
    1. Environment variables
    2. Configuration file (if INTEGRATION_TEST_CONFIG_FILE is set)
    3. Default configuration
    """
    config_file_env = os.getenv("INTEGRATION_TEST_CONFIG_FILE")
    
    if config_file_env:
        config_file = Path(config_file_env)
        if config_file.exists():
            try:
                return IntegrationTestConfig.from_file(config_file)
            except Exception as e:
                print(f"Warning: Failed to load config from {config_file}: {e}")
                print("Falling back to environment/default configuration")
    
    # Try to load from environment
    return IntegrationTestConfig.from_environment()


def create_sample_config_file(output_path: Path):
    """Create a sample configuration file for reference."""
    config = IntegrationTestConfig()
    config.save_to_file(output_path)
    
    # Add comments to the JSON file
    with open(output_path, 'r') as f:
        content = f.read()
    
    commented_content = f"""{{
  "_comment": "Comprehensive Integration Testing Framework Configuration",
  "_description": "This file configures all aspects of the integration testing framework",
  
{content[1:]}"""
    
    with open(output_path, 'w') as f:
        f.write(commented_content)


if __name__ == "__main__":
    # Create a sample configuration file when run directly
    sample_path = Path("integration_test_config.json")
    create_sample_config_file(sample_path)
    print(f"Sample configuration file created: {sample_path}")
    
    # Validate the default configuration
    config = get_config()
    issues = config.validate_config()
    
    if issues:
        print("Configuration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration validation passed")

