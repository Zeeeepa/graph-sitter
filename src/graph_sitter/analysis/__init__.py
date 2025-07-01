"""Graph-sitter analysis module with comprehensive codebase analysis capabilities."""

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

from .enhanced_analysis import (
    EnhancedCodebaseAnalyzer,
    AnalysisReport,
    run_full_analysis,
    get_function_context_analysis,
    get_codebase_health_score,
    query_analysis_data,
    generate_analysis_report
)

from .metrics import (
    MetricsCalculator,
    FunctionMetrics,
    ClassMetrics,
    FileMetrics,
    CodebaseMetrics,
    calculate_cyclomatic_complexity,
    calculate_maintainability_index,
    analyze_function_metrics,
    analyze_class_metrics,
    analyze_file_metrics,
    get_codebase_summary
)

from .database import (
    AnalysisDatabase,
    create_analysis_database,
    store_analysis_report,
    query_codebase_metrics,
    query_complex_functions,
    export_analysis_data
)

__all__ = [
    # Call Graph Analysis
    'CallGraphAnalyzer',
    'CallGraphNode', 
    'CallGraphEdge',
    'CallPath',
    'build_call_graph',
    'traverse_call_graph',
    
    # Dead Code Detection
    'DeadCodeDetector',
    'DeadCodeItem',
    'CleanupPlan',
    'find_dead_code',
    'find_unused_imports',
    'find_unused_variables',
    'estimate_cleanup_impact',
    'get_removal_plan',
    
    # Dependency Analysis
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
    
    # Enhanced Analysis
    'EnhancedCodebaseAnalyzer',
    'AnalysisReport',
    'run_full_analysis',
    'get_function_context_analysis',
    'get_codebase_health_score',
    'query_analysis_data',
    'generate_analysis_report',
    
    # Metrics
    'MetricsCalculator',
    'FunctionMetrics',
    'ClassMetrics',
    'FileMetrics',
    'CodebaseMetrics',
    'calculate_cyclomatic_complexity',
    'calculate_maintainability_index',
    'analyze_function_metrics',
    'analyze_class_metrics',
    'analyze_file_metrics',
    'get_codebase_summary',
    
    # Database
    'AnalysisDatabase',
    'create_analysis_database',
    'store_analysis_report',
    'query_codebase_metrics',
    'query_complex_functions',
    'export_analysis_data'
]

# Version info
__version__ = "1.0.0"
__author__ = "Graph-sitter Analysis Team"
__description__ = "Comprehensive codebase analysis following graph-sitter.com patterns"

