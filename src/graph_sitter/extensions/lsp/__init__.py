"""
LSP (Language Server Protocol) integration for graph-sitter.

This module provides LSP infrastructure for advanced code intelligence features.
"""

from .serena_bridge import SerenaLSPBridge, ErrorInfo

__all__ = ['SerenaLSPBridge', 'ErrorInfo']

