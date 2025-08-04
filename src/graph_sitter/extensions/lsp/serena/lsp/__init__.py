"""
LSP (Language Server Protocol) Integration for Serena Analysis

This module provides LSP client capabilities to communicate with Serena language servers
for real-time code analysis, error detection, and comprehensive code intelligence.
"""

from .client import (
    SerenaLSPClient,
    ConnectionType,
    LSPError,
    LSPConnectionError,
    LSPTimeoutError
)

from .server_manager import (
    SerenaServerManager,
    ServerConfig,
    ServerStatus
)

from .error_retrieval import (
    ErrorRetriever,
    CodeError,
    ErrorSeverity,
    ErrorCategory,
    ErrorLocation,
    ComprehensiveErrorList
)

from .diagnostics import (
    DiagnosticProcessor,
    DiagnosticFilter,
    DiagnosticAggregator,
    DiagnosticStats,
    RealTimeDiagnostics
)

from .protocol import (
    LSPMessage,
    LSPRequest,
    LSPResponse,
    LSPNotification,
    ProtocolHandler
)

__all__ = [
    # Core LSP client
    'SerenaLSPClient',
    'ConnectionType',
    'LSPError',
    'LSPConnectionError', 
    'LSPTimeoutError',
    
    # Server management
    'SerenaServerManager',
    'ServerConfig',
    'ServerStatus',
    
    # Error retrieval
    'ErrorRetriever',
    'CodeError',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorLocation',
    'ComprehensiveErrorList',
    
    # Diagnostics
    'DiagnosticProcessor',
    'DiagnosticFilter',
    'DiagnosticAggregator',
    'DiagnosticStats',
    'RealTimeDiagnostics',
    
    # Protocol handling
    'LSPMessage',
    'LSPRequest',
    'LSPResponse',
    'LSPNotification',
    'ProtocolHandler'
]
