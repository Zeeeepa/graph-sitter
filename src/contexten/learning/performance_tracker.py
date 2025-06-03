"""
Performance Tracker

This module tracks system performance metrics and provides insights
for continuous improvement and optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics
from collections import defaultdict, deque
import psutil
import time

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    SUCCESS_RATE = "success_rate"
    QUEUE_DEPTH = "queue_depth"
    RESPONSE_TIME = "response_time"


@dataclass
class MetricPoint:
    """A single metric measurement."""
    timestamp: datetime
    metric_type: MetricType
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert when thresholds are exceeded."""
    id: str
    metric_type: MetricType
    severity: str  # low, medium, high, critical
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


@dataclass
class PerformanceTrend:
    """Performance trend analysis."""
    metric_type: MetricType
    direction: str  # improving, degrading, stable
    change_rate: float
    confidence: float
    period_start: datetime
    period_end: datetime
    description: str


class PerformanceTracker:
    """
    Comprehensive performance tracking and analysis system.
    
    This tracker monitors various performance metrics, detects anomalies,
    identifies trends, and provides actionable insights for optimization.
    """
    
    def __init__(self, retention_days: int = 30, alert_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize the performance tracker.
        
        Args:
            retention_days: Number of days to retain metrics
            alert_thresholds: Custom alert thresholds for metrics
        """
        self.retention_days = retention_days
        self.alert_thresholds = alert_thresholds or self._default_thresholds()
        
        self.metrics: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=10000) for metric_type in MetricType
        }
        self.alerts: List[PerformanceAlert] = []
        self.trends: Dict[MetricType, PerformanceTrend] = {}
        
        # Performance baselines
        self.baselines: Dict[MetricType, Dict[str, float]] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("Performance tracker initialized")
    
    def _default_thresholds(self) -> Dict[str, float]:
        """Default alert thresholds."""
        return {
            "error_rate_high": 0.1,  # 10% error rate
            "error_rate_critical": 0.25,  # 25% error rate
            "latency_high": 5.0,  # 5 seconds
            "latency_critical": 10.0,  # 10 seconds
            "memory_usage_high": 80.0,  # 80% memory usage
            "memory_usage_critical": 95.0,  # 95% memory usage
            "cpu_usage_high": 80.0,  # 80% CPU usage
            "cpu_usage_critical": 95.0,  # 95% CPU usage
            "success_rate_low": 0.9,  # 90% success rate
            "success_rate_critical": 0.8  # 80% success rate
        }
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await self._check_alerts()
                await self._update_trends()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self):
        """Collect system-level performance metrics."""
        timestamp = datetime.now()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_metric(MetricPoint(
            timestamp=timestamp,
            metric_type=MetricType.RESOURCE_USAGE,
            value=cpu_percent,
            unit="percent",
            tags={"resource": "cpu"}
        ))
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.record_metric(MetricPoint(
            timestamp=timestamp,
            metric_type=MetricType.RESOURCE_USAGE,
            value=memory.percent,
            unit="percent",
            tags={"resource": "memory"}
        ))
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.record_metric(MetricPoint(
            timestamp=timestamp,
            metric_type=MetricType.RESOURCE_USAGE,
            value=disk_percent,
            unit="percent",
            tags={"resource": "disk"}
        ))
    
    def record_metric(self, metric_point: MetricPoint):
        """Record a performance metric."""
        self.metrics[metric_point.metric_type].append(metric_point)
        
        # Clean up old metrics
        self._cleanup_old_metrics()
        
        logger.debug(f"Recorded metric: {metric_point.metric_type.value} = {metric_point.value}")
    
    def record_task_performance(self, 
                              task_id: str,
                              duration: float,
                              success: bool,
                              error_type: Optional[str] = None):
        """Record task performance metrics."""
        timestamp = datetime.now()
        
        # Record latency
        self.record_metric(MetricPoint(
            timestamp=timestamp,
            metric_type=MetricType.LATENCY,
            value=duration,
            unit="seconds",
            tags={"task_id": task_id},
            metadata={"success": success, "error_type": error_type}
        ))
        
        # Record success/failure
        success_value = 1.0 if success else 0.0
        self.record_metric(MetricPoint(
            timestamp=timestamp,
            metric_type=MetricType.SUCCESS_RATE,
            value=success_value,
            unit="boolean",
            tags={"task_id": task_id},
            metadata={"error_type": error_type}
        ))
    
    def record_throughput(self, 
                         operations_count: int,
                         time_window_seconds: float,
                         operation_type: str = "general"):
        """Record throughput metrics."""
        throughput = operations_count / time_window_seconds
        
        self.record_metric(MetricPoint(
            timestamp=datetime.now(),
            metric_type=MetricType.THROUGHPUT,
            value=throughput,
            unit="ops/second",
            tags={"operation_type": operation_type},
            metadata={"operations_count": operations_count, "time_window": time_window_seconds}
        ))
    
    def record_queue_depth(self, queue_name: str, depth: int):
        """Record queue depth metrics."""
        self.record_metric(MetricPoint(
            timestamp=datetime.now(),
            metric_type=MetricType.QUEUE_DEPTH,
            value=float(depth),
            unit="count",
            tags={"queue_name": queue_name}
        ))
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        for metric_type, metric_deque in self.metrics.items():
            # Remove old metrics from the front of the deque
            while metric_deque and metric_deque[0].timestamp < cutoff_time:
                metric_deque.popleft()
    
    async def _check_alerts(self):
        """Check for performance alerts."""
        current_time = datetime.now()
        
        # Check error rate
        await self._check_error_rate_alerts(current_time)
        
        # Check latency
        await self._check_latency_alerts(current_time)
        
        # Check resource usage
        await self._check_resource_alerts(current_time)
        
        # Check success rate
        await self._check_success_rate_alerts(current_time)
    
    async def _check_error_rate_alerts(self, current_time: datetime):
        """Check for error rate alerts."""
        # Get recent success rate metrics
        recent_metrics = self._get_recent_metrics(MetricType.SUCCESS_RATE, minutes=10)
        if not recent_metrics:
            return
        
        # Calculate error rate
        success_values = [m.value for m in recent_metrics]
        error_rate = 1.0 - statistics.mean(success_values)
        
        # Check thresholds
        if error_rate >= self.alert_thresholds["error_rate_critical"]:
            await self._create_alert(
                metric_type=MetricType.ERROR_RATE,
                severity="critical",
                message=f"Critical error rate: {error_rate:.1%}",
                current_value=error_rate,
                threshold_value=self.alert_thresholds["error_rate_critical"],
                timestamp=current_time
            )
        elif error_rate >= self.alert_thresholds["error_rate_high"]:
            await self._create_alert(
                metric_type=MetricType.ERROR_RATE,
                severity="high",
                message=f"High error rate: {error_rate:.1%}",
                current_value=error_rate,
                threshold_value=self.alert_thresholds["error_rate_high"],
                timestamp=current_time
            )
    
    async def _check_latency_alerts(self, current_time: datetime):
        """Check for latency alerts."""
        recent_metrics = self._get_recent_metrics(MetricType.LATENCY, minutes=10)
        if not recent_metrics:
            return
        
        # Calculate average latency
        latencies = [m.value for m in recent_metrics]
        avg_latency = statistics.mean(latencies)
        
        # Check thresholds
        if avg_latency >= self.alert_thresholds["latency_critical"]:
            await self._create_alert(
                metric_type=MetricType.LATENCY,
                severity="critical",
                message=f"Critical latency: {avg_latency:.2f}s",
                current_value=avg_latency,
                threshold_value=self.alert_thresholds["latency_critical"],
                timestamp=current_time
            )
        elif avg_latency >= self.alert_thresholds["latency_high"]:
            await self._create_alert(
                metric_type=MetricType.LATENCY,
                severity="high",
                message=f"High latency: {avg_latency:.2f}s",
                current_value=avg_latency,
                threshold_value=self.alert_thresholds["latency_high"],
                timestamp=current_time
            )
    
    async def _check_resource_alerts(self, current_time: datetime):
        """Check for resource usage alerts."""
        recent_metrics = self._get_recent_metrics(MetricType.RESOURCE_USAGE, minutes=5)
        
        # Group by resource type
        resource_metrics = defaultdict(list)
        for metric in recent_metrics:
            resource_type = metric.tags.get("resource", "unknown")
            resource_metrics[resource_type].append(metric.value)
        
        # Check each resource type
        for resource_type, values in resource_metrics.items():
            if not values:
                continue
            
            avg_usage = statistics.mean(values)
            threshold_key = f"{resource_type}_usage"
            
            if f"{threshold_key}_critical" in self.alert_thresholds:
                if avg_usage >= self.alert_thresholds[f"{threshold_key}_critical"]:
                    await self._create_alert(
                        metric_type=MetricType.RESOURCE_USAGE,
                        severity="critical",
                        message=f"Critical {resource_type} usage: {avg_usage:.1f}%",
                        current_value=avg_usage,
                        threshold_value=self.alert_thresholds[f"{threshold_key}_critical"],
                        timestamp=current_time
                    )
                elif avg_usage >= self.alert_thresholds[f"{threshold_key}_high"]:
                    await self._create_alert(
                        metric_type=MetricType.RESOURCE_USAGE,
                        severity="high",
                        message=f"High {resource_type} usage: {avg_usage:.1f}%",
                        current_value=avg_usage,
                        threshold_value=self.alert_thresholds[f"{threshold_key}_high"],
                        timestamp=current_time
                    )
    
    async def _check_success_rate_alerts(self, current_time: datetime):
        """Check for success rate alerts."""
        recent_metrics = self._get_recent_metrics(MetricType.SUCCESS_RATE, minutes=15)
        if not recent_metrics:
            return
        
        # Calculate success rate
        success_values = [m.value for m in recent_metrics]
        success_rate = statistics.mean(success_values)
        
        # Check thresholds
        if success_rate <= self.alert_thresholds["success_rate_critical"]:
            await self._create_alert(
                metric_type=MetricType.SUCCESS_RATE,
                severity="critical",
                message=f"Critical success rate: {success_rate:.1%}",
                current_value=success_rate,
                threshold_value=self.alert_thresholds["success_rate_critical"],
                timestamp=current_time
            )
        elif success_rate <= self.alert_thresholds["success_rate_low"]:
            await self._create_alert(
                metric_type=MetricType.SUCCESS_RATE,
                severity="medium",
                message=f"Low success rate: {success_rate:.1%}",
                current_value=success_rate,
                threshold_value=self.alert_thresholds["success_rate_low"],
                timestamp=current_time
            )
    
    async def _create_alert(self, 
                          metric_type: MetricType,
                          severity: str,
                          message: str,
                          current_value: float,
                          threshold_value: float,
                          timestamp: datetime):
        """Create a performance alert."""
        alert_id = f"{metric_type.value}_{severity}_{int(timestamp.timestamp())}"
        
        # Check if similar alert already exists
        existing_alert = self._find_existing_alert(metric_type, severity)
        if existing_alert and not existing_alert.resolved:
            return  # Don't create duplicate alerts
        
        alert = PerformanceAlert(
            id=alert_id,
            metric_type=metric_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
            timestamp=timestamp
        )
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {message}")
    
    def _find_existing_alert(self, metric_type: MetricType, severity: str) -> Optional[PerformanceAlert]:
        """Find existing unresolved alert of the same type and severity."""
        for alert in reversed(self.alerts):  # Check most recent first
            if (alert.metric_type == metric_type and 
                alert.severity == severity and 
                not alert.resolved):
                return alert
        return None
    
    async def _update_trends(self):
        """Update performance trends."""
        for metric_type in MetricType:
            trend = await self._calculate_trend(metric_type)
            if trend:
                self.trends[metric_type] = trend
    
    async def _calculate_trend(self, metric_type: MetricType) -> Optional[PerformanceTrend]:
        """Calculate trend for a specific metric type."""
        # Get metrics from the last 24 hours
        recent_metrics = self._get_recent_metrics(metric_type, hours=24)
        if len(recent_metrics) < 10:  # Need sufficient data
            return None
        
        # Split into two periods for comparison
        mid_point = len(recent_metrics) // 2
        earlier_period = recent_metrics[:mid_point]
        later_period = recent_metrics[mid_point:]
        
        earlier_avg = statistics.mean([m.value for m in earlier_period])
        later_avg = statistics.mean([m.value for m in later_period])
        
        # Calculate change rate
        if earlier_avg == 0:
            change_rate = 0.0
        else:
            change_rate = (later_avg - earlier_avg) / earlier_avg
        
        # Determine direction
        if abs(change_rate) < 0.05:  # Less than 5% change
            direction = "stable"
        elif change_rate > 0:
            direction = "increasing" if metric_type in [MetricType.THROUGHPUT, MetricType.SUCCESS_RATE] else "degrading"
        else:
            direction = "decreasing" if metric_type in [MetricType.THROUGHPUT, MetricType.SUCCESS_RATE] else "improving"
        
        # Calculate confidence based on data consistency
        earlier_std = statistics.stdev([m.value for m in earlier_period]) if len(earlier_period) > 1 else 0
        later_std = statistics.stdev([m.value for m in later_period]) if len(later_period) > 1 else 0
        avg_std = (earlier_std + later_std) / 2
        
        confidence = max(0.1, min(0.9, 1.0 - (avg_std / max(earlier_avg, later_avg, 1))))
        
        return PerformanceTrend(
            metric_type=metric_type,
            direction=direction,
            change_rate=change_rate,
            confidence=confidence,
            period_start=earlier_period[0].timestamp,
            period_end=later_period[-1].timestamp,
            description=f"{metric_type.value} is {direction} with {abs(change_rate):.1%} change"
        )
    
    def _get_recent_metrics(self, 
                          metric_type: MetricType, 
                          minutes: Optional[int] = None,
                          hours: Optional[int] = None) -> List[MetricPoint]:
        """Get recent metrics of a specific type."""
        if minutes:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
        elif hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
        else:
            cutoff_time = datetime.now() - timedelta(minutes=10)  # Default to 10 minutes
        
        return [
            metric for metric in self.metrics[metric_type]
            if metric.timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "alerts": {
                "active": len([a for a in self.alerts if not a.resolved]),
                "total": len(self.alerts),
                "by_severity": defaultdict(int)
            },
            "trends": {}
        }
        
        # Summarize metrics
        for metric_type in MetricType:
            recent_metrics = self._get_recent_metrics(metric_type, hours=1)
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary["metrics"][metric_type.value] = {
                    "count": len(values),
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else None
                }
        
        # Summarize alerts
        for alert in self.alerts:
            summary["alerts"]["by_severity"][alert.severity] += 1
        
        # Summarize trends
        for metric_type, trend in self.trends.items():
            summary["trends"][metric_type.value] = {
                "direction": trend.direction,
                "change_rate": trend.change_rate,
                "confidence": trend.confidence,
                "description": trend.description
            }
        
        return summary
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolution_timestamp = datetime.now()
                logger.info(f"Resolved alert: {alert_id}")
                return True
        return False
    
    def export_metrics(self, 
                      metric_type: Optional[MetricType] = None,
                      hours: int = 24) -> Dict[str, Any]:
        """Export metrics data."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "metrics": {}
        }
        
        metric_types = [metric_type] if metric_type else list(MetricType)
        
        for mt in metric_types:
            metrics = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "value": m.value,
                    "unit": m.unit,
                    "tags": m.tags,
                    "metadata": m.metadata
                }
                for m in self.metrics[mt]
                if m.timestamp >= cutoff_time
            ]
            export_data["metrics"][mt.value] = metrics
        
        return export_data


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the performance tracker."""
        tracker = PerformanceTracker()
        
        # Start monitoring
        await tracker.start_monitoring(interval_seconds=5)
        
        # Simulate some task performance data
        for i in range(10):
            tracker.record_task_performance(
                task_id=f"task_{i}",
                duration=1.0 + i * 0.1,
                success=i % 4 != 0,  # 75% success rate
                error_type="timeout" if i % 4 == 0 else None
            )
            await asyncio.sleep(1)
        
        # Get performance summary
        summary = tracker.get_performance_summary()
        print(f"Performance summary: {json.dumps(summary, indent=2)}")
        
        # Check for alerts
        alerts = tracker.get_active_alerts()
        print(f"Active alerts: {len(alerts)}")
        
        # Stop monitoring
        await tracker.stop_monitoring()
    
    asyncio.run(example_usage())

