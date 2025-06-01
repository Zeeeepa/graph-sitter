"""
Tests for Enhanced Codebase AI functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from graph_sitter import Codebase
from graph_sitter.ai.ai_client_factory import AIClientFactory, AIResponse, OpenAIClient, CodegenSDKClient
from graph_sitter.ai.context_gatherer import ContextGatherer
from graph_sitter.configs.models.secrets import SecretsConfig


class TestAIClientFactory:
    """Test AI client factory functionality"""
    
    def test_get_available_providers_empty(self):
        """Test with no credentials"""
        secrets = SecretsConfig()
        providers = AIClientFactory.get_available_providers(secrets)
        assert providers == []
    
    def test_get_available_providers_openai_only(self):
        """Test with only OpenAI credentials"""
        secrets = SecretsConfig()
        secrets.openai_api_key = "test-key"
        providers = AIClientFactory.get_available_providers(secrets)
        assert providers == ["openai"]
    
    def test_get_available_providers_codegen_only(self):
        """Test with only Codegen SDK credentials"""
        secrets = SecretsConfig()
        secrets.codegen_org_id = "test-org"
        secrets.codegen_token = "test-token"
        providers = AIClientFactory.get_available_providers(secrets)
        assert providers == ["codegen_sdk"]
    
    def test_get_available_providers_both(self):
        """Test with both providers available"""
        secrets = SecretsConfig()
        secrets.openai_api_key = "test-key"
        secrets.codegen_org_id = "test-org"
        secrets.codegen_token = "test-token"
        providers = AIClientFactory.get_available_providers(secrets)
        assert set(providers) == {"openai", "codegen_sdk"}
    
    def test_create_client_no_credentials(self):
        """Test client creation with no credentials"""
        secrets = SecretsConfig()
        with pytest.raises(ValueError, match="No AI provider credentials available"):
            AIClientFactory.create_client(secrets)
    
    def test_create_client_preferred_provider(self):
        """Test client creation with preferred provider"""
        secrets = SecretsConfig()
        secrets.openai_api_key = "test-key"
        secrets.codegen_org_id = "test-org"
        secrets.codegen_token = "test-token"
        
        # Test OpenAI preference
        client = AIClientFactory.create_client(secrets, preferred_provider="openai")
        assert isinstance(client, OpenAIClient)
        
        # Test Codegen SDK preference
        with patch('graph_sitter.ai.ai_client_factory.CodegenSDKClient') as mock_codegen:
            mock_instance = Mock()
            mock_codegen.return_value = mock_instance
            client = AIClientFactory.create_client(secrets, preferred_provider="codegen_sdk")
            assert client == mock_instance


class TestContextGatherer:
    """Test context gathering functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_codebase = Mock()
        self.mock_codebase.files = []
        self.mock_codebase.functions = []
        self.mock_codebase.classes = []
        self.gatherer = ContextGatherer(self.mock_codebase)
    
    def test_gather_context_no_target(self):
        """Test context gathering without target"""
        context = self.gatherer.gather_context()
        
        assert "target_info" in context
        assert "static_analysis" in context
        assert "relationships" in context
        assert "user_context" in context
        assert "codebase_summary" in context
        
        assert context["target_info"] == {}
    
    def test_gather_context_with_string_context(self):
        """Test context gathering with string context"""
        context = self.gatherer.gather_context(context="test context")
        
        assert context["user_context"]["text"] == "test context"
    
    def test_gather_context_with_dict_context(self):
        """Test context gathering with dict context"""
        test_context = {"key1": "value1", "key2": "value2"}
        context = self.gatherer.gather_context(context=test_context)
        
        assert context["user_context"]["key1"] == "value1"
        assert context["user_context"]["key2"] == "value2"
    
    def test_format_context_for_ai(self):
        """Test context formatting for AI consumption"""
        context = {
            "target_info": {
                "name": "test_function",
                "type": "Function",
                "file_path": "test.py",
                "start_line": 10
            },
            "codebase_summary": {
                "total_files": 5,
                "total_functions": 20
            }
        }
        
        formatted = self.gatherer.format_context_for_ai(context)
        
        assert "TARGET: test_function" in formatted
        assert "Files: 5" in formatted
        assert "Functions: 20" in formatted


