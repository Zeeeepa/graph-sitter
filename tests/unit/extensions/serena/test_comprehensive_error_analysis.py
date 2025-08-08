#!/usr/bin/env python3
"""
Comprehensive Error Analysis Tests

Tests for the comprehensive error analysis system that demonstrate actual usage
and validate functionality with real-world scenarios.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

# Import the components we're testing
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena.error_analysis import (
    ComprehensiveErrorAnalyzer,
    ErrorContext,
    ParameterIssue,
    FunctionCallInfo,
    analyze_codebase_errors,
    get_instant_error_context,
    get_all_codebase_errors_with_context
)
from graph_sitter.extensions.serena.api import (
    SerenaAPI,
    create_serena_api,
    get_codebase_error_analysis,
    analyze_file_errors,
    find_function_relationships
)
from graph_sitter.extensions.lsp.serena_bridge import ErrorInfo
from graph_sitter.core.diagnostics import DiagnosticSeverity


class TestComprehensiveErrorAnalyzer:
    """Test the ComprehensiveErrorAnalyzer with real usage scenarios."""
    
    @pytest.fixture
    def sample_codebase(self):
        """Create a sample codebase with known issues for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample Python files with various issues
            
            # File 1: Function with unused parameters
            file1_content = '''
def process_data(data, unused_param, another_unused):
    """Process data but ignore some parameters."""
    return data.upper()

def call_process_data():
    return process_data("hello", "unused", "also_unused")
'''
            
            # File 2: Function with undefined variable error
            file2_content = '''
import os
from pathlib import Path

def analyze_file(file_path):
    """Analyze a file but has undefined variable."""
    if os.path.exists(file_path):
        content = undefined_variable  # This will cause an error
        return len(content)
    return 0

def main():
    result = analyze_file("/tmp/test.txt")
    return result
'''
            
            # File 3: Import errors and function calls
            file3_content = '''
from .file1 import process_data
from .file2 import analyze_file
import nonexistent_module  # This will cause import error

def orchestrate_processing():
    """Orchestrate processing with dependencies."""
    data = process_data("test", "param1", "param2")
    size = analyze_file("test.txt")
    return data, size

def complex_function(a, b, c, d, e, f, g):
    """Function with too many parameters."""
    return a + b + c + d + e + f + g
'''
            
            # Write files to temp directory
            Path(temp_dir, "file1.py").write_text(file1_content)
            Path(temp_dir, "file2.py").write_text(file2_content)
            Path(temp_dir, "file3.py").write_text(file3_content)
            
            # Create codebase
            codebase = Codebase(temp_dir)
            yield codebase
    
    @pytest.fixture
    def mock_error_info(self):
        """Create mock ErrorInfo objects for testing."""
        errors = [
            ErrorInfo(
                file_path="file1.py",
                line=2,
                character=25,
                message="Unused parameter 'unused_param'",
                severity=DiagnosticSeverity.WARNING,
                source="pylint",
                code="W0613"
            ),
            ErrorInfo(
                file_path="file2.py", 
                line=8,
                character=16,
                message="Undefined variable 'undefined_variable'",
                severity=DiagnosticSeverity.ERROR,
                source="pylint",
                code="E0602"
            ),
            ErrorInfo(
                file_path="file3.py",
                line=3,
                character=7,
                message="Import 'nonexistent_module' could not be resolved",
                severity=DiagnosticSeverity.ERROR,
                source="pylint", 
                code="E0401"
            )
        ]
        return errors
    
    def test_analyzer_initialization(self, sample_codebase):
        """Test that the analyzer initializes correctly."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        assert analyzer.codebase == sample_codebase
        assert analyzer.diagnostics is not None
        assert hasattr(analyzer, '_error_cache')
        assert hasattr(analyzer, '_parameter_cache')
        assert hasattr(analyzer, '_call_graph_cache')
    
    @patch('graph_sitter.extensions.serena.error_analysis.SerenaMCPBridge')
    def test_serena_components_initialization(self, mock_mcp_bridge, sample_codebase):
        """Test that Serena components are initialized when available."""
        # Mock successful MCP bridge initialization
        mock_bridge_instance = Mock()
        mock_bridge_instance.is_initialized = True
        mock_mcp_bridge.return_value = mock_bridge_instance
        
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        assert analyzer.mcp_bridge is not None
        assert analyzer.semantic_tools is not None
        assert analyzer.code_intelligence is not None
    
    def test_get_all_errors(self, sample_codebase, mock_error_info):
        """Test getting all errors from the codebase."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Mock the diagnostics to return our test errors
        with patch.object(analyzer.diagnostics, 'errors', mock_error_info):
            errors = analyzer.get_all_errors()
            
            assert len(errors) == 3
            assert any("unused_param" in error.message for error in errors)
            assert any("undefined_variable" in error.message for error in errors)
            assert any("nonexistent_module" in error.message for error in errors)
    
    def test_analyze_error_context(self, sample_codebase, mock_error_info):
        """Test comprehensive error context analysis."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Test analyzing context for the undefined variable error
        undefined_var_error = mock_error_info[1]  # file2.py undefined variable
        
        context = analyzer.analyze_error_context(undefined_var_error)
        
        assert isinstance(context, ErrorContext)
        assert context.error_info == undefined_var_error
        assert context.code_context is not None
        assert len(context.fix_suggestions) > 0
        
        # Check that fix suggestions are relevant
        suggestions = context.fix_suggestions
        assert any("undefined" in suggestion.lower() for suggestion in suggestions)
    
    def test_parameter_analysis_via_ast(self, sample_codebase):
        """Test parameter analysis using AST fallback."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Test analyzing parameters in file1.py (has unused parameters)
        parameter_issues = analyzer._analyze_parameters_via_ast("file1.py", 2)
        
        # Should find unused parameters
        assert len(parameter_issues) > 0
        
        # Check that unused parameters are detected
        unused_params = [issue for issue in parameter_issues if issue.get('issue_type') == 'unused']
        assert len(unused_params) > 0
        
        # Verify parameter names
        param_names = [issue.get('parameter_name') for issue in unused_params]
        assert 'unused_param' in param_names or 'another_unused' in param_names
    
    def test_function_call_analysis(self, sample_codebase):
        """Test function call analysis via AST."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Test finding callers of process_data function
        callers = analyzer._find_callers_via_ast("file1.py", 2)
        
        # Should find calls from file1.py and file3.py
        assert len(callers) >= 1
        
        # Check that we found the caller
        caller_functions = [caller.get('function_name') for caller in callers]
        assert any(func in ['call_process_data', 'orchestrate_processing'] for func in caller_functions)
    
    def test_dependency_chain_building(self, sample_codebase):
        """Test building dependency chains from imports."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Test dependency chain for file3.py (has multiple imports)
        deps = analyzer._build_dependency_chain("file3.py")
        
        assert len(deps) > 0
        # Should include the imports we defined
        assert any('os' in dep or 'pathlib' in dep for dep in deps)
    
    def test_code_context_extraction(self, sample_codebase):
        """Test extracting code context around error lines."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Test getting context for line 8 in file2.py (undefined variable)
        context = analyzer._get_code_context("file2.py", 8)
        
        assert context is not None
        assert "undefined_variable" in context
        assert ">>>" in context  # Should highlight the error line
    
    def test_error_classification(self, sample_codebase):
        """Test error type classification."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Test different error message classifications
        assert analyzer._classify_error_type("Undefined variable 'x'") == "undefined_error"
        assert analyzer._classify_error_type("Import error: module not found") == "import_error"
        assert analyzer._classify_error_type("Syntax error: invalid syntax") == "syntax_error"
        assert analyzer._classify_error_type("Type error: expected int") == "type_error"
        assert analyzer._classify_error_type("Random error message") == "other_error"
    
    def test_error_summary_generation(self, sample_codebase, mock_error_info):
        """Test generating comprehensive error summary."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Mock the diagnostics
        with patch.object(analyzer.diagnostics, 'errors', mock_error_info), \
             patch.object(analyzer.diagnostics, 'warnings', []), \
             patch.object(analyzer.diagnostics, 'diagnostics', mock_error_info):
            
            summary = analyzer.get_error_summary()
            
            assert 'total_errors' in summary
            assert 'total_warnings' in summary
            assert 'total_diagnostics' in summary
            assert 'errors_by_file' in summary
            assert 'errors_by_type' in summary
            assert 'most_problematic_files' in summary
            
            # Check error counts
            assert summary['total_errors'] == 3
            assert len(summary['errors_by_file']) > 0
            assert len(summary['errors_by_type']) > 0
    
    def test_caching_mechanism(self, sample_codebase, mock_error_info):
        """Test that error analysis results are cached."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        error = mock_error_info[0]
        
        # First call should populate cache
        context1 = analyzer.analyze_error_context(error)
        cache_size_after_first = len(analyzer._error_cache)
        
        # Second call should use cache
        context2 = analyzer.analyze_error_context(error)
        cache_size_after_second = len(analyzer._error_cache)
        
        # Cache size should not increase on second call
        assert cache_size_after_first == cache_size_after_second
        assert context1 is context2  # Should be the same cached object
    
    def test_refresh_analysis(self, sample_codebase):
        """Test refreshing analysis data."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Add some data to caches
        analyzer._error_cache['test'] = Mock()
        analyzer._parameter_cache['test'] = Mock()
        analyzer._call_graph_cache['test'] = Mock()
        
        # Refresh should clear caches
        analyzer.refresh_analysis()
        
        assert len(analyzer._error_cache) == 0
        assert len(analyzer._parameter_cache) == 0
        assert len(analyzer._call_graph_cache) == 0
    
    def test_shutdown(self, sample_codebase):
        """Test proper shutdown of analyzer."""
        analyzer = ComprehensiveErrorAnalyzer(sample_codebase, enable_lsp=False)
        
        # Should not raise any exceptions
        analyzer.shutdown()


class TestSerenaAPI:
    """Test the SerenaAPI with real usage scenarios."""
    
    @pytest.fixture
    def sample_codebase(self):
        """Create a sample codebase for API testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file with issues
            content = '''
def unused_param_function(used, unused):
    """Function with unused parameter."""
    return used * 2

def caller_function():
    return unused_param_function(5, "not_used")

def undefined_var_function():
    return undefined_variable  # Error here
'''
            Path(temp_dir, "test_file.py").write_text(content)
            codebase = Codebase(temp_dir)
            yield codebase
    
    @pytest.fixture
    def mock_errors(self):
        """Mock errors for API testing."""
        return [
            ErrorInfo(
                file_path="test_file.py",
                line=2,
                character=30,
                message="Unused parameter 'unused'",
                severity=DiagnosticSeverity.WARNING,
                source="pylint",
                code="W0613"
            ),
            ErrorInfo(
                file_path="test_file.py",
                line=9,
                character=11,
                message="Undefined variable 'undefined_variable'",
                severity=DiagnosticSeverity.ERROR,
                source="pylint",
                code="E0602"
            )
        ]
    
    def test_api_initialization(self, sample_codebase):
        """Test SerenaAPI initialization."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        assert api.codebase == sample_codebase
        assert api.error_analyzer is not None
        assert api.core is not None
    
    def test_get_all_errors_basic(self, sample_codebase, mock_errors):
        """Test getting all errors through API."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        with patch.object(api.error_analyzer, 'get_all_errors', return_value=mock_errors):
            errors = api.get_all_errors()
            
            assert len(errors) == 2
            assert all('file_path' in error for error in errors)
            assert all('line' in error for error in errors)
            assert all('message' in error for error in errors)
            assert all('severity' in error for error in errors)
    
    def test_get_all_errors_with_context(self, sample_codebase, mock_errors):
        """Test getting errors with comprehensive context."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Mock error contexts
        mock_contexts = []
        for error in mock_errors:
            context = ErrorContext(error_info=error)
            context.calling_functions = [{'function_name': 'caller_function', 'file_path': 'test_file.py'}]
            context.called_functions = []
            context.parameter_issues = [{'issue_type': 'unused', 'parameter_name': 'unused'}] if 'unused' in error.message else []
            context.dependency_chain = ['os', 'sys']
            context.related_symbols = []
            context.code_context = "Sample code context"
            context.fix_suggestions = ["Remove unused parameter", "Define the variable"]
            mock_contexts.append(context)
        
        with patch('graph_sitter.extensions.serena.api.get_all_codebase_errors_with_context', return_value=mock_contexts):
            errors_with_context = api.get_all_errors_with_context()
            
            assert len(errors_with_context) == 2
            
            # Check structure of returned data
            for error_ctx in errors_with_context:
                assert 'error' in error_ctx
                assert 'calling_functions' in error_ctx
                assert 'called_functions' in error_ctx
                assert 'parameter_issues' in error_ctx
                assert 'dependency_chain' in error_ctx
                assert 'related_symbols' in error_ctx
                assert 'code_context' in error_ctx
                assert 'fix_suggestions' in error_ctx
    
    def test_get_unused_parameters(self, sample_codebase, mock_errors):
        """Test finding unused parameters across codebase."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Mock error contexts with parameter issues
        mock_contexts = [
            ErrorContext(
                error_info=mock_errors[0],
                parameter_issues=[{
                    'issue_type': 'unused',
                    'parameter_name': 'unused',
                    'function_name': 'unused_param_function',
                    'suggestion': "Remove unused parameter 'unused'"
                }]
            )
        ]
        
        with patch('graph_sitter.extensions.serena.api.get_all_codebase_errors_with_context', return_value=mock_contexts):
            unused_params = api.get_unused_parameters()
            
            assert len(unused_params) == 1
            assert unused_params[0]['parameter_name'] == 'unused'
            assert unused_params[0]['function_name'] == 'unused_param_function'
            assert 'suggestion' in unused_params[0]
    
    def test_get_wrong_parameters(self, sample_codebase):
        """Test finding wrongly typed parameters."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Mock error contexts with wrong parameter types
        mock_contexts = [
            ErrorContext(
                error_info=Mock(file_path="test.py", line=5),
                parameter_issues=[{
                    'issue_type': 'wrong_type',
                    'parameter_name': 'count',
                    'function_name': 'process_count',
                    'expected_type': 'int',
                    'actual_type': 'str',
                    'suggestion': "Convert parameter to int"
                }]
            )
        ]
        
        with patch('graph_sitter.extensions.serena.api.get_all_codebase_errors_with_context', return_value=mock_contexts):
            wrong_params = api.get_wrong_parameters()
            
            assert len(wrong_params) == 1
            assert wrong_params[0]['parameter_name'] == 'count'
            assert wrong_params[0]['issue_type'] == 'wrong_type'
            assert wrong_params[0]['expected_type'] == 'int'
            assert wrong_params[0]['actual_type'] == 'str'
    
    def test_get_function_callers(self, sample_codebase):
        """Test finding function callers."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Mock semantic search results
        mock_search_results = [
            {
                'symbol_name': 'caller_function',
                'file': 'test_file.py',
                'line': 6,
                'context': 'return unused_param_function(5, "not_used")',
                'score': 0.95
            }
        ]
        
        # Mock semantic search
        mock_semantic_search = Mock()
        mock_semantic_search.semantic_search.return_value = mock_search_results
        api.semantic_search = mock_semantic_search
        
        callers = api.get_function_callers('unused_param_function')
        
        assert len(callers) == 1
        assert callers[0]['caller_function'] == 'caller_function'
        assert callers[0]['file_path'] == 'test_file.py'
        assert callers[0]['line_number'] == 6
    
    def test_find_symbol_usage(self, sample_codebase):
        """Test finding symbol usage across codebase."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Mock semantic search results
        mock_search_results = [
            {
                'symbol_name': 'unused_param_function',
                'symbol_type': 'function',
                'file': 'test_file.py',
                'line': 2,
                'context': 'def unused_param_function(used, unused):',
                'score': 1.0
            },
            {
                'symbol_name': 'unused_param_function',
                'symbol_type': 'function_call',
                'file': 'test_file.py',
                'line': 6,
                'context': 'return unused_param_function(5, "not_used")',
                'score': 0.9
            }
        ]
        
        # Mock semantic search
        mock_semantic_search = Mock()
        mock_semantic_search.semantic_search.return_value = mock_search_results
        api.semantic_search = mock_semantic_search
        
        usage = api.find_symbol_usage('unused_param_function')
        
        assert len(usage) == 2
        assert all('symbol_name' in u for u in usage)
        assert all('file_path' in u for u in usage)
        assert all('line_number' in u for u in usage)
    
    def test_get_dependency_graph(self, sample_codebase):
        """Test getting dependency graph for codebase."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Mock file dependencies
        with patch.object(api, 'get_file_dependencies') as mock_get_deps:
            mock_get_deps.return_value = ['os', 'sys', 'pathlib']
            
            dep_graph = api.get_dependency_graph()
            
            assert isinstance(dep_graph, dict)
            assert len(dep_graph) > 0
            
            # Should have dependencies for Python files
            python_files = [path for path in dep_graph.keys() if path.endswith('.py')]
            assert len(python_files) > 0
    
    def test_get_status(self, sample_codebase):
        """Test getting API status information."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        status = api.get_status()
        
        # Check required status fields
        required_fields = [
            'error_analyzer_initialized',
            'mcp_bridge_available',
            'semantic_tools_available',
            'code_intelligence_available',
            'symbol_intelligence_available',
            'semantic_search_available',
            'lsp_enabled',
            'lsp_status',
            'total_errors',
            'total_warnings',
            'total_diagnostics'
        ]
        
        for field in required_fields:
            assert field in status
    
    def test_api_shutdown(self, sample_codebase):
        """Test proper API shutdown."""
        api = SerenaAPI(sample_codebase, enable_lsp=False)
        
        # Should not raise any exceptions
        api.shutdown()


class TestConvenienceFunctions:
    """Test convenience functions for quick analysis."""
    
    @pytest.fixture
    def sample_codebase(self):
        """Create sample codebase for convenience function testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content = '''
def test_function(param1, unused_param):
    return param1 + 1

def main():
    return test_function(5, "unused")
'''
            Path(temp_dir, "main.py").write_text(content)
            codebase = Codebase(temp_dir)
            yield codebase
    
    def test_create_serena_api(self, sample_codebase):
        """Test create_serena_api convenience function."""
        api = create_serena_api(sample_codebase, enable_lsp=False)
        
        assert isinstance(api, SerenaAPI)
        assert api.codebase == sample_codebase
        
        # Clean up
        api.shutdown()
    
    def test_analyze_codebase_errors(self, sample_codebase):
        """Test analyze_codebase_errors convenience function."""
        analyzer = analyze_codebase_errors(sample_codebase, enable_lsp=False)
        
        assert isinstance(analyzer, ComprehensiveErrorAnalyzer)
        assert analyzer.codebase == sample_codebase
    
    @patch('graph_sitter.extensions.serena.error_analysis.get_all_codebase_errors_with_context')
    def test_get_codebase_error_analysis(self, mock_get_contexts, sample_codebase):
        """Test get_codebase_error_analysis convenience function."""
        # Mock the contexts
        mock_get_contexts.return_value = []
        
        with patch('graph_sitter.extensions.serena.api.SerenaAPI') as mock_api_class:
            mock_api = Mock()
            mock_api.get_error_summary.return_value = {'total_errors': 0}
            mock_api.get_unused_parameters.return_value = []
            mock_api.get_wrong_parameters.return_value = []
            mock_api.get_dependency_graph.return_value = {}
            mock_api.get_status.return_value = {'initialized': True}
            mock_api_class.return_value = mock_api
            
            analysis = get_codebase_error_analysis(sample_codebase)
            
            assert 'error_summary' in analysis
            assert 'all_errors_with_context' in analysis
            assert 'unused_parameters' in analysis
            assert 'wrong_parameters' in analysis
            assert 'dependency_graph' in analysis
            assert 'status' in analysis
    
    @patch('graph_sitter.extensions.serena.api.SerenaAPI')
    def test_analyze_file_errors(self, mock_api_class, sample_codebase):
        """Test analyze_file_errors convenience function."""
        mock_api = Mock()
        mock_api.get_file_errors.return_value = [
            {'file_path': 'main.py', 'line': 2, 'message': 'Test error'}
        ]
        mock_api.get_error_context.return_value = {
            'error': {'message': 'Test error'},
            'calling_functions': [],
            'called_functions': []
        }
        mock_api.get_file_dependencies.return_value = ['os']
        mock_api_class.return_value = mock_api
        
        result = analyze_file_errors(sample_codebase, "main.py")
        
        assert 'file_path' in result
        assert 'errors' in result
        assert 'error_contexts' in result
        assert 'dependencies' in result
        assert result['file_path'] == "main.py"
    
    @patch('graph_sitter.extensions.serena.api.SerenaAPI')
    def test_find_function_relationships(self, mock_api_class, sample_codebase):
        """Test find_function_relationships convenience function."""
        mock_api = Mock()
        mock_api.get_function_callers.return_value = [
            {'caller_function': 'main', 'file_path': 'main.py'}
        ]
        mock_api.get_function_calls.return_value = []
        mock_api.find_symbol_usage.return_value = [
            {'symbol_name': 'test_function', 'file_path': 'main.py', 'line_number': 2}
        ]
        mock_api.get_related_symbols.return_value = []
        mock_api_class.return_value = mock_api
        
        result = find_function_relationships(sample_codebase, "test_function", "main.py")
        
        assert 'function_name' in result
        assert 'file_path' in result
        assert 'callers' in result
        assert 'calls' in result
        assert 'symbol_usage' in result
        assert 'related_symbols' in result
        assert result['function_name'] == "test_function"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
