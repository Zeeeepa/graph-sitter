"""
Graph-Sitter Integrations

This module provides integrations with various external libraries and services
to extend graph-sitter's capabilities.
"""

from .grainchain_integration import GrainchainIntegration
from .web_eval_integration import WebEvalIntegration

__all__ = [
    'GrainchainIntegration',
    'WebEvalIntegration',
]

__version__ = "1.0.0"

