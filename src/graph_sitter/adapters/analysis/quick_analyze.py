#!/usr/bin/env python3
"""
Quick Analysis Entry Point

Provides simple, fast analysis functions for common use cases.
"""

import logging
from typing import Dict, List, Any, Optional

# Import with fallbacks for standalone usage
try:
    from .tools.unified_analyzer import UnifiedCodebaseAnalyzer
    from .core.models import create_default_analysis_options
except ImportError:
    # Fallback for standalone usage
    try:
        from tools.unified_analyzer import UnifiedCodebaseAnalyzer
        from core.models import create_default_analysis_options
    except ImportError:
        # Create minimal fallbacks for testing
        print("Warning: Core modules not available, using fallbacks")
        
        class UnifiedCodebaseAnalyzer:
            def __init__(self, **kwargs): 
                self.use_graph_sitter = kwargs.get('use_graph_sitter', False)
            
            def quick_analyze(self, path): 
                return {"error": "UnifiedCodebaseAnalyzer not available"}
            
            def analyze_codebase(self, path): 
                class Result:
                    def __init__(self):
                        self.issues = []
                        self.total_functions = 0
                        self.average_cyclomatic_complexity = 0
                        self.average_maintainability_index = 0
                        self.comment_density = 0
                        self.technical_debt_ratio = 0
                        self.total_lines = 0
                        self.function_metrics = []
                return Result()
            
            def analyze_dead_code(self, path):
                return {"dead_code_items": []}
            
            def analyze_import_loops(self, path):
                return {"import_loops": []}
            
            def get_enhanced_summary(self, path):
                return {"error": "Enhanced summary not available"}
        
        def create_default_analysis_options():
            class Options:
                def __init__(self):
                    self.max_complexity = 10
                    self.extensions = ['.py']
            return Options()

logger = logging.getLogger(__name__)


def quick_analyze(path: str, **kwargs) -> Dict[str, Any]:
    """
    Perform a quick analysis of a codebase.
    
    Args:
        path: Path to analyze
        **kwargs: Additional options (use_graph_sitter, extensions, etc.)
        
    Returns:
        Dictionary with basic analysis results
    """
    analyzer = UnifiedCodebaseAnalyzer(
        use_graph_sitter=kwargs.get('use_graph_sitter', True)
    )
    return analyzer.quick_analyze(path)


def analyze_complexity(path: str, max_complexity: int = 10) -> Dict[str, Any]:
    """
    Analyze codebase focusing on complexity issues.
    
    Args:
        path: Path to analyze
        max_complexity: Maximum allowed cyclomatic complexity
        
    Returns:
        Dictionary with complexity analysis results
    """
    options = create_default_analysis_options()
    options.max_complexity = max_complexity
    
    analyzer = UnifiedCodebaseAnalyzer()
    result = analyzer.analyze_codebase(path)
    
    # Filter for complexity-related issues
    complexity_issues = [
        issue for issue in result.issues 
        if hasattr(issue, 'type') and issue.type in ['complexity', 'maintainability']
    ]
    
    return {
        "total_functions": result.total_functions,
        "complexity_issues": len(complexity_issues),
        "average_complexity": result.average_cyclomatic_complexity,
        "high_complexity_functions": [
            f for f in result.function_metrics 
            if hasattr(f, 'cyclomatic_complexity') and f.cyclomatic_complexity > max_complexity
        ],
        "issues": [issue.__dict__ if hasattr(issue, '__dict__') else str(issue) for issue in complexity_issues]
    }


def analyze_quality_metrics(path: str) -> Dict[str, Any]:
    """
    Get basic quality metrics for a codebase.
    
    Args:
        path: Path to analyze
        
    Returns:
        Dictionary with quality metrics
    """
    analyzer = UnifiedCodebaseAnalyzer()
    result = analyzer.analyze_codebase(path)
    
    return {
        "maintainability_index": result.average_maintainability_index,
        "cyclomatic_complexity": result.average_cyclomatic_complexity,
        "halstead_volume": getattr(result, 'average_halstead_volume', 0),
        "comment_density": result.comment_density,
        "technical_debt_ratio": result.technical_debt_ratio,
        "total_issues": len(result.issues),
        "lines_of_code": result.total_lines
    }


def find_dead_code(path: str) -> List[Dict[str, Any]]:
    """
    Find potentially dead code in a codebase.
    
    Args:
        path: Path to analyze
        
    Returns:
        List of dead code items
    """
    analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=True)
    
    try:
        result = analyzer.analyze_dead_code(path)
        return result.get("dead_code_items", [])
    except Exception as e:
        logger.error(f"Error finding dead code: {e}")
        return []


def find_import_loops(path: str) -> List[Dict[str, Any]]:
    """
    Find circular import dependencies in a codebase.
    
    Args:
        path: Path to analyze
        
    Returns:
        List of import loops
    """
    analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=True)
    
    try:
        result = analyzer.analyze_import_loops(path)
        return result.get("import_loops", [])
    except Exception as e:
        logger.error(f"Error finding import loops: {e}")
        return []


def generate_ml_training_data(path: str) -> List[Dict[str, Any]]:
    """
    Generate training data for machine learning models.
    
    Args:
        path: Path to analyze
        
    Returns:
        List of training data items
    """
    analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=True)
    
    try:
        result = analyzer.analyze_training_data(path)
        return result.get("training_data", [])
    except Exception as e:
        logger.error(f"Error generating training data: {e}")
        return []


def get_codebase_summary(path: str) -> Dict[str, Any]:
    """
    Get a comprehensive summary of a codebase.
    
    Args:
        path: Path to analyze
        
    Returns:
        Dictionary with codebase summary
    """
    analyzer = UnifiedCodebaseAnalyzer()
    
    # Get basic analysis
    result = analyzer.analyze_codebase(path)
    summary = {
        "basic_metrics": {
            "total_files": result.total_files,
            "total_functions": result.total_functions,
            "total_classes": getattr(result, 'total_classes', 0),
            "total_lines": result.total_lines,
            "comment_density": result.comment_density
        },
        "quality_metrics": {
            "average_maintainability": result.average_maintainability_index,
            "average_complexity": result.average_cyclomatic_complexity,
            "technical_debt_ratio": result.technical_debt_ratio
        },
        "issues": {
            "total": len(result.issues),
            "critical": len([i for i in result.issues if hasattr(i, 'severity') and i.severity == "critical"]),
            "major": len([i for i in result.issues if hasattr(i, 'severity') and i.severity == "major"]),
            "minor": len([i for i in result.issues if hasattr(i, 'severity') and i.severity == "minor"])
        }
    }
    
    # Add enhanced metrics if graph-sitter is available
    try:
        enhanced_summary = analyzer.get_enhanced_summary(path)
        if "error" not in enhanced_summary:
            summary["enhanced_metrics"] = enhanced_summary
    except Exception as e:
        logger.debug(f"Could not get enhanced summary: {e}")
    
    return summary


# Convenience aliases for backward compatibility
analyze = quick_analyze
get_summary = get_codebase_summary

