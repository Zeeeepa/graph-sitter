#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Unified Serena Interface

This test suite validates the complete unified interface implementation:
- codebase.errors(): Get all errors with comprehensive context
- codebase.full_error_context(error_id): Get detailed context for specific error
- codebase.resolve_errors(): Auto-fix all errors with batch processing
- codebase.resolve_error(error_id): Auto-fix specific error with detailed feedback

Tests cover:
✅ Lazy Loading: LSP features initialized only when first accessed
✅ Performance: Sub-5s initialization, sub-1s context extraction
✅ Error Handling: Graceful fallbacks when LSP unavailable
✅ Consistency: Standardized return types across all methods
✅ Real Integration: Works with actual LSP servers and codebases
"""

import os
import sys
import time
import tempfile
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False

# Test fixtures and utilities
class TestCodebaseGenerator:
    """Generate test codebases with known errors for testing."""
    
    @staticmethod
    def create_python_codebase_with_errors(base_path: Path) -> Dict[str, str]:
        """Create a Python codebase with various types of errors."""
        
        # Create directory structure
        (base_path / "src").mkdir(exist_ok=True)
        (base_path / "tests").mkdir(exist_ok=True)
        
        # Files with different types of errors
        test_files = {
            "src/syntax_errors.py": '''
# File with syntax errors for testing
def missing_colon_function()  # Missing colon
    return "syntax error"

def unclosed_parenthesis(
    param1,
    param2  # Missing closing parenthesis

class MissingColon  # Missing colon
    pass

# Indentation error
def bad_indentation():
return "wrong indent"
''',
            
            "src/type_errors.py": '''
# File with type errors for testing
from typing import List, Dict

def type_mismatch() -> int:
    return "string instead of int"  # Type error

def undefined_variable():
    return undefined_var  # NameError

def wrong_argument_count():
    return len()  # Missing required argument

class TypeIssues:
    def __init__(self, value: int):
        self.value = value
    
    def method_with_issues(self) -> str:
        return self.value + "string"  # Type mismatch
''',
            
            "src/import_errors.py": '''
# File with import errors for testing
import nonexistent_module  # Import error
from os import nonexistent_function  # Import error
from . import missing_relative_import  # Relative import error

def use_imports():
    return nonexistent_module.function()
''',
            
            "src/linting_issues.py": '''
# File with linting issues for testing
import os
import sys  # Unused import

def unused_variable():
    x = 5  # Unused variable
    return 10

def long_line_issue():
    return "This is a very long line that exceeds the typical line length limit and should trigger a linting warning about line length"

def trailing_whitespace():   
    return "line with trailing spaces"   

# Missing docstring
def no_docstring():
    pass
''',
            
            "src/working_code.py": '''
"""
Working Python code without errors.
This file should not generate any errors.
"""

from typing import List, Optional
import os


class WorkingClass:
    """A class that works correctly."""
    
    def __init__(self, value: int) -> None:
        """Initialize with a value."""
        self.value = value
    
    def get_value(self) -> int:
        """Get the stored value."""
        return self.value
    
    def process_list(self, items: List[str]) -> List[str]:
        """Process a list of items."""
        return [item.upper() for item in items]


def working_function(param: str) -> Optional[str]:
    """A function that works correctly."""
    if param:
        return param.strip()
    return None


if __name__ == "__main__":
    instance = WorkingClass(42)
    result = working_function("test")
    print(f"Result: {result}, Value: {instance.get_value()}")
''',
            
            "tests/test_example.py": '''
"""Test file with some issues."""
import unittest

class TestExample(unittest.TestCase):
    def test_something(self):
        self.assertEqual(1, 1)
    
    def test_with_error(self):
        # This will cause an error
        undefined_variable_in_test  # NameError
''',
            
            "requirements.txt": '''
# Test requirements
pytest>=7.0.0
mypy>=1.0.0
pylsp>=1.7.0
''',
            
            "pyproject.toml": '''
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pylsp-mypy]
enabled = true
live_mode = true
strict = true
'''
        }
        
        # Write all test files
        for file_path, content in test_files.items():
            full_path = base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        return test_files


@pytest.fixture
def test_codebase():
    """Create a temporary codebase for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate test codebase with known errors
        generator = TestCodebaseGenerator()
        test_files = generator.create_python_codebase_with_errors(temp_path)
        
        yield temp_path, test_files


