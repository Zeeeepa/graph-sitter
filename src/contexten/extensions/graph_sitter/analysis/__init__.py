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

# Import existing comprehensive analysis functionality
from .core.engine import (
    ComprehensiveAnalysisEngine,
    AnalysisConfig,
    AnalysisResult,
    AnalysisPresets,
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
    
    # Core analysis
    'ComprehensiveAnalysisEngine',
    'AnalysisConfig',
    'AnalysisResult',
    'AnalysisPresets',
    'analyze_codebase',
    
    # Data classes
    'ImportLoop',
    'DeadCodeItem',
    'TrainingDataItem',
    'GraphAnalysisResult',
    'EnhancedFunctionMetrics',
    'EnhancedClassMetrics',
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
def quick_analysis(path: str, **kwargs) -> AnalysisResult:
    """Perform quick analysis with performance preset."""
    config = AnalysisPresets.performance()
    
    # Apply any keyword arguments
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    engine = ComprehensiveAnalysisEngine(config)
    return engine.analyze(path)


def comprehensive_analysis(path: str, **kwargs) -> AnalysisResult:
    """Perform comprehensive analysis with all features enabled."""
    config = AnalysisPresets.comprehensive()
    
    # Apply any keyword arguments
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    engine = ComprehensiveAnalysisEngine(config)
    return engine.analyze(path)


def quality_analysis(path: str, **kwargs) -> AnalysisResult:
    """Perform quality-focused analysis."""
    config = AnalysisPresets.quality_focused()
    
    # Apply any keyword arguments
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    engine = ComprehensiveAnalysisEngine(config)
    return engine.analyze(path)


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
