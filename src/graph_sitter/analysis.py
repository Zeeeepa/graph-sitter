"""
Analysis Module - Comprehensive Codebase Analysis and Visualization

This module provides a unified interface for all codebase analysis and visualization
capabilities, aggregating functionality from the adapters directory into a clean
public API suitable for external consumption.

Key Features:
- Enhanced code analysis with error detection
- Comprehensive metrics calculation
- Dependency and call graph analysis
- Dead code detection
- Interactive visualizations and dashboards
- Error blast radius analysis
- Security and quality analysis

Example usage:
    from graph_sitter import Codebase, Analysis
    
    codebase = Codebase("/path/to/project")
    
    # Comprehensive analysis
    result = Analysis.analyze_comprehensive(codebase)
    
    # Specific analysis types
    metrics = Analysis.calculate_metrics(codebase)
    dependencies = Analysis.analyze_dependencies(codebase)
    dead_code = Analysis.find_dead_code(codebase)
    
    # Visualizations
    dashboard = Analysis.create_dashboard(codebase)
    blast_radius = Analysis.visualize_blast_radius(codebase, function_name)
"""

# Import all analysis functionality from adapters
try:
    from .adapters.analysis import (
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
        
        # Dependencies
        DependencyAnalyzer,
        analyze_dependencies,
        find_circular_dependencies,
        calculate_coupling_metrics,
        
        # Dead code detection
        DeadCodeAnalyzer,
        find_dead_code,
        find_unused_imports,
        find_unreachable_code,
        
        # Call graph analysis
        CallGraphAnalyzer,
        build_call_graph,
        analyze_call_patterns,
        find_call_chains,
        
        # Function context
        get_function_context,
        get_enhanced_function_context,
        FunctionContext
    )
    
    # Import unified analysis system
    from .unified_analysis import (
        UnifiedAnalysis,
        UnifiedAnalysisResult,
        analyze_comprehensive,
        from_repo_analysis,
        ANALYSIS_CONFIG,
        ANALYSIS_TYPES
    )
    
    # Import error detection and blast radius
    from .adapters.analysis.error_detection import (
        ErrorDetector,
        ErrorInstance,
        ErrorAnalysisResult
    )
    
    from .adapters.analysis.blast_radius import (
        BlastRadiusAnalyzer,
        BlastRadiusResult,
        BlastRadiusNode
    )
    
    # Import configuration
    from .adapters.config.analysis_config import (
        AnalysisType,
        TargetType,
        SeverityLevel,
        get_analysis_config,
        get_target_config,
        ANALYSIS_PRESETS
    )
except ImportError as e:
    # Provide fallback implementations or informative errors
    class EnhancedAnalyzer:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Enhanced analysis requires additional dependencies: {e}")
    
    def analyze_codebase_enhanced(*args, **kwargs):
        raise ImportError(f"Enhanced analysis requires additional dependencies: {e}")
    
    # Add similar fallbacks for other functions...
    analyze_function_enhanced = analyze_codebase_enhanced
    get_enhanced_analysis_report = analyze_codebase_enhanced
    CodebaseMetrics = EnhancedAnalyzer
    calculate_codebase_metrics = analyze_codebase_enhanced
    calculate_function_metrics = analyze_codebase_enhanced
    calculate_class_metrics = analyze_codebase_enhanced
    calculate_complexity_metrics = analyze_codebase_enhanced
    calculate_maintainability_index = analyze_codebase_enhanced
    DependencyAnalyzer = EnhancedAnalyzer
    analyze_dependencies = analyze_codebase_enhanced
    find_circular_dependencies = analyze_codebase_enhanced
    calculate_coupling_metrics = analyze_codebase_enhanced
    DeadCodeAnalyzer = EnhancedAnalyzer
    find_dead_code = analyze_codebase_enhanced
    find_unused_imports = analyze_codebase_enhanced
    find_unreachable_code = analyze_codebase_enhanced
    CallGraphAnalyzer = EnhancedAnalyzer
    build_call_graph = analyze_codebase_enhanced
    analyze_call_patterns = analyze_codebase_enhanced
    find_call_chains = analyze_codebase_enhanced
    FunctionContext = EnhancedAnalyzer
    get_function_context = analyze_codebase_enhanced
    get_enhanced_function_context = analyze_codebase_enhanced

