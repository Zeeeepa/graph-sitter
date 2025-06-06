"""
Performance Configuration

Configuration options for optimizing analysis performance.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization during analysis."""
    
    # Memory Management
    max_memory_usage_mb: Optional[int] = 1024
    """Maximum memory usage in MB before triggering cleanup"""
    
    enable_memory_monitoring: bool = True
    """Enable memory usage monitoring during analysis"""
    
    # Processing Limits
    max_file_size_mb: int = 10
    """Maximum file size to process in MB"""
    
    max_files_per_batch: int = 100
    """Maximum number of files to process in a single batch"""
    
    max_analysis_depth: int = 10
    """Maximum depth for recursive analysis operations"""
    
    # Concurrency
    enable_parallel_processing: bool = True
    """Enable parallel processing for analysis operations"""
    
    max_worker_threads: Optional[int] = None
    """Maximum number of worker threads (None = auto-detect)"""
    
    # Caching
    enable_result_caching: bool = True
    """Enable caching of analysis results"""
    
    cache_ttl_seconds: int = 3600
    """Time-to-live for cached results in seconds"""
    
    # Timeouts
    analysis_timeout_seconds: int = 300
    """Timeout for individual analysis operations"""
    
    file_parse_timeout_seconds: int = 30
    """Timeout for parsing individual files"""
    
    # Progress Reporting
    enable_progress_reporting: bool = True
    """Enable progress reporting during long operations"""
    
    progress_update_interval: int = 10
    """Interval for progress updates (number of items)"""
    
    def get_optimized_config(self) -> 'PerformanceConfig':
        """Get a performance-optimized configuration."""
        config = PerformanceConfig()
        config.max_memory_usage_mb = 2048
        config.max_files_per_batch = 200
        config.enable_parallel_processing = True
        config.enable_result_caching = True
        config.cache_ttl_seconds = 7200
        return config
    
    def get_conservative_config(self) -> 'PerformanceConfig':
        """Get a conservative configuration for limited resources."""
        config = PerformanceConfig()
        config.max_memory_usage_mb = 512
        config.max_files_per_batch = 50
        config.enable_parallel_processing = False
        config.max_worker_threads = 1
        config.analysis_timeout_seconds = 600
        return config

