"""Pytest configuration and fixtures for graph-sitter tests."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

@pytest.fixture
def sample_codebase():
    """Fixture providing a sample codebase for testing."""
    from graph_sitter import Codebase
    # Use a small subset for testing
    return Codebase("./src")

@pytest.fixture
def graph_sitter_adapter(sample_codebase):
    """Fixture providing GraphSitterAdapter."""
    from src.graph_sitter_adapter import GraphSitterAdapter
    return GraphSitterAdapter(sample_codebase)

@pytest.fixture
def autogenlib_adapter(sample_codebase, graph_sitter_adapter):
    """Fixture providing AutoGenLibAdapter."""
    from src.autogenlib_adapter import AutoGenLibAdapter
    return AutoGenLibAdapter(sample_codebase, graph_sitter_adapter)

@pytest.fixture
def analysis_orchestrator():
    """Fixture providing AnalysisOrchestrator."""
    from src.lib_analysis import AnalysisOrchestrator
    return AnalysisOrchestrator()

@pytest.fixture
def sample_error():
    """Fixture providing a sample AnalysisError."""
    from src.analysis_utils import AnalysisError
    return AnalysisError(
        file_path="src/test_file.py",
        line=10,
        column=5,
        error_type="syntax_error",
        severity="error",
        message="Test error message",
        tool_source="ruff",
        category="syntax"
    )
