"""
LSP Extensions for Graph-Sitter

This package provides Language Server Protocol (LSP) integration and
comprehensive error analysis capabilities for graph-sitter, including
enhanced Serena integration and runtime error collection.
"""

# Import enhanced Serena bridge
from .serena_bridge import (
    SerenaErrorInfo,
    SerenaLSPBridge,
    ErrorInfo,  # Keep backward compatibility
    create_serena_bridge,
    get_enhanced_diagnostics,
    get_comprehensive_analysis,
    start_runtime_error_collection,
    stop_runtime_error_collection,
)

# Import comprehensive analysis
from .serena_analysis import (
    RepositoryInfo,
    AnalysisMetrics,
    ComprehensiveAnalysisResult,
    SerenaCodebaseAnalyzer,
    analyze_codebase_comprehensive,
    analyze_github_repository_comprehensive,
    get_repository_quality_report,
)

# Import transaction manager
from .transaction_manager import (
    TransactionAwareLSPManager,
    get_lsp_manager,
    shutdown_all_lsp_managers,
)

__all__ = [
    # Enhanced Serena Bridge
    "SerenaErrorInfo",
    "SerenaLSPBridge",
    "ErrorInfo",  # Backward compatibility
    "create_serena_bridge",
    "get_enhanced_diagnostics",
    "get_comprehensive_analysis",
    "start_runtime_error_collection",
    "stop_runtime_error_collection",
    
    # Comprehensive Analysis
    "RepositoryInfo",
    "AnalysisMetrics",
    "ComprehensiveAnalysisResult",
    "SerenaCodebaseAnalyzer",
    "analyze_codebase_comprehensive",
    "analyze_github_repository_comprehensive",
    "get_repository_quality_report",
    
    # Transaction Management
    "TransactionAwareLSPManager",
    "get_lsp_manager",
    "shutdown_all_lsp_managers",
]
