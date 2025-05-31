"""
Performance and quality metrics for graph-sitter operations.

Provides comprehensive metrics collection and analysis for monitoring
codebase health, performance characteristics, and quality indicators.
"""

import time
import threading
from typing import Dict, Any, List, Optional, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """A single metric value with metadata."""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class Metric:
    """Base metric class."""
    
    def __init__(self, name: str, description: str, metric_type: MetricType):
        self.name = name
        self.description = description
        self.type = metric_type
        self._values: List[MetricValue] = []
        self._lock = threading.Lock()
    
    def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        with self._lock:
            metric_value = MetricValue(
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            )
            self._values.append(metric_value)
    
    def get_values(self, since: Optional[float] = None) -> List[MetricValue]:
        """Get metric values, optionally filtered by timestamp."""
        with self._lock:
            if since is None:
                return self._values.copy()
            return [v for v in self._values if v.timestamp >= since]
    
    def clear(self) -> None:
        """Clear all recorded values."""
        with self._lock:
            self._values.clear()


class Counter(Metric):
    """Counter metric that only increases."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, MetricType.COUNTER)
        self._current_value = 0.0
    
    def increment(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the counter."""
        with self._lock:
            self._current_value += amount
            self.record(self._current_value, labels)
    
    def get_current_value(self) -> float:
        """Get current counter value."""
        with self._lock:
            return self._current_value


class Gauge(Metric):
    """Gauge metric that can increase or decrease."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description, MetricType.GAUGE)
        self._current_value = 0.0
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set the gauge value."""
        with self._lock:
            self._current_value = value
            self.record(value, labels)
    
    def increment(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the gauge."""
        with self._lock:
            self._current_value += amount
            self.record(self._current_value, labels)
    
    def decrement(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement the gauge."""
        with self._lock:
            self._current_value -= amount
            self.record(self._current_value, labels)
    
    def get_current_value(self) -> float:
        """Get current gauge value."""
        with self._lock:
            return self._current_value


class Histogram(Metric):
    """Histogram metric for tracking distributions."""
    
    def __init__(self, name: str, description: str, buckets: Optional[List[float]] = None):
        super().__init__(name, description, MetricType.HISTOGRAM)
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]
        self._bucket_counts: Dict[float, int] = {bucket: 0 for bucket in self.buckets}
        self._sum = 0.0
        self._count = 0
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value."""
        with self._lock:
            self.record(value, labels)
            self._sum += value
            self._count += 1
            
            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] += 1
    
    def get_statistics(self) -> Dict[str, float]:
        """Get histogram statistics."""
        with self._lock:
            values = [v.value for v in self._values]
            
            if not values:
                return {
                    'count': 0,
                    'sum': 0,
                    'mean': 0,
                    'median': 0,
                    'std_dev': 0,
                    'min': 0,
                    'max': 0,
                }
            
            return {
                'count': len(values),
                'sum': sum(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
            }
    
    def get_percentile(self, percentile: float) -> float:
        """Get a specific percentile value."""
        with self._lock:
            values = [v.value for v in self._values]
            if not values:
                return 0.0
            
            values.sort()
            index = int(len(values) * percentile / 100)
            return values[min(index, len(values) - 1)]


class Timer(Histogram):
    """Timer metric for measuring durations."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    def time_context(self, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimerContext(self, labels)


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, timer: Timer, labels: Optional[Dict[str, str]] = None):
        self.timer = timer
        self.labels = labels
        self.start_time = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.timer.observe(duration, self.labels)


