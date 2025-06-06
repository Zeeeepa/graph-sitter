"""
🔍 Graph-sitter Analysis Module

Comprehensive codebase analysis capabilities including:
- Core analysis engine with dependency tracking
- Advanced code quality metrics and complexity analysis
- Tree-sitter integration with query patterns
- Interactive visualization and reporting
- AI-powered code analysis and improvement
- Advanced configuration and performance tuning

This module consolidates all analysis functionality into a unified,
well-organized system based on patterns from graph-sitter.com and
comprehensive feature requirements.
"""

from .core import (
    AnalysisEngine,
    CodebaseAnalyzer,
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    get_function_context,
    analyze_codebase,
    hop_through_imports,
)

from .metrics import (
    MetricsCalculator,
    QualityMetrics,
    ComplexityAnalyzer,
    HalsteadMetrics,
    MaintainabilityIndex,
    calculate_cyclomatic_complexity,
    calculate_halstead_metrics,
    calculate_maintainability_index,
)

from .visualization import (
    VisualizationEngine,
    HTMLReportGenerator,
    DependencyGraphGenerator,
    InteractiveTreeVisualizer,
    export_to_html,
    export_to_json,
    export_to_dot,
    generate_d3_visualization,
)

from .ai_integration import (
    AIAnalyzer,
    AutomatedIssueDetector,
    CodeImprovementSuggester,
    DocumentationGenerator,
    analyze_with_ai,
    detect_issues_automatically,
    suggest_improvements,
)

from .tree_sitter_enhancements import (
    TreeSitterAnalyzer,
    QueryPatternEngine,
    SyntaxTreeVisualizer,
    PatternBasedSearcher,
    execute_query_patterns,
    visualize_syntax_tree,
    search_code_patterns,
)

from .config import (
    AnalysisConfig,
    AdvancedSettings,
    PerformanceConfig,
    DebugConfig,
    create_default_config,
    load_config_from_file,
    validate_config,
)

from .cli import (
    AnalysisCLI,
    run_analysis_cli,
    parse_arguments,
    execute_analysis_command,
)

__all__ = [
    # Core Analysis
    'AnalysisEngine',
    'CodebaseAnalyzer',
    'get_codebase_summary',
    'get_file_summary',
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    'get_function_context',
    'analyze_codebase',
    'hop_through_imports',
    
    # Metrics
    'MetricsCalculator',
    'QualityMetrics',
    'ComplexityAnalyzer',
    'HalsteadMetrics',
    'MaintainabilityIndex',
    'calculate_cyclomatic_complexity',
    'calculate_halstead_metrics',
    'calculate_maintainability_index',
    
    # Visualization
    'VisualizationEngine',
    'HTMLReportGenerator',
    'DependencyGraphGenerator',
    'InteractiveTreeVisualizer',
    'export_to_html',
    'export_to_json',
    'export_to_dot',
    'generate_d3_visualization',
    
    # AI Integration
    'AIAnalyzer',
    'AutomatedIssueDetector',
    'CodeImprovementSuggester',
    'DocumentationGenerator',
    'analyze_with_ai',
    'detect_issues_automatically',
    'suggest_improvements',
    
    # Tree-sitter Enhancements
    'TreeSitterAnalyzer',
    'QueryPatternEngine',
    'SyntaxTreeVisualizer',
    'PatternBasedSearcher',
    'execute_query_patterns',
    'visualize_syntax_tree',
    'search_code_patterns',
    
    # Configuration
    'AnalysisConfig',
    'AdvancedSettings',
    'PerformanceConfig',
    'DebugConfig',
    'create_default_config',
    'load_config_from_file',
    'validate_config',
    
    # CLI
    'AnalysisCLI',
    'run_analysis_cli',
    'parse_arguments',
    'execute_analysis_command',
]

# Version information
__version__ = "1.0.0"
__author__ = "Graph-sitter Analysis Team"
__description__ = "Comprehensive codebase analysis and intelligence system"

