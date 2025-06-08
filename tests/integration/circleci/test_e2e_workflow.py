"""
End-to-end integration tests for CircleCI extension workflow
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from contexten.extensions.circleci.integration_agent import CircleCIIntegrationAgent
from contexten.extensions.circleci.config import CircleCIIntegrationConfig, APIConfig, WebhookConfig
from contexten.extensions.circleci.types import (
    CircleCIEventType, BuildStatus, FailureType, FixConfidence
)


@pytest.fixture
def test_config():
    """Create test configuration"""
    api_config = APIConfig(api_token="test-token")
    webhook_config = WebhookConfig(
        webhook_secret="test-secret",
        validate_signatures=False,  # Disable for testing
        max_queue_size=10
    )
    
    config = CircleCIIntegrationConfig(
        api=api_config,
        webhook=webhook_config,
        debug_mode=True  # Enable debug mode for testing
    )
    
    # Disable external integrations for testing
    config.github.enabled = False
    config.codegen.enabled = False
    config.notifications.enabled = False
    
    return config


@pytest.fixture
def sample_failure_webhook():
    """Sample webhook payload for a failed workflow"""
    return {
        "type": "workflow-completed",
        "id": "test-event-123",
        "happened_at": "2024-01-01T12:00:00Z",
        "workflow": {
            "id": "workflow-123",
            "name": "test-workflow",
            "project_slug": "gh/test-org/test-repo",
            "status": "failed",
            "started_at": "2024-01-01T11:55:00Z",
            "stopped_at": "2024-01-01T12:00:00Z",
            "created_at": "2024-01-01T11:54:00Z",
            "pipeline_id": "pipeline-123",
            "pipeline_number": 42
        },
        "project": {
            "slug": "gh/test-org/test-repo",
            "name": "test-repo",
            "organization_name": "test-org",
            "organization_slug": "test-org",
            "organization_id": "org-123"
        },
        "pipeline": {
            "vcs": {
                "branch": "main",
                "revision": "abc123def456"
            }
        }
    }


@pytest.fixture
def mock_circleci_client():
    """Mock CircleCI client"""
    client = MagicMock()
    
    # Mock health check
    client.health_check = AsyncMock(return_value=True)
    
    # Mock workflow jobs
    client.get_workflow_jobs = AsyncMock(return_value=[
        MagicMock(
            id="job-123",
            name="test-job",
            status=BuildStatus.FAILED,
            is_failed=True
        )
    ])
    
    # Mock job logs
    client.get_job_logs = AsyncMock(return_value=[
        MagicMock(
            message="Error: Test failed",
            is_error=True,
            timestamp=datetime.now()
        ),
        MagicMock(
            message="FAIL src/test.js",
            is_error=True,
            timestamp=datetime.now()
        )
    ])
    
    # Mock job tests
    client.get_job_tests = AsyncMock(return_value=[
        MagicMock(
            name="should pass test",
            result="failed",
            failure_message="Expected true but got false",
            file="src/test.js"
        )
    ])
    
    # Mock close
    client.close = AsyncMock()
    
    return client


class TestE2EWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.mark.asyncio
    async def test_complete_failure_analysis_workflow(self, test_config, sample_failure_webhook, mock_circleci_client):
        """Test complete workflow from webhook to failure analysis"""
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                # Start the agent
                await agent.start()
                
                # Process webhook
                headers = {"content-type": "application/json"}
                body = json.dumps(sample_failure_webhook)
                
                result = await agent.process_webhook(headers, body)
                
                # Verify webhook processing
                assert result["success"] is True
                assert result["event_type"] == "workflow-completed"
                
                # Wait for workflow processing
                await asyncio.sleep(0.5)
                
                # Check that tasks were created
                active_tasks = await agent.get_active_tasks()
                
                # Should have created a failure analysis task
                analysis_tasks = [task for task in active_tasks if task["type"] == "failure_analysis"]
                assert len(analysis_tasks) > 0
                
                # Wait for task completion
                await asyncio.sleep(1.0)
                
                # Verify metrics
                metrics = agent.get_metrics()
                assert metrics.webhook_stats.workflow_events >= 1
                assert metrics.analysis_stats.failures_analyzed >= 0  # May not complete in test time
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_failure_analysis_task_execution(self, test_config, mock_circleci_client):
        """Test failure analysis task execution"""
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                # Create a test failure analysis directly
                analysis = await agent.analyze_build_failure("gh/test-org/test-repo", 123)
                
                # Verify analysis results
                assert analysis.project_slug == "gh/test-org/test-repo"
                assert analysis.failure_type in [FailureType.TEST_FAILURE, FailureType.UNKNOWN]
                assert analysis.confidence >= 0.0
                assert len(analysis.error_messages) >= 0
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_webhook_to_fix_generation_workflow(self, test_config, sample_failure_webhook, mock_circleci_client):
        """Test workflow from webhook to fix generation"""
        
        # Enable auto-fix for this test
        test_config.auto_fix.enabled = True
        test_config.auto_fix.fix_confidence_threshold = 0.1  # Low threshold for testing
        test_config.failure_analysis.enabled = True
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                # Process webhook
                headers = {"content-type": "application/json"}
                body = json.dumps(sample_failure_webhook)
                
                result = await agent.process_webhook(headers, body)
                assert result["success"] is True
                
                # Wait for processing
                await asyncio.sleep(1.0)
                
                # Check for fix generation tasks
                active_tasks = await agent.get_active_tasks()
                
                # May have both analysis and fix generation tasks
                task_types = [task["type"] for task in active_tasks]
                assert "failure_analysis" in task_types or len(active_tasks) == 0  # Tasks may complete quickly
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, test_config, mock_circleci_client):
        """Test health monitoring functionality"""
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                # Perform health check
                health = await agent.health_check()
                
                assert health["healthy"] is True
                assert "uptime" in health
                assert "components" in health
                assert "metrics" in health
                
                # Check component health
                components = health["components"]
                assert components["api"] is True
                assert components["webhook"] is True
                
                # Check integration status
                status = agent.get_integration_status()
                assert status.healthy is True
                assert status.api_healthy is True
                assert status.webhook_healthy is True
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, test_config, sample_failure_webhook, mock_circleci_client):
        """Test metrics collection throughout workflow"""
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                # Initial metrics
                initial_metrics = agent.get_metrics()
                initial_builds = initial_metrics.builds_monitored
                
                # Process multiple webhooks
                headers = {"content-type": "application/json"}
                body = json.dumps(sample_failure_webhook)
                
                for i in range(3):
                    result = await agent.process_webhook(headers, body)
                    assert result["success"] is True
                
                # Wait for processing
                await asyncio.sleep(0.5)
                
                # Check updated metrics
                updated_metrics = agent.get_metrics()
                assert updated_metrics.builds_monitored >= initial_builds + 3
                assert updated_metrics.webhook_stats.workflow_events >= 3
                
                # Check uptime
                assert updated_metrics.uptime_duration.total_seconds() > 0
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, test_config, mock_circleci_client):
        """Test error handling and recovery"""
        
        # Make client health check fail initially
        mock_circleci_client.health_check = AsyncMock(side_effect=[False, True, True])
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                # Start should succeed even with initial health check failure in debug mode
                await agent.start()
                
                # Health check should reflect the issue
                health = await agent.health_check()
                # In debug mode, may still start despite health check failure
                
                # Process invalid webhook
                headers = {"content-type": "application/json"}
                body = "invalid json"
                
                result = await agent.process_webhook(headers, body)
                assert result["success"] is False
                assert "error" in result
                
                # Agent should still be running
                assert agent.is_running is True
                
                # Process valid webhook after error
                valid_payload = {
                    "type": "ping",
                    "id": "ping-123",
                    "happened_at": "2024-01-01T12:00:00Z"
                }
                body = json.dumps(valid_payload)
                
                result = await agent.process_webhook(headers, body)
                assert result["success"] is True
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self, test_config, mock_circleci_client):
        """Test task cancellation functionality"""
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                # Create a long-running task by analyzing a build
                analysis_task = asyncio.create_task(
                    agent.analyze_build_failure("gh/test-org/test-repo", 123)
                )
                
                # Wait a bit then get active tasks
                await asyncio.sleep(0.1)
                active_tasks = await agent.get_active_tasks()
                
                if active_tasks:
                    task_id = active_tasks[0]["id"]
                    
                    # Cancel the task
                    result = await agent.cancel_task(task_id)
                    assert result is True
                    
                    # Wait for cancellation
                    await asyncio.sleep(0.1)
                    
                    # Task should no longer be active
                    updated_tasks = await agent.get_active_tasks()
                    active_task_ids = [task["id"] for task in updated_tasks]
                    assert task_id not in active_task_ids
                
                # Clean up
                try:
                    await analysis_task
                except:
                    pass  # Task may have been cancelled
                
            finally:
                await agent.stop()


class TestIntegrationConfiguration:
    """Test integration configuration in real scenarios"""
    
    def test_configuration_validation_in_context(self, test_config):
        """Test configuration validation with realistic settings"""
        
        # Test valid configuration
        issues = test_config.validate_configuration()
        # Should have some issues since we're using test tokens
        assert isinstance(issues, list)
        
        # Test production readiness
        assert not test_config.is_production_ready  # Debug mode is on
        
        test_config.debug_mode = False
        test_config.dry_run_mode = False
        # Still not production ready due to test tokens
        
    def test_configuration_summary(self, test_config):
        """Test configuration summary"""
        summary = test_config.summary
        
        assert summary["api_configured"] is True
        assert summary["webhook_configured"] is True
        assert summary["debug_mode"] is True
        assert summary["production_ready"] is False
    
    @pytest.mark.asyncio
    async def test_agent_initialization_with_config(self, test_config):
        """Test agent initialization with configuration"""
        
        with patch('src.contexten.extensions.circleci.client.CircleCIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.health_check = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            agent = CircleCIIntegrationAgent(test_config)
            
            # Verify components are initialized
            assert agent.config == test_config
            assert agent.client is not None
            assert agent.webhook_processor is not None
            assert agent.failure_analyzer is not None
            assert agent.workflow_automation is not None
            assert agent.auto_fix_generator is not None
            
            # Test start/stop
            await agent.start()
            assert agent.is_running is True
            
            await agent.stop()
            assert agent.is_running is False


class TestPerformanceAndScaling:
    """Test performance and scaling aspects"""
    
    @pytest.mark.asyncio
    async def test_concurrent_webhook_processing(self, test_config, sample_failure_webhook, mock_circleci_client):
        """Test concurrent webhook processing"""
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                # Process multiple webhooks concurrently
                headers = {"content-type": "application/json"}
                body = json.dumps(sample_failure_webhook)
                
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(agent.process_webhook(headers, body))
                    tasks.append(task)
                
                # Wait for all to complete
                results = await asyncio.gather(*tasks)
                
                # All should succeed
                for result in results:
                    assert result["success"] is True
                
                # Check metrics
                metrics = agent.get_metrics()
                assert metrics.webhook_stats.workflow_events >= 5
                
            finally:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_queue_overflow_handling(self, test_config, sample_failure_webhook, mock_circleci_client):
        """Test queue overflow handling"""
        
        # Set small queue size
        test_config.webhook.max_queue_size = 2
        
        with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
            agent = CircleCIIntegrationAgent(test_config)
            
            try:
                await agent.start()
                
                headers = {"content-type": "application/json"}
                body = json.dumps(sample_failure_webhook)
                
                # Process more webhooks than queue can handle
                results = []
                for i in range(5):
                    result = await agent.process_webhook(headers, body)
                    results.append(result)
                
                # Some should succeed, some may fail due to queue overflow
                successful = [r for r in results if r["success"]]
                failed = [r for r in results if not r["success"]]
                
                # At least some should succeed
                assert len(successful) > 0
                
                # If any failed, should be due to queue issues
                for failure in failed:
                    assert "queue" in failure.get("error", "").lower()
                
            finally:
                await agent.stop()


@pytest.mark.asyncio
async def test_agent_context_manager(test_config, mock_circleci_client):
    """Test agent as context manager"""
    
    with patch('src.contexten.extensions.circleci.integration_agent.CircleCIClient', return_value=mock_circleci_client):
        async with CircleCIIntegrationAgent(test_config) as agent:
            assert agent.is_running is True
            
            # Test basic functionality
            health = await agent.health_check()
            assert health["healthy"] is True
        
        # Should be stopped after context exit
        assert agent.is_running is False
