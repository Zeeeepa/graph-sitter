"""Unit tests for GraphSitterAdapter."""

import pytest
from src.analysis_utils import AnalysisError


class TestGraphSitterAdapter:
    """Test suite for GraphSitterAdapter."""
    
    def test_initialization(self, graph_sitter_adapter):
        """Test adapter initializes correctly."""
        assert graph_sitter_adapter is not None
        assert graph_sitter_adapter.codebase is not None
        assert hasattr(graph_sitter_adapter, '_cache')
    
    def test_get_codebase_overview(self, graph_sitter_adapter):
        """Test codebase overview generation."""
        overview = graph_sitter_adapter.get_codebase_overview()
        
        assert isinstance(overview, dict)
        assert 'files_count' in overview
        assert 'functions_count' in overview
        assert 'classes_count' in overview
        assert 'symbols_count' in overview
        
        # Verify counts are reasonable
        assert overview['files_count'] > 0
        assert isinstance(overview['files_count'], int)
    
    def test_get_file_details(self, graph_sitter_adapter):
        """Test file details retrieval."""
        # Test with existing file
        details = graph_sitter_adapter.get_file_details("src/analysis_utils.py")
        
        assert isinstance(details, dict)
        if details:  # If file found
            assert 'path' in details or details == {}
    
    def test_find_dead_code(self, graph_sitter_adapter):
        """Test dead code detection."""
        dead_code = graph_sitter_adapter.find_dead_code()
        
        assert isinstance(dead_code, list)
        # All items should be AnalysisError instances
        for item in dead_code:
            assert isinstance(item, AnalysisError)
            assert item.error_type == "dead_code"
            assert item.severity == "warning"
    
    def test_get_import_graph(self, graph_sitter_adapter):
        """Test import graph generation."""
        import_graph = graph_sitter_adapter.get_import_graph()
        
        assert isinstance(import_graph, dict)
        # Verify structure: file -> list of imports
        for file, imports in import_graph.items():
            assert isinstance(file, str)
            assert isinstance(imports, list)
    
    def test_find_circular_dependencies(self, graph_sitter_adapter):
        """Test circular dependency detection."""
        circular = graph_sitter_adapter.find_circular_dependencies()
        
        assert isinstance(circular, list)
        # Each circular dependency should be a list of files
        for cycle in circular:
            assert isinstance(cycle, list)
            assert len(cycle) >= 2  # At least 2 files in a cycle
    
    def test_analyze_complexity(self, graph_sitter_adapter):
        """Test complexity analysis."""
        # This will fail if function doesn't exist, which is expected
        result = graph_sitter_adapter.analyze_complexity("nonexistent_function")
        
        assert isinstance(result, dict)
        # Should return error or complexity data
        assert 'error' in result or 'cyclomatic_complexity' in result
    
    def test_analyze_dependencies(self, graph_sitter_adapter):
        """Test dependency analysis."""
        result = graph_sitter_adapter.analyze_dependencies("src/analysis_utils.py")
        
        assert isinstance(result, dict)
        if result:  # If file found
            assert 'file' in result or 'imports' in result or result == {}
    
    def test_find_usages(self, graph_sitter_adapter):
        """Test symbol usage finding."""
        # Test with a common symbol that likely exists
        usages = graph_sitter_adapter.find_usages("AnalysisError")
        
        assert isinstance(usages, list)
    
    def test_get_function_details(self, graph_sitter_adapter):
        """Test function details retrieval."""
        # This will return empty if function doesn't exist
        details = graph_sitter_adapter.get_function_details("setup_logger")
        
        assert isinstance(details, dict)
    
    def test_get_class_details(self, graph_sitter_adapter):
        """Test class details retrieval."""
        details = graph_sitter_adapter.get_class_details("AnalysisError")
        
        assert isinstance(details, dict)
    
    def test_entrypoint_identification(self, graph_sitter_adapter):
        """Test entrypoint identification helper."""
        entrypoints = graph_sitter_adapter._identify_entrypoints()
        
        assert isinstance(entrypoints, dict)
        assert 'main_functions' in entrypoints
        assert 'test_functions' in entrypoints
        assert 'special_methods' in entrypoints
        
        # Verify structure
        for category, points in entrypoints.items():
            assert isinstance(points, list)
    
    def test_complexity_rating(self, graph_sitter_adapter):
        """Test complexity rating helper."""
        assert graph_sitter_adapter._get_complexity_rating(3) == "low"
        assert graph_sitter_adapter._get_complexity_rating(7) == "moderate"
        assert graph_sitter_adapter._get_complexity_rating(15) == "high"
        assert graph_sitter_adapter._get_complexity_rating(25) == "very_high"


class TestComplexityCalculations:
    """Test complexity calculation methods."""
    
    def test_maintainability_index(self, graph_sitter_adapter):
        """Test maintainability index calculation."""
        # Test various scenarios
        mi_short_simple = graph_sitter_adapter._calculate_maintainability_index(10, 2)
        mi_long_complex = graph_sitter_adapter._calculate_maintainability_index(100, 20)
        
        assert 0 <= mi_short_simple <= 100
        assert 0 <= mi_long_complex <= 100
        # Simple code should have higher MI
        assert mi_short_simple > mi_long_complex

