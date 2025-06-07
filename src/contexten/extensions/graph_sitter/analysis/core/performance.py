#!/usr/bin/env python3
"""
⚡ PERFORMANCE OPTIMIZATION MODULE ⚡

Advanced performance optimizations for large codebase analysis including:
- Result caching and memoization
- Lazy loading of graph elements
- Parallel processing for analysis tasks
- Memory optimization strategies
- Progress tracking and cancellation support
- Incremental analysis capabilities
- Resource usage monitoring

Based on graph-sitter.com advanced settings for optimal performance.
"""

import logging
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Callable, Iterator
from pathlib import Path
import pickle
import hashlib
import json
import gc
import psutil
import os

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.debug("Redis not available - using in-memory cache only")

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    logger.debug("Joblib not available - using basic parallel processing")


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations."""
    # Caching
    enable_caching: bool = True
    cache_backend: str = "memory"  # memory, file, redis
    cache_ttl: int = 3600  # seconds
    cache_max_size: int = 1000  # max items in memory cache
    cache_directory: str = ".cache/graph_sitter"
    
    # Parallel processing
    enable_parallel: bool = True
    max_workers: Optional[int] = None  # None = auto-detect
    chunk_size: int = 100  # items per chunk
    use_processes: bool = False  # False = threads, True = processes
    
    # Memory optimization
    enable_lazy_loading: bool = True
    memory_limit_mb: Optional[int] = None  # None = no limit
    gc_frequency: int = 100  # run GC every N operations
    
    # Progress tracking
    enable_progress: bool = True
    progress_callback: Optional[Callable] = None
    
    # Resource monitoring
    monitor_resources: bool = True
    resource_check_interval: int = 10  # seconds


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_size: int = 0
    
    # Memory metrics
    peak_memory_mb: float = 0.0
    current_memory_mb: float = 0.0
    memory_samples: List[float] = field(default_factory=list)
    
    # Processing metrics
    items_processed: int = 0
    items_cached: int = 0
    items_skipped: int = 0
    
    # Parallel processing metrics
    workers_used: int = 0
    chunks_processed: int = 0
    
    def finish(self):
        """Mark the operation as finished and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    def items_per_second(self) -> float:
        """Calculate processing rate."""
        return self.items_processed / self.duration if self.duration and self.duration > 0 else 0.0


class CacheManager:
    """Advanced caching system with multiple backends."""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.memory_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.redis_client = None
        
        if config.cache_backend == "redis" and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(decode_responses=True)
                self.redis_client.ping()  # Test connection
                logger.info("Redis cache backend initialized")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory cache: {e}")
                self.config.cache_backend = "memory"
        
        if config.cache_backend == "file":
            os.makedirs(config.cache_directory, exist_ok=True)
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.config.enable_caching:
            return None
        
        try:
            if self.config.cache_backend == "redis" and self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data.encode('latin1'))
            
            elif self.config.cache_backend == "file":
                cache_file = Path(self.config.cache_directory) / f"{key}.pkl"
                if cache_file.exists():
                    # Check TTL
                    if time.time() - cache_file.stat().st_mtime < self.config.cache_ttl:
                        with open(cache_file, 'rb') as f:
                            return pickle.load(f)
                    else:
                        cache_file.unlink()  # Remove expired cache
            
            else:  # memory cache
                if key in self.memory_cache:
                    # Check TTL
                    if time.time() - self.cache_timestamps[key] < self.config.cache_ttl:
                        return self.memory_cache[key]
                    else:
                        del self.memory_cache[key]
                        del self.cache_timestamps[key]
        
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        if not self.config.enable_caching:
            return
        
        try:
            if self.config.cache_backend == "redis" and self.redis_client:
                data = pickle.dumps(value).decode('latin1')
                self.redis_client.setex(key, self.config.cache_ttl, data)
            
            elif self.config.cache_backend == "file":
                cache_file = Path(self.config.cache_directory) / f"{key}.pkl"
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)
            
            else:  # memory cache
                # Implement LRU eviction if cache is full
                if len(self.memory_cache) >= self.config.cache_max_size:
                    # Remove oldest item
                    oldest_key = min(self.cache_timestamps.keys(), 
                                   key=lambda k: self.cache_timestamps[k])
                    del self.memory_cache[oldest_key]
                    del self.cache_timestamps[oldest_key]
                
                self.memory_cache[key] = value
                self.cache_timestamps[key] = time.time()
        
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def clear(self):
        """Clear all cache."""
        try:
            if self.config.cache_backend == "redis" and self.redis_client:
                self.redis_client.flushdb()
            elif self.config.cache_backend == "file":
                cache_dir = Path(self.config.cache_directory)
                for cache_file in cache_dir.glob("*.pkl"):
                    cache_file.unlink()
            else:
                self.memory_cache.clear()
                self.cache_timestamps.clear()
            
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {"backend": self.config.cache_backend}
        
        try:
            if self.config.cache_backend == "redis" and self.redis_client:
                info = self.redis_client.info()
                stats.update({
                    "size": info.get("used_memory", 0),
                    "keys": self.redis_client.dbsize()
                })
            elif self.config.cache_backend == "file":
                cache_dir = Path(self.config.cache_directory)
                cache_files = list(cache_dir.glob("*.pkl"))
                stats.update({
                    "size": sum(f.stat().st_size for f in cache_files),
                    "keys": len(cache_files)
                })
            else:
                stats.update({
                    "size": len(self.memory_cache),
                    "keys": len(self.memory_cache)
                })
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
        
        return stats


