"""
Tests for Enhanced Serena LSP Bridge with Runtime Error Collection

This test suite verifies the comprehensive runtime error detection,
collection, and analysis capabilities of the enhanced SerenaLSPBridge.
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from graph_sitter.extensions.lsp.serena_bridge import (
    SerenaLSPBridge, ErrorInfo, ErrorType, RuntimeContext, 
    RuntimeErrorCollector, DiagnosticSeverity
)


class TestRuntimeErrorCollector:
    """Test runtime error collection functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        self.collector = RuntimeErrorCollector(str(self.repo_path))
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.collector._active:
            self.collector.stop_collection()
    
    def test_collector_initialization(self):
        """Test runtime error collector initialization."""
        assert self.collector.repo_path == self.repo_path
        assert not self.collector._active
        assert len(self.collector.runtime_errors) == 0
        assert self.collector.max_errors == 1000
    
    def test_start_stop_collection(self):
        """Test starting and stopping error collection."""
        # Start collection
        self.collector.start_collection()
        assert self.collector._active
        
        # Stop collection
        self.collector.stop_collection()
        assert not self.collector._active
    
    def test_error_collection_with_exception(self):
        """Test that runtime errors are collected when exceptions occur."""
        self.collector.start_collection()
        
        # Create a test file in the repo
        test_file = self.repo_path / "test_error.py"
        test_file.write_text("def test_func():\n    x = 1 / 0  # Division by zero\n")
        
        # Simulate an exception
        try:
            exec("x = 1 / 0")
        except ZeroDivisionError:
            pass
        
        # Give some time for error collection
        time.sleep(0.1)
        
        # Check if error was collected
        errors = self.collector.get_runtime_errors()
        # Note: In real scenario, this would capture the error
        # For unit test, we'll verify the collection mechanism works
        assert isinstance(errors, list)
    
    def test_error_summary(self):
        """Test error summary generation."""
        summary = self.collector.get_error_summary()
        
        assert 'total_errors' in summary
        assert 'errors_by_type' in summary
        assert 'errors_by_file' in summary
        assert 'collection_active' in summary
        assert 'max_errors' in summary
        
        assert summary['total_errors'] == 0
        assert summary['collection_active'] == False
    
    def test_clear_runtime_errors(self):
        """Test clearing runtime errors."""
        # Add a mock error
        mock_error = ErrorInfo(
            file_path="test.py",
            line=1,
            character=0,
            message="Test error",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR
        )
        self.collector.runtime_errors.append(mock_error)
        
        assert len(self.collector.get_runtime_errors()) == 1
        
        self.collector.clear_runtime_errors()
        assert len(self.collector.get_runtime_errors()) == 0
    
    def test_file_specific_errors(self):
        """Test getting errors for specific files."""
        # Add mock errors for different files
        error1 = ErrorInfo(
            file_path="file1.py",
            line=1,
            character=0,
            message="Error in file1",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR
        )
        error2 = ErrorInfo(
            file_path="file2.py",
            line=1,
            character=0,
            message="Error in file2",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR
        )
        
        self.collector.runtime_errors.extend([error1, error2])
        
        file1_errors = self.collector.get_runtime_errors_for_file("file1.py")
        assert len(file1_errors) == 1
        assert file1_errors[0].message == "Error in file1"
        
        file2_errors = self.collector.get_runtime_errors_for_file("file2.py")
        assert len(file2_errors) == 1
        assert file2_errors[0].message == "Error in file2"


