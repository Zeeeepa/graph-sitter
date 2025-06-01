"""
Configuration management for enhanced autogenlib module
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class CacheConfig:
    """Configuration for caching system"""
    memory_cache_size: int = 1000
    redis_url: Optional[str] = None
    disk_cache_dir: str = "/tmp/autogenlib_cache"
    ttl_seconds: int = 3600  # 1 hour default TTL

@dataclass
class AutogenConfig:
    """Configuration for AutogenClient"""
    
    # Required Codegen SDK configuration
    org_id: str
    token: str
    
    # Optional codebase analysis
    codebase_path: Optional[str] = None
    
    # Performance settings
    enable_caching: bool = True
    enable_context_enhancement: bool = True
    max_concurrent_requests: int = 5
    task_timeout_seconds: int = 300  # 5 minutes
    
    # Cache configuration
    cache_config: CacheConfig = field(default_factory=CacheConfig)
    
    # Cost management
    enable_usage_tracking: bool = True
    cost_alert_threshold: float = 100.0  # Alert when monthly cost exceeds this
    
    # Context enhancement settings
    max_context_size: int = 4000  # Maximum context size in characters
    context_relevance_threshold: float = 0.3
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    def __post_init__(self):
        """Validate configuration and set defaults from environment"""
        
        # Override with environment variables if available
        self.org_id = os.getenv('CODEGEN_ORG_ID', self.org_id)
        self.token = os.getenv('CODEGEN_TOKEN', self.token)
        
        if not self.org_id:
            raise ValueError("org_id is required. Set CODEGEN_ORG_ID environment variable or pass explicitly.")
        
        if not self.token:
            raise ValueError("token is required. Set CODEGEN_TOKEN environment variable or pass explicitly.")
        
        # Set codebase path from environment if not provided
        if not self.codebase_path:
            self.codebase_path = os.getenv('AUTOGENLIB_CODEBASE_PATH')
        
        # Override cache settings from environment
        if os.getenv('REDIS_URL'):
            self.cache_config.redis_url = os.getenv('REDIS_URL')
        
        if os.getenv('AUTOGENLIB_CACHE_DIR'):
            self.cache_config.disk_cache_dir = os.getenv('AUTOGENLIB_CACHE_DIR')
        
        # Override performance settings from environment
        if os.getenv('AUTOGENLIB_MAX_CONCURRENT'):
            self.max_concurrent_requests = int(os.getenv('AUTOGENLIB_MAX_CONCURRENT'))
        
        if os.getenv('AUTOGENLIB_TASK_TIMEOUT'):
            self.task_timeout_seconds = int(os.getenv('AUTOGENLIB_TASK_TIMEOUT'))
        
        # Validate settings
        if self.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least 1")
        
        if self.task_timeout_seconds < 10:
            raise ValueError("task_timeout_seconds must be at least 10")
        
        if self.max_context_size < 100:
            raise ValueError("max_context_size must be at least 100")
    
    @classmethod
    def from_env(cls) -> 'AutogenConfig':
        """Create configuration from environment variables"""
        return cls(
            org_id=os.getenv('CODEGEN_ORG_ID', ''),
            token=os.getenv('CODEGEN_TOKEN', ''),
            codebase_path=os.getenv('AUTOGENLIB_CODEBASE_PATH'),
            enable_caching=os.getenv('AUTOGENLIB_ENABLE_CACHING', 'true').lower() == 'true',
            enable_context_enhancement=os.getenv('AUTOGENLIB_ENABLE_CONTEXT', 'true').lower() == 'true',
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'org_id': self.org_id,
            'token': '***' if self.token else None,  # Mask token in output
            'codebase_path': self.codebase_path,
            'enable_caching': self.enable_caching,
            'enable_context_enhancement': self.enable_context_enhancement,
            'max_concurrent_requests': self.max_concurrent_requests,
            'task_timeout_seconds': self.task_timeout_seconds,
            'cache_config': {
                'memory_cache_size': self.cache_config.memory_cache_size,
                'redis_url': '***' if self.cache_config.redis_url else None,
                'disk_cache_dir': self.cache_config.disk_cache_dir,
                'ttl_seconds': self.cache_config.ttl_seconds
            },
            'enable_usage_tracking': self.enable_usage_tracking,
            'cost_alert_threshold': self.cost_alert_threshold,
            'max_context_size': self.max_context_size,
            'context_relevance_threshold': self.context_relevance_threshold,
            'max_retries': self.max_retries,
            'retry_delay_seconds': self.retry_delay_seconds
        }