class TestEnhancedCodebaseAI:
    """Test enhanced codebase AI functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a mock codebase
        with patch('graph_sitter.core.codebase.Codebase.__init__', return_value=None):
            self.codebase = Codebase.__new__(Codebase)
            
        # Mock the context and secrets
        self.codebase.ctx = Mock()
        self.codebase.ctx.secrets = SecretsConfig()
        self.codebase.ctx.session_options = Mock()
        self.codebase.ctx.session_options.max_ai_requests = None
        self.codebase._num_ai_requests = 0
        
        # Mock files, functions, classes
        self.codebase.files = []
        self.codebase.functions = []
        self.codebase.classes = []
    
    def test_set_codegen_credentials(self):
        """Test setting Codegen SDK credentials"""
        self.codebase._ai_helper = Mock()  # Should be reset
        
        self.codebase.set_codegen_credentials("test-org", "test-token")
        
        assert self.codebase.ctx.secrets.codegen_org_id == "test-org"
        assert self.codebase.ctx.secrets.codegen_token == "test-token"
        assert self.codebase._ai_helper is None
    
    @pytest.mark.asyncio
    async def test_ai_method_no_credentials(self):
        """Test AI method with no credentials"""
        with pytest.raises(ValueError, match="No AI provider credentials available"):
            await self.codebase.ai("test prompt")
    
    @pytest.mark.asyncio
    async def test_ai_method_with_openai(self):
        """Test AI method with OpenAI credentials"""
        self.codebase.ctx.secrets.openai_api_key = "test-key"
        
        # Mock the AI client and response
        mock_response = AIResponse(
            content="test response",
            provider="openai",
            tokens_used=100,
            generation_time=1.5
        )
        
        with patch('graph_sitter.ai.ai_client_factory.AIClientFactory.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.generate.return_value = mock_response
            mock_create.return_value = mock_client
            
            result = await self.codebase.ai("test prompt")
            
            assert result == "test response"
            assert self.codebase._num_ai_requests == 1
            mock_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ai_method_with_target(self):
        """Test AI method with target element"""
        self.codebase.ctx.secrets.openai_api_key = "test-key"
        
        # Create a mock target
        mock_target = Mock()
        mock_target.extended_source = "def test(): pass"
        mock_target.name = "test"
        
        mock_response = AIResponse(content="analysis result", provider="openai")
        
        with patch('graph_sitter.ai.ai_client_factory.AIClientFactory.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.generate.return_value = mock_response
            mock_create.return_value = mock_client
            
            result = await self.codebase.ai("analyze this", target=mock_target)
            
            assert result == "analysis result"
            # Verify that context gathering was attempted
            mock_client.generate.assert_called_once()
    
    def test_ai_sync_method(self):
        """Test synchronous AI method"""
        self.codebase.ctx.secrets.openai_api_key = "test-key"
        
        mock_response = AIResponse(content="sync response", provider="openai")
        
        with patch('graph_sitter.ai.ai_client_factory.AIClientFactory.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.generate.return_value = mock_response
            mock_create.return_value = mock_client
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "sync response"
                
                result = self.codebase.ai_sync("test prompt")
                
                assert result == "sync response"
                mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ai_method_max_requests_exceeded(self):
        """Test AI method with max requests exceeded"""
        self.codebase.ctx.secrets.openai_api_key = "test-key"
        self.codebase.ctx.session_options.max_ai_requests = 1
        self.codebase._num_ai_requests = 1
        
        from graph_sitter.shared.exceptions.control_flow import MaxAIRequestsError
        
        with pytest.raises(MaxAIRequestsError):
            await self.codebase.ai("test prompt")
    
    @pytest.mark.asyncio
    async def test_ai_method_with_provider_preference(self):
        """Test AI method with provider preference"""
        self.codebase.ctx.secrets.openai_api_key = "test-key"
        self.codebase.ctx.secrets.codegen_org_id = "test-org"
        self.codebase.ctx.secrets.codegen_token = "test-token"
        
        mock_response = AIResponse(content="codegen response", provider="codegen_sdk")
        
        with patch('graph_sitter.ai.ai_client_factory.AIClientFactory.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.generate.return_value = mock_response
            mock_create.return_value = mock_client
            
            result = await self.codebase.ai("test prompt", provider="codegen_sdk")
            
            assert result == "codegen response"
            mock_create.assert_called_with(self.codebase.ctx.secrets, preferred_provider="codegen_sdk")


class TestAIResponse:
    """Test AI response class"""
    
    def test_ai_response_creation(self):
        """Test AI response creation"""
        response = AIResponse(
            content="test content",
            metadata={"key": "value"},
            provider="test_provider",
            tokens_used=50,
            cost_estimate=0.01,
            generation_time=2.0
        )
        
        assert response.content == "test content"
        assert response.metadata == {"key": "value"}
        assert response.provider == "test_provider"
        assert response.tokens_used == 50
        assert response.cost_estimate == 0.01
        assert response.generation_time == 2.0
    
    def test_ai_response_defaults(self):
        """Test AI response with default values"""
        response = AIResponse(content="test")
        
        assert response.content == "test"
        assert response.metadata == {}
        assert response.provider == "unknown"
        assert response.tokens_used == 0
        assert response.cost_estimate == 0.0
        assert response.generation_time == 0.0


if __name__ == "__main__":
    pytest.main([__file__])

