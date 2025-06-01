"""Unit tests for OpenEvolve client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import aiohttp

from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from graph_sitter.openevolve.client import OpenEvolveClient, OpenEvolveAPIError
from graph_sitter.openevolve.models import EvaluationRequest, EvaluationStatus, EvaluationTrigger


@pytest.fixture
def config():
    """Create test configuration."""
    return OpenEvolveConfig(
        api_url="https://test.openevolve.com",
        api_key="test_api_key",
        timeout=5000,
        max_retries=2
    )


@pytest.fixture
def evaluation_request():
    """Create test evaluation request."""
    return EvaluationRequest(
        trigger_event=EvaluationTrigger.TASK_FAILURE,
        context={"task_id": "test_task"},
        priority=3
    )


class TestOpenEvolveClient:
    """Test cases for OpenEvolveClient."""
    
    def test_init_with_valid_config(self, config):
        """Test client initialization with valid config."""
        client = OpenEvolveClient(config)
        assert client.config == config
        assert client._session is None
    
    def test_init_without_api_key(self):
        """Test client initialization without API key."""
        config = OpenEvolveConfig(api_key=None)
        
        with pytest.raises(ValueError, match="OpenEvolve API key is required"):
            OpenEvolveClient(config)
    
    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        """Test async context manager."""
        async with OpenEvolveClient(config) as client:
            assert client._session is not None
            assert not client._session.closed
        
        # Session should be closed after exiting context
        assert client._session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, config):
        """Test session creation."""
        client = OpenEvolveClient(config)
        
        await client._ensure_session()
        
        assert client._session is not None
        assert not client._session.closed
        
        # Check headers
        headers = client._session._default_headers
        assert headers["Authorization"] == f"Bearer {config.api_key}"
        assert headers["Content-Type"] == "application/json"
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, config):
        """Test successful API request."""
        client = OpenEvolveClient(config)
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content_type = 'application/json'
        mock_response.json.return_value = {"result": "success"}
        
        mock_session = AsyncMock()
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        client._session = mock_session
        
        result = await client._make_request("GET", "/test")
        
        assert result == {"result": "success"}
        mock_session.request.assert_called_once()
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, config):
        """Test API request with HTTP error."""
        client = OpenEvolveClient(config)
        
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.content_type = 'application/json'
        mock_response.json.return_value = {"error": "Bad request"}
        
        mock_session = AsyncMock()
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        client._session = mock_session
        
        with pytest.raises(OpenEvolveAPIError) as exc_info:
            await client._make_request("GET", "/test")
        
        assert exc_info.value.status_code == 400
        assert "Bad request" in str(exc_info.value)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_make_request_client_error(self, config):
        """Test API request with client error."""
        client = OpenEvolveClient(config)
        
        # Mock client error
        mock_session = AsyncMock()
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
        
        client._session = mock_session
        
        with pytest.raises(OpenEvolveAPIError, match="Request failed"):
            await client._make_request("GET", "/test")
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_submit_evaluation_success(self, config, evaluation_request):
        """Test successful evaluation submission."""
        client = OpenEvolveClient(config)
        
        # Mock successful response
        mock_response = {"evaluation_id": "eval_123"}
        
        with patch.object(client, '_make_request', return_value=mock_response) as mock_request:
            result = await client.submit_evaluation(evaluation_request)
            
            assert result == "eval_123"
            mock_request.assert_called_once_with(
                "POST", 
                "/evaluations", 
                data={
                    "id": str(evaluation_request.id),
                    "trigger_event": evaluation_request.trigger_event,
                    "context": evaluation_request.context,
                    "metadata": evaluation_request.metadata,
                    "priority": evaluation_request.priority,
                    "timeout": evaluation_request.timeout
                }
            )
    
    @pytest.mark.asyncio
    async def test_submit_evaluation_no_id(self, config, evaluation_request):
        """Test evaluation submission without returned ID."""
        client = OpenEvolveClient(config)
        
        # Mock response without evaluation_id
        mock_response = {"status": "submitted"}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            with pytest.raises(OpenEvolveAPIError, match="No evaluation ID returned"):
                await client.submit_evaluation(evaluation_request)
    
    @pytest.mark.asyncio
    async def test_get_evaluation_result(self, config):
        """Test getting evaluation result."""
        client = OpenEvolveClient(config)
        
        evaluation_id = "eval_123"
        mock_response = {
            "id": evaluation_id,
            "status": "completed",
            "results": {"score": 0.85}
        }
        
        with patch.object(client, '_make_request', return_value=mock_response) as mock_request:
            result = await client.get_evaluation_result(evaluation_id)
            
            assert result == mock_response
            mock_request.assert_called_once_with("GET", f"/evaluations/{evaluation_id}")
    
    @pytest.mark.asyncio
    async def test_get_evaluation_status(self, config):
        """Test getting evaluation status."""
        client = OpenEvolveClient(config)
        
        evaluation_id = "eval_123"
        mock_response = {"status": "running"}
        
        with patch.object(client, '_make_request', return_value=mock_response) as mock_request:
            status = await client.get_evaluation_status(evaluation_id)
            
            assert status == EvaluationStatus.RUNNING
            mock_request.assert_called_once_with("GET", f"/evaluations/{evaluation_id}/status")
    
    @pytest.mark.asyncio
    async def test_get_evaluation_status_unknown(self, config):
        """Test getting unknown evaluation status."""
        client = OpenEvolveClient(config)
        
        evaluation_id = "eval_123"
        mock_response = {"status": "unknown_status"}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            status = await client.get_evaluation_status(evaluation_id)
            
            assert status == EvaluationStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_cancel_evaluation_success(self, config):
        """Test successful evaluation cancellation."""
        client = OpenEvolveClient(config)
        
        evaluation_id = "eval_123"
        
        with patch.object(client, '_make_request', return_value={}) as mock_request:
            result = await client.cancel_evaluation(evaluation_id)
            
            assert result is True
            mock_request.assert_called_once_with("DELETE", f"/evaluations/{evaluation_id}")
    
    @pytest.mark.asyncio
    async def test_cancel_evaluation_failure(self, config):
        """Test failed evaluation cancellation."""
        client = OpenEvolveClient(config)
        
        evaluation_id = "eval_123"
        
        with patch.object(client, '_make_request', side_effect=OpenEvolveAPIError("Not found")):
            result = await client.cancel_evaluation(evaluation_id)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_list_evaluations(self, config):
        """Test listing evaluations."""
        client = OpenEvolveClient(config)
        
        mock_response = {
            "evaluations": [
                {"id": "eval_1", "status": "completed"},
                {"id": "eval_2", "status": "running"}
            ]
        }
        
        with patch.object(client, '_make_request', return_value=mock_response) as mock_request:
            result = await client.list_evaluations(
                status=EvaluationStatus.COMPLETED,
                limit=10,
                offset=5
            )
            
            assert len(result) == 2
            assert result[0]["id"] == "eval_1"
            
            mock_request.assert_called_once_with(
                "GET", 
                "/evaluations", 
                params={
                    "limit": 10,
                    "offset": 5,
                    "status": "completed"
                }
            )
    
    @pytest.mark.asyncio
    async def test_get_system_improvements(self, config):
        """Test getting system improvements."""
        client = OpenEvolveClient(config)
        
        evaluation_id = "eval_123"
        mock_response = {
            "improvements": [
                {
                    "type": "cache_optimization",
                    "description": "Add caching layer",
                    "priority": 2
                }
            ]
        }
        
        with patch.object(client, '_make_request', return_value=mock_response) as mock_request:
            result = await client.get_system_improvements(evaluation_id)
            
            assert len(result) == 1
            assert result[0]["type"] == "cache_optimization"
            
            mock_request.assert_called_once_with("GET", f"/evaluations/{evaluation_id}/improvements")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, config):
        """Test successful health check."""
        client = OpenEvolveClient(config)
        
        with patch.object(client, '_make_request', return_value={"status": "healthy"}):
            result = await client.health_check()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, config):
        """Test failed health check."""
        client = OpenEvolveClient(config)
        
        with patch.object(client, '_make_request', side_effect=OpenEvolveAPIError("Service unavailable")):
            result = await client.health_check()
            
            assert result is False


class TestOpenEvolveAPIError:
    """Test cases for OpenEvolveAPIError."""
    
    def test_init_basic(self):
        """Test basic error initialization."""
        error = OpenEvolveAPIError("Test error")
        
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data is None
    
    def test_init_with_details(self):
        """Test error initialization with details."""
        response_data = {"error": "Invalid request", "code": "E001"}
        error = OpenEvolveAPIError("Test error", status_code=400, response_data=response_data)
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.response_data == response_data

