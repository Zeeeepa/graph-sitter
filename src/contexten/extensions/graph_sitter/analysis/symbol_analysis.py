"""
Symbol Analysis Module

Provides detailed analysis of symbol usage, dependencies, and relationships
within the codebase. Includes recursive function detection and dependency tracking.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.enums import SymbolType
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types
    Codebase = Any
    Function = Any
    Symbol = Any


def analyze_symbol_usage(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze symbol usage patterns across the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with symbol usage statistics and patterns
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        analysis = {
            "total_symbols": 0,
            "usage_patterns": {},
            "most_used_symbols": [],
            "unused_symbols": [],
            "symbol_types": defaultdict(int)
        }
        
        symbols = list(codebase.symbols)
        analysis["total_symbols"] = len(symbols)
        
        usage_counts = []
        
        for symbol in symbols:
            # Count symbol type
            if hasattr(symbol, 'symbol_type'):
                analysis["symbol_types"][symbol.symbol_type.name] += 1
            
            # Count usages
            usage_count = len(symbol.symbol_usages) if hasattr(symbol, 'symbol_usages') else 0
            usage_counts.append((symbol.name, usage_count, type(symbol).__name__))
            
            # Track unused symbols
            if usage_count == 0:
                analysis["unused_symbols"].append({
                    "name": symbol.name,
                    "type": type(symbol).__name__,
                    "file": symbol.file.filepath if hasattr(symbol, 'file') else "unknown"
                })
        
        # Sort by usage count and get top 10
        usage_counts.sort(key=lambda x: x[1], reverse=True)
        analysis["most_used_symbols"] = [
            {"name": name, "usage_count": count, "type": symbol_type}
            for name, count, symbol_type in usage_counts[:10]
        ]
        
        # Usage patterns
        usage_values = [count for _, count, _ in usage_counts]
        if usage_values:
            analysis["usage_patterns"] = {
                "max_usage": max(usage_values),
                "min_usage": min(usage_values),
                "avg_usage": sum(usage_values) / len(usage_values),
                "median_usage": sorted(usage_values)[len(usage_values) // 2]
            }
        
        return analysis
        
    except Exception as e:
        return {"error": f"Error analyzing symbol usage: {str(e)}"}


def find_recursive_functions(codebase: Codebase) -> List[Dict[str, Any]]:
    """
    Find functions that call themselves (recursive functions).
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        List of recursive functions with details
    """
    if not GRAPH_SITTER_AVAILABLE:
        return [{"error": "Graph-sitter not available"}]
    
    try:
        recursive_functions = []
        
        for function in codebase.functions:
            # Check if function calls itself
            self_calls = [call for call in function.function_calls if call.name == function.name]
            
            if self_calls:
                recursive_functions.append({
                    "name": function.name,
                    "file": function.file.filepath if hasattr(function, 'file') else "unknown",
                    "self_call_count": len(self_calls),
                    "total_calls": len(function.function_calls),
                    "parameters": [p.name for p in function.parameters] if hasattr(function, 'parameters') else [],
                    "line_number": getattr(function, 'line_number', None)
                })
        
        return recursive_functions
        
    except Exception as e:
        return [{"error": f"Error finding recursive functions: {str(e)}"}]


def get_symbol_dependencies(symbol: Symbol) -> Dict[str, Any]:
    """
    Get detailed dependency information for a symbol.
    
    Args:
        symbol: The symbol to analyze
        
    Returns:
        Dictionary with dependency details
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        dependencies = {
            "direct_dependencies": [],
            "indirect_dependencies": [],
            "dependents": [],
            "dependency_count": 0
        }
        
        # Direct dependencies
        if hasattr(symbol, 'dependencies'):
            for dep in symbol.dependencies:
                dep_info = {
                    "name": dep.name if hasattr(dep, 'name') else str(dep),
                    "type": type(dep).__name__,
                    "file": dep.file.filepath if hasattr(dep, 'file') else "unknown"
                }
                dependencies["direct_dependencies"].append(dep_info)
        
        dependencies["dependency_count"] = len(dependencies["direct_dependencies"])
        
        # Symbol usages (what depends on this symbol)
        if hasattr(symbol, 'symbol_usages'):
            for usage in symbol.symbol_usages:
                if hasattr(usage, 'usage_symbol'):
                    dependent_info = {
                        "name": usage.usage_symbol.name,
                        "type": type(usage.usage_symbol).__name__,
                        "file": usage.usage_symbol.file.filepath if hasattr(usage.usage_symbol, 'file') else "unknown"
                    }
                    dependencies["dependents"].append(dependent_info)
        
        return dependencies
        
    except Exception as e:
        return {"error": f"Error getting symbol dependencies: {str(e)}"}


