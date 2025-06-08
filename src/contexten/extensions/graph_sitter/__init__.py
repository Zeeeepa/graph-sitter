"""
Graph-Sitter Extensions

Consolidated entry point for all graph-sitter functionality.
Based on the official graph-sitter.com API and features.
"""

# Core configuration
from .core import CodebaseConfig, PresetConfigs

# Analysis module - comprehensive code analysis
from .analysis import (
    # Main API functions
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    
    # Pre-computed graph element access
    CodebaseElements,
    
    # Data classes
    CodebaseSummary,
    FileSummary,
    ClassSummary,
    FunctionSummary,
    SymbolSummary,
    
    # Analyzers
    CodebaseAnalyzer,
    EnhancedCodebaseAnalyzer,
    ComplexityAnalyzer,
    DependencyAnalyzer,
    SecurityAnalyzer,
    CallGraphAnalyzer,
    DeadCodeDetector,
)

# Visualization module
from .visualize import Visualize

# Resolve module - symbol resolution and import analysis
from .resolve import (
    Resolve,
    EnhancedResolver,
    ResolvedSymbol,
    ImportRelationship,
)

# Import the three main extension modules
from .analysis import Analysis
from .visualize import Visualize
from .resolve import Resolve

# Import main analysis functions for easy access
from .analysis.main_analyzer import comprehensive_analysis, print_analysis_summary, save_analysis_report

# Import legacy compatibility
from .code_analysis import ComprehensiveAnalysisEngine, CodeAnalysisEngine

# Import advanced configuration features
from .analysis.advanced_config import (
    AdvancedAnalysisConfig,
    PerformanceConfig,
    SecurityConfig,
    QualityConfig,
    create_custom_config,
    load_config_from_file,
    save_config_to_file,
    validate_config,
    merge_configs,
    get_default_config,
    get_performance_config,
    get_security_config,
    get_quality_config,
    ADVANCED_CONFIG_AVAILABLE,
)

# Import individual analyzers for granular control
from .analysis.dead_code_detector import detect_dead_code, DeadCodeDetector
from .analysis.complexity_analyzer import analyze_complexity, ComplexityAnalyzer
from .analysis.dependency_analyzer import analyze_dependencies, DependencyAnalyzer
from .analysis.security_analyzer import analyze_security, SecurityAnalyzer
from .analysis.call_graph_analyzer import analyze_call_graph, CallGraphAnalyzer

# Import configuration manager
from .analysis.config_manager import ConfigurationManager

__all__ = [
    # Core configuration
    'CodebaseConfig',
    'PresetConfigs',
    
    # Main API functions (as requested by user)
    'get_codebase_summary',
    'get_file_summary',
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    
    # Pre-computed graph element access
    'CodebaseElements',
    
    # Data classes
    'CodebaseSummary',
    'FileSummary',
    'ClassSummary',
    'FunctionSummary',
    'SymbolSummary',
    
    # Analyzers
    'CodebaseAnalyzer',
    'EnhancedCodebaseAnalyzer',
    'ComplexityAnalyzer',
    'DependencyAnalyzer',
    'SecurityAnalyzer',
    'CallGraphAnalyzer',
    'DeadCodeDetector',
    
    # Visualization
    'Visualize',
    
    # Resolution
    'Resolve',
    'EnhancedResolver',
    'ResolvedSymbol',
    'ImportRelationship',
    
    # Legacy compatibility (existing modules)
    'Analysis',
    'Visualize', 
    'Resolve',
    
    # Main analysis functions
    'comprehensive_analysis',
    'print_analysis_summary', 
    'save_analysis_report',
    
    # Legacy compatibility
    'ComprehensiveAnalysisEngine',
    'CodeAnalysisEngine',
    
    # Individual analyzers
    'detect_dead_code',
    'analyze_complexity',
    'analyze_dependencies',
    'analyze_security',
    'analyze_call_graph',
    
    # Advanced configuration
    'AdvancedAnalysisConfig',
    'PerformanceConfig',
    'SecurityConfig',
    'QualityConfig',
    'create_custom_config',
    'load_config_from_file',
    'save_config_to_file',
    'validate_config',
    'merge_configs',
    'get_default_config',
    'get_performance_config',
    'get_security_config',
    'get_quality_config',
    'ADVANCED_CONFIG_AVAILABLE',
    
    # Configuration management
    'ConfigurationManager',
]

# Convenience functions for quick access
def quick_analysis(path: str, **kwargs):
    """Quick analysis with default configuration."""
    return comprehensive_analysis(path, **kwargs)

def create_analyzer(path: str, config=None):
    """Create a comprehensive analyzer instance."""
    if config is None:
        config = get_default_config()
    return ComprehensiveAnalysisEngine(path, config)

# Version info
__version__ = "1.0.0"
__description__ = "Comprehensive codebase analysis using graph_sitter API"

