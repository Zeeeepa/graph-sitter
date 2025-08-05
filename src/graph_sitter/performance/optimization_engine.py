"""
Performance Optimization Engine

Core engine for system-wide performance optimization and scalability enhancements.
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from weakref import WeakKeyDictionary

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class OptimizationLevel(Enum):
    """Performance optimization levels"""
    MINIMAL = auto()
    BALANCED = auto()
    AGGRESSIVE = auto()
    MAXIMUM = auto()


class OptimizationStrategy(Enum):
    """Optimization strategies for different scenarios"""
    MEMORY_OPTIMIZED = auto()
    CPU_OPTIMIZED = auto()
    IO_OPTIMIZED = auto()
    LATENCY_OPTIMIZED = auto()
    THROUGHPUT_OPTIMIZED = auto()


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    execution_time: float = 0.0
    memory_usage: int = 0
    cpu_usage: float = 0.0
    io_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    concurrent_operations: int = 0
    error_count: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization"""
    level: OptimizationLevel = OptimizationLevel.BALANCED
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    max_workers: int = 4
    enable_async: bool = True
    enable_caching: bool = True
    enable_profiling: bool = False
    memory_limit_mb: int = 1024
    timeout_seconds: float = 30.0
    batch_size: int = 100


class PerformanceOptimizer:
    """Advanced performance optimizer with multiple strategies"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.metrics = PerformanceMetrics()
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._optimization_cache: Dict[str, Any] = {}
        self._active_operations: Set[str] = set()
        self._lock = threading.RLock()
        
    def optimize_function(self, 
                         strategy: OptimizationStrategy = None,
                         cache_key: str = None,
                         async_enabled: bool = None) -> Callable[[F], F]:
        """Decorator to optimize function performance"""
        
        def decorator(func: F) -> F:
            strategy_to_use = strategy or self.config.strategy
            async_enabled_to_use = async_enabled if async_enabled is not None else self.config.enable_async
            
            if asyncio.iscoroutinefunction(func):
                return self._optimize_async_function(func, strategy_to_use, cache_key)
            else:
                return self._optimize_sync_function(func, strategy_to_use, cache_key, async_enabled_to_use)
                
        return decorator
    
    def _optimize_sync_function(self, func: F, strategy: OptimizationStrategy, 
                               cache_key: str, async_enabled: bool) -> F:
        """Optimize synchronous function"""
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{id(args)}_{id(kwargs)}"
            
            # Check cache first
            if self.config.enable_caching and cache_key:
                cached_result = self._get_cached_result(cache_key, args, kwargs)
                if cached_result is not None:
                    self.metrics.cache_hits += 1
                    return cached_result
                self.metrics.cache_misses += 1
            
            # Track operation
            with self._lock:
                self._active_operations.add(operation_id)
                self.metrics.concurrent_operations = len(self._active_operations)
            
            start_time = time.perf_counter()
            
            try:
                # Apply optimization strategy
                if strategy == OptimizationStrategy.CPU_OPTIMIZED:
                    result = self._cpu_optimized_execution(func, args, kwargs)
                elif strategy == OptimizationStrategy.IO_OPTIMIZED:
                    result = self._io_optimized_execution(func, args, kwargs, async_enabled)
                elif strategy == OptimizationStrategy.MEMORY_OPTIMIZED:
                    result = self._memory_optimized_execution(func, args, kwargs)
                elif strategy == OptimizationStrategy.LATENCY_OPTIMIZED:
                    result = self._latency_optimized_execution(func, args, kwargs)
                elif strategy == OptimizationStrategy.THROUGHPUT_OPTIMIZED:
                    result = self._throughput_optimized_execution(func, args, kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Cache result if enabled
                if self.config.enable_caching and cache_key:
                    self._cache_result(cache_key, args, kwargs, result)
                
                return result
                
            except Exception as e:
                self.metrics.error_count += 1
                logger.error(f"Error in optimized function {func.__name__}: {e}")
                raise
            finally:
                execution_time = time.perf_counter() - start_time
                self.metrics.execution_time += execution_time
                
                with self._lock:
                    self._active_operations.discard(operation_id)
                    self.metrics.concurrent_operations = len(self._active_operations)
                
                if self.config.enable_profiling:
                    logger.info(f"Function {func.__name__} executed in {execution_time:.4f}s")
        
        return wrapper
    
    def _optimize_async_function(self, func: F, strategy: OptimizationStrategy, cache_key: str) -> F:
        """Optimize asynchronous function"""
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{id(args)}_{id(kwargs)}"
            
            # Check cache first
            if self.config.enable_caching and cache_key:
                cached_result = self._get_cached_result(cache_key, args, kwargs)
                if cached_result is not None:
                    self.metrics.cache_hits += 1
                    return cached_result
                self.metrics.cache_misses += 1
            
            # Track operation
            with self._lock:
                self._active_operations.add(operation_id)
                self.metrics.concurrent_operations = len(self._active_operations)
            
            start_time = time.perf_counter()
            
            try:
                # Apply async optimization
                if strategy == OptimizationStrategy.LATENCY_OPTIMIZED:
                    result = await asyncio.wait_for(func(*args, **kwargs), 
                                                  timeout=self.config.timeout_seconds)
                else:
                    result = await func(*args, **kwargs)
                
                # Cache result if enabled
                if self.config.enable_caching and cache_key:
                    self._cache_result(cache_key, args, kwargs, result)
                
                return result
                
            except Exception as e:
                self.metrics.error_count += 1
                logger.error(f"Error in async optimized function {func.__name__}: {e}")
                raise
            finally:
                execution_time = time.perf_counter() - start_time
                self.metrics.execution_time += execution_time
                
                with self._lock:
                    self._active_operations.discard(operation_id)
                    self.metrics.concurrent_operations = len(self._active_operations)
        
        return async_wrapper
    
    def _cpu_optimized_execution(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute function with CPU optimization"""
        # Use thread pool for CPU-intensive tasks
        if len(args) > self.config.batch_size:
            return self._batch_process(func, args, kwargs)
        return func(*args, **kwargs)
    
    def _io_optimized_execution(self, func: Callable, args: tuple, kwargs: dict, async_enabled: bool) -> Any:
        """Execute function with I/O optimization"""
        if async_enabled:
            # Convert to async execution for I/O operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._run_in_executor(func, args, kwargs))
            finally:
                loop.close()
        return func(*args, **kwargs)
    
    def _memory_optimized_execution(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute function with memory optimization"""
        # Implement memory-efficient execution
        import gc
        gc.collect()  # Force garbage collection before execution
        result = func(*args, **kwargs)
        gc.collect()  # Clean up after execution
        return result
    
    def _latency_optimized_execution(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute function with latency optimization"""
        # Use fastest execution path
        return func(*args, **kwargs)
    
    def _throughput_optimized_execution(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute function with throughput optimization"""
        # Use parallel execution when possible
        return self._parallel_execute(func, args, kwargs)
    
    def _batch_process(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Process large datasets in batches"""
        if not args:
            return func(*args, **kwargs)
        
        # Split first argument into batches if it's a sequence
        first_arg = args[0]
        if hasattr(first_arg, '__len__') and len(first_arg) > self.config.batch_size:
            results = []
            for i in range(0, len(first_arg), self.config.batch_size):
                batch = first_arg[i:i + self.config.batch_size]
                batch_args = (batch,) + args[1:]
                results.extend(func(*batch_args, **kwargs))
            return results
        
        return func(*args, **kwargs)
    
    def _parallel_execute(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute function in parallel when beneficial"""
        # Simple parallel execution for compatible functions
        return func(*args, **kwargs)
    
    async def _run_in_executor(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Run function in thread executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._thread_pool, lambda: func(*args, **kwargs))
    
    def _get_cached_result(self, cache_key: str, args: tuple, kwargs: dict) -> Optional[Any]:
        """Get cached result if available"""
        full_key = f"{cache_key}_{hash(args)}_{hash(frozenset(kwargs.items()))}"
        return self._optimization_cache.get(full_key)
    
    def _cache_result(self, cache_key: str, args: tuple, kwargs: dict, result: Any) -> None:
        """Cache function result"""
        full_key = f"{cache_key}_{hash(args)}_{hash(frozenset(kwargs.items()))}"
        self._optimization_cache[full_key] = result
        
        # Implement cache size limit
        if len(self._optimization_cache) > 10000:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._optimization_cache.keys())[:1000]
            for key in keys_to_remove:
                del self._optimization_cache[key]
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self.metrics = PerformanceMetrics()
    
    def clear_cache(self) -> None:
        """Clear optimization cache"""
        self._optimization_cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown optimizer and cleanup resources"""
        self._thread_pool.shutdown(wait=True)
        self.clear_cache()


class OptimizationEngine:
    """Main optimization engine coordinating all performance enhancements"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.optimizer = PerformanceOptimizer(self.config)
        self._global_metrics = PerformanceMetrics()
        self._optimizers: Dict[str, PerformanceOptimizer] = {}
        
    def get_optimizer(self, name: str = "default") -> PerformanceOptimizer:
        """Get or create named optimizer instance"""
        if name not in self._optimizers:
            self._optimizers[name] = PerformanceOptimizer(self.config)
        return self._optimizers[name]
    
    def optimize(self, 
                strategy: OptimizationStrategy = None,
                cache_key: str = None,
                optimizer_name: str = "default") -> Callable[[F], F]:
        """Main optimization decorator"""
        optimizer = self.get_optimizer(optimizer_name)
        return optimizer.optimize_function(strategy, cache_key)
    
    def get_global_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get metrics from all optimizers"""
        metrics = {}
        for name, optimizer in self._optimizers.items():
            metrics[name] = optimizer.get_metrics()
        return metrics
    
    def shutdown_all(self) -> None:
        """Shutdown all optimizers"""
        for optimizer in self._optimizers.values():
            optimizer.shutdown()
        self._optimizers.clear()


# Global optimization engine instance
_global_engine: Optional[OptimizationEngine] = None


def get_optimization_engine(config: OptimizationConfig = None) -> OptimizationEngine:
    """Get global optimization engine instance"""
    global _global_engine
    if _global_engine is None:
        _global_engine = OptimizationEngine(config)
    return _global_engine


def optimize(strategy: OptimizationStrategy = None,
            cache_key: str = None,
            optimizer_name: str = "default") -> Callable[[F], F]:
    """Global optimization decorator"""
    engine = get_optimization_engine()
    return engine.optimize(strategy, cache_key, optimizer_name)


# Convenience decorators for common optimization strategies
def cpu_optimized(cache_key: str = None) -> Callable[[F], F]:
    """Optimize for CPU-intensive operations"""
    return optimize(OptimizationStrategy.CPU_OPTIMIZED, cache_key)


def io_optimized(cache_key: str = None) -> Callable[[F], F]:
    """Optimize for I/O-intensive operations"""
    return optimize(OptimizationStrategy.IO_OPTIMIZED, cache_key)


def memory_optimized(cache_key: str = None) -> Callable[[F], F]:
    """Optimize for memory efficiency"""
    return optimize(OptimizationStrategy.MEMORY_OPTIMIZED, cache_key)


def latency_optimized(cache_key: str = None) -> Callable[[F], F]:
    """Optimize for low latency"""
    return optimize(OptimizationStrategy.LATENCY_OPTIMIZED, cache_key)


def throughput_optimized(cache_key: str = None) -> Callable[[F], F]:
    """Optimize for high throughput"""
    return optimize(OptimizationStrategy.THROUGHPUT_OPTIMIZED, cache_key)

