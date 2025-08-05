"""
Performance Monitor for OpenEvolve Integration

This module provides comprehensive performance monitoring and analytics
for the OpenEvolve integration, tracking metrics, trends, and optimization opportunities.
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from graph_sitter.shared.logging import get_logger

from .database_manager import OpenEvolveDatabase

logger = get_logger(__name__)


class MetricCollector:
    """
    Collects and aggregates performance metrics in real-time.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize the metric collector.
        
        Args:
            window_size: Size of the sliding window for metric aggregation
        """
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.timestamps = defaultdict(lambda: deque(maxlen=window_size))
        self.aggregated_metrics = {}
    
    def record_metric(self, metric_name: str, value: float, timestamp: float = None) -> None:
        """
        Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Timestamp (current time if None)
        """
        timestamp = timestamp or time.time()
        
        self.metrics[metric_name].append(value)
        self.timestamps[metric_name].append(timestamp)
        
        # Update aggregated metrics
        self._update_aggregated_metrics(metric_name)
    
    def get_metric_stats(self, metric_name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Dictionary with metric statistics
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        
        values = list(self.metrics[metric_name])
        
        return {
            "count": len(values),
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99)
        }
    
    def get_trend(self, metric_name: str, window: int = 20) -> Dict[str, Any]:
        """
        Get trend information for a metric.
        
        Args:
            metric_name: Name of the metric
            window: Window size for trend calculation
            
        Returns:
            Trend information
        """
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < window:
            return {"trend": "insufficient_data", "confidence": 0.0}
        
        values = list(self.metrics[metric_name])[-window:]
        timestamps = list(self.timestamps[metric_name])[-window:]
        
        # Calculate linear trend
        if len(values) >= 2:
            x = np.array(timestamps)
            y = np.array(values)
            
            # Normalize timestamps
            x = x - x[0]
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            # Calculate correlation coefficient for confidence
            correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
            confidence = abs(correlation)
            
            # Determine trend direction
            if abs(slope) < 0.001:  # Threshold for stable
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            return {
                "trend": trend,
                "slope": slope,
                "confidence": confidence,
                "window_size": len(values)
            }
        
        return {"trend": "insufficient_data", "confidence": 0.0}
    
    def _update_aggregated_metrics(self, metric_name: str) -> None:
        """Update aggregated metrics for a specific metric."""
        stats = self.get_metric_stats(metric_name)
        if stats:
            self.aggregated_metrics[metric_name] = stats


class PerformanceAnalyzer:
    """
    Analyzes performance data to identify bottlenecks and optimization opportunities.
    """
    
    def __init__(self):
        self.analysis_cache = {}
        self.bottleneck_thresholds = {
            "execution_time": 30.0,  # seconds
            "memory_usage": 1000.0,  # MB
            "cpu_usage": 80.0,       # percentage
            "error_rate": 0.1        # 10%
        }
    
    def analyze_session_performance(
        self,
        session_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze performance for an entire session.
        
        Args:
            session_data: List of session steps with performance data
            
        Returns:
            Performance analysis results
        """
        if not session_data:
            return {"status": "no_data"}
        
        # Extract performance metrics
        execution_times = [step.get("execution_time", 0) for step in session_data]
        success_rates = self._calculate_success_rates(session_data)
        error_patterns = self._analyze_error_patterns(session_data)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(session_data)
        
        # Calculate performance trends
        trends = self._calculate_performance_trends(session_data)
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(
            session_data, bottlenecks, trends
        )
        
        analysis = {
            "session_summary": {
                "total_steps": len(session_data),
                "avg_execution_time": np.mean(execution_times) if execution_times else 0,
                "total_execution_time": sum(execution_times),
                "success_rate": success_rates.get("overall", 0),
                "error_count": len(error_patterns)
            },
            "bottlenecks": bottlenecks,
            "trends": trends,
            "error_patterns": error_patterns,
            "recommendations": recommendations,
            "timestamp": time.time()
        }
        
        return analysis
    
    def _calculate_success_rates(self, session_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate success rates by different dimensions."""
        success_rates = {}
        
        # Overall success rate
        total_steps = len(session_data)
        successful_steps = sum(1 for step in session_data if step.get("success", False))
        success_rates["overall"] = successful_steps / total_steps if total_steps > 0 else 0
        
        # Success rate by step type
        by_step_type = defaultdict(lambda: {"total": 0, "successful": 0})
        for step in session_data:
            step_type = step.get("step_type", "unknown")
            by_step_type[step_type]["total"] += 1
            if step.get("success", False):
                by_step_type[step_type]["successful"] += 1
        
        success_rates["by_step_type"] = {}
        for step_type, counts in by_step_type.items():
            success_rates["by_step_type"][step_type] = (
                counts["successful"] / counts["total"] if counts["total"] > 0 else 0
            )
        
        # Success rate by file
        by_file = defaultdict(lambda: {"total": 0, "successful": 0})
        for step in session_data:
            file_path = step.get("file_path", "unknown")
            by_file[file_path]["total"] += 1
            if step.get("success", False):
                by_file[file_path]["successful"] += 1
        
        success_rates["by_file"] = {}
        for file_path, counts in by_file.items():
            success_rates["by_file"][file_path] = (
                counts["successful"] / counts["total"] if counts["total"] > 0 else 0
            )
        
        return success_rates
    
    def _analyze_error_patterns(self, session_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze error patterns in session data."""
        error_patterns = []
        error_counts = defaultdict(int)
        
        for step in session_data:
            errors = step.get("errors", [])
            for error in errors:
                error_message = error.get("error", "unknown_error")
                error_counts[error_message] += 1
        
        # Find common errors
        for error_message, count in error_counts.items():
            if count >= 2:  # Appears at least twice
                error_patterns.append({
                    "error_message": error_message,
                    "frequency": count,
                    "percentage": count / len(session_data) * 100
                })
        
        # Sort by frequency
        error_patterns.sort(key=lambda x: x["frequency"], reverse=True)
        
        return error_patterns
    
    def _identify_bottlenecks(self, session_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Execution time bottlenecks
        execution_times = [step.get("execution_time", 0) for step in session_data]
        if execution_times:
            avg_time = np.mean(execution_times)
            max_time = np.max(execution_times)
            
            if max_time > self.bottleneck_thresholds["execution_time"]:
                bottlenecks.append({
                    "type": "execution_time",
                    "severity": "high" if max_time > avg_time * 3 else "medium",
                    "description": f"Maximum execution time ({max_time:.2f}s) exceeds threshold",
                    "affected_steps": sum(1 for t in execution_times if t > self.bottleneck_thresholds["execution_time"]),
                    "recommendation": "Optimize slow operations or increase timeout limits"
                })
        
        # Error rate bottlenecks
        error_count = sum(1 for step in session_data if step.get("errors"))
        error_rate = error_count / len(session_data) if session_data else 0
        
        if error_rate > self.bottleneck_thresholds["error_rate"]:
            bottlenecks.append({
                "type": "error_rate",
                "severity": "high" if error_rate > 0.2 else "medium",
                "description": f"Error rate ({error_rate:.1%}) exceeds threshold",
                "affected_steps": error_count,
                "recommendation": "Investigate and fix common error patterns"
            })
        
        # Step type bottlenecks
        step_type_times = defaultdict(list)
        for step in session_data:
            step_type = step.get("step_type", "unknown")
            execution_time = step.get("execution_time", 0)
            step_type_times[step_type].append(execution_time)
        
        for step_type, times in step_type_times.items():
            if times:
                avg_time = np.mean(times)
                if avg_time > self.bottleneck_thresholds["execution_time"] / 2:
                    bottlenecks.append({
                        "type": "step_type_performance",
                        "severity": "medium",
                        "description": f"Step type '{step_type}' has high average execution time ({avg_time:.2f}s)",
                        "affected_steps": len(times),
                        "recommendation": f"Optimize '{step_type}' operations"
                    })
        
        return bottlenecks
    
    def _calculate_performance_trends(self, session_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance trends over the session."""
        trends = {}
        
        if len(session_data) < 5:
            return {"status": "insufficient_data"}
        
        # Sort by timestamp
        sorted_data = sorted(session_data, key=lambda x: x.get("start_time", 0))
        
        # Execution time trend
        execution_times = [step.get("execution_time", 0) for step in sorted_data]
        if execution_times:
            trends["execution_time"] = self._calculate_trend(execution_times)
        
        # Success rate trend (using sliding window)
        window_size = min(10, len(sorted_data) // 2)
        success_rates = []
        for i in range(window_size, len(sorted_data)):
            window = sorted_data[i-window_size:i]
            success_count = sum(1 for step in window if step.get("success", False))
            success_rate = success_count / len(window)
            success_rates.append(success_rate)
        
        if success_rates:
            trends["success_rate"] = self._calculate_trend(success_rates)
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend for a series of values."""
        if len(values) < 3:
            return {"trend": "insufficient_data", "confidence": 0.0}
        
        # Calculate linear trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # Calculate correlation for confidence
        correlation = np.corrcoef(x, values)[0, 1] if len(values) > 1 else 0
        confidence = abs(correlation)
        
        # Determine trend direction
        if abs(slope) < 0.001:
            trend = "stable"
        elif slope > 0:
            trend = "improving"
        else:
            trend = "degrading"
        
        return {
            "trend": trend,
            "slope": slope,
            "confidence": confidence,
            "data_points": len(values)
        }
    
    def _generate_optimization_recommendations(
        self,
        session_data: List[Dict[str, Any]],
        bottlenecks: List[Dict[str, Any]],
        trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Recommendations based on bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "execution_time":
                recommendations.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "Optimize Execution Time",
                    "description": "Several steps are taking longer than expected to execute",
                    "action": "Profile slow operations and optimize algorithms or increase resources",
                    "expected_impact": "20-50% reduction in execution time"
                })
            
            elif bottleneck["type"] == "error_rate":
                recommendations.append({
                    "type": "reliability",
                    "priority": "high",
                    "title": "Reduce Error Rate",
                    "description": "High error rate is impacting overall success",
                    "action": "Implement better error handling and input validation",
                    "expected_impact": "Improved success rate and stability"
                })
        
        # Recommendations based on trends
        execution_trend = trends.get("execution_time", {})
        if execution_trend.get("trend") == "degrading" and execution_trend.get("confidence", 0) > 0.7:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "title": "Address Performance Degradation",
                "description": "Execution times are increasing over the session",
                "action": "Investigate memory leaks or resource accumulation",
                "expected_impact": "Stabilize performance over long sessions"
            })
        
        success_trend = trends.get("success_rate", {})
        if success_trend.get("trend") == "degrading" and success_trend.get("confidence", 0) > 0.7:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "title": "Improve Success Rate Stability",
                "description": "Success rate is declining over the session",
                "action": "Review and improve error recovery mechanisms",
                "expected_impact": "More consistent success rates"
            })
        
        # General recommendations based on session characteristics
        avg_execution_time = np.mean([step.get("execution_time", 0) for step in session_data])
        if avg_execution_time > 15:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "title": "Consider Parallel Processing",
                "description": "Average execution time is high, parallel processing might help",
                "action": "Implement parallel execution for independent operations",
                "expected_impact": "Significant reduction in total session time"
            })
        
        return recommendations


