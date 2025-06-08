"""
Graph_Sitter Extension for Contexten

Comprehensive codebase analysis using the actual graph_sitter API.
Provides real issue detection, complexity analysis, security scanning, and more.

Main Components:
- dead_code_detector: Find and remove unused code
- complexity_analyzer: Analyze cyclomatic complexity and maintainability
- dependency_analyzer: Analyze imports and circular dependencies  
- security_analyzer: Detect security vulnerabilities
- call_graph_analyzer: Analyze function call relationships
- main_analyzer: Comprehensive analysis combining all modules

Usage:
    from contexten.extensions.graph_sitter import comprehensive_analysis
    from graph_sitter import Codebase
    
    # Run comprehensive analysis
    codebase = Codebase("./my_project")
    results = comprehensive_analysis(codebase)
    
    # Or run individual analyzers
    from contexten.extensions.graph_sitter.analysis.dead_code_detector import detect_dead_code
    dead_code_results = detect_dead_code(codebase)
"""

# Import main analysis functions for easy access
from .analysis.main_analyzer import comprehensive_analysis, print_analysis_summary, save_analysis_report

# Import individual analyzers
from .analysis.dead_code_detector import detect_dead_code, remove_dead_code
from .analysis.complexity_analyzer import analyze_complexity, find_complex_functions, find_large_functions
from .analysis.dependency_analyzer import analyze_dependencies, detect_circular_dependencies, analyze_module_coupling
from .analysis.security_analyzer import analyze_security, check_import_security
from .analysis.call_graph_analyzer import analyze_call_graph, find_hotspot_functions

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
    'find_hotspot_functions'
]

# Version info
__version__ = "1.0.0"
__description__ = "Comprehensive codebase analysis using graph_sitter API"

