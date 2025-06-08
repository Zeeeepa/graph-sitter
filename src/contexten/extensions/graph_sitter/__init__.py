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

# Import individual analyzers
from .analysis.dead_code_detector import detect_dead_code, remove_dead_code
from .analysis.complexity_analyzer import analyze_complexity, find_complex_functions, find_large_functions
from .analysis.dependency_analyzer import analyze_dependencies, detect_circular_dependencies, analyze_module_coupling
from .analysis.security_analyzer import analyze_security, check_import_security
from .analysis.call_graph_analyzer import analyze_call_graph, find_hotspot_functions

# Import advanced configuration features
from .analysis.advanced_config import (
    AdvancedCodebaseConfig,
    create_debug_config,
    create_performance_config,
    create_comprehensive_analysis_config,
    create_typescript_analysis_config,
    create_ast_only_config,
    analyze_with_advanced_config
)
from .analysis.enhanced_analyzer import enhanced_comprehensive_analysis
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
    
    # Dead code analysis
    'detect_dead_code',
    'remove_dead_code',
    
    # Complexity analysis
    'analyze_complexity',
    'find_complex_functions',
    'find_large_functions',
    
    # Dependency analysis
    'analyze_dependencies',
    'detect_circular_dependencies',
    'analyze_module_coupling',
    
    # Security analysis
    'analyze_security',
    'check_import_security',
    
    # Call graph analysis
    'analyze_call_graph',
    'find_hotspot_functions',
    
    # Advanced configuration
    'AdvancedCodebaseConfig',
    'create_debug_config',
    'create_performance_config',
    'create_comprehensive_analysis_config',
    'create_typescript_analysis_config',
    'create_ast_only_config',
    'analyze_with_advanced_config',
    'enhanced_comprehensive_analysis',
    'ConfigurationManager'
]

# Version info
__version__ = "1.0.0"
__description__ = "Comprehensive codebase analysis using graph_sitter API"