class PerformanceMetrics:
    """
    Central registry for performance metrics.
    
    Provides a unified interface for collecting and querying
    performance metrics across the graph-sitter system.
    """
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        
        # Initialize common metrics
        self._init_common_metrics()
    
    def _init_common_metrics(self) -> None:
        """Initialize commonly used metrics."""
        # Operation counters
        self.register_counter("operations_total", "Total number of operations")
        self.register_counter("operations_failed", "Number of failed operations")
        
        # Performance timers
        self.register_timer("parse_duration", "Time spent parsing files")
        self.register_timer("analysis_duration", "Time spent analyzing code")
        self.register_timer("modification_duration", "Time spent modifying code")
        
        # Resource gauges
        self.register_gauge("memory_usage", "Current memory usage in bytes")
        self.register_gauge("active_codebases", "Number of active codebases")
        self.register_gauge("cached_symbols", "Number of cached symbols")
        
        # Quality histograms
        self.register_histogram("file_size", "Distribution of file sizes")
        self.register_histogram("complexity_score", "Distribution of complexity scores")
    
    def register_counter(self, name: str, description: str) -> Counter:
        """Register a new counter metric."""
        with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")
            
            counter = Counter(name, description)
            self._metrics[name] = counter
            return counter
    
    def register_gauge(self, name: str, description: str) -> Gauge:
        """Register a new gauge metric."""
        with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")
            
            gauge = Gauge(name, description)
            self._metrics[name] = gauge
            return gauge
    
    def register_histogram(self, name: str, description: str, 
                          buckets: Optional[List[float]] = None) -> Histogram:
        """Register a new histogram metric."""
        with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")
            
            histogram = Histogram(name, description, buckets)
            self._metrics[name] = histogram
            return histogram
    
    def register_timer(self, name: str, description: str) -> Timer:
        """Register a new timer metric."""
        with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")
            
            timer = Timer(name, description)
            self._metrics[name] = timer
            return timer
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        with self._lock:
            return self._metrics.get(name)
    
    def get_counter(self, name: str) -> Optional[Counter]:
        """Get a counter metric by name."""
        metric = self.get_metric(name)
        return metric if isinstance(metric, Counter) else None
    
    def get_gauge(self, name: str) -> Optional[Gauge]:
        """Get a gauge metric by name."""
        metric = self.get_metric(name)
        return metric if isinstance(metric, Gauge) else None
    
    def get_histogram(self, name: str) -> Optional[Histogram]:
        """Get a histogram metric by name."""
        metric = self.get_metric(name)
        return metric if isinstance(metric, Histogram) else None
    
    def get_timer(self, name: str) -> Optional[Timer]:
        """Get a timer metric by name."""
        metric = self.get_metric(name)
        return metric if isinstance(metric, Timer) else None
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics."""
        with self._lock:
            return self._metrics.copy()
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics in a structured format."""
        with self._lock:
            result = {}
            
            for name, metric in self._metrics.items():
                if isinstance(metric, Counter):
                    result[name] = {
                        'type': 'counter',
                        'value': metric.get_current_value(),
                        'description': metric.description,
                    }
                elif isinstance(metric, Gauge):
                    result[name] = {
                        'type': 'gauge',
                        'value': metric.get_current_value(),
                        'description': metric.description,
                    }
                elif isinstance(metric, Histogram):
                    result[name] = {
                        'type': 'histogram',
                        'statistics': metric.get_statistics(),
                        'description': metric.description,
                    }
            
            return result
    
    def clear_all_metrics(self) -> None:
        """Clear all metric values."""
        with self._lock:
            for metric in self._metrics.values():
                metric.clear()


class QualityMetrics:
    """
    Quality metrics for codebase analysis.
    
    Tracks code quality indicators such as complexity,
    maintainability, and technical debt.
    """
    
    def __init__(self):
        self.complexity_scores: List[float] = []
        self.maintainability_scores: List[float] = []
        self.test_coverage: float = 0.0
        self.technical_debt_ratio: float = 0.0
        self.code_duplication: float = 0.0
        self._lock = threading.Lock()
    
    def record_complexity(self, score: float) -> None:
        """Record a complexity score."""
        with self._lock:
            self.complexity_scores.append(score)
    
    def record_maintainability(self, score: float) -> None:
        """Record a maintainability score."""
        with self._lock:
            self.maintainability_scores.append(score)
    
    def set_test_coverage(self, coverage: float) -> None:
        """Set test coverage percentage."""
        with self._lock:
            self.test_coverage = coverage
    
    def set_technical_debt_ratio(self, ratio: float) -> None:
        """Set technical debt ratio."""
        with self._lock:
            self.technical_debt_ratio = ratio
    
    def set_code_duplication(self, duplication: float) -> None:
        """Set code duplication percentage."""
        with self._lock:
            self.code_duplication = duplication
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get overall quality summary."""
        with self._lock:
            summary = {
                'test_coverage': self.test_coverage,
                'technical_debt_ratio': self.technical_debt_ratio,
                'code_duplication': self.code_duplication,
            }
            
            if self.complexity_scores:
                summary['complexity'] = {
                    'mean': statistics.mean(self.complexity_scores),
                    'median': statistics.median(self.complexity_scores),
                    'max': max(self.complexity_scores),
                    'count': len(self.complexity_scores),
                }
            
            if self.maintainability_scores:
                summary['maintainability'] = {
                    'mean': statistics.mean(self.maintainability_scores),
                    'median': statistics.median(self.maintainability_scores),
                    'min': min(self.maintainability_scores),
                    'count': len(self.maintainability_scores),
                }
            
            return summary
    
    def get_quality_grade(self) -> str:
        """Get overall quality grade (A-F)."""
        summary = self.get_quality_summary()
        
        # Simple scoring algorithm
        score = 0
        
        # Test coverage (0-30 points)
        score += min(30, self.test_coverage * 0.3)
        
        # Technical debt (0-25 points, inverted)
        score += max(0, 25 - self.technical_debt_ratio * 25)
        
        # Code duplication (0-20 points, inverted)
        score += max(0, 20 - self.code_duplication * 0.2)
        
        # Complexity (0-25 points)
        if self.complexity_scores:
            avg_complexity = statistics.mean(self.complexity_scores)
            # Assume complexity scale 0-100, lower is better
            score += max(0, 25 - avg_complexity * 0.25)
        
        # Convert to letter grade
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


# Global metrics instances
performance_metrics = PerformanceMetrics()
quality_metrics = QualityMetrics()

