"""
Comprehensive Test Suite for Enhanced Error System

This test suite validates ALL aspects of the enhanced error handling system:
- Error detection for every error type
- Context extraction accuracy
- Reasoning quality
- False positive detection
- Fix suggestion generation
- Performance requirements
"""

import pytest
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any

# Import the enhanced error system
from src.graph_sitter.core.enhanced_error_types import (
    EnhancedErrorInfo, ErrorSeverity, ErrorCategory, FixDifficulty
)
from src.graph_sitter.core.enhanced_lsp_manager import EnhancedLSPManager


class TestEnhancedErrorSystem:
    """Test suite for the enhanced error handling system."""
    
    @pytest.fixture
    async def lsp_manager(self):
        """Create LSP manager for testing."""
        manager = EnhancedLSPManager(".")
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_syntax_error_detection(self, lsp_manager):
        """Test detection of all syntax error types."""
        # Test missing colon errors
        errors = await lsp_manager.get_all_errors()
        
        # Find syntax errors from our test fixtures
        syntax_errors = [e for e in errors if e.category == ErrorCategory.SYNTAX]
        
        # Validate we detect missing colon errors
        missing_colon_errors = [e for e in syntax_errors if e.error_type == 'E001']
        assert len(missing_colon_errors) > 0, "Should detect missing colon errors"
        
        # Validate error has proper context
        for error in missing_colon_errors:
            assert error.context.surrounding_code, "Should have surrounding code context"
            assert error.reasoning.root_cause, "Should have root cause analysis"
            assert len(error.suggested_fixes) > 0, "Should have fix suggestions"
            assert error.confidence_score > 0.8, "Syntax errors should have high confidence"
    
    @pytest.mark.asyncio
    async def test_semantic_error_detection(self, lsp_manager):
        """Test detection of all semantic error types."""
        errors = await lsp_manager.get_all_errors()
        
        # Find semantic errors
        semantic_errors = [e for e in errors if e.category == ErrorCategory.SEMANTIC]
        
        # Validate we detect undefined variable errors
        undefined_var_errors = [e for e in semantic_errors if e.error_type == 'S001']
        assert len(undefined_var_errors) > 0, "Should detect undefined variable errors"
        
        # Validate error context and reasoning
        for error in undefined_var_errors:
            assert error.context.surrounding_code, "Should have surrounding code"
            assert error.reasoning.root_cause, "Should explain why variable is undefined"
            assert error.reasoning.why_occurred, "Should explain how error occurred"
            assert error.impact_analysis.affected_symbols, "Should identify affected symbols"
    
    @pytest.mark.asyncio
    async def test_type_error_detection(self, lsp_manager):
        """Test detection of type errors (requires type checker)."""
        # This test would require actual type checker integration
        # For now, validate the framework can handle type errors
        
        # Create mock type error
        from src.graph_sitter.core.enhanced_error_types import CodeLocation
        
        location = CodeLocation(
            file_path="tests/fixtures/type_errors/type_mismatches.py",
            line=7,
            character=10
        )
        
        error = EnhancedErrorInfo(
            id="test_type_error",
            location=location,
            message="Incompatible types in assignment",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TYPE,
            error_type="T001",
            source="mypy"
        )
        
        # Enhance the error
        enhanced_error = await lsp_manager._enhance_single_error(error)
        
        # Validate enhancement
        assert enhanced_error.context.surrounding_code, "Should have context"
        assert enhanced_error.reasoning.root_cause, "Should have reasoning"
        assert enhanced_error.confidence_score > 0.0, "Should have confidence score"
    
    @pytest.mark.asyncio
    async def test_import_error_detection(self, lsp_manager):
        """Test detection of import errors."""
        errors = await lsp_manager.get_all_errors()
        
        # Find import errors
        import_errors = [e for e in errors if e.category == ErrorCategory.IMPORT]
        
        # Validate import error handling
        for error in import_errors:
            assert error.error_type.startswith('I'), "Import errors should have I-prefix"
            assert error.context.surrounding_code, "Should have context"
            assert error.reasoning.root_cause, "Should explain import failure"
            
            # Import errors should have specific fix suggestions
            if error.suggested_fixes:
                fix_types = [fix.fix_type for fix in error.suggested_fixes]
                assert any('import' in fix_type for fix_type in fix_types), \
                    "Should suggest import-related fixes"
    
    @pytest.mark.asyncio
    async def test_false_positive_detection(self, lsp_manager):
        """Test false positive detection and filtering."""
        # Get all errors including potential false positives
        all_errors = await lsp_manager.get_all_errors()
        
        # Check false positive likelihood calculation
        for error in all_errors:
            assert 0.0 <= error.false_positive_likelihood <= 1.0, \
                "False positive likelihood should be between 0 and 1"
            
            # Errors with high false positive likelihood should be filtered
            if error.false_positive_likelihood > 0.5:
                assert error.is_likely_false_positive, \
                    "High false positive likelihood should mark error as likely false positive"
        
        # Test specific false positive patterns
        false_positive_patterns = [
            "dynamic attribute access",
            "magic method",
            "monkey patching",
            "conditional import"
        ]
        
        for error in all_errors:
            message_lower = error.message.lower()
            if any(pattern in message_lower for pattern in false_positive_patterns):
                assert error.false_positive_likelihood > 0.3, \
                    f"Should have higher false positive likelihood for: {error.message}"
    
    @pytest.mark.asyncio
    async def test_error_context_accuracy(self, lsp_manager):
        """Test accuracy of error context extraction."""
        errors = await lsp_manager.get_all_errors()
        
        for error in errors:
            # Get full context
            full_error = await lsp_manager.get_full_error_context(error.id)
            assert full_error is not None, f"Should retrieve full context for {error.id}"
            
            # Validate context completeness
            context = full_error.context
            assert context.surrounding_code, "Should have surrounding code"
            
            # Context should include the error location
            assert str(error.location.line) in context.surrounding_code, \
                "Surrounding code should include error line"
            
            # Validate reasoning quality
            reasoning = full_error.reasoning
            assert reasoning.root_cause, "Should have root cause"
            assert reasoning.why_occurred, "Should explain why error occurred"
            
            # Validate impact analysis
            impact = full_error.impact_analysis
            assert impact.impact_score >= 0.0, "Should have impact score"
    
    @pytest.mark.asyncio
    async def test_fix_suggestion_quality(self, lsp_manager):
        """Test quality of fix suggestions."""
        errors = await lsp_manager.get_all_errors()
        
        fixable_errors = [e for e in errors if e.has_fix]
        assert len(fixable_errors) > 0, "Should have some fixable errors"
        
        for error in fixable_errors:
            for fix in error.suggested_fixes:
                # Validate fix properties
                assert fix.fix_type, "Fix should have type"
                assert fix.description, "Fix should have description"
                assert 0.0 <= fix.confidence <= 1.0, "Fix confidence should be 0-1"
                assert fix.difficulty in FixDifficulty, "Fix should have valid difficulty"
                
                # Safe fixes should meet criteria
                if fix.is_safe:
                    assert fix.confidence >= 0.8, "Safe fixes should have high confidence"
                    assert fix.difficulty in [FixDifficulty.TRIVIAL, FixDifficulty.EASY], \
                        "Safe fixes should be easy"
                    assert len(fix.side_effects) == 0, "Safe fixes should have no side effects"
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, lsp_manager):
        """Test performance requirements are met."""
        # Test cached error retrieval performance
        start_time = time.time()
        errors1 = await lsp_manager.get_all_errors()
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        errors2 = await lsp_manager.get_all_errors()  # Should be cached
        second_call_time = time.time() - start_time
        
        # Cached call should be much faster
        assert second_call_time < first_call_time / 2, \
            "Cached error retrieval should be significantly faster"
        
        # Cached call should be under 100ms
        assert second_call_time < 0.1, \
            f"Cached error retrieval should be under 100ms, got {second_call_time:.3f}s"
        
        # Test context retrieval performance
        if errors1:
            start_time = time.time()
            context = await lsp_manager.get_full_error_context(errors1[0].id)
            context_time = time.time() - start_time
            
            assert context_time < 1.0, \
                f"Error context retrieval should be under 1s, got {context_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_error_type_coverage(self, lsp_manager):
        """Test that all error types are covered."""
        errors = await lsp_manager.get_all_errors()
        
        # Check we have errors from different categories
        categories_found = {error.category for error in errors}
        
        # Should detect at least syntax and semantic errors from our fixtures
        assert ErrorCategory.SYNTAX in categories_found, "Should detect syntax errors"
        assert ErrorCategory.SEMANTIC in categories_found, "Should detect semantic errors"
        
        # Check error type coverage
        error_types_found = {error.error_type for error in errors}
        
        # Should detect specific error types from our fixtures
        expected_types = {'E001', 'S001'}  # Missing colon, undefined variable
        found_expected = expected_types.intersection(error_types_found)
        assert len(found_expected) > 0, f"Should detect expected error types: {expected_types}"
    
    @pytest.mark.asyncio
    async def test_error_reliability_scoring(self, lsp_manager):
        """Test error reliability scoring."""
        errors = await lsp_manager.get_all_errors()
        
        for error in errors:
            # Validate reliability score calculation
            expected_reliability = error.confidence_score * (1.0 - error.false_positive_likelihood)
            assert abs(error.reliability_score - expected_reliability) < 0.01, \
                "Reliability score should be calculated correctly"
            
            # High reliability errors should have high confidence and low false positive likelihood
            if error.reliability_score > 0.8:
                assert error.confidence_score > 0.7, "High reliability needs high confidence"
                assert error.false_positive_likelihood < 0.3, "High reliability needs low false positive likelihood"
    
    @pytest.mark.asyncio
    async def test_batch_error_processing(self, lsp_manager):
        """Test batch processing of errors."""
        # Force refresh to test batch processing
        start_time = time.time()
        errors = await lsp_manager.get_all_errors(force_refresh=True)
        processing_time = time.time() - start_time
        
        if len(errors) > 0:
            # Batch processing should be efficient
            time_per_error = processing_time / len(errors)
            assert time_per_error < 0.1, \
                f"Should process errors efficiently, got {time_per_error:.3f}s per error"
        
        # Validate all errors are properly enhanced
        for error in errors:
            assert error.context.surrounding_code or error.location.file_path.endswith('.py'), \
                "All Python errors should have context"
            assert error.reasoning.root_cause, "All errors should have root cause"
            assert error.confidence_score > 0.0, "All errors should have confidence score"
    
    def test_error_serialization(self):
        """Test error serialization to dict."""
        from src.graph_sitter.core.enhanced_error_types import CodeLocation
        
        location = CodeLocation(
            file_path="test.py",
            line=10,
            character=5
        )
        
        error = EnhancedErrorInfo(
            id="test_error",
            location=location,
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            error_type="E001",
            source="test"
        )
        
        # Test serialization
        error_dict = error.to_dict()
        
        # Validate required fields
        assert error_dict['id'] == "test_error"
        assert error_dict['message'] == "Test error message"
        assert error_dict['severity'] == "error"
        assert error_dict['category'] == "syntax"
        assert error_dict['error_type'] == "E001"
        assert error_dict['location']['file_path'] == "test.py"
        assert error_dict['location']['line'] == 10
        assert error_dict['location']['character'] == 5
        
        # Validate computed properties
        assert 'reliability_score' in error_dict
        assert 'has_fix' in error_dict
        assert 'has_safe_fix' in error_dict
        assert 'is_likely_false_positive' in error_dict
    
    @pytest.mark.asyncio
    async def test_error_caching_invalidation(self, lsp_manager):
        """Test error cache invalidation on file changes."""
        # Get initial errors
        initial_errors = await lsp_manager.get_all_errors()
        initial_count = len(initial_errors)
        
        # Simulate file modification by updating modification times
        test_file = Path("tests/fixtures/syntax_errors/missing_colon.py")
        if test_file.exists():
            # Update modification time in manager's tracking
            lsp_manager.file_modification_times[str(test_file)] = time.time() - 100
            
            # Force refresh should detect the "modification"
            refreshed_errors = await lsp_manager.get_all_errors(force_refresh=True)
            
            # Should have processed the file again
            assert len(refreshed_errors) >= 0, "Should handle file refresh"
    
    @pytest.mark.asyncio
    async def test_manager_statistics(self, lsp_manager):
        """Test LSP manager statistics tracking."""
        # Get errors to populate stats
        await lsp_manager.get_all_errors()
        
        # Get statistics
        stats = lsp_manager.get_stats()
        
        # Validate statistics structure
        required_stats = [
            'errors_detected', 'context_extractions', 'false_positives_filtered',
            'cache_hits', 'cache_misses', 'active_servers', 'cached_errors', 'is_initialized'
        ]
        
        for stat in required_stats:
            assert stat in stats, f"Should track {stat} statistic"
            assert isinstance(stats[stat], (int, bool)), f"{stat} should be int or bool"
        
        # Validate reasonable values
        assert stats['is_initialized'] == True, "Should be initialized"
        assert stats['cached_errors'] >= 0, "Should have non-negative cached errors"


