"""Tests for enhanced codebase AI functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from graph_sitter.ai.client_factory import AIClientFactory, CodegenAIClient
from graph_sitter.ai.context_gatherer import ContextGatherer
from graph_sitter.codebase.codebase_ai import AIResponse, codebase_ai, codebase_ai_sync
from graph_sitter.configs.models.secrets import SecretsConfig


class TestSecretsConfig:
    """Test enhanced secrets configuration."""
    
    def test_codegen_credentials_fields(self):
        """Test that codegen credential fields exist."""
        config = SecretsConfig()
        assert hasattr(config, 'codegen_org_id')
        assert hasattr(config, 'codegen_token')
        assert config.codegen_org_id is None
        assert config.codegen_token is None


class TestAIClientFactory:
    """Test AI client factory functionality."""
    
    def test_create_openai_client(self):
        """Test OpenAI client creation."""
        with patch('graph_sitter.ai.client_factory.OpenAI') as mock_openai:
            client, provider = AIClientFactory.create_client(
                openai_api_key="test-key"
            )
            assert provider == "openai"
            mock_openai.assert_called_once_with(api_key="test-key")
    
    def test_create_codegen_client(self):
        """Test Codegen client creation."""
        with patch('graph_sitter.ai.client_factory.CodegenAIClient') as mock_codegen:
            client, provider = AIClientFactory.create_client(
                codegen_org_id="test-org",
                codegen_token="test-token"
            )
            assert provider == "codegen"
            mock_codegen.assert_called_once_with(org_id="test-org", token="test-token")
    
    def test_prefer_codegen_when_both_available(self):
        """Test that Codegen is preferred when both are available."""
        with patch('graph_sitter.ai.client_factory.CodegenAIClient') as mock_codegen:
            client, provider = AIClientFactory.create_client(
                openai_api_key="test-key",
                codegen_org_id="test-org",
                codegen_token="test-token",
                prefer_codegen=True
            )
            assert provider == "codegen"
    
    def test_fallback_to_openai(self):
        """Test fallback to OpenAI when Codegen fails."""
        with patch('graph_sitter.ai.client_factory.CodegenAIClient', side_effect=ImportError):
            with patch('graph_sitter.ai.client_factory.OpenAI') as mock_openai:
                client, provider = AIClientFactory.create_client(
                    openai_api_key="test-key",
                    codegen_org_id="test-org",
                    codegen_token="test-token",
                    prefer_codegen=True
                )
                assert provider == "openai"
    
    def test_no_credentials_error(self):
        """Test error when no credentials provided."""
        with pytest.raises(ValueError, match="No AI credentials provided"):
            AIClientFactory.create_client()


class TestCodegenAIClient:
    """Test Codegen AI client wrapper."""
    
    def test_codegen_client_import_error(self):
        """Test handling of missing Codegen SDK."""
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(ImportError, match="Codegen SDK not available"):
                CodegenAIClient("test-org", "test-token")


class TestContextGatherer:
    """Test context gathering functionality."""
    
    def test_context_gatherer_initialization(self):
        """Test context gatherer initialization."""
        mock_codebase = Mock()
        gatherer = ContextGatherer(mock_codebase)
        assert gatherer.codebase == mock_codebase
    
    def test_get_target_info(self):
        """Test target information extraction."""
        mock_codebase = Mock()
        gatherer = ContextGatherer(mock_codebase)
        
        mock_target = Mock()
        mock_target.__class__.__name__ = "Function"
        mock_target.name = "test_function"
        mock_target.file.filepath = "test.py"
        mock_target.line_start = 10
        mock_target.line_end = 20
        mock_target.source = "def test_function():\n    pass"
        
        info = gatherer._get_target_info(mock_target)
        
        assert info["type"] == "Function"
        assert info["name"] == "test_function"
        assert info["location"]["file"] == "test.py"
        assert info["location"]["line_start"] == 10
    
    def test_format_context_for_prompt(self):
        """Test context formatting for prompts."""
        mock_codebase = Mock()
        gatherer = ContextGatherer(mock_codebase)
        
        context = {
            "target_info": {
                "type": "Function",
                "name": "test_func",
                "source_preview": "def test_func(): pass"
            },
            "codebase_summary": {
                "total_files": 10,
                "total_classes": 5,
                "total_functions": 20
            }
        }
        
        formatted = gatherer.format_context_for_prompt(context)
        
        assert "=== TARGET INFORMATION ===" in formatted
        assert "Function" in formatted
        assert "test_func" in formatted
        assert "=== CODEBASE OVERVIEW ===" in formatted
        assert "Files: 10" in formatted
    
    def test_optimize_context_size(self):
        """Test context size optimization."""
        mock_codebase = Mock()
        gatherer = ContextGatherer(mock_codebase)
        
        # Create a large context
        large_context = "x" * 50000  # ~12500 tokens
        
        optimized = gatherer.optimize_context_size(large_context, max_tokens=1000)
        
        # Should be significantly smaller
        assert len(optimized) < len(large_context)
        assert "context truncated" in optimized


class TestAIResponse:
    """Test AI response structure."""
    
    def test_ai_response_creation(self):
        """Test AI response object creation."""
        response = AIResponse(
            content="Test response",
            provider="openai",
            model="gpt-4o",
            tokens_used=100,
            response_time=1.5,
            context_size=500
        )
        
        assert response.content == "Test response"
        assert response.provider == "openai"
        assert response.model == "gpt-4o"
        assert response.tokens_used == 100
        assert response.response_time == 1.5
        assert response.context_size == 500
    
    def test_ai_response_str(self):
        """Test AI response string representation."""
        response = AIResponse("Test content", "openai", "gpt-4o")
        assert str(response) == "Test content"
    
    def test_ai_response_repr(self):
        """Test AI response repr."""
        response = AIResponse("Test content", "openai", "gpt-4o", tokens_used=50)
        assert "openai" in repr(response)
        assert "gpt-4o" in repr(response)
        assert "tokens=50" in repr(response)


class TestEnhancedCodebaseAI:
    """Test enhanced codebase AI functions."""
    
    @pytest.mark.asyncio
    async def test_codebase_ai_async(self):
        """Test async codebase AI function."""
        mock_codebase = Mock()
        mock_codebase.ctx.secrets.openai_api_key = "test-key"
        mock_codebase.ctx.secrets.codegen_org_id = None
        mock_codebase.ctx.secrets.codegen_token = None
        
        # Mock the AI client factory
        with patch('graph_sitter.codebase.codebase_ai.AIClientFactory.create_client') as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].finish_reason = "tool_calls"
            mock_response.choices[0].message.tool_calls = [Mock()]
            mock_response.choices[0].message.tool_calls[0].function.arguments = '{"answer": "Test response"}'
            
            mock_client.chat.completions.create.return_value = mock_response
            mock_factory.return_value = (mock_client, "openai")
            
            # Mock context gatherer
            with patch('graph_sitter.codebase.codebase_ai.ContextGatherer'):
                result = await codebase_ai(mock_codebase, "Test prompt")
                
                assert isinstance(result, AIResponse)
                assert result.content == "Test response"
                assert result.provider == "openai"
    
    def test_codebase_ai_sync(self):
        """Test sync codebase AI function."""
        mock_codebase = Mock()
        
        # Mock the async function
        with patch('graph_sitter.codebase.codebase_ai.codebase_ai') as mock_async:
            mock_response = AIResponse("Test response", "openai", "gpt-4o")
            
            # Create a coroutine that returns the mock response
            async def mock_coroutine(*args, **kwargs):
                return mock_response
            
            mock_async.return_value = mock_coroutine()
            
            result = codebase_ai_sync(mock_codebase, "Test prompt")
            
            assert isinstance(result, AIResponse)
            assert result.content == "Test response"


class TestCodebaseIntegration:
    """Test integration with main Codebase class."""
    
    def test_set_codegen_credentials(self):
        """Test setting Codegen credentials."""
        # This would require a full Codebase instance
        # For now, just test that the method exists
        from graph_sitter.core.codebase import Codebase
        
        # Check that the method exists
        assert hasattr(Codebase, 'set_codegen_credentials')
        assert hasattr(Codebase, 'ai')
        assert hasattr(Codebase, 'ai_sync')


if __name__ == "__main__":
    pytest.main([__file__])

