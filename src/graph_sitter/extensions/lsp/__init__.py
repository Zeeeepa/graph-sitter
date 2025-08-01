"""
LSP (Language Server Protocol) integration for graph-sitter.

This module provides LSP infrastructure for advanced code intelligence features.
"""

from .serena_bridge import SerenaLSPBridge, ErrorInfo
from .protocol.lsp_types import DiagnosticSeverity, CompletionItemKind, Position, Range, Diagnostic
from .language_servers.base import BaseLanguageServer
from .transaction_manager import TransactionAwareLSPManager, get_lsp_manager

# Import missing types from Serena (temporary until consolidation)
try:
    from ..serena.lsp.diagnostics import DiagnosticStats
    from ..serena.lsp.client import ConnectionType
except ImportError:
    # Fallback definitions
    class DiagnosticStats:
        def __init__(self):
            self.total_errors = 0
            self.total_warnings = 0
    
    class ConnectionType:
        STDIO = "stdio"
        TCP = "tcp"
        WEBSOCKET = "websocket"
        HTTP = "http"

__all__ = [
    'SerenaLSPBridge', 
    'ErrorInfo',
    'DiagnosticSeverity',
    'CompletionItemKind', 
    'Position',
    'Range',
    'Diagnostic',
    'BaseLanguageServer',
    'TransactionAwareLSPManager',
    'get_lsp_manager',
    'DiagnosticStats',
    'ConnectionType'
]
