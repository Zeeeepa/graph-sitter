"""
Graph-sitter Analysis Module

This module provides comprehensive codebase analysis capabilities including:
- Tree-sitter integration with advanced syntax analysis
- AI-powered code analysis and improvement suggestions
- Interactive visualization with D3.js
- Comprehensive metrics collection
- Dependency tracking and dead code detection
- Import relationship analysis
"""

from .analyzer import CodebaseAnalyzer
from .config.analysis_config import AnalysisConfig
from .core.analysis_engine import AnalysisEngine, AnalysisResult
from .orchestrator import AnalysisOrchestrator

__version__ = "1.0.0"
__all__ = [
    "CodebaseAnalyzer",
    "AnalysisConfig", 
    "AnalysisEngine",
    "AnalysisResult",
    "AnalysisOrchestrator"
]

