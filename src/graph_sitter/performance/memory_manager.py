"""
Memory Management and Resource Optimization

Advanced memory management system for optimal resource utilization and garbage collection.
"""

import gc
import os
import psutil
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from weakref import WeakSet, WeakKeyDictionary

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class MemoryStrategy(Enum):
    """Memory optimization strategies"""
    CONSERVATIVE = auto()  # Minimal memory optimization
    BALANCED = auto()      # Balanced memory and performance
    AGGRESSIVE = auto()    # Aggressive memory optimization
    STREAMING = auto()     # Streaming/lazy loading


class GCStrategy(Enum):
    """Garbage collection strategies"""
    AUTOMATIC = auto()     # Let Python handle GC
    PERIODIC = auto()      # Periodic forced collection
    THRESHOLD = auto()     # Threshold-based collection
    MANUAL = auto()        # Manual control only


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_memory: int = 0
    available_memory: int = 0
    used_memory: int = 0
    memory_percent: float = 0.0
    gc_collections: int = 0
    gc_collected: int = 0
    gc_uncollectable: int = 0
    object_count: int = 0
    weak_refs: int = 0
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def current(cls) -> 'MemoryStats':
        """Get current memory statistics"""
        memory = psutil.virtual_memory()
        process = psutil.Process()
        
        # Get GC stats
        gc_stats = gc.get_stats()
        total_collections = sum(stat['collections'] for stat in gc_stats)
        total_collected = sum(stat['collected'] for stat in gc_stats)
        total_uncollectable = sum(stat['uncollectable'] for stat in gc_stats)
        
        return cls(
            total_memory=memory.total,
            available_memory=memory.available,
            used_memory=process.memory_info().rss,
            memory_percent=memory.percent,
            gc_collections=total_collections,
            gc_collected=total_collected,
            gc_uncollectable=total_uncollectable,
            object_count=len(gc.get_objects())
        )


@dataclass
class MemoryConfig:
    """Memory management configuration"""
    strategy: MemoryStrategy = MemoryStrategy.BALANCED
    gc_strategy: GCStrategy = GCStrategy.AUTOMATIC
    max_memory_mb: int = 1024
    gc_threshold_mb: int = 100
    gc_interval_seconds: float = 30.0
    enable_weak_refs: bool = True
    enable_object_pooling: bool = True
    enable_lazy_loading: bool = True
    memory_warning_threshold: float = 0.8
    memory_critical_threshold: float = 0.9


class ObjectPool:
    """Object pool for reusing expensive objects"""
    
    def __init__(self, factory: Callable[[], Any], max_size: int = 100):
        self.factory = factory
        self.max_size = max_size
        self._pool: deque = deque()
        self._lock = threading.Lock()
        self._created_count = 0
        self._reused_count = 0
    
    def acquire(self) -> Any:
        """Acquire object from pool"""
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self._reused_count += 1
                return obj
            else:
                obj = self.factory()
                self._created_count += 1
                return obj
    
    def release(self, obj: Any) -> None:
        """Release object back to pool"""
        with self._lock:
            if len(self._pool) < self.max_size:
                # Reset object state if it has a reset method
                if hasattr(obj, 'reset'):
                    obj.reset()
                self._pool.append(obj)
    
    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        return {
            'pool_size': len(self._pool),
            'max_size': self.max_size,
            'created_count': self._created_count,
            'reused_count': self._reused_count,
            'reuse_rate': self._reused_count / max(1, self._created_count + self._reused_count)
        }


class WeakRefManager:
    """Manager for weak references to prevent memory leaks"""
    
    def __init__(self):
        self._weak_refs: WeakSet = WeakSet()
        self._callbacks: WeakKeyDictionary = WeakKeyDictionary()
        self._lock = threading.RLock()
    
    def add_weak_ref(self, obj: Any, callback: Optional[Callable] = None) -> weakref.ref:
        """Add weak reference with optional callback"""
        with self._lock:
            if callback:
                weak_ref = weakref.ref(obj, callback)
                self._callbacks[obj] = callback
            else:
                weak_ref = weakref.ref(obj)
            
            self._weak_refs.add(obj)
            return weak_ref
    
    def remove_weak_ref(self, obj: Any) -> bool:
        """Remove weak reference"""
        with self._lock:
            if obj in self._weak_refs:
                self._weak_refs.discard(obj)
                self._callbacks.pop(obj, None)
                return True
            return False
    
    def get_alive_count(self) -> int:
        """Get count of alive weak references"""
        return len(self._weak_refs)
    
    def cleanup_dead_refs(self) -> int:
        """Clean up dead weak references"""
        # WeakSet automatically handles cleanup
        return 0


