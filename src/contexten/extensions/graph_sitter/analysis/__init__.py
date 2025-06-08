"""
🚀 UNIFIED ANALYSIS MODULE 🚀

Consolidated codebase analysis using official tree-sitter patterns and methods.
This module provides a unified interface for all analysis operations with proper
tree-sitter integration and eliminated legacy technical debt.

Key Features:
- Official tree-sitter API integration (TSParser → TSLanguage → TSTree → TSNode)
- Standardized query patterns using tree-sitter Query objects
- Consolidated analysis engine with proper error handling
- Performance-optimized tree traversal using TreeCursor
- Field-based node access using official methods
- Proper dependency management (no more try/catch patterns)

Main Classes:
- UnifiedAnalyzer: Core analysis engine using tree-sitter
- CodebaseAnalyzer: Main interface (backward compatible)
- TreeSitterCore: Low-level tree-sitter operations
"""

# Core unified analysis components
from .unified_analyzer import UnifiedAnalyzer, AnalysisResult, CodebaseAnalysisResult
from .core.tree_sitter_core import TreeSitterCore, get_tree_sitter_core, ParseResult, QueryMatch

# Query engines
from .queries.python_queries import PythonQueries
from .queries.javascript_queries import JavaScriptQueries
from .queries.common_queries import CommonQueries

# Configuration
from .config.tree_sitter_config import TreeSitterConfig, LanguageConfig, create_default_tree_sitter_config

# Main interface (backward compatible)
from .analyzer import CodebaseAnalyzer

__all__ = [
    # Core unified components
    'UnifiedAnalyzer',
    'AnalysisResult', 
    'CodebaseAnalysisResult',
    'TreeSitterCore',
    'get_tree_sitter_core',
    'ParseResult',
    'QueryMatch',
    
    # Query engines
    'PythonQueries',
    'JavaScriptQueries', 
    'CommonQueries',
    
    # Configuration
    'TreeSitterConfig',
    'LanguageConfig',
    'create_default_tree_sitter_config',
    
    # Main interface
    'CodebaseAnalyzer',
]

# Version info
__version__ = '2.0.0'
__description__ = 'Unified codebase analysis using official tree-sitter patterns'

# ... existing legacy code for backward compatibility ...
