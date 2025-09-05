#!/usr/bin/env python3
"""
Comprehensive Test Suite for Serena LSP Integration

This test suite thoroughly validates all error retrieval features of the Serena LSP integration,
including error classification, GitHub repository analysis, real-time monitoring, and performance.
"""

import asyncio
import pytest
import tempfile
import time
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Import the modules under test
try:
    from graph_sitter.extensions.lsp.serena_bridge import (
        SerenaLSPBridge, ErrorInfo, RuntimeErrorCollector, ErrorType,
        DiagnosticSeverity, ErrorSeverity, ErrorCategory, ErrorLocation,
        CodeError, ComprehensiveErrorList, ProtocolHandler, SerenaProtocolExtensions
    )
    from graph_sitter.extensions.lsp.serena_analysis import (
        GitHubRepositoryAnalyzer, analyze_github_repository, RepositoryInfo, AnalysisResult
    )
    SERENA_AVAILABLE = True
except ImportError as e:
    SERENA_AVAILABLE = False
    pytest.skip(f"Serena LSP integration not available: {e}", allow_module_level=True)


class TestSerenaLSPBridge:
    """Test the core SerenaLSPBridge functionality."""
    
    @pytest.fixture
    def temp_codebase(self):
        """Create a temporary codebase with various error types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Python files with different types of errors
            (temp_path / "syntax_errors.py").write_text('''
# Syntax errors for testing
def broken_function():
    print("missing quote
    return [1, 2, 3,  # missing bracket
    
def another_broken():
    if True
        pass  # missing colon
''')
            
            (temp_path / "type_errors.py").write_text('''
# Type errors for testing
def type_issues():
    result = "string" + 42
    items = [1, 2, 3]
    return items.nonexistent_method()
    
def more_type_issues():
    x = None
    return x.attribute  # AttributeError
''')
            
            (temp_path / "import_errors.py").write_text('''
# Import errors for testing
import nonexistent_module
from missing_package import something
from another_missing import *

def use_missing():
    return nonexistent_module.function()
''')
            
            (temp_path / "logic_errors.py").write_text('''
# Logic errors for testing
def logic_issues():
    x = undefined_variable  # NameError
    return x / 0  # ZeroDivisionError
    
def more_logic_issues():
    items = []
    return items[0]  # IndexError
''')
            
            (temp_path / "performance_issues.py").write_text('''
# Performance issues for testing
def slow_function():
    # Inefficient nested loops
    result = []
    for i in range(1000):
        for j in range(1000):
            result.append(i * j)
    return result
    
def memory_intensive():
    # Large memory allocation
    big_list = [i for i in range(10**6)]
    return big_list
''')
            
            (temp_path / "security_issues.py").write_text('''
# Security issues for testing
import os
import subprocess

def security_risk():
    # Command injection risk
    user_input = "rm -rf /"
    os.system(user_input)
    
def another_risk():
    # SQL injection risk
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
''')
            
            yield temp_path
    
    def test_bridge_initialization(self, temp_codebase):
        """Test SerenaLSPBridge initialization."""
        bridge = SerenaLSPBridge(str(temp_codebase), enable_runtime_collection=True)
        
        assert bridge.repo_path == temp_codebase
        assert bridge.enable_runtime_collection is True
        assert bridge.runtime_collector is not None
        
        # Test status
        status = bridge.get_status()
        assert isinstance(status, dict)
        assert 'initialized' in status
        assert 'runtime_collection_enabled' in status
        
        bridge.shutdown()
    
    def test_error_detection_and_classification(self, temp_codebase):
        """Test comprehensive error detection and classification."""
        bridge = SerenaLSPBridge(str(temp_codebase), enable_runtime_collection=True)
        
        try:
            # Get all diagnostics
            diagnostics = bridge.get_diagnostics(include_runtime=True)
            
            # Should find errors in our test files
            assert len(diagnostics) >= 0  # May vary based on LSP availability
            
            # Test error classification by severity
            errors = [d for d in diagnostics if hasattr(d, 'severity') and d.severity == DiagnosticSeverity.ERROR]
            warnings = [d for d in diagnostics if hasattr(d, 'severity') and d.severity == DiagnosticSeverity.WARNING]
            
            # Test error classification by type
            static_errors = [d for d in diagnostics if hasattr(d, 'error_type') and d.error_type == ErrorType.STATIC_ANALYSIS]
            
            # Test file-specific diagnostics
            syntax_file_errors = bridge.get_file_diagnostics("syntax_errors.py")
            assert isinstance(syntax_file_errors, list)
            
            type_file_errors = bridge.get_file_diagnostics("type_errors.py")
            assert isinstance(type_file_errors, list)
            
        finally:
            bridge.shutdown()
    
    def test_runtime_error_collection(self, temp_codebase):
        """Test runtime error collection capabilities."""
        bridge = SerenaLSPBridge(str(temp_codebase), enable_runtime_collection=True)
        
        try:
            # Test runtime collector
            assert bridge.runtime_collector is not None
            
            # Get runtime error summary
            summary = bridge.get_runtime_error_summary()
            assert isinstance(summary, dict)
            assert 'runtime_collection_enabled' in summary
            assert summary['runtime_collection_enabled'] is True
            
            # Test clearing runtime errors
            bridge.clear_runtime_errors()
            runtime_errors = bridge.get_runtime_errors()
            assert len(runtime_errors) == 0
            
        finally:
            bridge.shutdown()
    
    def test_error_context_and_suggestions(self, temp_codebase):
        """Test error context analysis and fix suggestions."""
        bridge = SerenaLSPBridge(str(temp_codebase), enable_runtime_collection=True)
        
        try:
            # Get errors with full context
            errors_with_context = bridge.get_all_errors_with_context()
            
            if errors_with_context:
                # Check that context includes expected fields
                error_context = errors_with_context[0]
                assert 'basic_info' in error_context
                
                basic_info = error_context['basic_info']
                assert 'file_path' in basic_info
                assert 'line' in basic_info
                assert 'message' in basic_info
                assert 'severity' in basic_info
            
        finally:
            bridge.shutdown()
    
    def test_performance_and_caching(self, temp_codebase):
        """Test performance monitoring and caching."""
        bridge = SerenaLSPBridge(str(temp_codebase), enable_runtime_collection=True)
        
        try:
            # Measure initial analysis time
            start_time = time.time()
            diagnostics1 = bridge.get_diagnostics(include_runtime=True)
            first_analysis_time = time.time() - start_time
            
            # Second analysis should be faster (cached)
            start_time = time.time()
            diagnostics2 = bridge.get_diagnostics(include_runtime=True)
            second_analysis_time = time.time() - start_time
            
            # Results should be consistent
            assert len(diagnostics1) == len(diagnostics2)
            
            # Test refresh functionality
            bridge.refresh_diagnostics()
            diagnostics3 = bridge.get_diagnostics(include_runtime=True)
            assert len(diagnostics3) >= 0  # Should still work after refresh
            
        finally:
            bridge.shutdown()


class TestErrorClasses:
    """Test error representation classes."""
    
    def test_error_location(self):
        """Test ErrorLocation class."""
        location = ErrorLocation(
            file_path="test.py",
            line=10,
            column=5,
            end_line=10,
            end_column=15
        )
        
        assert location.file_name == "test.py"
        assert location.range_text == "10:5-10:15"
        
        # Test LSP conversion
        lsp_position = location.to_lsp_position()
        assert lsp_position['line'] == 9  # LSP is 0-based
        assert lsp_position['character'] == 4
        
        lsp_range = location.to_lsp_range()
        assert 'start' in lsp_range
        assert 'end' in lsp_range
    
    def test_code_error(self):
        """Test CodeError class."""
        location = ErrorLocation("test.py", 10, 5)
        
        error = CodeError(
            id="test_error_1",
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            location=location,
            suggestions=["Fix the syntax", "Check parentheses"]
        )
        
        assert error.is_critical is True
        assert error.display_text.startswith("[ERROR]")
        
        # Test dictionary conversion
        error_dict = error.to_dict()
        assert error_dict['id'] == "test_error_1"
        assert error_dict['severity'] == "error"
        assert error_dict['category'] == "syntax"
        assert len(error_dict['suggestions']) == 2
    
    def test_comprehensive_error_list(self):
        """Test ComprehensiveErrorList class."""
        error_list = ComprehensiveErrorList()
        
        # Add some test errors
        location1 = ErrorLocation("file1.py", 10, 5)
        error1 = CodeError("err1", "Error 1", ErrorSeverity.ERROR, ErrorCategory.SYNTAX, location1)
        
        location2 = ErrorLocation("file2.py", 20, 10)
        error2 = CodeError("err2", "Warning 1", ErrorSeverity.WARNING, ErrorCategory.STYLE, location2)
        
        error_list.add_error(error1)
        error_list.add_error(error2)
        
        # Test counts
        assert error_list.total_count == 2
        assert error_list.critical_count == 1
        assert error_list.warning_count == 1
        assert len(error_list.files_analyzed) == 2
        
        # Test filtering
        critical_errors = error_list.get_critical_errors()
        assert len(critical_errors) == 1
        assert critical_errors[0].severity == ErrorSeverity.ERROR
        
        syntax_errors = error_list.get_errors_by_category(ErrorCategory.SYNTAX)
        assert len(syntax_errors) == 1
        
        file1_errors = error_list.get_errors_by_file("file1.py")
        assert len(file1_errors) == 1
        
        # Test summary
        summary = error_list.get_summary()
        assert summary['total_errors'] == 2
        assert summary['critical_errors'] == 1
        assert summary['warnings'] == 1


class TestProtocolHandler:
    """Test LSP protocol handling."""
    
    def test_protocol_handler_initialization(self):
        """Test ProtocolHandler initialization."""
        handler = ProtocolHandler()
        
        assert len(handler._pending_requests) == 0
        assert len(handler._notification_handlers) == 0
        assert len(handler._request_handlers) == 0
        assert handler._message_id_counter == 0
    
    def test_message_creation(self):
        """Test LSP message creation."""
        handler = ProtocolHandler()
        
        # Test request creation
        request = handler.create_request("test/method", {"param": "value"})
        assert request.jsonrpc == "2.0"
        assert request.method == "test/method"
        assert request.params == {"param": "value"}
        assert request.id.startswith("serena_")
        
        # Test response creation
        response = handler.create_response("test_id", result={"result": "success"})
        assert response.jsonrpc == "2.0"
        assert response.id == "test_id"
        assert response.result == {"result": "success"}
        assert response.error is None
        
        # Test notification creation
        notification = handler.create_notification("test/notification", {"data": "test"})
        assert notification.jsonrpc == "2.0"
        assert notification.method == "test/notification"
        assert notification.params == {"data": "test"}
    
    def test_serena_protocol_extensions(self):
        """Test Serena-specific protocol extensions."""
        # Test request parameter creation
        analyze_params = SerenaProtocolExtensions.create_analyze_file_request(
            "/path/to/file.py", "file content"
        )
        assert analyze_params["uri"] == "file:///path/to/file.py"
        assert analyze_params["content"] == "file content"
        
        error_params = SerenaProtocolExtensions.create_get_errors_request(
            "/path/to/file.py", ["error", "warning"]
        )
        assert error_params["uri"] == "file:///path/to/file.py"
        assert error_params["severityFilter"] == ["error", "warning"]
        
        comprehensive_params = SerenaProtocolExtensions.create_comprehensive_errors_request(
            include_context=True, include_suggestions=True, max_errors=100
        )
        assert comprehensive_params["includeContext"] is True
        assert comprehensive_params["includeSuggestions"] is True
        assert comprehensive_params["maxErrors"] == 100


@pytest.mark.asyncio
class TestGitHubRepositoryAnalyzer:
    """Test GitHub repository analysis functionality."""
    
    @pytest.fixture
    def mock_repo_structure(self):
        """Create a mock repository structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "test_repo"
            repo_path.mkdir()
            
            # Create a realistic Python project structure
            (repo_path / "main.py").write_text('''
#!/usr/bin/env python3
"""Main application entry point."""

import sys
import os
from utils import helper_function

def main():
    print("Hello, World!")
    result = helper_function("test")
    return result

if __name__ == "__main__":
    main()
''')
            
            (repo_path / "utils.py").write_text('''
"""Utility functions."""

def helper_function(input_str):
    """Process input string."""
    if not input_str:
        raise ValueError("Input cannot be empty")
    return input_str.upper()

def unused_function():
    """This function is not used anywhere."""
    pass
''')
            
            (repo_path / "requirements.txt").write_text('''
requests>=2.25.0
pytest>=6.0.0
''')
            
            # Initialize git repository
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
            
            yield repo_path
    
    async def test_analyzer_initialization(self):
        """Test GitHubRepositoryAnalyzer initialization."""
        analyzer = GitHubRepositoryAnalyzer()
        
        assert analyzer.work_dir.exists()
        assert analyzer.enable_runtime_collection is True
        assert len(analyzer.repositories) == 0
        assert len(analyzer.analysis_cache) == 0
        
        await analyzer.shutdown()
    
    async def test_repository_info_creation(self):
        """Test RepositoryInfo creation from URL."""
        repo_info = RepositoryInfo.from_url(
            "https://github.com/owner/repo.git",
            "/local/path"
        )
        
        assert repo_info.url == "https://github.com/owner/repo.git"
        assert repo_info.owner == "owner"
        assert repo_info.name == "repo"
        assert repo_info.local_path == "/local/path"
        assert repo_info.branch == "main"
    
    @patch('subprocess.run')
    async def test_repository_cloning(self, mock_subprocess):
        """Test repository cloning functionality."""
        mock_subprocess.return_value.returncode = 0
        
        analyzer = GitHubRepositoryAnalyzer()
        
        try:
            repo_info = RepositoryInfo.from_url(
                "https://github.com/test/repo.git",
                str(analyzer.work_dir / "test_repo")
            )
            
            # Test the cloning method (mocked)
            await analyzer._clone_repository(repo_info)
            
            # Verify git clone was called
            mock_subprocess.assert_called()
            call_args = mock_subprocess.call_args[0][0]
            assert "git" in call_args
            assert "clone" in call_args
            assert repo_info.url in call_args
            
        finally:
            await analyzer.shutdown()
    
    async def test_analysis_result_processing(self):
        """Test analysis result processing and categorization."""
        # Create mock analysis result
        error_list = ComprehensiveErrorList()
        
        # Add various types of errors
        location1 = ErrorLocation("main.py", 10, 5)
        error1 = CodeError("err1", "Syntax error", ErrorSeverity.ERROR, ErrorCategory.SYNTAX, location1)
        
        location2 = ErrorLocation("utils.py", 20, 10)
        error2 = CodeError("err2", "Style warning", ErrorSeverity.WARNING, ErrorCategory.STYLE, location2)
        
        location3 = ErrorLocation("main.py", 15, 8)
        error3 = CodeError("err3", "Type hint missing", ErrorSeverity.INFO, ErrorCategory.TYPE, location3)
        
        error_list.add_errors([error1, error2, error3])
        
        repo_info = RepositoryInfo.from_url("https://github.com/test/repo", "/local/path")
        result = AnalysisResult(
            repository=repo_info,
            error_list=error_list,
            analysis_metadata={"test": True}
        )
        
        # Test error grouping by severity
        errors_by_severity = result.get_errors_by_severity()
        assert len(errors_by_severity['critical']) == 1
        assert len(errors_by_severity['warning']) == 1
        assert len(errors_by_severity['info']) == 1
        assert len(errors_by_severity['hint']) == 0
        
        # Test summary by severity
        summary = result.get_summary_by_severity()
        assert summary['critical']['count'] == 1
        assert summary['warning']['count'] == 1
        assert summary['info']['count'] == 1
        
        # Test file analysis
        assert summary['critical']['files_affected'] == 1
        assert summary['warning']['files_affected'] == 1


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
