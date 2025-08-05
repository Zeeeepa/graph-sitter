"""
Analytics Engine for Graph-Sitter CI/CD

Provides comprehensive analytics and monitoring:
- Performance metrics collection
- Pattern analysis and insights
- Predictive analytics
- System optimization recommendations
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AnalysisType(Enum):
    """Types of analysis"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    RELIABILITY = "reliability"
    EFFICIENCY = "efficiency"
    TREND = "trend"
    ANOMALY = "anomaly"


@dataclass
class Metric:
    """System metric definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    metric_type: MetricType = MetricType.GAUGE
    value: float = 0.0
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    dimensions: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_tag(self, key: str, value: str) -> None:
        """Add a tag to the metric"""
        self.tags[key] = value
    
    def add_dimension(self, key: str, value: Any) -> None:
        """Add a dimension to the metric"""
        self.dimensions[key] = value


@dataclass
class AnalysisResult:
    """Analysis result with insights and recommendations"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_type: AnalysisType = AnalysisType.PERFORMANCE
    target_type: str = ""  # task, pipeline, system, component
    target_id: str = ""
    
    # Analysis period
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=7))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Results
    score: float = 0.0  # 0-100 score
    insights: List[str] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Trends
    trend_direction: str = "stable"  # improving, declining, stable
    trend_confidence: float = 0.0  # 0-1 confidence
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_insight(self, insight: str) -> None:
        """Add an insight to the analysis"""
        self.insights.append(insight)
    
    def add_recommendation(self, title: str, description: str, priority: str = "medium", impact: str = "medium") -> None:
        """Add a recommendation to the analysis"""
        self.recommendations.append({
            "title": title,
            "description": description,
            "priority": priority,
            "impact": impact,
            "id": str(uuid.uuid4())
        })


@dataclass
class Pattern:
    """Detected pattern in system behavior"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = ""
    name: str = ""
    description: str = ""
    
    # Pattern characteristics
    frequency: str = ""  # daily, weekly, monthly, irregular
    confidence: float = 0.0  # 0-1 confidence
    significance: float = 0.0  # 0-1 significance
    
    # Pattern data
    pattern_data: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Impact
    impact_score: float = 0.0  # 0-100
    affected_components: List[str] = field(default_factory=list)
    
    # Lifecycle
    first_detected: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_observed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class MetricsCollector:
    """
    Metrics collection and storage system
    """
    
    def __init__(self, organization_id: str, database_connection=None):
        self.organization_id = organization_id
        self.db = database_connection
        
        # In-memory storage (would be replaced with time-series database in production)
        self.metrics: List[Metric] = []
        self.metric_definitions: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.retention_days = 90
        self.aggregation_intervals = [60, 300, 3600, 86400]  # 1min, 5min, 1hour, 1day
        
        # Performance tracking
        self.collection_stats = {
            "total_metrics_collected": 0,
            "metrics_per_second": 0.0,
            "last_collection_time": datetime.now(timezone.utc)
        }
    
    async def collect_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                           unit: str = "", tags: Dict[str, str] = None, dimensions: Dict[str, Any] = None) -> str:
        """Collect a single metric"""
        metric = Metric(
            name=name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {},
            dimensions=dimensions or {}
        )
        
        self.metrics.append(metric)
        self.collection_stats["total_metrics_collected"] += 1
        
        # Store in database if available
        if self.db:
            await self._store_metric_in_db(metric)
        
        return metric.id
    
    async def collect_batch_metrics(self, metrics_data: List[Dict[str, Any]]) -> List[str]:
        """Collect multiple metrics in batch"""
        metric_ids = []
        
        for metric_data in metrics_data:
            metric_id = await self.collect_metric(
                name=metric_data["name"],
                value=metric_data["value"],
                metric_type=MetricType(metric_data.get("type", "gauge")),
                unit=metric_data.get("unit", ""),
                tags=metric_data.get("tags", {}),
                dimensions=metric_data.get("dimensions", {})
            )
            metric_ids.append(metric_id)
        
        return metric_ids
    
    async def get_metrics(self, name: str, start_time: datetime, end_time: datetime, 
                         tags: Dict[str, str] = None) -> List[Metric]:
        """Get metrics for a specific time range"""
        filtered_metrics = []
        
        for metric in self.metrics:
            # Check name
            if metric.name != name:
                continue
            
            # Check time range
            if not (start_time <= metric.timestamp <= end_time):
                continue
            
            # Check tags
            if tags:
                if not all(metric.tags.get(k) == v for k, v in tags.items()):
                    continue
            
            filtered_metrics.append(metric)
        
        return filtered_metrics
    
    async def aggregate_metrics(self, name: str, start_time: datetime, end_time: datetime,
                              aggregation: str = "avg", interval_seconds: int = 3600) -> List[Dict[str, Any]]:
        """Aggregate metrics over time intervals"""
        metrics = await self.get_metrics(name, start_time, end_time)
        
        if not metrics:
            return []
        
        # Group metrics by time intervals
        intervals = {}
        for metric in metrics:
            interval_start = datetime.fromtimestamp(
                (metric.timestamp.timestamp() // interval_seconds) * interval_seconds,
                tz=timezone.utc
            )
            
            if interval_start not in intervals:
                intervals[interval_start] = []
            intervals[interval_start].append(metric.value)
        
        # Aggregate each interval
        aggregated = []
        for interval_start, values in sorted(intervals.items()):
            if aggregation == "avg":
                agg_value = statistics.mean(values)
            elif aggregation == "sum":
                agg_value = sum(values)
            elif aggregation == "min":
                agg_value = min(values)
            elif aggregation == "max":
                agg_value = max(values)
            elif aggregation == "count":
                agg_value = len(values)
            else:
                agg_value = statistics.mean(values)
            
            aggregated.append({
                "timestamp": interval_start.isoformat(),
                "value": agg_value,
                "count": len(values)
            })
        
        return aggregated
    
    async def cleanup_old_metrics(self) -> int:
        """Clean up old metrics beyond retention period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        
        initial_count = len(self.metrics)
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        cleaned_count = initial_count - len(self.metrics)
        logger.info(f"Cleaned up {cleaned_count} old metrics")
        
        return cleaned_count
    
    async def _store_metric_in_db(self, metric: Metric) -> None:
        """Store metric in database"""
        # Implementation would depend on database connection
        pass


