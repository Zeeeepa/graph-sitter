"""
Environment-specific configuration management for Codegen SDK integration.

This module handles configuration variations across different environments
(development, staging, production) with appropriate defaults and validation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from ..config import Environment


logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """
    Environment-specific configuration for Codegen SDK integration.
    
    Manages configuration variations across different deployment environments
    with appropriate defaults, validation, and environment-specific overrides.
    """
    
    environment: Environment
    
    # API Configuration
    api_base_url: Optional[str] = None
    api_timeout: float = 30.0
    api_retries: int = 3
    
    # Performance Configuration
    max_concurrent_requests: int = 10
    connection_pool_size: int = 20
    request_timeout: float = 30.0
    
    # Rate Limiting (environment-specific)
    requests_per_second: float = 5.0
    burst_limit: int = 10
    
    # Context Configuration
    max_context_tokens: int = 8000
    context_cache_ttl: int = 3600
    enable_context_caching: bool = True
    
    # Monitoring and Logging
    log_level: str = "INFO"
    enable_metrics: bool = True
    enable_cost_tracking: bool = True
    enable_performance_monitoring: bool = True
    
    # Security Configuration
    enable_request_signing: bool = False
    enable_response_validation: bool = True
    
    # Feature Flags (environment-specific)
    feature_overrides: Dict[str, bool] = field(default_factory=dict)
    
    # Custom Environment Variables
    custom_env_vars: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def for_environment(cls, environment: Environment) -> "EnvironmentConfig":
        """
        Create environment-specific configuration with appropriate defaults.
        
        Args:
            environment: Target environment
            
        Returns:
            EnvironmentConfig with environment-specific defaults
        """
        if environment == Environment.DEVELOPMENT:
            return cls._development_config()
        elif environment == Environment.STAGING:
            return cls._staging_config()
        elif environment == Environment.PRODUCTION:
            return cls._production_config()
        elif environment == Environment.TESTING:
            return cls._testing_config()
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    @classmethod
    def _development_config(cls) -> "EnvironmentConfig":
        """Development environment configuration."""
        return cls(
            environment=Environment.DEVELOPMENT,
            api_timeout=60.0,  # Longer timeout for debugging
            max_concurrent_requests=5,  # Lower concurrency for development
            requests_per_second=2.0,  # Conservative rate limiting
            burst_limit=5,
            log_level="DEBUG",
            enable_metrics=True,
            enable_cost_tracking=True,
            enable_performance_monitoring=True,
            enable_request_signing=False,
            feature_overrides={
                "enhanced_context": True,
                "batch_processing": False,  # Disabled for simpler debugging
                "intelligent_caching": True,
                "cost_optimization": False,  # Disabled for development
                "quality_scoring": True
            }
        )
    
    @classmethod
    def _staging_config(cls) -> "EnvironmentConfig":
        """Staging environment configuration."""
        return cls(
            environment=Environment.STAGING,
            api_timeout=45.0,
            max_concurrent_requests=8,
            requests_per_second=4.0,
            burst_limit=8,
            log_level="INFO",
            enable_metrics=True,
            enable_cost_tracking=True,
            enable_performance_monitoring=True,
            enable_request_signing=True,
            feature_overrides={
                "enhanced_context": True,
                "batch_processing": True,
                "intelligent_caching": True,
                "cost_optimization": True,
                "quality_scoring": True
            }
        )
    
    @classmethod
    def _production_config(cls) -> "EnvironmentConfig":
        """Production environment configuration."""
        return cls(
            environment=Environment.PRODUCTION,
            api_timeout=30.0,
            max_concurrent_requests=15,  # Higher concurrency for production
            connection_pool_size=30,
            requests_per_second=8.0,  # Higher rate limit for production
            burst_limit=15,
            log_level="WARNING",  # Less verbose logging
            enable_metrics=True,
            enable_cost_tracking=True,
            enable_performance_monitoring=True,
            enable_request_signing=True,
            enable_response_validation=True,
            feature_overrides={
                "enhanced_context": True,
                "batch_processing": True,
                "intelligent_caching": True,
                "cost_optimization": True,
                "quality_scoring": True
            }
        )
    
    @classmethod
    def _testing_config(cls) -> "EnvironmentConfig":
        """Testing environment configuration."""
        return cls(
            environment=Environment.TESTING,
            api_timeout=10.0,  # Shorter timeout for tests
            max_concurrent_requests=3,  # Lower concurrency for tests
            requests_per_second=10.0,  # Higher rate for fast tests
            burst_limit=20,
            log_level="ERROR",  # Minimal logging for tests
            enable_metrics=False,  # Disabled for tests
            enable_cost_tracking=False,
            enable_performance_monitoring=False,
            enable_request_signing=False,
            context_cache_ttl=60,  # Shorter cache for tests
            feature_overrides={
                "enhanced_context": False,  # Simplified for tests
                "batch_processing": False,
                "intelligent_caching": False,
                "cost_optimization": False,
                "quality_scoring": False
            }
        )
    
    @classmethod
    def from_file(cls, config_path: Path, environment: Environment) -> "EnvironmentConfig":
        """
        Load configuration from JSON file with environment-specific overrides.
        
        Args:
            config_path: Path to configuration file
            environment: Target environment
            
        Returns:
            EnvironmentConfig loaded from file
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Get base configuration for environment
            base_config = cls.for_environment(environment)
            
            # Apply overrides from file
            env_section = config_data.get(environment.value, {})
            common_section = config_data.get("common", {})
            
            # Merge configurations: common -> environment-specific -> base
            merged_config = {**common_section, **env_section}
            
            # Update base configuration with merged values
            for key, value in merged_config.items():
                if hasattr(base_config, key):
                    setattr(base_config, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            return base_config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
    
    def apply_environment_overrides(self) -> None:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables follow the pattern: CONTEXTEN_CODEGEN_{SETTING_NAME}
        """
        env_prefix = "CONTEXTEN_CODEGEN_"
        
        # Mapping of environment variable suffixes to config attributes
        env_mappings = {
            "API_TIMEOUT": ("api_timeout", float),
            "MAX_CONCURRENT": ("max_concurrent_requests", int),
            "REQUESTS_PER_SECOND": ("requests_per_second", float),
            "BURST_LIMIT": ("burst_limit", int),
            "MAX_CONTEXT_TOKENS": ("max_context_tokens", int),
            "CACHE_TTL": ("context_cache_ttl", int),
            "LOG_LEVEL": ("log_level", str),
            "ENABLE_METRICS": ("enable_metrics", lambda x: x.lower() == "true"),
            "ENABLE_COST_TRACKING": ("enable_cost_tracking", lambda x: x.lower() == "true"),
            "ENABLE_CACHING": ("enable_context_caching", lambda x: x.lower() == "true"),
        }
        
        for env_suffix, (attr_name, converter) in env_mappings.items():
            env_var = f"{env_prefix}{env_suffix}"
            env_value = os.environ.get(env_var)
            
            if env_value is not None:
                try:
                    converted_value = converter(env_value)
                    setattr(self, attr_name, converted_value)
                    logger.info(f"Applied environment override: {attr_name} = {converted_value}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid value for {env_var}: {env_value} ({e})")
        
        # Handle feature flag overrides
        for feature in ["enhanced_context", "batch_processing", "intelligent_caching", 
                       "cost_optimization", "quality_scoring"]:
            env_var = f"{env_prefix}FEATURE_{feature.upper()}"
            env_value = os.environ.get(env_var)
            
            if env_value is not None:
                self.feature_overrides[feature] = env_value.lower() == "true"
                logger.info(f"Applied feature override: {feature} = {self.feature_overrides[feature]}")
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If configuration values are invalid
        """
        if self.api_timeout <= 0:
            raise ValueError("api_timeout must be positive")
        
        if self.max_concurrent_requests <= 0:
            raise ValueError("max_concurrent_requests must be positive")
        
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
        
        if self.context_cache_ttl < 0:
            raise ValueError("context_cache_ttl must be non-negative")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"log_level must be one of: {valid_log_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "api_base_url": self.api_base_url,
            "api_timeout": self.api_timeout,
            "api_retries": self.api_retries,
            "max_concurrent_requests": self.max_concurrent_requests,
            "connection_pool_size": self.connection_pool_size,
            "request_timeout": self.request_timeout,
            "requests_per_second": self.requests_per_second,
            "burst_limit": self.burst_limit,
            "max_context_tokens": self.max_context_tokens,
            "context_cache_ttl": self.context_cache_ttl,
            "enable_context_caching": self.enable_context_caching,
            "log_level": self.log_level,
            "enable_metrics": self.enable_metrics,
            "enable_cost_tracking": self.enable_cost_tracking,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "enable_request_signing": self.enable_request_signing,
            "enable_response_validation": self.enable_response_validation,
            "feature_overrides": self.feature_overrides,
            "custom_env_vars": self.custom_env_vars
        }
    
    def get_feature_flag(self, feature_name: str, default: bool = False) -> bool:
        """
        Get feature flag value with fallback to default.
        
        Args:
            feature_name: Name of the feature flag
            default: Default value if feature not found
            
        Returns:
            Feature flag value
        """
        return self.feature_overrides.get(feature_name, default)
    
    def set_feature_flag(self, feature_name: str, enabled: bool) -> None:
        """
        Set feature flag value.
        
        Args:
            feature_name: Name of the feature flag
            enabled: Whether the feature is enabled
        """
        self.feature_overrides[feature_name] = enabled
        logger.info(f"Set feature flag: {feature_name} = {enabled}")
    
    def save_to_file(self, config_path: Path) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path where to save the configuration
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            self.environment.value: self.to_dict()
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Saved configuration to: {config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

