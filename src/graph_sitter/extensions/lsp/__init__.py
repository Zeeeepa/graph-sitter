"""
LSP (Language Server Protocol) integration for graph-sitter.

This module provides comprehensive LSP infrastructure for advanced code intelligence features,
including comprehensive error analysis, real-time monitoring, and context-aware diagnostics.
"""

from .serena_bridge import (
    SerenaLSPBridge, ErrorInfo, ErrorSeverity, ErrorCategory, 
    ComprehensiveErrorList, ErrorLocation
)
from .serena_analysis import (
    ComprehensiveErrorAnalyzer, ErrorContext, ParameterIssue, FunctionCallInfo,
    analyze_codebase_errors, get_instant_error_context, get_all_codebase_errors_with_context
)

__all__ = [
    # Bridge components
    'SerenaLSPBridge', 'ErrorInfo', 'ErrorSeverity', 'ErrorCategory', 
    'ComprehensiveErrorList', 'ErrorLocation',
    
    # Analysis components
    'ComprehensiveErrorAnalyzer', 'ErrorContext', 'ParameterIssue', 'FunctionCallInfo',
    
    # Convenience functions
    'analyze_codebase_errors', 'get_instant_error_context', 'get_all_codebase_errors_with_context'
]
