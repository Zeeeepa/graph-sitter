"""
Simplified Graph-Sitter Adapter

This replaces the overcomplicated adapter system with simple imports
of graph-sitter's built-in capabilities and provides the user's requested API.
"""

# Core graph-sitter functionality (already implemented)
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.symbol import Symbol

# Import the Analysis class from core
try:
    from graph_sitter.core.analysis import Analysis
except ImportError:
    # Fallback to simplified analysis if core Analysis doesn't exist
    Analysis = None

# Import simplified analysis functions
from .analysis import (
    analyze_codebase,
    get_dead_code,
    remove_dead_code,
    get_call_graph,
    get_inheritance_hierarchy,
    get_dependencies,
    get_usages,
    find_recursive_functions,
    analyze_test_coverage,
    get_codebase_stats,
    visualize_call_graph,
    visualize_inheritance,
    visualize_dependencies,
    create_interactive_dashboard
)

# Essential visualization (keep only simple dashboard)
try:
    from .visualizations.dashboard import InteractiveDashboard
except ImportError:
    InteractiveDashboard = None

# Simple exports
__all__ = [
    'Codebase',
    'Function', 
    'Class',
    'Symbol',
    'Analysis',
    'analyze_codebase',
    'get_dead_code',
    'remove_dead_code',
    'get_call_graph',
    'get_inheritance_hierarchy',
    'get_dependencies',
    'get_usages',
    'find_recursive_functions',
    'analyze_test_coverage',
    'get_codebase_stats',
    'visualize_call_graph',
    'visualize_inheritance',
    'visualize_dependencies',
    'create_interactive_dashboard',
    'InteractiveDashboard'
]


def analyze_codebase(repo_path: str) -> dict:
    """
    Simple codebase analysis using graph-sitter's built-in capabilities.
    
    This replaces all the complex analyzer classes with simple property access.
    """
    # Use the simplified pattern
    codebase = Codebase(repo_path)
    
    # Simple analysis using built-in properties
    stats = {
        'total_files': len(codebase.files),
        'total_functions': len(codebase.functions),
        'total_classes': len(codebase.classes),
        'total_imports': len(codebase.imports)
    }
    
    # Simple issue detection using built-in properties
    issues = []
    
    # Unused functions (instant lookup)
    for func in codebase.functions:
        if not func.usages and not func.name.startswith('_'):
            issues.append({
                'type': 'unused_function',
                'severity': 'high',
                'description': f"Function '{func.name}' is unused",
                'location': f"{func.file.filepath}:{func.line_number}"
            })
    
    return {'stats': stats, 'issues': issues}


def get_dead_code(repo_path: str) -> list:
    """
    Get dead code using graph-sitter's simple pattern.
    
    This is the exact pattern from graph-sitter.com documentation.
    """
    codebase = Codebase(repo_path)
    return [f.name for f in codebase.functions if not f.usages]


def remove_dead_code(repo_path: str):
    """
    Remove dead code using graph-sitter's built-in removal.
    
    This is the exact pattern from graph-sitter.com documentation.
    """
    codebase = Codebase(repo_path)
    for function in codebase.functions:
        if not function.usages:
            function.remove()
    codebase.commit()


# User's requested API patterns
class CodebaseAnalysisAPI:
    """
    Provides the user's requested API patterns:
    - Codebase.from_repo.Analysis('repo/name')
    - Codebase.Analysis('path/to/repo')
    """
    
    @staticmethod
    def from_repo_analysis(repo_name: str):
        """Clone + parse from repository with analysis."""
        codebase = Codebase.from_repo(repo_name)
        if Analysis:
            return Analysis(codebase)
        else:
            # Fallback to simple analysis
            return analyze_codebase(str(codebase.repo_path))
    
    @staticmethod
    def local_analysis(repo_path: str):
        """Parse local repository with analysis."""
        if Analysis:
            codebase = Codebase(repo_path)
            return Analysis(codebase)
        else:
            # Fallback to simple analysis
            return analyze_codebase(repo_path)


# Monkey patch to provide user's requested API
# This enables: Codebase.from_repo.Analysis('repo/name')
if hasattr(Codebase, 'from_repo'):
    Codebase.from_repo.Analysis = CodebaseAnalysisAPI.from_repo_analysis

# This enables: Codebase.Analysis('path/to/repo')  
Codebase.Analysis = CodebaseAnalysisAPI.local_analysis
