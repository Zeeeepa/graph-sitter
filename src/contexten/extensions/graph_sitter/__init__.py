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

# Export all main components
__all__ = [
    # Main classes
    'Analysis',
    'Visualize', 
    'Resolve',
    
    # Analysis functions
    'get_codebase_summary',
    'get_file_summary',
    'get_class_summary', 
    'get_function_summary',
    'get_symbol_summary',
    'get_optimized_config',
    
    # Data classes
    'CodebaseMetrics',
    'FunctionMetrics',
    'ClassMetrics',
    'FileMetrics'
]

# Version info
__version__ = "1.0.0"
__author__ = "Graph-Sitter Extensions"
__description__ = """
Consolidated Tree-sitter analysis, visualization, and resolution features.

This module provides comprehensive codebase analysis capabilities using Tree-sitter
parsing with advanced graph-based insights, interactive visualizations, and 
sophisticated symbol resolution.

Key Features:
- Pre-computed graph element access (functions, classes, imports, files, symbols)
- Advanced function analysis (usages, call sites, dependencies, decorators)
- Class hierarchy analysis (inheritance, methods, attributes)
- Import relationship analysis (inbound/outbound imports, external modules)
- Interactive visualizations (charts, dependency graphs, heatmaps)
- Symbol resolution and dependency tracking
- Comprehensive reporting (HTML, JSON, text formats)
- Performance-optimized configuration
- Tree-sitter best practices implementation

Based on official Tree-sitter documentation and patterns from:
- https://tree-sitter.github.io/tree-sitter/
- https://tree-sitter.github.io/tree-sitter/creating-parsers
- https://tree-sitter.github.io/tree-sitter/using-parsers
"""