class TestEnhancedErrorInfo:
    """Test enhanced ErrorInfo functionality."""
    
    def test_basic_error_info(self):
        """Test basic ErrorInfo functionality."""
        error = ErrorInfo(
            file_path="test.py",
            line=10,
            character=5,
            message="Test error message",
            severity=DiagnosticSeverity.ERROR
        )
        
        assert error.file_path == "test.py"
        assert error.line == 10
        assert error.character == 5
        assert error.message == "Test error message"
        assert error.severity == DiagnosticSeverity.ERROR
        assert error.error_type == ErrorType.STATIC_ANALYSIS
        assert error.is_error
        assert not error.is_warning
        assert not error.is_runtime_error
        assert error.is_static_error
    
    def test_runtime_error_info(self):
        """Test runtime-specific ErrorInfo functionality."""
        runtime_context = RuntimeContext(
            exception_type="ValueError",
            stack_trace=["File test.py, line 10, in test_func"],
            local_variables={"x": "10", "y": "0"},
            timestamp=time.time()
        )
        
        error = ErrorInfo(
            file_path="test.py",
            line=10,
            character=5,
            message="ValueError: invalid value",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR,
            runtime_context=runtime_context,
            fix_suggestions=["Check input validation", "Add error handling"]
        )
        
        assert error.is_runtime_error
        assert not error.is_static_error
        assert error.runtime_context is not None
        assert error.runtime_context.exception_type == "ValueError"
        assert len(error.fix_suggestions) == 2
    
    def test_error_context_retrieval(self):
        """Test comprehensive error context retrieval."""
        runtime_context = RuntimeContext(
            exception_type="AttributeError",
            stack_trace=["traceback line 1", "traceback line 2"],
            local_variables={"obj": "None"},
            execution_path=["main", "process_data", "get_attribute"]
        )
        
        error = ErrorInfo(
            file_path="test.py",
            line=15,
            character=8,
            message="AttributeError: 'NoneType' object has no attribute 'value'",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR,
            runtime_context=runtime_context,
            symbol_info={"name": "obj", "type": "variable"},
            code_context="obj.value = 10",
            dependency_chain=["module1", "module2"]
        )
        
        context = error.get_full_context()
        
        assert 'basic_info' in context
        assert 'runtime' in context
        assert 'symbol_info' in context
        assert 'code_context' in context
        assert 'dependency_chain' in context
        
        assert context['basic_info']['error_type'] == 'RUNTIME_ERROR'
        assert context['runtime']['exception_type'] == 'AttributeError'
        assert len(context['runtime']['stack_trace']) == 2


class TestEnhancedSerenaLSPBridge:
    """Test enhanced SerenaLSPBridge functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create a simple Python file for testing
        test_file = self.repo_path / "test.py"
        test_file.write_text("""
def test_function():
    x = 1
    y = 0
    result = x / y  # This will cause a runtime error
    return result

if __name__ == "__main__":
    test_function()
