"""Unit tests for AutoGenLibAdapter."""

import pytest
from src.analysis_utils import AnalysisError


class TestAutoGenLibAdapter:
    """Test suite for AutoGenLibAdapter."""
    
    def test_initialization(self, autogenlib_adapter):
        """Test adapter initializes correctly."""
        assert autogenlib_adapter is not None
        assert autogenlib_adapter.codebase is not None
        assert autogenlib_adapter.gs_adapter is not None
        assert hasattr(autogenlib_adapter, '_context_cache')
    
    def test_get_error_context(self, autogenlib_adapter, sample_error):
        """Test error context generation."""
        context = autogenlib_adapter.get_error_context(sample_error)
        
        assert isinstance(context, dict)
        assert 'error' in context or 'file_path' in context
        
        if 'file_path' in context:
            assert context['file_path'] == sample_error.file_path
            assert context['line'] == sample_error.line
            assert 'code_snippet' in context
    
    def test_generate_fix_strategy(self, autogenlib_adapter, sample_error):
        """Test fix strategy generation."""
        errors = [sample_error]
        strategy = autogenlib_adapter.generate_fix_strategy(errors)
        
        assert isinstance(strategy, dict)
        assert 'total_errors' in strategy
        assert strategy['total_errors'] == 1
        assert 'by_severity' in strategy
        assert 'by_category' in strategy
        assert 'priority_order' in strategy
    
    def test_resolve_multiple_errors(self, autogenlib_adapter, sample_error):
        """Test multiple error resolution."""
        errors = [sample_error]
        results = autogenlib_adapter.resolve_multiple_errors(errors, max_fixes=1)
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], dict)
    
    def test_generate_comprehensive_context(self, autogenlib_adapter, sample_error):
        """Test comprehensive context generation."""
        errors = [sample_error]
        context = autogenlib_adapter.generate_comprehensive_context(errors)
        
        assert isinstance(context, dict)
        assert 'codebase_overview' in context
        assert 'error_summary' in context
        assert 'patterns' in context
        assert 'related_files' in context
        assert 'suggested_approach' in context
        
        # Verify error summary structure
        summary = context['error_summary']
        assert 'total' in summary
        assert summary['total'] == 1
        assert 'by_severity' in summary
        assert 'by_category' in summary
    
    def test_batch_resolve(self, autogenlib_adapter, sample_error):
        """Test batch error resolution."""
        errors = [sample_error] * 3  # Create 3 errors
        results = autogenlib_adapter.batch_resolve(errors, batch_size=2)
        
        assert isinstance(results, list)
        assert len(results) == 3
    
    def test_error_grouping(self, autogenlib_adapter, sample_error):
        """Test error grouping methods."""
        errors = [sample_error]
        
        by_severity = autogenlib_adapter._group_by_severity(errors)
        assert isinstance(by_severity, dict)
        assert 'error' in by_severity
        
        by_category = autogenlib_adapter._group_by_category(errors)
        assert isinstance(by_category, dict)
        
        by_file = autogenlib_adapter._group_by_file(errors)
        assert isinstance(by_file, dict)
    
    def test_find_error_patterns(self, autogenlib_adapter):
        """Test error pattern detection."""
        # Create multiple errors with same type
        errors = [
            AnalysisError(
                file_path=f"file{i}.py",
                line=i,
                column=0,
                error_type="type_error",
                severity="error",
                message="Type error",
                tool_source="mypy",
                category="type_checking"
            )
            for i in range(5)
        ]
        
        patterns = autogenlib_adapter._find_error_patterns(errors)
        
        assert isinstance(patterns, list)
        # Should detect repeated error type pattern
        if patterns:
            pattern = patterns[0]
            assert 'type' in pattern
            assert 'count' in pattern
    
    def test_get_relevant_files(self, autogenlib_adapter, sample_error):
        """Test relevant files identification."""
        errors = [sample_error]
        files = autogenlib_adapter._get_relevant_files(errors)
        
        assert isinstance(files, list)
        assert sample_error.file_path in files
    
    def test_generate_fix_approach(self, autogenlib_adapter):
        """Test fix approach generation."""
        # Test with critical errors
        critical_errors = [
            AnalysisError(
                file_path="file.py",
                line=1,
                column=0,
                error_type="error",
                severity="error",
                message="Critical error",
                tool_source="ruff",
                category="syntax"
            )
        ]
        
        approach = autogenlib_adapter._generate_fix_approach(critical_errors)
        assert isinstance(approach, str)
        assert "critical" in approach.lower() or "error" in approach.lower()
    
    def test_batch_context_generation(self, autogenlib_adapter, sample_error):
        """Test batch context generation."""
        batch = [sample_error]
        context = autogenlib_adapter._get_batch_context(batch)
        
        assert isinstance(context, dict)
        assert 'batch_size' in context
        assert context['batch_size'] == 1
        assert 'common_files' in context
        assert 'severity_distribution' in context
    
    def test_code_snippet_extraction(self, autogenlib_adapter):
        """Test code snippet extraction."""
        # This will fail gracefully if file doesn't exist
        snippet = autogenlib_adapter._get_code_snippet(
            "src/analysis_utils.py",
            10,
            context_lines=3
        )
        
        assert isinstance(snippet, str)
    
    def test_error_prioritization(self, autogenlib_adapter):
        """Test error prioritization."""
        errors = [
            AnalysisError(
                file_path="file1.py", line=1, column=0,
                error_type="error", severity="error",
                message="Error 1", tool_source="ruff",
                category="syntax", confidence=0.9
            ),
            AnalysisError(
                file_path="file2.py", line=2, column=0,
                error_type="warning", severity="warning",
                message="Warning 1", tool_source="ruff",
                category="style", confidence=0.5
            )
        ]
        
        priority = autogenlib_adapter._prioritize_errors(errors)
        
        assert isinstance(priority, list)
        assert len(priority) <= 10  # Should limit to top 10
        # Error should be prioritized over warning
        if len(priority) >= 2:
            assert "file1.py" in priority[0]
    
    def test_fix_effort_estimation(self, autogenlib_adapter, sample_error):
        """Test fix effort estimation."""
        few_errors = [sample_error] * 3
        many_errors = [sample_error] * 15
        lots_of_errors = [sample_error] * 25
        
        assert autogenlib_adapter._estimate_fix_effort(few_errors) == "low"
        assert autogenlib_adapter._estimate_fix_effort(many_errors) == "medium"
        assert autogenlib_adapter._estimate_fix_effort(lots_of_errors) == "high"

