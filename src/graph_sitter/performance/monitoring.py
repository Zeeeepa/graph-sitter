"""
Performance Monitoring and Alerting System

Comprehensive monitoring system for tracking performance metrics and generating alerts.
"""

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from datetime import datetime, timedelta

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = auto()      # Monotonically increasing
    GAUGE = auto()        # Point-in-time value
    HISTOGRAM = auto()    # Distribution of values
    TIMER = auto()        # Execution time tracking


@dataclass
class MetricValue:
    """Individual metric value with metadata"""
    value: Union[int, float]
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'value': self.value,
            'timestamp': self.timestamp,
            'labels': self.labels
        }


@dataclass
class Alert:
    """Performance alert"""
    level: AlertLevel
    message: str
    metric_name: str
    current_value: Union[int, float]
    threshold: Union[int, float]
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class MonitoringConfig:
    """Configuration for performance monitoring"""
    enable_metrics: bool = True
    enable_alerts: bool = True
    metrics_retention_hours: int = 24
    alert_retention_hours: int = 72
    collection_interval_seconds: float = 1.0
    alert_cooldown_seconds: float = 300.0
    max_metrics_per_type: int = 10000
    enable_histogram_percentiles: bool = True
    histogram_buckets: List[float] = field(default_factory=lambda: [0.1, 0.5, 0.9, 0.95, 0.99])


class Metric:
    """Base metric class"""
    
    def __init__(self, name: str, metric_type: MetricType, description: str = ""):
        self.name = name
        self.type = metric_type
        self.description = description
        self.values: deque = deque()
        self.labels: Dict[str, str] = {}
        self._lock = threading.RLock()
    
    def add_value(self, value: Union[int, float], labels: Dict[str, str] = None) -> None:
        """Add a value to the metric"""
        with self._lock:
            metric_value = MetricValue(
                value=value,
                labels=labels or {}
            )
            self.values.append(metric_value)
            
            # Limit retention
            max_values = 10000  # Configurable
            while len(self.values) > max_values:
                self.values.popleft()
    
    def get_current_value(self) -> Optional[Union[int, float]]:
        """Get the most recent value"""
        with self._lock:
            if self.values:
                return self.values[-1].value
            return None
    
    def get_values_in_range(self, start_time: float, end_time: float) -> List[MetricValue]:
        """Get values within time range"""
        with self._lock:
            return [
                value for value in self.values
                if start_time <= value.timestamp <= end_time
            ]
    
    def get_statistics(self, window_seconds: float = 300) -> Dict[str, float]:
        """Get statistical summary of recent values"""
        with self._lock:
            cutoff_time = time.time() - window_seconds
            recent_values = [
                value.value for value in self.values
                if value.timestamp >= cutoff_time
            ]
            
            if not recent_values:
                return {}
            
            stats = {
                'count': len(recent_values),
                'min': min(recent_values),
                'max': max(recent_values),
                'avg': sum(recent_values) / len(recent_values),
                'sum': sum(recent_values)
            }
            
            # Add percentiles for histograms
            if self.type == MetricType.HISTOGRAM:
                sorted_values = sorted(recent_values)
                stats.update(self._calculate_percentiles(sorted_values))
            
            return stats
    
    def _calculate_percentiles(self, sorted_values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for histogram metrics"""
        percentiles = {}
        n = len(sorted_values)
        
        for p in [50, 90, 95, 99]:
            index = int((p / 100) * (n - 1))
            percentiles[f'p{p}'] = sorted_values[index]
        
        return percentiles


class Counter(Metric):
    """Counter metric - monotonically increasing"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, MetricType.COUNTER, description)
        self._count = 0
    
    def increment(self, amount: Union[int, float] = 1, labels: Dict[str, str] = None) -> None:
        """Increment counter"""
        with self._lock:
            self._count += amount
            self.add_value(self._count, labels)
    
    def get_count(self) -> Union[int, float]:
        """Get current count"""
        return self._count


class Gauge(Metric):
    """Gauge metric - point-in-time value"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, MetricType.GAUGE, description)
    
    def set(self, value: Union[int, float], labels: Dict[str, str] = None) -> None:
        """Set gauge value"""
        self.add_value(value, labels)
    
    def increment(self, amount: Union[int, float] = 1, labels: Dict[str, str] = None) -> None:
        """Increment gauge value"""
        current = self.get_current_value() or 0
        self.set(current + amount, labels)
    
    def decrement(self, amount: Union[int, float] = 1, labels: Dict[str, str] = None) -> None:
        """Decrement gauge value"""
        current = self.get_current_value() or 0
        self.set(current - amount, labels)


class Histogram(Metric):
    """Histogram metric - distribution of values"""
    
    def __init__(self, name: str, description: str = "", buckets: List[float] = None):
        super().__init__(name, MetricType.HISTOGRAM, description)
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.bucket_counts = defaultdict(int)
    
    def observe(self, value: Union[int, float], labels: Dict[str, str] = None) -> None:
        """Observe a value"""
        self.add_value(value, labels)
        
        # Update bucket counts
        with self._lock:
            for bucket in self.buckets:
                if value <= bucket:
                    self.bucket_counts[bucket] += 1


class Timer(Metric):
    """Timer metric - execution time tracking"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, MetricType.TIMER, description)
    
    def time(self, labels: Dict[str, str] = None) -> 'TimerContext':
        """Create timer context manager"""
        return TimerContext(self, labels)
    
    def record(self, duration: float, labels: Dict[str, str] = None) -> None:
        """Record a duration"""
        self.add_value(duration, labels)


class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, timer: Timer, labels: Dict[str, str] = None):
        self.timer = timer
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.timer.record(duration, self.labels)


