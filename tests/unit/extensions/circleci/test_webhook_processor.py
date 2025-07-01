"""
Unit tests for CircleCI webhook processor
"""

import pytest
import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from graph_sitter.extensions.circleci.webhook_processor import (
    WebhookProcessor,
    WebhookValidationError,
    WebhookProcessingError
)
from graph_sitter.extensions.circleci.config import CircleCIIntegrationConfig, APIConfig, WebhookConfig
from graph_sitter.extensions.circleci.types import CircleCIEventType, BuildStatus

@pytest.fixture
def config():
    """Create test configuration"""
    api_config = APIConfig(api_token="test-token")
    webhook_config = WebhookConfig(
        webhook_secret="test-secret",
        validate_signatures=True,
        max_queue_size=10
    )
    return CircleCIIntegrationConfig(api=api_config, webhook=webhook_config)


@pytest.fixture
def webhook_processor(config):
    """Create webhook processor"""
    return WebhookProcessor(config)


@pytest.fixture
def sample_workflow_payload():
    """Sample workflow completed payload"""
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
def sample_job_payload():
    """Sample job completed payload"""
    return {
        "type": "job-completed",
        "id": "test-event-456",
        "happened_at": "2024-01-01T12:00:00Z",
        "job": {
            "id": "job-123",
            "name": "test-job",
            "project_slug": "gh/test-org/test-repo",
            "status": "failed",
            "started_at": "2024-01-01T11:55:00Z",
            "stopped_at": "2024-01-01T12:00:00Z",
            "web_url": "https://circleci.com/gh/test-org/test-repo/123",
            "exit_code": 1
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
def sample_ping_payload():
    """Sample ping payload"""
    return {
        "type": "ping",
        "id": "ping-123",
        "happened_at": "2024-01-01T12:00:00Z"
    }


class TestWebhookProcessor:
    """Test webhook processor functionality"""
    
    @pytest.mark.asyncio
    async def test_start_stop(self, webhook_processor):
        """Test starting and stopping the processor"""
        assert not webhook_processor.is_running
        
        await webhook_processor.start()
        assert webhook_processor.is_running
        
        await webhook_processor.stop()
        assert not webhook_processor.is_running
    
    def test_register_handler(self, webhook_processor):
        """Test registering event handlers"""
        handler = AsyncMock()
        
        webhook_processor.register_handler(
            handler=handler,
            event_type=CircleCIEventType.WORKFLOW_COMPLETED,
            name="test-handler"
        )
        
        assert len(webhook_processor.handlers) == 1
        assert webhook_processor.handlers[0].name == "test-handler"
        assert webhook_processor.handlers[0].event_type == CircleCIEventType.WORKFLOW_COMPLETED
    
    def test_unregister_handler(self, webhook_processor):
        """Test unregistering event handlers"""
        handler = AsyncMock()
        
        webhook_processor.register_handler(handler, name="test-handler")
        assert len(webhook_processor.handlers) == 1
        
        result = webhook_processor.unregister_handler("test-handler")
        assert result is True
        assert len(webhook_processor.handlers) == 0
        
        result = webhook_processor.unregister_handler("non-existent")
        assert result is False
    
    def test_handler_priority_sorting(self, webhook_processor):
        """Test handler priority sorting"""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        handler3 = AsyncMock()
        
        webhook_processor.register_handler(handler1, name="low", priority=1)
        webhook_processor.register_handler(handler2, name="high", priority=10)
        webhook_processor.register_handler(handler3, name="medium", priority=5)
        
        # Should be sorted by priority (high to low)
        assert webhook_processor.handlers[0].name == "high"
        assert webhook_processor.handlers[1].name == "medium"
        assert webhook_processor.handlers[2].name == "low"


class TestWebhookValidation:
    """Test webhook validation"""
    
    def create_signature(self, secret: str, body: str) -> str:
        """Create HMAC signature for testing"""
        return hmac.new(
            secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @pytest.mark.asyncio
    async def test_valid_signature(self, webhook_processor, sample_workflow_payload):
        """Test webhook with valid signature"""
        body = json.dumps(sample_workflow_payload)
        signature = self.create_signature("test-secret", body)
        
        headers = {
            "circleci-signature": f"sha256={signature}",
            "content-type": "application/json"
        }
        
        result = await webhook_processor.process_webhook(headers, body)
        assert result.success is True
        assert result.event_type == CircleCIEventType.WORKFLOW_COMPLETED
    
    @pytest.mark.asyncio
    async def test_invalid_signature(self, webhook_processor, sample_workflow_payload):
        """Test webhook with invalid signature"""
        body = json.dumps(sample_workflow_payload)
        
        headers = {
            "circleci-signature": "sha256=invalid-signature",
            "content-type": "application/json"
        }
        
        result = await webhook_processor.process_webhook(headers, body)
        assert result.success is False
        assert "Invalid webhook signature" in result.error
    
    @pytest.mark.asyncio
    async def test_missing_signature(self, webhook_processor, sample_workflow_payload):
        """Test webhook with missing signature"""
        body = json.dumps(sample_workflow_payload)
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        assert result.success is False
        assert "Missing signature header" in result.error
    
    @pytest.mark.asyncio
    async def test_signature_validation_disabled(self, config, sample_workflow_payload):
        """Test webhook with signature validation disabled"""
        config.webhook.validate_signatures = False
        processor = WebhookProcessor(config)
        
        body = json.dumps(sample_workflow_payload)
        headers = {"content-type": "application/json"}
        
        result = await processor.process_webhook(headers, body)
        assert result.success is True


class TestWebhookPayloadProcessing:
    """Test webhook payload processing"""
    
    @pytest.mark.asyncio
    async def test_workflow_completed_payload(self, webhook_processor, sample_workflow_payload):
        """Test processing workflow completed payload"""
        # Disable signature validation for this test
        webhook_processor.config.webhook.validate_signatures = False
        
        body = json.dumps(sample_workflow_payload)
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        
        assert result.success is True
        assert result.event_type == CircleCIEventType.WORKFLOW_COMPLETED
        assert result.event_id == "test-event-123"
    
    @pytest.mark.asyncio
    async def test_job_completed_payload(self, webhook_processor, sample_job_payload):
        """Test processing job completed payload"""
        webhook_processor.config.webhook.validate_signatures = False
        
        body = json.dumps(sample_job_payload)
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        
        assert result.success is True
        assert result.event_type == CircleCIEventType.JOB_COMPLETED
        assert result.event_id == "test-event-456"
    
    @pytest.mark.asyncio
    async def test_ping_payload(self, webhook_processor, sample_ping_payload):
        """Test processing ping payload"""
        webhook_processor.config.webhook.validate_signatures = False
        
        body = json.dumps(sample_ping_payload)
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        
        assert result.success is True
        assert result.event_type == CircleCIEventType.PING
        assert result.event_id == "ping-123"
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, webhook_processor):
        """Test processing invalid JSON"""
        webhook_processor.config.webhook.validate_signatures = False
        
        body = "invalid json {"
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        
        assert result.success is False
        assert "Invalid JSON payload" in result.error
    
    @pytest.mark.asyncio
    async def test_missing_event_type(self, webhook_processor):
        """Test processing payload without event type"""
        webhook_processor.config.webhook.validate_signatures = False
        
        payload = {"id": "test", "happened_at": "2024-01-01T12:00:00Z"}
        body = json.dumps(payload)
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        
        assert result.success is False
        assert "Missing event type" in result.error
    
    @pytest.mark.asyncio
    async def test_unknown_event_type(self, webhook_processor):
        """Test processing payload with unknown event type"""
        webhook_processor.config.webhook.validate_signatures = False
        
        payload = {
            "type": "unknown-event",
            "id": "test",
            "happened_at": "2024-01-01T12:00:00Z"
        }
        body = json.dumps(payload)
        headers = {"content-type": "application/json"}
        
        result = await webhook_processor.process_webhook(headers, body)
        
        assert result.success is False
        assert "Unknown event type" in result.error


class TestEventProcessing:
    """Test event processing and handler execution"""
    
    @pytest.mark.asyncio
    async def test_event_handler_execution(self, webhook_processor, sample_workflow_payload):
        """Test that event handlers are executed"""
        webhook_processor.config.webhook.validate_signatures = False
        
        # Register handler
        handler = AsyncMock()
        webhook_processor.register_handler(
            handler=handler,
            event_type=CircleCIEventType.WORKFLOW_COMPLETED,
            name="test-handler"
        )
        
        # Start processor
        await webhook_processor.start()
        
        try:
            # Process webhook
            body = json.dumps(sample_workflow_payload)
            headers = {"content-type": "application/json"}
            
            result = await webhook_processor.process_webhook(headers, body)
            assert result.success is True
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify handler was called
            handler.assert_called_once()
            
        finally:
            await webhook_processor.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_handlers(self, webhook_processor, sample_workflow_payload):
        """Test multiple handlers for same event type"""
        webhook_processor.config.webhook.validate_signatures = False
        
        # Register multiple handlers
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        webhook_processor.register_handler(handler1, name="handler1")
        webhook_processor.register_handler(handler2, name="handler2")
        
        await webhook_processor.start()
        
        try:
            body = json.dumps(sample_workflow_payload)
            headers = {"content-type": "application/json"}
            
            result = await webhook_processor.process_webhook(headers, body)
            assert result.success is True
            
            await asyncio.sleep(0.1)
            
            # Both handlers should be called
            handler1.assert_called_once()
            handler2.assert_called_once()
            
        finally:
            await webhook_processor.stop()
    
    @pytest.mark.asyncio
    async def test_handler_exception(self, webhook_processor, sample_workflow_payload):
        """Test handler exception handling"""
        webhook_processor.config.webhook.validate_signatures = False
        
        # Register handler that raises exception
        async def failing_handler(event):
            raise ValueError("Handler failed")
        
        webhook_processor.register_handler(failing_handler, name="failing-handler")
        
        await webhook_processor.start()
        
        try:
            body = json.dumps(sample_workflow_payload)
            headers = {"content-type": "application/json"}
            
            result = await webhook_processor.process_webhook(headers, body)
            assert result.success is True  # Webhook processing should still succeed
            
            await asyncio.sleep(0.1)
            
            # Check stats for failed events
            stats = webhook_processor.get_stats()
            assert stats.events_failed > 0
            
        finally:
            await webhook_processor.stop()
    
    @pytest.mark.asyncio
    async def test_event_filtering(self, webhook_processor, sample_ping_payload):
        """Test event filtering (ping events)"""
        webhook_processor.config.webhook.validate_signatures = False
        webhook_processor.config.webhook.ignore_ping_events = True
        
        handler = AsyncMock()
        webhook_processor.register_handler(handler, name="test-handler")
        
        await webhook_processor.start()
        
        try:
            body = json.dumps(sample_ping_payload)
            headers = {"content-type": "application/json"}
            
            result = await webhook_processor.process_webhook(headers, body)
            assert result.success is True
            
            await asyncio.sleep(0.1)
            
            # Handler should not be called for ping events
            handler.assert_not_called()
            
        finally:
            await webhook_processor.stop()


class TestWebhookStats:
    """Test webhook statistics"""
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, webhook_processor, sample_workflow_payload):
        """Test statistics tracking"""
        webhook_processor.config.webhook.validate_signatures = False
        
        initial_stats = webhook_processor.get_stats()
        assert initial_stats.requests_total == 0
        assert initial_stats.events_processed == 0
        
        # Start the processor to enable background event processing
        await webhook_processor.start()
        
        try:
            body = json.dumps(sample_workflow_payload)
            headers = {"content-type": "application/json"}
            
            result = await webhook_processor.process_webhook(headers, body)
            assert result.success is True
            
            # Wait for background processing to complete
            await asyncio.sleep(0.1)
            
            updated_stats = webhook_processor.get_stats()
            assert updated_stats.requests_total == 1
            assert updated_stats.requests_successful == 1
            assert updated_stats.events_processed == 1
            assert updated_stats.workflow_events == 1
        finally:
            await webhook_processor.stop()
    
    @pytest.mark.asyncio
    async def test_failed_request_stats(self, webhook_processor):
        """Test failed request statistics"""
        webhook_processor.config.webhook.validate_signatures = False
        
        # Start the processor
        await webhook_processor.start()
        
        try:
            # Send invalid payload
            body = "invalid json"
            headers = {"content-type": "application/json"}
            
            result = await webhook_processor.process_webhook(headers, body)
            assert result.success is False
            
            stats = webhook_processor.get_stats()
            assert stats.requests_total == 1
            assert stats.requests_failed == 1
            assert stats.events_failed == 1
        finally:
            await webhook_processor.stop()

    def test_success_rate_calculation(self, webhook_processor):
        """Test success rate calculation"""
        stats = webhook_processor.get_stats()
        
        # No requests yet
        assert stats.success_rate == 0.0
        
        # Simulate some requests
        stats.requests_total = 10
        stats.requests_successful = 8
        
        assert stats.success_rate == 80.0


class TestWebhookUtilities:
    """Test webhook utility methods"""
    
    def test_get_queue_info(self, webhook_processor):
        """Test queue information"""
        info = webhook_processor.get_queue_info()
        
        assert "queue_size" in info
        assert "max_queue_size" in info
        assert "is_running" in info
        assert "handlers_registered" in info
        
        assert info["max_queue_size"] == 10
        assert info["is_running"] is False
        assert info["handlers_registered"] == 0
    
    def test_get_recent_events(self, webhook_processor):
        """Test getting recent events"""
        events = webhook_processor.get_recent_events()
        assert isinstance(events, list)
        assert len(events) == 0
    
    def test_get_handlers(self, webhook_processor):
        """Test getting handlers info"""
        handler = AsyncMock()
        webhook_processor.register_handler(
            handler=handler,
            event_type=CircleCIEventType.WORKFLOW_COMPLETED,
            name="test-handler",
            priority=5
        )
        
        handlers = webhook_processor.get_handlers()
        assert len(handlers) == 1
        assert handlers[0]["name"] == "test-handler"
        assert handlers[0]["event_type"] == "workflow-completed"
        assert handlers[0]["priority"] == 5
    
    @pytest.mark.asyncio
    async def test_health_check(self, webhook_processor):
        """Test health check"""
        health = await webhook_processor.health_check()
        
        assert "healthy" in health
        assert "queue_size" in health
        assert "handlers_count" in health
        assert "stats" in health
        
        assert health["healthy"] is False  # Not running
        assert health["handlers_count"] == 0
