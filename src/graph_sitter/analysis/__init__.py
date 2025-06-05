"""
Graph-sitter analysis module.

This module provides comprehensive analysis capabilities for codebases,
including:
- Enhanced analysis with issue detection
- Metrics calculation (complexity, maintainability, etc.)
- Dependency analysis and circular dependency detection
- Call graph generation and analysis
- Dead code detection
- Function context analysis
- Unified analysis orchestration
"""

from .enhanced_analysis import (
    EnhancedCodebaseAnalyzer,
    AnalysisReport,
    run_full_analysis,
    get_function_context_analysis,
    get_codebase_health_score,
    generate_analysis_report
)

from .metrics import (
    CodebaseMetrics,
    FunctionMetrics,
    ClassMetrics,
    FileMetrics,
    MetricsCalculator,
    calculate_cyclomatic_complexity,
    calculate_maintainability_index,
    analyze_function_metrics,
    analyze_class_metrics,
    analyze_file_metrics,
    get_codebase_summary
)

from .dependency_analyzer import (
    DependencyAnalyzer,
    DependencyPath,
    CircularDependency,
    ImportAnalysis,
    hop_through_imports,
    find_dependency_paths,
    analyze_symbol_dependencies,
    find_circular_dependencies,
    build_dependency_graph,
    analyze_imports
)

from .call_graph import (
    CallGraphAnalyzer,
    CallGraphNode,
    CallGraphEdge,
    CallPath,
    build_call_graph,
    traverse_call_graph
)

from .dead_code import (
    DeadCodeDetector,
    DeadCodeItem,
    CleanupPlan,
    find_dead_code,
    find_unused_imports,
    find_unused_variables,
    estimate_cleanup_impact,
    get_removal_plan
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
from .database import (
    AnalysisDatabase,
    create_analysis_database,
    store_analysis_report,
    query_codebase_metrics,
    query_complex_functions,
    export_analysis_data
)

__all__ = [
    # Enhanced analysis
    'EnhancedCodebaseAnalyzer',
    'AnalysisReport',
    'run_full_analysis',
    'get_function_context_analysis',
    'get_codebase_health_score',
    'generate_analysis_report',
    
    # Metrics
    'CodebaseMetrics',
    'FunctionMetrics',
    'ClassMetrics',
    'FileMetrics',
    'MetricsCalculator',
    'calculate_cyclomatic_complexity',
    'calculate_maintainability_index',
    'analyze_function_metrics',
    'analyze_class_metrics',
    'analyze_file_metrics',
    'get_codebase_summary',
    
    # Dependency analysis
    'DependencyAnalyzer',
    'DependencyPath',
    'CircularDependency',
    'ImportAnalysis',
    'hop_through_imports',
    'find_dependency_paths',
    'analyze_symbol_dependencies',
    'find_circular_dependencies',
    'build_dependency_graph',
    'analyze_imports',
    
    # Call graph
    'CallGraphAnalyzer',
    'CallGraphNode',
    'CallGraphEdge',
    'CallPath',
    'build_call_graph',
    'traverse_call_graph',
    
    # Dead code
    'DeadCodeDetector',
    'DeadCodeItem',
    'CleanupPlan',
    'find_dead_code',
    'find_unused_imports',
    'find_unused_variables',
    'estimate_cleanup_impact',
    'get_removal_plan',
    
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
    'AnalysisDatabase',
    'create_analysis_database',
    'store_analysis_report',
    'query_codebase_metrics',
    'query_complex_functions',
    'export_analysis_data'
]
