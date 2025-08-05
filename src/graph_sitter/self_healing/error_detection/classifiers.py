"""
Error classification and anomaly detection.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime, timedelta

from ..models.events import ErrorEvent, HealthMetric
from ..models.enums import ErrorType, ErrorSeverity


class ErrorClassifier:
    """Classifies errors based on patterns and context."""
    
    def __init__(self):
        """Initialize the error classifier."""
        self.logger = logging.getLogger(__name__)
        
        # Error type patterns
        self.type_patterns = {
            ErrorType.MEMORY_LEAK: [
                r"out of memory",
                r"memory.*leak",
                r"heap.*overflow",
                r"cannot allocate memory",
            ],
            ErrorType.CPU_SPIKE: [
                r"cpu.*high",
                r"high.*cpu",
                r"cpu.*spike",
                r"processor.*overload",
            ],
            ErrorType.NETWORK_TIMEOUT: [
                r"connection.*timeout",
                r"network.*timeout",
                r"request.*timeout",
                r"socket.*timeout",
            ],
            ErrorType.DATABASE_CONNECTION: [
                r"database.*connection",
                r"db.*connection",
                r"connection.*refused",
                r"database.*timeout",
            ],
            ErrorType.API_FAILURE: [
                r"api.*error",
                r"http.*error",
                r"service.*unavailable",
                r"internal.*server.*error",
            ],
            ErrorType.DEPLOYMENT_FAILURE: [
                r"deployment.*failed",
                r"deploy.*error",
                r"rollback.*required",
                r"build.*failed",
            ],
            ErrorType.CONFIGURATION_ERROR: [
                r"config.*error",
                r"configuration.*invalid",
                r"missing.*config",
                r"invalid.*setting",
            ],
            ErrorType.DEPENDENCY_FAILURE: [
                r"dependency.*error",
                r"module.*not.*found",
                r"import.*error",
                r"package.*missing",
            ],
        }
        
        # Severity indicators
        self.severity_indicators = {
            ErrorSeverity.CRITICAL: [
                r"critical",
                r"fatal",
                r"emergency",
                r"system.*down",
                r"service.*unavailable",
            ],
            ErrorSeverity.HIGH: [
                r"error",
                r"failed",
                r"exception",
                r"timeout",
                r"refused",
            ],
            ErrorSeverity.MEDIUM: [
                r"warning",
                r"warn",
                r"degraded",
                r"slow",
            ],
            ErrorSeverity.LOW: [
                r"info",
                r"notice",
                r"debug",
            ],
        }
    
    def classify_type(self, error_event: ErrorEvent) -> ErrorType:
        """
        Classify error type based on message and context.
        
        Args:
            error_event: The error event to classify
            
        Returns:
            Classified error type
        """
        try:
            message = error_event.message.lower() if error_event.message else ""
            stack_trace = error_event.stack_trace.lower() if error_event.stack_trace else ""
            combined_text = f"{message} {stack_trace}"
            
            # Check patterns for each error type
            for error_type, patterns in self.type_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, combined_text, re.IGNORECASE):
                        self.logger.debug(f"Classified error as {error_type.value} based on pattern: {pattern}")
                        return error_type
            
            # Check context for additional clues
            context = error_event.context or {}
            
            # CPU-related errors
            if "cpu" in context and isinstance(context.get("current_cpu"), (int, float)):
                if context["current_cpu"] > 90:
                    return ErrorType.CPU_SPIKE
            
            # Memory-related errors
            if "memory" in context and isinstance(context.get("current_memory"), (int, float)):
                if context["current_memory"] > 90:
                    return ErrorType.MEMORY_LEAK
            
            # Network-related errors
            if "network" in context or "response_time" in context:
                return ErrorType.NETWORK_TIMEOUT
            
            # Performance degradation
            if "performance" in error_event.tags:
                return ErrorType.PERFORMANCE_DEGRADATION
            
            return ErrorType.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Error classifying error type: {e}")
            return ErrorType.UNKNOWN
    
    def assess_severity(self, error_event: ErrorEvent) -> ErrorSeverity:
        """
        Assess error severity based on message and context.
        
        Args:
            error_event: The error event to assess
            
        Returns:
            Assessed error severity
        """
        try:
            message = error_event.message.lower() if error_event.message else ""
            stack_trace = error_event.stack_trace.lower() if error_event.stack_trace else ""
            combined_text = f"{message} {stack_trace}"
            
            # Check severity patterns (highest priority first)
            for severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH, ErrorSeverity.MEDIUM, ErrorSeverity.LOW]:
                patterns = self.severity_indicators.get(severity, [])
                for pattern in patterns:
                    if re.search(pattern, combined_text, re.IGNORECASE):
                        return severity
            
            # Context-based severity assessment
            context = error_event.context or {}
            
            # High resource usage indicates higher severity
            cpu_usage = context.get("current_cpu", 0)
            memory_usage = context.get("current_memory", 0)
            
            if isinstance(cpu_usage, (int, float)) and cpu_usage > 95:
                return ErrorSeverity.CRITICAL
            if isinstance(memory_usage, (int, float)) and memory_usage > 95:
                return ErrorSeverity.CRITICAL
            
            if isinstance(cpu_usage, (int, float)) and cpu_usage > 85:
                return ErrorSeverity.HIGH
            if isinstance(memory_usage, (int, float)) and memory_usage > 85:
                return ErrorSeverity.HIGH
            
            # Error type-based severity
            if error_event.error_type in [ErrorType.DEPLOYMENT_FAILURE, ErrorType.DATABASE_CONNECTION]:
                return ErrorSeverity.HIGH
            
            if error_event.error_type in [ErrorType.CONFIGURATION_ERROR, ErrorType.DEPENDENCY_FAILURE]:
                return ErrorSeverity.MEDIUM
            
            # Default to medium severity
            return ErrorSeverity.MEDIUM
            
        except Exception as e:
            self.logger.error(f"Error assessing severity: {e}")
            return ErrorSeverity.MEDIUM


class AnomalyDetector:
    """Detects anomalies in system behavior and error patterns."""
    
    def __init__(self, window_size: int = 100, threshold: float = 2.0):
        """
        Initialize the anomaly detector.
        
        Args:
            window_size: Size of the sliding window for analysis
            threshold: Standard deviation threshold for anomaly detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.logger = logging.getLogger(__name__)
        
        # Historical data for baseline calculation
        self.metric_baselines: Dict[str, Dict[str, float]] = {}
        self.error_patterns: Dict[str, List[datetime]] = {}
    
    def detect_anomaly(self, error_event: ErrorEvent, metrics_history: Dict[str, deque]) -> float:
        """
        Detect if an error event represents an anomaly.
        
        Args:
            error_event: The error event to analyze
            metrics_history: Historical metrics data
            
        Returns:
            Anomaly score (0.0 to 1.0, higher means more anomalous)
        """
        try:
            anomaly_score = 0.0
            
            # Check for metric anomalies
            metric_anomaly = self._detect_metric_anomaly(error_event, metrics_history)
            anomaly_score = max(anomaly_score, metric_anomaly)
            
            # Check for temporal anomalies (unusual timing)
            temporal_anomaly = self._detect_temporal_anomaly(error_event)
            anomaly_score = max(anomaly_score, temporal_anomaly)
            
            # Check for pattern anomalies
            pattern_anomaly = self._detect_pattern_anomaly(error_event)
            anomaly_score = max(anomaly_score, pattern_anomaly)
            
            return min(anomaly_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"Error detecting anomaly: {e}")
            return 0.0
    
    def _detect_metric_anomaly(self, error_event: ErrorEvent, metrics_history: Dict[str, deque]) -> float:
        """Detect anomalies in metric values."""
        try:
            max_anomaly = 0.0
            
            for metric_name, history in metrics_history.items():
                if len(history) < 10:  # Need sufficient data
                    continue
                
                # Get recent values
                recent_values = [m.current_value for m in list(history)[-self.window_size:]]
                
                if len(recent_values) < 10:
                    continue
                
                # Calculate baseline statistics
                mean_value = sum(recent_values) / len(recent_values)
                variance = sum((x - mean_value) ** 2 for x in recent_values) / len(recent_values)
                std_dev = variance ** 0.5
                
                if std_dev == 0:
                    continue
                
                # Check current value against baseline
                current_value = recent_values[-1]
                z_score = abs(current_value - mean_value) / std_dev
                
                if z_score > self.threshold:
                    anomaly_score = min(z_score / (self.threshold * 2), 1.0)
                    max_anomaly = max(max_anomaly, anomaly_score)
                    
                    self.logger.debug(f"Metric anomaly detected in {metric_name}: z_score={z_score:.2f}")
            
            return max_anomaly
            
        except Exception as e:
            self.logger.error(f"Error detecting metric anomaly: {e}")
            return 0.0
    
    def _detect_temporal_anomaly(self, error_event: ErrorEvent) -> float:
        """Detect temporal anomalies (unusual timing patterns)."""
        try:
            error_type_key = error_event.error_type.value
            current_time = error_event.detected_at
            
            # Track error occurrence times
            if error_type_key not in self.error_patterns:
                self.error_patterns[error_type_key] = []
            
            # Clean old entries (keep last 24 hours)
            cutoff_time = current_time - timedelta(hours=24)
            self.error_patterns[error_type_key] = [
                t for t in self.error_patterns[error_type_key] if t > cutoff_time
            ]
            
            # Add current error
            self.error_patterns[error_type_key].append(current_time)
            
            # Check for unusual frequency
            recent_errors = len(self.error_patterns[error_type_key])
            
            # If we have more than 10 errors of this type in 24 hours, it's anomalous
            if recent_errors > 10:
                return min(recent_errors / 20.0, 1.0)  # Scale to 0-1
            
            # Check for clustering (multiple errors in short time)
            if recent_errors >= 3:
                recent_times = sorted(self.error_patterns[error_type_key][-3:])
                time_span = (recent_times[-1] - recent_times[0]).total_seconds()
                
                if time_span < 300:  # 3 errors in 5 minutes
                    return 0.8
                elif time_span < 900:  # 3 errors in 15 minutes
                    return 0.6
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error detecting temporal anomaly: {e}")
            return 0.0
    
    def _detect_pattern_anomaly(self, error_event: ErrorEvent) -> float:
        """Detect pattern anomalies in error characteristics."""
        try:
            # Check for unusual error combinations
            anomaly_score = 0.0
            
            # Unusual severity for error type
            severity_mapping = {
                ErrorType.CONFIGURATION_ERROR: ErrorSeverity.MEDIUM,
                ErrorType.DEPENDENCY_FAILURE: ErrorSeverity.MEDIUM,
                ErrorType.MEMORY_LEAK: ErrorSeverity.HIGH,
                ErrorType.CPU_SPIKE: ErrorSeverity.HIGH,
                ErrorType.DATABASE_CONNECTION: ErrorSeverity.HIGH,
                ErrorType.DEPLOYMENT_FAILURE: ErrorSeverity.CRITICAL,
            }
            
            expected_severity = severity_mapping.get(error_event.error_type)
            if expected_severity and error_event.severity != expected_severity:
                # Severity mismatch
                severity_values = {
                    ErrorSeverity.LOW: 1,
                    ErrorSeverity.MEDIUM: 2,
                    ErrorSeverity.HIGH: 3,
                    ErrorSeverity.CRITICAL: 4,
                }
                
                expected_val = severity_values.get(expected_severity, 2)
                actual_val = severity_values.get(error_event.severity, 2)
                
                if abs(expected_val - actual_val) >= 2:
                    anomaly_score = 0.5
            
            # Check for unusual context combinations
            context = error_event.context or {}
            
            # High CPU but memory error type
            if (error_event.error_type == ErrorType.MEMORY_LEAK and 
                context.get("current_cpu", 0) > 90):
                anomaly_score = max(anomaly_score, 0.6)
            
            # Network error but high local resource usage
            if (error_event.error_type == ErrorType.NETWORK_TIMEOUT and
                context.get("current_cpu", 0) > 80 and
                context.get("current_memory", 0) > 80):
                anomaly_score = max(anomaly_score, 0.7)
            
            return anomaly_score
            
        except Exception as e:
            self.logger.error(f"Error detecting pattern anomaly: {e}")
            return 0.0

