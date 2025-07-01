"""
🚀 ANALYSIS MODULE 🚀

Simplified analysis capabilities for graph-sitter integration.
This module provides the core Analysis class and available analyzers.
"""

# Import the main Analysis class that provides the documentation API
from .analyzer import Analysis

# Import individual analyzers that exist
try:
    from .complexity_analyzer import (
        analyze_complexity,
        calculate_cyclomatic_complexity,
        find_complex_functions,
        find_large_functions
    )
    complexity_available = True
except ImportError:
    complexity_available = False

try:
    from .dependency_analyzer import (
        analyze_dependencies,
        detect_circular_dependencies,
        create_dependency_graph
    )
    dependency_available = True
except ImportError:
    dependency_available = False

try:
    from .security_analyzer import (
        analyze_security,
        detect_sql_injection,
        detect_hardcoded_secrets
    )
    security_available = True
except ImportError:
    security_available = False

try:
    from .dead_code_detector import (
        detect_dead_code,
        remove_dead_code
    )
    dead_code_available = True
except ImportError:
    dead_code_available = False

try:
    from .call_graph_analyzer import (
        analyze_call_graph,
        find_call_chains,
        find_hotspot_functions
    )
    call_graph_available = True
except ImportError:
    call_graph_available = False

# Export what's available
__all__ = ['Analysis']

# Add available analyzers to exports
if complexity_available:
    __all__.extend([
        'analyze_complexity',
        'calculate_cyclomatic_complexity', 
        'find_complex_functions',
        'find_large_functions'
    ])

if dependency_available:
    __all__.extend([
        'analyze_dependencies',
        'detect_circular_dependencies',
        'create_dependency_graph'
    ])

if security_available:
    __all__.extend([
        'analyze_security',
        'detect_sql_injection',
        'detect_hardcoded_secrets'
    ])

if dead_code_available:
    __all__.extend([
        'detect_dead_code',
        'remove_dead_code'
    ])

if call_graph_available:
    __all__.extend([
        'analyze_call_graph',
        'find_call_chains',
        'find_hotspot_functions'
    ])

# Module metadata
__version__ = "1.0.0"
__description__ = "Simplified graph-sitter analysis module"

# Feature availability information
FEATURES = {
    "core_analysis": True,
    "complexity_analysis": complexity_available,
    "dependency_analysis": dependency_available,
    "security_analysis": security_available,
    "dead_code_detection": dead_code_available,
    "call_graph_analysis": call_graph_available,
}

