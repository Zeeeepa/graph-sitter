"""
LSP Extensions for Graph-Sitter

This package provides comprehensive error analysis capabilities for graph-sitter
by leveraging existing infrastructure without redundant type definitions.
"""

# Import comprehensive error analysis
from .error_analysis import (
    ComprehensiveErrorAnalyzer,
    analyze_codebase_errors,
    get_repo_error_analysis,
)

__all__ = [
    "ComprehensiveErrorAnalyzer",
    "analyze_codebase_errors", 
    "get_repo_error_analysis",
]
