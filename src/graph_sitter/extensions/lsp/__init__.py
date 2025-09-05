"""
LSP (Language Server Protocol) integration for graph-sitter.
This module provides enhanced functionality with Serena integration.
This module provides LSP infrastructure for advanced code intelligence features.
"""

from .codebase import *
from .serena_bridge import SerenaLSPBridge, ErrorInfo

__all__ = ["SerenaLSPBridge", "ErrorInfo"]
