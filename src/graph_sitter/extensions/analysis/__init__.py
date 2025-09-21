#!/usr/bin/env python3
"""
Comprehensive Code Analysis Extension for Graph-Sitter

This module provides enterprise-grade code analysis capabilities including:
- 40+ static analysis tools integration
- Real-time LSP diagnostics  
- AI-powered error fixing via AutoGenLib
- Interactive analysis CLI
- Comprehensive reporting (HTML/JSON/terminal)
- Analysis history and metrics tracking

Usage:
    from graph_sitter.extensions.analysis import ComprehensiveAnalyzer
    
    analyzer = ComprehensiveAnalyzer("/path/to/code")
    results = analyzer.run_comprehensive_analysis()
"""

__version__ = "1.0.0"
__author__ = "Graph-Sitter Analysis Team"

# Import main analysis components
try:
    from .comprehensive import ComprehensiveAnalyzer
    from .database import ErrorDatabase, AnalysisError
    
    # Make key classes available at package level
    __all__ = [
        "ComprehensiveAnalyzer",
        "ErrorDatabase", 
        "AnalysisError",
    ]
    
    ANALYSIS_AVAILABLE = True
    
except ImportError as e:
    # Graceful degradation if optional dependencies not installed
    ANALYSIS_AVAILABLE = False
    __all__ = []
    
    def ComprehensiveAnalyzer(*args, **kwargs):
        raise ImportError(
            f"Comprehensive analysis not available: {e}\n"
            "Install with: pip install graph-sitter[analysis]"
        )

# Configuration and feature flags
FEATURES = {
    "comprehensive_analysis": ANALYSIS_AVAILABLE,
    "ai_fixing": False,  # Set to True when AutoGenLib integration is complete
    "lsp_diagnostics": False,  # Set to True when LSP integration is complete
    "interactive_mode": ANALYSIS_AVAILABLE,
    "reporting": ANALYSIS_AVAILABLE,
}

def get_analysis_info():
    """Get information about available analysis features."""
    return {
        "version": __version__,
        "available": ANALYSIS_AVAILABLE,
        "features": FEATURES,
        "tools_supported": [
            "ruff", "mypy", "pyright", "pylint", "bandit", 
            "safety", "semgrep", "vulture", "radon", "xenon",
            "black", "isort", "pydocstyle", "pyflakes", 
            "pycodestyle", "mccabe"
        ] if ANALYSIS_AVAILABLE else [],
    }