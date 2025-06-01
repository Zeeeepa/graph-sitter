"""
Error Detection Service

Main service for detecting and classifying system errors and anomalies.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from collections import deque

from ..models.config import ErrorDetectionConfig
from ..models.events import ErrorEvent, HealthMetric
from ..models.enums import ErrorType, ErrorSeverity, HealthStatus
from .monitors import CPUMonitor, MemoryMonitor, NetworkMonitor, ErrorRateMonitor
from .classifiers import ErrorClassifier, AnomalyDetector


class ErrorDetectionService:
    """
    Service for real-time error detection and classification.
    
    Monitors system health metrics, detects anomalies, and classifies errors
    for automated diagnosis and recovery.
    """
    
    def __init__(self, config: ErrorDetectionConfig):
        """
        Initialize the error detection service.
        
        Args:
            config: Configuration for error detection
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self._stop_event = asyncio.Event()
        
        # Initialize monitors
        self.monitors = {
            "cpu": CPUMonitor(config.threshold_cpu),
            "memory": MemoryMonitor(config.threshold_memory),
            "network": NetworkMonitor(config.threshold_response_time),
            "error_rate": ErrorRateMonitor(config.threshold_error_rate),
        }
        
        # Initialize classifiers
        self.error_classifier = ErrorClassifier()
        self.anomaly_detector = AnomalyDetector() if config.anomaly_detection_enabled else None
        
        # Event handlers
        self.error_handlers: List[Callable[[ErrorEvent], None]] = []
        self.health_handlers: List[Callable[[HealthMetric], None]] = []
        
        # Metrics history for pattern recognition
        self.metrics_history: Dict[str, deque] = {}
        self.max_history_size = 1000
        
        # Pattern recognition state
        self.pattern_cache: Dict[str, Any] = {}
        self.last_pattern_analysis = datetime.utcnow()
    
    def add_error_handler(self, handler: Callable[[ErrorEvent], None]) -> None:
        """Add a handler for error events."""
        self.error_handlers.append(handler)
    
    def add_health_handler(self, handler: Callable[[HealthMetric], None]) -> None:
        """Add a handler for health metric events."""
        self.health_handlers.append(handler)
    
    async def start(self) -> None:
        """Start the error detection service."""
        if self.is_running:
            self.logger.warning("Error detection service is already running")
            return
        
        self.logger.info("Starting error detection service")
        self.is_running = True
        self._stop_event.clear()
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
        
        # Start pattern recognition task if enabled
        if self.config.pattern_recognition_enabled:
            asyncio.create_task(self._pattern_recognition_loop())
    
    async def stop(self) -> None:
        """Stop the error detection service."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping error detection service")
        self.is_running = False
        self._stop_event.set()
    
    async def monitor_system_health(self) -> List[HealthMetric]:
        """
        Monitor system health and return current metrics.
        
        Returns:
            List of current health metrics
        """
        metrics = []
        
        for name, monitor in self.monitors.items():
            try:
                metric = await monitor.get_metric()
                if metric:
                    metrics.append(metric)
                    
                    # Store in history for pattern recognition
                    if name not in self.metrics_history:
                        self.metrics_history[name] = deque(maxlen=self.max_history_size)
                    self.metrics_history[name].append(metric)
                    
                    # Notify health handlers
                    for handler in self.health_handlers:
                        try:
                            handler(metric)
                        except Exception as e:
                            self.logger.error(f"Error in health handler: {e}")
                            
            except Exception as e:
                self.logger.error(f"Error monitoring {name}: {e}")
        
        return metrics
    
    async def classify_error(self, error_event: ErrorEvent) -> ErrorEvent:
        """
        Classify and assess error severity.
        
        Args:
            error_event: The error event to classify
            
        Returns:
            Updated error event with classification
        """
        try:
            # Use error classifier to determine type and severity
            error_event.error_type = self.error_classifier.classify_type(error_event)
            error_event.severity = self.error_classifier.assess_severity(error_event)
            
            # Add context from recent metrics
            error_event.context.update(self._get_error_context())
            
            # Detect if this is part of an anomaly pattern
            if self.anomaly_detector and self.config.anomaly_detection_enabled:
                anomaly_score = self.anomaly_detector.detect_anomaly(error_event, self.metrics_history)
                error_event.context["anomaly_score"] = anomaly_score
                
                if anomaly_score > 0.8:  # High anomaly score
                    error_event.severity = ErrorSeverity.HIGH
                    error_event.tags.append("anomaly")
            
            # Notify error handlers
            for handler in self.error_handlers:
                try:
                    handler(error_event)
                except Exception as e:
                    self.logger.error(f"Error in error handler: {e}")
            
            return error_event
            
        except Exception as e:
            self.logger.error(f"Error classifying error event: {e}")
            return error_event
    
    async def detect_performance_degradation(self) -> Optional[ErrorEvent]:
        """
        Detect performance degradation patterns.
        
        Returns:
            Error event if degradation is detected, None otherwise
        """
        try:
            # Analyze recent metrics for degradation patterns
            current_time = datetime.utcnow()
            
            # Check CPU trends
            if "cpu" in self.metrics_history and len(self.metrics_history["cpu"]) > 10:
                recent_cpu = list(self.metrics_history["cpu"])[-10:]
                avg_cpu = sum(m.current_value for m in recent_cpu) / len(recent_cpu)
                
                if avg_cpu > self.config.threshold_cpu * 0.9:  # 90% of threshold
                    return ErrorEvent(
                        error_type=ErrorType.PERFORMANCE_DEGRADATION,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"CPU usage trending high: {avg_cpu:.1f}%",
                        context={"avg_cpu": avg_cpu, "threshold": self.config.threshold_cpu},
                        source_component="cpu_monitor",
                        detected_at=current_time,
                        tags=["performance", "cpu"]
                    )
            
            # Check memory trends
            if "memory" in self.metrics_history and len(self.metrics_history["memory"]) > 10:
                recent_memory = list(self.metrics_history["memory"])[-10:]
                avg_memory = sum(m.current_value for m in recent_memory) / len(recent_memory)
                
                if avg_memory > self.config.threshold_memory * 0.9:  # 90% of threshold
                    return ErrorEvent(
                        error_type=ErrorType.PERFORMANCE_DEGRADATION,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Memory usage trending high: {avg_memory:.1f}%",
                        context={"avg_memory": avg_memory, "threshold": self.config.threshold_memory},
                        source_component="memory_monitor",
                        detected_at=current_time,
                        tags=["performance", "memory"]
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting performance degradation: {e}")
            return None
    
    def _get_error_context(self) -> Dict[str, Any]:
        """Get current system context for error events."""
        context = {}
        
        # Add recent metric values
        for name, history in self.metrics_history.items():
            if history:
                latest = history[-1]
                context[f"current_{name}"] = latest.current_value
                context[f"{name}_status"] = latest.status.value
        
        # Add system timestamp
        context["system_time"] = datetime.utcnow().isoformat()
        
        return context
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running and not self._stop_event.is_set():
            try:
                # Monitor system health
                await self.monitor_system_health()
                
                # Check for performance degradation
                degradation_event = await self.detect_performance_degradation()
                if degradation_event:
                    await self.classify_error(degradation_event)
                
                # Wait for next monitoring interval
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _pattern_recognition_loop(self) -> None:
        """Pattern recognition loop for detecting recurring issues."""
        while self.is_running and not self._stop_event.is_set():
            try:
                current_time = datetime.utcnow()
                
                # Run pattern analysis every 5 minutes
                if current_time - self.last_pattern_analysis > timedelta(minutes=5):
                    await self._analyze_patterns()
                    self.last_pattern_analysis = current_time
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in pattern recognition loop: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_patterns(self) -> None:
        """Analyze metrics history for patterns."""
        try:
            # Look for recurring patterns in metrics
            for metric_name, history in self.metrics_history.items():
                if len(history) < 20:  # Need sufficient data
                    continue
                
                # Simple pattern detection: look for cycles or trends
                values = [m.current_value for m in list(history)[-50:]]  # Last 50 values
                
                # Detect if values are consistently increasing (trend)
                if len(values) >= 10:
                    recent_trend = sum(values[-5:]) / 5 - sum(values[-10:-5]) / 5
                    if recent_trend > 0 and metric_name in ["cpu", "memory"]:
                        # Increasing trend detected
                        pattern_key = f"{metric_name}_increasing_trend"
                        if pattern_key not in self.pattern_cache:
                            self.pattern_cache[pattern_key] = {
                                "detected_at": datetime.utcnow(),
                                "trend_value": recent_trend,
                                "metric": metric_name
                            }
                            self.logger.info(f"Detected increasing trend in {metric_name}: {recent_trend:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")

