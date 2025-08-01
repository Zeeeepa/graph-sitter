#!/usr/bin/env python3
"""
Unit Tests for Serena LSP Integration

This test suite focuses on unit testing individual components of the Serena LSP integration,
including the unified error interface, LSP bridge, and core functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

try:
    from graph_sitter.extensions.lsp.serena.unified_error_interface import UnifiedErrorInterface, add_unified_error_interface
    from graph_sitter.extensions.lsp.serena.lsp_integration import SerenaLSPIntegration
    from graph_sitter.extensions.lsp.serena.types import SerenaConfig
    from graph_sitter.core.codebase import Codebase
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    pytest.skip(f"Required imports not available: {e}", allow_module_level=True)


class TestUnifiedErrorInterfaceUnit:
    """Unit tests for UnifiedErrorInterface class."""
    
    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase for testing."""
        mock_codebase = Mock()
        mock_codebase.repo_path = "/tmp/test_repo"
        mock_codebase.files = []
        mock_codebase.get_file = Mock(return_value=None)
        return mock_codebase
    
    @pytest.fixture
    def error_interface(self, mock_codebase):
        """Create UnifiedErrorInterface instance for testing."""
        return UnifiedErrorInterface(mock_codebase)
    
    def test_unified_error_interface_initialization(self, mock_codebase):
        """Test UnifiedErrorInterface initialization."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        assert interface.codebase == mock_codebase
        assert interface._lsp_integration is None
        assert isinstance(interface._error_cache, dict)
        assert len(interface._error_cache) == 0
    
    def test_lazy_lsp_integration_initialization(self, error_interface):
        """Test lazy initialization of LSP integration."""
        # Mock SerenaLSPIntegration
        with patch('graph_sitter.extensions.lsp.serena.unified_error_interface.SerenaLSPIntegration') as mock_lsp:
            mock_lsp_instance = Mock()
            mock_lsp.return_value = mock_lsp_instance
            
            # First call should initialize LSP integration
            result = error_interface._ensure_lsp_integration()
            
            assert result == mock_lsp_instance
            assert error_interface._lsp_integration == mock_lsp_instance
            
            # Second call should return cached instance
            result2 = error_interface._ensure_lsp_integration()
            assert result2 == mock_lsp_instance
            
            # Should only initialize once
            mock_lsp.assert_called_once()
    
    def test_errors_method_empty_codebase(self, error_interface):
        """Test errors() method with empty codebase."""
        error_interface.codebase.files = []
        
        errors = error_interface.errors()
        
        assert isinstance(errors, list)
        assert len(errors) == 0
    
    def test_errors_method_with_files(self, error_interface):
        """Test errors() method with files containing errors."""
        # Mock file objects
        mock_file1 = Mock()
        mock_file1.file_path = "test1.py"
        mock_file2 = Mock()
        mock_file2.file_path = "test2.py"
        
        error_interface.codebase.files = [mock_file1, mock_file2]
        
        # Mock diagnostic responses
        mock_diagnostics = [
            {
                'file_path': 'test1.py',
                'line': 10,
                'character': 5,
                'message': 'Test error',
                'severity': 'error',
                'source': 'test',
                'code': 'TEST001',
                'has_fix': True
            }
        ]
        
        with patch.object(error_interface, '_get_file_diagnostics_placeholder') as mock_get_diag:
            mock_get_diag.return_value = mock_diagnostics
            
            errors = error_interface.errors()
            
            assert isinstance(errors, list)
            assert len(errors) == 2  # Called for each Python file
            
            # Check error structure
            for error in errors:
                assert 'id' in error
                assert 'file_path' in error
                assert 'severity' in error
                assert error['severity'] in ['error', 'warning', 'info', 'hint']
    
    def test_full_error_context_existing_error(self, error_interface):
        """Test full_error_context() with existing error."""
        # Setup error cache
        test_error = {
            'file_path': 'test.py',
            'line': 10,
            'message': 'Test error',
            'severity': 'error'
        }
        error_interface._error_cache['test_error_1'] = test_error
        
        # Mock file content
        with patch('builtins.open', mock_open_with_content("def test():\n    print('hello')\n    undefined_var\n")):
            context = error_interface.full_error_context('test_error_1')
        
        assert isinstance(context, dict)
        assert 'error' in context
        assert 'context' in context
        assert 'suggestions' in context
        assert 'fix_available' in context
        
        assert context['error'] == test_error
        assert isinstance(context['suggestions'], list)
        assert len(context['suggestions']) > 0
    
    def test_full_error_context_nonexistent_error(self, error_interface):
        """Test full_error_context() with nonexistent error."""
        context = error_interface.full_error_context('nonexistent_error')
        
        assert isinstance(context, dict)
        assert context['error'] is None
        assert 'suggestions' in context
        assert 'Error not found' in context['suggestions'][0]
    
    def test_resolve_errors_method(self, error_interface):
        """Test resolve_errors() method."""
        # Mock errors with some fixable
        mock_errors = [
            {'id': 'error_1', 'has_fix': True},
            {'id': 'error_2', 'has_fix': False},
            {'id': 'error_3', 'has_fix': True}
        ]
        
        with patch.object(error_interface, 'errors') as mock_errors_method:
            mock_errors_method.return_value = mock_errors
            
            with patch.object(error_interface, 'resolve_error') as mock_resolve:
                mock_resolve.side_effect = [
                    {'success': True, 'error_id': 'error_1'},
                    {'success': False, 'error_id': 'error_3'}
                ]
                
                result = error_interface.resolve_errors()
        
        assert isinstance(result, dict)
        assert result['total_errors'] == 3
        assert result['fixable_errors'] == 2
        assert result['fixed_errors'] == 1
        assert result['failed_fixes'] == 1
        assert len(result['results']) == 2
    
    def test_resolve_error_method_success(self, error_interface):
        """Test resolve_error() method with successful fix."""
        # Setup error cache
        test_error = {
            'file_path': 'test.py',
            'has_fix': True,
            'message': 'Test error'
        }
        error_interface._error_cache['test_error_1'] = test_error
        
        # Mock successful fix
        mock_fix_result = {
            'success': True,
            'message': 'Fix applied',
            'changes_made': ['Added import'],
            'fix_description': 'Added missing import'
        }
        
        with patch.object(error_interface, '_apply_error_fix') as mock_apply_fix:
            mock_apply_fix.return_value = mock_fix_result
            
            result = error_interface.resolve_error('test_error_1')
        
        assert result['error_id'] == 'test_error_1'
        assert result['success'] is True
        assert result['message'] == 'Fix applied'
        assert len(result['changes_made']) > 0
    
    def test_resolve_error_method_no_fix_available(self, error_interface):
        """Test resolve_error() method when no fix is available."""
        # Setup error cache without fix
        test_error = {
            'file_path': 'test.py',
            'has_fix': False,
            'message': 'Test error'
        }
        error_interface._error_cache['test_error_1'] = test_error
        
        result = error_interface.resolve_error('test_error_1')
        
        assert result['error_id'] == 'test_error_1'
        assert result['success'] is False
        assert 'No automatic fix available' in result['message']
    
    def test_build_error_context(self, error_interface):
        """Test _build_error_context() method."""
        # Mock file object
        mock_file = Mock()
        mock_file.functions = [Mock(name='test_func', line_number=10)]
        mock_file.classes = [Mock(name='TestClass', line_number=5)]
        mock_file.imports = [Mock(name='os'), Mock(name='sys')]
        
        error_interface.codebase.get_file.return_value = mock_file
        
        with patch('builtins.open', mock_open_with_content("def test():\n    print('hello')\n")):
            context = error_interface._build_error_context('test.py', 10)
        
        assert isinstance(context, dict)
        assert 'surrounding_code' in context
        assert 'function_context' in context
        assert 'class_context' in context
        assert 'imports' in context
        
        assert context['function_context'] == 'test_func'
        assert context['class_context'] == 'TestClass'
        assert len(context['imports']) == 2
    
    def test_generate_error_suggestions(self, error_interface):
        """Test _generate_error_suggestions() method."""
        test_cases = [
            {
                'error': {'message': 'undefined variable: test_var'},
                'expected_keywords': ['variable', 'defined', 'import']
            },
            {
                'error': {'message': 'import error: no module named test'},
                'expected_keywords': ['module', 'installed', 'import']
            },
            {
                'error': {'message': 'syntax error: invalid syntax'},
                'expected_keywords': ['syntax', 'parentheses', 'indentation']
            },
            {
                'error': {'message': 'type error: unsupported operand'},
                'expected_keywords': ['type', 'variable', 'function']
            }
        ]
        
        for test_case in test_cases:
            suggestions = error_interface._generate_error_suggestions(test_case['error'], {})
            
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
            
            # Check that suggestions contain relevant keywords
            suggestions_text = ' '.join(suggestions).lower()
            found_keywords = [kw for kw in test_case['expected_keywords'] if kw in suggestions_text]
            assert len(found_keywords) > 0, f"Expected keywords {test_case['expected_keywords']} not found in suggestions: {suggestions}"


class TestSerenaLSPIntegrationUnit:
    """Unit tests for SerenaLSPIntegration class."""
    
    def test_serena_lsp_integration_initialization(self):
        """Test SerenaLSPIntegration initialization."""
        with patch('graph_sitter.extensions.lsp.serena.lsp_integration.SerenaServerManager'):
            integration = SerenaLSPIntegration(
                codebase_path="/tmp/test",
                auto_discover_servers=True
            )
            
            assert integration.codebase_path == Path("/tmp/test")
            assert integration.auto_discover_servers is True
    
    def test_serena_config_initialization(self):
        """Test SerenaConfig initialization."""
        config = SerenaConfig()
        
        # Should have default values
        assert hasattr(config, '__dict__')


class TestCodebaseIntegration:
    """Test integration of unified error interface with Codebase class."""
    
    def test_add_unified_error_interface_to_codebase(self):
        """Test that unified error interface methods are added to Codebase class."""
        # Create a mock codebase class
        class MockCodebase:
            def __init__(self):
                self.repo_path = "/tmp/test"
        
        # Add unified error interface
        add_unified_error_interface(MockCodebase)
        
        # Check that methods were added
        methods_to_check = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error', '_get_error_interface']
        
        for method in methods_to_check:
            assert hasattr(MockCodebase, method), f"Method {method} should be added to codebase class"
            assert callable(getattr(MockCodebase, method)), f"Method {method} should be callable"
    
    def test_error_interface_instance_creation(self):
        """Test that error interface instance is created correctly."""
        class MockCodebase:
            def __init__(self):
                self.repo_path = "/tmp/test"
        
        add_unified_error_interface(MockCodebase)
        
        instance = MockCodebase()
        error_interface = instance._get_error_interface()
        
        assert isinstance(error_interface, UnifiedErrorInterface)
        assert error_interface.codebase == instance
        
        # Second call should return same instance
        error_interface2 = instance._get_error_interface()
        assert error_interface2 is error_interface
    
    def test_codebase_methods_delegation(self):
        """Test that codebase methods properly delegate to error interface."""
        class MockCodebase:
            def __init__(self):
                self.repo_path = "/tmp/test"
        
        add_unified_error_interface(MockCodebase)
        
        instance = MockCodebase()
        
        # Mock the error interface
        mock_interface = Mock()
        mock_interface.errors.return_value = ['error1', 'error2']
        mock_interface.full_error_context.return_value = {'context': 'test'}
        mock_interface.resolve_errors.return_value = {'fixed': 1}
        mock_interface.resolve_error.return_value = {'success': True}
        
        with patch.object(instance, '_get_error_interface', return_value=mock_interface):
            # Test method delegation
            errors = instance.errors()
            assert errors == ['error1', 'error2']
            mock_interface.errors.assert_called_once()
            
            context = instance.full_error_context('test_id')
            assert context == {'context': 'test'}
            mock_interface.full_error_context.assert_called_once_with('test_id')
            
            resolve_result = instance.resolve_errors()
            assert resolve_result == {'fixed': 1}
            mock_interface.resolve_errors.assert_called_once()
            
            resolve_single = instance.resolve_error('test_id')
            assert resolve_single == {'success': True}
            mock_interface.resolve_error.assert_called_once_with('test_id')


class TestErrorHandling:
    """Test error handling in unified error interface."""
    
    @pytest.fixture
    def error_interface_with_failing_lsp(self):
        """Create error interface with failing LSP integration."""
        mock_codebase = Mock()
        mock_codebase.repo_path = "/tmp/test"
        mock_codebase.files = []
        
        interface = UnifiedErrorInterface(mock_codebase)
        
        # Mock LSP integration to fail
        with patch.object(interface, '_ensure_lsp_integration') as mock_ensure:
            mock_ensure.side_effect = RuntimeError("LSP integration failed")
            yield interface
    
    def test_errors_method_lsp_failure(self, error_interface_with_failing_lsp):
        """Test errors() method when LSP integration fails."""
        errors = error_interface_with_failing_lsp.errors()
        
        # Should return empty list instead of crashing
        assert isinstance(errors, list)
        assert len(errors) == 0
    
    def test_full_error_context_lsp_failure(self, error_interface_with_failing_lsp):
        """Test full_error_context() method when LSP integration fails."""
        context = error_interface_with_failing_lsp.full_error_context('test_id')
        
        # Should return error context instead of crashing
        assert isinstance(context, dict)
        assert context['error'] is None
        assert 'suggestions' in context
    
    def test_resolve_errors_lsp_failure(self, error_interface_with_failing_lsp):
        """Test resolve_errors() method when LSP integration fails."""
        result = error_interface_with_failing_lsp.resolve_errors()
        
        # Should return error result instead of crashing
        assert isinstance(result, dict)
        assert result['total_errors'] == 0
        assert result['fixed_errors'] == 0


def mock_open_with_content(content):
    """Helper function to create mock open with specific content."""
    from unittest.mock import mock_open
    return mock_open(read_data=content)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])

