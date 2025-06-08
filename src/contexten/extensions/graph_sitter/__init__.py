"""
Graph-Sitter Extensions

Consolidated entry point for all graph-sitter functionality.
Based on the official graph-sitter.com API and features.

Comprehensive codebase analysis using the actual graph_sitter API.
Provides real issue detection, complexity analysis, security scanning, and more.

Main Components:
- Analysis: Comprehensive codebase analysis and summary functions
- Visualize: Code visualization and graph representation
- Resolve: Symbol resolution and import relationship analysis
- dead_code_detector: Find and remove unused code
- complexity_analyzer: Analyze cyclomatic complexity and maintainability
- dependency_analyzer: Analyze imports and circular dependencies  
- security_analyzer: Detect security vulnerabilities
- call_graph_analyzer: Analyze function call relationships
- main_analyzer: Comprehensive analysis combining all modules

Usage:
    from contexten.extensions.graph_sitter import comprehensive_analysis, Analysis, Visualize, Resolve
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    
    # Create advanced config
    config = CodebaseConfig(
        method_usages=True,
        generics=True,
        sync_enabled=True,
        full_range_index=True,
        py_resolve_syspath=True,
        exp_lazy_graph=False,
    )
    
    # Run comprehensive analysis
    codebase = Codebase("./my_project", config=config)
    results = comprehensive_analysis(codebase)
    
    # Use extension modules
    analysis = Analysis(codebase)
    visualizer = Visualize(codebase)
    resolver = Resolve(codebase)
    
    # Access pre-computed graph elements (as per documentation)
    analysis.functions    # All functions in codebase
    analysis.classes      # All classes
    analysis.imports      # All import statements
    analysis.files        # All files
    analysis.symbols      # All symbols
    analysis.external_modules  # External dependencies
"""

# Import legacy compatibility
from .code_analysis import ComprehensiveAnalysisEngine, CodeAnalysisEngine

# Import the three main extension modules
from .analysis import Analysis
from .visualize import Visualize
from .resolve import Resolve

# Import main analysis functions for easy access
from .analysis.main_analyzer import comprehensive_analysis, print_analysis_summary, save_analysis_report

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
    # Legacy compatibility
    'ComprehensiveAnalysisEngine',
    'CodeAnalysisEngine',
    
    # Main extension modules
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

