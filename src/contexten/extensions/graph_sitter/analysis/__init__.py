"""
🚀 COMPREHENSIVE ANALYSIS MODULE 🚀

Enhanced analysis capabilities for graph-sitter with advanced features:

PHASE 1 FEATURES:
- Import loop detection and circular dependency analysis
- Dead code detection using usage analysis
- Training data generation for LLMs
- Enhanced function and class metrics
- Graph structure analysis with NetworkX
- Performance optimizations and graceful degradation

PHASE 2 FEATURES:
- Tree-sitter query patterns for advanced syntax analysis
- Interactive HTML reports with D3.js integration
- Performance optimizations with caching and parallel processing
- Advanced CodebaseConfig usage with all flags
- Custom analysis pipelines and feature toggles

This module consolidates all analysis functionality into a unified system
while maintaining backward compatibility and clean architecture.

DOCUMENTATION API:
- Analysis class providing the exact API from graph-sitter documentation
- Direct access to pre-computed graph elements
- Advanced function and class analysis
"""

# Import the Analysis class that provides the documentation API
from .analyzer import Analysis
try:
    from .enhanced_analyzer import EnhancedCodebaseAnalyzer
except ImportError:
    EnhancedCodebaseAnalyzer = None

try:
    from .codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary,
        CodebaseElements,
        CodebaseSummary,
        FileSummary,
        ClassSummary,
        FunctionSummary,
        SymbolSummary,
    )
except ImportError:
    # Provide stub functions if not available
    def get_codebase_summary(*args, **kwargs):
        raise NotImplementedError("codebase_analysis module not available")
    def get_file_summary(*args, **kwargs):
        raise NotImplementedError("codebase_analysis module not available")
    def get_class_summary(*args, **kwargs):
        raise NotImplementedError("codebase_analysis module not available")
    def get_function_summary(*args, **kwargs):
        raise NotImplementedError("codebase_analysis module not available")
    def get_symbol_summary(*args, **kwargs):
        raise NotImplementedError("codebase_analysis module not available")
    
    CodebaseElements = None
    CodebaseSummary = None
    FileSummary = None
    ClassSummary = None
    FunctionSummary = None
    SymbolSummary = None

# Import optional analyzers with fallbacks
try:
    from .complexity_analyzer import ComplexityAnalyzer
except ImportError:
    ComplexityAnalyzer = None

try:
    from .dependency_analyzer import DependencyAnalyzer
except ImportError:
    DependencyAnalyzer = None

try:
    from .security_analyzer import SecurityAnalyzer
except ImportError:
    SecurityAnalyzer = None

try:
    from .call_graph_analyzer import CallGraphAnalyzer
except ImportError:
    CallGraphAnalyzer = None

try:
    from .dead_code_detector import DeadCodeDetector
except ImportError:
    DeadCodeDetector = None

# Import existing comprehensive analysis functionality
from .core.engine import (
    ComprehensiveAnalysisEngine,
    AnalysisConfig,
    AnalysisResult,
    AnalysisMetrics,
    QualityMetrics,
    SecurityMetrics,
    PerformanceMetrics,
    MaintainabilityMetrics,
    ComplexityMetrics,
    DependencyMetrics,
    TestCoverageMetrics,
    DocumentationMetrics,
    CodeStyleMetrics,
    ArchitecturalMetrics,
    TechnicalDebtMetrics,
    analyze_codebase,
    
    # Data classes
    ImportLoop,
    DeadCodeItem,
    TrainingDataItem,
    GraphAnalysisResult,
    EnhancedFunctionMetrics,
    EnhancedClassMetrics
)

# Phase 2 exports - Tree-sitter queries
try:
    from .enhanced.tree_sitter_queries import (
        TreeSitterQueryEngine,
        QueryPattern,
        QueryResult,
        analyze_with_queries
    )
    TREE_SITTER_QUERIES_AVAILABLE = True
except ImportError:
    TREE_SITTER_QUERIES_AVAILABLE = False

