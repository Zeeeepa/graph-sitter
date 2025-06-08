"""
Simple analysis implementation using Graph-Sitter's built-in capabilities.

This module provides a clean, lightweight analysis API that leverages
Graph-Sitter's pre-computed relationships and indexes instead of
reimplementing complex analysis logic.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


@dataclass
class AnalysisResult:
    """Simple analysis result using Graph-Sitter's built-in data."""
    health_score: float
    total_functions: int
    total_classes: int
    total_files: int
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    dead_code_items: List[Dict[str, Any]]
    export_paths: Dict[str, str]


def analyze_codebase(codebase, output_dir: str = "analysis_output") -> AnalysisResult:
    """
    Perform comprehensive analysis using Graph-Sitter's built-in capabilities.
    
    This replaces our complex analysis pipeline with simple API calls to
    Graph-Sitter's pre-computed relationships and indexes.
    
    Args:
        codebase: Graph-Sitter Codebase instance
        output_dir: Directory to save analysis results
        
    Returns:
        AnalysisResult with comprehensive analysis data
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Use Graph-Sitter's built-in capabilities for analysis
    functions = list(codebase.functions)
    classes = list(codebase.classes)
    files = list(codebase.files)
    
    # Dead code detection using Graph-Sitter's usage tracking
    dead_code_items = []
    for function in functions:
        if not function.usages:  # Graph-Sitter pre-computes usages
            dead_code_items.append({
                "name": function.name,
                "type": "function",
                "filepath": function.filepath,
                "reason": "No usages found"
            })
    
    for class_def in classes:
        if not class_def.usages:  # Graph-Sitter pre-computes usages
            dead_code_items.append({
                "name": class_def.name,
                "type": "class", 
                "filepath": class_def.filepath,
                "reason": "No usages found"
            })
    
    # Calculate health score based on simple metrics
    total_symbols = len(functions) + len(classes)
    dead_code_count = len(dead_code_items)
    
    # Simple health calculation
    if total_symbols == 0:
        health_score = 1.0
    else:
        dead_code_ratio = dead_code_count / total_symbols
        health_score = max(0.0, 1.0 - dead_code_ratio)
    
    # Generate issues based on findings
    issues = []
    if dead_code_count > 0:
        issues.append({
            "type": "dead_code",
            "severity": "medium" if dead_code_count > 5 else "low",
            "description": f"Found {dead_code_count} unused symbols",
            "suggestion": "Consider removing unused functions and classes"
        })
    
    if health_score < 0.7:
        issues.append({
            "type": "code_quality",
            "severity": "medium",
            "description": f"Low health score: {health_score:.2f}",
            "suggestion": "Review and clean up codebase"
        })
    
    # Generate recommendations
    recommendations = []
    if dead_code_count > 0:
        recommendations.append(f"Remove {dead_code_count} unused symbols to improve codebase cleanliness")
    
    if len(functions) > 100:
        recommendations.append("Consider breaking down large modules for better maintainability")
    
    if health_score > 0.8:
        recommendations.append("Codebase is in good health - maintain current practices")
    
    # Create analysis summary
    analysis_summary = {
        "codebase_id": f"analysis_{output_dir.replace('/', '_')}",
        "health_score": health_score,
        "total_functions": len(functions),
        "total_classes": len(classes),
        "total_files": len(files),
        "dead_code_count": dead_code_count,
        "issues": issues,
        "recommendations": recommendations,
        "dead_code_items": dead_code_items
    }
    
    # Save analysis results
    export_paths = {}
    
    # Save main analysis
    analysis_path = output_path / "analysis_summary.json"
    with open(analysis_path, "w") as f:
        json.dump(analysis_summary, f, indent=2)
    export_paths["analysis_summary"] = str(analysis_path)
    
    # Save function details using Graph-Sitter's data
    function_details = []
    for func in functions:
        function_details.append({
            "name": func.name,
            "filepath": func.filepath,
            "has_usages": bool(func.usages),
            "usage_count": len(func.usages) if func.usages else 0,
            "dependencies": [dep.name for dep in func.dependencies] if func.dependencies else [],
            "source_preview": func.source[:200] + "..." if len(func.source) > 200 else func.source
        })
    
    functions_path = output_path / "functions.json"
    with open(functions_path, "w") as f:
        json.dump(function_details, f, indent=2)
    export_paths["functions"] = str(functions_path)
    
    # Save class details using Graph-Sitter's data
    class_details = []
    for cls in classes:
        class_details.append({
            "name": cls.name,
            "filepath": cls.filepath,
            "has_usages": bool(cls.usages),
            "usage_count": len(cls.usages) if cls.usages else 0,
            "methods": [method.name for method in cls.methods] if hasattr(cls, 'methods') else [],
            "source_preview": cls.source[:200] + "..." if len(cls.source) > 200 else cls.source
        })
    
    classes_path = output_path / "classes.json"
    with open(classes_path, "w") as f:
        json.dump(class_details, f, indent=2)
    export_paths["classes"] = str(classes_path)
    
    return AnalysisResult(
        health_score=health_score,
        total_functions=len(functions),
        total_classes=len(classes),
        total_files=len(files),
        issues=issues,
        recommendations=recommendations,
        dead_code_items=dead_code_items,
        export_paths=export_paths
    )


def find_circular_dependencies(codebase) -> List[List[str]]:
    """
    Find circular dependencies using Graph-Sitter's dependency graph.
    
    Args:
        codebase: Graph-Sitter Codebase instance
        
    Returns:
        List of circular dependency chains
    """
    # Use Graph-Sitter's pre-computed dependency relationships
    circular_deps = []
    
    # Simple cycle detection using Graph-Sitter's dependencies
    visited = set()
    rec_stack = set()
    
    def has_cycle(symbol, path):
        if symbol.name in rec_stack:
            # Found a cycle
            cycle_start = path.index(symbol.name)
            return path[cycle_start:]
        
        if symbol.name in visited:
            return None
            
        visited.add(symbol.name)
        rec_stack.add(symbol.name)
        path.append(symbol.name)
        
        # Check dependencies using Graph-Sitter's pre-computed data
        if hasattr(symbol, 'dependencies') and symbol.dependencies:
            for dep in symbol.dependencies:
                cycle = has_cycle(dep, path.copy())
                if cycle:
                    return cycle
        
        rec_stack.remove(symbol.name)
        return None
    
    # Check all symbols for cycles
    for symbol in list(codebase.functions) + list(codebase.classes):
        if symbol.name not in visited:
            cycle = has_cycle(symbol, [])
            if cycle:
                circular_deps.append(cycle)
    
    return circular_deps


def get_call_graph_stats(codebase) -> Dict[str, Any]:
    """
    Get call graph statistics using Graph-Sitter's relationships.
    
    Args:
        codebase: Graph-Sitter Codebase instance
        
    Returns:
        Dictionary with call graph statistics
    """
    functions = list(codebase.functions)
    
    # Use Graph-Sitter's pre-computed usage data
    total_calls = sum(len(func.usages) if func.usages else 0 for func in functions)
    
    # Find most used functions
    most_used = max(functions, key=lambda f: len(f.usages) if f.usages else 0, default=None)
    
    # Find unused functions
    unused_functions = [f.name for f in functions if not f.usages]
    
    return {
        "total_functions": len(functions),
        "total_calls": total_calls,
        "average_calls_per_function": total_calls / len(functions) if functions else 0,
        "most_used_function": most_used.name if most_used else None,
        "unused_functions": unused_functions,
        "unused_count": len(unused_functions)
    }

