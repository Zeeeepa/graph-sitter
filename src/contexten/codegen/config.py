"""
Configuration classes for Codegen SDK integration.

This module provides configuration management for the Codegen SDK integration,
including authentication, performance settings, and feature flags.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class Environment(Enum):
    """Environment types for configuration management."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class CodegenConfig:
    """
    Main configuration class for Codegen SDK integration.
    
    This class manages all configuration aspects including authentication,
    performance settings, and feature flags.
    """
    
    # Authentication Configuration
    org_id: str
    token: str
    base_url: Optional[str] = None
    
    # Performance Configuration
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    connection_pool_size: int = 20
    
    # Rate Limiting Configuration
    requests_per_second: float = 5.0
    burst_limit: int = 10
    
    # Context Enhancement Configuration
    max_context_tokens: int = 8000
    context_cache_ttl: int = 3600  # seconds
    enable_context_caching: bool = True
    
    # Monitoring Configuration
    enable_metrics: bool = True
    enable_cost_tracking: bool = True
    metrics_export_interval: int = 60  # seconds
    
    # Feature Flags
    feature_flags: Dict[str, bool] = field(default_factory=lambda: {
        "enhanced_context": True,
        "batch_processing": True,
        "intelligent_caching": True,
        "cost_optimization": True,
        "quality_scoring": True
    })
    
    # Environment Configuration
    environment: Environment = Environment.DEVELOPMENT
    debug_mode: bool = False
    
    @classmethod
    def from_environment(cls, environment: Optional[Environment] = None) -> "CodegenConfig":
        """
        Create configuration from environment variables.
        
        Args:
            environment: Target environment (auto-detected if not provided)
            
        Returns:
            CodegenConfig instance with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Detect environment if not provided
        if environment is None:
            env_name = os.environ.get("CONTEXTEN_ENVIRONMENT", "development").lower()
            environment = Environment(env_name)
        
        # Required environment variables
        org_id = os.environ.get("CODEGEN_ORG_ID")
        token = os.environ.get("CODEGEN_API_TOKEN")
        
        if not org_id:
            raise ValueError("CODEGEN_ORG_ID environment variable is required")
        if not token:
            raise ValueError("CODEGEN_API_TOKEN environment variable is required")
        
        # Optional environment variables with defaults
        base_url = os.environ.get("CODEGEN_BASE_URL")
        
        # Performance settings
        max_concurrent = int(os.environ.get("CODEGEN_MAX_CONCURRENT", "10"))
        timeout = float(os.environ.get("CODEGEN_TIMEOUT", "30.0"))
        max_retries = int(os.environ.get("CODEGEN_MAX_RETRIES", "3"))
        
        # Rate limiting
        rps = float(os.environ.get("CODEGEN_REQUESTS_PER_SECOND", "5.0"))
        burst = int(os.environ.get("CODEGEN_BURST_LIMIT", "10"))
        
        # Context settings
        max_tokens = int(os.environ.get("CODEGEN_MAX_CONTEXT_TOKENS", "8000"))
        cache_ttl = int(os.environ.get("CODEGEN_CACHE_TTL", "3600"))
        enable_cache = os.environ.get("CODEGEN_ENABLE_CACHE", "true").lower() == "true"
        
        # Monitoring
        enable_metrics = os.environ.get("CODEGEN_ENABLE_METRICS", "true").lower() == "true"
        enable_cost = os.environ.get("CODEGEN_ENABLE_COST_TRACKING", "true").lower() == "true"
        
        # Debug mode
        debug = os.environ.get("CODEGEN_DEBUG", "false").lower() == "true"
        
        # Feature flags from environment
        feature_flags = {}
        for flag in ["enhanced_context", "batch_processing", "intelligent_caching", 
                    "cost_optimization", "quality_scoring"]:
            env_var = f"CODEGEN_FEATURE_{flag.upper()}"
            feature_flags[flag] = os.environ.get(env_var, "true").lower() == "true"
        
        return cls(
            org_id=org_id,
            token=token,
            base_url=base_url,
            max_concurrent_requests=max_concurrent,
            request_timeout=timeout,
            max_retries=max_retries,
            requests_per_second=rps,
            burst_limit=burst,
            max_context_tokens=max_tokens,
            context_cache_ttl=cache_ttl,
            enable_context_caching=enable_cache,
            enable_metrics=enable_metrics,
            enable_cost_tracking=enable_cost,
            feature_flags=feature_flags,
            environment=environment,
            debug_mode=debug
        )
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If configuration values are invalid
        """
        if not self.org_id:
            raise ValueError("org_id is required")
        if not self.token:
            raise ValueError("token is required")
        if self.max_concurrent_requests <= 0:
            raise ValueError("max_concurrent_requests must be positive")
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "org_id": self.org_id,
            "token": "***" if self.token else None,  # Mask token in output
            "base_url": self.base_url,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "retry_backoff_factor": self.retry_backoff_factor,
            "connection_pool_size": self.connection_pool_size,
            "requests_per_second": self.requests_per_second,
            "burst_limit": self.burst_limit,
            "max_context_tokens": self.max_context_tokens,
            "context_cache_ttl": self.context_cache_ttl,
            "enable_context_caching": self.enable_context_caching,
            "enable_metrics": self.enable_metrics,
            "enable_cost_tracking": self.enable_cost_tracking,
            "metrics_export_interval": self.metrics_export_interval,
            "feature_flags": self.feature_flags,
            "environment": self.environment.value,
            "debug_mode": self.debug_mode
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.feature_flags.get(feature_name, False)
    
    def enable_feature(self, feature_name: str) -> None:
        """Enable a feature flag."""
        self.feature_flags[feature_name] = True
    
    def disable_feature(self, feature_name: str) -> None:
        """Disable a feature flag."""
        self.feature_flags[feature_name] = False