# Phase 2 exports - Visualization
try:
    from .visualization import (
        InteractiveReportGenerator,
        ReportConfig,
        create_interactive_report,
        generate_html_report
    )
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Phase 2 exports - Performance optimization
try:
    from .core.performance import (
        PerformanceOptimizer,
        PerformanceConfig,
        create_optimizer
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False

# Phase 2 exports - Advanced configuration
try:
    from .config import (
        AdvancedCodebaseConfig,
        create_optimized_config,
        create_debug_config,
        create_production_config
    )
    ADVANCED_CONFIG_AVAILABLE = True
except ImportError:
    ADVANCED_CONFIG_AVAILABLE = False

__all__ = [
    # Documentation API
    'Analysis',
    
    # New codebase analysis API
    'get_codebase_summary',
    'get_file_summary',
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    'CodebaseElements',
    'CodebaseSummary',
    'FileSummary',
    'ClassSummary',
    'FunctionSummary',
    'SymbolSummary',
    
    # Specialized analyzers
    'ComplexityAnalyzer',
    'DependencyAnalyzer',
    'SecurityAnalyzer',
    'CallGraphAnalyzer',
    'DeadCodeDetector',
    
    # Core analysis
    'ComprehensiveAnalysisEngine',
    'AnalysisConfig',
    'AnalysisResult',
    'AnalysisMetrics',
    'QualityMetrics',
    'SecurityMetrics',
    'PerformanceMetrics',
    'MaintainabilityMetrics',
    'ComplexityMetrics',
    'DependencyMetrics',
    'TestCoverageMetrics',
    'DocumentationMetrics',
    'CodeStyleMetrics',
    'ArchitecturalMetrics',
    'TechnicalDebtMetrics',
    
    # Analysis functions
    'analyze_codebase',
    'analyze_file',
    'analyze_function',
    'analyze_class',
    'analyze_dependencies',
    'analyze_complexity',
    'analyze_security',
    'analyze_performance',
    'analyze_maintainability',
    'analyze_test_coverage',
    'analyze_documentation',
    'analyze_code_style',
    'analyze_architecture',
    'analyze_technical_debt',
    
    # Utility functions
    'get_analysis_summary',
    'export_analysis_results',
    'generate_analysis_report',
    'compare_analysis_results',
    'track_analysis_trends',
    
    # Configuration
    'create_analysis_config',
    'load_analysis_config',
    'save_analysis_config',
    'validate_analysis_config',
    
    # Reporting
    'generate_html_report',
    'generate_json_report',
    'generate_csv_report',
    'generate_markdown_report',
    
    # Visualization
    'create_dependency_graph',
    'create_complexity_heatmap',
    'create_architecture_diagram',
    'create_call_graph',
    'create_metrics_dashboard',
]

# Add Phase 2 exports if available
if TREE_SITTER_QUERIES_AVAILABLE:
    __all__.extend([
        'TreeSitterQueryEngine',
        'QueryPattern',
        'QueryResult',
        'analyze_with_queries'
    ])

if VISUALIZATION_AVAILABLE:
    __all__.extend([
        'InteractiveReportGenerator',
        'ReportConfig',
        'create_interactive_report',
        'generate_html_report'
    ])

if PERFORMANCE_AVAILABLE:
    __all__.extend([
        'PerformanceOptimizer',
        'PerformanceConfig',
        'create_optimizer'
    ])

if ADVANCED_CONFIG_AVAILABLE:
    __all__.extend([
        'AdvancedCodebaseConfig',
        'create_optimized_config',
        'create_debug_config',
        'create_production_config'
    ])

# Convenience functions for quick analysis
def quick_analysis(path: str, **kwargs):
    """Perform quick analysis with performance preset."""
    try:
        from .core.engine import ComprehensiveAnalysisEngine, AnalysisPresets
        config = AnalysisPresets.performance()
        
        # Apply any keyword arguments
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        engine = ComprehensiveAnalysisEngine(config)
        return engine.analyze(path)
    except ImportError:
        raise NotImplementedError("Analysis engine not available")


def comprehensive_analysis(path: str, **kwargs):
    """Perform comprehensive analysis with all features enabled."""
    try:
        from .core.engine import ComprehensiveAnalysisEngine, AnalysisPresets
        config = AnalysisPresets.comprehensive()
        
        # Apply any keyword arguments
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        engine = ComprehensiveAnalysisEngine(config)
        return engine.analyze(path)
    except ImportError:
        raise NotImplementedError("Analysis engine not available")


def quality_analysis(path: str, **kwargs):
    """Perform quality-focused analysis."""
    try:
        from .core.engine import ComprehensiveAnalysisEngine, AnalysisPresets
        config = AnalysisPresets.quality_focused()
        
        # Apply any keyword arguments
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        engine = ComprehensiveAnalysisEngine(config)
        return engine.analyze(path)
    except ImportError:
        raise NotImplementedError("Analysis engine not available")

# Add convenience functions to __all__
__all__.extend([
    'quick_analysis',
    'comprehensive_analysis',
    'quality_analysis'
])

# Module metadata
__version__ = "2.0.0"
__author__ = "Graph-Sitter Analysis Team"
__description__ = "Enhanced comprehensive analysis system with Phase 2 features"

# Feature availability information
FEATURES = {
    "core_analysis": True,
    "import_loops": True,
    "dead_code": True,
    "training_data": True,
    "graph_analysis": True,
    "enhanced_metrics": True,
    "tree_sitter_queries": TREE_SITTER_QUERIES_AVAILABLE,
    "visualization": VISUALIZATION_AVAILABLE,
    "performance_optimization": PERFORMANCE_AVAILABLE,
    "advanced_configuration": ADVANCED_CONFIG_AVAILABLE
}

def get_feature_status() -> dict:
    """Get the status of all available features."""
    return FEATURES.copy()


def print_feature_status():
    """Print the status of all features."""
    print("🚀 Graph-Sitter Analysis Features")
    print("=" * 40)
    
    for feature, available in FEATURES.items():
        status = "✅" if available else "❌"
        print(f"{status} {feature.replace('_', ' ').title()}")
    
    print(f"\nVersion: {__version__}")
    print(f"Phase 2 Features: {sum(1 for f in ['tree_sitter_queries', 'visualization', 'performance_optimization', 'advanced_configuration'] if FEATURES[f])}/4")


if __name__ == "__main__":
    print_feature_status()
