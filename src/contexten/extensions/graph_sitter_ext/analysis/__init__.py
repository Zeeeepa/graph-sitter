"""
Graph-Sitter Analysis Module

Comprehensive analysis capabilities for graph-sitter with advanced features:
- Import loop detection and circular dependency analysis
- Dead code detection using usage analysis
- Enhanced function and class metrics
- Security analysis and vulnerability detection
- Call graph analysis
- Complexity analysis
"""

# Import the main analyzer class that actually exists
try:
    from .analyzer import Analysis
    _analyzer_available = True
except ImportError as e:
    _analyzer_available = False
    print(f"Warning: Main analyzer not available: {e}")

# Import complexity analysis functions
try:
    from .complexity_analyzer import (
        calculate_cyclomatic_complexity,
        calculate_halstead_volume,
        calculate_maintainability_index,
        analyze_complexity,
        find_complex_functions,
        find_large_functions
    )
    _complexity_available = True
except ImportError as e:
    _complexity_available = False
    print(f"Warning: Complexity analyzer not available: {e}")

# Import dependency analysis functions
try:
    from .dependency_analyzer import (
        analyze_dependencies,
        create_dependency_graph,
        analyze_module_coupling
    )
    _dependency_available = True
except ImportError as e:
    _dependency_available = False
    print(f"Warning: Dependency analyzer not available: {e}")

# Import security analysis functions
try:
    from .security_analyzer import (
        analyze_security,
        detect_sql_injection,
        detect_hardcoded_secrets,
        detect_unsafe_eval,
        detect_insecure_random
    )
    _security_available = True
except ImportError as e:
    _security_available = False
    print(f"Warning: Security analyzer not available: {e}")

# Import call graph analysis functions
try:
    from .call_graph_analyzer import (
        analyze_call_graph,
        find_call_chains,
        create_downstream_call_trace
    )
    _call_graph_available = True
except ImportError as e:
    _call_graph_available = False
    print(f"Warning: Call graph analyzer not available: {e}")

# Import dead code detection functions
try:
    from .dead_code_detector import (
        detect_dead_code,
        remove_dead_code
    )
    _dead_code_available = True
except ImportError as e:
    _dead_code_available = False
    print(f"Warning: Dead code detector not available: {e}")

# Enhanced analyzer functions
try:
    from .enhanced_analyzer import enhanced_comprehensive_analysis
    _enhanced_available = True
except ImportError as e:
    print(f"Warning: Enhanced analyzer not available: {e}")
    enhanced_comprehensive_analysis = None
    _enhanced_available = False

# Export what's actually available
__all__ = []

if _analyzer_available:
    __all__.extend(['Analysis'])

if _complexity_available:
    __all__.extend([
        'calculate_cyclomatic_complexity', 'calculate_halstead_volume',
        'calculate_maintainability_index', 'analyze_complexity',
        'find_complex_functions', 'find_large_functions'
    ])

if _dependency_available:
    __all__.extend([
        'analyze_dependencies', 'create_dependency_graph', 'analyze_module_coupling'
    ])

if _security_available:
    __all__.extend([
        'analyze_security', 'detect_sql_injection', 'detect_hardcoded_secrets',
        'detect_unsafe_eval', 'detect_insecure_random'
    ])

if _call_graph_available:
    __all__.extend([
        'analyze_call_graph', 'find_call_chains', 'create_downstream_call_trace'
    ])

if _dead_code_available:
    __all__.extend([
        'detect_dead_code', 'remove_dead_code'
    ])

if _enhanced_available:
    __all__.extend(['EnhancedCodebaseAnalyzer'])

# Aliases for backward compatibility
CodebaseAnalyzer = Analysis if _analyzer_available else None

def get_analysis_status():
    """Get the status of all analysis components."""
    return {
        'analyzer': _analyzer_available,
        'complexity': _complexity_available,
        'dependency': _dependency_available,
        'security': _security_available,
        'call_graph': _call_graph_available,
        'dead_code': _dead_code_available,
        'enhanced': _enhanced_available,
    }

__all__.append('get_analysis_status')
