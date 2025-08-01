"""
LSP (Language Server Protocol) integration for graph-sitter.

This module provides LSP infrastructure for advanced code intelligence features
including the consolidated Serena extension.
"""

from .serena_bridge import SerenaLSPBridge, ErrorInfo
from .diagnostics import add_diagnostic_capabilities

# Import Serena components from the consolidated location
try:
    from .serena import (
        SerenaCore,
        SerenaConfig,
        SerenaCapability,
        RefactoringType
    )
    SERENA_AVAILABLE = True
except ImportError:
    SERENA_AVAILABLE = False

__all__ = [
    'SerenaLSPBridge', 
    'ErrorInfo',
    'add_diagnostic_capabilities'
]

if SERENA_AVAILABLE:
    __all__.extend([
        'SerenaCore',
        'SerenaConfig', 
        'SerenaCapability',
        'RefactoringType'
    ])
