"""
Tests for the error detection service.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from graph_sitter.self_healing.error_detection.service import ErrorDetectionService
from graph_sitter.self_healing.models.config import ErrorDetectionConfig
from graph_sitter.self_healing.models.events import ErrorEvent, HealthMetric
from graph_sitter.self_healing.models.enums import ErrorType, ErrorSeverity, HealthStatus


@pytest.fixture
def error_detection_config():
    """Create test configuration for error detection."""
    return ErrorDetectionConfig(
        monitoring_interval=1,  # Fast for testing
        threshold_cpu=80.0,
        threshold_memory=85.0,
        threshold_error_rate=5.0,
        pattern_recognition_enabled=True,
        anomaly_detection_enabled=True,
    )


@pytest.fixture
def error_detection_service(error_detection_config):
    """Create error detection service for testing."""
    return ErrorDetectionService(error_detection_config)


@pytest.mark.asyncio
async def test_error_detection_service_initialization(error_detection_service):
    """Test error detection service initialization."""
    assert error_detection_service.config is not None
    assert not error_detection_service.is_running
    assert len(error_detection_service.monitors) > 0
    assert error_detection_service.error_classifier is not None


@pytest.mark.asyncio
async def test_monitor_system_health(error_detection_service):
    """Test system health monitoring."""
    # Mock the monitors to return test metrics
    with patch.object(error_detection_service.monitors['cpu'], 'get_metric') as mock_cpu:
        mock_cpu.return_value = HealthMetric(
            metric_name="cpu_usage",
            current_value=75.0,
            threshold_warning=80.0,
            threshold_critical=90.0,
            status=HealthStatus.HEALTHY,
        )
        
        metrics = await error_detection_service.monitor_system_health()
        
        assert len(metrics) >= 1
        assert any(m.metric_name == "cpu_usage" for m in metrics)


@pytest.mark.asyncio
async def test_classify_error(error_detection_service):
    """Test error classification."""
    error_event = ErrorEvent(
        error_type=ErrorType.UNKNOWN,
        severity=ErrorSeverity.MEDIUM,
        message="High CPU usage detected",
        context={"current_cpu": 85.0},
        detected_at=datetime.utcnow(),
    )
    
    classified_error = await error_detection_service.classify_error(error_event)
    
    assert classified_error.error_type != ErrorType.UNKNOWN
    assert classified_error.severity is not None


@pytest.mark.asyncio
async def test_detect_performance_degradation(error_detection_service):
    """Test performance degradation detection."""
    # Add some mock metrics to history
    cpu_metrics = [
        HealthMetric(
            metric_name="cpu_usage",
            current_value=85.0,
            measured_at=datetime.utcnow(),
        )
        for _ in range(10)
    ]
    
    error_detection_service.metrics_history["cpu"] = cpu_metrics
    
    degradation_event = await error_detection_service.detect_performance_degradation()
    
    # Should detect degradation due to high CPU
    assert degradation_event is not None
    assert degradation_event.error_type == ErrorType.PERFORMANCE_DEGRADATION


@pytest.mark.asyncio
async def test_error_handlers(error_detection_service):
    """Test error event handlers."""
    handler_called = False
    received_error = None
    
    def test_handler(error_event):
        nonlocal handler_called, received_error
        handler_called = True
        received_error = error_event
    
    error_detection_service.add_error_handler(test_handler)
    
    error_event = ErrorEvent(
        error_type=ErrorType.CPU_SPIKE,
        severity=ErrorSeverity.HIGH,
        message="Test error",
    )
    
    await error_detection_service.classify_error(error_event)
    
    assert handler_called
    assert received_error is not None
    assert received_error.id == error_event.id


@pytest.mark.asyncio
async def test_start_stop_service(error_detection_service):
    """Test starting and stopping the service."""
    assert not error_detection_service.is_running
    
    await error_detection_service.start()
    assert error_detection_service.is_running
    
    await error_detection_service.stop()
    assert not error_detection_service.is_running


class TestErrorClassifier:
    """Tests for error classifier."""
    
    def test_classify_memory_error(self):
        """Test classification of memory-related errors."""
        from graph_sitter.self_healing.error_detection.classifiers import ErrorClassifier
        
        classifier = ErrorClassifier()
        
        error_event = ErrorEvent(
            message="Out of memory error occurred",
            stack_trace="java.lang.OutOfMemoryError: Java heap space",
        )
        
        error_type = classifier.classify_type(error_event)
        assert error_type == ErrorType.MEMORY_LEAK
    
    def test_classify_cpu_error(self):
        """Test classification of CPU-related errors."""
        from graph_sitter.self_healing.error_detection.classifiers import ErrorClassifier
        
        classifier = ErrorClassifier()
        
        error_event = ErrorEvent(
            message="High CPU usage detected",
            context={"current_cpu": 95.0},
        )
        
        error_type = classifier.classify_type(error_event)
        assert error_type == ErrorType.CPU_SPIKE
    
    def test_assess_severity_critical(self):
        """Test severity assessment for critical errors."""
        from graph_sitter.self_healing.error_detection.classifiers import ErrorClassifier
        
        classifier = ErrorClassifier()
        
        error_event = ErrorEvent(
            message="CRITICAL: System failure detected",
            context={"current_cpu": 98.0},
        )
        
        severity = classifier.assess_severity(error_event)
        assert severity == ErrorSeverity.CRITICAL
    
    def test_assess_severity_from_context(self):
        """Test severity assessment based on context."""
        from graph_sitter.self_healing.error_detection.classifiers import ErrorClassifier
        
        classifier = ErrorClassifier()
        
        error_event = ErrorEvent(
            message="Resource usage high",
            context={"current_memory": 96.0},
        )
        
        severity = classifier.assess_severity(error_event)
        assert severity == ErrorSeverity.CRITICAL


class TestAnomalyDetector:
    """Tests for anomaly detector."""
    
    def test_detect_metric_anomaly(self):
        """Test metric anomaly detection."""
        from graph_sitter.self_healing.error_detection.classifiers import AnomalyDetector
        from collections import deque
        
        detector = AnomalyDetector(threshold=2.0)
        
        # Create normal metrics
        normal_metrics = [
            HealthMetric(metric_name="cpu", current_value=50.0 + i)
            for i in range(20)
        ]
        
        # Add anomalous metric
        anomalous_metric = HealthMetric(metric_name="cpu", current_value=95.0)
        normal_metrics.append(anomalous_metric)
        
        metrics_history = {"cpu": deque(normal_metrics)}
        
        error_event = ErrorEvent(
            message="Test error",
            context={"current_cpu": 95.0},
        )
        
        anomaly_score = detector.detect_anomaly(error_event, metrics_history)
        
        assert anomaly_score > 0.5  # Should detect anomaly
    
    def test_detect_temporal_anomaly(self):
        """Test temporal anomaly detection."""
        from graph_sitter.self_healing.error_detection.classifiers import AnomalyDetector
        
        detector = AnomalyDetector()
        
        # Create multiple errors of same type in short time
        error_events = [
            ErrorEvent(
                error_type=ErrorType.MEMORY_LEAK,
                detected_at=datetime.utcnow(),
            )
            for _ in range(5)
        ]
        
        # Simulate adding errors to detector's history
        for event in error_events[:-1]:
            detector._detect_temporal_anomaly(event)
        
        # Test the last error
        anomaly_score = detector._detect_temporal_anomaly(error_events[-1])
        
        assert anomaly_score > 0.0  # Should detect temporal anomaly

