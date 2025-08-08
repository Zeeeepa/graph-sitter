"""
Unified Error Handling for Graph-Sitter

This module provides a unified interface for all error handling capabilities
in graph-sitter, including LSP diagnostics, runtime error collection,
comprehensive analysis, and Serena integration.
"""

# Import core graph-sitter functionality
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, 
    get_file_summary, 
    get_class_summary, 
    get_function_summary, 
    get_symbol_summary
)

# Import all Serena analysis features
from graph_sitter.extensions.lsp.serena_analysis import *

# Import all bridge functionality for backward compatibility
from graph_sitter.extensions.lsp.serena_bridge import (
    SerenaErrorInfo,
    SerenaLSPBridge,
    ErrorInfo,  # Backward compatibility
    TransactionAwareLSPManager,
    create_serena_bridge,
    get_enhanced_diagnostics,
    get_comprehensive_analysis,
    start_runtime_error_collection,
    stop_runtime_error_collection,
    get_lsp_manager,
    shutdown_all_lsp_managers,
)

# Re-export everything for convenience
__all__ = [
    # Core graph-sitter
    "Codebase",
    "get_codebase_summary",
    "get_file_summary", 
    "get_class_summary",
    "get_function_summary",
    "get_symbol_summary",
    
    # Serena Bridge
    "SerenaErrorInfo",
    "SerenaLSPBridge", 
    "ErrorInfo",
    "TransactionAwareLSPManager",
    "create_serena_bridge",
    "get_enhanced_diagnostics",
    "get_comprehensive_analysis",
    "start_runtime_error_collection",
    "stop_runtime_error_collection",
    "get_lsp_manager",
    "shutdown_all_lsp_managers",
    
    # All exports from serena_analysis (imported via *)
    # This includes:
    # - RuntimeErrorCollector, RuntimeError, RuntimeContext
    # - GitHubRepositoryAnalyzer, RepositoryInfo, AnalysisResult
    # - SerenaCodebaseAnalyzer, AnalysisMetrics, ComprehensiveAnalysisResult
    # - analyze_codebase_comprehensive, analyze_github_repository_comprehensive
    # - get_repository_quality_report, analyze_github_repository
    # - get_repository_error_summary, analyze_multiple_repositories
]


# Convenience functions for unified error handling
def get_all_errors(codebase_path: str, include_runtime: bool = True) -> dict:
    """
    Get all errors for a codebase using unified error handling.
    
    Args:
        codebase_path: Path to the codebase
        include_runtime: Whether to include runtime errors
        
    Returns:
        Dictionary with comprehensive error information
    """
    try:
        # Create Serena bridge for comprehensive analysis
        bridge = SerenaLSPBridge(codebase_path, enable_runtime_collection=include_runtime)
        
        # Get enhanced diagnostics
        diagnostics = bridge.get_enhanced_diagnostics()
        
        # Get runtime errors if requested
        runtime_errors = []
        if include_runtime:
            runtime_errors = bridge.get_runtime_errors()
        
        # Get codebase summary for context
        codebase = Codebase(codebase_path)
        summary = get_codebase_summary(codebase)
        
        return {
            'codebase_summary': summary,
            'diagnostics': diagnostics,
            'runtime_errors': [error.to_dict() for error in runtime_errors],
            'bridge_status': bridge.get_status()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'codebase_summary': None,
            'diagnostics': {'total_count': 0, 'diagnostics': []},
            'runtime_errors': [],
            'bridge_status': {'initialized': False}
        }


def analyze_codebase_errors(codebase_path: str, **kwargs) -> dict:
    """
    Analyze codebase errors with comprehensive reporting.
    
    Args:
        codebase_path: Path to the codebase
        **kwargs: Additional arguments for analysis
        
    Returns:
        Comprehensive error analysis results
    """
    try:
        # Use the comprehensive analyzer
        analyzer = SerenaCodebaseAnalyzer(codebase_path)
        result = analyzer.analyze_comprehensive(**kwargs)
        
        # Add codebase context
        codebase = Codebase(codebase_path)
        codebase_summary = get_codebase_summary(codebase)
        
        return {
            'codebase_summary': codebase_summary,
            'analysis_result': result.to_dict() if hasattr(result, 'to_dict') else result,
            'analyzer_status': analyzer.get_status() if hasattr(analyzer, 'get_status') else {}
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'codebase_summary': None,
            'analysis_result': None,
            'analyzer_status': {}
        }


def get_file_errors(codebase_path: str, file_path: str, include_runtime: bool = True) -> dict:
    """
    Get errors for a specific file with comprehensive analysis.
    
    Args:
        codebase_path: Path to the codebase
        file_path: Path to the specific file
        include_runtime: Whether to include runtime errors
        
    Returns:
        File-specific error information
    """
    try:
        # Create Serena bridge
        bridge = SerenaLSPBridge(codebase_path, enable_runtime_collection=include_runtime)
        
        # Get file diagnostics
        file_diagnostics = bridge.get_file_diagnostics(file_path)
        
        # Get file summary for context
        codebase = Codebase(codebase_path)
        file_summary = get_file_summary(codebase, file_path)
        
        return {
            'file_path': file_path,
            'file_summary': file_summary,
            'diagnostics': [diag.to_dict() for diag in file_diagnostics],
            'error_count': len([d for d in file_diagnostics if d.is_error]),
            'warning_count': len([d for d in file_diagnostics if d.is_warning]),
            'hint_count': len([d for d in file_diagnostics if d.is_hint])
        }
        
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e),
            'file_summary': None,
            'diagnostics': [],
            'error_count': 0,
            'warning_count': 0,
            'hint_count': 0
        }


def start_comprehensive_error_monitoring(codebase_path: str) -> dict:
    """
    Start comprehensive error monitoring for a codebase.
    
    Args:
        codebase_path: Path to the codebase
        
    Returns:
        Status information about started monitoring
    """
    try:
        # Start runtime error collection
        collector = start_runtime_error_collection(codebase_path)
        
        # Get LSP manager for transaction-aware monitoring
        manager = get_lsp_manager(codebase_path, enable_lsp=True)
        
        return {
            'monitoring_started': True,
            'runtime_collection_active': collector.is_active if hasattr(collector, 'is_active') else True,
            'lsp_manager_status': manager.get_lsp_status(),
            'codebase_path': codebase_path
        }
        
    except Exception as e:
        return {
            'monitoring_started': False,
            'error': str(e),
            'codebase_path': codebase_path
        }


def stop_comprehensive_error_monitoring(codebase_path: str) -> dict:
    """
    Stop comprehensive error monitoring for a codebase.
    
    Args:
        codebase_path: Path to the codebase
        
    Returns:
        Status information about stopped monitoring
    """
    try:
        # Stop runtime error collection
        stop_runtime_error_collection(codebase_path)
        
        # Shutdown all LSP managers
        shutdown_all_lsp_managers()
        
        return {
            'monitoring_stopped': True,
            'codebase_path': codebase_path
        }
        
    except Exception as e:
        return {
            'monitoring_stopped': False,
            'error': str(e),
            'codebase_path': codebase_path
        }


# Backward compatibility aliases
RuntimeErrorCollector = RuntimeErrorCollector  # From serena_analysis import
RuntimeError = RuntimeError  # From serena_analysis import
get_runtime_collector = start_runtime_error_collection