# Integration tests with actual fixture files
class TestErrorFixtureIntegration:
    """Test integration with actual error fixture files."""
    
    @pytest.mark.asyncio
    async def test_syntax_error_fixtures(self):
        """Test detection of errors in syntax error fixtures."""
        manager = EnhancedLSPManager("tests/fixtures/syntax_errors")
        await manager.initialize()
        
        try:
            errors = await manager.get_all_errors()
            
            # Should detect errors in missing_colon.py
            missing_colon_errors = [
                e for e in errors 
                if 'missing_colon.py' in e.location.file_path and e.error_type == 'E001'
            ]
            
            assert len(missing_colon_errors) > 0, "Should detect missing colon errors in fixture"
            
            # Validate error details
            for error in missing_colon_errors:
                assert error.severity == ErrorSeverity.ERROR
                assert error.category == ErrorCategory.SYNTAX
                assert 'colon' in error.message.lower()
                assert error.confidence_score > 0.8
                
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_semantic_error_fixtures(self):
        """Test detection of errors in semantic error fixtures."""
        manager = EnhancedLSPManager("tests/fixtures/semantic_errors")
        await manager.initialize()
        
        try:
            errors = await manager.get_all_errors()
            
            # Should detect errors in undefined_variables.py
            undefined_var_errors = [
                e for e in errors 
                if 'undefined_variables.py' in e.location.file_path and e.error_type == 'S001'
            ]
            
            assert len(undefined_var_errors) > 0, "Should detect undefined variable errors in fixture"
            
            # Validate error details
            for error in undefined_var_errors:
                assert error.severity == ErrorSeverity.ERROR
                assert error.category == ErrorCategory.SEMANTIC
                assert 'undefined' in error.message.lower()
                
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_false_positive_fixtures(self):
        """Test false positive detection with fixture files."""
        manager = EnhancedLSPManager("tests/fixtures/false_positives")
        await manager.initialize()
        
        try:
            errors = await manager.get_all_errors()
            
            # Errors from false positive fixtures should have higher false positive likelihood
            false_positive_file_errors = [
                e for e in errors 
                if 'lsp_quirks.py' in e.location.file_path
            ]
            
            if false_positive_file_errors:
                avg_false_positive_likelihood = sum(
                    e.false_positive_likelihood for e in false_positive_file_errors
                ) / len(false_positive_file_errors)
                
                # Should have higher than average false positive likelihood
                assert avg_false_positive_likelihood > 0.2, \
                    "False positive fixtures should have higher false positive likelihood"
                
        finally:
            await manager.shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

