"""
Tests for the self-healing orchestrator.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from graph_sitter.self_healing.orchestrator import SelfHealingOrchestrator
from graph_sitter.self_healing.models.config import SelfHealingConfig
from graph_sitter.self_healing.models.events import ErrorEvent, DiagnosisResult, RecoveryAction
from graph_sitter.self_healing.models.enums import ErrorType, ErrorSeverity, DiagnosisConfidence, RecoveryStatus


@pytest.fixture
def self_healing_config():
    """Create test configuration for self-healing system."""
    return SelfHealingConfig(
        enabled=True,
        log_level="INFO",
    )


@pytest.fixture
def orchestrator(self_healing_config):
    """Create orchestrator for testing."""
    return SelfHealingOrchestrator(self_healing_config)


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization."""
    assert orchestrator.config is not None
    assert not orchestrator.is_running
    assert orchestrator.error_detection is not None
    assert orchestrator.diagnosis_engine is not None
    assert orchestrator.recovery_system is not None
    assert orchestrator.health_monitor is not None


@pytest.mark.asyncio
async def test_start_stop_orchestrator(orchestrator):
    """Test starting and stopping the orchestrator."""
    assert not orchestrator.is_running
    
    # Mock the component start methods
    with patch.object(orchestrator.error_detection, 'start', new_callable=AsyncMock) as mock_error_start, \
         patch.object(orchestrator.health_monitor, 'start', new_callable=AsyncMock) as mock_health_start:
        
        await orchestrator.start()
        assert orchestrator.is_running
        mock_error_start.assert_called_once()
        mock_health_start.assert_called_once()
    
    # Mock the component stop methods
    with patch.object(orchestrator.error_detection, 'stop', new_callable=AsyncMock) as mock_error_stop, \
         patch.object(orchestrator.health_monitor, 'stop', new_callable=AsyncMock) as mock_health_stop:
        
        await orchestrator.stop()
        assert not orchestrator.is_running
        mock_error_stop.assert_called_once()
        mock_health_stop.assert_called_once()


@pytest.mark.asyncio
async def test_handle_error_event_with_recovery(orchestrator):
    """Test handling an error event that should trigger recovery."""
    error_event = ErrorEvent(
        error_type=ErrorType.MEMORY_LEAK,
        severity=ErrorSeverity.HIGH,
        message="Memory usage critical",
        context={"current_memory": 95.0},
    )
    
    # Mock diagnosis result with high confidence
    mock_diagnosis = DiagnosisResult(
        root_cause="Memory leak in application",
        confidence=DiagnosisConfidence.HIGH,
        recommended_actions=["Restart service", "Increase memory allocation"],
    )
    
    # Mock recovery actions
    mock_recovery_action = RecoveryAction(
        action_type="restart_service",
        description="Restart affected service",
        status=RecoveryStatus.COMPLETED,
    )
    
    with patch.object(orchestrator.error_detection, 'classify_error', new_callable=AsyncMock) as mock_classify, \
         patch.object(orchestrator.diagnosis_engine, 'analyze_error', new_callable=AsyncMock) as mock_diagnose, \
         patch.object(orchestrator.recovery_system, 'create_recovery_actions', new_callable=AsyncMock) as mock_create_actions, \
         patch.object(orchestrator.recovery_system, 'execute_recovery_action', new_callable=AsyncMock) as mock_execute:
        
        mock_classify.return_value = error_event
        mock_diagnose.return_value = mock_diagnosis
        mock_create_actions.return_value = [mock_recovery_action]
        mock_execute.return_value = mock_recovery_action
        
        incident_id = await orchestrator.handle_error_event(error_event)
        
        assert incident_id is not None
        assert incident_id in orchestrator.active_incidents
        
        # Verify the workflow was executed
        mock_classify.assert_called_once()
        mock_diagnose.assert_called_once()
        mock_create_actions.assert_called_once()
        mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_handle_error_event_with_escalation(orchestrator):
    """Test handling an error event that should be escalated."""
    error_event = ErrorEvent(
        error_type=ErrorType.UNKNOWN,
        severity=ErrorSeverity.CRITICAL,
        message="Unknown critical error",
    )
    
    # Mock diagnosis result with low confidence
    mock_diagnosis = DiagnosisResult(
        root_cause="Unable to determine cause",
        confidence=DiagnosisConfidence.LOW,
        recommended_actions=["Manual investigation required"],
    )
    
    with patch.object(orchestrator.error_detection, 'classify_error', new_callable=AsyncMock) as mock_classify, \
         patch.object(orchestrator.diagnosis_engine, 'analyze_error', new_callable=AsyncMock) as mock_diagnose, \
         patch.object(orchestrator.recovery_system, 'escalate_to_human', new_callable=AsyncMock) as mock_escalate:
        
        mock_classify.return_value = error_event
        mock_diagnose.return_value = mock_diagnosis
        mock_escalate.return_value = True
        
        incident_id = await orchestrator.handle_error_event(error_event)
        
        assert incident_id is not None
        assert incident_id in orchestrator.active_incidents
        
        # Verify escalation was called
        mock_escalate.assert_called_once()


