"""Graph-Sitter refactored analysis package.

Import components individually:
    from src.analysis_utils import AnalysisError
    from src.graph_sitter_adapter import GraphSitterAdapter
    from src.lib_analysis import AnalysisOrchestrator
    
Or use lazy imports:
    from src import lazy_import
    GraphSitterAdapter = lazy_import('graph_sitter_adapter', 'GraphSitterAdapter')
"""

__version__ = "2.0.0-alpha"

# Don't do eager imports - causes circular dependency issues
# Import modules individually as needed

__all__ = [
    "__version__",
]
