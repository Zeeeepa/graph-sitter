"""
🚀 UNIFIED ANALYSIS MODULE 🚀

Consolidated codebase analysis using official tree-sitter patterns and methods.
This module provides a unified interface for all analysis operations with proper
tree-sitter integration and eliminated legacy technical debt.

Key Features:
- Official tree-sitter API integration (TSParser → TSLanguage → TSTree → TSNode)
- Standardized query patterns using tree-sitter Query objects
- Consolidated analysis engine with proper error handling
- Performance-optimized tree traversal using TreeCursor
- Field-based node access using official methods
- Proper dependency management (no more try/catch patterns)

Main Classes:
- UnifiedAnalyzer: Core analysis engine using tree-sitter
- CodebaseAnalyzer: Main interface (backward compatible)
- TreeSitterCore: Low-level tree-sitter operations

# ... existing legacy imports for backward compatibility ...

# Core unified analysis components
from .unified_analyzer import UnifiedAnalyzer, AnalysisResult, CodebaseAnalysisResult
from .core.tree_sitter_core import TreeSitterCore, get_tree_sitter_core, ParseResult, QueryMatch

# Query engines
from .queries.python_queries import PythonQueries
from .queries.javascript_queries import JavaScriptQueries
from .queries.common_queries import CommonQueries

# Configuration
from .config.tree_sitter_config import TreeSitterConfig, LanguageConfig, create_default_tree_sitter_config

# Main interface (backward compatible)
from .analyzer import CodebaseAnalyzer

# Legacy components for backward compatibility
from .core.analysis_engine import AnalysisResult as LegacyAnalysisResult

# ... existing legacy exports ...

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
