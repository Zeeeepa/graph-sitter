"""
🚀 ENHANCED COMPREHENSIVE ANALYSIS SYSTEM 🚀

A unified analysis system that consolidates all advanced analysis capabilities:
- Core quality metrics (maintainability, complexity, Halstead, etc.)
- Advanced investigation features (function context, relationships)
- Import loop detection and circular dependency analysis
- Training data generation for LLMs
- Dead code detection using usage analysis
- Advanced graph structure analysis
- Tree-sitter query patterns and visualization
- Performance optimizations with lazy loading
- Enhanced configuration with CodebaseConfig

Enhanced Features from Legacy Integration:
- Graph-sitter pre-computed element access
- Function/class dependency and usage analysis
- Import relationship mapping and loop detection
- Training data extraction for ML models
- Advanced visualization and reporting
- Performance optimizations with caching

Usage:
    from graph_sitter.adapters.analysis import analyze_codebase, AnalysisPresets
    
    # Quick analysis
    result = analyze_codebase("/path/to/code")
    
    # Comprehensive analysis
    result = analyze_codebase("/path/to/code", AnalysisPresets.comprehensive())
    
    # Custom configuration
    from graph_sitter.adapters.analysis import AnalysisConfig
    config = AnalysisConfig(
        detect_import_loops=True,
        detect_dead_code=True,
        generate_training_data=True,
        analyze_graph_structure=True,
        enhanced_metrics=True
    )
    result = analyze_codebase("/path/to/code", config)

Command Line:
    python -m graph_sitter.adapters.analysis.cli /path/to/code --comprehensive
    python -m graph_sitter.adapters.analysis.cli /path/to/code --import-loops --dead-code
    python -m graph_sitter.adapters.analysis.cli /path/to/code --training-data --output ml_data.json
"""

# Core analysis engine
from .core.engine import (
    # Main analysis function
    analyze_codebase,
    
    # Core classes
    ComprehensiveAnalysisEngine,
    AnalysisConfig,
    AnalysisResult,
    
    # Enhanced data classes
    ImportLoop,
    TrainingDataItem,
    DeadCodeItem,
    GraphAnalysisResult,
    EnhancedFunctionMetrics,
    EnhancedClassMetrics,
    
    # Preset configurations
    AnalysisPresets,
)

# Enhanced graph-sitter integration
from .enhanced.graph_sitter_integration import (
    get_codebase_summary_enhanced,
    analyze_function_enhanced,
    analyze_class_enhanced,
    get_function_context,
    analyze_graph_structure,
    calculate_cyclomatic_complexity,
    calculate_halstead_volume,
    calculate_maintainability_index
)

# Legacy analysis modules (import with error handling)
try:
    from .codebase_summary import get_codebase_summary, print_codebase_overview
    from .symbol_analysis import analyze_symbol_usage, find_recursive_functions
    from .dead_code_detection import find_dead_code, generate_dead_code_report
    from .import_analysis import analyze_import_relationships, detect_circular_imports
    from .class_hierarchy import analyze_inheritance_chains, detect_design_patterns
    from .test_analysis import analyze_test_coverage, get_test_statistics
    from .training_data import generate_training_data as legacy_generate_training_data
    LEGACY_MODULES_AVAILABLE = True
except ImportError:
    # Create dummy functions for missing legacy modules
    def get_codebase_summary(*args, **kwargs): return {}
    def print_codebase_overview(*args, **kwargs): pass
    def analyze_symbol_usage(*args, **kwargs): return {}
    def find_recursive_functions(*args, **kwargs): return []
    def find_dead_code(*args, **kwargs): return []
    def generate_dead_code_report(*args, **kwargs): return ""
    def analyze_import_relationships(*args, **kwargs): return {}
    def detect_circular_imports(*args, **kwargs): return []
    def analyze_inheritance_chains(*args, **kwargs): return {}
    def detect_design_patterns(*args, **kwargs): return []
    def analyze_test_coverage(*args, **kwargs): return {}
    def get_test_statistics(*args, **kwargs): return {}
    def legacy_generate_training_data(*args, **kwargs): return []
    LEGACY_MODULES_AVAILABLE = False

# AI analysis (import with error handling)
try:
    from .ai_analysis import analyze_codebase as ai_analyze_codebase, flag_code_issues
    AI_ANALYSIS_AVAILABLE = True
except ImportError:
    def ai_analyze_codebase(*args, **kwargs): return {}
    def flag_code_issues(*args, **kwargs): return []
    AI_ANALYSIS_AVAILABLE = False

# Convenience functions
def comprehensive_analysis(path, **kwargs):
    """Perform comprehensive analysis with all features enabled."""
    config = AnalysisConfig(
        detect_import_loops=True,
        detect_dead_code=True,
        generate_training_data=kwargs.get('training_data', False),
        analyze_graph_structure=True,
        **kwargs
    )
    return analyze_codebase(path, config)

def basic_analysis(path, **kwargs):
    """Perform basic analysis with core metrics only."""
    config = AnalysisConfig(
        detect_import_loops=False,
        detect_dead_code=False,
        generate_training_data=False,
        analyze_graph_structure=True,
        **kwargs
    )
    return analyze_codebase(path, config)

# Analysis presets
class AnalysisPresets:
    """Predefined analysis configurations."""
    
    @staticmethod
    def comprehensive():
        """Full analysis with all features."""
        return AnalysisConfig(
            detect_import_loops=True,
            detect_dead_code=True,
            generate_training_data=True,
            analyze_graph_structure=True,
            include_source_locations=True,
            include_metrics=True
        )
    
    @staticmethod
    def quality_focused():
        """Focus on code quality metrics."""
        return AnalysisConfig(
            detect_import_loops=True,
            detect_dead_code=True,
            generate_training_data=False,
            analyze_graph_structure=True,
            include_metrics=True
        )
    
    @staticmethod
    def performance():
        """Fast analysis with minimal features."""
        return AnalysisConfig(
            detect_import_loops=False,
            detect_dead_code=False,
            generate_training_data=False,
            analyze_graph_structure=True,
            use_advanced_config=False
        )
    
    @staticmethod
    def ml_training():
        """Generate training data for ML models."""
        return AnalysisConfig(
            detect_import_loops=False,
            detect_dead_code=False,
            generate_training_data=True,
            analyze_graph_structure=True,
            include_source_locations=True
        )

__all__ = [
    # Main analysis function
    'analyze_codebase',
    
    # Core classes
    'ComprehensiveAnalysisEngine',
    'AnalysisConfig',
    'AnalysisResult',
    
    # Enhanced data classes
    'ImportLoop',
    'TrainingDataItem', 
    'DeadCodeItem',
    'GraphAnalysisResult',
    'EnhancedFunctionMetrics',
    'EnhancedClassMetrics',
    
    # Preset configurations
    'AnalysisPresets',
    
    # ... existing exports ...
]

# Version info
__version__ = "2.0.0"
__author__ = "Graph-Sitter Analysis Team"
__description__ = "Enhanced comprehensive codebase analysis with graph-sitter integration"
