"""
Performance monitoring utilities for graph-sitter operations.

Provides decorators and context managers for monitoring performance
of critical operations, with support for metrics collection and alerting.
"""

import time
import functools
import threading
from typing import Dict, Any, Optional, Callable, TypeVar, List
from dataclasses import dataclass, field
from contextlib import contextmanager
import psutil
import logging

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    name: str
    duration: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_percent: float
    timestamp: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def memory_delta(self) -> float:
        """Memory change during operation."""
        return self.memory_after - self.memory_before

    @property
    def memory_efficiency(self) -> float:
        """Memory efficiency score (0-1)."""
        if self.memory_peak == 0:
            return 1.0
        return min(1.0, self.memory_before / self.memory_peak)


class PerformanceMonitor:
    """
    Thread-safe performance monitor for graph-sitter operations.
    
    Tracks operation metrics, provides alerting for performance issues,
    and supports both real-time monitoring and historical analysis.
    """
    
    def __init__(self, 
                 alert_threshold_seconds: float = 10.0,
                 memory_threshold_mb: float = 1000.0,
                 max_history: int = 1000):
        self.alert_threshold = alert_threshold_seconds
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  # Convert to bytes
        self.max_history = max_history
        
        self._metrics: List[OperationMetrics] = []
        self._lock = threading.Lock()
        self._process = psutil.Process()
    
    def record_operation(self, metrics: OperationMetrics) -> None:
        """Record operation metrics with thread safety."""
        with self._lock:
            self._metrics.append(metrics)
            
            # Maintain max history size
            if len(self._metrics) > self.max_history:
                self._metrics = self._metrics[-self.max_history:]
            
            # Check for performance alerts
            self._check_alerts(metrics)
    
    def _check_alerts(self, metrics: OperationMetrics) -> None:
        """Check if metrics trigger any performance alerts."""
        if metrics.duration > self.alert_threshold:
            logger.warning(
                f"Slow operation detected: {metrics.name} took {metrics.duration:.2f}s "
                f"(threshold: {self.alert_threshold}s)"
            )
        
        if metrics.memory_delta > self.memory_threshold:
            logger.warning(
                f"High memory usage: {metrics.name} used {metrics.memory_delta / 1024 / 1024:.1f}MB "
                f"(threshold: {self.memory_threshold / 1024 / 1024:.1f}MB)"
            )
        
        if not metrics.success and metrics.error:
            logger.error(f"Operation failed: {metrics.name} - {metrics.error}")
    
    def get_metrics(self, operation_name: Optional[str] = None) -> List[OperationMetrics]:
        """Get recorded metrics, optionally filtered by operation name."""
        with self._lock:
            if operation_name:
                return [m for m in self._metrics if m.name == operation_name]
            return self._metrics.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        with self._lock:
            if not self._metrics:
                return {"total_operations": 0}
            
            successful_ops = [m for m in self._metrics if m.success]
            failed_ops = [m for m in self._metrics if not m.success]
            
            durations = [m.duration for m in successful_ops]
            memory_deltas = [m.memory_delta for m in successful_ops]
            
            return {
                "total_operations": len(self._metrics),
                "successful_operations": len(successful_ops),
                "failed_operations": len(failed_ops),
                "success_rate": len(successful_ops) / len(self._metrics) if self._metrics else 0,
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "avg_memory_delta": sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
                "max_memory_delta": max(memory_deltas) if memory_deltas else 0,
                "operations_by_name": self._get_operations_by_name(),
            }
    
    def _get_operations_by_name(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics grouped by operation name."""
        by_name: Dict[str, List[OperationMetrics]] = {}
        
        for metric in self._metrics:
            if metric.name not in by_name:
                by_name[metric.name] = []
            by_name[metric.name].append(metric)
        
        result = {}
        for name, metrics in by_name.items():
            successful = [m for m in metrics if m.success]
            durations = [m.duration for m in successful]
            
            result[name] = {
                "count": len(metrics),
                "success_rate": len(successful) / len(metrics) if metrics else 0,
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
            }
        
        return result
    
    @contextmanager
    def monitor_operation(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for monitoring an operation."""
        metadata = metadata or {}
        
        # Get initial state
        memory_before = self._process.memory_info().rss
        cpu_before = self._process.cpu_percent()
        start_time = time.time()
        
        success = True
        error = None
        memory_peak = memory_before
        
        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            # Get final state
            end_time = time.time()
            memory_after = self._process.memory_info().rss
            cpu_after = self._process.cpu_percent()
            
            # Record peak memory (approximate)
            memory_peak = max(memory_before, memory_after)
            
            metrics = OperationMetrics(
                name=name,
                duration=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                cpu_percent=(cpu_before + cpu_after) / 2,
                timestamp=start_time,
                success=success,
                error=error,
                metadata=metadata
            )
            
            self.record_operation(metrics)


# Global monitor instance
_global_monitor = PerformanceMonitor()


def monitor_performance(name: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> Callable[[F], F]:
    """
    Decorator for monitoring function performance.
    
    Args:
        name: Operation name (defaults to function name)
        metadata: Additional metadata to record
    
    Returns:
        Decorated function with performance monitoring
    """
    def decorator(func: F) -> F:
        operation_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with _global_monitor.monitor_operation(operation_name, metadata):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get_global_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor


def reset_global_monitor() -> None:
    """Reset the global performance monitor."""
    global _global_monitor
    _global_monitor = PerformanceMonitor()


# Convenience functions for common monitoring patterns
@contextmanager
def monitor_codebase_operation(operation: str, codebase_path: str):
    """Monitor a codebase-related operation."""
    metadata = {"codebase_path": codebase_path}
    with _global_monitor.monitor_operation(f"codebase_{operation}", metadata):
        yield


@contextmanager  
def monitor_file_operation(operation: str, file_path: str, file_size: Optional[int] = None):
    """Monitor a file-related operation."""
    metadata = {"file_path": file_path}
    if file_size is not None:
        metadata["file_size"] = file_size
    
    with _global_monitor.monitor_operation(f"file_{operation}", metadata):
        yield


@contextmanager
def monitor_symbol_operation(operation: str, symbol_count: int):
    """Monitor a symbol-related operation."""
    metadata = {"symbol_count": symbol_count}
    with _global_monitor.monitor_operation(f"symbol_{operation}", metadata):
        yield