class AlertRule:
    """Alert rule for monitoring thresholds"""
    
    def __init__(self, 
                 name: str,
                 metric_name: str,
                 threshold: Union[int, float],
                 comparison: str = "greater_than",
                 level: AlertLevel = AlertLevel.WARNING,
                 message_template: str = None):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.comparison = comparison  # greater_than, less_than, equal_to
        self.level = level
        self.message_template = message_template or f"Metric {metric_name} {comparison} {threshold}"
        self.last_alert_time = 0
        self.cooldown_seconds = 300  # 5 minutes default
    
    def check(self, metric_value: Union[int, float]) -> Optional[Alert]:
        """Check if alert should be triggered"""
        should_alert = False
        
        if self.comparison == "greater_than" and metric_value > self.threshold:
            should_alert = True
        elif self.comparison == "less_than" and metric_value < self.threshold:
            should_alert = True
        elif self.comparison == "equal_to" and metric_value == self.threshold:
            should_alert = True
        
        # Check cooldown
        current_time = time.time()
        if should_alert and (current_time - self.last_alert_time) > self.cooldown_seconds:
            self.last_alert_time = current_time
            
            message = self.message_template.format(
                metric_name=self.metric_name,
                current_value=metric_value,
                threshold=self.threshold
            )
            
            return Alert(
                level=self.level,
                message=message,
                metric_name=self.metric_name,
                current_value=metric_value,
                threshold=self.threshold
            )
        
        return None


