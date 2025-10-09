"""Integration tests for complete workflows."""

import pytest
from pathlib import Path


class TestIntegrationWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_full_analysis_workflow(self, graph_sitter_adapter, analysis_orchestrator):
        """Test complete analysis workflow."""
        # 1. Get codebase overview
        overview = graph_sitter_adapter.get_codebase_overview()
        assert overview['files_count'] > 0
        
        # 2. Analyze a specific file
        file_details = graph_sitter_adapter.get_file_details("src/analysis_utils.py")
        assert isinstance(file_details, dict)
        
        # 3. Check for dead code
        dead_code = graph_sitter_adapter.find_dead_code()
        assert isinstance(dead_code, list)
    
    def test_error_resolution_workflow(self, autogenlib_adapter):
        """Test error resolution workflow."""
        from src.analysis_utils import AnalysisError
        
        # 1. Create sample error
        error = AnalysisError(
            file_path="src/test.py",
            line=10,
            column=5,
            error_type="type_error",
            severity="error",
            message="Test error",
            tool_source="mypy",
            category="type_checking"
        )
        
        # 2. Get error context
        context = autogenlib_adapter.get_error_context(error)
        assert 'file_path' in context or 'error' in context
        
        # 3. Generate fix strategy
        strategy = autogenlib_adapter.generate_fix_strategy([error])
        assert 'total_errors' in strategy
        assert strategy['total_errors'] == 1
    
    def test_batch_analysis_workflow(self, autogenlib_adapter):
        """Test batch analysis workflow."""
        from src.analysis_utils import AnalysisError
        
        # Create multiple errors
        errors = [
            AnalysisError(
                file_path=f"src/file{i}.py",
                line=i*10,
                column=0,
                error_type="error",
                severity="error",
                message=f"Error {i}",
                tool_source="ruff",
                category="syntax"
            )
            for i in range(5)
        ]
        
        # 1. Generate comprehensive context
        context = autogenlib_adapter.generate_comprehensive_context(errors)
        assert context['error_summary']['total'] == 5
        
        # 2. Batch resolve
        results = autogenlib_adapter.batch_resolve(errors, batch_size=2)
        assert len(results) == 5
    
    def test_import_analysis_workflow(self, graph_sitter_adapter):
        """Test import analysis workflow."""
        # 1. Get import graph
        import_graph = graph_sitter_adapter.get_import_graph()
        assert isinstance(import_graph, dict)
        
        # 2. Find circular dependencies
        circular = graph_sitter_adapter.find_circular_dependencies()
        assert isinstance(circular, list)
    
    def test_complexity_analysis_workflow(self, graph_sitter_adapter):
        """Test complexity analysis workflow."""
        # Get overview
        overview = graph_sitter_adapter.get_codebase_overview()
        
        # Try to analyze complexity of first function found
        # (will gracefully handle if no functions exist)
        if overview['functions_count'] > 0:
            # This is expected to return result or error
            result = graph_sitter_adapter.analyze_complexity("some_function")
            assert isinstance(result, dict)


class TestAdapterIntegration:
    """Test integration between different adapters."""
    
    def test_graph_sitter_autogenlib_integration(
        self, 
        graph_sitter_adapter,
        autogenlib_adapter
    ):
        """Test GraphSitter and AutoGenLib adapters work together."""
        from src.analysis_utils import AnalysisError
        
        # 1. Get codebase overview from GraphSitter
        overview = graph_sitter_adapter.get_codebase_overview()
        
        # 2. Create error
        error = AnalysisError(
            file_path="src/analysis_utils.py",
            line=10,
            column=0,
            error_type="error",
            severity="error",
            message="Test",
            tool_source="test",
            category="test"
        )
        
        # 3. Get context (should use GraphSitter data)
        context = autogenlib_adapter.get_error_context(error)
        
        # Should have codebase overview from GraphSitter
        if 'codebase_overview' in context:
            assert 'files_count' in context['codebase_overview']
    
    def test_orchestrator_integration(self, analysis_orchestrator):
        """Test analysis orchestrator integration."""
        # Get available tools
        tools = analysis_orchestrator.get_available_tools()
        assert isinstance(tools, list)
        
        # Verify tools are registered
        assert len(tools) > 0


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""
    
    def test_new_project_analysis_scenario(self, graph_sitter_adapter):
        """Simulate analyzing a new project."""
        # Step 1: Get overview
        overview = graph_sitter_adapter.get_codebase_overview()
        assert 'files_count' in overview
        
        # Step 2: Check for dead code
        dead_code = graph_sitter_adapter.find_dead_code()
        assert isinstance(dead_code, list)
        
        # Step 3: Get import graph
        imports = graph_sitter_adapter.get_import_graph()
        assert isinstance(imports, dict)
        
        # Step 4: Check for circular dependencies
        circular = graph_sitter_adapter.find_circular_dependencies()
        assert isinstance(circular, list)
    
    def test_error_fixing_scenario(self, autogenlib_adapter):
        """Simulate finding and fixing errors."""
        from src.analysis_utils import AnalysisError
        
        # Simulate multiple errors discovered
        errors = [
            AnalysisError(
                file_path="src/main.py",
                line=10,
                column=0,
                error_type="import_error",
                severity="error",
                message="Module not found",
                tool_source="mypy",
                category="import"
            ),
            AnalysisError(
                file_path="src/main.py",
                line=20,
                column=5,
                error_type="type_error",
                severity="error",
                message="Type mismatch",
                tool_source="mypy",
                category="type_checking"
            )
        ]
        
        # Generate strategy
        strategy = autogenlib_adapter.generate_fix_strategy(errors)
        assert strategy['total_errors'] == 2
        
        # Generate comprehensive context
        context = autogenlib_adapter.generate_comprehensive_context(errors)
        assert 'suggested_approach' in context
    
    def test_refactoring_scenario(self, graph_sitter_adapter):
        """Simulate code refactoring analysis."""
        # Find potentially unused code
        dead_code = graph_sitter_adapter.find_dead_code()
        
        # Analyze file structure
        overview = graph_sitter_adapter.get_codebase_overview()
        
        # Check dependencies
        if overview['files_count'] > 0:
            import_graph = graph_sitter_adapter.get_import_graph()
            assert isinstance(import_graph, dict)