def analyze_function_complexity(function: Function) -> Dict[str, Any]:
    """
    Analyze the complexity of a function based on various metrics.
    
    Args:
        function: The function to analyze
        
    Returns:
        Dictionary with complexity metrics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        complexity = {
            "name": function.name,
            "parameter_count": 0,
            "return_statement_count": 0,
            "function_call_count": 0,
            "dependency_count": 0,
            "usage_count": 0,
            "cyclomatic_complexity": 1,  # Base complexity
            "file": "unknown"
        }
        
        if hasattr(function, 'file'):
            complexity["file"] = function.file.filepath
        
        if hasattr(function, 'parameters'):
            complexity["parameter_count"] = len(function.parameters)
        
        if hasattr(function, 'return_statements'):
            complexity["return_statement_count"] = len(function.return_statements)
        
        if hasattr(function, 'function_calls'):
            complexity["function_call_count"] = len(function.function_calls)
        
        if hasattr(function, 'dependencies'):
            complexity["dependency_count"] = len(function.dependencies)
        
        if hasattr(function, 'usages'):
            complexity["usage_count"] = len(function.usages)
        
        # Simple cyclomatic complexity estimation
        # This is a basic implementation - could be enhanced with AST analysis
        if hasattr(function, 'source'):
            source = function.source
            # Count decision points (if, while, for, try, except, etc.)
            decision_keywords = ['if ', 'elif ', 'while ', 'for ', 'try:', 'except ', 'and ', 'or ']
            for keyword in decision_keywords:
                complexity["cyclomatic_complexity"] += source.count(keyword)
        
        return complexity
        
    except Exception as e:
        return {"error": f"Error analyzing function complexity: {str(e)}"}


def find_symbol_clusters(codebase: Codebase) -> Dict[str, Any]:
    """
    Find clusters of related symbols based on usage patterns.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with symbol clusters
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        clusters = {
            "file_clusters": defaultdict(list),
            "usage_clusters": defaultdict(list),
            "dependency_clusters": defaultdict(list)
        }
        
        # Group symbols by file
        for symbol in codebase.symbols:
            if hasattr(symbol, 'file'):
                file_path = symbol.file.filepath
                clusters["file_clusters"][file_path].append({
                    "name": symbol.name,
                    "type": type(symbol).__name__
                })
        
        # Group symbols by usage patterns
        for symbol in codebase.symbols:
            if hasattr(symbol, 'symbol_usages'):
                usage_count = len(symbol.symbol_usages)
                usage_category = "high" if usage_count > 10 else "medium" if usage_count > 3 else "low"
                clusters["usage_clusters"][usage_category].append({
                    "name": symbol.name,
                    "usage_count": usage_count,
                    "type": type(symbol).__name__
                })
        
        # Group symbols by dependency count
        for symbol in codebase.symbols:
            if hasattr(symbol, 'dependencies'):
                dep_count = len(symbol.dependencies)
                dep_category = "high" if dep_count > 5 else "medium" if dep_count > 2 else "low"
                clusters["dependency_clusters"][dep_category].append({
                    "name": symbol.name,
                    "dependency_count": dep_count,
                    "type": type(symbol).__name__
                })
        
        return dict(clusters)
        
    except Exception as e:
        return {"error": f"Error finding symbol clusters: {str(e)}"}


def analyze_symbol_relationships(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze relationships between symbols in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with relationship analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        relationships = {
            "symbol_graph": {},
            "strongly_connected": [],
            "isolated_symbols": [],
            "hub_symbols": []
        }
        
        symbol_connections = defaultdict(set)
        
        # Build symbol connection graph
        for symbol in codebase.symbols:
            symbol_name = symbol.name
            
            # Add dependencies as outgoing connections
            if hasattr(symbol, 'dependencies'):
                for dep in symbol.dependencies:
                    if hasattr(dep, 'name'):
                        symbol_connections[symbol_name].add(dep.name)
            
            # Add usages as incoming connections
            if hasattr(symbol, 'symbol_usages'):
                for usage in symbol.symbol_usages:
                    if hasattr(usage, 'usage_symbol') and hasattr(usage.usage_symbol, 'name'):
                        symbol_connections[usage.usage_symbol.name].add(symbol_name)
        
        relationships["symbol_graph"] = {k: list(v) for k, v in symbol_connections.items()}
        
        # Find isolated symbols (no connections)
        all_symbols = {symbol.name for symbol in codebase.symbols}
        connected_symbols = set(symbol_connections.keys()) | set().union(*symbol_connections.values())
        relationships["isolated_symbols"] = list(all_symbols - connected_symbols)
        
        # Find hub symbols (highly connected)
        connection_counts = [(symbol, len(connections)) for symbol, connections in symbol_connections.items()]
        connection_counts.sort(key=lambda x: x[1], reverse=True)
        relationships["hub_symbols"] = [
            {"name": symbol, "connection_count": count}
            for symbol, count in connection_counts[:10]
        ]
        
        return relationships
        
    except Exception as e:
        return {"error": f"Error analyzing symbol relationships: {str(e)}"}

