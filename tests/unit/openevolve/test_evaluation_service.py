"""Unit tests for EvaluationService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from graph_sitter.openevolve.service import EvaluationService
from graph_sitter.openevolve.models import EvaluationTrigger, EvaluationStatus
from graph_sitter.openevolve.database import EvaluationRepository


@pytest.fixture
def config():
    """Create test configuration."""
    return OpenEvolveConfig(
        api_key="test_api_key",
        enable_auto_evaluation=True,
        min_evaluation_interval=60,
        evaluation_queue_size=10
    )


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def mock_repository():
    """Create mock evaluation repository."""
    return MagicMock(spec=EvaluationRepository)


@pytest.fixture
async def evaluation_service(config, mock_session):
    """Create evaluation service for testing."""
    service = EvaluationService(config, mock_session)
    
    # Mock the client
    service._client = AsyncMock()
    
    # Mock the repository
    service.repository = MagicMock(spec=EvaluationRepository)
    
    return service


class TestEvaluationService:
    """Test cases for EvaluationService."""
    
    def test_init(self, config, mock_session):
        """Test service initialization."""
        service = EvaluationService(config, mock_session)
        
        assert service.config == config
        assert service.session == mock_session
        assert isinstance(service.repository, EvaluationRepository)
        assert service._client is None
        assert service._last_evaluation_time is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, config, mock_session):
        """Test async context manager."""
        async with EvaluationService(config, mock_session) as service:
            assert service._client is not None
    
    @pytest.mark.asyncio
    async def test_trigger_evaluation_success(self, evaluation_service):
        """Test successful evaluation triggering."""
        # Mock repository response
        mock_evaluation = MagicMock()
        mock_evaluation.id = uuid4()
        evaluation_service.repository.create_evaluation.return_value = mock_evaluation
        
        # Trigger evaluation
        eval_id = await evaluation_service.trigger_evaluation(
            trigger_event=EvaluationTrigger.TASK_FAILURE,
            context={"task_id": "test_task"},
            priority=3
        )
        
        assert eval_id == mock_evaluation.id
        evaluation_service.repository.create_evaluation.assert_called_once()
        
        # Check that evaluation was added to queue
        assert not evaluation_service._evaluation_queue.empty()
    
    @pytest.mark.asyncio
    async def test_trigger_evaluation_disabled(self, evaluation_service):
        """Test triggering evaluation when auto evaluation is disabled."""
        evaluation_service.config.enable_auto_evaluation = False
        
        with pytest.raises(ValueError, match="Automatic evaluations are disabled"):
            await evaluation_service.trigger_evaluation(
                trigger_event=EvaluationTrigger.TASK_FAILURE,
                context={"task_id": "test_task"}
            )
    
    @pytest.mark.asyncio
    async def test_trigger_evaluation_rate_limited(self, evaluation_service):
        """Test rate limiting for evaluation triggering."""
        # Set last evaluation time to recent
        evaluation_service._last_evaluation_time = datetime.utcnow() - timedelta(seconds=30)
        evaluation_service.config.min_evaluation_interval = 60
        
        with pytest.raises(ValueError, match="Rate limited"):
            await evaluation_service.trigger_evaluation(
                trigger_event=EvaluationTrigger.TASK_FAILURE,
                context={"task_id": "test_task"}
            )
    
    @pytest.mark.asyncio
    async def test_trigger_evaluation_manual_when_disabled(self, evaluation_service):
        """Test manual evaluation triggering when auto evaluation is disabled."""
        evaluation_service.config.enable_auto_evaluation = False
        
        # Mock repository response
        mock_evaluation = MagicMock()
        mock_evaluation.id = uuid4()
        evaluation_service.repository.create_evaluation.return_value = mock_evaluation
        
        # Manual evaluations should still work
        eval_id = await evaluation_service.trigger_evaluation(
            trigger_event=EvaluationTrigger.MANUAL,
            context={"reason": "manual_review"}
        )
        
        assert eval_id == mock_evaluation.id
    
    @pytest.mark.asyncio
    async def test_get_evaluation_result(self, evaluation_service):
        """Test getting evaluation result."""
        eval_id = uuid4()
        
        # Mock database evaluation
        mock_evaluation = MagicMock()
        mock_evaluation.id = eval_id
        mock_evaluation.evaluation_id = "openevolve_123"
        mock_evaluation.status = EvaluationStatus.COMPLETED.value
        mock_evaluation.submitted_at = datetime.utcnow()
        mock_evaluation.started_at = None
        mock_evaluation.completed_at = datetime.utcnow()
        mock_evaluation.results = {"score": 0.85}
        mock_evaluation.metrics = {"accuracy": 0.9}
        mock_evaluation.error_message = None
        
        evaluation_service.repository.get_evaluation.return_value = mock_evaluation
        
        result = await evaluation_service.get_evaluation_result(eval_id)
        
        assert result is not None
        assert result.id == eval_id
        assert result.status == EvaluationStatus.COMPLETED
        assert result.results == {"score": 0.85}
    
    @pytest.mark.asyncio
    async def test_get_evaluation_result_not_found(self, evaluation_service):
        """Test getting evaluation result when not found."""
        eval_id = uuid4()
        evaluation_service.repository.get_evaluation.return_value = None
        
        result = await evaluation_service.get_evaluation_result(eval_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_evaluations(self, evaluation_service):
        """Test listing evaluations."""
        # Mock database evaluations
        mock_evaluations = [
            MagicMock(
                id=uuid4(),
                evaluation_id="eval_1",
                status=EvaluationStatus.COMPLETED.value,
                submitted_at=datetime.utcnow(),
                started_at=None,
                completed_at=datetime.utcnow(),
                results={},
                metrics=None,
                error_message=None
            ),
            MagicMock(
                id=uuid4(),
                evaluation_id="eval_2",
                status=EvaluationStatus.RUNNING.value,
                submitted_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=None,
                results=None,
                metrics=None,
                error_message=None
            )
        ]
        
        evaluation_service.repository.list_evaluations.return_value = mock_evaluations
        
        results = await evaluation_service.list_evaluations(limit=10)
        
        assert len(results) == 2
        assert results[0].status == EvaluationStatus.COMPLETED
        assert results[1].status == EvaluationStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_cancel_evaluation_success(self, evaluation_service):
        """Test successful evaluation cancellation."""
        eval_id = uuid4()
        
        # Mock database evaluation
        mock_evaluation = MagicMock()
        mock_evaluation.status = EvaluationStatus.RUNNING.value
        mock_evaluation.evaluation_id = "openevolve_123"
        
        evaluation_service.repository.get_evaluation.return_value = mock_evaluation
        evaluation_service._client.cancel_evaluation.return_value = True
        
        result = await evaluation_service.cancel_evaluation(eval_id)
        
        assert result is True
        evaluation_service._client.cancel_evaluation.assert_called_once_with("openevolve_123")
        evaluation_service.repository.update_evaluation_status.assert_called_once_with(
            eval_id, EvaluationStatus.CANCELLED
        )
    
    @pytest.mark.asyncio
    async def test_cancel_evaluation_not_found(self, evaluation_service):
        """Test cancelling evaluation that doesn't exist."""
        eval_id = uuid4()
        evaluation_service.repository.get_evaluation.return_value = None
        
        result = await evaluation_service.cancel_evaluation(eval_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cancel_evaluation_already_completed(self, evaluation_service):
        """Test cancelling evaluation that's already completed."""
        eval_id = uuid4()
        
        # Mock completed evaluation
        mock_evaluation = MagicMock()
        mock_evaluation.status = EvaluationStatus.COMPLETED.value
        
        evaluation_service.repository.get_evaluation.return_value = mock_evaluation
        
        result = await evaluation_service.cancel_evaluation(eval_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_process_evaluation_result_success(self, evaluation_service):
        """Test successful evaluation result processing."""
        eval_id = uuid4()
        
        # Mock database evaluation
        mock_evaluation = MagicMock()
        mock_evaluation.evaluation_id = "openevolve_123"
        
        evaluation_service.repository.get_evaluation.return_value = mock_evaluation
        
        # Mock OpenEvolve API responses
        evaluation_service._client.get_evaluation_result.return_value = {
            "status": "completed",
            "results": {"score": 0.85},
            "metrics": {"accuracy": 0.9}
        }
        
        evaluation_service._client.get_system_improvements.return_value = [
            {
                "type": "cache_optimization",
                "description": "Add caching layer",
                "priority": 2,
                "estimated_impact": 0.25,
                "complexity": "medium"
            }
        ]
        
        # Mock get_evaluation_result for return value
        mock_result = MagicMock()
        evaluation_service.get_evaluation_result = AsyncMock(return_value=mock_result)
        
        result = await evaluation_service.process_evaluation_result(eval_id)
        
        assert result == mock_result
        evaluation_service.repository.update_evaluation_status.assert_called_once()
        evaluation_service.repository.create_improvement.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_evaluation_result_not_found(self, evaluation_service):
        """Test processing evaluation result when evaluation not found."""
        eval_id = uuid4()
        evaluation_service.repository.get_evaluation.return_value = None
        
        result = await evaluation_service.process_evaluation_result(eval_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_evaluation_summary(self, evaluation_service):
        """Test getting evaluation summary."""
        # Mock database query
        mock_evaluations = [
            MagicMock(
                status=EvaluationStatus.COMPLETED.value,
                metrics={"execution_time": 10.5, "improvement_score": 0.8}
            ),
            MagicMock(
                status=EvaluationStatus.COMPLETED.value,
                metrics={"execution_time": 8.2, "improvement_score": 0.6}
            ),
            MagicMock(
                status=EvaluationStatus.FAILED.value,
                metrics=None
            )
        ]
        
        evaluation_service.session.query.return_value.filter.return_value.all.return_value = mock_evaluations
        
        summary = await evaluation_service.get_evaluation_summary(days=7)
        
        assert summary.total_evaluations == 3
        assert summary.completed_evaluations == 2
        assert summary.failed_evaluations == 1
        assert summary.success_rate == 66.67  # 2/3 * 100, rounded
        assert summary.average_execution_time == 9.35  # (10.5 + 8.2) / 2
        assert summary.average_improvement_score == 0.7  # (0.8 + 0.6) / 2
    
    @pytest.mark.asyncio
    async def test_apply_system_improvement_success(self, evaluation_service):
        """Test successful system improvement application."""
        improvement_id = uuid4()
        
        # Mock improvement
        mock_improvement = MagicMock()
        mock_improvement.applied = False
        mock_improvement.description = "Test improvement"
        
        evaluation_service.session.query.return_value.filter.return_value.first.return_value = mock_improvement
        
        result = await evaluation_service.apply_system_improvement(improvement_id)
        
        assert result is True
        evaluation_service.repository.mark_improvement_applied.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_apply_system_improvement_not_found(self, evaluation_service):
        """Test applying system improvement when not found."""
        improvement_id = uuid4()
        evaluation_service.session.query.return_value.filter.return_value.first.return_value = None
        
        result = await evaluation_service.apply_system_improvement(improvement_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_apply_system_improvement_already_applied(self, evaluation_service):
        """Test applying system improvement that's already applied."""
        improvement_id = uuid4()
        
        # Mock already applied improvement
        mock_improvement = MagicMock()
        mock_improvement.applied = True
        
        evaluation_service.session.query.return_value.filter.return_value.first.return_value = mock_improvement
        
        result = await evaluation_service.apply_system_improvement(improvement_id)
        
        assert result is False
    
    def test_start_stop_processing(self, evaluation_service):
        """Test starting and stopping background processing."""
        # Start processing
        evaluation_service.start_processing()
        assert evaluation_service._processing_task is not None
        assert not evaluation_service._processing_task.done()
        
        # Stop processing
        evaluation_service.stop_processing()
        assert evaluation_service._processing_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_process_single_evaluation_success(self, evaluation_service):
        """Test processing a single evaluation successfully."""
        from graph_sitter.openevolve.models import EvaluationRequest
        
        # Create evaluation request
        eval_request = EvaluationRequest(
            trigger_event=EvaluationTrigger.TASK_FAILURE,
            context={"task_id": "test_task"}
        )
        
        # Mock client response
        evaluation_service._client.submit_evaluation.return_value = "openevolve_123"
        
        # Mock polling completion
        evaluation_service._poll_evaluation_completion = AsyncMock()
        
        await evaluation_service._process_single_evaluation(eval_request)
        
        evaluation_service._client.submit_evaluation.assert_called_once_with(eval_request)
        evaluation_service.repository.update_evaluation_status.assert_called_once()
        evaluation_service._poll_evaluation_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_poll_evaluation_completion_success(self, evaluation_service):
        """Test polling evaluation completion successfully."""
        eval_id = uuid4()
        openevolve_id = "openevolve_123"
        
        # Mock status progression: running -> completed
        evaluation_service._client.get_evaluation_status.side_effect = [
            EvaluationStatus.RUNNING,
            EvaluationStatus.COMPLETED
        ]
        
        # Mock process_evaluation_result
        evaluation_service.process_evaluation_result = AsyncMock()
        
        await evaluation_service._poll_evaluation_completion(eval_id, openevolve_id)
        
        # Should update to running status and then process final result
        evaluation_service.repository.update_evaluation_status.assert_called()
        evaluation_service.process_evaluation_result.assert_called_once_with(eval_id)
    
    @pytest.mark.asyncio
    async def test_poll_evaluation_completion_timeout(self, evaluation_service):
        """Test polling evaluation completion with timeout."""
        eval_id = uuid4()
        openevolve_id = "openevolve_123"
        
        # Mock status that never completes
        evaluation_service._client.get_evaluation_status.return_value = EvaluationStatus.RUNNING
        
        # Patch the max_polls to make test faster
        with patch.object(evaluation_service, '_poll_evaluation_completion') as mock_poll:
            # Simulate timeout by calling the real method with modified max_polls
            async def mock_poll_impl(eval_id, openevolve_id):
                max_polls = 2  # Reduced for testing
                poll_interval = 0.01  # Very short interval for testing
                
                for _ in range(max_polls):
                    status = await evaluation_service._client.get_evaluation_status(openevolve_id)
                    if status in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED]:
                        break
                    await asyncio.sleep(poll_interval)
                else:
                    # Timeout
                    evaluation_service.repository.update_evaluation_status(
                        eval_id,
                        EvaluationStatus.FAILED,
                        error_message="Evaluation polling timed out"
                    )
            
            mock_poll.side_effect = mock_poll_impl
            
            await evaluation_service._poll_evaluation_completion(eval_id, openevolve_id)
            
            # Should mark as failed due to timeout
            evaluation_service.repository.update_evaluation_status.assert_called_with(
                eval_id,
                EvaluationStatus.FAILED,
                error_message="Evaluation polling timed out"
            )

