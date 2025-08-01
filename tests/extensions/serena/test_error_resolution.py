"""
Tests for Error Resolution System

This test suite validates the error resolution capabilities,
including fix application, safety checks, and rollback functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import os

from graph_sitter.extensions.serena.unified_error_models import (
    UnifiedError, ErrorSeverity, ErrorCategory, ErrorLocation, 
    ErrorFix, FixConfidence, ErrorResolutionResult
)
from graph_sitter.extensions.serena.error_resolver import ErrorResolver, FixApplicator


class MockCodebase:
    """Mock codebase for testing error resolution."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.files = []
    
    def add_file(self, file_path: str, content: str):
        """Add a file to the mock codebase."""
        full_path = self.repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.files.append({'file_path': file_path})
    
    def get_file_content(self, file_path: str) -> str:
        """Get content of a file."""
        full_path = self.repo_path / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""


class MockErrorManager:
    """Mock error manager for testing."""
    
    def __init__(self):
        self.errors = {}
    
    def add_error(self, error: UnifiedError):
        """Add an error to the manager."""
        self.errors[error.id] = error
    
    def get_error_by_id(self, error_id: str) -> UnifiedError:
        """Get error by ID."""
        return self.errors.get(error_id)
    
    def get_all_errors(self) -> List[UnifiedError]:
        """Get all errors."""
        return list(self.errors.values())


class MockContextEngine:
    """Mock context engine for testing."""
    
    def __init__(self, codebase):
        self.codebase = codebase
    
    def get_full_error_context(self, error: UnifiedError):
        """Get mock context for an error."""
        from graph_sitter.extensions.serena.unified_error_models import ErrorContext
        
        context = ErrorContext(error=error)
        context.surrounding_code = "Mock surrounding code"
        context.recommended_fixes = error.fixes
        return context


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_codebase_with_files(temp_repo):
    """Create a mock codebase with test files for resolution."""
    codebase = MockCodebase(temp_repo)
    
    # File with unused import (easy to fix)
    codebase.add_file("unused_import.py", """import os
import sys
import json  # This will be unused

def main():
    print("Hello, world!")
    sys.exit(0)
""")
    
    # File with whitespace issues (easy to fix)
    codebase.add_file("whitespace_issues.py", """def bad_function(x,y):
    result=x+y
    return result

class BadClass:
    def method(self):pass
""")
    
    # File with missing imports (medium difficulty)
    codebase.add_file("missing_imports.py", """def use_os_functions():
    # Missing import for os
    return os.getcwd()

def use_json():
    # Missing import for json
    data = {"key": "value"}
    return json.dumps(data)
""")
    
    # File with complex issues (hard to fix automatically)
    codebase.add_file("complex_issues.py", """def complex_function(data):
    # This has multiple issues that are hard to fix automatically
    if data is None:
        return None
    
    # Logic error - should handle empty data
    result = data[0]  # Could raise IndexError
    
    # Type inconsistency
    if isinstance(result, str):
        return int(result)  # Could raise ValueError
    else:
        return str(result)
""")
    
    return codebase


