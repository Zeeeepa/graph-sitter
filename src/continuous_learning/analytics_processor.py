"""
Analytics Processor for Continuous Learning System

This module implements real-time analytics processing, metrics collection,
and performance monitoring for the continuous learning system.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict, deque
import statistics

from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary
)


class MetricType(Enum):
    """Types of metrics that can be collected."""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    USAGE = "usage"
    ERROR = "error"
    LEARNING = "learning"
    SYSTEM = "system"


class EventType(Enum):
    """Types of events in the analytics system."""
    CODE_ANALYSIS = "code_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    USER_INTERACTION = "user_interaction"
    SYSTEM_PERFORMANCE = "system_performance"
    ERROR_OCCURRENCE = "error_occurrence"
    LEARNING_UPDATE = "learning_update"


@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""
    event_id: str
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'data': self.data,
            'metadata': self.metadata
        }


@dataclass
class Metric:
    """Represents a collected metric."""
    metric_name: str
    metric_type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary representation."""
        return {
            'metric_name': self.metric_name,
            'metric_type': self.metric_type.value,
            'value': self.value,
            'timestamp': self.timestamp,
            'tags': self.tags
        }


class MetricsCollector:
    """Collects and aggregates metrics from various sources."""
    
    def __init__(self, buffer_size: int = 1000):
        self.metrics_buffer: deque = deque(maxlen=buffer_size)
        self.aggregated_metrics: Dict[str, List[float]] = defaultdict(list)
        self.metric_callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    def collect_metric(self, metric: Metric):
        """Collect a single metric."""
        self.metrics_buffer.append(metric)
        self.aggregated_metrics[metric.metric_name].append(metric.value)
        
        # Trigger callbacks
        for callback in self.metric_callbacks[metric.metric_name]:
            try:
                callback(metric)
            except Exception as e:
                print(f"Error in metric callback: {e}")
    
    def collect_performance_metrics(self, operation_name: str, duration: float, 
                                  success: bool = True, **tags):
        """Collect performance metrics for an operation."""
        base_tags = {'operation': operation_name, 'success': str(success)}
        base_tags.update(tags)
        
        # Duration metric
        duration_metric = Metric(
            metric_name=f"{operation_name}_duration",
            metric_type=MetricType.PERFORMANCE,
            value=duration,
            timestamp=time.time(),
            tags=base_tags
        )
        self.collect_metric(duration_metric)
        
        # Success/failure count
        count_metric = Metric(
            metric_name=f"{operation_name}_count",
            metric_type=MetricType.PERFORMANCE,
            value=1.0,
            timestamp=time.time(),
            tags=base_tags
        )
        self.collect_metric(count_metric)
    
    def collect_quality_metrics(self, codebase: Codebase, **tags):
        """Collect code quality metrics from a codebase."""
        timestamp = time.time()
        
        # Basic counts
        file_count = len(list(codebase.files))
        function_count = len(list(codebase.functions))
        class_count = len(list(codebase.classes))
        symbol_count = len(list(codebase.symbols))
        
        metrics = [
            Metric("file_count", MetricType.QUALITY, file_count, timestamp, tags),
            Metric("function_count", MetricType.QUALITY, function_count, timestamp, tags),
            Metric("class_count", MetricType.QUALITY, class_count, timestamp, tags),
            Metric("symbol_count", MetricType.QUALITY, symbol_count, timestamp, tags),
        ]
        
        # Calculate complexity metrics
        total_complexity = 0
        for func in codebase.functions:
            # Simplified complexity calculation
            complexity = len(func.function_calls) + len(func.return_statements)
            total_complexity += complexity
        
        avg_complexity = total_complexity / max(function_count, 1)
        complexity_metric = Metric(
            "average_complexity", MetricType.QUALITY, avg_complexity, timestamp, tags
        )
        metrics.append(complexity_metric)
        
        # Collect all metrics
        for metric in metrics:
            self.collect_metric(metric)
    
    def get_metric_summary(self, metric_name: str, window_size: int = 100) -> Dict[str, float]:
        """Get summary statistics for a metric."""
        values = list(self.aggregated_metrics[metric_name])[-window_size:]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def register_callback(self, metric_name: str, callback: Callable[[Metric], None]):
        """Register a callback for when a specific metric is collected."""
        self.metric_callbacks[metric_name].append(callback)
    
    def get_recent_metrics(self, count: int = 100) -> List[Metric]:
        """Get the most recent metrics."""
        return list(self.metrics_buffer)[-count:]


