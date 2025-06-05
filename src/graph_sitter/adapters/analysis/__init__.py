"""
Analysis adapters for graph-sitter codebase analysis.

This module contains all analysis-related functionality including:
- Enhanced code analysis
- Metrics calculation
- Dependency analysis
- Call graph generation
- Dead code detection
- Function context analysis
- Database-integrated analysis
- Backward compatibility functions
"""

from .enhanced_analysis import (
    EnhancedAnalyzer,
    analyze_codebase_enhanced,
    analyze_function_enhanced,
    get_enhanced_analysis_report
)

from .metrics import (
    CodebaseMetrics,
    EnhancedCodebaseMetrics,
    calculate_codebase_metrics,
    calculate_function_metrics,
    calculate_class_metrics,
    calculate_complexity_metrics,
    calculate_maintainability_index
)

from .dependency_analyzer import (
    DependencyAnalyzer,
    analyze_dependencies,
    get_dependency_graph,
    find_circular_dependencies,
    analyze_import_patterns
)

from .call_graph import (
    CallGraphAnalyzer,
    generate_call_graph,
    analyze_function_calls,
    find_call_chains,
    detect_recursive_calls
)

from .dead_code import (
    DeadCodeAnalyzer,
    find_dead_code,
    analyze_unused_functions,
    analyze_unused_imports,
    get_dead_code_report
)

from .function_context import (
    FunctionContext,
    get_function_context,
    get_enhanced_function_context,
    analyze_function_issues,
    analyze_codebase_functions,
    create_training_example
)

# New database-integrated analysis functionality
from .db_integrated_analysis import (
    CodebaseDBAdapter,
    create_enhanced_analyzer
)

from .database_utils import (
    AnalysisResult,
    DatabaseMetrics,
    DatabaseConnection,
    convert_rset_to_dicts,
    execute_query_with_rset_conversion
)

from .compatibility import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    get_codebase_summary_enhanced
)

__all__ = [
    # Enhanced analysis
    'EnhancedAnalyzer',
    'analyze_codebase_enhanced',
    'analyze_function_enhanced',
    'get_enhanced_analysis_report',
    
    # Metrics
    'CodebaseMetrics',
    'EnhancedCodebaseMetrics',
    'calculate_codebase_metrics',
    'calculate_function_metrics',
    'calculate_class_metrics',
    'calculate_complexity_metrics',
    'calculate_maintainability_index',
    
    # Dependency analysis
    'DependencyAnalyzer',
    'analyze_dependencies',
    'get_dependency_graph',
    'find_circular_dependencies',
    'analyze_import_patterns',
    
    # Call graph
    'CallGraphAnalyzer',
    'generate_call_graph',
    'analyze_function_calls',
    'find_call_chains',
    'detect_recursive_calls',
    
    # Dead code
    'DeadCodeAnalyzer',
    'find_dead_code',
    'analyze_unused_functions',
    'analyze_unused_imports',
    'get_dead_code_report',
    
    # Function context
    'FunctionContext',
    'get_function_context',
    'get_enhanced_function_context',
    'analyze_function_issues',
    'analyze_codebase_functions',
    'create_training_example',
    
    # Database-integrated analysis
    'CodebaseDBAdapter',
    'create_enhanced_analyzer',
    'AnalysisResult',
    'DatabaseMetrics',
    'DatabaseConnection',
    'convert_rset_to_dicts',
    'execute_query_with_rset_conversion',
    
    # Backward compatibility
    'get_codebase_summary',
    'get_file_summary',
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    'get_codebase_summary_enhanced'
]

