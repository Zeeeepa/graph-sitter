"""
Comprehensive Tests for Unified Error Interface

This test suite validates all error types and variations to ensure
the unified error interface works correctly and doesn't show false positives.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import os

from graph_sitter.extensions.serena.unified_error_models import (
    UnifiedError, ErrorSeverity, ErrorCategory, ErrorLocation, 
    ErrorFix, FixConfidence, ErrorSummary
)
from graph_sitter.extensions.serena.lsp_error_manager import UnifiedLSPErrorManager
from graph_sitter.extensions.serena.unified_error_context import ErrorContextEngine
from graph_sitter.extensions.serena.error_resolver import ErrorResolver
from graph_sitter.extensions.serena.unified_error_interface import UnifiedErrorInterface


class MockCodebase:
    """Mock codebase for testing."""
    
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


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_codebase(temp_repo):
    """Create a mock codebase with test files."""
    codebase = MockCodebase(temp_repo)
    
    # Add test files with various error types
    
    # File with syntax errors
    codebase.add_file("syntax_errors.py", """
# Syntax error: missing colon
def broken_function()
    return "missing colon"

# Syntax error: invalid indentation
def another_function():
return "bad indentation"

# Syntax error: unclosed parenthesis
result = some_function(arg1, arg2
""")
    
    # File with type errors
    codebase.add_file("type_errors.py", """
def add_numbers(a: int, b: int) -> int:
    return a + b

# Type error: wrong argument types
result = add_numbers("hello", "world")

# Type error: incompatible assignment
number: int = "not a number"

# Type error: missing return type annotation
def no_return_type(x):
    return x * 2
""")
    
    # File with import errors
    codebase.add_file("import_errors.py", """
# Import error: non-existent module
import non_existent_module

# Import error: non-existent symbol
from os import non_existent_function

# Import error: circular import (would need another file)
from . import circular_import

# Undefined name error
result = undefined_variable + 5

# Undefined function call
output = undefined_function()
""")
    
    # File with unused imports and variables
    codebase.add_file("unused_code.py", """
import os  # Unused import
import sys  # Used import
from typing import List, Dict, Optional  # Mixed usage

def example_function():
    unused_variable = "never used"
    used_variable = "this is used"
    another_unused = 42
    
    print(used_variable)
    sys.exit(0)  # Uses sys
    
    return used_variable
""")
    
    # File with style issues
    codebase.add_file("style_issues.py", """
# Style issues: missing whitespace, wrong line length, etc.
def bad_style(x,y,z):
    result=x+y+z
    very_long_line_that_exceeds_the_recommended_line_length_limit_and_should_be_broken_into_multiple_lines_for_better_readability = True
    return result

class BadClass:
    def method1(self):pass
    def method2(self):pass
""")
    
    # File with logic errors (that static analysis can catch)
    codebase.add_file("logic_errors.py", """
def divide_by_zero():
    return 10 / 0  # Division by zero

def unreachable_code():
    return "early return"
    print("This will never execute")  # Unreachable code

def missing_return():
    x = 5
    if x > 0:
        return "positive"
    # Missing return for negative/zero case

def duplicate_key():
    data = {
        "key1": "value1",
        "key2": "value2",
        "key1": "duplicate"  # Duplicate key
    }
    return data
""")
    
    # File with security issues
    codebase.add_file("security_issues.py", """
import subprocess
import pickle

def security_risk1(user_input):
    # Security risk: shell injection
    subprocess.call(f"echo {user_input}", shell=True)

def security_risk2(data):
    # Security risk: unsafe deserialization
    return pickle.loads(data)

def security_risk3():
    # Security risk: hardcoded password
    password = "hardcoded_password_123"
    return password
""")
    
    # File with performance issues
    codebase.add_file("performance_issues.py", """
def inefficient_loop():
    result = []
    for i in range(1000):
        result = result + [i]  # Inefficient list concatenation
    return result

def inefficient_string_concat():
    result = ""
    for i in range(100):
        result += str(i)  # Inefficient string concatenation
    return result

def unnecessary_list_comprehension():
    # Could be a generator
    return [x for x in range(1000000)]
""")
    
    # File with correct code (should have no errors)
    codebase.add_file("correct_code.py", """
from typing import List, Optional

def well_written_function(numbers: List[int]) -> Optional[int]:
    \"\"\"
    Calculate the sum of positive numbers in a list.
    
    Args:
        numbers: List of integers to process
        
    Returns:
        Sum of positive numbers, or None if no positive numbers found
    \"\"\"
    positive_numbers = [n for n in numbers if n > 0]
    
    if not positive_numbers:
        return None
    
    return sum(positive_numbers)

class WellWrittenClass:
    \"\"\"Example of a well-written class.\"\"\"
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    def greet(self) -> str:
        \"\"\"Return a greeting message.\"\"\"
        return f"Hello, {self.name}!"
""")
    
    return codebase


class TestUnifiedErrorModels:
    """Test the unified error data models."""
    
    def test_error_location_creation(self):
        """Test ErrorLocation creation and properties."""
        location = ErrorLocation(
            file_path="test.py",
            line=10,
            character=5,
            end_line=10,
            end_character=15
        )
        
        assert location.file_path == "test.py"
        assert location.line == 10
        assert location.character == 5
        assert location.range_text == "10:5-15"
        assert str(location) == "test.py:10:5-15"
    
    def test_unified_error_creation(self):
        """Test UnifiedError creation and auto-categorization."""
        location = ErrorLocation("test.py", 5, 10)
        
        error = UnifiedError(
            id="",  # Will be auto-generated
            message="undefined name 'missing_var'",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,  # Will be auto-categorized
            location=location,
            source="pylsp"
        )
        
        assert error.id  # Should be auto-generated
        assert error.category == ErrorCategory.UNDEFINED  # Auto-categorized
        assert error.is_error
        assert not error.is_warning
    
    def test_error_fix_creation(self):
        """Test ErrorFix creation."""
        fix = ErrorFix(
            id="fix_1",
            title="Add import",
            description="Add missing import statement",
            confidence=FixConfidence.HIGH,
            changes=[{"type": "add_import", "symbol": "os"}]
        )
        
        assert fix.confidence == FixConfidence.HIGH
        assert len(fix.changes) == 1
        
        fix_dict = fix.to_dict()
        assert fix_dict["confidence"] == "high"
        assert fix_dict["title"] == "Add import"


class TestLSPErrorManager:
    """Test the LSP error manager."""
    
    def test_error_manager_initialization(self, temp_repo):
        """Test error manager initialization."""
        manager = UnifiedLSPErrorManager(temp_repo, enable_background_refresh=False)
        
        # Should initialize even without LSP available
        assert manager.repo_path == Path(temp_repo)
        assert not manager.enable_background_refresh
    
    def test_error_cache(self):
        """Test error caching functionality."""
        from graph_sitter.extensions.serena.lsp_error_manager import LSPErrorCache
        
        cache = LSPErrorCache(ttl=1.0)
        
        # Create test error
        location = ErrorLocation("test.py", 1, 0)
        error = UnifiedError(
            id="test_error",
            message="Test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.OTHER,
            location=location,
            source="test"
        )
        
        # Test cache operations
        cache.set("test.py", [error])
        cached_errors = cache.get("test.py")
        
        assert cached_errors is not None
        assert len(cached_errors) == 1
        assert cached_errors[0].id == "test_error"
        
        # Test cache invalidation
        cache.invalidate("test.py")
        assert cache.get("test.py") is None


class TestErrorContextEngine:
    """Test the error context engine."""
    
    def test_symbol_analyzer(self, mock_codebase):
        """Test symbol analysis functionality."""
        from graph_sitter.extensions.serena.unified_error_context import SymbolAnalyzer
        
        analyzer = SymbolAnalyzer(mock_codebase)
        
        # Test symbol extraction from error message
        message = "undefined name 'missing_var'"
        symbols = analyzer._extract_symbol_names(message)
        
        assert "missing_var" in symbols
    
    def test_context_engine_initialization(self, mock_codebase):
        """Test context engine initialization."""
        engine = ErrorContextEngine(mock_codebase)
        
        assert engine.codebase == mock_codebase
        assert engine.symbol_analyzer is not None
        assert len(engine._context_cache) == 0


class TestErrorResolver:
    """Test the error resolution system."""
    
    def test_fix_applicator(self, mock_codebase):
        """Test fix application functionality."""
        from graph_sitter.extensions.serena.error_resolver import FixApplicator
        
        applicator = FixApplicator(mock_codebase)
        
        # Create a test error and fix
        location = ErrorLocation("test.py", 1, 0)
        error = UnifiedError(
            id="test_error",
            message="unused import 'os'",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.UNUSED,
            location=location,
            source="test"
        )
        
        fix = ErrorFix(
            id="remove_import",
            title="Remove unused import",
            description="Remove the unused import statement",
            confidence=FixConfidence.HIGH,
            changes=[{
                "type": "delete_line",
                "file": "test.py",
                "line": 1
            }]
        )
        
        # Test fix preview (without actually applying)
        assert fix.confidence == FixConfidence.HIGH
        assert len(fix.changes) == 1


class TestUnifiedErrorInterface:
    """Test the unified error interface."""
    
    def test_interface_initialization(self, mock_codebase):
        """Test interface initialization."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        assert interface.codebase == mock_codebase
        assert not interface._initialized
        assert not interface._initialization_attempted
    
    def test_lazy_loading(self, mock_codebase):
        """Test lazy loading of components."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        # Should not be initialized yet
        assert not interface._initialized
        
        # Calling a method should trigger initialization
        errors = interface.errors()
        
        # Should have attempted initialization
        assert interface._initialization_attempted
        
        # Errors should be a list (even if empty due to no LSP)
        assert isinstance(errors, list)


class TestErrorTypeValidation:
    """Test validation of different error types to avoid false positives."""
    
    def test_syntax_error_detection(self):
        """Test that syntax errors are correctly identified."""
        location = ErrorLocation("test.py", 1, 0)
        
        # Test various syntax error messages
        syntax_messages = [
            "invalid syntax",
            "unexpected EOF while parsing",
            "expected ':'",
            "invalid character in identifier"
        ]
        
        for message in syntax_messages:
            error = UnifiedError(
                id="",
                message=message,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OTHER,
                location=location,
                source="python"
            )
            
            assert error.category == ErrorCategory.SYNTAX
    
    def test_type_error_detection(self):
        """Test that type errors are correctly identified."""
        location = ErrorLocation("test.py", 1, 0)
        
        type_messages = [
            "incompatible types in assignment",
            "expected int, got str",
            "type mismatch",
            "incompatible return value type"
        ]
        
        for message in type_messages:
            error = UnifiedError(
                id="",
                message=message,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OTHER,
                location=location,
                source="mypy"
            )
            
            assert error.category == ErrorCategory.TYPE
    
    def test_import_error_detection(self):
        """Test that import errors are correctly identified."""
        location = ErrorLocation("test.py", 1, 0)
        
        import_messages = [
            "cannot import name 'missing'",
            "module 'os' has no attribute 'missing'",
            "no module named 'missing_module'"
        ]
        
        for message in import_messages:
            error = UnifiedError(
                id="",
                message=message,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OTHER,
                location=location,
                source="python"
            )
            
            assert error.category == ErrorCategory.IMPORT
    
    def test_undefined_error_detection(self):
        """Test that undefined name errors are correctly identified."""
        location = ErrorLocation("test.py", 1, 0)
        
        undefined_messages = [
            "undefined name 'missing_var'",
            "name 'missing_func' is not defined",
            "'missing_class' is not defined"
        ]
        
        for message in undefined_messages:
            error = UnifiedError(
                id="",
                message=message,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.OTHER,
                location=location,
                source="pylsp"
            )
            
            assert error.category == ErrorCategory.UNDEFINED
    
    def test_unused_code_detection(self):
        """Test that unused code is correctly identified."""
        location = ErrorLocation("test.py", 1, 0)
        
        unused_messages = [
            "unused import 'os'",
            "unused variable 'x'",
            "'func' is not used"
        ]
        
        for message in unused_messages:
            error = UnifiedError(
                id="",
                message=message,
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.OTHER,
                location=location,
                source="ruff"
            )
            
            assert error.category == ErrorCategory.UNUSED
    
    def test_style_issue_detection(self):
        """Test that style issues are correctly identified."""
        location = ErrorLocation("test.py", 1, 0)
        
        style_messages = [
            "line too long",
            "missing whitespace around operator",
            "expected 2 blank lines",
            "trailing whitespace"
        ]
        
        for message in style_messages:
            error = UnifiedError(
                id="",
                message=message,
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.OTHER,
                location=location,
                source="flake8"
            )
            
            assert error.category == ErrorCategory.STYLE


class TestErrorSummaryGeneration:
    """Test error summary generation."""
    
    def test_empty_summary(self):
        """Test summary with no errors."""
        summary = ErrorSummary()
        
        assert summary.total_errors == 0
        assert summary.total_warnings == 0
        assert summary.total_issues == 0
        assert summary.critical_issues == 0
    
    def test_summary_with_errors(self):
        """Test summary with various error types."""
        summary = ErrorSummary()
        summary.total_errors = 5
        summary.total_warnings = 10
        summary.total_info = 3
        summary.total_hints = 2
        
        assert summary.total_issues == 20
        assert summary.critical_issues == 5
        
        # Test dictionary conversion
        summary_dict = summary.to_dict()
        assert summary_dict["total_errors"] == 5
        assert summary_dict["total_issues"] == 20


class TestFixGeneration:
    """Test automatic fix generation."""
    
    def test_unused_import_fix(self):
        """Test fix generation for unused imports."""
        location = ErrorLocation("test.py", 1, 0)
        error = UnifiedError(
            id="",
            message="unused import 'os'",
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.UNUSED,
            location=location,
            source="ruff"
        )
        
        # The error should have auto-generated fixes
        assert len(error.fixes) > 0
        
        # Should have a high-confidence fix for removing unused import
        high_confidence_fixes = [f for f in error.fixes if f.confidence == FixConfidence.HIGH]
        assert len(high_confidence_fixes) > 0
        
        # Should be marked as auto-fixable
        assert error.auto_fixable
    
    def test_undefined_name_fix(self):
        """Test fix generation for undefined names."""
        location = ErrorLocation("test.py", 1, 0)
        error = UnifiedError(
            id="",
            message="undefined name 'os'",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.UNDEFINED,
            location=location,
            source="pylsp"
        )
        
        # Should have fixes, but they might require user input
        assert len(error.fixes) > 0
        
        # Check if any fixes require user input (which is expected for imports)
        user_input_fixes = [f for f in error.fixes if f.requires_user_input]
        assert len(user_input_fixes) > 0


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_full_error_workflow(self, mock_codebase):
        """Test the complete error detection and resolution workflow."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        # Get all errors
        all_errors = interface.errors()
        assert isinstance(all_errors, list)
        
        # Get error summary
        summary = interface.error_summary()
        assert isinstance(summary, ErrorSummary)
        
        # Get fixable errors
        fixable_errors = interface.get_fixable_errors()
        assert isinstance(fixable_errors, list)
        
        # All fixable errors should be in the main error list
        fixable_ids = {e.id for e in fixable_errors}
        all_ids = {e.id for e in all_errors}
        assert fixable_ids.issubset(all_ids)
    
    def test_error_filtering(self, mock_codebase):
        """Test error filtering functionality."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        # Test filtering by severity
        errors_with_warnings = interface.errors(include_warnings=True)
        errors_without_warnings = interface.errors(include_warnings=False)
        
        assert isinstance(errors_with_warnings, list)
        assert isinstance(errors_without_warnings, list)
        
        # Test filtering by category
        syntax_errors = interface.errors(category="syntax")
        assert isinstance(syntax_errors, list)
        
        # All returned errors should be syntax errors
        for error in syntax_errors:
            assert error.category == ErrorCategory.SYNTAX
    
    def test_error_context_retrieval(self, mock_codebase):
        """Test error context retrieval."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        # Get some errors first
        errors = interface.errors()
        
        if errors:
            # Get context for the first error
            context = interface.full_error_context(errors[0].id)
            
            if context:  # Context might be None if LSP is not available
                assert context.error.id == errors[0].id
                assert isinstance(context.surrounding_code, str)
    
    def test_fix_preview(self, mock_codebase):
        """Test fix preview functionality."""
        interface = UnifiedErrorInterface(mock_codebase)
        
        # Get fixable errors
        fixable_errors = interface.get_fixable_errors()
        
        if fixable_errors:
            # Preview fix for the first fixable error
            preview = interface.preview_fix(fixable_errors[0].id)
            
            assert isinstance(preview, dict)
            assert "can_resolve" in preview


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

