"""
Analysis adapters for graph-sitter codebase analysis.

This module contains all analysis-related functionality including:
- Enhanced code analysis
- Metrics calculation
- Dependency analysis
- Call graph generation
- Dead code detection
- Function context analysis
- Code modification tools (codemods)
"""

from .enhanced_analysis import (
    EnhancedAnalyzer,
    analyze_codebase_enhanced,
    analyze_function_enhanced,
    get_enhanced_analysis_report
)

from .metrics import (
    CodebaseMetrics,
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
    create_training_example,
    TrainingData
)

from .unified_analyzer import (
    UnifiedCodebaseAnalyzer,
    ComprehensiveAnalysisResult
)

from .codebase_db_adapter import CodebaseDBAdapter
from .database import Database

__all__ = [
    # Enhanced analysis
    'EnhancedAnalyzer',
    'analyze_codebase_enhanced',
    'analyze_function_enhanced',
    'get_enhanced_analysis_report',
    
    # Metrics
    'CodebaseMetrics',
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
    'TrainingData',
    
    # Unified analysis
    'UnifiedCodebaseAnalyzer',
    'ComprehensiveAnalysisResult',
    
    # Database components
    'CodebaseDBAdapter',
    'Database'
]
