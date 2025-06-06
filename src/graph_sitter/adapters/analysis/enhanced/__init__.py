"""
🌳 ENHANCED ANALYSIS FEATURES 🌳

Advanced analysis features including tree-sitter query patterns
and enhanced syntax analysis capabilities.

Features:
- Tree-sitter query patterns for advanced syntax analysis
- Pattern-based code search and analysis
- Query-based metrics calculation
- Custom query pattern support
- Performance-optimized query execution
"""

from .tree_sitter_queries import (
    TreeSitterQueryEngine,
    QueryPattern,
    QueryMatch,
    QueryResult,
    create_query_engine,
    analyze_with_queries
)

__all__ = [
    'TreeSitterQueryEngine',
    'QueryPattern',
    'QueryMatch',
    'QueryResult',
    'create_query_engine',
    'analyze_with_queries'
]

