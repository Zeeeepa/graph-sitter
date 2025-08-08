"""
Test Suite for Serena LSP Integration

Comprehensive tests for all Serena capabilities integrated into graph-sitter.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the integration
from graph_sitter.extensions.serena.integration import SerenaIntegration, add_serena_to_codebase
from graph_sitter.extensions.serena.core import SerenaCore, SerenaConfig, SerenaCapability


class MockCodebase:
    """Mock Codebase class for testing."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.files = []
        self.symbols = []
    
    def get_file(self, file_path: str):
        """Mock get_file method."""
        return Mock(content="def test_function():\n    pass", symbols=[])


class TestSerenaIntegration:
    """Test the Serena integration functionality."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello_world():\n    print('Hello, World!')\n")
            
            yield temp_dir
    
    @pytest.fixture
    def mock_codebase(self, temp_repo):
        """Create a mock codebase instance."""
        return MockCodebase(temp_repo)
    
    @pytest.fixture
    def serena_integration(self, mock_codebase):
        """Create a Serena integration instance."""
        return SerenaIntegration(mock_codebase)
    
    def test_serena_integration_initialization(self, serena_integration):
        """Test that Serena integration initializes correctly."""
        assert serena_integration.codebase is not None
        assert serena_integration._serena_core is None
        assert serena_integration._serena_enabled is True
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_ensure_serena_initialized(self, mock_serena_core, serena_integration):
        """Test that Serena core is initialized on first use."""
        mock_core_instance = Mock()
        mock_serena_core.return_value = mock_core_instance
        
        # First call should initialize
        result = serena_integration._ensure_serena_initialized()
        assert result == mock_core_instance
        assert serena_integration._serena_core == mock_core_instance
        
        # Second call should return existing instance
        result2 = serena_integration._ensure_serena_initialized()
        assert result2 == mock_core_instance
        assert mock_serena_core.call_count == 1
    
    def test_ensure_serena_disabled(self, serena_integration):
        """Test behavior when Serena is disabled."""
        serena_integration._serena_enabled = False
        
        result = serena_integration._ensure_serena_initialized()
        assert result is None
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_get_completions(self, mock_serena_core, serena_integration):
        """Test get_completions method."""
        mock_core_instance = Mock()
        mock_core_instance.get_completions.return_value = [
            {'label': 'test_function', 'kind': 'Function', 'detail': 'def test_function()'}
        ]
        mock_serena_core.return_value = mock_core_instance
        
        result = serena_integration.get_completions("test.py", 1, 5)
        
        assert len(result) == 1
        assert result[0]['label'] == 'test_function'
        mock_core_instance.get_completions.assert_called_once_with("test.py", 1, 5)
    
    def test_get_completions_disabled(self, serena_integration):
        """Test get_completions when Serena is disabled."""
        serena_integration._serena_enabled = False
        
        result = serena_integration.get_completions("test.py", 1, 5)
        assert result == []
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_get_hover_info(self, mock_serena_core, serena_integration):
        """Test get_hover_info method."""
        mock_core_instance = Mock()
        mock_core_instance.get_hover_info.return_value = {
            'symbolName': 'test_function',
            'symbolType': 'function',
            'documentation': 'A test function'
        }
        mock_serena_core.return_value = mock_core_instance
        
        result = serena_integration.get_hover_info("test.py", 1, 5)
        
        assert result['symbolName'] == 'test_function'
        assert result['symbolType'] == 'function'
        mock_core_instance.get_hover_info.assert_called_once_with("test.py", 1, 5)
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_rename_symbol(self, mock_serena_core, serena_integration):
        """Test rename_symbol method."""
        mock_core_instance = Mock()
        mock_core_instance.rename_symbol.return_value = {
            'success': True,
            'changes': [{'file': 'test.py', 'old_name': 'old_func', 'new_name': 'new_func'}]
        }
        mock_serena_core.return_value = mock_core_instance
        
        result = serena_integration.rename_symbol("test.py", 1, 5, "new_func")
        
        assert result['success'] is True
        assert len(result['changes']) == 1
        mock_core_instance.rename_symbol.assert_called_once_with("test.py", 1, 5, "new_func", False)
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_semantic_search(self, mock_serena_core, serena_integration):
        """Test semantic_search method."""
        mock_core_instance = Mock()
        mock_core_instance.semantic_search.return_value = [
            {'file': 'test.py', 'line': 1, 'match': 'def hello_world()', 'score': 0.95}
        ]
        mock_serena_core.return_value = mock_core_instance
        
        result = serena_integration.semantic_search("hello world function")
        
        assert len(result) == 1
        assert result[0]['file'] == 'test.py'
        assert result[0]['score'] == 0.95
        mock_core_instance.semantic_search.assert_called_once_with("hello world function", "natural")
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_get_serena_status(self, mock_serena_core, serena_integration):
        """Test get_serena_status method."""
        mock_core_instance = Mock()
        mock_core_instance.get_status.return_value = {
            'enabled_capabilities': ['intelligence', 'refactoring'],
            'active_capabilities': ['intelligence', 'refactoring'],
            'realtime_analysis': True
        }
        mock_serena_core.return_value = mock_core_instance
        
        result = serena_integration.get_serena_status()
        
        assert result['enabled'] is True
        assert 'intelligence' in result['enabled_capabilities']
        assert 'refactoring' in result['enabled_capabilities']
    
    def test_get_serena_status_disabled(self, serena_integration):
        """Test get_serena_status when Serena is disabled."""
        serena_integration._serena_enabled = False
        
        result = serena_integration.get_serena_status()
        
        assert result['enabled'] is False
        assert 'error' in result
    
    @patch('graph_sitter.extensions.serena.integration.SerenaCore')
    def test_shutdown_serena(self, mock_serena_core, serena_integration):
        """Test shutdown_serena method."""
        mock_core_instance = Mock()
        mock_serena_core.return_value = mock_core_instance
        
        # Initialize Serena first
        serena_integration._ensure_serena_initialized()
        
        # Then shutdown
        serena_integration.shutdown_serena()
        
        mock_core_instance.shutdown.assert_called_once()
        assert serena_integration._serena_core is None
        assert serena_integration._serena_enabled is False


class TestCodebaseIntegration:
    """Test integration with the Codebase class."""
    
    def test_add_serena_to_codebase(self):
        """Test that Serena methods are added to Codebase class."""
        # Create a mock Codebase class
        class MockCodebaseClass:
            def __init__(self, repo_path):
                self.repo_path = repo_path
        
        # Add Serena methods
        add_serena_to_codebase(MockCodebaseClass)
        
        # Check that methods were added
        expected_methods = [
            'get_completions', 'get_hover_info', 'get_signature_help',
            'rename_symbol', 'extract_method', 'extract_variable',
            'get_code_actions', 'apply_code_action', 'organize_imports',
            'generate_boilerplate', 'generate_tests', 'generate_documentation',
            'semantic_search', 'find_code_patterns', 'find_similar_code',
            'get_symbol_context', 'analyze_symbol_impact',
            'enable_realtime_analysis', 'disable_realtime_analysis',
            'get_serena_status', 'shutdown_serena'
        ]
        
        for method_name in expected_methods:
            assert hasattr(MockCodebaseClass, method_name)
            assert callable(getattr(MockCodebaseClass, method_name))
    
    def test_codebase_method_calls(self):
        """Test that Codebase methods call Serena integration correctly."""
        # Create a mock Codebase class
        class MockCodebaseClass:
            def __init__(self, repo_path):
                self.repo_path = repo_path
        
        # Add Serena methods
        add_serena_to_codebase(MockCodebaseClass)
        
        # Create instance
        codebase = MockCodebaseClass("/test/repo")
        
        # Mock the integration
        with patch.object(codebase, '_get_serena_integration') as mock_get_integration:
            mock_integration = Mock()
            mock_integration.get_completions.return_value = [{'label': 'test'}]
            mock_get_integration.return_value = mock_integration
            
            # Call method
            result = codebase.get_completions("test.py", 1, 5)
            
            # Verify
            assert result == [{'label': 'test'}]
            mock_integration.get_completions.assert_called_once_with("test.py", 1, 5)


class TestSerenaCore:
    """Test the Serena core functionality."""
    
    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase."""
        return MockCodebase("/test/repo")
    
    @pytest.fixture
    def serena_config(self):
        """Create a test Serena configuration."""
        return SerenaConfig(
            enabled_capabilities=[SerenaCapability.INTELLIGENCE, SerenaCapability.REFACTORING],
            realtime_analysis=False,  # Disable for testing
            cache_size=100
        )
    
    @patch('graph_sitter.extensions.serena.core.SerenaLSPBridge')
    def test_serena_core_initialization(self, mock_lsp_bridge, mock_codebase, serena_config):
        """Test SerenaCore initialization."""
        mock_bridge_instance = Mock()
        mock_lsp_bridge.return_value = mock_bridge_instance
        
        with patch('graph_sitter.extensions.serena.intelligence.CodeIntelligence') as mock_intelligence:
            with patch('graph_sitter.extensions.serena.refactoring.RefactoringEngine') as mock_refactoring:
                mock_intelligence_instance = Mock()
                mock_refactoring_instance = Mock()
                mock_intelligence.return_value = mock_intelligence_instance
                mock_refactoring.return_value = mock_refactoring_instance
                
                core = SerenaCore(mock_codebase, serena_config)
                
                assert core.codebase == mock_codebase
                assert core.config == serena_config
                assert SerenaCapability.INTELLIGENCE in core._capabilities
                assert SerenaCapability.REFACTORING in core._capabilities
    
    @patch('graph_sitter.extensions.serena.core.SerenaLSPBridge')
    def test_serena_core_get_status(self, mock_lsp_bridge, mock_codebase, serena_config):
        """Test SerenaCore get_status method."""
        mock_bridge_instance = Mock()
        mock_bridge_instance.get_status.return_value = {'initialized': True}
        mock_lsp_bridge.return_value = mock_bridge_instance
        
        with patch('graph_sitter.extensions.serena.intelligence.CodeIntelligence') as mock_intelligence:
            mock_intelligence_instance = Mock()
            mock_intelligence_instance.get_status.return_value = {'initialized': True}
            mock_intelligence.return_value = mock_intelligence_instance
            
            core = SerenaCore(mock_codebase, serena_config)
            status = core.get_status()
            
            assert 'enabled_capabilities' in status
            assert 'active_capabilities' in status
            assert 'lsp_bridge_status' in status
            assert 'capability_details' in status


