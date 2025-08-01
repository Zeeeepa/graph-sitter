"""
Integration Tests for Unified Serena Error Interface

This test suite validates the complete integration of the unified error interface
with the Codebase class and ensures all components work together correctly.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False


@pytest.fixture
def temp_project():
    """Create a temporary project for testing."""
    temp_dir = tempfile.mkdtemp(prefix="serena_integration_test_")
    project_path = Path(temp_dir)
    
    # Create project structure
    (project_path / "src").mkdir(parents=True, exist_ok=True)
    
    # Create test files with various error types
    
    # File with unused imports
    unused_imports_code = '''import os
import sys
import json  # Unused import
from typing import List, Dict  # Mixed usage

def process_files(files: List[str]) -> None:
    """Process a list of files."""
    for file in files:
        print(f"Processing: {file}")
    
    sys.exit(0)  # Uses sys
'''
    
    with open(project_path / "src" / "unused_imports.py", "w") as f:
        f.write(unused_imports_code)
    
    # File with missing imports
    missing_imports_code = '''def get_current_dir():
    """Get current directory."""
    return os.getcwd()  # Missing import

def parse_json(data):
    """Parse JSON data."""
    return json.loads(data)  # Missing import

def create_path(filename):
    """Create a Path object."""
    return Path(filename)  # Missing import
'''
    
    with open(project_path / "src" / "missing_imports.py", "w") as f:
        f.write(missing_imports_code)
    
    # File with style issues
    style_issues_code = '''def bad_function(x,y,z):
    result=x+y+z
    return result

class BadClass:
    def method1(self):pass
    def method2(self):pass
'''
    
    with open(project_path / "src" / "style_issues.py", "w") as f:
        f.write(style_issues_code)
    
    # File with correct code
    correct_code = '''from typing import List, Optional

def well_written_function(numbers: List[int]) -> Optional[int]:
    """Calculate sum of positive numbers."""
    positive = [n for n in numbers if n > 0]
    return sum(positive) if positive else None

class WellWrittenClass:
    """A well-written class."""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    def greet(self) -> str:
        """Return greeting."""
        return f"Hello, {self.name}!"
'''
    
    with open(project_path / "src" / "correct_code.py", "w") as f:
        f.write(correct_code)
    
    yield project_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.skipif(not GRAPH_SITTER_AVAILABLE, reason="Graph-sitter not available")
class TestUnifiedSerenaIntegration:
    """Test the complete unified Serena integration."""
    
    def test_codebase_has_unified_methods(self, temp_project):
        """Test that Codebase class has the unified error methods."""
        codebase = Codebase(str(temp_project))
        
        # Check that all unified error methods are available
        required_methods = [
            'errors',
            'full_error_context',
            'resolve_errors',
            'resolve_error',
            'error_summary',
            'refresh_errors',
            'get_fixable_errors',
            'preview_fix'
        ]
        
        for method_name in required_methods:
            assert hasattr(codebase, method_name), f"Method {method_name} not found on Codebase"
            assert callable(getattr(codebase, method_name)), f"Method {method_name} is not callable"
    
    def test_errors_method_basic_functionality(self, temp_project):
        """Test basic functionality of the errors() method."""
        codebase = Codebase(str(temp_project))
        
        # Get all errors
        all_errors = codebase.errors()
        
        # Should return a list
        assert isinstance(all_errors, list)
        
        # Test filtering parameters
        errors_no_warnings = codebase.errors(include_warnings=False)
        assert isinstance(errors_no_warnings, list)
        
        errors_with_hints = codebase.errors(include_hints=True)
        assert isinstance(errors_with_hints, list)
        
        # Test file filtering
        file_errors = codebase.errors(file_path="src/unused_imports.py")
        assert isinstance(file_errors, list)
        
        # Test category filtering
        unused_errors = codebase.errors(category="unused")
        assert isinstance(unused_errors, list)
    
    def test_error_summary_functionality(self, temp_project):
        """Test the error_summary() method."""
        codebase = Codebase(str(temp_project))
        
        summary = codebase.error_summary()
        
        # Should have summary object with expected attributes
        assert hasattr(summary, 'total_errors')
        assert hasattr(summary, 'total_warnings')
        assert hasattr(summary, 'total_issues')
        assert hasattr(summary, 'auto_fixable')
        
        # Values should be non-negative integers
        assert summary.total_errors >= 0
        assert summary.total_warnings >= 0
        assert summary.total_issues >= 0
        assert summary.auto_fixable >= 0
        
        # Total issues should be sum of individual counts
        expected_total = summary.total_errors + summary.total_warnings + summary.total_info + summary.total_hints
        assert summary.total_issues == expected_total
    
    def test_get_fixable_errors_functionality(self, temp_project):
        """Test the get_fixable_errors() method."""
        codebase = Codebase(str(temp_project))
        
        # Get auto-fixable errors only
        auto_fixable = codebase.get_fixable_errors(auto_fixable_only=True)
        assert isinstance(auto_fixable, list)
        
        # Get all fixable errors
        all_fixable = codebase.get_fixable_errors(auto_fixable_only=False)
        assert isinstance(all_fixable, list)
        
        # Auto-fixable should be subset of all fixable
        auto_fixable_ids = {e.id for e in auto_fixable}
        all_fixable_ids = {e.id for e in all_fixable}
        assert auto_fixable_ids.issubset(all_fixable_ids)
        
        # All returned errors should be fixable
        for error in all_fixable:
            assert hasattr(error, 'is_fixable')
            assert error.is_fixable or error.auto_fixable
    
    def test_full_error_context_functionality(self, temp_project):
        """Test the full_error_context() method."""
        codebase = Codebase(str(temp_project))
        
        # Get some errors first
        errors = codebase.errors()
        
        if errors:
            # Get context for the first error
            context = codebase.full_error_context(errors[0].id)
            
            # Context might be None if LSP is not available, which is okay
            if context:
                assert hasattr(context, 'error')
                assert context.error.id == errors[0].id
                assert hasattr(context, 'surrounding_code')
                assert hasattr(context, 'recommended_fixes')
        
        # Test with invalid error ID
        invalid_context = codebase.full_error_context("invalid_error_id")
        assert invalid_context is None
    
    def test_preview_fix_functionality(self, temp_project):
        """Test the preview_fix() method."""
        codebase = Codebase(str(temp_project))
        
        # Get fixable errors
        fixable_errors = codebase.get_fixable_errors()
        
        if fixable_errors:
            # Preview fix for the first fixable error
            preview = codebase.preview_fix(fixable_errors[0].id)
            
            assert isinstance(preview, dict)
            assert 'can_resolve' in preview
            
            if preview['can_resolve']:
                assert 'fix_title' in preview
                assert 'confidence' in preview
                assert 'requires_user_input' in preview
        
        # Test with invalid error ID
        invalid_preview = codebase.preview_fix("invalid_error_id")
        assert isinstance(invalid_preview, dict)
        assert 'error' in invalid_preview or 'can_resolve' in invalid_preview
    
    def test_resolve_error_functionality(self, temp_project):
        """Test the resolve_error() method."""
        codebase = Codebase(str(temp_project))
        
        # Get auto-fixable errors
        auto_fixable = codebase.get_fixable_errors(auto_fixable_only=True)
        
        if auto_fixable:
            # Try to resolve the first auto-fixable error
            result = codebase.resolve_error(auto_fixable[0].id)
            
            # Should return a result object
            assert hasattr(result, 'success')
            assert hasattr(result, 'error_id')
            assert hasattr(result, 'message')
            assert result.error_id == auto_fixable[0].id
            
            # Result should be boolean
            assert isinstance(result.success, bool)
        
        # Test with invalid error ID
        invalid_result = codebase.resolve_error("invalid_error_id")
        assert hasattr(invalid_result, 'success')
        assert invalid_result.success is False
    
    def test_resolve_errors_functionality(self, temp_project):
        """Test the resolve_errors() method."""
        codebase = Codebase(str(temp_project))
        
        # Test resolving all auto-fixable errors
        results = codebase.resolve_errors(auto_fixable_only=True, max_fixes=5)
        
        assert isinstance(results, list)
        
        # Each result should have expected attributes
        for result in results:
            assert hasattr(result, 'success')
            assert hasattr(result, 'error_id')
            assert hasattr(result, 'message')
            assert isinstance(result.success, bool)
        
        # Test with specific error IDs
        auto_fixable = codebase.get_fixable_errors(auto_fixable_only=True)
        if auto_fixable:
            specific_results = codebase.resolve_errors(
                error_ids=[auto_fixable[0].id],
                max_fixes=1
            )
            
            assert isinstance(specific_results, list)
            assert len(specific_results) <= 1
    
    def test_refresh_errors_functionality(self, temp_project):
        """Test the refresh_errors() method."""
        codebase = Codebase(str(temp_project))
        
        # Should not raise an exception
        codebase.refresh_errors()
        
        # Should be able to refresh specific file
        codebase.refresh_errors("src/unused_imports.py")
        
        # Should still be able to get errors after refresh
        errors_after_refresh = codebase.errors()
        assert isinstance(errors_after_refresh, list)
    
    def test_error_object_properties(self, temp_project):
        """Test that error objects have expected properties."""
        codebase = Codebase(str(temp_project))
        
        errors = codebase.errors()
        
        for error in errors:
            # Check required attributes
            assert hasattr(error, 'id')
            assert hasattr(error, 'message')
            assert hasattr(error, 'severity')
            assert hasattr(error, 'location')
            assert hasattr(error, 'source')
            
            # Check computed properties
            assert hasattr(error, 'is_error')
            assert hasattr(error, 'is_warning')
            assert hasattr(error, 'is_fixable')
            assert hasattr(error, 'auto_fixable')
            
            # Check that properties return expected types
            assert isinstance(error.id, str)
            assert isinstance(error.message, str)
            assert isinstance(error.source, str)
            assert isinstance(error.is_error, bool)
            assert isinstance(error.is_warning, bool)
            assert isinstance(error.is_fixable, bool)
            assert isinstance(error.auto_fixable, bool)
            
            # Check location object
            assert hasattr(error.location, 'file_path')
            assert hasattr(error.location, 'line')
            assert hasattr(error.location, 'character')
            assert isinstance(error.location.file_path, str)
            assert isinstance(error.location.line, int)
            assert isinstance(error.location.character, int)
    
    def test_error_filtering_consistency(self, temp_project):
        """Test that error filtering works consistently."""
        codebase = Codebase(str(temp_project))
        
        # Get all errors
        all_errors = codebase.errors(include_warnings=True, include_hints=True)
        
        # Filter by severity
        only_errors = codebase.errors(include_warnings=False, include_hints=False)
        only_warnings = [e for e in all_errors if e.is_warning]
        
        # Check consistency
        error_count = len([e for e in all_errors if e.is_error])
        assert len(only_errors) == error_count
        
        # Filter by file
        files_with_errors = set(e.location.file_path for e in all_errors)
        
        for file_path in files_with_errors:
            file_errors = codebase.errors(file_path=file_path)
            
            # All returned errors should be from the specified file
            for error in file_errors:
                assert error.location.file_path == file_path
            
            # Should match manual filtering
            manual_filter = [e for e in all_errors if e.location.file_path == file_path]
            assert len(file_errors) == len(manual_filter)
    
    def test_lazy_initialization(self, temp_project):
        """Test that the unified interface uses lazy initialization."""
        codebase = Codebase(str(temp_project))
        
        # Initially, the error interface should not be initialized
        assert not hasattr(codebase, '_unified_error_interface') or \
               not codebase._unified_error_interface._initialized
        
        # Calling an error method should trigger initialization
        errors = codebase.errors()
        
        # Now the interface should be initialized (if LSP is available)
        if hasattr(codebase, '_unified_error_interface'):
            # The interface should have attempted initialization
            assert codebase._unified_error_interface._initialization_attempted
    
    def test_error_interface_graceful_degradation(self, temp_project):
        """Test that the interface degrades gracefully when LSP is not available."""
        codebase = Codebase(str(temp_project))
        
        # All methods should return appropriate empty/default values
        # rather than raising exceptions
        
        errors = codebase.errors()
        assert isinstance(errors, list)  # Should be empty list if no LSP
        
        summary = codebase.error_summary()
        assert hasattr(summary, 'total_errors')  # Should be default summary
        
        fixable = codebase.get_fixable_errors()
        assert isinstance(fixable, list)  # Should be empty list if no LSP
        
        # Methods with error IDs should handle gracefully
        context = codebase.full_error_context("nonexistent")
        assert context is None  # Should return None for invalid ID
        
        preview = codebase.preview_fix("nonexistent")
        assert isinstance(preview, dict)  # Should return error dict
        
        result = codebase.resolve_error("nonexistent")
        assert hasattr(result, 'success')  # Should return failure result
        assert result.success is False


@pytest.mark.skipif(not GRAPH_SITTER_AVAILABLE, reason="Graph-sitter not available")
class TestUnifiedSerenaPerformance:
    """Test performance characteristics of the unified interface."""
    
    def test_multiple_calls_performance(self, temp_project):
        """Test that multiple calls don't cause performance issues."""
        codebase = Codebase(str(temp_project))
        
        # Multiple calls to errors() should be reasonably fast
        # (caching should help)
        import time
        
        start_time = time.time()
        for _ in range(5):
            errors = codebase.errors()
        end_time = time.time()
        
        # Should complete within reasonable time (10 seconds is very generous)
        assert end_time - start_time < 10.0
        
        # Multiple calls to summary should also be fast
        start_time = time.time()
        for _ in range(5):
            summary = codebase.error_summary()
        end_time = time.time()
        
        assert end_time - start_time < 10.0
    
    def test_large_error_list_handling(self, temp_project):
        """Test handling of potentially large error lists."""
        codebase = Codebase(str(temp_project))
        
        # Get all errors including hints and info
        all_errors = codebase.errors(include_warnings=True, include_hints=True)
        
        # Should handle the list efficiently
        assert isinstance(all_errors, list)
        
        # Should be able to iterate through all errors
        count = 0
        for error in all_errors:
            count += 1
            if count > 1000:  # Safety limit for test
                break
        
        # Should be able to filter large lists
        if all_errors:
            filtered = [e for e in all_errors if e.is_error]
            assert isinstance(filtered, list)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

