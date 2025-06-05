"""
Graph-sitter adapters for enhanced codebase analysis and visualization.

This package provides comprehensive adapters for analyzing codebases using tree-sitter,
with specialized modules for analysis and visualization functionality.
"""

# Analysis adapters
from .analysis import (
    # Enhanced analysis
    EnhancedAnalyzer,
    analyze_codebase_enhanced,
    analyze_function_enhanced,
    get_enhanced_analysis_report,
    
    # Metrics
    CodebaseMetrics,
    calculate_codebase_metrics,
    calculate_function_metrics,
    calculate_class_metrics,
    calculate_complexity_metrics,
    calculate_maintainability_index,
    
    # Dependency analysis
    DependencyAnalyzer,
    analyze_dependencies,
    get_dependency_graph,
    find_circular_dependencies,
    analyze_import_patterns,
    
    # Call graph
    CallGraphAnalyzer,
    generate_call_graph,
    analyze_function_calls,
    find_call_chains,
    detect_recursive_calls,
    
    # Dead code
    DeadCodeAnalyzer,
    find_dead_code,
    analyze_unused_functions,
    analyze_unused_imports,
    get_dead_code_report,
    
    # Function context
    FunctionContext,
    get_function_context,
    get_enhanced_function_context,
    analyze_function_issues,
    analyze_codebase_functions,
    create_training_example
)

# Visualization adapters
from .visualizations import (
    # React visualizations
    ReactVisualizationGenerator,
    create_react_visualizations,
    generate_function_blast_radius,
    generate_issue_dashboard,
    generate_complexity_heatmap,
    generate_call_graph_visualization,
    generate_dependency_graph_visualization,
    generate_class_methods_visualization,
    generate_metrics_dashboard,
    generate_issues_visualization,
    
    # Codebase visualizations
    CodebaseVisualizer,
    create_comprehensive_visualization,
    create_interactive_html_report,
    generate_visualization_data,
    create_visualization_components
)

# Core adapters (remaining in main directory)
from .unified_analyzer import (
    UnifiedCodebaseAnalyzer,
    analyze_codebase_comprehensive,
    UnifiedAnalyzer
)

from .database import (
    AnalysisDatabase,
    store_analysis_report,
    get_analysis_reports,
    get_codebase_summary
)

from .codebase_db_adapter import (
    CodebaseDbAdapter,
    CodebaseDBAdapter
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
    'store_analysis_report',
    'get_analysis_reports',
    'get_codebase_summary'
]

# Version info
__version__ = "1.0.0"
__author__ = "Graph-sitter Analysis Team"
__description__ = "Comprehensive codebase analysis following graph-sitter.com patterns"