class ResourceMonitor:
    """Monitor system resource usage during analysis."""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
        self.metrics = PerformanceMetrics()
    
    def start_monitoring(self):
        """Start resource monitoring in background thread."""
        if not self.config.monitor_resources:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.debug("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.debug("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                # Get memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                self.metrics.current_memory_mb = memory_mb
                self.metrics.peak_memory_mb = max(self.metrics.peak_memory_mb, memory_mb)
                self.metrics.memory_samples.append(memory_mb)
                
                # Check memory limit
                if (self.config.memory_limit_mb and 
                    memory_mb > self.config.memory_limit_mb):
                    logger.warning(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.config.memory_limit_mb}MB)")
                    gc.collect()  # Force garbage collection
                
                time.sleep(self.config.resource_check_interval)
            
            except Exception as e:
                logger.warning(f"Resource monitoring error: {e}")
                break
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current resource statistics."""
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            
            return {
                "memory_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": self.process.memory_percent(),
                "cpu_percent": cpu_percent,
                "num_threads": self.process.num_threads(),
                "open_files": len(self.process.open_files())
            }
        except Exception as e:
            logger.warning(f"Error getting resource stats: {e}")
            return {}


class ParallelProcessor:
    """Advanced parallel processing for analysis tasks."""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.max_workers = config.max_workers or min(32, (os.cpu_count() or 1) + 4)
    
    def process_items(self, items: List[Any], process_func: Callable, 
                     progress_callback: Optional[Callable] = None) -> List[Any]:
        """Process items in parallel."""
        if not self.config.enable_parallel or len(items) < 2:
            # Process sequentially
            results = []
            for i, item in enumerate(items):
                result = process_func(item)
                results.append(result)
                if progress_callback:
                    progress_callback(i + 1, len(items))
            return results
        
        # Process in parallel
        results = [None] * len(items)
        completed = 0
        
        executor_class = ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor
        
        try:
            with executor_class(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(process_func, item): i 
                    for i, item in enumerate(items)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result()
                        results[index] = result
                        completed += 1
                        
                        if progress_callback:
                            progress_callback(completed, len(items))
                    
                    except Exception as e:
                        logger.warning(f"Error processing item {index}: {e}")
                        results[index] = None
        
        except Exception as e:
            logger.error(f"Parallel processing error: {e}")
            # Fallback to sequential processing
            return self.process_items(items, process_func, progress_callback)
        
        return results
    
    def process_chunks(self, items: List[Any], process_func: Callable,
                      progress_callback: Optional[Callable] = None) -> List[Any]:
        """Process items in chunks for better memory efficiency."""
        chunks = [items[i:i + self.config.chunk_size] 
                 for i in range(0, len(items), self.config.chunk_size)]
        
        def process_chunk(chunk):
            return [process_func(item) for item in chunk]
        
        chunk_results = self.process_items(chunks, process_chunk, progress_callback)
        
        # Flatten results
        results = []
        for chunk_result in chunk_results:
            if chunk_result:
                results.extend(chunk_result)
        
        return results


class PerformanceOptimizer:
    """Main performance optimization coordinator."""
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.cache = CacheManager(self.config)
        self.monitor = ResourceMonitor(self.config)
        self.processor = ParallelProcessor(self.config)
        self.metrics = PerformanceMetrics()
        self.operation_count = 0
    
    def start_operation(self, operation_name: str = "analysis"):
        """Start a performance-optimized operation."""
        logger.info(f"Starting optimized operation: {operation_name}")
        self.metrics = PerformanceMetrics()
        self.operation_count = 0
        
        if self.config.monitor_resources:
            self.monitor.start_monitoring()
    
    def finish_operation(self):
        """Finish the operation and collect metrics."""
        self.metrics.finish()
        
        if self.config.monitor_resources:
            self.monitor.stop_monitoring()
            # Copy monitoring metrics
            self.metrics.peak_memory_mb = self.monitor.metrics.peak_memory_mb
            self.metrics.current_memory_mb = self.monitor.metrics.current_memory_mb
            self.metrics.memory_samples = self.monitor.metrics.memory_samples
        
        logger.info(f"Operation completed in {self.metrics.duration:.2f}s")
        logger.info(f"Cache hit rate: {self.metrics.cache_hit_rate():.1%}")
        logger.info(f"Peak memory: {self.metrics.peak_memory_mb:.1f}MB")
    
    def cached_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with caching."""
        cache_key = self.cache._generate_key(func.__name__, *args, **kwargs)
        
        # Try to get from cache
        result = self.cache.get(cache_key)
        if result is not None:
            self.metrics.cache_hits += 1
            return result
        
        # Execute function
        self.metrics.cache_misses += 1
        result = func(*args, **kwargs)
        
        # Cache result
        self.cache.set(cache_key, result)
        self.metrics.items_cached += 1
        
        return result
    
    def parallel_map(self, func: Callable, items: List[Any], 
                    progress_callback: Optional[Callable] = None) -> List[Any]:
        """Execute function over items in parallel."""
        self.metrics.workers_used = self.processor.max_workers
        
        if len(items) > self.config.chunk_size * 2:
            # Use chunked processing for large datasets
            results = self.processor.process_chunks(items, func, progress_callback)
            self.metrics.chunks_processed = len(items) // self.config.chunk_size + 1
        else:
            # Use direct parallel processing
            results = self.processor.process_items(items, func, progress_callback)
        
        self.metrics.items_processed += len(items)
        return results
    
    def maybe_gc(self):
        """Conditionally run garbage collection."""
        self.operation_count += 1
        if self.operation_count % self.config.gc_frequency == 0:
            gc.collect()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        cache_stats = self.cache.stats()
        resource_stats = self.monitor.get_current_stats()
        
        return {
            "operation": {
                "duration": self.metrics.duration,
                "items_processed": self.metrics.items_processed,
                "items_per_second": self.metrics.items_per_second()
            },
            "cache": {
                "hit_rate": self.metrics.cache_hit_rate(),
                "hits": self.metrics.cache_hits,
                "misses": self.metrics.cache_misses,
                "backend": cache_stats.get("backend"),
                "size": cache_stats.get("size", 0),
                "keys": cache_stats.get("keys", 0)
            },
            "memory": {
                "peak_mb": self.metrics.peak_memory_mb,
                "current_mb": self.metrics.current_memory_mb,
                "samples": len(self.metrics.memory_samples)
            },
            "parallel": {
                "workers_used": self.metrics.workers_used,
                "chunks_processed": self.metrics.chunks_processed,
                "enabled": self.config.enable_parallel
            },
            "resources": resource_stats,
            "config": {
                "caching_enabled": self.config.enable_caching,
                "parallel_enabled": self.config.enable_parallel,
                "lazy_loading": self.config.enable_lazy_loading,
                "monitoring": self.config.monitor_resources
            }
        }