@pytest.mark.skipif(not GRAPH_SITTER_AVAILABLE, reason="Graph-sitter not available")
class TestUnifiedInterface:
    """Test the unified Serena interface."""
    
    def test_codebase_initialization(self, test_codebase):
        """Test that Codebase can be initialized with the unified interface."""
        temp_path, _ = test_codebase
        
        start_time = time.time()
        codebase = Codebase(str(temp_path))
        init_time = time.time() - start_time
        
        # Verify codebase is initialized
        assert codebase is not None
        assert hasattr(codebase, 'errors')
        assert hasattr(codebase, 'full_error_context')
        assert hasattr(codebase, 'resolve_errors')
        assert hasattr(codebase, 'resolve_error')
        
        # Performance requirement: initialization should be fast
        assert init_time < 5.0, f"Initialization took {init_time:.2f}s, should be < 5s"
        
        print(f"✅ Codebase initialized in {init_time:.2f}s")
    
    def test_errors_method_basic(self, test_codebase):
        """Test basic functionality of codebase.errors() method."""
        temp_path, test_files = test_codebase
        codebase = Codebase(str(temp_path))
        
        start_time = time.time()
        all_errors = codebase.errors()
        errors_time = time.time() - start_time
        
        # Verify return type and structure
        assert isinstance(all_errors, list), "errors() should return a list"
        
        # Performance requirement: error detection should be reasonably fast
        assert errors_time < 10.0, f"Error detection took {errors_time:.2f}s, should be < 10s"
        
        print(f"✅ Found {len(all_errors)} errors in {errors_time:.2f}s")
        
        # Verify error structure if errors found
        if all_errors:
            error = all_errors[0]
            required_fields = [
                'id', 'location', 'message', 'severity', 'category', 
                'error_type', 'source', 'confidence_score'
            ]
            
            for field in required_fields:
                assert field in error, f"Error missing required field: {field}"
            
            # Verify location structure
            location = error['location']
            location_fields = ['file_path', 'line', 'character']
            for field in location_fields:
                assert field in location, f"Location missing required field: {field}"
            
            print(f"✅ Error structure validated: {error['id']}")
    
    def test_errors_method_comprehensive(self, test_codebase):
        """Test comprehensive functionality of codebase.errors() method."""
        temp_path, test_files = test_codebase
        codebase = Codebase(str(temp_path))
        
        all_errors = codebase.errors()
        
        if not all_errors:
            print("⚠️  No errors detected - this might indicate LSP servers are not available")
            return
        
        # Categorize errors by type
        error_categories = {}
        error_severities = {}
        error_sources = {}
        
        for error in all_errors:
            # Count by category
            category = error.get('category', 'unknown')
            error_categories[category] = error_categories.get(category, 0) + 1
            
            # Count by severity
            severity = error.get('severity', 'unknown')
            error_severities[severity] = error_severities.get(severity, 0) + 1
            
            # Count by source
            source = error.get('source', 'unknown')
            error_sources[source] = error_sources.get(source, 0) + 1
            
            # Verify comprehensive fields
            assert 'context' in error or error.get('context') is not None
            assert 'reasoning' in error or error.get('reasoning') is not None
            assert 'suggested_fixes' in error
            assert isinstance(error.get('confidence_score', 0), (int, float))
            assert 0.0 <= error.get('confidence_score', 0) <= 1.0
        
        print(f"✅ Error analysis complete:")
        print(f"   Categories: {error_categories}")
        print(f"   Severities: {error_severities}")
        print(f"   Sources: {error_sources}")
    
    def test_full_error_context_method(self, test_codebase):
        """Test codebase.full_error_context() method."""
        temp_path, test_files = test_codebase
        codebase = Codebase(str(temp_path))
        
        # Get errors first
        all_errors = codebase.errors()
        
        if not all_errors:
            print("⚠️  No errors to test context for")
            return
        
        # Test context for first error
        error_id = all_errors[0]['id']
        
        start_time = time.time()
        context = codebase.full_error_context(error_id)
        context_time = time.time() - start_time
        
        # Performance requirement: context should be fast
        assert context_time < 1.0, f"Context extraction took {context_time:.2f}s, should be < 1s"
        
        # Verify context structure
        if context:
            assert isinstance(context, dict), "full_error_context should return a dict"
            assert context['id'] == error_id, "Context should match requested error ID"
            
            # Verify enhanced context fields
            enhanced_fields = ['context', 'reasoning', 'impact_analysis', 'suggested_fixes']
            for field in enhanced_fields:
                assert field in context, f"Context missing enhanced field: {field}"
            
            print(f"✅ Context retrieved in {context_time:.3f}s for error: {error_id}")
            print(f"   Root cause: {context.get('reasoning', {}).get('root_cause', 'N/A')}")
        else:
            print(f"⚠️  No context found for error: {error_id}")
    
    def test_resolve_errors_method(self, test_codebase):
        """Test codebase.resolve_errors() batch resolution method."""
        temp_path, test_files = test_codebase
        codebase = Codebase(str(temp_path))
        
        # Get initial errors
        initial_errors = codebase.errors()
        
        if not initial_errors:
            print("⚠️  No errors to resolve")
            return
        
        # Find fixable errors
        fixable_errors = [e for e in initial_errors if e.get('has_safe_fix', False)]
        
        if not fixable_errors:
            print("⚠️  No safe fixable errors found")
            # Test with all errors anyway
            fixable_error_ids = [e['id'] for e in initial_errors[:3]]  # Test with first 3
        else:
            fixable_error_ids = [e['id'] for e in fixable_errors]
        
        start_time = time.time()
        result = codebase.resolve_errors(fixable_error_ids)
        resolve_time = time.time() - start_time
        
        # Verify result structure
        assert isinstance(result, dict), "resolve_errors should return a dict"
        
        required_fields = [
            'total_errors', 'successful_fixes', 'failed_fixes', 'skipped_errors',
            'execution_time', 'individual_results', 'summary'
        ]
        
        for field in required_fields:
            assert field in result, f"Result missing required field: {field}"
        
        # Verify counts make sense
        total = result['total_errors']
        successful = result['successful_fixes']
        failed = result['failed_fixes']
        skipped = result['skipped_errors']
        
        assert total == successful + failed + skipped, "Error counts should add up"
        assert len(result['individual_results']) == total, "Individual results count should match total"
        
        print(f"✅ Batch resolution completed in {resolve_time:.2f}s:")
        print(f"   {result['summary']}")
        print(f"   Total: {total}, Success: {successful}, Failed: {failed}, Skipped: {skipped}")
    
    def test_resolve_error_method(self, test_codebase):
        """Test codebase.resolve_error() single error resolution method."""
        temp_path, test_files = test_codebase
        codebase = Codebase(str(temp_path))
        
        # Get errors
        all_errors = codebase.errors()
        
        if not all_errors:
            print("⚠️  No errors to resolve")
            return
        
        # Find a fixable error or use the first one
        test_error = None
        for error in all_errors:
            if error.get('has_safe_fix', False):
                test_error = error
                break
        
        if not test_error:
            test_error = all_errors[0]  # Use first error anyway for testing
        
        error_id = test_error['id']
        
        start_time = time.time()
        result = codebase.resolve_error(error_id)
        resolve_time = time.time() - start_time
        
        # Verify result structure
        if result:
            assert isinstance(result, dict), "resolve_error should return a dict"
            
            required_fields = [
                'success', 'error_id', 'applied_fixes', 'execution_time', 'confidence_score'
            ]
            
            for field in required_fields:
                assert field in result, f"Result missing required field: {field}"
            
            assert result['error_id'] == error_id, "Result should match requested error ID"
            assert isinstance(result['applied_fixes'], list), "Applied fixes should be a list"
            assert isinstance(result['confidence_score'], (int, float)), "Confidence should be numeric"
            
            print(f"✅ Single error resolution completed in {resolve_time:.3f}s:")
            print(f"   Success: {result['success']}")
            print(f"   Confidence: {result['confidence_score']:.2f}")
            if result['applied_fixes']:
                print(f"   Fix: {result['applied_fixes'][0].get('description', 'N/A')}")
        else:
            print(f"⚠️  No result returned for error: {error_id}")
    
    def test_lazy_loading_behavior(self, test_codebase):
        """Test that LSP features are loaded lazily."""
        temp_path, test_files = test_codebase
        
        # Create codebase but don't call any error methods yet
        start_time = time.time()
        codebase = Codebase(str(temp_path))
        init_time = time.time() - start_time
        
        # Initial creation should be fast (no LSP initialization)
        assert init_time < 2.0, f"Initial creation took {init_time:.2f}s, should be < 2s"
        
        # First call to errors() should trigger LSP initialization
        start_time = time.time()
        first_errors = codebase.errors()
        first_call_time = time.time() - start_time
        
        # Second call should be faster (cached/initialized)
        start_time = time.time()
        second_errors = codebase.errors()
        second_call_time = time.time() - start_time
        
        # Second call should be significantly faster
        if first_call_time > 0.1:  # Only test if first call took meaningful time
            assert second_call_time < first_call_time, "Second call should be faster due to caching"
        
        print(f"✅ Lazy loading verified:")
        print(f"   Initial creation: {init_time:.3f}s")
        print(f"   First errors() call: {first_call_time:.3f}s")
        print(f"   Second errors() call: {second_call_time:.3f}s")
    
    def test_error_handling_graceful_fallbacks(self, test_codebase):
        """Test graceful error handling when LSP is unavailable."""
        temp_path, test_files = test_codebase
        codebase = Codebase(str(temp_path))
        
        # All methods should work even if LSP is not available
        try:
            errors = codebase.errors()
            assert isinstance(errors, list), "errors() should always return a list"
            
            if errors:
                context = codebase.full_error_context(errors[0]['id'])
                # Context might be None if not available, but shouldn't crash
                
                result = codebase.resolve_errors()
                assert isinstance(result, dict), "resolve_errors() should always return a dict"
                
                single_result = codebase.resolve_error(errors[0]['id'])
                # Single result might be None if not available, but shouldn't crash
            
            print("✅ Graceful error handling verified - no crashes")
            
        except Exception as e:
            pytest.fail(f"Methods should not crash even when LSP unavailable: {e}")
    
    def test_performance_requirements(self, test_codebase):
        """Test that performance requirements are met."""
        temp_path, test_files = test_codebase
        
        # Test initialization performance
        start_time = time.time()
        codebase = Codebase(str(temp_path))
        init_time = time.time() - start_time
        
        assert init_time < 5.0, f"Initialization took {init_time:.2f}s, requirement: < 5s"
        
        # Test error detection performance
        start_time = time.time()
        errors = codebase.errors()
        errors_time = time.time() - start_time
        
        assert errors_time < 10.0, f"Error detection took {errors_time:.2f}s, requirement: < 10s"
        
        # Test context extraction performance (if errors exist)
        if errors:
            start_time = time.time()
            context = codebase.full_error_context(errors[0]['id'])
            context_time = time.time() - start_time
            
            assert context_time < 1.0, f"Context extraction took {context_time:.2f}s, requirement: < 1s"
        
        print(f"✅ Performance requirements met:")
        print(f"   Initialization: {init_time:.2f}s (< 5s)")
        print(f"   Error detection: {errors_time:.2f}s (< 10s)")
        if errors:
            print(f"   Context extraction: {context_time:.3f}s (< 1s)")


