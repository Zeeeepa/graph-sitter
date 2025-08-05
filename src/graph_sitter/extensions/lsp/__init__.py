"""
LSP Extensions for Graph-Sitter

This package provides Language Server Protocol (LSP) integration and
comprehensive error analysis capabilities for graph-sitter.
"""

# Import comprehensive error analysis
from .error_analysis import (
    ErrorSeverity,
    ErrorCategory,
    ErrorLocation,
    ErrorInfo,
    ComprehensiveErrorList,
    ComprehensiveErrorAnalyzer,
    analyze_codebase_errors,
    get_repo_error_analysis,
)

__all__ = [
    # Error Analysis
    "ErrorSeverity",
    "ErrorCategory", 
    "ErrorLocation",
    "ErrorInfo",
    "ComprehensiveErrorList",
    "ComprehensiveErrorAnalyzer",
    "analyze_codebase_errors",
    "get_repo_error_analysis",
]
