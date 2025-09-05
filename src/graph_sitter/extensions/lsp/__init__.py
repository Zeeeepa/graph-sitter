"""
LSP Extensions for Graph-Sitter

This package provides Language Server Protocol (LSP) integration and
comprehensive error analysis capabilities for graph-sitter using
official Serena and SolidLSP components.
"""

# Import Serena LSP bridge and analysis
from .serena_bridge import (
    SerenaLSPBridge,
    SerenaErrorInfo,
    RuntimeContext,
    RuntimeErrorCollector,
    create_serena_bridge,
    get_enhanced_diagnostics,
)

from .serena_analysis import (
    GitHubRepositoryAnalyzer,
    RepositoryInfo,
    AnalysisResult,
    analyze_github_repository,
    get_repository_error_summary,
    analyze_multiple_repositories,
)

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
    # Serena LSP Integration
    "SerenaLSPBridge",
    "SerenaErrorInfo",
    "RuntimeContext",
    "RuntimeErrorCollector",
    "create_serena_bridge",
    "get_enhanced_diagnostics",
    
    # GitHub Repository Analysis
    "GitHubRepositoryAnalyzer",
    "RepositoryInfo",
    "AnalysisResult",
    "analyze_github_repository",
    "get_repository_error_summary",
    "analyze_multiple_repositories",
    
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
