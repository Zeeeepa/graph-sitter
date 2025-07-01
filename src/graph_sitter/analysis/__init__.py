"""
Graph-sitter Analysis Module

This module provides comprehensive codebase analysis capabilities including:
- Advanced code metrics (cyclomatic complexity, maintainability index)
- Call graph analysis and traversal
- Dead code detection
- Dependency mapping and import resolution
- Database storage for analysis results
- Integration with graph-sitter.com API patterns
"""

from .database import AnalysisDatabase
from .metrics import CodeMetrics, FunctionMetrics, ClassMetrics
from .call_graph import CallGraphAnalyzer
from .dead_code import DeadCodeDetector
from .dependency_analyzer import DependencyAnalyzer
from .enhanced_analysis import EnhancedCodebaseAnalysis

__all__ = [
    'AnalysisDatabase',
    'CodeMetrics',
    'FunctionMetrics', 
    'ClassMetrics',
    'CallGraphAnalyzer',
    'DeadCodeDetector',
    'DependencyAnalyzer',
    'EnhancedCodebaseAnalysis'
]