class TestFixApplicator:
    """Test the fix applicator functionality."""
    
    def test_delete_line_fix(self, mock_codebase_with_files):
        """Test deleting a line (e.g., unused import)."""
        applicator = FixApplicator(mock_codebase_with_files)
        
        # Create error for unused import
        location = ErrorLocation("unused_import.py", 3, 0)  # json import line
        error = UnifiedError(
            id="unused_json_import",
            message="unused import 'json'",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.UNUSED,
            location=location,
            source="ruff"
        )
        
        # Create fix to delete the line
        fix = ErrorFix(
            id="remove_unused_json",
            title="Remove unused import",
            description="Remove the unused json import",
            confidence=FixConfidence.HIGH,
            changes=[{
                "type": "delete_line",
                "file": "unused_import.py",
                "line": 3
            }]
        )
        
        # Get original content
        original_content = mock_codebase_with_files.get_file_content("unused_import.py")
        assert "import json" in original_content
        
        # Apply the fix
        result = applicator.apply_fix(fix, error)
        
        # Check result
        assert result.success
        assert result.error_id == error.id
        assert "unused_import.py" in result.files_modified
        
        # Check that the line was removed
        new_content = mock_codebase_with_files.get_file_content("unused_import.py")
        assert "import json" not in new_content
        assert "import os" in new_content  # Other imports should remain
        assert "import sys" in new_content
    
    def test_fix_whitespace(self, mock_codebase_with_files):
        """Test fixing whitespace issues."""
        applicator = FixApplicator(mock_codebase_with_files)
        
        # Create error for missing whitespace
        location = ErrorLocation("whitespace_issues.py", 1, 20)
        error = UnifiedError(
            id="missing_whitespace",
            message="missing whitespace around operator",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STYLE,
            location=location,
            source="flake8"
        )
        
        # Create fix for whitespace
        fix = ErrorFix(
            id="fix_whitespace",
            title="Fix whitespace",
            description="Add missing whitespace around operators",
            confidence=FixConfidence.HIGH,
            changes=[{
                "type": "fix_whitespace",
                "file": "whitespace_issues.py",
                "line": 1
            }]
        )
        
        # Apply the fix
        result = applicator.apply_fix(fix, error)
        
        # Check result
        assert result.success
        assert result.error_id == error.id
    
    def test_add_import_fix(self, mock_codebase_with_files):
        """Test adding missing imports."""
        applicator = FixApplicator(mock_codebase_with_files)
        
        # Create error for missing import
        location = ErrorLocation("missing_imports.py", 3, 11)
        error = UnifiedError(
            id="missing_os_import",
            message="undefined name 'os'",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.UNDEFINED,
            location=location,
            source="pylsp"
        )
        
        # Create fix to add import
        fix = ErrorFix(
            id="add_os_import",
            title="Add import for 'os'",
            description="Add missing import statement for os module",
            confidence=FixConfidence.MEDIUM,
            changes=[{
                "type": "add_import",
                "file": "missing_imports.py",
                "symbol": "os"
            }]
        )
        
        # Apply the fix
        result = applicator.apply_fix(fix, error)
        
        # Check result
        assert result.success
        assert result.error_id == error.id
        
        # Check that import was added
        new_content = mock_codebase_with_files.get_file_content("missing_imports.py")
        assert "import os" in new_content or "from os import" in new_content
    
    def test_replace_text_fix(self, mock_codebase_with_files):
        """Test replacing text in a file."""
        applicator = FixApplicator(mock_codebase_with_files)
        
        # Create error for text that needs replacement
        location = ErrorLocation("whitespace_issues.py", 2, 10)
        error = UnifiedError(
            id="bad_assignment",
            message="missing spaces around assignment",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STYLE,
            location=location,
            source="flake8"
        )
        
        # Create fix to replace text
        fix = ErrorFix(
            id="fix_assignment",
            title="Fix assignment spacing",
            description="Add spaces around assignment operator",
            confidence=FixConfidence.HIGH,
            changes=[{
                "type": "replace_text",
                "file": "whitespace_issues.py",
                "line": 2,
                "old_text": "result=x+y",
                "new_text": "result = x + y"
            }]
        )
        
        # Apply the fix
        result = applicator.apply_fix(fix, error)
        
        # Check result
        assert result.success
        assert result.error_id == error.id
        
        # Check that text was replaced
        new_content = mock_codebase_with_files.get_file_content("whitespace_issues.py")
        assert "result = x + y" in new_content
        assert "result=x+y" not in new_content
    
    def test_backup_and_restore(self, mock_codebase_with_files):
        """Test backup and restore functionality on fix failure."""
        applicator = FixApplicator(mock_codebase_with_files)
        
        # Create an error
        location = ErrorLocation("unused_import.py", 1, 0)
        error = UnifiedError(
            id="test_error",
            message="test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=location,
            source="test"
        )
        
        # Create a fix that will fail (invalid change type)
        fix = ErrorFix(
            id="bad_fix",
            title="Bad fix",
            description="This fix will fail",
            confidence=FixConfidence.HIGH,
            changes=[{
                "type": "invalid_change_type",
                "file": "unused_import.py"
            }]
        )
        
        # Get original content
        original_content = mock_codebase_with_files.get_file_content("unused_import.py")
        
        # Apply the fix (should fail)
        result = applicator.apply_fix(fix, error)
        
        # Check that fix failed
        assert not result.success
        
        # Check that file was restored to original content
        restored_content = mock_codebase_with_files.get_file_content("unused_import.py")
        assert restored_content == original_content


