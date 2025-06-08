"""
Graph-Sitter Extensions

Clean 4-module architecture for graph-sitter functionality:
1. Core - Configuration and base classes
2. Analysis - Code analysis capabilities
3. Visualize - Code visualization features  
4. Resolve - Symbol resolution and auto-fix using graph_sitter's robust code context
"""

# Note: This module should be imported as contexten.extensions.graph_sitter_ext
# to avoid conflicts with the actual graph_sitter library

def get_module_status():
    """Get the status of all modules for debugging."""
    status = {}
    
    # Test Core module
    try:
        from .core import CodebaseConfig, PresetConfigs
        status['core'] = True
    except ImportError:
        status['core'] = False
    
    # Test Analysis module
    try:
        from .analysis import Analysis, get_analysis_status
        analysis_status = get_analysis_status()
        status['analysis'] = analysis_status
    except ImportError:
        status['analysis'] = False
    
    # Test Visualize module
    try:
        from .visualize import Visualize
        status['visualize'] = True
    except ImportError:
        status['visualize'] = False
    
    # Test Resolve module
    try:
        from .resolve import Resolve, EnhancedResolver
        status['resolve'] = True
    except ImportError:
        status['resolve'] = False
    
    return status

def get_working_imports():
    """Get a list of working imports for easy access."""
    imports = {}
    
    # Core imports
    try:
        from .core import CodebaseConfig, PresetConfigs
        imports['core'] = ['CodebaseConfig', 'PresetConfigs']
    except ImportError:
        imports['core'] = []
    
    # Analysis imports
    try:
        from .analysis import (
            Analysis,
            calculate_cyclomatic_complexity,
            calculate_halstead_volume,
            calculate_maintainability_index,
            analyze_complexity,
            analyze_dependencies,
            create_dependency_graph,
            analyze_security,
            detect_sql_injection,
            detect_hardcoded_secrets,
            analyze_call_graph,
            find_call_chains,
            detect_dead_code,
            remove_dead_code
        )
        imports['analysis'] = [
            'Analysis', 'calculate_cyclomatic_complexity', 'calculate_halstead_volume',
            'calculate_maintainability_index', 'analyze_complexity', 'analyze_dependencies',
            'create_dependency_graph', 'analyze_security', 'detect_sql_injection',
            'detect_hardcoded_secrets', 'analyze_call_graph', 'find_call_chains',
            'detect_dead_code', 'remove_dead_code'
        ]
    except ImportError:
        imports['analysis'] = []
    
    # Visualize imports
    try:
        from .visualize import Visualize
        imports['visualize'] = ['Visualize']
    except ImportError:
        imports['visualize'] = []
    
    # Resolve imports
    try:
        from .resolve import Resolve, EnhancedResolver
        imports['resolve'] = ['Resolve', 'EnhancedResolver']
    except ImportError:
        imports['resolve'] = []
    
    return imports

# For convenience, expose the main classes directly
try:
    from .core import CodebaseConfig
except ImportError:
    CodebaseConfig = None

try:
    from .analysis import Analysis
except ImportError:
    Analysis = None

try:
    from .visualize import Visualize
except ImportError:
    Visualize = None

try:
    from .resolve import Resolve
except ImportError:
    Resolve = None

__all__ = ['get_module_status', 'get_working_imports', 'CodebaseConfig', 'Analysis', 'Visualize', 'Resolve']

