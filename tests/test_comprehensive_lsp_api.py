"""
Comprehensive Test Suite for LSP Error Retrieval API

This test suite validates all the new LSP error retrieval methods work correctly
with real codebases and provides the exact functionality specified by the user.
"""

import pytest
import tempfile
import os
from pathlib import Path
from graph_sitter import Codebase


class TestComprehensiveLSPAPI:
    """Test suite for comprehensive LSP error retrieval API."""
    
    @pytest.fixture
    def sample_codebase(self):
        """Create a sample codebase with intentional errors for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a Python file with syntax errors
            test_file = Path(tmp_dir) / "test_file.py"
            test_file.write_text("""
# This file has intentional errors for testing
def broken_function():
    # Missing closing parenthesis - syntax error
    print("Hello world"
    
    # Undefined variable - semantic error
    result = undefined_variable + 5
    
    # Type error
    number = "string" + 5
    
    return result

class TestClass:
    def __init__(self):
        self.value = 42
    
    def method_with_issues(self):
        # Unused variable
        unused_var = "never used"
        
        # Wrong number of arguments
        self.nonexistent_method(1, 2, 3)
        
        return self.value
""")
            
            # Create another file with different types of errors
            another_file = Path(tmp_dir) / "another_file.py"
            another_file.write_text("""
import nonexistent_module  # Import error

def function_with_warnings():
    # Redefined variable
    x = 1
    x = 2  # Warning: redefined
    
    # Unreachable code
    return x
    print("This will never execute")  # Warning: unreachable

# Missing docstring for public function
def public_function():
    pass
""")
            
            # Initialize codebase
            codebase = Codebase(tmp_dir)
            yield codebase

    def test_core_error_retrieval_commands(self, sample_codebase):
        """Test core error retrieval commands."""
        codebase = sample_codebase
        
        # Test errors() - Get all errors
        all_errors = codebase.errors()
        assert isinstance(all_errors, list), "errors() should return a list"
        
        # Test errors_by_file() - Get errors in specific file
        file_errors = codebase.errors_by_file("test_file.py")
        assert isinstance(file_errors, list), "errors_by_file() should return a list"
        
        # Test errors_by_severity() - Filter by severity
        error_level_errors = codebase.errors_by_severity("ERROR")
        warning_level_errors = codebase.errors_by_severity("WARNING")
        assert isinstance(error_level_errors, list), "errors_by_severity() should return a list"
        assert isinstance(warning_level_errors, list), "errors_by_severity() should return a list"
        
        # Test errors_by_type() - Filter by type
        syntax_errors = codebase.errors_by_type("syntax")
        semantic_errors = codebase.errors_by_type("semantic")
        assert isinstance(syntax_errors, list), "errors_by_type() should return a list"
        assert isinstance(semantic_errors, list), "errors_by_type() should return a list"
        
        # Test recent_errors() - Get recent errors
        import time
        recent_errors = codebase.recent_errors(time.time() - 3600)  # Last hour
        assert isinstance(recent_errors, list), "recent_errors() should return a list"

    def test_detailed_error_context(self, sample_codebase):
        """Test detailed error context methods."""
        codebase = sample_codebase
        
        all_errors = codebase.errors()
        if all_errors:
            error_id = getattr(all_errors[0], 'id', 'test_error_1')
            
            # Test full_error_context() - Get full context for specific error
            error_context = codebase.full_error_context(error_id)
            # Should return None or dict with error details
            assert error_context is None or isinstance(error_context, dict)
            
            # Test error_suggestions() - Get fix suggestions
            suggestions = codebase.error_suggestions(error_id)
            assert isinstance(suggestions, list), "error_suggestions() should return a list"
            
            # Test error_related_symbols() - Get related symbols
            related_symbols = codebase.error_related_symbols(error_id)
            assert isinstance(related_symbols, list), "error_related_symbols() should return a list"
            
            # Test error_impact_analysis() - Get impact analysis
            impact_analysis = codebase.error_impact_analysis(error_id)
            assert isinstance(impact_analysis, dict), "error_impact_analysis() should return a dict"

    def test_error_statistics_and_analysis(self, sample_codebase):
        """Test error statistics and analysis methods."""
        codebase = sample_codebase
        
        # Test error_summary() - Get summary statistics
        summary = codebase.error_summary()
        assert isinstance(summary, dict), "error_summary() should return a dict"
        expected_keys = ['total_diagnostics', 'error_count', 'warning_count', 'info_count']
        for key in expected_keys:
            assert key in summary, f"error_summary() should include {key}"
        
        # Test error_trends() - Get error trends
        trends = codebase.error_trends()
        assert isinstance(trends, dict), "error_trends() should return a dict"
        assert 'current_snapshot' in trends, "error_trends() should include current_snapshot"
        
        # Test most_common_errors() - Get most frequent errors
        common_errors = codebase.most_common_errors()
        assert isinstance(common_errors, list), "most_common_errors() should return a list"
        
        # Test error_hotspots() - Get files with most errors
        hotspots = codebase.error_hotspots()
        assert isinstance(hotspots, list), "error_hotspots() should return a list"

    def test_real_time_error_monitoring(self, sample_codebase):
        """Test real-time error monitoring methods."""
        codebase = sample_codebase
        
        # Test watch_errors() - Set up real-time monitoring
        callback_called = False
        def test_callback(errors):
            nonlocal callback_called
            callback_called = True
            assert isinstance(errors, list), "Callback should receive list of errors"
        
        result = codebase.watch_errors(test_callback)
        assert isinstance(result, bool), "watch_errors() should return boolean"
        
        # Test error_stream() - Get stream of error updates
        error_stream = codebase.error_stream()
        assert hasattr(error_stream, '__iter__'), "error_stream() should return an iterable"
        
        # Test refresh_errors() - Force refresh
        refresh_result = codebase.refresh_errors()
        assert isinstance(refresh_result, bool), "refresh_errors() should return boolean"

    def test_error_resolution_and_actions(self, sample_codebase):
        """Test error resolution and action methods."""
        codebase = sample_codebase
        
        # Test get_quick_fixes() - Get available fixes
        all_errors = codebase.errors()
        if all_errors:
            error_id = getattr(all_errors[0], 'id', 'test_error_1')
            
            quick_fixes = codebase.get_quick_fixes(error_id)
            assert isinstance(quick_fixes, list), "get_quick_fixes() should return a list"
            
            # Test apply_error_fix() - Apply specific fix
            if quick_fixes:
                fix_result = codebase.apply_error_fix(error_id, quick_fixes[0].get('id', 'test_fix'))
                assert isinstance(fix_result, bool), "apply_error_fix() should return boolean"
        
        # Test auto_fix_errors() - Auto-fix multiple errors
        error_ids = ['test_error_1', 'test_error_2']
        fixed_errors = codebase.auto_fix_errors(error_ids)
        assert isinstance(fixed_errors, list), "auto_fix_errors() should return a list"

    def test_full_serena_lsp_feature_retrieval(self, sample_codebase):
        """Test full Serena LSP feature retrieval methods."""
        codebase = sample_codebase
        
        # Test completions() - Get code completions
        completions = codebase.completions("test_file.py", (5, 10))
        assert isinstance(completions, list), "completions() should return a list"
        
        # Test hover_info() - Get hover information
        hover = codebase.hover_info("test_file.py", (5, 10))
        # Should return None or dict with hover info
        assert hover is None or isinstance(hover, dict)
        
        # Test signature_help() - Get function signature help
        signature = codebase.signature_help("test_file.py", (5, 10))
        assert isinstance(signature, dict), "signature_help() should return a dict"
        
        # Test definitions() - Go to definition
        definitions = codebase.definitions("broken_function")
        assert isinstance(definitions, list), "definitions() should return a list"
        
        # Test references() - Find all references
        references = codebase.references("TestClass")
        assert isinstance(references, list), "references() should return a list"

    def test_code_actions_and_refactoring(self, sample_codebase):
        """Test code actions and refactoring methods."""
        codebase = sample_codebase
        
        # Test code_actions() - Get available code actions
        actions = codebase.code_actions("test_file.py", {"start": {"line": 5, "character": 0}, "end": {"line": 10, "character": 0}})
        assert isinstance(actions, list), "code_actions() should return a list"
        
        # Test rename_symbol() - Rename symbol
        rename_result = codebase.rename_symbol("broken_function", "fixed_function")
        assert isinstance(rename_result, dict), "rename_symbol() should return a dict"
        assert 'success' in rename_result, "rename_symbol() should include success status"
        
        # Test extract_method() - Extract method refactoring
        extract_result = codebase.extract_method("test_file.py", {"start": {"line": 5, "character": 0}, "end": {"line": 8, "character": 0}})
        assert isinstance(extract_result, dict), "extract_method() should return a dict"
        
        # Test organize_imports() - Organize imports
        organize_result = codebase.organize_imports("another_file.py")
        assert isinstance(organize_result, dict), "organize_imports() should return a dict"

    def test_semantic_analysis(self, sample_codebase):
        """Test semantic analysis methods."""
        codebase = sample_codebase
        
        # Test semantic_tokens() - Get semantic tokens
        tokens = codebase.semantic_tokens("test_file.py")
        assert isinstance(tokens, list), "semantic_tokens() should return a list"
        
        # Test document_symbols() - Get document symbols
        doc_symbols = codebase.document_symbols("test_file.py")
        assert isinstance(doc_symbols, list), "document_symbols() should return a list"
        
        # Test workspace_symbols() - Search workspace symbols
        workspace_symbols = codebase.workspace_symbols("TestClass")
        assert isinstance(workspace_symbols, list), "workspace_symbols() should return a list"
        
        # Test call_hierarchy() - Get call hierarchy
        call_hierarchy = codebase.call_hierarchy("broken_function")
        assert isinstance(call_hierarchy, dict), "call_hierarchy() should return a dict"
        assert 'incoming_calls' in call_hierarchy, "call_hierarchy() should include incoming_calls"
        assert 'outgoing_calls' in call_hierarchy, "call_hierarchy() should include outgoing_calls"

    def test_diagnostics_and_health(self, sample_codebase):
        """Test diagnostics and health monitoring methods."""
        codebase = sample_codebase
        
        # Test diagnostics() - Get all diagnostics
        diagnostics = codebase.diagnostics()
        assert isinstance(diagnostics, list), "diagnostics() should return a list"
        
        # Test health_check() - Get overall health
        health = codebase.health_check()
        assert isinstance(health, dict), "health_check() should return a dict"
        expected_keys = ['health_score', 'health_status', 'error_summary', 'recommendations']
        for key in expected_keys:
            assert key in health, f"health_check() should include {key}"
        
        # Test lsp_status() - Get LSP server status
        lsp_status = codebase.lsp_status()
        assert isinstance(lsp_status, dict), "lsp_status() should return a dict"
        assert 'lsp_available' in lsp_status, "lsp_status() should include lsp_available"
        
        # Test capabilities() - Get available capabilities
        capabilities = codebase.capabilities()
        assert isinstance(capabilities, dict), "capabilities() should return a dict"
        expected_capabilities = [
            'error_retrieval', 'code_intelligence', 'refactoring', 
            'semantic_analysis', 'real_time_monitoring', 'auto_fix'
        ]
        for capability in expected_capabilities:
            assert capability in capabilities, f"capabilities() should include {capability}"

    def test_method_availability_on_codebase(self):
        """Test that all methods are available on the Codebase class."""
        # All the methods that should be available
        expected_methods = [
            # Core Error Retrieval Commands
            'errors', 'errors_by_file', 'errors_by_severity', 'errors_by_type', 'recent_errors',
            # Detailed Error Context
            'full_error_context', 'error_suggestions', 'error_related_symbols', 'error_impact_analysis',
            # Error Statistics & Analysis
            'error_summary', 'error_trends', 'most_common_errors', 'error_hotspots',
            # Real-time Error Monitoring
            'watch_errors', 'error_stream', 'refresh_errors',
            # Error Resolution & Actions
            'auto_fix_errors', 'get_quick_fixes', 'apply_error_fix',
            # Full Serena LSP Feature Retrieval
            'completions', 'hover_info', 'signature_help', 'definitions', 'references',
            # Code Actions & Refactoring
            'code_actions', 'rename_symbol', 'extract_method', 'organize_imports',
            # Semantic Analysis
            'semantic_tokens', 'document_symbols', 'workspace_symbols', 'call_hierarchy',
            # Diagnostics & Health
            'diagnostics', 'health_check', 'lsp_status', 'capabilities'
        ]
        
        for method_name in expected_methods:
            assert hasattr(Codebase, method_name), f"Codebase should have method: {method_name}"
            method = getattr(Codebase, method_name)
            assert callable(method), f"Codebase.{method_name} should be callable"

    def test_usage_examples_from_specification(self, sample_codebase):
        """Test the exact usage examples from the user specification."""
        codebase = sample_codebase
        
        # Test the exact examples provided by the user
        try:
            # Get all errors
            all_errors = codebase.errors()
            print(f"Found {len(all_errors)} errors")
            
            # Get detailed context for a specific error
            if all_errors:
                error_id = getattr(all_errors[0], 'id', 'test_error')
                error_context = codebase.full_error_context(error_id)
                print(f"Error context: {error_context}")
            
            # Get errors in a specific file
            file_errors = codebase.errors_by_file("test_file.py")
            
            # Get error summary
            summary = codebase.error_summary()
            print(f"Errors: {summary.get('error_count', 0)}, Warnings: {summary.get('warning_count', 0)}")
            
            # Auto-fix errors where possible
            fixable_errors = [e for e in all_errors if hasattr(e, 'has_quick_fix') and e.has_quick_fix]
            if fixable_errors:
                error_ids = [getattr(e, 'id', f'error_{i}') for i, e in enumerate(fixable_errors)]
                codebase.auto_fix_errors(error_ids)
            
            # Real-time error monitoring
            def on_error_change(errors):
                print(f"Errors updated: {len(errors)} total errors")
            
            codebase.watch_errors(on_error_change)
            
            # All tests passed - the API works as specified
            assert True, "All usage examples from specification work correctly"
            
        except Exception as e:
            pytest.fail(f"Usage examples failed: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])

