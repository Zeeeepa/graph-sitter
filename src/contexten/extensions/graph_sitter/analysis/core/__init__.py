"""
Core Analysis Components

Provides the fundamental analysis capabilities for the unified tree-sitter system.
"""

from .models import (
    CodeIssue, DeadCodeItem, FunctionMetrics, ClassMetrics, FileAnalysis,
    ComprehensiveAnalysisResult, AnalysisOptions, AnalysisContext,
    ImportLoop, TrainingDataItem, GraphAnalysisResult,
    EnhancedFunctionMetrics, EnhancedClassMetrics,
    create_default_analysis_options, merge_analysis_results
)

# Tree-sitter core components
from .tree_sitter_core import TreeSitterCore, get_tree_sitter_core, ParseResult, QueryMatch

from .analysis_engine import (
    calculate_cyclomatic_complexity, calculate_cyclomatic_complexity_graph_sitter,
    get_operators_and_operands, calculate_halstead_volume, calculate_maintainability_index,
    calculate_doi, count_lines, analyze_python_file, analyze_function_ast,
    analyze_class_ast, analyze_codebase_directory, get_complexity_rank,
    calculate_technical_debt_hours, generate_summary_statistics
)

from .graph_enhancements import (
    hop_through_imports, get_function_context, detect_import_loops,
    analyze_graph_structure, detect_dead_code, generate_training_data,
    analyze_function_enhanced, analyze_class_enhanced, get_codebase_summary_enhanced,
    generate_import_loop_recommendations, generate_dead_code_recommendations,
    generate_graph_insights, generate_graph_recommendations
)

try:
    from .codebase_analyzer import CodebaseAnalyzer
    CODEBASE_ANALYZER_AVAILABLE = True
except ImportError:
    CODEBASE_ANALYZER_AVAILABLE = False

__all__ = [
    # Models
    "CodeIssue", "DeadCodeItem", "FunctionMetrics", "ClassMetrics", "FileAnalysis",
    "ComprehensiveAnalysisResult", "AnalysisOptions", "AnalysisContext",
    "ImportLoop", "TrainingDataItem", "GraphAnalysisResult",
    "EnhancedFunctionMetrics", "EnhancedClassMetrics",
    "create_default_analysis_options", "merge_analysis_results",
    
    # Analysis Engine Functions
    "calculate_cyclomatic_complexity", "calculate_cyclomatic_complexity_graph_sitter",
    "get_operators_and_operands", "calculate_halstead_volume", "calculate_maintainability_index",
    "calculate_doi", "count_lines", "analyze_python_file", "analyze_function_ast",
    "analyze_class_ast", "analyze_codebase_directory", "get_complexity_rank",
    "calculate_technical_debt_hours", "generate_summary_statistics",
    
    # Graph Enhancement Functions
    "hop_through_imports", "get_function_context", "detect_import_loops",
    "analyze_graph_structure", "detect_dead_code", "generate_training_data",
    "analyze_function_enhanced", "analyze_class_enhanced", "get_codebase_summary_enhanced",
    "generate_import_loop_recommendations", "generate_dead_code_recommendations",
    "generate_graph_insights", "generate_graph_recommendations",
    
    # Tree-sitter core components
    "TreeSitterCore", "get_tree_sitter_core", "ParseResult", "QueryMatch",
]

# Add CodebaseAnalyzer if available
if CODEBASE_ANALYZER_AVAILABLE:
    __all__.append("CodebaseAnalyzer")
