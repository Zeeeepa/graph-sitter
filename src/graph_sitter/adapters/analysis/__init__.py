"""
Graph-Sitter Analysis Module

This module provides comprehensive codebase analysis capabilities including:
- Codebase summarization and statistics
- Symbol analysis and usage tracking
- Dead code detection
- Import relationship analysis
- Class hierarchy exploration
- Test analysis and organization
- AI-powered code analysis
- Training data generation for LLMs

All analysis features are consolidated here for better organization and maintainability.
"""

from .codebase_summary import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

from .symbol_analysis import (
    analyze_symbol_usage,
    find_recursive_functions,
    get_symbol_dependencies
)

from .dead_code_detection import (
    find_dead_code,
    analyze_unused_imports,
    detect_unreachable_code
)

from .import_analysis import (
    analyze_import_relationships,
    detect_circular_imports,
    get_import_graph
)

from .class_hierarchy import (
    analyze_inheritance_chains,
    find_deepest_inheritance,
    get_class_relationships
)

from .test_analysis import (
    analyze_test_coverage,
    split_test_files,
    get_test_statistics
)

from .ai_analysis import (
    analyze_codebase,
    get_function_context,
    hop_through_imports,
    flag_code_issues
)

from .training_data import (
    generate_training_data,
    create_function_embeddings,
    extract_code_patterns
)

__all__ = [
    # Codebase summary
    'get_codebase_summary',
    'get_file_summary', 
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    
    # Symbol analysis
    'analyze_symbol_usage',
    'find_recursive_functions',
    'get_symbol_dependencies',
    
    # Dead code detection
    'find_dead_code',
    'analyze_unused_imports',
    'detect_unreachable_code',
    
    # Import analysis
    'analyze_import_relationships',
    'detect_circular_imports',
    'get_import_graph',
    
    # Class hierarchy
    'analyze_inheritance_chains',
    'find_deepest_inheritance',
    'get_class_relationships',
    
    # Test analysis
    'analyze_test_coverage',
    'split_test_files',
    'get_test_statistics',
    
    # AI analysis
    'analyze_codebase',
    'get_function_context',
    'hop_through_imports',
    'flag_code_issues',
    
    # Training data
    'generate_training_data',
    'create_function_embeddings',
    'extract_code_patterns'
]

