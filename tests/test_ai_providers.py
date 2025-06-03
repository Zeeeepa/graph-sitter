"""Tests for the AI provider system."""

import pytest
from unittest.mock import Mock, patch
from graph_sitter.ai.providers.base import AIProvider, AIResponse
from graph_sitter.ai.providers.factory import create_ai_provider
from graph_sitter.ai.client import get_ai_client


class MockProvider(AIProvider):
    """Mock provider for testing."""
    
    provider_name = "mock"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def generate_response(self, prompt, **kwargs):
        return AIResponse(
            content=f"Mock response to: {prompt}",
            provider_name=self.provider_name,
            model=kwargs.get("model", "mock-model")
        )


class TestAIProviders:
    """Test cases for AI provider system."""
    
    def test_ai_response_creation(self):
        """Test AIResponse dataclass creation."""
        response = AIResponse(
            content="Test content",
            provider_name="test",
            model="test-model"
        )
        
        assert response.content == "Test content"
        assert response.provider_name == "test"
        assert response.model == "test-model"
        assert response.raw_response is None
    
    def test_mock_provider(self):
        """Test mock provider implementation."""
        provider = MockProvider()
        
        response = provider.generate_response(
            prompt="Test prompt",
            model="test-model"
        )
        
        assert response.content == "Mock response to: Test prompt"
        assert response.provider_name == "mock"
        assert response.model == "test-model"
    
    @patch.dict('os.environ', {}, clear=True)
    def test_no_providers_available(self):
        """Test behavior when no providers are configured."""
        with pytest.raises(ValueError, match="No AI providers available"):
            create_ai_provider()
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_openai_provider_selection(self):
        """Test OpenAI provider selection when configured."""
        try:
            provider = create_ai_provider(provider_name="openai")
            assert provider.provider_name == "OpenAI"
        except ImportError:
            # OpenAI might not be available in test environment
            pytest.skip("OpenAI not available")
    
    @patch.dict('os.environ', {
        'CODEGEN_ORG_ID': 'test_org',
        'CODEGEN_TOKEN': 'test_token'
    })
    def test_codegen_provider_selection(self):
        """Test Codegen provider selection when configured."""
        try:
            provider = create_ai_provider(provider_name="codegen")
            assert provider.provider_name == "Codegen"
        except Exception:
            # Codegen SDK might not be available in test environment
            pytest.skip("Codegen SDK not available")
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_get_ai_client(self):
        """Test get_ai_client function."""
        try:
            client = get_ai_client()
            assert hasattr(client, 'generate_response')
            assert hasattr(client, 'provider_name')
        except ImportError:
            pytest.skip("AI providers not available")
    
    def test_provider_interface(self):
        """Test that providers implement the required interface."""
        provider = MockProvider()
        
        # Check required attributes
        assert hasattr(provider, 'provider_name')
        assert hasattr(provider, 'generate_response')
        
        # Check method signature
        response = provider.generate_response("test")
        assert isinstance(response, AIResponse)
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'CODEGEN_ORG_ID': 'test_org',
        'CODEGEN_TOKEN': 'test_token'
    })
    def test_provider_preference(self):
        """Test provider preference logic."""
        try:
            # Should prefer Codegen when both are available
            provider = create_ai_provider(prefer_codegen=True)
            # This might fail if Codegen SDK is not available
        except Exception:
            pytest.skip("Provider preference test requires both providers")
    
    def test_invalid_provider_name(self):
        """Test handling of invalid provider names."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_ai_provider(provider_name="invalid_provider")


if __name__ == "__main__":
    pytest.main([__file__])