class MetricsCollector:
    """Collector for managing metrics and alerts"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.metrics: Dict[str, Metric] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: deque = deque()
        self._lock = threading.RLock()
        self._collection_thread: Optional[threading.Thread] = None
        self._running = False
    
    def create_counter(self, name: str, description: str = "") -> Counter:
        """Create a counter metric"""
        with self._lock:
            counter = Counter(name, description)
            self.metrics[name] = counter
            return counter
    
    def create_gauge(self, name: str, description: str = "") -> Gauge:
        """Create a gauge metric"""
        with self._lock:
            gauge = Gauge(name, description)
            self.metrics[name] = gauge
            return gauge
    
    def create_histogram(self, name: str, description: str = "", buckets: List[float] = None) -> Histogram:
        """Create a histogram metric"""
        with self._lock:
            histogram = Histogram(name, description, buckets)
            self.metrics[name] = histogram
            return histogram
    
    def create_timer(self, name: str, description: str = "") -> Timer:
        """Create a timer metric"""
        with self._lock:
            timer = Timer(name, description)
            self.metrics[name] = timer
            return timer
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name"""
        return self.metrics.get(name)
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add alert rule"""
        with self._lock:
            self.alert_rules[rule.name] = rule
    
    def remove_alert_rule(self, name: str) -> bool:
        """Remove alert rule"""
        with self._lock:
            if name in self.alert_rules:
                del self.alert_rules[name]
                return True
            return False
    
    def check_alerts(self) -> List[Alert]:
        """Check all alert rules and return triggered alerts"""
        triggered_alerts = []
        
        with self._lock:
            for rule in self.alert_rules.values():
                metric = self.metrics.get(rule.metric_name)
                if metric:
                    current_value = metric.get_current_value()
                    if current_value is not None:
                        alert = rule.check(current_value)
                        if alert:
                            triggered_alerts.append(alert)
                            self.alerts.append(alert)
        
        # Clean up old alerts
        self._cleanup_old_alerts()
        
        return triggered_alerts
    
    def _cleanup_old_alerts(self) -> None:
        """Remove old alerts based on retention policy"""
        cutoff_time = time.time() - (self.config.alert_retention_hours * 3600)
        
        while self.alerts and self.alerts[0].timestamp < cutoff_time:
            self.alerts.popleft()
    
    def get_all_metrics_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all metrics"""
        stats = {}
        
        with self._lock:
            for name, metric in self.metrics.items():
                stats[name] = {
                    'type': metric.type.name,
                    'description': metric.description,
                    'current_value': metric.get_current_value(),
                    'statistics': metric.get_statistics()
                }
        
        return stats
    
    def get_recent_alerts(self, hours: int = 1) -> List[Alert]:
        """Get recent alerts"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            return [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        stats = self.get_all_metrics_stats()
        
        if format == "json":
            return json.dumps(stats, indent=2)
        elif format == "prometheus":
            return self._export_prometheus_format(stats)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_prometheus_format(self, stats: Dict[str, Dict[str, Any]]) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        for name, metric_stats in stats.items():
            metric_type = metric_stats['type'].lower()
            description = metric_stats['description']
            current_value = metric_stats['current_value']
            
            if description:
                lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} {metric_type}")
            
            if current_value is not None:
                lines.append(f"{name} {current_value}")
        
        return "\n".join(lines)
    
    def start_collection(self) -> None:
        """Start background metrics collection"""
        if self._running:
            return
        
        self._running = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        logger.info("Metrics collection started")
    
    def stop_collection(self) -> None:
        """Stop background metrics collection"""
        self._running = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Metrics collection stopped")
    
    def _collection_loop(self) -> None:
        """Background collection loop"""
        while self._running:
            try:
                # Check alerts
                if self.config.enable_alerts:
                    alerts = self.check_alerts()
                    for alert in alerts:
                        logger.warning(f"Alert triggered: {alert.message}")
                
                # Sleep until next collection
                time.sleep(self.config.collection_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(1)  # Brief pause before retrying


class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.collector = MetricsCollector(self.config)
        self._function_timers: Dict[str, Timer] = {}
        self._lock = threading.RLock()
        
        # Create default metrics
        self._setup_default_metrics()
        
        # Start collection if enabled
        if self.config.enable_metrics:
            self.collector.start_collection()
    
    def _setup_default_metrics(self) -> None:
        """Setup default system metrics"""
        # Function execution metrics
        self.function_calls = self.collector.create_counter(
            "function_calls_total", 
            "Total number of function calls"
        )
        
        self.function_errors = self.collector.create_counter(
            "function_errors_total", 
            "Total number of function errors"
        )
        
        self.function_duration = self.collector.create_histogram(
            "function_duration_seconds", 
            "Function execution duration in seconds"
        )
        
        # Memory metrics
        self.memory_usage = self.collector.create_gauge(
            "memory_usage_bytes", 
            "Current memory usage in bytes"
        )
        
        # Cache metrics
        self.cache_hits = self.collector.create_counter(
            "cache_hits_total", 
            "Total cache hits"
        )
        
        self.cache_misses = self.collector.create_counter(
            "cache_misses_total", 
            "Total cache misses"
        )
    
    def monitor_function(self, 
                        name: str = None,
                        track_errors: bool = True,
                        track_duration: bool = True) -> Callable[[F], F]:
        """Decorator to monitor function performance"""
        
        def decorator(func: F) -> F:
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Track function call
                self.function_calls.increment(labels={'function': func_name})
                
                # Track duration if enabled
                timer_context = None
                if track_duration:
                    timer_context = self.function_duration.time(labels={'function': func_name})
                    timer_context.__enter__()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    if track_errors:
                        self.function_errors.increment(labels={
                            'function': func_name,
                            'error_type': type(e).__name__
                        })
                    raise
                    
                finally:
                    if timer_context:
                        timer_context.__exit__(None, None, None)
            
            return wrapper
        
        return decorator
    
    def add_alert(self, 
                 name: str,
                 metric_name: str,
                 threshold: Union[int, float],
                 comparison: str = "greater_than",
                 level: AlertLevel = AlertLevel.WARNING) -> None:
        """Add performance alert rule"""
        rule = AlertRule(
            name=name,
            metric_name=metric_name,
            threshold=threshold,
            comparison=comparison,
            level=level
        )
        self.collector.add_alert_rule(rule)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'metrics': self.collector.get_all_metrics_stats(),
            'recent_alerts': self.collector.get_recent_alerts(),
            'collection_config': {
                'enabled': self.config.enable_metrics,
                'interval_seconds': self.config.collection_interval_seconds,
                'retention_hours': self.config.metrics_retention_hours
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown monitoring system"""
        self.collector.stop_collection()


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(config: MonitoringConfig = None) -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(config)
    return _global_monitor


def monitor_performance(name: str = None,
                       track_errors: bool = True,
                       track_duration: bool = True) -> Callable[[F], F]:
    """Global performance monitoring decorator"""
    monitor = get_performance_monitor()
    return monitor.monitor_function(name, track_errors, track_duration)