class TestErrorResolver:
    """Test the error resolver system."""
    
    def test_resolver_initialization(self, mock_codebase_with_files):
        """Test error resolver initialization."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        assert resolver.codebase == mock_codebase_with_files
        assert resolver.error_manager == error_manager
        assert resolver.context_engine == context_engine
        assert resolver.resolution_stats["total_attempts"] == 0
    
    def test_resolve_single_error(self, mock_codebase_with_files):
        """Test resolving a single error."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create a resolvable error
        location = ErrorLocation("unused_import.py", 3, 0)
        error = UnifiedError(
            id="unused_json_import",
            message="unused import 'json'",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.UNUSED,
            location=location,
            source="ruff"
        )
        
        # Add fix to the error
        fix = ErrorFix(
            id="remove_unused_json",
            title="Remove unused import",
            description="Remove the unused json import",
            confidence=FixConfidence.HIGH,
            changes=[{
                "type": "delete_line",
                "file": "unused_import.py",
                "line": 3
            }]
        )
        error.add_fix(fix)
        
        # Add error to manager
        error_manager.add_error(error)
        
        # Resolve the error
        result = resolver.resolve_error(error.id)
        
        # Check result
        assert result.success
        assert result.error_id == error.id
        assert len(result.applied_fixes) > 0
        
        # Check statistics
        assert resolver.resolution_stats["total_attempts"] == 1
        assert resolver.resolution_stats["successful_fixes"] == 1
    
    def test_resolve_multiple_errors(self, mock_codebase_with_files):
        """Test resolving multiple errors."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create multiple resolvable errors
        errors = []
        
        # Error 1: Unused import
        location1 = ErrorLocation("unused_import.py", 3, 0)
        error1 = UnifiedError(
            id="unused_json_import",
            message="unused import 'json'",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.UNUSED,
            location=location1,
            source="ruff"
        )
        fix1 = ErrorFix(
            id="remove_unused_json",
            title="Remove unused import",
            description="Remove the unused json import",
            confidence=FixConfidence.HIGH,
            changes=[{"type": "delete_line", "file": "unused_import.py", "line": 3}]
        )
        error1.add_fix(fix1)
        errors.append(error1)
        
        # Error 2: Whitespace issue
        location2 = ErrorLocation("whitespace_issues.py", 1, 20)
        error2 = UnifiedError(
            id="missing_whitespace",
            message="missing whitespace around operator",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.STYLE,
            location=location2,
            source="flake8"
        )
        fix2 = ErrorFix(
            id="fix_whitespace",
            title="Fix whitespace",
            description="Add missing whitespace",
            confidence=FixConfidence.HIGH,
            changes=[{"type": "fix_whitespace", "file": "whitespace_issues.py", "line": 1}]
        )
        error2.add_fix(fix2)
        errors.append(error2)
        
        # Add errors to manager
        for error in errors:
            error_manager.add_error(error)
        
        # Resolve all errors
        error_ids = [e.id for e in errors]
        results = resolver.resolve_errors(error_ids)
        
        # Check results
        assert len(results) == 2
        successful_results = [r for r in results if r.success]
        assert len(successful_results) >= 1  # At least one should succeed
        
        # Check statistics
        assert resolver.resolution_stats["total_attempts"] == 2
    
    def test_fix_selection(self, mock_codebase_with_files):
        """Test fix selection logic."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create error with multiple fixes of different confidence levels
        location = ErrorLocation("test.py", 1, 0)
        error = UnifiedError(
            id="multi_fix_error",
            message="test error with multiple fixes",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=location,
            source="test"
        )
        
        # Add fixes with different confidence levels
        low_fix = ErrorFix(
            id="low_confidence_fix",
            title="Low confidence fix",
            description="This fix has low confidence",
            confidence=FixConfidence.LOW,
            changes=[{"type": "test_change"}]
        )
        
        high_fix = ErrorFix(
            id="high_confidence_fix",
            title="High confidence fix",
            description="This fix has high confidence",
            confidence=FixConfidence.HIGH,
            changes=[{"type": "test_change"}]
        )
        
        medium_fix = ErrorFix(
            id="medium_confidence_fix",
            title="Medium confidence fix",
            description="This fix has medium confidence",
            confidence=FixConfidence.MEDIUM,
            changes=[{"type": "test_change"}]
        )
        
        error.fixes = [low_fix, medium_fix, high_fix]  # Add in mixed order
        
        # Get context
        context = context_engine.get_full_error_context(error)
        
        # Select best fix
        best_fix = resolver._select_best_fix(error, context)
        
        # Should select the high confidence fix
        assert best_fix is not None
        assert best_fix.confidence == FixConfidence.HIGH
        assert best_fix.id == "high_confidence_fix"
    
    def test_can_resolve_error(self, mock_codebase_with_files):
        """Test checking if an error can be resolved."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create resolvable error
        location = ErrorLocation("test.py", 1, 0)
        resolvable_error = UnifiedError(
            id="resolvable_error",
            message="resolvable error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=location,
            source="test"
        )
        
        high_fix = ErrorFix(
            id="high_confidence_fix",
            title="High confidence fix",
            description="This fix has high confidence",
            confidence=FixConfidence.HIGH,
            requires_user_input=False,
            changes=[{"type": "test_change"}]
        )
        resolvable_error.add_fix(high_fix)
        
        # Create non-resolvable error
        non_resolvable_error = UnifiedError(
            id="non_resolvable_error",
            message="non-resolvable error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=location,
            source="test"
        )
        
        low_fix = ErrorFix(
            id="low_confidence_fix",
            title="Low confidence fix",
            description="This fix has low confidence",
            confidence=FixConfidence.LOW,
            changes=[{"type": "test_change"}]
        )
        non_resolvable_error.add_fix(low_fix)
        
        # Test resolution capability
        assert resolver.can_resolve_error(resolvable_error)
        assert not resolver.can_resolve_error(non_resolvable_error)
    
    def test_preview_resolution(self, mock_codebase_with_files):
        """Test resolution preview functionality."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create error with fix
        location = ErrorLocation("test.py", 1, 0)
        error = UnifiedError(
            id="preview_error",
            message="error for preview",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=location,
            source="test"
        )
        
        fix = ErrorFix(
            id="preview_fix",
            title="Preview fix",
            description="This is a preview fix",
            confidence=FixConfidence.HIGH,
            requires_user_input=False,
            estimated_impact="low",
            changes=[{"type": "test_change"}]
        )
        error.add_fix(fix)
        
        # Add to manager
        error_manager.add_error(error)
        
        # Preview resolution
        preview = resolver.preview_resolution(error.id)
        
        # Check preview
        assert preview["can_resolve"] is True
        assert preview["fix_title"] == "Preview fix"
        assert preview["confidence"] == "high"
        assert preview["requires_user_input"] is False
        assert preview["estimated_impact"] == "low"
    
    def test_resolution_statistics(self, mock_codebase_with_files):
        """Test resolution statistics tracking."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create and resolve some errors
        for i in range(3):
            location = ErrorLocation("test.py", i + 1, 0)
            error = UnifiedError(
                id=f"test_error_{i}",
                message=f"test error {i}",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OTHER,
                location=location,
                source="test"
            )
            
            # Add a fix that will succeed for even numbers, fail for odd
            if i % 2 == 0:
                fix = ErrorFix(
                    id=f"good_fix_{i}",
                    title=f"Good fix {i}",
                    description="This fix will work",
                    confidence=FixConfidence.HIGH,
                    changes=[{"type": "delete_line", "file": "unused_import.py", "line": 1}]
                )
            else:
                fix = ErrorFix(
                    id=f"bad_fix_{i}",
                    title=f"Bad fix {i}",
                    description="This fix will fail",
                    confidence=FixConfidence.HIGH,
                    changes=[{"type": "invalid_change_type"}]
                )
            
            error.add_fix(fix)
            error_manager.add_error(error)
        
        # Resolve all errors
        error_ids = [f"test_error_{i}" for i in range(3)]
        results = resolver.resolve_errors(error_ids)
        
        # Check statistics
        stats = resolver.get_resolution_stats()
        
        assert stats["total_attempts"] == 3
        assert stats["successful_fixes"] >= 1  # At least one should succeed
        assert stats["failed_fixes"] >= 1  # At least one should fail
        assert 0 <= stats["success_rate"] <= 1


class TestSafetyAndRollback:
    """Test safety mechanisms and rollback functionality."""
    
    def test_max_fixes_limit(self, mock_codebase_with_files):
        """Test that max_fixes parameter limits the number of fixes applied."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create multiple errors
        for i in range(5):
            location = ErrorLocation("test.py", i + 1, 0)
            error = UnifiedError(
                id=f"test_error_{i}",
                message=f"test error {i}",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OTHER,
                location=location,
                source="test"
            )
            
            fix = ErrorFix(
                id=f"fix_{i}",
                title=f"Fix {i}",
                description="Test fix",
                confidence=FixConfidence.HIGH,
                changes=[{"type": "delete_line", "file": "unused_import.py", "line": 1}]
            )
            error.add_fix(fix)
            error_manager.add_error(error)
        
        # Resolve with limit
        results = resolver.resolve_errors(max_fixes=2)
        
        # Should only attempt to fix 2 errors
        assert len(results) <= 2
    
    def test_auto_fixable_only_filter(self, mock_codebase_with_files):
        """Test that auto_fixable_only parameter filters correctly."""
        error_manager = MockErrorManager()
        context_engine = MockContextEngine(mock_codebase_with_files)
        resolver = ErrorResolver(mock_codebase_with_files, error_manager, context_engine)
        
        # Create mix of auto-fixable and non-auto-fixable errors
        auto_fixable_error = UnifiedError(
            id="auto_fixable",
            message="auto fixable error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=ErrorLocation("test.py", 1, 0),
            source="test"
        )
        
        high_fix = ErrorFix(
            id="high_fix",
            title="High confidence fix",
            description="Auto-fixable",
            confidence=FixConfidence.HIGH,
            changes=[{"type": "delete_line", "file": "unused_import.py", "line": 1}]
        )
        auto_fixable_error.add_fix(high_fix)
        
        non_auto_fixable_error = UnifiedError(
            id="non_auto_fixable",
            message="non auto fixable error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=ErrorLocation("test.py", 2, 0),
            source="test"
        )
        
        low_fix = ErrorFix(
            id="low_fix",
            title="Low confidence fix",
            description="Not auto-fixable",
            confidence=FixConfidence.LOW,
            changes=[{"type": "test_change"}]
        )
        non_auto_fixable_error.add_fix(low_fix)
        
        error_manager.add_error(auto_fixable_error)
        error_manager.add_error(non_auto_fixable_error)
        
        # Resolve with auto_fixable_only=True
        results = resolver.resolve_errors(auto_fixable_only=True)
        
        # Should only attempt to fix the auto-fixable error
        assert len(results) == 1
        assert results[0].error_id == "auto_fixable"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

