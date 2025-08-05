"""Tests for AutoGenLib integration."""

import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from graph_sitter.core.codebase import Codebase
from .config import AutoGenLibConfig
from .core import AutoGenLibIntegration
from .generator import CodegenSDKProvider, ClaudeProvider, CodeGenerator
from .context import GraphSitterContextProvider
from .cache import CodeCache
from .integration import ContextenAutoGenLibIntegration


class TestAutoGenLibConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AutoGenLibConfig()
        self.assertEqual(config.description, "Dynamic code generation library")
        self.assertFalse(config.enable_caching)
        self.assertTrue(config.enable_exception_handler)
        self.assertEqual(config.provider_order, ["codegen", "claude", "openai"])
    
    def test_from_environment(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            "CODEGEN_ORG_ID": "test-org",
            "CODEGEN_TOKEN": "test-token",
            "CLAUDE_API_KEY": "test-claude-key",
            "AUTOGENLIB_ENABLE_CACHING": "true",
            "AUTOGENLIB_DESCRIPTION": "Test library"
        }):
            config = AutoGenLibConfig.from_environment()
            self.assertEqual(config.codegen_org_id, "test-org")
            self.assertEqual(config.codegen_token, "test-token")
            self.assertEqual(config.claude_api_key, "test-claude-key")
            self.assertTrue(config.enable_caching)
            self.assertEqual(config.description, "Test library")
    
    def test_validation(self):
        """Test configuration validation."""
        # Valid config
        config = AutoGenLibConfig(
            codegen_org_id="test-org",
            codegen_token="test-token"
        )
        issues = config.validate()
        self.assertEqual(len(issues), 0)
        
        # Invalid config
        config = AutoGenLibConfig(
            generation_timeout=-1,
            temperature=3.0
        )
        issues = config.validate()
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("generation_timeout" in issue for issue in issues))
        self.assertTrue(any("temperature" in issue for issue in issues))
    
    def test_available_providers(self):
        """Test available providers detection."""
        config = AutoGenLibConfig(
            codegen_org_id="test-org",
            codegen_token="test-token",
            claude_api_key="test-claude-key"
        )
        providers = config.get_available_providers()
        self.assertIn("codegen", providers)
        self.assertIn("claude", providers)


class TestCodeCache(unittest.TestCase):
    """Test code caching functionality."""
    
    def setUp(self):
        """Set up test cache directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CodeCache(enabled=True, cache_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test cache directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_cache_disabled(self):
        """Test cache when disabled."""
        cache = CodeCache(enabled=False)
        cache.set("test.module", "test code")
        result = cache.get("test.module")
        self.assertIsNone(result)
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        # Set and get
        self.cache.set("test.module", "test code")
        result = self.cache.get("test.module")
        self.assertEqual(result, "test code")
        
        # List cached
        cached = self.cache.list_cached()
        self.assertIn("test.module", cached)
        
        # Clear cache
        self.cache.clear()
        result = self.cache.get("test.module")
        self.assertIsNone(result)
    
    def test_cache_info(self):
        """Test cache information."""
        info = self.cache.get_cache_info()
        self.assertTrue(info["enabled"])
        self.assertEqual(info["cached_modules"], 0)
        
        # Add some cached modules
        self.cache.set("test1", "code1")
        self.cache.set("test2", "code2")
        
        info = self.cache.get_cache_info()
        self.assertEqual(info["cached_modules"], 2)
        self.assertGreater(info["total_size"], 0)


class TestCodeGenerationProviders(unittest.TestCase):
    """Test code generation providers."""
    
    def test_codegen_sdk_provider_unavailable(self):
        """Test Codegen SDK provider when not available."""
        provider = CodegenSDKProvider("test-org", "test-token")
        # Without actual SDK, should not be available
        self.assertFalse(provider.is_available())
        
        result = provider.generate_code(
            "test description",
            "autogenlib.test.module"
        )
        self.assertIsNone(result)
    
    def test_claude_provider_unavailable(self):
        """Test Claude provider when not available."""
        provider = ClaudeProvider("test-key")
        # Without actual Anthropic library, should not be available
        self.assertFalse(provider.is_available())
        
        result = provider.generate_code(
            "test description",
            "autogenlib.test.module"
        )
        self.assertIsNone(result)
    
    @patch('contexten.extensions.autogenlib.generator.anthropic')
    def test_claude_provider_available(self, mock_anthropic):
        """Test Claude provider when available."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="def test_function():\n    return 'test'")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        
        provider = ClaudeProvider("test-key")
        self.assertTrue(provider.is_available())
        
        result = provider.generate_code(
            "test description",
            "autogenlib.test.module"
        )
        self.assertIsNotNone(result)
        self.assertIn("def test_function", result)
    
    def test_code_generator_fallback(self):
        """Test code generator fallback mechanism."""
        # Create mock providers
        provider1 = Mock()
        provider1.is_available.return_value = False
        provider1.name = "Provider1"
        
        provider2 = Mock()
        provider2.is_available.return_value = True
        provider2.name = "Provider2"
        provider2.generate_code.return_value = "generated code"
        
        generator = CodeGenerator([provider1, provider2])
        
        result = generator.generate_code(
            "test description",
            "autogenlib.test.module"
        )
        
        self.assertEqual(result, "generated code")
        provider1.generate_code.assert_not_called()
        provider2.generate_code.assert_called_once()