class AnalyticsEngine:
    """
    Comprehensive analytics engine for system analysis and optimization
    """
    
    def __init__(self, organization_id: str, metrics_collector: MetricsCollector, database_connection=None):
        self.organization_id = organization_id
        self.metrics_collector = metrics_collector
        self.db = database_connection
        
        # Analysis storage
        self.analysis_results: Dict[str, AnalysisResult] = {}
        self.detected_patterns: Dict[str, Pattern] = {}
        
        # Configuration
        self.analysis_intervals = {
            "performance": 3600,  # 1 hour
            "quality": 86400,     # 1 day
            "reliability": 3600,  # 1 hour
            "trend": 86400        # 1 day
        }
        
        # Thresholds
        self.performance_thresholds = {
            "response_time_ms": {"good": 500, "warning": 1000, "critical": 2000},
            "error_rate": {"good": 1, "warning": 5, "critical": 10},
            "throughput": {"good": 100, "warning": 50, "critical": 20}
        }
        
        # Pattern detection
        self.pattern_detectors = {
            "performance_degradation": self._detect_performance_degradation,
            "error_spike": self._detect_error_spike,
            "usage_pattern": self._detect_usage_pattern,
            "seasonal_trend": self._detect_seasonal_trend
        }
    
    async def analyze_performance(self, target_type: str, target_id: str, 
                                period_days: int = 7) -> AnalysisResult:
        """Analyze performance metrics for a target"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=period_days)
        
        analysis = AnalysisResult(
            analysis_type=AnalysisType.PERFORMANCE,
            target_type=target_type,
            target_id=target_id,
            period_start=start_time,
            period_end=end_time
        )
        
        # Collect performance metrics
        response_times = await self.metrics_collector.get_metrics(
            f"{target_type}_response_time", start_time, end_time,
            tags={"target_id": target_id}
        )
        
        error_rates = await self.metrics_collector.get_metrics(
            f"{target_type}_error_rate", start_time, end_time,
            tags={"target_id": target_id}
        )
        
        # Calculate performance score
        score = await self._calculate_performance_score(response_times, error_rates)
        analysis.score = score
        
        # Generate insights
        if response_times:
            avg_response_time = statistics.mean([m.value for m in response_times])
            analysis.metrics["avg_response_time_ms"] = avg_response_time
            
            if avg_response_time > self.performance_thresholds["response_time_ms"]["critical"]:
                analysis.add_insight(f"Critical: Average response time ({avg_response_time:.1f}ms) exceeds critical threshold")
                analysis.add_recommendation(
                    "Optimize Response Time",
                    "Response time is critically high. Consider performance optimization.",
                    priority="high",
                    impact="high"
                )
            elif avg_response_time > self.performance_thresholds["response_time_ms"]["warning"]:
                analysis.add_insight(f"Warning: Average response time ({avg_response_time:.1f}ms) exceeds warning threshold")
        
        if error_rates:
            avg_error_rate = statistics.mean([m.value for m in error_rates])
            analysis.metrics["avg_error_rate"] = avg_error_rate
            
            if avg_error_rate > self.performance_thresholds["error_rate"]["critical"]:
                analysis.add_insight(f"Critical: Error rate ({avg_error_rate:.1f}%) is critically high")
                analysis.add_recommendation(
                    "Reduce Error Rate",
                    "Error rate is critically high. Investigate and fix underlying issues.",
                    priority="critical",
                    impact="high"
                )
        
        # Detect trends
        trend = await self._analyze_trend(response_times, "response_time")
        analysis.trend_direction = trend["direction"]
        analysis.trend_confidence = trend["confidence"]
        
        # Store analysis
        self.analysis_results[analysis.id] = analysis
        
        return analysis
    
    async def analyze_quality(self, target_type: str, target_id: str, 
                            period_days: int = 30) -> AnalysisResult:
        """Analyze quality metrics for a target"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=period_days)
        
        analysis = AnalysisResult(
            analysis_type=AnalysisType.QUALITY,
            target_type=target_type,
            target_id=target_id,
            period_start=start_time,
            period_end=end_time
        )
        
        # Collect quality metrics
        success_rates = await self.metrics_collector.get_metrics(
            f"{target_type}_success_rate", start_time, end_time,
            tags={"target_id": target_id}
        )
        
        test_coverage = await self.metrics_collector.get_metrics(
            f"{target_type}_test_coverage", start_time, end_time,
            tags={"target_id": target_id}
        )
        
        # Calculate quality score
        score = await self._calculate_quality_score(success_rates, test_coverage)
        analysis.score = score
        
        # Generate insights
        if success_rates:
            avg_success_rate = statistics.mean([m.value for m in success_rates])
            analysis.metrics["avg_success_rate"] = avg_success_rate
            
            if avg_success_rate < 90:
                analysis.add_insight(f"Success rate ({avg_success_rate:.1f}%) is below target (90%)")
                analysis.add_recommendation(
                    "Improve Success Rate",
                    "Success rate is below target. Review and fix failing processes.",
                    priority="medium",
                    impact="medium"
                )
        
        if test_coverage:
            latest_coverage = test_coverage[-1].value if test_coverage else 0
            analysis.metrics["test_coverage"] = latest_coverage
            
            if latest_coverage < 80:
                analysis.add_insight(f"Test coverage ({latest_coverage:.1f}%) is below recommended threshold (80%)")
                analysis.add_recommendation(
                    "Increase Test Coverage",
                    "Test coverage is below recommended threshold. Add more tests.",
                    priority="medium",
                    impact="medium"
                )
        
        self.analysis_results[analysis.id] = analysis
        return analysis
    
    async def detect_patterns(self, period_days: int = 30) -> List[Pattern]:
        """Detect patterns in system behavior"""
        detected_patterns = []
        
        for pattern_type, detector in self.pattern_detectors.items():
            try:
                patterns = await detector(period_days)
                detected_patterns.extend(patterns)
            except Exception as e:
                logger.error(f"Error detecting {pattern_type} patterns: {e}")
        
        # Store detected patterns
        for pattern in detected_patterns:
            self.detected_patterns[pattern.id] = pattern
        
        logger.info(f"Detected {len(detected_patterns)} patterns")
        return detected_patterns
    
    async def get_optimization_recommendations(self, target_type: str = None, 
                                            target_id: str = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on analysis"""
        recommendations = []
        
        # Filter analyses
        analyses = list(self.analysis_results.values())
        if target_type:
            analyses = [a for a in analyses if a.target_type == target_type]
        if target_id:
            analyses = [a for a in analyses if a.target_id == target_id]
        
        # Collect recommendations from analyses
        for analysis in analyses:
            for rec in analysis.recommendations:
                rec["source"] = f"{analysis.analysis_type.value}_analysis"
                rec["target_type"] = analysis.target_type
                rec["target_id"] = analysis.target_id
                rec["analysis_score"] = analysis.score
                recommendations.append(rec)
        
        # Add pattern-based recommendations
        for pattern in self.detected_patterns.values():
            if pattern.is_active and pattern.impact_score > 50:
                recommendations.append({
                    "id": str(uuid.uuid4()),
                    "title": f"Address {pattern.name}",
                    "description": f"Pattern detected: {pattern.description}",
                    "priority": "medium" if pattern.impact_score < 75 else "high",
                    "impact": "medium" if pattern.impact_score < 75 else "high",
                    "source": "pattern_detection",
                    "pattern_id": pattern.id,
                    "confidence": pattern.confidence
                })
        
        # Sort by priority and impact
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        recommendations.sort(
            key=lambda r: (priority_order.get(r.get("priority", "low"), 1), 
                          priority_order.get(r.get("impact", "low"), 1)),
            reverse=True
        )
        
        return recommendations
    
    async def get_system_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        recent_analyses = [
            a for a in self.analysis_results.values()
            if a.analyzed_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ]
        
        if not recent_analyses:
            return {"overall_score": 100, "component_scores": {}, "timestamp": datetime.now(timezone.utc).isoformat()}
        
        # Calculate component scores
        component_scores = {}
        analysis_types = {}
        
        for analysis in recent_analyses:
            analysis_type = analysis.analysis_type.value
            if analysis_type not in analysis_types:
                analysis_types[analysis_type] = []
            analysis_types[analysis_type].append(analysis.score)
        
        # Average scores by analysis type
        for analysis_type, scores in analysis_types.items():
            component_scores[analysis_type] = statistics.mean(scores)
        
        # Calculate overall score (weighted average)
        weights = {"performance": 0.3, "quality": 0.25, "reliability": 0.25, "efficiency": 0.2}
        overall_score = 0
        total_weight = 0
        
        for analysis_type, score in component_scores.items():
            weight = weights.get(analysis_type, 0.1)
            overall_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        else:
            overall_score = 100
        
        return {
            "overall_score": round(overall_score, 1),
            "component_scores": component_scores,
            "active_patterns": len([p for p in self.detected_patterns.values() if p.is_active]),
            "recommendations_count": len(await self.get_optimization_recommendations()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _calculate_performance_score(self, response_times: List[Metric], 
                                         error_rates: List[Metric]) -> float:
        """Calculate performance score based on metrics"""
        score = 100.0
        
        # Response time score
        if response_times:
            avg_response_time = statistics.mean([m.value for m in response_times])
            thresholds = self.performance_thresholds["response_time_ms"]
            
            if avg_response_time > thresholds["critical"]:
                score -= 40
            elif avg_response_time > thresholds["warning"]:
                score -= 20
            elif avg_response_time > thresholds["good"]:
                score -= 10
        
        # Error rate score
        if error_rates:
            avg_error_rate = statistics.mean([m.value for m in error_rates])
            thresholds = self.performance_thresholds["error_rate"]
            
            if avg_error_rate > thresholds["critical"]:
                score -= 40
            elif avg_error_rate > thresholds["warning"]:
                score -= 20
            elif avg_error_rate > thresholds["good"]:
                score -= 10
        
        return max(0, score)
    
    async def _calculate_quality_score(self, success_rates: List[Metric], 
                                     test_coverage: List[Metric]) -> float:
        """Calculate quality score based on metrics"""
        score = 100.0
        
        # Success rate score
        if success_rates:
            avg_success_rate = statistics.mean([m.value for m in success_rates])
            if avg_success_rate < 80:
                score -= 40
            elif avg_success_rate < 90:
                score -= 20
            elif avg_success_rate < 95:
                score -= 10
        
        # Test coverage score
        if test_coverage:
            latest_coverage = test_coverage[-1].value
            if latest_coverage < 60:
                score -= 30
            elif latest_coverage < 80:
                score -= 15
            elif latest_coverage < 90:
                score -= 5
        
        return max(0, score)
    
    async def _analyze_trend(self, metrics: List[Metric], metric_name: str) -> Dict[str, Any]:
        """Analyze trend in metrics"""
        if len(metrics) < 2:
            return {"direction": "stable", "confidence": 0.0}
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        values = [m.value for m in sorted_metrics]
        
        # Simple trend analysis (can be enhanced with more sophisticated methods)
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
        
        if abs(change_percent) < 5:
            direction = "stable"
            confidence = 0.7
        elif change_percent > 0:
            direction = "improving" if metric_name in ["success_rate", "throughput"] else "declining"
            confidence = min(0.9, abs(change_percent) / 20)
        else:
            direction = "declining" if metric_name in ["success_rate", "throughput"] else "improving"
            confidence = min(0.9, abs(change_percent) / 20)
        
        return {"direction": direction, "confidence": confidence, "change_percent": change_percent}
    
    async def _detect_performance_degradation(self, period_days: int) -> List[Pattern]:
        """Detect performance degradation patterns"""
        patterns = []
        
        # Mock pattern detection (in real implementation, would use ML algorithms)
        pattern = Pattern(
            pattern_type="performance_degradation",
            name="Gradual Response Time Increase",
            description="Response times have been gradually increasing over the past week",
            frequency="daily",
            confidence=0.8,
            significance=0.7,
            impact_score=75,
            pattern_data={"trend": "increasing", "rate": "gradual"}
        )
        patterns.append(pattern)
        
        return patterns
    
    async def _detect_error_spike(self, period_days: int) -> List[Pattern]:
        """Detect error spike patterns"""
        patterns = []
        
        # Mock pattern detection
        pattern = Pattern(
            pattern_type="error_spike",
            name="Weekly Error Spike",
            description="Error rates spike every Monday morning",
            frequency="weekly",
            confidence=0.9,
            significance=0.8,
            impact_score=60,
            pattern_data={"day": "monday", "time": "morning"}
        )
        patterns.append(pattern)
        
        return patterns
    
    async def _detect_usage_pattern(self, period_days: int) -> List[Pattern]:
        """Detect usage patterns"""
        patterns = []
        
        # Mock pattern detection
        pattern = Pattern(
            pattern_type="usage_pattern",
            name="Business Hours Peak",
            description="System usage peaks during business hours (9 AM - 5 PM)",
            frequency="daily",
            confidence=0.95,
            significance=0.9,
            impact_score=40,
            pattern_data={"peak_hours": "9-17", "timezone": "UTC"}
        )
        patterns.append(pattern)
        
        return patterns
    
    async def _detect_seasonal_trend(self, period_days: int) -> List[Pattern]:
        """Detect seasonal trends"""
        patterns = []
        
        # Mock pattern detection
        if period_days >= 30:
            pattern = Pattern(
                pattern_type="seasonal_trend",
                name="Month-End Processing Load",
                description="System load increases significantly during month-end processing",
                frequency="monthly",
                confidence=0.85,
                significance=0.8,
                impact_score=55,
                pattern_data={"period": "month_end", "duration": "2-3 days"}
            )
            patterns.append(pattern)
        
        return patterns


# Utility functions
def create_metric_from_dict(data: Dict[str, Any]) -> Metric:
    """Create a Metric object from dictionary data"""
    metric = Metric()
    for key, value in data.items():
        if key == "metric_type" and isinstance(value, str):
            metric.metric_type = MetricType(value)
        elif hasattr(metric, key):
            setattr(metric, key, value)
    return metric


def create_analysis_from_dict(data: Dict[str, Any]) -> AnalysisResult:
    """Create an AnalysisResult object from dictionary data"""
    analysis = AnalysisResult()
    for key, value in data.items():
        if key == "analysis_type" and isinstance(value, str):
            analysis.analysis_type = AnalysisType(value)
        elif hasattr(analysis, key):
            setattr(analysis, key, value)
    return analysis

