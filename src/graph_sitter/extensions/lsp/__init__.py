"""
LSP Integration for Graph-Sitter

This module provides Language Server Protocol integration for comprehensive
error detection and diagnostic capabilities in graph-sitter codebases.

Adapted from Serena's solidlsp implementation.
"""

from .serena_bridge import ErrorInfo, DiagnosticSeverity
from .transaction_manager import TransactionAwareLSPManager, get_lsp_manager

__all__ = [
    'ErrorInfo',
    'DiagnosticSeverity', 
    'TransactionAwareLSPManager',
    'get_lsp_manager'
]

