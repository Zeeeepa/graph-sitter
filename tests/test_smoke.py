"""Smoke tests - quick validation that core functionality works."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_imports():
    """Test all modules can be imported."""
    # Core utilities
    from src.analysis_utils import AnalysisError, setup_logger, ToolConfig
    assert AnalysisError is not None
    
    # Protocols
    from src.protocols import GraphSitterAnalyzerProtocol
    assert GraphSitterAnalyzerProtocol is not None
    
    # Adapters
    from src.graph_sitter_adapter import GraphSitterAdapter
    from src.autogenlib_adapter import AutoGenLibAdapter
    assert GraphSitterAdapter is not None
    assert AutoGenLibAdapter is not None
    
    # Analysis tools
    from src.lib_analysis import AnalysisOrchestrator, RuffAnalyzer
    assert AnalysisOrchestrator is not None
    assert RuffAnalyzer is not None
    
    print("✅ All imports successful")


def test_basic_instantiation():
    """Test basic object instantiation."""
    from graph_sitter import Codebase
    from src.graph_sitter_adapter import GraphSitterAdapter
    from src.autogenlib_adapter import AutoGenLibAdapter
    from src.lib_analysis import AnalysisOrchestrator
    
    # Create codebase (using minimal path)
    codebase = Codebase("./src")
    assert codebase is not None
    
    # Create adapters
    gs_adapter = GraphSitterAdapter(codebase)
    assert gs_adapter is not None
    
    ai_adapter = AutoGenLibAdapter(codebase, gs_adapter)
    assert ai_adapter is not None
    
    orchestrator = AnalysisOrchestrator()
    assert orchestrator is not None
    
    print("✅ All instantiations successful")


def test_codebase_overview():
    """Test getting codebase overview."""
    from graph_sitter import Codebase
    from src.graph_sitter_adapter import GraphSitterAdapter
    
    codebase = Codebase("./src")
    adapter = GraphSitterAdapter(codebase)
    
    overview = adapter.get_codebase_overview()
    
    assert isinstance(overview, dict)
    assert 'files_count' in overview
    assert overview['files_count'] > 0
    
    print(f"✅ Codebase overview: {overview['files_count']} files")


def test_error_creation():
    """Test creating and working with errors."""
    from src.analysis_utils import AnalysisError
    
    error = AnalysisError(
        file_path="test.py",
        line=10,
        column=5,
        error_type="test_error",
        severity="error",
        message="Test message",
        tool_source="test",
        category="test"
    )
    
    assert error.file_path == "test.py"
    assert error.line == 10
    
    # Test to_dict
    error_dict = error.to_dict()
    assert isinstance(error_dict, dict)
    assert error_dict['file_path'] == "test.py"
    
    print("✅ Error creation and serialization works")


def test_tool_detection():
    """Test tool detection."""
    from src.lib_analysis import AnalysisOrchestrator
    
    orchestrator = AnalysisOrchestrator()
    tools = orchestrator.get_available_tools()
    
    assert isinstance(tools, list)
    print(f"✅ Found {len(tools)} analysis tools")


def test_dead_code_detection():
    """Test dead code detection runs."""
    from graph_sitter import Codebase
    from src.graph_sitter_adapter import GraphSitterAdapter
    
    codebase = Codebase("./src")
    adapter = GraphSitterAdapter(codebase)
    
    # This should run without crashing
    dead_code = adapter.find_dead_code()
    
    assert isinstance(dead_code, list)
    print(f"✅ Dead code detection found {len(dead_code)} potential issues")


def test_import_graph():
    """Test import graph generation."""
    from graph_sitter import Codebase
    from src.graph_sitter_adapter import GraphSitterAdapter
    
    codebase = Codebase("./src")
    adapter = GraphSitterAdapter(codebase)
    
    import_graph = adapter.get_import_graph()
    
    assert isinstance(import_graph, dict)
    print(f"✅ Import graph generated for {len(import_graph)} files")


def test_circular_dependencies():
    """Test circular dependency detection."""
    from graph_sitter import Codebase
    from src.graph_sitter_adapter import GraphSitterAdapter
    
    codebase = Codebase("./src")
    adapter = GraphSitterAdapter(codebase)
    
    circular = adapter.find_circular_dependencies()
    
    assert isinstance(circular, list)
    print(f"✅ Circular dependency check complete ({len(circular)} cycles found)")


def test_context_generation():
    """Test AI context generation."""
    from graph_sitter import Codebase
    from src.graph_sitter_adapter import GraphSitterAdapter
    from src.autogenlib_adapter import AutoGenLibAdapter
    from src.analysis_utils import AnalysisError
    
    codebase = Codebase("./src")
    gs_adapter = GraphSitterAdapter(codebase)
    ai_adapter = AutoGenLibAdapter(codebase, gs_adapter)
    
    error = AnalysisError(
        file_path="test.py",
        line=10,
        column=0,
        error_type="test",
        severity="error",
        message="Test",
        tool_source="test",
        category="test"
    )
    
    context = ai_adapter.get_error_context(error)
    
    assert isinstance(context, dict)
    print("✅ Context generation works")


if __name__ == "__main__":
    """Run smoke tests directly."""
    print("Running smoke tests...")
    print()
    
    try:
        test_imports()
        test_basic_instantiation()
        test_codebase_overview()
        test_error_creation()
        test_tool_detection()
        test_dead_code_detection()
        test_import_graph()
        test_circular_dependencies()
        test_context_generation()
        
        print()
        print("=" * 60)
        print("🎉 ALL SMOKE TESTS PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
