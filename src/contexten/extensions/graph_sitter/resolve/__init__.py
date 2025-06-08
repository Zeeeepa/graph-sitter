"""
Resolve Extension for Graph-sitter

Provides symbol resolution functionality including:
- Import relationship analysis
- Symbol resolution and tracking
- Dependency loop detection
- External module resolution
"""

from .resolver import Resolve

__all__ = ['Resolve']

