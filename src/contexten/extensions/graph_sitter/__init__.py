"""
Graph-Sitter Extensions

Simplified entry point for working graph-sitter functionality.
"""

# Import the main Analysis class that works
try:
    from .analysis import Analysis
    ANALYSIS_AVAILABLE = True
except ImportError:
    Analysis = None
    ANALYSIS_AVAILABLE = False

# Try to import Visualize module
try:
    from .visualize import Visualize
    VISUALIZE_AVAILABLE = True
except ImportError:
    Visualize = None
    VISUALIZE_AVAILABLE = False

# Try to import Resolve module
try:
    from .resolve import Resolve
    RESOLVE_AVAILABLE = True
except ImportError:
    Resolve = None
    RESOLVE_AVAILABLE = False

# Try to import the renamed main extension class
try:
    from .contexten_graph_sitter import GraphSitter
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GraphSitter = None
    GRAPH_SITTER_AVAILABLE = False

# Export what's available
__all__ = []

if Analysis:
    __all__.append('Analysis')
if Visualize:
    __all__.append('Visualize')
if Resolve:
    __all__.append('Resolve')
if GraphSitter:
    __all__.append('GraphSitter')

# Convenience functions for quick access
def quick_analysis(path: str, **kwargs):
    """Quick analysis with default configuration."""
    if not Analysis:
        raise ImportError("Analysis module not available")
    
    from graph_sitter import Codebase
    codebase = Codebase(path)
    return Analysis(codebase)

def create_analyzer(path: str, config=None):
    """Create an analyzer instance."""
    if not Analysis:
        raise ImportError("Analysis module not available")
    
    from graph_sitter import Codebase
    codebase = Codebase(path, config=config)
    return Analysis(codebase)

# Version info
__version__ = "1.0.0"
__description__ = "Simplified graph-sitter extensions"

# Feature availability
FEATURES = {
    "analysis": ANALYSIS_AVAILABLE,
    "visualize": VISUALIZE_AVAILABLE,
    "resolve": RESOLVE_AVAILABLE,
    "graph_sitter_extension": GRAPH_SITTER_AVAILABLE,
}

