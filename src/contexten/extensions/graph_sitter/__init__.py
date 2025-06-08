"""
Graph-Sitter Extensions

Consolidated Tree-sitter analysis, visualization, and resolution features
based on official Tree-sitter documentation and advanced graph-based analysis.

This module provides a unified interface to all graph-sitter extension capabilities:
- Analysis: Comprehensive codebase analysis with Tree-sitter integration
- Visualize: Interactive charts, graphs, and reports
- Resolve: Symbol resolution, import analysis, and dependency tracking

Usage:
    from contexten.extensions.graph_sitter import Analysis, Visualize, Resolve
    from contexten.extensions.graph_sitter.analysis.codebase_analysis import (
        get_codebase_summary, get_file_summary, get_class_summary, 
        get_function_summary, get_symbol_summary, get_optimized_config
    )
    
    # Create optimized codebase configuration
    config = get_optimized_config()
    codebase = Codebase(path="./my_project", config=config)
    
    # Initialize analysis modules
    analysis = Analysis(codebase)
    visualize = Visualize(codebase)
    resolve = Resolve(codebase)
    
    # Access pre-computed graph elements (as requested)
    functions = codebase.functions        # All functions in codebase
    classes = codebase.classes           # All classes
    imports = codebase.imports           # All import statements
    files = codebase.files               # All files
    symbols = codebase.symbols           # All symbols
    external_modules = codebase.external_modules  # External dependencies
    
    # Advanced function analysis
    for function in codebase.functions:
        function.usages           # All usage sites
        function.call_sites       # All call locations
        function.dependencies     # Function dependencies
        function.function_calls   # Functions this function calls
        function.parameters       # Function parameters
        function.return_statements # Return statements
        function.decorators       # Function decorators
        function.is_async         # Async function detection
        function.is_generator     # Generator function detection
    
    # Class hierarchy analysis
    for cls in codebase.classes:
        cls.superclasses         # Parent classes
        cls.subclasses          # Child classes
        cls.methods             # Class methods
        cls.attributes          # Class attributes
        cls.decorators          # Class decorators
        cls.usages              # Class usage sites
        cls.dependencies        # Class dependencies
        cls.is_abstract         # Abstract class detection
    
    # Import relationship analysis
    for file in codebase.files:
        file.imports            # Outbound imports
        file.inbound_imports    # Files that import this file
        file.symbols            # Symbols defined in file
        file.external_modules   # External dependencies
"""

# Import our extension modules
from .analysis import Analysis
from .visualize import Visualize
from .resolve import Resolve

# Import key functions for direct access
from .analysis.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    get_optimized_config,
    CodebaseMetrics,
    FunctionMetrics,
    ClassMetrics,
    FileMetrics
)

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
