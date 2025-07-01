"""Unit tests for AutogenClient."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.codegen.autogenlib.client import AutogenClient
from src.codegen.autogenlib.config import AutogenConfig
from src.codegen.autogenlib.models import TaskRequest, TaskStatus
from src.codegen.autogenlib.exceptions import ConfigurationError, AuthenticationError


class TestAutogenClient:
    """Test cases for AutogenClient."""
    
    def test_init_with_config(self):
        """Test client initialization with config."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        assert client.config == config
        assert client._agent is None
    
    def test_init_without_config(self):
        """Test client initialization without config."""
        with patch('src.codegen.autogenlib.client.get_config') as mock_get_config:
            mock_config = AutogenConfig(org_id="test_org", token="test_token")
            mock_get_config.return_value = mock_config
            
            client = AutogenClient()
            
            assert client.config == mock_config
    
    def test_validate_config_missing_org_id(self):
        """Test config validation with missing org_id."""
        config = AutogenConfig(org_id="", token="test_token")
        
        with pytest.raises(ConfigurationError, match="org_id is required"):
            AutogenClient(config)
    
    def test_validate_config_missing_token(self):
        """Test config validation with missing token."""
        config = AutogenConfig(org_id="test_org", token="")
        
        with pytest.raises(ConfigurationError, match="token is required"):
            AutogenClient(config)
    
    @patch('src.codegen.autogenlib.client.Agent')
    def test_agent_property_success(self, mock_agent_class):
        """Test successful agent property access."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        agent = client.agent
        
        assert agent == mock_agent
        mock_agent_class.assert_called_once_with(
            org_id="test_org",
            token="test_token",
            base_url="https://api.codegen.com"
        )
    
    @patch('src.codegen.autogenlib.client.Agent')
    def test_agent_property_failure(self, mock_agent_class):
        """Test agent property access failure."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        mock_agent_class.side_effect = Exception("Authentication failed")
        
        with pytest.raises(AuthenticationError, match="Failed to authenticate with Codegen"):
            _ = client.agent
    
    @patch('src.codegen.autogenlib.client.Agent')
    def test_run_task_success(self, mock_agent_class):
        """Test successful task execution."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        # Mock agent and task
        mock_agent = Mock()
        mock_task = Mock()
        mock_task.status = "completed"
        mock_task.result = "Task completed successfully"
        mock_task.refresh = Mock()
        
        mock_agent.run.return_value = mock_task
        mock_agent_class.return_value = mock_agent
        
        # Create request
        request = TaskRequest(prompt="Test prompt")
        
        # Run task
        response = client.run_task(request)
        
        # Verify response
        assert response.status == TaskStatus.COMPLETED
        assert response.result == "Task completed successfully"
        assert response.error is None
        
        # Verify agent was called
        mock_agent.run.assert_called_once_with(prompt="Test prompt")
    
    @patch('src.codegen.autogenlib.client.Agent')
    def test_run_task_failure(self, mock_agent_class):
        """Test task execution failure."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        # Mock agent and task
        mock_agent = Mock()
        mock_task = Mock()
        mock_task.status = "failed"
        mock_task.error = "Task failed"
        mock_task.refresh = Mock()
        
        mock_agent.run.return_value = mock_task
        mock_agent_class.return_value = mock_agent
        
        # Create request
        request = TaskRequest(prompt="Test prompt")
        
        # Run task
        response = client.run_task(request)
        
        # Verify response
        assert response.status == TaskStatus.FAILED
        assert response.result is None
        assert response.error == "Task failed"
    
    @patch('src.codegen.autogenlib.client.Agent')
    @pytest.mark.asyncio
    async def test_run_task_async(self, mock_agent_class):
        """Test async task execution."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        # Mock agent and task
        mock_agent = Mock()
        mock_task = Mock()
        mock_task.status = "completed"
        mock_task.result = "Task completed successfully"
        mock_task.refresh = Mock()
        
        mock_agent.run.return_value = mock_task
        mock_agent_class.return_value = mock_agent
        
        # Create request
        request = TaskRequest(prompt="Test prompt")
        
        # Run task async
        response = await client.run_task_async(request)
        
        # Verify response
        assert response.status == TaskStatus.COMPLETED
        assert response.result == "Task completed successfully"
    
    def test_health_check_healthy(self):
        """Test health check when client is healthy."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        with patch.object(client, 'agent', Mock()):
            health = client.health_check()
            
            assert health["status"] == "healthy"
            assert health["org_id"] == "test_org"
            assert "timestamp" in health
            assert "usage_stats" in health
    
    def test_health_check_unhealthy(self):
        """Test health check when client is unhealthy."""
        config = AutogenConfig(org_id="test_org", token="test_token")
        client = AutogenClient(config)
        
        with patch.object(client, 'agent', side_effect=Exception("Connection failed")):
            health = client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "Connection failed" in health["error"]
            assert "timestamp" in health