class EventProcessor:
    """Processes analytics events and extracts insights."""
    
    def __init__(self):
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.event_buffer: deque = deque(maxlen=1000)
        self.processing_stats = {
            'events_processed': 0,
            'processing_errors': 0,
            'average_processing_time': 0.0
        }
    
    async def process_event(self, event: AnalyticsEvent):
        """Process a single analytics event."""
        start_time = time.time()
        
        try:
            self.event_buffer.append(event)
            
            # Call registered handlers
            handlers = self.event_handlers[event.event_type]
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
                    self.processing_stats['processing_errors'] += 1
            
            # Update processing stats
            processing_time = time.time() - start_time
            self.processing_stats['events_processed'] += 1
            
            # Update average processing time
            current_avg = self.processing_stats['average_processing_time']
            count = self.processing_stats['events_processed']
            new_avg = (current_avg * (count - 1) + processing_time) / count
            self.processing_stats['average_processing_time'] = new_avg
            
        except Exception as e:
            print(f"Error processing event: {e}")
            self.processing_stats['processing_errors'] += 1
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler for a specific event type."""
        self.event_handlers[event_type].append(handler)
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about event processing."""
        return {
            **self.processing_stats,
            'buffer_size': len(self.event_buffer),
            'handler_count': sum(len(handlers) for handlers in self.event_handlers.values())
        }


class RealTimeAnalyzer:
    """Performs real-time analysis on incoming data streams."""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size  # seconds
        self.time_windows: Dict[str, deque] = defaultdict(lambda: deque())
        self.anomaly_threshold = 2.0  # standard deviations
    
    def add_data_point(self, metric_name: str, value: float, timestamp: Optional[float] = None):
        """Add a data point for real-time analysis."""
        if timestamp is None:
            timestamp = time.time()
        
        window = self.time_windows[metric_name]
        window.append((timestamp, value))
        
        # Remove old data points outside the window
        cutoff_time = timestamp - self.window_size
        while window and window[0][0] < cutoff_time:
            window.popleft()
    
    def detect_anomalies(self, metric_name: str) -> List[Dict[str, Any]]:
        """Detect anomalies in the metric data."""
        window = self.time_windows[metric_name]
        
        if len(window) < 10:  # Need minimum data points
            return []
        
        values = [point[1] for point in window]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        anomalies = []
        for timestamp, value in window:
            if std_val > 0:
                z_score = abs(value - mean_val) / std_val
                if z_score > self.anomaly_threshold:
                    anomalies.append({
                        'timestamp': timestamp,
                        'value': value,
                        'z_score': z_score,
                        'mean': mean_val,
                        'std_dev': std_val
                    })
        
        return anomalies
    
    def calculate_trend(self, metric_name: str) -> Dict[str, float]:
        """Calculate trend information for a metric."""
        window = self.time_windows[metric_name]
        
        if len(window) < 2:
            return {'trend': 0.0, 'confidence': 0.0}
        
        # Simple linear trend calculation
        timestamps = [point[0] for point in window]
        values = [point[1] for point in window]
        
        # Normalize timestamps
        min_time = min(timestamps)
        norm_timestamps = [t - min_time for t in timestamps]
        
        # Calculate slope (trend)
        n = len(values)
        sum_x = sum(norm_timestamps)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(norm_timestamps, values))
        sum_x2 = sum(x * x for x in norm_timestamps)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return {'trend': 0.0, 'confidence': 0.0}
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Calculate confidence (R-squared)
        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for y in values)
        ss_res = sum((y - (slope * x)) ** 2 for x, y in zip(norm_timestamps, values))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {'trend': slope, 'confidence': r_squared}