@pytest.mark.asyncio
async def test_get_incident_status(orchestrator):
    """Test getting incident status."""
    # Create a mock incident
    incident_id = "test-incident-123"
    error_event = ErrorEvent(
        error_type=ErrorType.CPU_SPIKE,
        severity=ErrorSeverity.MEDIUM,
        message="CPU usage high",
    )
    
    orchestrator.active_incidents[incident_id] = {
        "id": incident_id,
        "error_event": error_event,
        "started_at": datetime.utcnow(),
        "status": "analyzing",
        "diagnosis": None,
        "recovery_actions": [],
        "resolved": False,
    }
    
    status = await orchestrator.get_incident_status(incident_id)
    
    assert status is not None
    assert status["id"] == incident_id
    assert status["status"] == "analyzing"
    assert status["error_type"] == ErrorType.CPU_SPIKE.value
    assert status["severity"] == ErrorSeverity.MEDIUM.value
    assert not status["resolved"]


@pytest.mark.asyncio
async def test_get_system_status(orchestrator):
    """Test getting system status."""
    with patch.object(orchestrator.health_monitor, 'get_system_status') as mock_health_status, \
         patch.object(orchestrator.recovery_system, 'get_recovery_statistics') as mock_recovery_stats:
        
        mock_health_status.return_value = {"overall_status": "healthy"}
        mock_recovery_stats.return_value = {"success_rate": 85.0}
        
        status = orchestrator.get_system_status()
        
        assert status["enabled"] == orchestrator.config.enabled
        assert status["running"] == orchestrator.is_running
        assert "active_incidents" in status
        assert "statistics" in status
        assert "health_status" in status
        assert "recovery_stats" in status


def test_should_attempt_recovery_critical_high_confidence(orchestrator):
    """Test recovery decision for critical error with high confidence."""
    error_event = ErrorEvent(
        severity=ErrorSeverity.CRITICAL,
    )
    
    diagnosis = DiagnosisResult(
        confidence=DiagnosisConfidence.HIGH,
    )
    
    should_recover = orchestrator._should_attempt_recovery(error_event, diagnosis)
    assert should_recover


def test_should_attempt_recovery_low_severity(orchestrator):
    """Test recovery decision for low severity error."""
    error_event = ErrorEvent(
        severity=ErrorSeverity.LOW,
    )
    
    diagnosis = DiagnosisResult(
        confidence=DiagnosisConfidence.HIGH,
    )
    
    should_recover = orchestrator._should_attempt_recovery(error_event, diagnosis)
    assert not should_recover


def test_should_attempt_recovery_low_confidence(orchestrator):
    """Test recovery decision for low confidence diagnosis."""
    error_event = ErrorEvent(
        severity=ErrorSeverity.HIGH,
    )
    
    diagnosis = DiagnosisResult(
        confidence=DiagnosisConfidence.LOW,
    )
    
    should_recover = orchestrator._should_attempt_recovery(error_event, diagnosis)
    assert not should_recover


@pytest.mark.asyncio
async def test_disabled_orchestrator(self_healing_config):
    """Test orchestrator behavior when disabled."""
    self_healing_config.enabled = False
    orchestrator = SelfHealingOrchestrator(self_healing_config)
    
    await orchestrator.start()
    assert not orchestrator.is_running


class TestEventHandlers:
    """Tests for event handlers."""
    
    @pytest.mark.asyncio
    async def test_error_detection_handler(self, orchestrator):
        """Test error detection event handler."""
        error_event = ErrorEvent(
            error_type=ErrorType.NETWORK_TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            message="Network timeout detected",
        )
        
        with patch.object(orchestrator, 'handle_error_event', new_callable=AsyncMock) as mock_handle:
            orchestrator._on_error_detected(error_event)
            
            # Give async task time to execute
            await asyncio.sleep(0.1)
            
            # Note: The actual call happens in an async task, so we can't directly assert
            # In a real test, you might want to use more sophisticated mocking
    
    def test_health_metric_handler(self, orchestrator):
        """Test health metric event handler."""
        from graph_sitter.self_healing.models.events import HealthMetric
        from graph_sitter.self_healing.models.enums import HealthStatus
        
        health_metric = HealthMetric(
            metric_name="cpu_usage",
            current_value=75.0,
            status=HealthStatus.HEALTHY,
        )
        
        with patch.object(orchestrator.diagnosis_engine, 'add_metric_data') as mock_add_metric:
            orchestrator._on_health_metric(health_metric)
            mock_add_metric.assert_called_once_with("cpu_usage", [health_metric])
    
    def test_recovery_update_handler(self, orchestrator):
        """Test recovery update event handler."""
        recovery_action = RecoveryAction(
            action_type="restart_service",
            status=RecoveryStatus.COMPLETED,
        )
        
        with patch.object(orchestrator.health_monitor, 'track_recovery_effectiveness', new_callable=AsyncMock) as mock_track:
            orchestrator._on_recovery_update(recovery_action)
            
            # The tracking happens in an async task
            # In a real test environment, you'd wait for the task to complete
    
    def test_health_status_change_handler(self, orchestrator):
        """Test health status change event handler."""
        from graph_sitter.self_healing.models.enums import HealthStatus
        
        new_status = HealthStatus.WARNING
        
        # This should not raise an exception
        orchestrator._on_health_status_change(new_status)