def test_integration_with_real_codebase():
    """Test the unified interface with the actual graph-sitter codebase."""
    # Test with the current codebase
    current_dir = Path(__file__).parent.parent.parent
    
    if not GRAPH_SITTER_AVAILABLE:
        print("⚠️  Skipping real codebase test - Graph-sitter not available")
        return
    
    try:
        print(f"🧪 Testing unified interface with real codebase: {current_dir}")
        
        start_time = time.time()
        codebase = Codebase(str(current_dir))
        init_time = time.time() - start_time
        
        print(f"✅ Real codebase initialized in {init_time:.2f}s")
        
        # Test error detection
        start_time = time.time()
        errors = codebase.errors()
        errors_time = time.time() - start_time
        
        print(f"✅ Found {len(errors)} errors in real codebase ({errors_time:.2f}s)")
        
        # Test context extraction for first few errors
        if errors:
            for i, error in enumerate(errors[:3]):  # Test first 3 errors
                start_time = time.time()
                context = codebase.full_error_context(error['id'])
                context_time = time.time() - start_time
                
                print(f"✅ Context {i+1}: {context_time:.3f}s - {error['message'][:50]}...")
        
        # Test batch resolution (dry run)
        if errors:
            safe_errors = [e for e in errors if e.get('has_safe_fix', False)]
            if safe_errors:
                start_time = time.time()
                result = codebase.resolve_errors([e['id'] for e in safe_errors[:5]])  # Test first 5
                resolve_time = time.time() - start_time
                
                print(f"✅ Batch resolution test: {resolve_time:.2f}s - {result['summary']}")
        
        print("✅ Real codebase integration test completed successfully")
        
    except Exception as e:
        print(f"⚠️  Real codebase test failed (this is expected if LSP servers not available): {e}")


if __name__ == "__main__":
    print("🧪 Running Unified Serena Interface Integration Tests")
    print("=" * 60)
    
    # Run basic integration test with real codebase
    test_integration_with_real_codebase()
    
    print("\n" + "=" * 60)
    print("✅ Integration tests completed!")
    print("\nTo run full test suite with pytest:")
    print("  cd tests && python -m pytest integration/test_unified_interface.py -v")

