"""
Basic tests for the Codegen SDK.

This module contains simple tests to verify the SDK functionality.
Run with: python -m pytest test_basic.py
"""

import pytest
from unittest.mock import Mock, patch
import json

from .agent import Agent
from .task import Task
from .config import Config
from .exceptions import (
    CodegenError, 
    AuthenticationError, 
    TaskError, 
    ValidationError
)
from .utils import (
    validate_org_id,
    validate_repository,
    sanitize_prompt,
    format_duration
)


class TestUtils:
    """Test utility functions."""
    
    def test_validate_org_id(self):
        """Test organization ID validation."""
        assert validate_org_id("valid-org-123") == True
        assert validate_org_id("valid_org_123") == True
        assert validate_org_id("") == False
        assert validate_org_id(None) == False
        assert validate_org_id("invalid org") == False
        assert validate_org_id("invalid@org") == False
    
    def test_validate_repository(self):
        """Test repository validation."""
        assert validate_repository("owner/repo") == True
        assert validate_repository("my-org/my-repo") == True
        assert validate_repository("") == False
        assert validate_repository(None) == False
        assert validate_repository("invalid") == False
        assert validate_repository("owner/") == False
        assert validate_repository("/repo") == False
    
    def test_sanitize_prompt(self):
        """Test prompt sanitization."""
        assert sanitize_prompt("  hello   world  ") == "hello world"
        assert sanitize_prompt("") == ""
        assert sanitize_prompt(None) == ""
        
        # Test length limiting
        long_prompt = "a" * 15000
        sanitized = sanitize_prompt(long_prompt)
        assert len(sanitized) <= 10003  # 10000 + "..."
        assert sanitized.endswith("...")
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(30) == "30.0s"
        assert format_duration(90) == "1.5m"
        assert format_duration(3900) == "1.1h"


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test config initialization."""
        config = Config()
        assert hasattr(config, 'org_id')
        assert hasattr(config, 'token')
        assert hasattr(config, 'base_url')
        assert config.base_url == "https://api.codegen.com"
    
    def test_config_validation(self):
        """Test config validation."""
        config = Config()
        config.org_id = "test-org"
        config.token = "test-token"
        assert config.is_valid() == True
        
        config.token = None
        assert config.is_valid() == False
    
    def test_config_to_dict(self):
        """Test config serialization."""
        config = Config()
        config.org_id = "test-org"
        config.token = "secret-token"
        
        data = config.to_dict()
        assert data["org_id"] == "test-org"
        assert data["token"] == "***"  # Should be masked


class TestTask:
    """Test task functionality."""
    
    def test_task_initialization(self):
        """Test task initialization."""
        mock_agent = Mock()
        task_data = {
            "status": "pending",
            "prompt": "Test prompt",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        task = Task("task-123", mock_agent, task_data)
        assert task.task_id == "task-123"
        assert task.status == "pending"
        assert task.prompt == "Test prompt"
    
    def test_task_properties(self):
        """Test task properties."""
        mock_agent = Mock()
        task_data = {
            "status": "completed",
            "result": "Task completed successfully",
            "error": None,
            "progress": {"step": 1, "total": 3},
            "metadata": {"priority": "high"}
        }
        
        task = Task("task-123", mock_agent, task_data)
        assert task.status == "completed"
        assert task.result == "Task completed successfully"
        assert task.error is None
        assert task.progress == {"step": 1, "total": 3}
        assert task.metadata == {"priority": "high"}
    
    def test_task_to_dict(self):
        """Test task serialization."""
        mock_agent = Mock()
        task_data = {
            "status": "completed",
            "result": "Success",
            "prompt": "Test prompt"
        }
        
        task = Task("task-123", mock_agent, task_data)
        data = task.to_dict()
        
        assert data["task_id"] == "task-123"
        assert data["status"] == "completed"
        assert data["result"] == "Success"
        assert data["prompt"] == "Test prompt"


class TestAgent:
    """Test agent functionality."""
    
    def test_agent_initialization_validation(self):
        """Test agent initialization validation."""
        # Valid initialization
        with patch.object(Agent, '_validate_credentials'):
            agent = Agent(org_id="test-org", token="test-token")
            assert agent.org_id == "test-org"
            assert agent.token == "test-token"
        
        # Invalid org_id
        with pytest.raises(ValidationError):
            Agent(org_id="", token="test-token")
        
        # Invalid token
        with pytest.raises(ValidationError):
            Agent(org_id="test-org", token="")
    
    @patch('requests.Session.request')
    def test_agent_make_request(self, mock_request):
        """Test agent request making."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response
        
        with patch.object(Agent, '_validate_credentials'):
            agent = Agent(org_id="test-org", token="test-token")
            response = agent._make_request("GET", "/test")
            
            assert response.status_code == 200
            mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_agent_run_task(self, mock_request):
        """Test running a task."""
        # Mock successful task creation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "task-123",
            "status": "pending",
            "prompt": "Test prompt"
        }
        mock_request.return_value = mock_response
        
        with patch.object(Agent, '_validate_credentials'):
            agent = Agent(org_id="test-org", token="test-token")
            task = agent.run(prompt="Test prompt")
            
            assert isinstance(task, Task)
            assert task.task_id == "task-123"
            assert task.status == "pending"
    
    def test_agent_run_validation(self):
        """Test task run validation."""
        with patch.object(Agent, '_validate_credentials'):
            agent = Agent(org_id="test-org", token="test-token")
            
            # Empty prompt should raise ValidationError
            with pytest.raises(ValidationError):
                agent.run(prompt="")
            
            # Invalid priority should raise ValidationError
            with pytest.raises(ValidationError):
                agent.run(prompt="Test", priority="invalid")


class TestExceptions:
    """Test exception classes."""
    
    def test_codegen_error(self):
        """Test base CodegenError."""
        error = CodegenError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert isinstance(error, CodegenError)
    
    def test_task_error(self):
        """Test TaskError."""
        error = TaskError("Task failed")
        assert str(error) == "Task failed"
        assert isinstance(error, CodegenError)
    
    def test_api_error(self):
        """Test APIError with additional data."""
        from .exceptions import APIError
        
        error = APIError("API error", status_code=400, response_data={"error": "Bad request"})
        assert str(error) == "API error"
        assert error.status_code == 400
        assert error.response_data == {"error": "Bad request"}


if __name__ == "__main__":
    """Run tests when script is executed directly."""
    pytest.main([__file__, "-v"])

