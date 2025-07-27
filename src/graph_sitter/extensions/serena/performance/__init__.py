"""
Performance Optimization Module for Serena Analysis

This module provides performance enhancements for Serena analysis operations,
including intelligent caching, parallel processing, and memory optimization.
"""

from .caching import (
    AnalysisCache,
    CacheEntry,
    get_cache,
    configure_cache,
    cached_analysis,
    BatchCache,
    batch_cached_analysis
)

from .parallel import (
    ParallelAnalyzer,
    parallel_analysis,
    batch_analyze_files,
    AnalysisTask,
    AnalysisResult
)

from .memory import (
    MemoryOptimizer,
    get_memory_optimizer,
    get_memory_stats,
    memory_efficient_analysis,
    optimize_memory_usage
)

__all__ = [
    # Caching
    'AnalysisCache',
    'CacheEntry', 
    'get_cache',
    'configure_cache',
    'cached_analysis',
    'BatchCache',
    'batch_cached_analysis',
    
    # Parallel processing
    'ParallelAnalyzer',
    'parallel_analysis',
    'batch_analyze_files',
    'AnalysisTask',
    'AnalysisResult',
    
    # Memory optimization
    'MemoryOptimizer',
    'get_memory_optimizer',
    'get_memory_stats',
    'memory_efficient_analysis',
    'optimize_memory_usage'
]