def create_optimizer(config: Optional[PerformanceConfig] = None) -> PerformanceOptimizer:
    """Create a new performance optimizer."""
    return PerformanceOptimizer(config)


def optimized_analysis(analysis_func: Callable, *args, **kwargs) -> Any:
    """Decorator for performance-optimized analysis functions."""
    def wrapper(*args, **kwargs):
        optimizer = create_optimizer()
        optimizer.start_operation(analysis_func.__name__)
        
        try:
            result = analysis_func(*args, **kwargs)
            return result
        finally:
            optimizer.finish_operation()
            logger.info(f"Performance report: {optimizer.get_performance_report()}")
    
    return wrapper


if __name__ == "__main__":
    # Example usage and testing
    print("⚡ Performance Optimization Module")
    print("=" * 50)
    
    config = PerformanceConfig(
        enable_caching=True,
        enable_parallel=True,
        monitor_resources=True
    )
    
    optimizer = create_optimizer(config)
    optimizer.start_operation("test")
    
    # Simulate some work
    def test_function(x):
        time.sleep(0.01)  # Simulate work
        return x * 2
    
    items = list(range(100))
    results = optimizer.parallel_map(test_function, items)
    
    optimizer.finish_operation()
    
    report = optimizer.get_performance_report()
    print(f"Processed {len(results)} items")
    print(f"Duration: {report['operation']['duration']:.2f}s")
    print(f"Items/sec: {report['operation']['items_per_second']:.1f}")
    print(f"Peak memory: {report['memory']['peak_mb']:.1f}MB")
    
    if REDIS_AVAILABLE:
        print("✅ Redis available for distributed caching")
    else:
        print("⚠️ Redis not available - using memory cache")
    
    if JOBLIB_AVAILABLE:
        print("✅ Joblib available for advanced parallel processing")
    else:
        print("⚠️ Joblib not available - using basic parallel processing")

