"""
Performance monitoring and optimization system.
"""

import asyncio
import time
import psutil
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    active_connections: int
    response_times: Dict[str, float]
    operation_counts: Dict[str, int]
    error_rates: Dict[str, float]


class PerformanceMonitor:
    """System performance monitoring and optimization."""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.operation_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.operation_errors: Dict[str, int] = defaultdict(int)
        
        # Performance targets from settings
        self.target_response_time = 2.0  # seconds
        self.target_concurrent_ops = 1000
        
        # Monitoring state
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize performance monitoring."""
        logger.info("Initializing performance monitoring")
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
    async def shutdown(self) -> None:
        """Shutdown performance monitoring."""
        logger.info("Shutting down performance monitoring")
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for performance issues
                await self._check_performance_thresholds(metrics)
                
                # Wait before next collection
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate response times
        response_times = {}
        for operation, times in self.operation_times.items():
            if times:
                response_times[operation] = sum(times) / len(times)
        
        # Calculate error rates
        error_rates = {}
        for operation in self.operation_counts:
            total_ops = self.operation_counts[operation]
            errors = self.operation_errors[operation]
            error_rates[operation] = (errors / total_ops) * 100 if total_ops > 0 else 0
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            memory_available=memory.available / (1024 * 1024 * 1024),  # GB
            disk_usage=disk.percent,
            active_connections=len(psutil.net_connections()),
            response_times=response_times,
            operation_counts=dict(self.operation_counts),
            error_rates=error_rates
        )
    
    async def _check_performance_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check if performance metrics exceed thresholds."""
        issues = []
        
        # Check CPU usage
        if metrics.cpu_usage > 80:
            issues.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        # Check memory usage
        if metrics.memory_usage > 85:
            issues.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        # Check response times
        for operation, avg_time in metrics.response_times.items():
            if avg_time > self.target_response_time:
                issues.append(f"Slow response time for {operation}: {avg_time:.2f}s")
        
        # Check error rates
        for operation, error_rate in metrics.error_rates.items():
            if error_rate > 5:  # 5% error rate threshold
                issues.append(f"High error rate for {operation}: {error_rate:.1f}%")
        
        if issues:
            logger.warning(f"Performance issues detected: {'; '.join(issues)}")
            
            # Emit performance alert event
            # This would integrate with the orchestrator's event system
            # await self.emit_event("performance_alert", {"issues": issues, "metrics": metrics})
    
    def start_operation(self, operation_name: str) -> 'OperationContext':
        """Start monitoring an operation."""
        return OperationContext(self, operation_name)
    
    async def record_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Record the completion of an operation."""
        self.operation_times[operation_name].append(duration)
        self.operation_counts[operation_name] += 1
        
        if not success:
            self.operation_errors[operation_name] += 1
            logger.debug(f"Operation {operation_name} failed in {duration:.3f}s: {error}")
        else:
            logger.debug(f"Operation {operation_name} completed in {duration:.3f}s")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest = self.metrics_history[-1]
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_usage": latest.cpu_usage,
            "memory_usage": latest.memory_usage,
            "memory_available_gb": latest.memory_available,
            "disk_usage": latest.disk_usage,
            "active_connections": latest.active_connections,
            "average_response_times": latest.response_times,
            "operation_counts": latest.operation_counts,
            "error_rates": latest.error_rates,
            "performance_score": self._calculate_performance_score(latest)
        }
    
    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate an overall performance score (0-100)."""
        score = 100.0
        
        # Deduct points for high resource usage
        if metrics.cpu_usage > 50:
            score -= (metrics.cpu_usage - 50) * 0.5
        
        if metrics.memory_usage > 50:
            score -= (metrics.memory_usage - 50) * 0.5
        
        # Deduct points for slow response times
        for operation, avg_time in metrics.response_times.items():
            if avg_time > self.target_response_time:
                score -= min(20, (avg_time - self.target_response_time) * 10)
        
        # Deduct points for high error rates
        for operation, error_rate in metrics.error_rates.items():
            score -= min(30, error_rate * 3)
        
        return max(0, score)
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a performance report for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter metrics within the time period
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available for the specified period"}
        
        # Calculate aggregated statistics
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        
        # Calculate response time statistics
        response_time_stats = {}
        for operation in set().union(*(m.response_times.keys() for m in recent_metrics)):
            times = [m.response_times.get(operation, 0) for m in recent_metrics if operation in m.response_times]
            if times:
                response_time_stats[operation] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        
        return {
            "period_hours": hours,
            "total_samples": len(recent_metrics),
            "cpu_usage": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values)
            },
            "memory_usage": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values)
            },
            "response_times": response_time_stats,
            "operation_counts": dict(self.operation_counts),
            "error_rates": {
                op: (self.operation_errors[op] / self.operation_counts[op]) * 100
                for op in self.operation_counts if self.operation_counts[op] > 0
            }
        }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Analyze performance and suggest optimizations."""
        if not self.metrics_history:
            return {"error": "No performance data available"}
        
        latest = self.metrics_history[-1]
        suggestions = []
        
        # Analyze CPU usage
        if latest.cpu_usage > 80:
            suggestions.append({
                "type": "cpu",
                "issue": f"High CPU usage: {latest.cpu_usage:.1f}%",
                "suggestion": "Consider scaling horizontally or optimizing CPU-intensive operations"
            })
        
        # Analyze memory usage
        if latest.memory_usage > 85:
            suggestions.append({
                "type": "memory",
                "issue": f"High memory usage: {latest.memory_usage:.1f}%",
                "suggestion": "Consider increasing memory or optimizing memory-intensive operations"
            })
        
        # Analyze response times
        for operation, avg_time in latest.response_times.items():
            if avg_time > self.target_response_time:
                suggestions.append({
                    "type": "response_time",
                    "issue": f"Slow {operation}: {avg_time:.2f}s",
                    "suggestion": f"Optimize {operation} or consider caching"
                })
        
        # Analyze error rates
        for operation, error_rate in latest.error_rates.items():
            if error_rate > 5:
                suggestions.append({
                    "type": "error_rate",
                    "issue": f"High error rate for {operation}: {error_rate:.1f}%",
                    "suggestion": f"Investigate and fix errors in {operation}"
                })
        
        return {
            "performance_score": self._calculate_performance_score(latest),
            "suggestions": suggestions,
            "metrics": await self.get_current_metrics()
        }


class OperationContext:
    """Context manager for monitoring individual operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            
            # Record the operation (this would be async in real usage)
            asyncio.create_task(
                self.monitor.record_operation(
                    self.operation_name, duration, success, error
                )
            )

