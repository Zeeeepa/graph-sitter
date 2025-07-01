"""Tests for autogenlib integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from graph_sitter.integrations.autogenlib import (
    AutogenLibIntegration,
    AutogenLibConfig,
    GenerationRequest,
    GenerationResult
)


class TestAutogenLibIntegration:
    """Test cases for AutogenLibIntegration."""
    
    def test_integration_disabled_by_default(self):
        """Test that integration is disabled by default."""
        config = AutogenLibConfig()
        integration = AutogenLibIntegration(config)
        
        assert not integration.is_enabled()
        
    def test_integration_enabled_with_config(self):
        """Test that integration can be enabled with proper config."""
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        
        with patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator'):
            integration = AutogenLibIntegration(config)
            assert integration.is_enabled()
            
    def test_generate_missing_implementation_disabled(self):
        """Test generation when integration is disabled."""
        config = AutogenLibConfig(enabled=False)
        integration = AutogenLibIntegration(config)
        
        result = integration.generate_missing_implementation(
            module_name="test.module",
            description="Test function"
        )
        
        assert not result.success
        assert "not enabled" in result.error
        
    @patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator')
    def test_generate_missing_implementation_success(self, mock_generator_class):
        """Test successful code generation."""
        # Setup mocks
        mock_generator = Mock()
        mock_generator.generate_code.return_value = GenerationResult(
            success=True,
            code="def test_function(): pass",
            generation_time=1.5
        )
        mock_generator_class.return_value = mock_generator
        
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        integration = AutogenLibIntegration(config)
        
        result = integration.generate_missing_implementation(
            module_name="test.module",
            function_name="test_function",
            description="Test function"
        )
        
        assert result.success
        assert "def test_function" in result.code
        assert result.generation_time == 1.5
        
    def test_suggest_code_completion_disabled(self):
        """Test code completion when integration is disabled."""
        config = AutogenLibConfig(enabled=False)
        integration = AutogenLibIntegration(config)
        
        suggestions = integration.suggest_code_completion(
            context="def test_",
            cursor_position=8
        )
        
        assert suggestions == []
        
    @patch('graph_sitter.integrations.autogenlib.integration.GraphSitterContextProvider')
    @patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator')
    def test_suggest_code_completion_enabled(self, mock_generator_class, mock_context_class):
        """Test code completion when integration is enabled."""
        # Setup mocks
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_context = Mock()
        mock_context_class.return_value = mock_context
        
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        integration = AutogenLibIntegration(config)
        
        suggestions = integration.suggest_code_completion(
            context="def test_",
            cursor_position=8
        )
        
        assert isinstance(suggestions, list)
        
    def test_generate_refactoring_suggestions_disabled(self):
        """Test refactoring suggestions when integration is disabled."""
        config = AutogenLibConfig(enabled=False)
        integration = AutogenLibIntegration(config)
        
        suggestions = integration.generate_refactoring_suggestions(
            code="def complex_function(): pass"
        )
        
        assert suggestions == []
        
    @patch('graph_sitter.integrations.autogenlib.integration.GraphSitterContextProvider')
    @patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator')
    def test_generate_template_code(self, mock_generator_class, mock_context_class):
        """Test template code generation."""
        # Setup mocks
        mock_generator = Mock()
        mock_generator.generate_code.return_value = GenerationResult(
            success=True,
            code="class TestClass: pass",
            generation_time=2.0
        )
        mock_generator_class.return_value = mock_generator
        mock_context = Mock()
        mock_context_class.return_value = mock_context
        
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        integration = AutogenLibIntegration(config)
        
        result = integration.generate_template_code(
            template_type="class",
            parameters={"class_name": "TestClass"}
        )
        
        assert result.success
        assert "class TestClass" in result.code
        
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid config."""
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key",
            max_context_size=5000,
            allowed_namespaces=["test.namespace"]
        )
        
        with patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator'):
            integration = AutogenLibIntegration(config)
            validation = integration.validate_configuration()
            
            assert validation["valid"]
            assert len(validation["errors"]) == 0
            
    def test_validate_configuration_invalid(self):
        """Test configuration validation with invalid config."""
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key=None  # Missing required API key
        )
        
        with patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator'):
            integration = AutogenLibIntegration(config)
            validation = integration.validate_configuration()
            
            assert not validation["valid"]
            assert len(validation["errors"]) > 0
            assert any("API key" in error for error in validation["errors"])
            
    def test_update_config_enable(self):
        """Test updating configuration to enable integration."""
        config = AutogenLibConfig(enabled=False)
        integration = AutogenLibIntegration(config)
        
        assert not integration.is_enabled()
        
        new_config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        
        with patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator'):
            integration.update_config(new_config)
            assert integration.is_enabled()
            
    def test_update_config_disable(self):
        """Test updating configuration to disable integration."""
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        
        with patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator'):
            integration = AutogenLibIntegration(config)
            assert integration.is_enabled()
            
            new_config = AutogenLibConfig(enabled=False)
            integration.update_config(new_config)
            assert not integration.is_enabled()
            
    def test_get_statistics_disabled(self):
        """Test getting statistics when integration is disabled."""
        config = AutogenLibConfig(enabled=False)
        integration = AutogenLibIntegration(config)
        
        stats = integration.get_statistics()
        
        assert stats["enabled"] is False
        
    @patch('graph_sitter.integrations.autogenlib.integration.EnhancedCodeGenerator')
    def test_get_statistics_enabled(self, mock_generator_class):
        """Test getting statistics when integration is enabled."""
        mock_generator = Mock()
        mock_generator.get_generation_stats.return_value = {
            "total_generations": 10,
            "successful_generations": 8,
            "failed_generations": 2
        }
        mock_generator_class.return_value = mock_generator
        
        config = AutogenLibConfig(
            enabled=True,
            openai_api_key="test-key"
        )
        integration = AutogenLibIntegration(config)
        
        stats = integration.get_statistics()
        
        assert stats["enabled"] is True
        assert stats["total_generations"] == 10
        assert stats["successful_generations"] == 8
        assert stats["failed_generations"] == 2

