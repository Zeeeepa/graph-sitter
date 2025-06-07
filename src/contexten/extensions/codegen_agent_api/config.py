"""
Configuration management for Codegen Agent API extension.

Handles both local configuration and integration with pip-installed codegen packages.
"""

import os
import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CodegenAgentAPIConfig:
    """Configuration for Codegen Agent API extension."""
    
    # Core API settings
    org_id: str
    token: str
    base_url: str = "https://api.codegen.com"
    
    # Connection settings
    timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    rate_limit_buffer: float = 0.1
    connection_pool_size: int = 10
    
    # Extension settings
    enable_logging: bool = True
    validate_on_init: bool = False
    enable_overlay: bool = True
    fallback_to_local: bool = True
    
    # Overlay settings
    pip_package_name: str = "codegen"
    overlay_priority: str = "pip_first"  # "pip_first", "local_first", "pip_only", "local_only"
    
    # Webhook settings
    webhook_secret: Optional[str] = None
    webhook_events: list = None
    
    # Monitoring settings
    enable_metrics: bool = True
    metrics_interval: int = 60
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.webhook_events is None:
            self.webhook_events = ["task.completed", "task.failed", "task.cancelled"]
        
        # Validate overlay priority
        valid_priorities = ["pip_first", "local_first", "pip_only", "local_only"]
        if self.overlay_priority not in valid_priorities:
            raise ValueError(f"overlay_priority must be one of {valid_priorities}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodegenAgentAPIConfig':
        """Create config from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_env(cls, prefix: str = "CODEGEN_") -> 'CodegenAgentAPIConfig':
        """Create config from environment variables."""
        env_mapping = {
            "org_id": f"{prefix}ORG_ID",
            "token": f"{prefix}TOKEN",
            "base_url": f"{prefix}BASE_URL",
            "timeout": f"{prefix}TIMEOUT",
            "max_retries": f"{prefix}MAX_RETRIES",
            "retry_backoff_factor": f"{prefix}RETRY_BACKOFF_FACTOR",
            "rate_limit_buffer": f"{prefix}RATE_LIMIT_BUFFER",
            "connection_pool_size": f"{prefix}CONNECTION_POOL_SIZE",
            "enable_logging": f"{prefix}ENABLE_LOGGING",
            "validate_on_init": f"{prefix}VALIDATE_ON_INIT",
            "enable_overlay": f"{prefix}ENABLE_OVERLAY",
            "fallback_to_local": f"{prefix}FALLBACK_TO_LOCAL",
            "pip_package_name": f"{prefix}PIP_PACKAGE_NAME",
            "overlay_priority": f"{prefix}OVERLAY_PRIORITY",
            "webhook_secret": f"{prefix}WEBHOOK_SECRET",
            "enable_metrics": f"{prefix}ENABLE_METRICS",
            "metrics_interval": f"{prefix}METRICS_INTERVAL",
        }
        
        config_data = {}
        
        # Required fields
        for field in ["org_id", "token"]:
            env_var = env_mapping[field]
            value = os.getenv(env_var)
            if not value:
                raise ValueError(f"Required environment variable {env_var} not set")
            config_data[field] = value
        
        # Optional fields with type conversion
        for field, env_var in env_mapping.items():
            if field in config_data:  # Skip already processed required fields
                continue
                
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion based on field
                if field in ["timeout", "max_retries", "connection_pool_size", "metrics_interval"]:
                    config_data[field] = int(value)
                elif field in ["retry_backoff_factor", "rate_limit_buffer"]:
                    config_data[field] = float(value)
                elif field in ["enable_logging", "validate_on_init", "enable_overlay", "fallback_to_local", "enable_metrics"]:
                    config_data[field] = value.lower() in ("true", "1", "yes", "on")
                elif field == "webhook_events":
                    config_data[field] = value.split(",") if value else []
                else:
                    config_data[field] = value
        
        return cls(**config_data)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'CodegenAgentAPIConfig':
        """Create config from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    def to_file(self, file_path: Union[str, Path]) -> None:
        """Save config to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.org_id:
            raise ValueError("org_id is required")
        if not self.token:
            raise ValueError("token is required")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


def get_codegen_config(
    config_file: Optional[Union[str, Path]] = None,
    env_prefix: str = "CODEGEN_",
    **kwargs
) -> CodegenAgentAPIConfig:
    """
    Get Codegen configuration from various sources.
    
    Priority order:
    1. Explicit kwargs
    2. Config file (if provided)
    3. Environment variables
    4. Default values
    
    Args:
        config_file: Optional path to JSON config file
        env_prefix: Prefix for environment variables
        **kwargs: Explicit configuration overrides
        
    Returns:
        CodegenAgentAPIConfig instance
    """
    config_data = {}
    
    # Start with environment variables
    try:
        env_config = CodegenAgentAPIConfig.from_env(env_prefix)
        config_data.update(env_config.to_dict())
    except ValueError:
        # Environment config not complete, use defaults
        pass
    
    # Override with config file if provided
    if config_file:
        try:
            file_config = CodegenAgentAPIConfig.from_file(config_file)
            config_data.update(file_config.to_dict())
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load config file {config_file}: {e}")
    
    # Override with explicit kwargs
    config_data.update(kwargs)
    
    # Create and validate config
    config = CodegenAgentAPIConfig.from_dict(config_data)
    config.validate()
    
    return config


def create_config_template(file_path: Union[str, Path]) -> None:
    """Create a template configuration file."""
    template_config = CodegenAgentAPIConfig(
        org_id="your_org_id_here",
        token="your_token_here",
        base_url="https://api.codegen.com",
        timeout=30,
        max_retries=3,
        enable_overlay=True,
        overlay_priority="pip_first",
        enable_logging=True,
        enable_metrics=True
    )
    
    template_config.to_file(file_path)


def detect_pip_codegen() -> Optional[Dict[str, Any]]:
    """
    Detect if codegen is installed via pip and get its information.
    
    Returns:
        Dictionary with pip package info or None if not found
    """
    try:
        import importlib.metadata
        
        # Try to get package metadata
        try:
            metadata = importlib.metadata.metadata("codegen")
            version = importlib.metadata.version("codegen")
            
            return {
                "installed": True,
                "version": version,
                "name": metadata.get("Name"),
                "summary": metadata.get("Summary"),
                "home_page": metadata.get("Home-page"),
                "author": metadata.get("Author"),
                "location": None  # Will be filled by importlib if needed
            }
        except importlib.metadata.PackageNotFoundError:
            pass
        
        # Fallback: try to import the package directly
        try:
            import codegen
            return {
                "installed": True,
                "version": getattr(codegen, "__version__", "unknown"),
                "name": "codegen",
                "summary": "Codegen SDK",
                "location": getattr(codegen, "__file__", None)
            }
        except ImportError:
            pass
            
    except ImportError:
        # importlib.metadata not available (Python < 3.8)
        try:
            import pkg_resources
            try:
                dist = pkg_resources.get_distribution("codegen")
                return {
                    "installed": True,
                    "version": dist.version,
                    "name": dist.project_name,
                    "summary": dist.metadata.get("Summary", ""),
                    "location": dist.location
                }
            except pkg_resources.DistributionNotFound:
                pass
        except ImportError:
            pass
    
    return None


def get_overlay_strategy(config: CodegenAgentAPIConfig) -> str:
    """
    Determine the overlay strategy based on config and pip package availability.
    
    Returns:
        Strategy string: "pip_only", "local_only", "pip_with_local_fallback", "local_with_pip_fallback"
    """
    if not config.enable_overlay:
        return "local_only"
    
    pip_info = detect_pip_codegen()
    pip_available = pip_info is not None
    
    if config.overlay_priority == "pip_only":
        if pip_available:
            return "pip_only"
        elif config.fallback_to_local:
            return "local_only"
        else:
            raise RuntimeError("pip install codegen not found and fallback_to_local is disabled")
    
    elif config.overlay_priority == "local_only":
        return "local_only"
    
    elif config.overlay_priority == "pip_first":
        if pip_available:
            return "pip_with_local_fallback" if config.fallback_to_local else "pip_only"
        else:
            return "local_only"
    
    elif config.overlay_priority == "local_first":
        return "local_with_pip_fallback" if pip_available else "local_only"
    
    else:
        raise ValueError(f"Unknown overlay_priority: {config.overlay_priority}")

