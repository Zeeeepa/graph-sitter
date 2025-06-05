"""
Graph-Sitter Analysis - Using Built-in Capabilities

This module implements the actual graph-sitter analysis patterns from graph-sitter.com
instead of the overcomplicated custom implementations that were removed.

All analysis is based on graph-sitter's pre-computed relationships and instant lookups.
"""

from .simple_analysis import (
    analyze_codebase,
    get_dead_code,
    remove_dead_code,
    get_call_graph,
    get_inheritance_hierarchy,
    get_dependencies,
    get_usages,
    find_recursive_functions,
    analyze_test_coverage,
    get_codebase_stats
)

from .visualization import (
    visualize_call_graph,
    visualize_inheritance,
    visualize_dependencies,
    create_interactive_dashboard
)

__all__ = [
    # Core analysis functions
    'analyze_codebase',
    'get_dead_code', 
    'remove_dead_code',
    'get_call_graph',
    'get_inheritance_hierarchy',
    'get_dependencies',
    'get_usages',
    'find_recursive_functions',
    'analyze_test_coverage',
    'get_codebase_stats',
    
    # Visualization functions
    'visualize_call_graph',
    'visualize_inheritance', 
    'visualize_dependencies',
    'create_interactive_dashboard'
]