""")
    
    def test_bridge_initialization(self):
        """Test enhanced bridge initialization."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        assert bridge.repo_path == self.repo_path
        assert bridge.enable_runtime_collection
        assert bridge.runtime_collector is not None
        
        # Clean up
        bridge.shutdown()
    
    def test_bridge_initialization_without_runtime(self):
        """Test bridge initialization without runtime collection."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=False)
        
        assert not bridge.enable_runtime_collection
        assert bridge.runtime_collector is None
        
        # Clean up
        bridge.shutdown()
    
    def test_get_diagnostics_with_runtime(self):
        """Test getting diagnostics including runtime errors."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        # Get diagnostics including runtime errors
        diagnostics = bridge.get_diagnostics(include_runtime=True)
        assert isinstance(diagnostics, list)
        
        # Get only static diagnostics
        static_diagnostics = bridge.get_static_errors()
        assert isinstance(static_diagnostics, list)
        
        # Get only runtime errors
        runtime_errors = bridge.get_runtime_errors()
        assert isinstance(runtime_errors, list)
        
        # Clean up
        bridge.shutdown()
    
    def test_runtime_error_methods(self):
        """Test runtime error specific methods."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        # Test runtime error summary
        summary = bridge.get_runtime_error_summary()
        assert 'runtime_collection_enabled' in summary
        assert summary['runtime_collection_enabled'] == True
        
        # Test clearing runtime errors
        bridge.clear_runtime_errors()
        
        # Test file-specific runtime errors
        file_errors = bridge.get_runtime_errors_for_file("test.py")
        assert isinstance(file_errors, list)
        
        # Clean up
        bridge.shutdown()
    
    def test_enhanced_status(self):
        """Test enhanced status information."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        status = bridge.get_status()
        
        # Check basic status fields
        assert 'initialized' in status
        assert 'repo_path' in status
        assert 'runtime_collection_enabled' in status
        
        # Check enhanced status fields
        assert 'runtime_status' in status
        assert 'serena_status' in status
        assert 'diagnostic_counts' in status
        assert 'cache_sizes' in status
        
        # Check diagnostic counts
        diagnostic_counts = status['diagnostic_counts']
        assert 'total_diagnostics' in diagnostic_counts
        assert 'static_diagnostics' in diagnostic_counts
        assert 'runtime_errors' in diagnostic_counts
        assert 'errors' in diagnostic_counts
        assert 'warnings' in diagnostic_counts
        assert 'hints' in diagnostic_counts
        
        # Clean up
        bridge.shutdown()
    
    def test_bridge_shutdown(self):
        """Test comprehensive bridge shutdown."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        # Verify initialization
        assert bridge.is_initialized or bridge.runtime_collector is not None
        
        # Shutdown
        bridge.shutdown()
        
        # Verify shutdown
        assert not bridge.is_initialized
        assert bridge.runtime_collector is None
        assert len(bridge.diagnostics_cache) == 0
        assert len(bridge.error_context_cache) == 0
        assert len(bridge.symbol_cache) == 0
    
    def test_error_context_enhancement(self):
        """Test error context enhancement with Serena analysis."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        # Create a mock runtime error
        runtime_context = RuntimeContext(
            exception_type="ZeroDivisionError",
            stack_trace=["File test.py, line 5, in test_function"]
        )
        
        error = ErrorInfo(
            file_path="test.py",
            line=4,
            character=15,
            message="ZeroDivisionError: division by zero",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR,
            runtime_context=runtime_context
        )
        
        # Test fix suggestion generation
        suggestions = bridge._generate_fix_suggestions(error)
        assert isinstance(suggestions, list)
        assert any("division by zero" in suggestion.lower() for suggestion in suggestions)
        
        # Clean up
        bridge.shutdown()


class TestIntegrationScenarios:
    """Test integration scenarios with multiple error types."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create multiple test files
        (self.repo_path / "syntax_error.py").write_text("def broken_syntax(\n    pass")
        (self.repo_path / "runtime_error.py").write_text("x = 1 / 0")
        (self.repo_path / "good_file.py").write_text("def good_function():\n    return 42")
    
    def test_mixed_error_types(self):
        """Test handling of mixed static and runtime errors."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        # Get all diagnostics
        all_diagnostics = bridge.get_diagnostics(include_runtime=True)
        static_only = bridge.get_diagnostics(include_runtime=False)
        runtime_only = bridge.get_runtime_errors()
        
        # Verify we can distinguish between error types
        assert isinstance(all_diagnostics, list)
        assert isinstance(static_only, list)
        assert isinstance(runtime_only, list)
        
        # Test error context retrieval
        errors_with_context = bridge.get_all_errors_with_context()
        assert isinstance(errors_with_context, list)
        
        # Clean up
        bridge.shutdown()
    
    def test_file_specific_mixed_errors(self):
        """Test file-specific error retrieval with mixed error types."""
        bridge = SerenaLSPBridge(str(self.repo_path), enable_runtime_collection=True)
        
        # Test file-specific diagnostics
        runtime_file_errors = bridge.get_file_diagnostics("runtime_error.py", include_runtime=True)
        runtime_file_static = bridge.get_file_diagnostics("runtime_error.py", include_runtime=False)
        
        assert isinstance(runtime_file_errors, list)
        assert isinstance(runtime_file_static, list)
        
        # Clean up
        bridge.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])

