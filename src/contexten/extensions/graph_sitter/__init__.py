"""
Graph-sitter adapters for enhanced codebase analysis and visualization.

This package provides comprehensive adapters for analyzing codebases using tree-sitter,
with specialized modules for analysis, visualization, and code modification functionality.
"""

# Analysis module
from .analysis import (
    analyze_codebase,
    ComprehensiveAnalysisEngine,
    AnalysisConfig,
    AnalysisResult,
    AnalysisPresets,
    ImportLoop,
    DeadCodeItem,
    TrainingDataItem,
    EnhancedFunctionMetrics,
    EnhancedClassMetrics,
    GraphAnalysisResult,
)

# Visualization adapters (if available)
try:
    from .visualizations import (
        # Configuration
        VisualizationConfig,
        VisualizationType,
        OutputFormat,
        CallTraceConfig,
        DependencyTraceConfig,
        BlastRadiusConfig,
        MethodRelationshipsConfig,
        create_config,
        get_default_config,
        DEFAULT_COLOR_PALETTE,
        
        # Base classes
        BaseVisualizationAdapter,
        VisualizationResult,
        FunctionCallMixin,
        DependencyMixin,
        UsageMixin,
        
        # Specific visualizers
        CallTraceVisualizer,
        DependencyTraceVisualizer,
        BlastRadiusVisualizer,
        MethodRelationshipsVisualizer,
        UnifiedVisualizationManager,
        
        # React visualizations
        ReactVisualizationGenerator,
        create_react_visualizations,
    )
    VISUALIZATIONS_AVAILABLE = True
except ImportError:
    VISUALIZATIONS_AVAILABLE = False

__all__ = [
    # Core analysis engine
    'ComprehensiveAnalysisEngine',
    'AnalysisConfig',
    'AnalysisResult',
    'analyze_codebase',
    'quick_analysis',
    'comprehensive_analysis',
    'basic_analysis',
    'AnalysisPresets',
    
    # Data classes
    'ImportLoop',
    'DeadCodeItem',
    'TrainingDataItem',
    'EnhancedFunctionMetrics',
    'EnhancedClassMetrics',
    'GraphAnalysisResult',
    
    # Enhanced analysis
    'get_codebase_summary_enhanced',
    'analyze_function_enhanced',
    'analyze_class_enhanced',
    'get_function_context',
    'analyze_graph_structure',
    
    # Metrics
    'calculate_cyclomatic_complexity',
    'calculate_halstead_volume',
    'calculate_maintainability_index',
    
    # Legacy compatibility
    'get_codebase_summary',
    'print_codebase_overview',
    'analyze_symbol_usage',
    'find_recursive_functions',
    'find_dead_code',
    'generate_dead_code_report',
    'analyze_import_relationships',
    'detect_circular_imports',
    'analyze_inheritance_chains',
    'detect_design_patterns',
    'analyze_test_coverage',
    'get_test_statistics',
    'ai_analyze_codebase',
    'flag_code_issues',
    'legacy_generate_training_data'
]

# Add visualization exports if available
if VISUALIZATIONS_AVAILABLE:
    __all__.extend([
        # Visualization configuration
        'VisualizationConfig',
        'VisualizationType',
        'OutputFormat',
        'CallTraceConfig',
        'DependencyTraceConfig',
        'BlastRadiusConfig',
        'MethodRelationshipsConfig',
        'create_config',
        'get_default_config',
        'DEFAULT_COLOR_PALETTE',
        
        # Base classes
        'BaseVisualizationAdapter',
        'VisualizationResult',
        'FunctionCallMixin',
        'DependencyMixin',
        'UsageMixin',
        
        # Specific visualizers
        'CallTraceVisualizer',
        'DependencyTraceVisualizer',
        'BlastRadiusVisualizer',
        'MethodRelationshipsVisualizer',
        'UnifiedVisualizationManager',
        
        # React visualizations
        'ReactVisualizationGenerator',
        'create_react_visualizations',
    ])