# Import visualization functionality
try:
    from .adapters.visualizations import (
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
except ImportError as e:
    # Provide fallback implementations
    class ReactVisualizationGenerator:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Visualization functionality requires additional dependencies: {e}")
    
    def create_react_visualizations(*args, **kwargs):
        raise ImportError(f"Visualization functionality requires additional dependencies: {e}")
    
    # Add similar fallbacks for other visualization functions...
    generate_function_blast_radius = create_react_visualizations
    generate_issue_dashboard = create_react_visualizations
    generate_complexity_heatmap = create_react_visualizations
    generate_call_graph_visualization = create_react_visualizations
    generate_dependency_graph_visualization = create_react_visualizations
    generate_class_methods_visualization = create_react_visualizations
    generate_metrics_dashboard = create_react_visualizations
    generate_issues_visualization = create_react_visualizations
    CodebaseVisualizer = ReactVisualizationGenerator
    create_comprehensive_visualization = create_react_visualizations
    create_interactive_html_report = create_react_visualizations
    generate_visualization_data = create_react_visualizations
    create_visualization_components = create_react_visualizations

# Import unified analyzer
try:
    from .adapters.unified_analyzer import (
        UnifiedCodebaseAnalyzer,
        analyze_codebase_comprehensive,
        UnifiedAnalyzer,
        ComprehensiveAnalysisResult
    )
except ImportError as e:
    class UnifiedCodebaseAnalyzer:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Unified analyzer requires additional dependencies: {e}")
    
    def analyze_codebase_comprehensive(*args, **kwargs):
        raise ImportError(f"Unified analyzer requires additional dependencies: {e}")
    
    UnifiedAnalyzer = UnifiedCodebaseAnalyzer
    ComprehensiveAnalysisResult = UnifiedCodebaseAnalyzer

# Import database functionality
try:
    from .adapters.database import (
        AnalysisDatabase,
        store_analysis_report,
        get_analysis_reports,
        get_codebase_summary
    )
    
    from .adapters.codebase_db_adapter import (
        CodebaseDbAdapter,
        CodebaseDBAdapter
    )
except ImportError as e:
    class AnalysisDatabase:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Database functionality requires additional dependencies: {e}")
    
    def store_analysis_report(*args, **kwargs):
        raise ImportError(f"Database functionality requires additional dependencies: {e}")
    
    get_analysis_reports = store_analysis_report
    get_codebase_summary = store_analysis_report
    CodebaseDbAdapter = AnalysisDatabase
    CodebaseDBAdapter = AnalysisDatabase

# High-level convenience functions for external consumption
def analyze_comprehensive(codebase, **kwargs):
    """
    Perform comprehensive analysis of a codebase including all available analysis types.
    
    Args:
        codebase: Codebase instance to analyze
        **kwargs: Additional options for analysis
        
    Returns:
        ComprehensiveAnalysisResult: Complete analysis results with all components
    """
    analyzer = UnifiedCodebaseAnalyzer()
    return analyzer.analyze_comprehensive(codebase, **kwargs)

def calculate_metrics(codebase, **kwargs):
    """
    Calculate comprehensive metrics for a codebase.
    
    Args:
        codebase: Codebase instance to analyze
        **kwargs: Additional options for metrics calculation
        
    Returns:
        CodebaseMetrics: Calculated metrics
    """
    return calculate_codebase_metrics(codebase, **kwargs)

def analyze_dependencies(codebase, **kwargs):
    """
    Analyze dependencies and import patterns in a codebase.
    
    Args:
        codebase: Codebase instance to analyze
        **kwargs: Additional options for dependency analysis
        
    Returns:
        Dict: Dependency analysis results
    """
    analyzer = DependencyAnalyzer()
    return analyzer.analyze(codebase, **kwargs)

def find_dead_code(codebase, **kwargs):
    """
    Find dead code including unused functions, imports, and variables.
    
    Args:
        codebase: Codebase instance to analyze
        **kwargs: Additional options for dead code detection
        
    Returns:
        Dict: Dead code analysis results
    """
    analyzer = DeadCodeAnalyzer()
    return analyzer.find_dead_code(codebase, **kwargs)

def create_dashboard(codebase, **kwargs):
    """
    Create an interactive dashboard with comprehensive codebase visualizations.
    
    Args:
        codebase: Codebase instance to visualize
        **kwargs: Additional options for dashboard creation
        
    Returns:
        str: HTML content for interactive dashboard
    """
    return create_comprehensive_visualization(codebase, **kwargs)

def visualize_blast_radius(codebase, function_name=None, **kwargs):
    """
    Create blast radius visualization showing how changes propagate through the codebase.
    
    Args:
        codebase: Codebase instance to analyze
        function_name: Optional specific function to analyze
        **kwargs: Additional options for blast radius visualization
        
    Returns:
        str: HTML content for blast radius visualization
    """
    if function_name:
        return generate_function_blast_radius(codebase, function_name, **kwargs)
    else:
        # Generate general dependency visualization
        return generate_dependency_graph_visualization(codebase, **kwargs)

def create_react_visualizations(codebase, **kwargs):
    """
    Create React-compatible visualization components.
    
    Args:
        codebase: Codebase instance to visualize
        **kwargs: Additional options for React visualizations
        
    Returns:
        Dict: React visualization data and components
    """
    generator = ReactVisualizationGenerator()
    return generator.create_visualizations(codebase, **kwargs)

# Export all public functions and classes
__all__ = [
    # High-level convenience functions
    "analyze_comprehensive",
    "calculate_metrics", 
    "analyze_dependencies",
    "find_dead_code",
    "create_dashboard",
    "visualize_blast_radius",
    "create_react_visualizations",
    
    # Core analyzer classes
    "EnhancedAnalyzer",
    "CodebaseMetrics",
    "DependencyAnalyzer", 
    "CallGraphAnalyzer",
    "DeadCodeAnalyzer",
    "UnifiedCodebaseAnalyzer",
    "ReactVisualizationGenerator",
    "CodebaseVisualizer",
    
    # Analysis functions
    "analyze_codebase_enhanced",
    "calculate_codebase_metrics",
    "analyze_dependencies",
    "generate_call_graph",
    "find_dead_code",
    "get_function_context",
    
    # Visualization functions
    "create_comprehensive_visualization",
    "generate_function_blast_radius",
    "generate_issue_dashboard",
    "generate_complexity_heatmap",
    "create_interactive_html_report",
    
    # Database functions
    "store_analysis_report",
    "get_analysis_reports",
    
    # Data classes
    "ComprehensiveAnalysisResult",
    "FunctionContext",
]