class AnalyticsProcessor:
    """Main analytics processor that coordinates metrics collection, event processing, and real-time analysis."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.event_processor = EventProcessor()
        self.real_time_analyzer = RealTimeAnalyzer()
        self.enhanced_analyzer = EnhancedCodebaseAnalyzer()
        
        # Register default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Set up default event handlers."""
        
        async def handle_code_analysis_event(event: AnalyticsEvent):
            """Handle code analysis events."""
            if 'codebase' in event.data:
                codebase = event.data['codebase']
                self.metrics_collector.collect_quality_metrics(codebase)
        
        async def handle_performance_event(event: AnalyticsEvent):
            """Handle performance events."""
            if 'duration' in event.data and 'operation' in event.data:
                self.metrics_collector.collect_performance_metrics(
                    event.data['operation'],
                    event.data['duration'],
                    event.data.get('success', True)
                )
        
        self.event_processor.register_handler(EventType.CODE_ANALYSIS, handle_code_analysis_event)
        self.event_processor.register_handler(EventType.SYSTEM_PERFORMANCE, handle_performance_event)
    
    async def process_codebase_analysis(self, codebase: Codebase) -> Dict[str, Any]:
        """Process a complete codebase analysis with enhanced analytics."""
        start_time = time.time()
        
        try:
            # Get enhanced analysis
            analysis_result = self.enhanced_analyzer.enhanced_analysis(codebase)
            
            # Create analytics event
            event = AnalyticsEvent(
                event_id=f"analysis_{int(time.time())}",
                event_type=EventType.CODE_ANALYSIS,
                timestamp=time.time(),
                data={'codebase': codebase, 'analysis_result': analysis_result}
            )
            
            # Process event
            await self.event_processor.process_event(event)
            
            # Record performance
            duration = time.time() - start_time
            perf_event = AnalyticsEvent(
                event_id=f"perf_{int(time.time())}",
                event_type=EventType.SYSTEM_PERFORMANCE,
                timestamp=time.time(),
                data={'operation': 'codebase_analysis', 'duration': duration, 'success': True}
            )
            await self.event_processor.process_event(perf_event)
            
            return analysis_result
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            error_event = AnalyticsEvent(
                event_id=f"error_{int(time.time())}",
                event_type=EventType.ERROR_OCCURRENCE,
                timestamp=time.time(),
                data={'operation': 'codebase_analysis', 'error': str(e), 'duration': duration}
            )
            await self.event_processor.process_event(error_event)
            raise
    
    def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get data for analytics dashboard."""
        return {
            'metrics_summary': {
                metric_name: self.metrics_collector.get_metric_summary(metric_name)
                for metric_name in ['file_count', 'function_count', 'average_complexity']
            },
            'event_statistics': self.event_processor.get_event_statistics(),
            'anomalies': {
                metric_name: self.real_time_analyzer.detect_anomalies(metric_name)
                for metric_name in ['file_count', 'function_count', 'average_complexity']
            },
            'trends': {
                metric_name: self.real_time_analyzer.calculate_trend(metric_name)
                for metric_name in ['file_count', 'function_count', 'average_complexity']
            }
        }
    
    def register_custom_handler(self, event_type: EventType, handler: Callable):
        """Register a custom event handler."""
        self.event_processor.register_handler(event_type, handler)
    
    def register_metric_callback(self, metric_name: str, callback: Callable[[Metric], None]):
        """Register a callback for metric collection."""
        self.metrics_collector.register_callback(metric_name, callback)


class EnhancedCodebaseAnalyzer:
    """Enhanced version of the existing codebase analyzer with continuous learning integration."""
    
    def __init__(self):
        self.analysis_cache = {}
        self.trend_data = defaultdict(list)
    
    def enhanced_analysis(self, codebase: Codebase) -> Dict[str, Any]:
        """Perform enhanced analysis with trend tracking and predictions."""
        # Get base analysis
        base_summary = get_codebase_summary(codebase)
        
        # Extract metrics for trend analysis
        current_metrics = self._extract_metrics(codebase)
        
        # Update trend data
        timestamp = time.time()
        for metric_name, value in current_metrics.items():
            self.trend_data[metric_name].append((timestamp, value))
            
            # Keep only recent data (last 30 days)
            cutoff = timestamp - (30 * 24 * 3600)
            self.trend_data[metric_name] = [
                (t, v) for t, v in self.trend_data[metric_name] if t > cutoff
            ]
        
        # Calculate trends
        trends = self._calculate_trends()
        
        # Generate predictions
        predictions = self._generate_predictions(current_metrics, trends)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(current_metrics)
        
        return {
            'base_summary': base_summary,
            'current_metrics': current_metrics,
            'trends': trends,
            'predictions': predictions,
            'quality_score': quality_score,
            'recommendations': self._generate_recommendations(current_metrics, trends)
        }
    
    def _extract_metrics(self, codebase: Codebase) -> Dict[str, float]:
        """Extract key metrics from codebase."""
        files = list(codebase.files)
        functions = list(codebase.functions)
        classes = list(codebase.classes)
        symbols = list(codebase.symbols)
        
        return {
            'file_count': len(files),
            'function_count': len(functions),
            'class_count': len(classes),
            'symbol_count': len(symbols),
            'avg_functions_per_file': len(functions) / max(len(files), 1),
            'avg_methods_per_class': sum(len(cls.methods) for cls in classes) / max(len(classes), 1)
        }
    
    def _calculate_trends(self) -> Dict[str, Dict[str, float]]:
        """Calculate trends for all tracked metrics."""
        trends = {}
        
        for metric_name, data_points in self.trend_data.items():
            if len(data_points) < 2:
                trends[metric_name] = {'slope': 0.0, 'confidence': 0.0}
                continue
            
            # Simple linear regression
            timestamps = [point[0] for point in data_points]
            values = [point[1] for point in data_points]
            
            # Normalize timestamps
            min_time = min(timestamps)
            norm_timestamps = [t - min_time for t in timestamps]
            
            # Calculate slope
            n = len(values)
            sum_x = sum(norm_timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(norm_timestamps, values))
            sum_x2 = sum(x * x for x in norm_timestamps)
            
            if n * sum_x2 - sum_x * sum_x == 0:
                slope = 0.0
                r_squared = 0.0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                
                # Calculate R-squared
                mean_y = sum_y / n
                ss_tot = sum((y - mean_y) ** 2 for y in values)
                ss_res = sum((y - (slope * x)) ** 2 for x, y in zip(norm_timestamps, values))
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            trends[metric_name] = {'slope': slope, 'confidence': r_squared}
        
        return trends
    
    def _generate_predictions(self, current_metrics: Dict[str, float], 
                           trends: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Generate predictions for future metric values."""
        predictions = {}
        
        # Predict values 30 days from now
        prediction_horizon = 30 * 24 * 3600  # 30 days in seconds
        
        for metric_name, current_value in current_metrics.items():
            if metric_name in trends:
                trend_data = trends[metric_name]
                slope = trend_data['slope']
                confidence = trend_data['confidence']
                
                # Only make predictions if we have reasonable confidence
                if confidence > 0.5:
                    predicted_value = current_value + (slope * prediction_horizon)
                    predictions[f"{metric_name}_30d"] = max(0, predicted_value)
        
        return predictions
    
    def _calculate_quality_score(self, metrics: Dict[str, float]) -> float:
        """Calculate an overall quality score for the codebase."""
        # Simple quality scoring based on various factors
        score = 100.0
        
        # Penalize for high complexity
        avg_functions_per_file = metrics.get('avg_functions_per_file', 0)
        if avg_functions_per_file > 10:
            score -= min(20, (avg_functions_per_file - 10) * 2)
        
        # Penalize for very large classes
        avg_methods_per_class = metrics.get('avg_methods_per_class', 0)
        if avg_methods_per_class > 15:
            score -= min(15, (avg_methods_per_class - 15) * 1)
        
        # Bonus for reasonable file count
        file_count = metrics.get('file_count', 0)
        if 10 <= file_count <= 100:
            score += 5
        
        return max(0, min(100, score))
    
    def _generate_recommendations(self, metrics: Dict[str, float], 
                                trends: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate recommendations based on metrics and trends."""
        recommendations = []
        
        # Check for growing complexity
        if 'avg_functions_per_file' in trends:
            trend = trends['avg_functions_per_file']
            if trend['slope'] > 0 and trend['confidence'] > 0.7:
                recommendations.append("Consider refactoring large files to reduce functions per file")
        
        # Check for growing class size
        if 'avg_methods_per_class' in trends:
            trend = trends['avg_methods_per_class']
            if trend['slope'] > 0 and trend['confidence'] > 0.7:
                recommendations.append("Consider breaking down large classes into smaller components")
        
        # Check current metrics
        if metrics.get('avg_functions_per_file', 0) > 15:
            recommendations.append("Some files have too many functions - consider splitting them")
        
        if metrics.get('avg_methods_per_class', 0) > 20:
            recommendations.append("Some classes are too large - consider applying Single Responsibility Principle")
        
        return recommendations

