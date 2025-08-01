#!/usr/bin/env python3
"""
Comprehensive Test Suite for Consolidated LSP System

This test suite validates the consolidated LSP error retrieval system,
including all integrated components and their interactions.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import consolidated components
from graph_sitter.enhanced import Codebase
from graph_sitter.core.lsp_types import ErrorSeverity, ErrorType, ErrorInfo, ErrorCollection
from graph_sitter.core.lsp_type_adapters import LSPTypeAdapter, convert_serena_errors_to_unified
from graph_sitter.core.unified_diagnostics import UnifiedDiagnosticCollector
from graph_sitter.core.unified_analysis import UnifiedAnalyzer, AnalysisDepth
from graph_sitter.core.lsp_manager import LSPManager
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge, ErrorInfo as SerenaErrorInfo
from graph_sitter.extensions.lsp.protocol.lsp_types import DiagnosticSeverity


class TestLSPTypeAdapters:
    """Test LSP type conversion and adaptation."""
    
    def test_severity_conversion(self):
        """Test severity conversion between type systems."""
        # Test protocol to unified
        assert LSPTypeAdapter.severity_to_unified(DiagnosticSeverity.ERROR) == ErrorSeverity.ERROR
        assert LSPTypeAdapter.severity_to_unified(DiagnosticSeverity.WARNING) == ErrorSeverity.WARNING
        assert LSPTypeAdapter.severity_to_unified(DiagnosticSeverity.INFORMATION) == ErrorSeverity.INFO
        assert LSPTypeAdapter.severity_to_unified(DiagnosticSeverity.HINT) == ErrorSeverity.HINT
        
        # Test integer to unified
        assert LSPTypeAdapter.severity_to_unified(1) == ErrorSeverity.ERROR
        assert LSPTypeAdapter.severity_to_unified(2) == ErrorSeverity.WARNING
        assert LSPTypeAdapter.severity_to_unified(3) == ErrorSeverity.INFO
        assert LSPTypeAdapter.severity_to_unified(4) == ErrorSeverity.HINT
        
        # Test unified to protocol
        assert LSPTypeAdapter.severity_to_protocol(ErrorSeverity.ERROR) == DiagnosticSeverity.ERROR
        assert LSPTypeAdapter.severity_to_protocol(ErrorSeverity.WARNING) == DiagnosticSeverity.WARNING
        assert LSPTypeAdapter.severity_to_protocol(ErrorSeverity.INFO) == DiagnosticSeverity.INFORMATION
        assert LSPTypeAdapter.severity_to_protocol(ErrorSeverity.HINT) == DiagnosticSeverity.HINT
    
    def test_serena_error_conversion(self):
        """Test conversion from Serena ErrorInfo to unified ErrorInfo."""
        serena_error = SerenaErrorInfo(
            file_path="test.py",
            line=10,
            character=5,
            message="Undefined variable 'x'",
            severity=DiagnosticSeverity.ERROR,
            source="pylsp",
            code="undefined-variable"
        )
        
        unified_error = LSPTypeAdapter.serena_error_to_unified(serena_error)
        
        assert unified_error.file_path == "test.py"
        assert unified_error.line == 10
        assert unified_error.character == 5
        assert unified_error.message == "Undefined variable 'x'"
        assert unified_error.severity == ErrorSeverity.ERROR
        assert unified_error.error_type == ErrorType.UNDEFINED  # Should detect from message
        assert unified_error.source == "pylsp"
        assert unified_error.code == "undefined-variable"
    
    def test_error_type_detection(self):
        """Test automatic error type detection from message content."""
        test_cases = [
            ("Syntax error: invalid syntax", ErrorType.SYNTAX),
            ("Import error: module not found", ErrorType.IMPORT),
            ("Type error: incompatible types", ErrorType.TYPE_CHECK),
            ("Lint error: line too long", ErrorType.LINT),
            ("Undefined variable 'x'", ErrorType.UNDEFINED),
            ("Generic error message", ErrorType.SEMANTIC)  # Default
        ]
        
        for message, expected_type in test_cases:
            serena_error = SerenaErrorInfo(
                file_path="test.py",
                line=1,
                character=1,
                message=message,
                severity=DiagnosticSeverity.ERROR
            )
            
            unified_error = LSPTypeAdapter.serena_error_to_unified(serena_error)
            assert unified_error.error_type == expected_type


class TestUnifiedDiagnosticCollector:
    """Test unified diagnostic collection from multiple sources."""
    
    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase for testing."""
        codebase = Mock()
        codebase.repo_path = "/test/repo"
        return codebase
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # Create a simple Python file
        test_file = repo_path / "test.py"
        test_file.write_text("""
def hello_world():
    print("Hello, World!")
    undefined_variable  # This should cause an error
""")
        
        yield str(repo_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_collector_initialization(self, mock_codebase):
        """Test that the unified diagnostic collector initializes properly."""
        collector = UnifiedDiagnosticCollector(
            codebase=mock_codebase,
            enable_lsp=True,
            enable_transaction_awareness=True
        )
        
        assert collector.codebase == mock_codebase
        assert collector.enable_lsp is True
        assert collector.enable_transaction_awareness is True
        assert collector._unified_cache == []
        assert collector._file_cache == {}
    
    @patch('graph_sitter.core.unified_diagnostics.SerenaLSPBridge')
    @patch('graph_sitter.core.unified_diagnostics.TransactionAwareLSPManager')
    @patch('graph_sitter.core.unified_diagnostics.CodebaseDiagnostics')
    def test_diagnostic_collection(self, mock_core_diag, mock_transaction, mock_serena, mock_codebase):
        """Test diagnostic collection from multiple sources."""
        # Setup mocks
        mock_serena_instance = Mock()
        mock_serena_instance.get_all_diagnostics.return_value = [
            SerenaErrorInfo(
                file_path="test.py",
                line=1,
                character=1,
                message="Test error",
                severity=DiagnosticSeverity.ERROR
            )
        ]
        mock_serena.return_value = mock_serena_instance
        
        mock_transaction_instance = Mock()
        mock_transaction_instance.get_all_diagnostics.return_value = []
        mock_transaction.return_value = mock_transaction_instance
        
        mock_core_instance = Mock()
        mock_core_instance.get_errors.return_value = []
        mock_core_diag.return_value = mock_core_instance
        
        # Test collection
        collector = UnifiedDiagnosticCollector(mock_codebase)
        diagnostics = collector.get_all_diagnostics()
        
        assert isinstance(diagnostics, ErrorCollection)
        assert len(diagnostics.errors) == 1
        assert diagnostics.errors[0].message == "Test error"
        assert diagnostics.errors[0].severity == ErrorSeverity.ERROR
    
    def test_deduplication(self, mock_codebase):
        """Test that duplicate errors are properly deduplicated."""
        collector = UnifiedDiagnosticCollector(mock_codebase)
        
        # Create duplicate errors
        error1 = ErrorInfo(
            id="test1",
            file_path="test.py",
            line=1,
            character=1,
            message="Duplicate error",
            severity=ErrorSeverity.ERROR,
            error_type=ErrorType.SEMANTIC
        )
        
        error2 = ErrorInfo(
            id="test2",
            file_path="test.py",
            line=1,
            character=1,
            message="Duplicate error",  # Same message, position
            severity=ErrorSeverity.ERROR,
            error_type=ErrorType.SEMANTIC
        )
        
        error3 = ErrorInfo(
            id="test3",
            file_path="test.py",
            line=2,
            character=1,
            message="Different error",
            severity=ErrorSeverity.WARNING,
            error_type=ErrorType.LINT
        )
        
        deduplicated = collector._deduplicate_errors([error1, error2, error3])
        
        assert len(deduplicated) == 2  # Should remove one duplicate
        messages = [e.message for e in deduplicated]
        assert "Duplicate error" in messages
        assert "Different error" in messages


class TestUnifiedAnalyzer:
    """Test unified analysis system."""
    
    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase with test data."""
        codebase = Mock()
        
        # Mock files
        mock_file = Mock()
        mock_file.name = "test.py"
        mock_file.filepath = "/test/test.py"
        mock_file.classes = []
        mock_file.functions = []
        mock_file.imports = []
        
        codebase.files = [mock_file]
        codebase.functions = []
        codebase.classes = []
        codebase.symbols = []
        codebase.imports = []
        codebase.external_modules = []
        
        return codebase
    
    def test_basic_analysis(self, mock_codebase):
        """Test basic analysis functionality."""
        analyzer = UnifiedAnalyzer(mock_codebase)
        result = analyzer.analyze(AnalysisDepth.BASIC)
        
        assert result["analysis_type"] == "basic"
        assert "timestamp" in result
        assert "counts" in result
        assert result["counts"]["files"] == 1
        assert result["counts"]["functions"] == 0
        assert result["counts"]["classes"] == 0
    
    def test_analysis_depth_progression(self, mock_codebase):
        """Test that different analysis depths provide increasing detail."""
        analyzer = UnifiedAnalyzer(mock_codebase)
        
        basic_result = analyzer.analyze(AnalysisDepth.BASIC)
        standard_result = analyzer.analyze(AnalysisDepth.STANDARD)
        
        # Basic should have fewer keys than standard
        assert len(basic_result.keys()) <= len(standard_result.keys())
        
        # Standard should include metrics
        assert "metrics" in standard_result or "error" in standard_result
    
    def test_custom_analysis(self, mock_codebase):
        """Test custom analysis with configuration."""
        analyzer = UnifiedAnalyzer(mock_codebase)
        
        config = {
            "include_basic": True,
            "include_metrics": True,
            "include_deep": False
        }
        
        result = analyzer.analyze(AnalysisDepth.CUSTOM, config)
        
        assert result["analysis_type"] == "custom"
        assert result["config"] == config
    
    def test_quick_stats(self, mock_codebase):
        """Test quick statistics functionality."""
        analyzer = UnifiedAnalyzer(mock_codebase)
        stats = analyzer.get_quick_stats()
        
        assert isinstance(stats, dict)
        assert "files" in stats
        assert "functions" in stats
        assert "classes" in stats
        assert stats["files"] == 1


class TestLSPManager:
    """Test LSP manager functionality."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        yield str(repo_path)
        
        shutil.rmtree(temp_dir)
    
    def test_manager_initialization(self, temp_repo):
        """Test LSP manager initialization."""
        manager = LSPManager(temp_repo)
        
        assert str(manager.repo_path) == str(Path(temp_repo).resolve())
        assert manager._initialized is False
        assert manager._shutdown is False
    
    @patch('graph_sitter.core.lsp_manager.SerenaLSPBridge')
    @patch('graph_sitter.core.lsp_manager.TransactionAwareLSPManager')
    def test_lazy_initialization(self, mock_transaction, mock_serena, temp_repo):
        """Test that LSP components are lazily initialized."""
        mock_serena_instance = Mock()
        mock_serena.return_value = mock_serena_instance
        
        mock_transaction_instance = Mock()
        mock_transaction.return_value = mock_transaction_instance
        
        manager = LSPManager(temp_repo)
        
        # Should not be initialized yet
        assert manager._initialized is False
        
        # Trigger initialization
        success = manager._ensure_initialized()
        
        assert success is True
        assert manager._initialized is True
        assert mock_serena.called
        assert mock_transaction.called
    
    def test_caching_behavior(self, temp_repo):
        """Test that error caching works correctly."""
        manager = LSPManager(temp_repo)
        
        # Mock error collection
        mock_errors = ErrorCollection(
            errors=[],
            total_count=0,
            error_count=0,
            warning_count=0,
            info_count=0,
            hint_count=0,
            files_with_errors=0
        )
        
        # Test cache update
        manager._update_cache(mock_errors)
        assert manager._error_cache == mock_errors
        assert manager._cache_timestamp is not None
        
        # Test cache validity
        assert manager._is_cache_valid() is True
        
        # Test cache retrieval
        cached = manager._get_cached_errors()
        assert cached == mock_errors
        assert manager._cache_hits == 1


class TestEnhancedCodebaseIntegration:
    """Test enhanced codebase integration with consolidated LSP system."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()
        
        # Create a simple Python file
        test_file = repo_path / "test.py"
        test_file.write_text("""
def hello_world():
    print("Hello, World!")
""")
        
        yield str(repo_path)
        
        shutil.rmtree(temp_dir)
    
    def test_enhanced_codebase_creation(self, temp_repo):
        """Test that enhanced codebase can be created."""
        codebase = Codebase(temp_repo)
        
        assert codebase is not None
        assert hasattr(codebase, 'errors')
        assert hasattr(codebase, 'full_error_context')
        assert hasattr(codebase, 'health_check')
    
    @patch('graph_sitter.core.lsp_manager.SerenaLSPBridge')
    def test_error_retrieval_integration(self, mock_serena, temp_repo):
        """Test that error retrieval works through enhanced codebase."""
        # Setup mock
        mock_serena_instance = Mock()
        mock_serena_instance.get_all_diagnostics.return_value = []
        mock_serena.return_value = mock_serena_instance
        
        codebase = Codebase(temp_repo)
        errors = codebase.errors()
        
        assert isinstance(errors, ErrorCollection)
        assert errors.total_count >= 0
    
    def test_lsp_methods_availability(self, temp_repo):
        """Test that all LSP methods are available on enhanced codebase."""
        codebase = Codebase(temp_repo)
        
        # Core error retrieval methods
        assert hasattr(codebase, 'errors')
        assert hasattr(codebase, 'full_error_context')
        assert hasattr(codebase, 'errors_by_file')
        assert hasattr(codebase, 'errors_by_severity')
        assert hasattr(codebase, 'errors_by_type')
        
        # Advanced methods
        assert hasattr(codebase, 'error_summary')
        assert hasattr(codebase, 'error_trends')
        assert hasattr(codebase, 'most_common_errors')
        assert hasattr(codebase, 'error_hotspots')
        
        # Real-time monitoring
        assert hasattr(codebase, 'watch_errors')
        assert hasattr(codebase, 'refresh_errors')
        
        # Health and diagnostics
        assert hasattr(codebase, 'health_check')
        assert hasattr(codebase, 'lsp_status')
        assert hasattr(codebase, 'capabilities')


class TestErrorHandlingAndValidation:
    """Test error handling and parameter validation."""
    
    def test_invalid_file_path_handling(self):
        """Test handling of invalid file paths."""
        adapter = LSPTypeAdapter()
        
        # Test with None values
        try:
            result = adapter.position_to_unified(None)
            # Should handle gracefully or raise appropriate error
        except (AttributeError, TypeError):
            pass  # Expected for None input
    
    def test_malformed_diagnostic_handling(self):
        """Test handling of malformed diagnostic data."""
        collector = UnifiedDiagnosticCollector(Mock())
        
        # Test with empty list
        result = collector._deduplicate_errors([])
        assert result == []
        
        # Test with malformed error (missing required fields)
        try:
            malformed_error = ErrorInfo(
                id="test",
                file_path="",  # Empty path
                line=-1,       # Invalid line
                character=-1,  # Invalid character
                message="",    # Empty message
                severity=ErrorSeverity.ERROR,
                error_type=ErrorType.SEMANTIC
            )
            result = collector._deduplicate_errors([malformed_error])
            # Should handle gracefully
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"Should handle malformed errors gracefully: {e}")
    
    def test_concurrent_access_safety(self):
        """Test that concurrent access to LSP manager is safe."""
        import threading
        import time
        
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LSPManager(temp_dir)
            results = []
            errors = []
            
            def worker():
                try:
                    # Simulate concurrent initialization attempts
                    success = manager._ensure_initialized()
                    results.append(success)
                except Exception as e:
                    errors.append(e)
            
            # Start multiple threads
            threads = [threading.Thread(target=worker) for _ in range(5)]
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Should not have any errors from concurrent access
            assert len(errors) == 0
            # All threads should get consistent results
            assert len(set(results)) <= 1  # All same result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