class TestSerenaConfig:
    """Test Serena configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SerenaConfig()
        
        assert config.enabled_capabilities == list(SerenaCapability)
        assert config.realtime_analysis is True
        assert config.cache_size == 1000
        assert config.max_completions == 50
        assert config.enable_ai_features is True
        assert config.performance_mode is False
        assert "*.py" in config.file_watch_patterns
        assert "*.ts" in config.file_watch_patterns
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SerenaConfig(
            enabled_capabilities=[SerenaCapability.INTELLIGENCE],
            realtime_analysis=False,
            cache_size=500,
            max_completions=25,
            enable_ai_features=False,
            performance_mode=True,
            file_watch_patterns=["*.py"]
        )
        
        assert config.enabled_capabilities == [SerenaCapability.INTELLIGENCE]
        assert config.realtime_analysis is False
        assert config.cache_size == 500
        assert config.max_completions == 25
        assert config.enable_ai_features is False
        assert config.performance_mode is True
        assert config.file_watch_patterns == ["*.py"]


class TestErrorHandling:
    """Test error handling in Serena integration."""
    
    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase."""
        return MockCodebase("/test/repo")
    
    def test_serena_initialization_failure(self, mock_codebase):
        """Test handling of Serena initialization failure."""
        integration = SerenaIntegration(mock_codebase)
        
        with patch('graph_sitter.extensions.serena.integration.SerenaCore', side_effect=Exception("Init failed")):
            result = integration._ensure_serena_initialized()
            
            assert result is None
            assert integration._serena_enabled is False
    
    def test_method_calls_with_disabled_serena(self, mock_codebase):
        """Test method calls when Serena is disabled."""
        integration = SerenaIntegration(mock_codebase)
        integration._serena_enabled = False
        
        # Test various methods return appropriate defaults
        assert integration.get_completions("test.py", 1, 5) == []
        assert integration.get_hover_info("test.py", 1, 5) is None
        assert integration.get_signature_help("test.py", 1, 5) is None
        
        result = integration.rename_symbol("test.py", 1, 5, "new_name")
        assert result['success'] is False
        assert "not available" in result['error']
    
    def test_method_exception_handling(self, mock_codebase):
        """Test exception handling in methods."""
        integration = SerenaIntegration(mock_codebase)
        
        with patch.object(integration, '_ensure_serena_initialized', side_effect=Exception("Test error")):
            # Methods should handle exceptions gracefully
            assert integration.get_completions("test.py", 1, 5) == []
            assert integration.get_hover_info("test.py", 1, 5) is None


if __name__ == "__main__":
    pytest.main([__file__])