class MemoryOptimizer:
    """Advanced memory optimizer with multiple strategies"""
    
    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        self._object_pools: Dict[str, ObjectPool] = {}
        self._weak_ref_manager = WeakRefManager()
        self._memory_stats = MemoryStats.current()
        self._gc_timer: Optional[threading.Timer] = None
        self._lock = threading.RLock()
        self._monitoring_active = False
        
        # Start monitoring if configured
        if self.config.gc_strategy == GCStrategy.PERIODIC:
            self._start_periodic_gc()
    
    def optimize_memory(self, 
                       strategy: MemoryStrategy = None,
                       enable_pooling: bool = None) -> Callable[[F], F]:
        """Decorator to optimize memory usage of functions"""
        
        def decorator(func: F) -> F:
            strategy_to_use = strategy or self.config.strategy
            pooling_enabled = enable_pooling if enable_pooling is not None else self.config.enable_object_pooling
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Pre-execution memory optimization
                if strategy_to_use == MemoryStrategy.AGGRESSIVE:
                    self._aggressive_cleanup()
                elif strategy_to_use == MemoryStrategy.STREAMING:
                    return self._streaming_execution(func, args, kwargs)
                
                # Check memory before execution
                if self._should_trigger_gc():
                    self._force_gc()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Post-execution optimization
                    if strategy_to_use in [MemoryStrategy.BALANCED, MemoryStrategy.AGGRESSIVE]:
                        self._cleanup_after_execution()
                    
                    return result
                    
                except MemoryError:
                    logger.error(f"Memory error in function {func.__name__}")
                    self._emergency_cleanup()
                    raise
            
            return wrapper
        
        return decorator
    
    def _aggressive_cleanup(self) -> None:
        """Perform aggressive memory cleanup"""
        # Force garbage collection
        collected = gc.collect()
        
        # Clear weak references
        self._weak_ref_manager.cleanup_dead_refs()
        
        # Log cleanup results
        logger.debug(f"Aggressive cleanup collected {collected} objects")
    
    def _streaming_execution(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Execute function with streaming/lazy loading strategy"""
        # For streaming, we try to process data in chunks
        # This is a simplified implementation
        return func(*args, **kwargs)
    
    def _should_trigger_gc(self) -> bool:
        """Check if garbage collection should be triggered"""
        if self.config.gc_strategy == GCStrategy.THRESHOLD:
            current_stats = MemoryStats.current()
            memory_usage_mb = current_stats.used_memory / (1024 * 1024)
            return memory_usage_mb > self.config.gc_threshold_mb
        return False
    
    def _force_gc(self) -> int:
        """Force garbage collection"""
        collected = gc.collect()
        self._memory_stats = MemoryStats.current()
        logger.debug(f"Forced GC collected {collected} objects")
        return collected
    
    def _cleanup_after_execution(self) -> None:
        """Cleanup after function execution"""
        # Light cleanup
        if gc.get_count()[0] > 700:  # Default threshold
            gc.collect(0)  # Only collect generation 0
    
    def _emergency_cleanup(self) -> None:
        """Emergency memory cleanup when out of memory"""
        logger.warning("Emergency memory cleanup triggered")
        
        # Clear all object pools
        for pool in self._object_pools.values():
            pool._pool.clear()
        
        # Force full garbage collection
        for generation in range(3):
            gc.collect(generation)
        
        # Clear weak references
        self._weak_ref_manager.cleanup_dead_refs()
    
    def _start_periodic_gc(self) -> None:
        """Start periodic garbage collection"""
        def periodic_gc():
            if self._monitoring_active:
                collected = self._force_gc()
                logger.debug(f"Periodic GC collected {collected} objects")
                
                # Schedule next collection
                self._gc_timer = threading.Timer(
                    self.config.gc_interval_seconds, 
                    periodic_gc
                )
                self._gc_timer.start()
        
        self._monitoring_active = True
        self._gc_timer = threading.Timer(
            self.config.gc_interval_seconds, 
            periodic_gc
        )
        self._gc_timer.start()
    
    def create_object_pool(self, 
                          name: str, 
                          factory: Callable[[], Any], 
                          max_size: int = 100) -> ObjectPool:
        """Create object pool for expensive objects"""
        with self._lock:
            pool = ObjectPool(factory, max_size)
            self._object_pools[name] = pool
            return pool
    
    def get_object_pool(self, name: str) -> Optional[ObjectPool]:
        """Get object pool by name"""
        return self._object_pools.get(name)
    
    def add_weak_ref(self, obj: Any, callback: Optional[Callable] = None) -> weakref.ref:
        """Add weak reference to object"""
        return self._weak_ref_manager.add_weak_ref(obj, callback)
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        return MemoryStats.current()
    
    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        stats = {
            'memory_stats': self.get_memory_stats(),
            'weak_refs_count': self._weak_ref_manager.get_alive_count(),
            'object_pools': {}
        }
        
        for name, pool in self._object_pools.items():
            stats['object_pools'][name] = pool.get_stats()
        
        return stats
    
    def check_memory_pressure(self) -> Dict[str, Any]:
        """Check for memory pressure and return recommendations"""
        stats = self.get_memory_stats()
        pressure_info = {
            'memory_percent': stats.memory_percent,
            'status': 'normal',
            'recommendations': []
        }
        
        if stats.memory_percent > self.config.memory_critical_threshold * 100:
            pressure_info['status'] = 'critical'
            pressure_info['recommendations'].extend([
                'Immediate garbage collection needed',
                'Consider reducing cache sizes',
                'Review object pools for cleanup'
            ])
        elif stats.memory_percent > self.config.memory_warning_threshold * 100:
            pressure_info['status'] = 'warning'
            pressure_info['recommendations'].extend([
                'Monitor memory usage closely',
                'Consider proactive cleanup'
            ])
        
        return pressure_info
    
    def shutdown(self) -> None:
        """Shutdown memory optimizer"""
        self._monitoring_active = False
        if self._gc_timer:
            self._gc_timer.cancel()
        
        # Final cleanup
        self._emergency_cleanup()


class MemoryManager:
    """Main memory manager coordinating all memory optimization"""
    
    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        self.optimizer = MemoryOptimizer(self.config)
        self._optimizers: Dict[str, MemoryOptimizer] = {}
        self._lock = threading.RLock()
    
    def get_optimizer(self, name: str = "default") -> MemoryOptimizer:
        """Get or create named optimizer instance"""
        with self._lock:
            if name == "default":
                return self.optimizer
            
            if name not in self._optimizers:
                self._optimizers[name] = MemoryOptimizer(self.config)
            
            return self._optimizers[name]
    
    def optimize_memory(self, 
                       strategy: MemoryStrategy = None,
                       optimizer_name: str = "default") -> Callable[[F], F]:
        """Main memory optimization decorator"""
        optimizer = self.get_optimizer(optimizer_name)
        return optimizer.optimize_memory(strategy)
    
    def create_object_pool(self, 
                          name: str, 
                          factory: Callable[[], Any], 
                          max_size: int = 100,
                          optimizer_name: str = "default") -> ObjectPool:
        """Create object pool"""
        optimizer = self.get_optimizer(optimizer_name)
        return optimizer.create_object_pool(name, factory, max_size)
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global memory statistics"""
        stats = {
            'system_memory': MemoryStats.current(),
            'optimizers': {}
        }
        
        stats['optimizers']['default'] = self.optimizer.get_optimizer_stats()
        
        for name, optimizer in self._optimizers.items():
            stats['optimizers'][name] = optimizer.get_optimizer_stats()
        
        return stats
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system memory health"""
        health_info = {
            'status': 'healthy',
            'memory_pressure': self.optimizer.check_memory_pressure(),
            'recommendations': [],
            'optimizers_status': {}
        }
        
        # Check each optimizer
        for name, optimizer in [('default', self.optimizer)] + list(self._optimizers.items()):
            pressure = optimizer.check_memory_pressure()
            health_info['optimizers_status'][name] = pressure
            
            if pressure['status'] == 'critical':
                health_info['status'] = 'critical'
            elif pressure['status'] == 'warning' and health_info['status'] == 'healthy':
                health_info['status'] = 'warning'
        
        return health_info
    
    def emergency_cleanup(self) -> None:
        """Perform emergency cleanup across all optimizers"""
        logger.warning("Emergency cleanup triggered across all memory optimizers")
        
        self.optimizer._emergency_cleanup()
        for optimizer in self._optimizers.values():
            optimizer._emergency_cleanup()
    
    def shutdown_all(self) -> None:
        """Shutdown all memory optimizers"""
        self.optimizer.shutdown()
        for optimizer in self._optimizers.values():
            optimizer.shutdown()
        self._optimizers.clear()


# Global memory manager instance
_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(config: MemoryConfig = None) -> MemoryManager:
    """Get global memory manager instance"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager(config)
    return _global_memory_manager


def memory_optimized(strategy: MemoryStrategy = None,
                    optimizer_name: str = "default") -> Callable[[F], F]:
    """Global memory optimization decorator"""
    manager = get_memory_manager()
    return manager.optimize_memory(strategy, optimizer_name)


# Convenience decorators for common memory strategies
def conservative_memory(optimizer_name: str = "default") -> Callable[[F], F]:
    """Conservative memory optimization"""
    return memory_optimized(MemoryStrategy.CONSERVATIVE, optimizer_name)


def balanced_memory(optimizer_name: str = "default") -> Callable[[F], F]:
    """Balanced memory optimization"""
    return memory_optimized(MemoryStrategy.BALANCED, optimizer_name)


def aggressive_memory(optimizer_name: str = "default") -> Callable[[F], F]:
    """Aggressive memory optimization"""
    return memory_optimized(MemoryStrategy.AGGRESSIVE, optimizer_name)


def streaming_memory(optimizer_name: str = "default") -> Callable[[F], F]:
    """Streaming memory optimization"""
    return memory_optimized(MemoryStrategy.STREAMING, optimizer_name)

