"""
Graph-Sitter System: Comprehensive Code Analysis Framework

This package provides a modular, extensible framework for code analysis,
parsing, and manipulation using Graph-Sitter technology.

Key Components:
- Core: Fundamental parsing and graph construction
- Modules: Specialized analysis modules (contexten, codegen integration)
- Integrations: External service integrations
- Utils: Utility functions and helpers

Author: Codegen AI
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Codegen AI"

from .core.codebase_analyzer import CodebaseAnalyzer
from .core.graph_builder import GraphBuilder
from .core.metrics_calculator import MetricsCalculator

__all__ = [
    "CodebaseAnalyzer",
    "GraphBuilder", 
    "MetricsCalculator"
]