class TestGraphSitterContextProvider(unittest.TestCase):
    """Test graph-sitter context provider."""
    
    def setUp(self):
        """Set up mock codebase."""
        self.mock_codebase = Mock(spec=Codebase)
        
        # Mock functions
        mock_func1 = Mock()
        mock_func1.name = "test_function"
        mock_func1.source = "def test_function(): pass"
        mock_func1.filepath = "/test/file.py"
        mock_func1.call_sites = []
        mock_func1.function_calls = []
        
        mock_func2 = Mock()
        mock_func2.name = "helper_function"
        mock_func2.source = "def helper_function(): pass"
        mock_func2.filepath = "/test/helper.py"
        mock_func2.call_sites = []
        mock_func2.function_calls = []
        
        self.mock_codebase.functions = [mock_func1, mock_func2]
        self.mock_codebase.classes = []
        self.mock_codebase.files = []
        
        self.provider = GraphSitterContextProvider(self.mock_codebase)
    
    def test_get_context(self):
        """Test context gathering."""
        context = self.provider.get_context("autogenlib.test.module")
        
        self.assertIn("codebase_stats", context)
        self.assertIn("related_functions", context)
        self.assertIn("dependencies", context)
        self.assertIn("usages", context)
        
        stats = context["codebase_stats"]
        self.assertEqual(stats["total_functions"], 2)
        self.assertEqual(stats["total_classes"], 0)
        self.assertEqual(stats["total_files"], 0)
    
    def test_find_related_functions(self):
        """Test finding related functions."""
        related = self.provider._find_related_functions("autogenlib.test.module")
        
        # Should find the test_function since it contains "test"
        self.assertGreater(len(related), 0)
        function_names = [f["name"] for f in related]
        self.assertIn("test_function", function_names)


class TestAutoGenLibIntegration(unittest.TestCase):
    """Test main integration class."""
    
    def setUp(self):
        """Set up test integration."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_integration_no_providers(self):
        """Test integration with no providers configured."""
        integration = AutoGenLibIntegration(
            description="Test library",
            enable_caching=False
        )
        
        # Should initialize but have no providers
        self.assertEqual(len(integration.generator.providers), 0)
    
    def test_integration_with_mock_provider(self):
        """Test integration with mock provider."""
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.name = "MockProvider"
        mock_provider.generate_code.return_value = "def test(): pass"
        
        integration = AutoGenLibIntegration(
            description="Test library",
            enable_caching=True,
            cache_dir=self.temp_dir
        )
        integration.add_provider(mock_provider)
        
        # Test code generation
        result = integration.generate_module("autogenlib.test.module")
        self.assertEqual(result, "def test(): pass")
        
        # Test caching
        cached_result = integration.generate_module("autogenlib.test.module")
        self.assertEqual(cached_result, "def test(): pass")
        
        # Provider should only be called once due to caching
        self.assertEqual(mock_provider.generate_code.call_count, 1)


class TestContextenIntegration(unittest.TestCase):
    """Test contexten ecosystem integration."""
    
    def test_integration_initialization(self):
        """Test contexten integration initialization."""
        config = AutoGenLibConfig(
            description="Test library",
            enable_caching=False
        )
        
        integration = ContextenAutoGenLibIntegration(config=config)
        
        # Should initialize but not be available without providers
        self.assertFalse(integration.is_available())
        
        status = integration.get_status()
        self.assertFalse(status["initialized"])
        self.assertFalse(status["config_valid"])  # No providers configured
    
    def test_integration_with_codegen_app(self):
        """Test integration with mock CodegenApp."""
        mock_app = Mock()
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.functions = []
        mock_codebase.classes = []
        mock_codebase.files = []
        mock_app.get_codebase.return_value = mock_codebase
        
        config = AutoGenLibConfig(
            description="Test library",
            codegen_org_id="test-org",
            codegen_token="test-token"
        )
        
        integration = ContextenAutoGenLibIntegration(
            codegen_app=mock_app,
            config=config
        )
        
        self.assertTrue(integration.config.codegen_org_id == "test-org")
        self.assertTrue(integration.codegen_app == mock_app)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)