class PerformanceMonitor:
    """
    Main performance monitoring system for OpenEvolve integration.
    """
    
    def __init__(self, database: OpenEvolveDatabase):
        """
        Initialize the performance monitor.
        
        Args:
            database: Database manager for storing performance data
        """
        self.database = database
        self.metric_collector = MetricCollector()
        self.analyzer = PerformanceAnalyzer()
        self.active_sessions = {}
        self.monitoring_enabled = True
    
    def start_monitoring(self, session_id: str) -> None:
        """Start monitoring for a session."""
        self.active_sessions[session_id] = {
            "start_time": time.time(),
            "metrics": MetricCollector(),
            "step_count": 0,
            "error_count": 0
        }
        
        logger.info(f"Started performance monitoring for session {session_id}")
    
    async def record_evolution_metrics(
        self,
        session_id: str,
        step_id: str,
        execution_time: float,
        result: Dict[str, Any]
    ) -> None:
        """
        Record metrics for an evolution step.
        
        Args:
            session_id: Session ID
            step_id: Step ID
            execution_time: Execution time in seconds
            result: Evolution result with metrics
        """
        if not self.monitoring_enabled:
            return
        
        timestamp = time.time()
        
        # Record basic metrics
        self.metric_collector.record_metric("execution_time", execution_time, timestamp)
        
        # Record session-specific metrics
        if session_id in self.active_sessions:
            session_metrics = self.active_sessions[session_id]["metrics"]
            session_metrics.record_metric("execution_time", execution_time, timestamp)
            self.active_sessions[session_id]["step_count"] += 1
        
        # Extract and record evolution-specific metrics
        evolution_metrics = result.get("evolution_metrics", {})
        for metric_name, metric_value in evolution_metrics.items():
            if isinstance(metric_value, (int, float)):
                self.metric_collector.record_metric(f"evolution_{metric_name}", metric_value, timestamp)
                
                if session_id in self.active_sessions:
                    session_metrics = self.active_sessions[session_id]["metrics"]
                    session_metrics.record_metric(f"evolution_{metric_name}", metric_value, timestamp)
        
        # Store in database
        await self.database.update_step_metrics(step_id, {
            "execution_time": execution_time,
            "timestamp": timestamp,
            **evolution_metrics
        })
        
        logger.debug(f"Recorded evolution metrics for step {step_id}")
    
    async def record_error(self, session_id: str, step_id: str, error: str) -> None:
        """Record an error occurrence."""
        if not self.monitoring_enabled:
            return
        
        timestamp = time.time()
        
        # Record error metrics
        self.metric_collector.record_metric("error_rate", 1.0, timestamp)
        
        if session_id in self.active_sessions:
            session_metrics = self.active_sessions[session_id]["metrics"]
            session_metrics.record_metric("error_rate", 1.0, timestamp)
            self.active_sessions[session_id]["error_count"] += 1
        
        logger.debug(f"Recorded error for step {step_id}")
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session analytics
        """
        # Get session data from database
        session_data = await self.database.get_session_data(session_id)
        
        # Perform performance analysis
        performance_analysis = self.analyzer.analyze_session_performance(session_data)
        
        # Get real-time metrics if session is active
        real_time_metrics = {}
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            session_metrics = session_info["metrics"]
            
            real_time_metrics = {
                "current_step_count": session_info["step_count"],
                "current_error_count": session_info["error_count"],
                "session_duration": time.time() - session_info["start_time"],
                "avg_execution_time": session_metrics.get_metric_stats("execution_time").get("mean", 0),
                "execution_time_trend": session_metrics.get_trend("execution_time")
            }
        
        # Get database analytics
        db_analytics = await self.database.get_performance_analytics(session_id)
        
        analytics = {
            "session_id": session_id,
            "performance_analysis": performance_analysis,
            "real_time_metrics": real_time_metrics,
            "database_analytics": db_analytics,
            "timestamp": time.time()
        }
        
        return analytics
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global performance metrics across all sessions."""
        global_metrics = {}
        
        # Get aggregated metrics from collector
        for metric_name in self.metric_collector.metrics:
            stats = self.metric_collector.get_metric_stats(metric_name)
            trend = self.metric_collector.get_trend(metric_name)
            
            global_metrics[metric_name] = {
                "stats": stats,
                "trend": trend
            }
        
        # Add system-wide statistics
        global_metrics["system"] = {
            "active_sessions": len(self.active_sessions),
            "total_metrics_collected": sum(
                len(metrics) for metrics in self.metric_collector.metrics.values()
            ),
            "monitoring_enabled": self.monitoring_enabled
        }
        
        return global_metrics
    
    def stop_monitoring(self, session_id: str) -> None:
        """Stop monitoring for a session."""
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            session_info["end_time"] = time.time()
            session_info["total_duration"] = session_info["end_time"] - session_info["start_time"]
            
            # Keep session data for a while for analysis
            # Could implement cleanup later
            
            logger.info(f"Stopped performance monitoring for session {session_id}")
    
    def enable_monitoring(self) -> None:
        """Enable performance monitoring."""
        self.monitoring_enabled = True
        logger.info("Performance monitoring enabled")
    
    def disable_monitoring(self) -> None:
        """Disable performance monitoring."""
        self.monitoring_enabled = False
        logger.info("Performance monitoring disabled")
    
    async def generate_performance_report(
        self,
        session_id: Optional[str] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Args:
            session_id: Specific session to report on (all sessions if None)
            include_recommendations: Whether to include optimization recommendations
            
        Returns:
            Performance report
        """
        report = {
            "report_type": "session" if session_id else "global",
            "timestamp": time.time(),
            "monitoring_enabled": self.monitoring_enabled
        }
        
        if session_id:
            # Session-specific report
            analytics = await self.get_session_analytics(session_id)
            report.update(analytics)
        else:
            # Global report
            global_metrics = self.get_global_metrics()
            report["global_metrics"] = global_metrics
            
            # Get summary statistics across all active sessions
            session_summaries = []
            for sid in self.active_sessions:
                try:
                    session_analytics = await self.get_session_analytics(sid)
                    session_summaries.append({
                        "session_id": sid,
                        "summary": session_analytics.get("performance_analysis", {}).get("session_summary", {})
                    })
                except Exception as e:
                    logger.warning(f"Failed to get analytics for session {sid}: {e}")
            
            report["session_summaries"] = session_summaries
        
        if include_recommendations and session_id:
            # Add specific recommendations for the session
            session_data = await self.database.get_session_data(session_id)
            analysis = self.analyzer.analyze_session_performance(session_data)
            report["recommendations"] = analysis.get("recommendations", [])
        
        return report

