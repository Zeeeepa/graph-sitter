"""
Tree-sitter Query Patterns

Standardized query patterns for code analysis using official tree-sitter Query syntax.
"""

from .python_queries import PythonQueries
from .javascript_queries import JavaScriptQueries
from .common_queries import CommonQueries

__all__ = ['PythonQueries', 'JavaScriptQueries', 'CommonQueries']

