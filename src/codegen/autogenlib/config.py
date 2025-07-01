"""Configuration management for autogenlib module."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AutogenConfig(BaseSettings):
    """Configuration for Codegen SDK integration."""
    
    # Codegen SDK Configuration
    org_id: str = Field(..., description="Codegen organization ID")
    token: str = Field(..., description="Codegen API token")
    api_base_url: Optional[str] = Field("https://api.codegen.com", description="Codegen API base URL")
    
    # Performance Configuration
    cache_enabled: bool = Field(True, description="Enable caching for performance optimization")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds")
    max_response_time: float = Field(2.0, description="Maximum response time target in seconds")
    
    # Retry Configuration
    max_retries: int = Field(3, description="Maximum number of retry attempts")
    retry_delay: float = Field(1.0, description="Initial retry delay in seconds")
    retry_backoff: float = Field(2.0, description="Retry backoff multiplier")
    
    # Context Enhancement Configuration
    enable_context_enhancement: bool = Field(True, description="Enable automatic context enhancement")
    max_context_length: int = Field(8000, description="Maximum context length in characters")
    include_file_summaries: bool = Field(True, description="Include file summaries in context")
    include_class_summaries: bool = Field(True, description="Include class summaries in context")
    include_function_summaries: bool = Field(True, description="Include function summaries in context")
    
    # Async Processing Configuration
    enable_async_processing: bool = Field(True, description="Enable asynchronous task processing")
    max_concurrent_tasks: int = Field(5, description="Maximum concurrent tasks")
    task_timeout: int = Field(300, description="Default task timeout in seconds")
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_requests: bool = Field(True, description="Log API requests")
    log_responses: bool = Field(False, description="Log API responses (may contain sensitive data)")
    
    # Usage Tracking Configuration
    enable_usage_tracking: bool = Field(True, description="Enable usage tracking and cost management")
    usage_alert_threshold: float = Field(100.0, description="Usage alert threshold in USD")
    
    class Config:
        env_prefix = "AUTOGENLIB_"
        env_file = ".env"
        case_sensitive = False


class CacheConfig(BaseModel):
    """Configuration for caching layer."""
    
    backend: str = Field("memory", description="Cache backend (memory, file, redis)")
    redis_url: Optional[str] = Field(None, description="Redis URL for redis backend")
    file_cache_dir: str = Field("/tmp/autogenlib_cache", description="Directory for file cache")
    max_memory_size: int = Field(100 * 1024 * 1024, description="Maximum memory cache size in bytes")
    cleanup_interval: int = Field(3600, description="Cache cleanup interval in seconds")


def get_config() -> AutogenConfig:
    """Get the current autogenlib configuration."""
    return AutogenConfig()


def validate_config(config: AutogenConfig) -> bool:
    """Validate the configuration."""
    if not config.org_id:
        raise ValueError("org_id is required")
    
    if not config.token:
        raise ValueError("token is required")
    
    if config.max_response_time <= 0:
        raise ValueError("max_response_time must be positive")
    
    if config.max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    
    if config.max_concurrent_tasks <= 0:
        raise ValueError("max_concurrent_tasks must be positive")
    
    return True

