"""
Analysis components for the diagnosis engine.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from ..models.events import ErrorEvent, HealthMetric
from ..models.enums import ErrorType, ErrorSeverity


class RootCauseAnalyzer:
    """Analyzes errors to determine root causes."""
    
    def __init__(self):
        """Initialize the root cause analyzer."""
        self.logger = logging.getLogger(__name__)
        
        # Root cause patterns for different error types
        self.cause_patterns = {
            ErrorType.MEMORY_LEAK: {
                "patterns": [
                    {"condition": "memory_trend_increasing", "cause": "Memory leak in application code"},
                    {"condition": "memory_spike_sudden", "cause": "Large object allocation or memory bomb"},
                    {"condition": "memory_gradual_increase", "cause": "Gradual memory leak or cache growth"},
                ],
                "default": "Memory usage exceeded threshold"
            },
            ErrorType.CPU_SPIKE: {
                "patterns": [
                    {"condition": "cpu_spike_sudden", "cause": "Infinite loop or CPU-intensive operation"},
                    {"condition": "cpu_high_sustained", "cause": "High load or inefficient algorithm"},
                    {"condition": "cpu_periodic_spikes", "cause": "Scheduled task or batch processing"},
                ],
                "default": "CPU usage exceeded threshold"
            },
            ErrorType.NETWORK_TIMEOUT: {
                "patterns": [
                    {"condition": "network_latency_high", "cause": "Network congestion or slow external service"},
                    {"condition": "connection_refused", "cause": "Service unavailable or firewall blocking"},
                    {"condition": "dns_resolution_slow", "cause": "DNS server issues or configuration"},
                ],
                "default": "Network communication timeout"
            },
            ErrorType.DATABASE_CONNECTION: {
                "patterns": [
                    {"condition": "db_pool_exhausted", "cause": "Database connection pool exhausted"},
                    {"condition": "db_server_down", "cause": "Database server unavailable"},
                    {"condition": "db_query_timeout", "cause": "Long-running query or database lock"},
                ],
                "default": "Database connection failure"
            },
            ErrorType.DEPLOYMENT_FAILURE: {
                "patterns": [
                    {"condition": "config_invalid", "cause": "Invalid configuration or missing environment variables"},
                    {"condition": "dependency_missing", "cause": "Missing dependencies or version conflicts"},
                    {"condition": "resource_insufficient", "cause": "Insufficient resources for deployment"},
                ],
                "default": "Deployment process failure"
            },
        }
    
    async def analyze(self, error_event: ErrorEvent, 
                     recent_metrics: Dict[str, List[HealthMetric]]) -> Dict[str, Any]:
        """
        Analyze error event to determine root cause.
        
        Args:
            error_event: The error event to analyze
            recent_metrics: Recent system metrics
            
        Returns:
            Root cause analysis result
        """
        try:
            error_type = error_event.error_type
            
            # Get patterns for this error type
            type_patterns = self.cause_patterns.get(error_type, {})
            patterns = type_patterns.get("patterns", [])
            default_cause = type_patterns.get("default", "Unknown root cause")
            
            # Analyze metrics to determine specific conditions
            conditions = self._analyze_conditions(error_event, recent_metrics)
            
            # Find matching pattern
            for pattern in patterns:
                condition = pattern["condition"]
                if condition in conditions and conditions[condition]:
                    return {
                        "description": pattern["cause"],
                        "confidence": conditions[condition],
                        "evidence": conditions.get(f"{condition}_evidence", []),
                        "conditions_met": [condition],
                    }
            
            # No specific pattern matched, use default
            return {
                "description": default_cause,
                "confidence": 0.5,
                "evidence": [f"Error type: {error_type.value}"],
                "conditions_met": [],
            }
            
        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
            return {
                "description": "Analysis failed",
                "confidence": 0.1,
                "evidence": [f"Analysis error: {str(e)}"],
                "conditions_met": [],
            }
    
    def _analyze_conditions(self, error_event: ErrorEvent, 
                          recent_metrics: Dict[str, List[HealthMetric]]) -> Dict[str, Any]:
        """Analyze conditions based on error event and metrics."""
        conditions = {}
        
        try:
            # Memory-related conditions
            if "memory" in recent_metrics:
                memory_metrics = recent_metrics["memory"]
                if len(memory_metrics) >= 5:
                    recent_values = [m.current_value for m in memory_metrics[-10:]]
                    
                    # Check for increasing trend
                    if len(recent_values) >= 5:
                        early_avg = sum(recent_values[:3]) / 3
                        late_avg = sum(recent_values[-3:]) / 3
                        
                        if late_avg > early_avg + 10:  # 10% increase
                            conditions["memory_trend_increasing"] = 0.8
                            conditions["memory_trend_increasing_evidence"] = [
                                f"Memory increased from {early_avg:.1f}% to {late_avg:.1f}%"
                            ]
                    
                    # Check for sudden spike
                    if len(recent_values) >= 2:
                        if recent_values[-1] - recent_values[-2] > 20:  # 20% sudden increase
                            conditions["memory_spike_sudden"] = 0.9
                            conditions["memory_spike_sudden_evidence"] = [
                                f"Memory spiked from {recent_values[-2]:.1f}% to {recent_values[-1]:.1f}%"
                            ]
            
            # CPU-related conditions
            if "cpu" in recent_metrics:
                cpu_metrics = recent_metrics["cpu"]
                if len(cpu_metrics) >= 5:
                    recent_values = [m.current_value for m in cpu_metrics[-10:]]
                    
                    # Check for sudden spike
                    if len(recent_values) >= 2:
                        if recent_values[-1] - recent_values[-2] > 30:  # 30% sudden increase
                            conditions["cpu_spike_sudden"] = 0.9
                            conditions["cpu_spike_sudden_evidence"] = [
                                f"CPU spiked from {recent_values[-2]:.1f}% to {recent_values[-1]:.1f}%"
                            ]
                    
                    # Check for sustained high usage
                    if len(recent_values) >= 5:
                        high_count = sum(1 for v in recent_values[-5:] if v > 80)
                        if high_count >= 4:
                            conditions["cpu_high_sustained"] = 0.8
                            conditions["cpu_high_sustained_evidence"] = [
                                f"CPU usage above 80% for {high_count}/5 recent measurements"
                            ]
            
            # Network-related conditions
            if "network" in recent_metrics:
                network_metrics = recent_metrics["network"]
                if network_metrics:
                    latest_latency = network_metrics[-1].current_value
                    if latest_latency > 1000:  # > 1 second
                        conditions["network_latency_high"] = 0.8
                        conditions["network_latency_high_evidence"] = [
                            f"Network latency: {latest_latency:.0f}ms"
                        ]
            
            # Error message analysis
            message = error_event.message.lower() if error_event.message else ""
            
            if "connection refused" in message:
                conditions["connection_refused"] = 0.9
                conditions["connection_refused_evidence"] = ["Connection refused in error message"]
            
            if "pool" in message and "exhaust" in message:
                conditions["db_pool_exhausted"] = 0.9
                conditions["db_pool_exhausted_evidence"] = ["Connection pool exhaustion in error message"]
            
            if "timeout" in message and "query" in message:
                conditions["db_query_timeout"] = 0.8
                conditions["db_query_timeout_evidence"] = ["Query timeout in error message"]
            
            if "config" in message or "environment" in message:
                conditions["config_invalid"] = 0.7
                conditions["config_invalid_evidence"] = ["Configuration issue in error message"]
            
            if "dependency" in message or "module not found" in message:
                conditions["dependency_missing"] = 0.8
                conditions["dependency_missing_evidence"] = ["Dependency issue in error message"]
            
        except Exception as e:
            self.logger.error(f"Error analyzing conditions: {e}")
        
        return conditions


class EventCorrelator:
    """Correlates error events to find patterns and relationships."""
    
    def __init__(self):
        """Initialize the event correlator."""
        self.logger = logging.getLogger(__name__)
    
    async def correlate(self, error_event: ErrorEvent, 
                       recent_events: List[ErrorEvent]) -> List[str]:
        """
        Correlate error event with recent events.
        
        Args:
            error_event: The error event to correlate
            recent_events: List of recent error events
            
        Returns:
            List of correlated event IDs
        """
        try:
            correlated_ids = []
            
            # Time window for correlation (last 1 hour)
            time_window = timedelta(hours=1)
            cutoff_time = error_event.detected_at - time_window
            
            for event in recent_events:
                if event.id == error_event.id:
                    continue
                
                if event.detected_at < cutoff_time:
                    continue
                
                # Check for correlation
                correlation_score = self._calculate_correlation(error_event, event)
                
                if correlation_score > 0.5:  # Threshold for correlation
                    correlated_ids.append(event.id)
            
            return correlated_ids
            
        except Exception as e:
            self.logger.error(f"Error correlating events: {e}")
            return []
    
    def _calculate_correlation(self, event1: ErrorEvent, event2: ErrorEvent) -> float:
        """Calculate correlation score between two events."""
        score = 0.0
        
        try:
            # Same error type
            if event1.error_type == event2.error_type:
                score += 0.3
            
            # Same component
            if (event1.source_component and event2.source_component and
                event1.source_component == event2.source_component):
                score += 0.2
            
            # Similar severity
            severity_values = {
                ErrorSeverity.LOW: 1,
                ErrorSeverity.MEDIUM: 2,
                ErrorSeverity.HIGH: 3,
                ErrorSeverity.CRITICAL: 4,
            }
            
            sev1 = severity_values.get(event1.severity, 2)
            sev2 = severity_values.get(event2.severity, 2)
            
            if abs(sev1 - sev2) <= 1:
                score += 0.1
            
            # Similar tags
            tags1 = set(event1.tags)
            tags2 = set(event2.tags)
            
            if tags1 and tags2:
                tag_overlap = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
                score += tag_overlap * 0.2
            
            # Time proximity (closer in time = higher correlation)
            time_diff = abs((event1.detected_at - event2.detected_at).total_seconds())
            if time_diff < 300:  # Within 5 minutes
                score += 0.2
            elif time_diff < 900:  # Within 15 minutes
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return 0.0


class DecisionTree:
    """Decision tree for determining recommended recovery actions."""
    
    def __init__(self):
        """Initialize the decision tree."""
        self.logger = logging.getLogger(__name__)
        
        # Decision rules for different scenarios
        self.decision_rules = {
            ErrorType.MEMORY_LEAK: {
                "high_confidence": [
                    "Restart affected service",
                    "Increase memory allocation",
                    "Enable memory profiling",
                    "Review recent code changes for memory leaks",
                ],
                "medium_confidence": [
                    "Monitor memory usage closely",
                    "Prepare for service restart if needed",
                    "Check for memory-intensive operations",
                ],
                "low_confidence": [
                    "Investigate memory usage patterns",
                    "Enable detailed logging",
                    "Manual analysis required",
                ],
            },
            ErrorType.CPU_SPIKE: {
                "high_confidence": [
                    "Identify and terminate CPU-intensive processes",
                    "Scale up compute resources",
                    "Enable CPU profiling",
                    "Check for infinite loops or inefficient algorithms",
                ],
                "medium_confidence": [
                    "Monitor CPU usage trends",
                    "Prepare for resource scaling",
                    "Review recent deployments",
                ],
                "low_confidence": [
                    "Investigate CPU usage patterns",
                    "Enable performance monitoring",
                    "Manual analysis required",
                ],
            },
            ErrorType.NETWORK_TIMEOUT: {
                "high_confidence": [
                    "Check network connectivity",
                    "Increase timeout values",
                    "Implement retry logic",
                    "Contact external service providers",
                ],
                "medium_confidence": [
                    "Monitor network latency",
                    "Check firewall rules",
                    "Verify DNS resolution",
                ],
                "low_confidence": [
                    "Investigate network issues",
                    "Enable network monitoring",
                    "Manual analysis required",
                ],
            },
            ErrorType.DATABASE_CONNECTION: {
                "high_confidence": [
                    "Check database server status",
                    "Increase connection pool size",
                    "Restart database connections",
                    "Optimize long-running queries",
                ],
                "medium_confidence": [
                    "Monitor database performance",
                    "Check connection pool usage",
                    "Review database logs",
                ],
                "low_confidence": [
                    "Investigate database issues",
                    "Enable database monitoring",
                    "Manual analysis required",
                ],
            },
            ErrorType.DEPLOYMENT_FAILURE: {
                "high_confidence": [
                    "Rollback to previous version",
                    "Check configuration files",
                    "Verify environment variables",
                    "Check resource availability",
                ],
                "medium_confidence": [
                    "Review deployment logs",
                    "Validate dependencies",
                    "Check service health",
                ],
                "low_confidence": [
                    "Investigate deployment issues",
                    "Manual deployment analysis required",
                ],
            },
        }
    
    async def get_recommendations(self, error_event: ErrorEvent, 
                                root_cause: Dict[str, Any],
                                correlated_events: List[str]) -> List[str]:
        """
        Get recommended actions based on error analysis.
        
        Args:
            error_event: The error event
            root_cause: Root cause analysis result
            correlated_events: List of correlated event IDs
            
        Returns:
            List of recommended actions
        """
        try:
            error_type = error_event.error_type
            confidence = root_cause.get("confidence", 0.5)
            
            # Determine confidence level
            if confidence >= 0.8:
                confidence_level = "high_confidence"
            elif confidence >= 0.5:
                confidence_level = "medium_confidence"
            else:
                confidence_level = "low_confidence"
            
            # Get base recommendations for error type
            type_rules = self.decision_rules.get(error_type, {})
            base_recommendations = type_rules.get(confidence_level, [
                "Investigate the issue manually",
                "Enable detailed logging",
                "Contact system administrator",
            ])
            
            recommendations = base_recommendations.copy()
            
            # Add specific recommendations based on context
            context = error_event.context or {}
            
            # High resource usage
            if context.get("current_cpu", 0) > 90:
                recommendations.insert(0, "Scale up CPU resources immediately")
            
            if context.get("current_memory", 0) > 90:
                recommendations.insert(0, "Scale up memory resources immediately")
            
            # Multiple correlated events
            if len(correlated_events) >= 3:
                recommendations.append("Investigate system-wide issues - multiple related errors detected")
            
            # Severity-based recommendations
            if error_event.severity == ErrorSeverity.CRITICAL:
                recommendations.insert(0, "Escalate to on-call engineer immediately")
                recommendations.insert(1, "Activate incident response procedures")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)
            
            return unique_recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return [
                "Manual investigation required",
                "Enable detailed logging",
                "Contact system administrator",
            ]

