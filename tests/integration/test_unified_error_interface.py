#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Unified Error Interface

This test suite provides thorough testing of all unified error interface methods:
- codebase.errors()
- codebase.full_error_context(error_id)
- codebase.resolve_errors()
- codebase.resolve_error(error_id)

Tests cover real LSP integration, edge cases, performance, and error handling.
"""

import os
import sys
import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from graph_sitter import Codebase
    from graph_sitter.enhanced.codebase import Codebase as EnhancedCodebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    pytest.skip("Graph-sitter not available", allow_module_level=True)


class TestUnifiedErrorInterface:
    """Comprehensive test suite for the unified error interface."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test Python files with various types of errors
        test_files = {
            "syntax_error.py": '''
def broken_function(
    print("Missing closing parenthesis")
    return "syntax error"
''',
            "import_error.py": '''
import nonexistent_module
from another_fake_module import something

def test_function():
    return something
''',
            "type_error.py": '''
def add_numbers(a: int, b: int) -> int:
    return a + b

# Type error: passing string to int function
result = add_numbers("hello", 42)
''',
            "undefined_variable.py": '''
def use_undefined():
    print(undefined_variable)  # NameError
    return some_other_undefined_var
''',
            "valid_file.py": '''
"""A valid Python file with no errors."""

def hello_world():
    """Print hello world."""
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
''',
            "complex_errors.py": '''
import os
import sys
from typing import List, Dict

class TestClass:
    def __init__(self):
        self.value = undefined_var  # NameError
    
    def method_with_issues(self, param):
        # Multiple issues in one method
        result = param + "string"  # Potential type error
        return result.nonexistent_method()  # AttributeError
    
    def unused_method(self):
        """This method is never called."""
        pass

def function_with_many_params(a, b, c, d, e, f, g, h, i, j):
    """Function with too many parameters."""
    return a + b + c + d + e + f + g + h + i + j

# Missing docstring
def no_docstring():
    pass
'''
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def codebase(self, temp_project_dir):
        """Create a codebase instance for testing."""
        return EnhancedCodebase(temp_project_dir)
    
    def test_errors_method_basic_functionality(self, codebase):
        """Test basic functionality of the errors() method."""
        # Test that the method exists and returns a list
        errors = codebase.errors()
        assert isinstance(errors, list), "errors() should return a list"
        
        # Test return format
        for error in errors:
            assert isinstance(error, dict), "Each error should be a dictionary"
            required_fields = ['id', 'file_path', 'line', 'character', 'message', 'severity', 'source']
            for field in required_fields:
                assert field in error, f"Error should contain '{field}' field"
    
    def test_errors_method_with_real_files(self, codebase):
        """Test errors() method with files containing actual errors."""
        errors = codebase.errors()
        
        # We should get some errors from our test files
        # Note: Actual count depends on LSP server implementation
        print(f"Found {len(errors)} errors in test files")
        
        if errors:
            # Test error structure
            sample_error = errors[0]
            assert 'id' in sample_error
            assert 'file_path' in sample_error
            assert 'severity' in sample_error
            assert sample_error['severity'] in ['error', 'warning', 'info', 'hint']
    
    def test_errors_method_performance(self, codebase):
        """Test performance of errors() method."""
        start_time = time.time()
        errors = codebase.errors()
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"errors() execution time: {execution_time:.3f} seconds")
        
        # Should complete within reasonable time (adjust based on your requirements)
        assert execution_time < 30.0, f"errors() took too long: {execution_time:.3f}s"
    
    def test_errors_method_caching(self, codebase):
        """Test that errors() method implements caching for performance."""
        # First call
        start_time = time.time()
        errors1 = codebase.errors()
        first_call_time = time.time() - start_time
        
        # Second call (should be faster due to caching)
        start_time = time.time()
        errors2 = codebase.errors()
        second_call_time = time.time() - start_time
        
        print(f"First call: {first_call_time:.3f}s, Second call: {second_call_time:.3f}s")
        
        # Results should be identical
        assert len(errors1) == len(errors2), "Cached results should be identical"
        
        # Second call should be faster (allowing some variance)
        # Note: This might not always be true depending on implementation
        if first_call_time > 0.1:  # Only test if first call was significant
            assert second_call_time <= first_call_time * 1.5, "Second call should benefit from caching"
    
    def test_full_error_context_method(self, codebase):
        """Test full_error_context() method functionality."""
        errors = codebase.errors()
        
        if errors:
            error_id = errors[0]['id']
            context = codebase.full_error_context(error_id)
            
            # Test return structure
            assert isinstance(context, dict), "full_error_context() should return a dictionary"
            
            required_fields = ['error', 'context', 'suggestions', 'fix_available']
            for field in required_fields:
                assert field in context, f"Context should contain '{field}' field"
            
            # Test context structure
            assert isinstance(context['context'], dict), "Context should be a dictionary"
            assert isinstance(context['suggestions'], list), "Suggestions should be a list"
            assert isinstance(context['fix_available'], bool), "fix_available should be boolean"
    
    def test_full_error_context_with_invalid_id(self, codebase):
        """Test full_error_context() with invalid error ID."""
        context = codebase.full_error_context("invalid_error_id")
        
        assert isinstance(context, dict), "Should return dict even for invalid ID"
        assert context['error'] is None, "Error should be None for invalid ID"
        assert 'suggestions' in context, "Should provide suggestions even for invalid ID"
    
    def test_full_error_context_detailed_info(self, codebase):
        """Test that full_error_context() provides detailed contextual information."""
        errors = codebase.errors()
        
        if errors:
            error_id = errors[0]['id']
            context = codebase.full_error_context(error_id)
            
            # Check for detailed context information
            ctx = context['context']
            expected_context_fields = ['surrounding_code', 'function_context', 'class_context', 'imports']
            
            for field in expected_context_fields:
                assert field in ctx, f"Context should include '{field}'"
            
            # Test suggestions quality
            suggestions = context['suggestions']
            assert len(suggestions) > 0, "Should provide at least one suggestion"
            
            for suggestion in suggestions:
                assert isinstance(suggestion, str), "Each suggestion should be a string"
                assert len(suggestion) > 10, "Suggestions should be meaningful"
    
    def test_resolve_errors_method(self, codebase):
        """Test resolve_errors() method functionality."""
        result = codebase.resolve_errors()
        
        # Test return structure
        assert isinstance(result, dict), "resolve_errors() should return a dictionary"
        
        required_fields = ['total_errors', 'fixable_errors', 'fixed_errors', 'failed_fixes', 'results']
        for field in required_fields:
            assert field in result, f"Result should contain '{field}' field"
        
        # Test field types
        assert isinstance(result['total_errors'], int), "total_errors should be integer"
        assert isinstance(result['fixable_errors'], int), "fixable_errors should be integer"
        assert isinstance(result['fixed_errors'], int), "fixed_errors should be integer"
        assert isinstance(result['failed_fixes'], int), "failed_fixes should be integer"
        assert isinstance(result['results'], list), "results should be a list"
        
        # Test logical consistency
        assert result['fixed_errors'] + result['failed_fixes'] == len(result['results']), \
            "Sum of fixed and failed should equal results count"
    
    def test_resolve_error_method(self, codebase):
        """Test resolve_error() method functionality."""
        errors = codebase.errors()
        
        if errors:
            error_id = errors[0]['id']
            result = codebase.resolve_error(error_id)
            
            # Test return structure
            assert isinstance(result, dict), "resolve_error() should return a dictionary"
            
            required_fields = ['error_id', 'success', 'message', 'changes_made']
            for field in required_fields:
                assert field in result, f"Result should contain '{field}' field"
            
            # Test field types
            assert result['error_id'] == error_id, "Should return the same error ID"
            assert isinstance(result['success'], bool), "success should be boolean"
            assert isinstance(result['message'], str), "message should be string"
            assert isinstance(result['changes_made'], list), "changes_made should be list"
    
    def test_resolve_error_with_invalid_id(self, codebase):
        """Test resolve_error() with invalid error ID."""
        result = codebase.resolve_error("invalid_error_id")
        
        assert isinstance(result, dict), "Should return dict even for invalid ID"
        assert result['error_id'] == "invalid_error_id", "Should return the provided ID"
        assert result['success'] is False, "Should indicate failure for invalid ID"
        assert 'not found' in result['message'].lower(), "Should indicate error not found"
    
    def test_error_interface_integration(self, codebase):
        """Test integration between all error interface methods."""
        # Get errors
        errors = codebase.errors()
        print(f"Integration test found {len(errors)} errors")
        
        if errors:
            # Test workflow: errors -> context -> resolution
            error_id = errors[0]['id']
            
            # Get context
            context = codebase.full_error_context(error_id)
            assert context['error'] is not None, "Context should contain error info"
            
            # Try to resolve
            resolution = codebase.resolve_error(error_id)
            assert resolution['error_id'] == error_id, "Resolution should reference correct error"
            
            # Test bulk resolution
            bulk_result = codebase.resolve_errors()
            assert bulk_result['total_errors'] >= len(errors), "Bulk result should account for all errors"
    
    def test_error_severity_filtering(self, codebase):
        """Test that errors are properly categorized by severity."""
        errors = codebase.errors()
        
        severity_counts = {'error': 0, 'warning': 0, 'info': 0, 'hint': 0}
        
        for error in errors:
            severity = error.get('severity', 'unknown')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        print(f"Severity distribution: {severity_counts}")
        
        # Should have at least some categorization
        total_categorized = sum(severity_counts.values())
        assert total_categorized == len(errors), "All errors should have valid severity"
    
    def test_error_source_attribution(self, codebase):
        """Test that errors are properly attributed to their sources."""
        errors = codebase.errors()
        
        sources = set()
        for error in errors:
            source = error.get('source', 'unknown')
            sources.add(source)
        
        print(f"Error sources found: {sources}")
        
        # Should have meaningful source attribution
        assert len(sources) > 0, "Should have at least one error source"
        assert 'unknown' not in sources or len(sources) > 1, "Should have specific source attribution"
    
    def test_concurrent_access(self, codebase):
        """Test thread safety of error interface methods."""
        import threading
        import concurrent.futures
        
        results = []
        errors_list = []
        
        def get_errors():
            try:
                errors = codebase.errors()
                errors_list.append(len(errors))
                return len(errors)
            except Exception as e:
                results.append(f"Error: {e}")
                return 0
        
        def get_context():
            try:
                errors = codebase.errors()
                if errors:
                    context = codebase.full_error_context(errors[0]['id'])
                    return len(context.get('suggestions', []))
                return 0
            except Exception as e:
                results.append(f"Context Error: {e}")
                return 0
        
        # Test concurrent access
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            # Submit multiple concurrent requests
            for _ in range(5):
                futures.append(executor.submit(get_errors))
                futures.append(executor.submit(get_context))
            
            # Wait for completion
            concurrent.futures.wait(futures)
        
        # Check results
        if errors_list:
            # All error counts should be consistent
            assert len(set(errors_list)) <= 2, "Error counts should be consistent across threads"
        
        # Should not have any exceptions
        exception_results = [r for r in results if 'Error:' in str(r)]
        assert len(exception_results) == 0, f"Should not have thread safety issues: {exception_results}"
    
    def test_large_codebase_performance(self, temp_project_dir):
        """Test performance with a larger codebase."""
        # Create additional files to simulate larger codebase
        large_dir = Path(temp_project_dir) / "large_project"
        large_dir.mkdir()
        
        # Create 20 files with various content
        for i in range(20):
            file_content = f'''
"""Module {i} for performance testing."""

import os
import sys
from typing import List, Dict, Optional

class TestClass{i}:
    """Test class {i}."""
    
    def __init__(self):
        self.value = {i}
        self.data = []
    
    def process_data(self, items: List[str]) -> Dict[str, int]:
        """Process data items."""
        result = {{}}
        for item in items:
            result[item] = len(item) * {i}
        return result
    
    def calculate(self, x: int, y: int) -> int:
        """Calculate something."""
        return x * y + {i}

def main_function_{i}():
    """Main function for module {i}."""
    instance = TestClass{i}()
    data = ["test", "data", "items"]
    result = instance.process_data(data)
    print(f"Module {i} result: {{result}}")

if __name__ == "__main__":
    main_function_{i}()
'''
            (large_dir / f"module_{i}.py").write_text(file_content)
        
        # Test with larger codebase
        large_codebase = EnhancedCodebase(str(large_dir))
        
        start_time = time.time()
        errors = large_codebase.errors()
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"Large codebase ({20} files) analysis time: {execution_time:.3f} seconds")
        print(f"Found {len(errors)} errors in large codebase")
        
        # Should handle larger codebases efficiently
        assert execution_time < 60.0, f"Large codebase analysis took too long: {execution_time:.3f}s"
    
    @pytest.mark.parametrize("error_type", [
        "syntax_error.py",
        "import_error.py", 
        "type_error.py",
        "undefined_variable.py"
    ])
    def test_specific_error_types(self, codebase, error_type):
        """Test handling of specific error types."""
        errors = codebase.errors()
        
        # Find errors from the specific file
        file_errors = [e for e in errors if error_type in e.get('file_path', '')]
        
        print(f"Found {len(file_errors)} errors in {error_type}")
        
        if file_errors:
            error = file_errors[0]
            
            # Test context for this error type
            context = codebase.full_error_context(error['id'])
            
            # Should provide relevant suggestions based on error type
            suggestions = context['suggestions']
            assert len(suggestions) > 0, f"Should provide suggestions for {error_type}"
            
            # Test resolution attempt
            resolution = codebase.resolve_error(error['id'])
            assert 'error_id' in resolution, "Resolution should include error ID"


class TestErrorInterfaceEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_codebase(self):
        """Test error interface with empty codebase."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_codebase = EnhancedCodebase(temp_dir)
            
            errors = empty_codebase.errors()
            assert isinstance(errors, list), "Should return empty list for empty codebase"
            assert len(errors) == 0, "Empty codebase should have no errors"
            
            # Test other methods with empty codebase
            context = empty_codebase.full_error_context("nonexistent")
            assert context['error'] is None, "Should handle nonexistent errors gracefully"
            
            result = empty_codebase.resolve_errors()
            assert result['total_errors'] == 0, "Should report zero errors for empty codebase"
    
    def test_invalid_file_paths(self):
        """Test handling of invalid file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create codebase with invalid file reference
            invalid_file = Path(temp_dir) / "invalid.py"
            invalid_file.write_text("print('test')")
            
            codebase = EnhancedCodebase(temp_dir)
            
            # Remove file after codebase creation
            invalid_file.unlink()
            
            # Should handle missing files gracefully
            errors = codebase.errors()
            assert isinstance(errors, list), "Should handle missing files gracefully"
    
    def test_permission_errors(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file and remove read permissions
            restricted_file = Path(temp_dir) / "restricted.py"
            restricted_file.write_text("print('restricted')")
            
            try:
                restricted_file.chmod(0o000)  # Remove all permissions
                
                codebase = EnhancedCodebase(temp_dir)
                errors = codebase.errors()
                
                # Should handle permission errors gracefully
                assert isinstance(errors, list), "Should handle permission errors gracefully"
                
            finally:
                # Restore permissions for cleanup
                try:
                    restricted_file.chmod(0o644)
                except:
                    pass
    
    def test_malformed_python_files(self):
        """Test handling of severely malformed Python files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with various malformations
            malformed_files = {
                "binary_data.py": b'\x00\x01\x02\x03\x04\x05',  # Binary data
                "encoding_issue.py": "# -*- coding: utf-8 -*-\nprint('test with weird chars: \xff\xfe')",
                "extremely_long_line.py": f"# {'x' * 10000}\nprint('test')",  # Very long line
            }
            
            for filename, content in malformed_files.items():
                file_path = Path(temp_dir) / filename
                if isinstance(content, bytes):
                    file_path.write_bytes(content)
                else:
                    file_path.write_text(content, encoding='utf-8', errors='ignore')
            
            codebase = EnhancedCodebase(temp_dir)
            
            # Should handle malformed files without crashing
            try:
                errors = codebase.errors()
                assert isinstance(errors, list), "Should handle malformed files gracefully"
            except Exception as e:
                pytest.fail(f"Should not crash on malformed files: {e}")


class TestErrorInterfaceMocking:
    """Test error interface with mocked LSP responses."""
    
    @pytest.fixture
    def mock_lsp_errors(self):
        """Mock LSP error responses for testing."""
        return [
            {
                'file_path': 'test.py',
                'line': 10,
                'character': 5,
                'message': 'Undefined variable: test_var',
                'severity': 'error',
                'source': 'pylsp',
                'code': 'undefined-variable',
                'has_fix': True
            },
            {
                'file_path': 'test.py', 
                'line': 15,
                'character': 0,
                'message': 'Missing import: os',
                'severity': 'warning',
                'source': 'pylsp',
                'code': 'missing-import',
                'has_fix': True
            },
            {
                'file_path': 'another.py',
                'line': 5,
                'character': 10,
                'message': 'Line too long (85 > 79 characters)',
                'severity': 'info',
                'source': 'flake8',
                'code': 'E501',
                'has_fix': False
            }
        ]
    
    def test_mocked_errors_method(self, mock_lsp_errors):
        """Test errors() method with mocked LSP responses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            codebase = EnhancedCodebase(temp_dir)
            
            # Mock the _get_file_diagnostics_placeholder method
            with patch.object(codebase._get_error_interface(), '_get_file_diagnostics_placeholder') as mock_diag:
                mock_diag.return_value = mock_lsp_errors
                
                errors = codebase.errors()
                
                assert len(errors) >= len(mock_lsp_errors), "Should return mocked errors"
                
                # Verify error structure
                for error in errors:
                    assert 'id' in error, "Should have error ID"
                    assert 'severity' in error, "Should have severity"
                    assert error['severity'] in ['error', 'warning', 'info', 'hint']
    
    def test_mocked_error_resolution(self, mock_lsp_errors):
        """Test error resolution with mocked responses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            codebase = EnhancedCodebase(temp_dir)
            
            # Mock successful fix
            mock_fix_result = {
                'success': True,
                'message': 'Fixed undefined variable',
                'changes_made': ['Added variable definition'],
                'fix_description': 'Defined missing variable'
            }
            
            with patch.object(codebase._get_error_interface(), '_apply_error_fix') as mock_fix:
                mock_fix.return_value = mock_fix_result
                
                with patch.object(codebase._get_error_interface(), '_get_file_diagnostics_placeholder') as mock_diag:
                    mock_diag.return_value = mock_lsp_errors
                    
                    # Get errors and try to resolve one
                    errors = codebase.errors()
                    if errors:
                        result = codebase.resolve_error(errors[0]['id'])
                        
                        assert result['success'] is True, "Mocked fix should succeed"
                        assert len(result['changes_made']) > 0, "Should report changes made"


def test_error_interface_availability():
    """Test that error interface methods are available on Codebase class."""
    methods_to_check = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error']
    
    for method in methods_to_check:
        assert hasattr(EnhancedCodebase, method), f"Codebase should have {method} method"
        
        # Check method is callable
        method_obj = getattr(EnhancedCodebase, method)
        assert callable(method_obj), f"{method} should be callable"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])

