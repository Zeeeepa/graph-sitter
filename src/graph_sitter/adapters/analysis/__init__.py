"""
Analysis adapters for graph-sitter.

This module provides comprehensive analysis capabilities for codebases,
including metrics calculation, dependency analysis, call graph generation,
dead code detection, and function context analysis.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from .enhanced_analysis import (
    EnhancedCodebaseAnalyzer as EnhancedAnalyzer,
    AnalysisReport,
    run_full_analysis as analyze_codebase_enhanced,
    get_function_context_analysis as analyze_function_enhanced,
    generate_analysis_report as get_enhanced_analysis_report
)

from .metrics import (
    FunctionMetrics,
    ClassMetrics,
    FileMetrics,
    CodebaseMetrics,
    MetricsCalculator,
    get_codebase_summary as calculate_codebase_metrics,
    analyze_function_metrics as calculate_function_metrics,
    analyze_class_metrics as calculate_class_metrics
)

from .dependency_analyzer import (
    DependencyAnalyzer,
    DependencyPath,
    CircularDependency,
    ImportAnalysis,
    find_circular_dependencies,
    build_dependency_graph as get_dependency_graph,
    analyze_imports as analyze_dependencies
)

from .call_graph import (
    CallGraphAnalyzer,
)

from .comprehensive_analysis import (
    ComprehensiveAnalysis,
    ComprehensiveAnalysisResult,
    analyze_codebase,
    quick_analysis,
    IssueItem,
    AnalysisSummary
)

__all__ = [
    # Core analysis classes
    'ComprehensiveAnalysis',
    'ComprehensiveAnalysisResult',
    
    # Enhanced analysis
    'EnhancedAnalyzer',
    'AnalysisReport',
    'analyze_codebase_enhanced',
    'analyze_function_enhanced',
    'get_enhanced_analysis_report',
    
    # Metrics
    'FunctionMetrics',
    'ClassMetrics',
    'FileMetrics',
    'CodebaseMetrics',
    'MetricsCalculator',
    'calculate_codebase_metrics',
    'calculate_function_metrics',
    'calculate_class_metrics',
    
    # Dependency analysis
    'DependencyAnalyzer',
    'DependencyPath',
    'CircularDependency',
    'ImportAnalysis',
    'find_circular_dependencies',
    'get_dependency_graph',
    'analyze_dependencies',
    
    # Call graph analysis
    'CallGraphAnalyzer',
    
    # Comprehensive analysis functions
    'analyze_codebase',
    'quick_analysis',
    'IssueItem',
    'AnalysisSummary'
]
