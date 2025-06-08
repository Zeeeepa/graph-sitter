#!/usr/bin/env python3
"""
Call Graph Analyzer

Analyzes function call relationships and creates call graphs using graph_sitter API.
Provides insights into function usage patterns and call hierarchies.
"""

import graph_sitter
from graph_sitter import Codebase
from graph_sitter.core.external_module import ExternalModule
import networkx as nx
from collections import defaultdict, Counter


# Configuration
MAX_DEPTH = 5
IGNORE_EXTERNAL_MODULE_CALLS = True
IGNORE_CLASS_CALLS = False

# Color palette for visualization
COLOR_PALETTE = {
    "Function": "#4CAF50",
    "Class": "#2196F3", 
    "ExternalModule": "#FF9800",
    "HTTP_METHOD": "#F44336"
}


def generate_edge_meta(call) -> dict:
    """Generate metadata for call graph edges."""
    return {
        "name": call.name,
        "file_path": call.filepath if hasattr(call, 'filepath') else '',
        "start_point": call.start_point if hasattr(call, 'start_point') else None,
        "end_point": call.end_point if hasattr(call, 'end_point') else None,
        "symbol_name": "FunctionCall"
    }


def create_downstream_call_trace(src_func, G, depth: int = 0):
    """Creates call graph by recursively traversing function calls."""
    # Prevent infinite recursion
    if MAX_DEPTH <= depth:
        return
        
    # External modules are not functions
    if isinstance(src_func, ExternalModule):
        return

    # Process each function call
    for call in src_func.function_calls:
        # Skip self-recursive calls
        if call.name == src_func.name:
            continue
            
        # Get called function definition
        func = call.function_definition if hasattr(call, 'function_definition') else None
        if not func:
            continue
            
        # Apply configured filters
        if isinstance(func, ExternalModule) and IGNORE_EXTERNAL_MODULE_CALLS:
            continue
        if hasattr(func, '__class__') and func.__class__.__name__ == 'Class' and IGNORE_CLASS_CALLS:
            continue

        # Generate display name (include class for methods)
        if isinstance(func, ExternalModule):
            func_name = func.name
        elif hasattr(func, 'is_method') and func.is_method and hasattr(func, 'parent_class'):
            func_name = f"{func.parent_class.name}.{func.name}"
        else:
            func_name = func.name

        # Add node and edge with metadata
        G.add_node(func, name=func_name, 
                  color=COLOR_PALETTE.get(func.__class__.__name__, "#f694ff"))
        G.add_edge(src_func, func, **generate_edge_meta(call))

        # Recurse for regular functions
        if hasattr(func, 'function_calls'):
            create_downstream_call_trace(func, G, depth + 1)


@graph_sitter.function("analyze-call-graph")
def analyze_call_graph(codebase: Codebase):
    """Analyze function call relationships in the codebase."""
    results = {
        'call_statistics': {},
        'most_called_functions': [],
        'functions_making_most_calls': [],
        'recursive_functions': [],
        'unused_functions': [],
        'call_chains': [],
        'summary': {
            'total_functions': len(codebase.functions),
            'total_calls': 0,
            'avg_calls_per_function': 0,
            'recursive_count': 0,
            'unused_count': 0
        }
    }
    
    # Analyze each function
    call_counts = Counter()
    caller_counts = Counter()
    total_calls = 0
    
    for function in codebase.functions:
        # Skip test files
        if "test" in function.file.filepath:
            continue
        
        # Count calls made by this function
        calls_made = len(function.function_calls)
        caller_counts[function.name] = calls_made
        total_calls += calls_made
        
        # Count how many times this function is called
        calls_received = len(function.call_sites) if hasattr(function, 'call_sites') else 0
        call_counts[function.name] = calls_received
        
        # Check for recursion
        is_recursive = any(call.name == function.name for call in function.function_calls)
        if is_recursive:
            results['recursive_functions'].append({
                'name': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0
            })
        
        # Check if function is unused
        if calls_received == 0 and not function.name.startswith('_'):  # Ignore private functions
            results['unused_functions'].append({
                'name': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0
            })
    
    # Get most called functions
    results['most_called_functions'] = [
        {
            'name': name,
            'call_count': count,
            'file': next((f.file.filepath for f in codebase.functions if f.name == name), 'unknown')
        }
        for name, count in call_counts.most_common(10)
    ]
    
    # Get functions making most calls
    results['functions_making_most_calls'] = [
        {
            'name': name,
            'calls_made': count,
            'file': next((f.file.filepath for f in codebase.functions if f.name == name), 'unknown')
        }
        for name, count in caller_counts.most_common(10)
    ]
    
    # Update summary
    results['summary']['total_calls'] = total_calls
    results['summary']['avg_calls_per_function'] = total_calls / len(codebase.functions) if codebase.functions else 0
    results['summary']['recursive_count'] = len(results['recursive_functions'])
    results['summary']['unused_count'] = len(results['unused_functions'])
    
    return results


def find_call_chains(codebase: Codebase, max_depth: int = 3):
    """Find call chains starting from entry points."""
    call_chains = []
    
    # Find potential entry points (functions with no callers)
    entry_points = []
    for function in codebase.functions:
        if hasattr(function, 'call_sites'):
            if len(function.call_sites) == 0 and not function.name.startswith('_'):
                entry_points.append(function)
    
    # Build call chains from entry points
    for entry in entry_points[:5]:  # Limit to first 5 entry points
        chain = build_call_chain(entry, max_depth)
        if len(chain) > 1:  # Only include chains with actual calls
            call_chains.append({
                'entry_point': entry.name,
                'chain': chain,
                'depth': len(chain)
            })
    
    return call_chains


def build_call_chain(function, max_depth: int, current_chain=None, visited=None):
    """Build a call chain starting from a function."""
    if current_chain is None:
        current_chain = []
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion
    if len(current_chain) >= max_depth or function.name in visited:
        return current_chain
    
    visited.add(function.name)
    current_chain.append(function.name)
    
    # Follow the first function call (simplified)
    if function.function_calls:
        first_call = function.function_calls[0]
        called_func = first_call.function_definition if hasattr(first_call, 'function_definition') else None
        
        if called_func and hasattr(called_func, 'function_calls'):
            return build_call_chain(called_func, max_depth, current_chain, visited)
    
    return current_chain


def analyze_function_complexity_by_calls(codebase: Codebase):
    """Analyze function complexity based on call patterns."""
    complexity_analysis = []
    
    for function in codebase.functions:
        if "test" in function.file.filepath:
            continue
        
        # Calculate various complexity metrics
        calls_made = len(function.function_calls)
        calls_received = len(function.call_sites) if hasattr(function, 'call_sites') else 0
        unique_callees = len(set(call.name for call in function.function_calls))
        
        # Simple complexity score
        complexity_score = calls_made + (calls_received * 0.5) + unique_callees
        
        complexity_analysis.append({
            'name': function.name,
            'file': function.file.filepath,
            'calls_made': calls_made,
            'calls_received': calls_received,
            'unique_callees': unique_callees,
            'complexity_score': complexity_score
        })
    
    # Sort by complexity score
    complexity_analysis.sort(key=lambda x: x['complexity_score'], reverse=True)
    
    return complexity_analysis


def find_hotspot_functions(codebase: Codebase):
    """Find functions that are called frequently (hotspots)."""
    hotspots = []
    
    for function in codebase.functions:
        if "test" in function.file.filepath:
            continue
        
        call_count = len(function.call_sites) if hasattr(function, 'call_sites') else 0
        
        # Consider functions with more than 5 call sites as hotspots
        if call_count > 5:
            # Get caller information
            callers = []
            if hasattr(function, 'call_sites'):
                for call_site in function.call_sites:
                    if hasattr(call_site, 'parent_function'):
                        callers.append(call_site.parent_function.name)
            
            hotspots.append({
                'name': function.name,
                'file': function.file.filepath,
                'call_count': call_count,
                'unique_callers': len(set(callers)),
                'callers': list(set(callers))[:5]  # Show first 5 unique callers
            })
    
    return sorted(hotspots, key=lambda x: x['call_count'], reverse=True)


def create_call_graph_visualization(codebase: Codebase, start_function_name: str = None):
    """Create a NetworkX graph for visualization."""
    G = nx.DiGraph()
    
    # If start function specified, build from there
    if start_function_name:
        start_func = next((f for f in codebase.functions if f.name == start_function_name), None)
        if start_func:
            create_downstream_call_trace(start_func, G)
    else:
        # Build graph for all functions (limited depth)
        for function in codebase.functions[:10]:  # Limit to first 10 functions
            if "test" not in function.file.filepath:
                create_downstream_call_trace(function, G, depth=0)
    
    return G


# HTTP methods to highlight
HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]


def is_http_method(symbol) -> bool:
    """Check if a symbol is an HTTP endpoint method."""
    if hasattr(symbol, 'is_method') and symbol.is_method:
        return symbol.name.lower() in HTTP_METHODS
    return False


if __name__ == "__main__":
    # Example usage
    codebase = Codebase("./")
    
    print("📞 Analyzing function call graph...")
    results = analyze_call_graph(codebase)
    
    print(f"\n📊 Call Graph Analysis Results:")
    print(f"Total functions: {results['summary']['total_functions']}")
    print(f"Total function calls: {results['summary']['total_calls']}")
    print(f"Average calls per function: {results['summary']['avg_calls_per_function']:.1f}")
    print(f"Recursive functions: {results['summary']['recursive_count']}")
    print(f"Unused functions: {results['summary']['unused_count']}")
    
    # Show most called functions
    if results['most_called_functions']:
        print(f"\n🔥 Most Called Functions:")
        for func in results['most_called_functions'][:5]:
            print(f"  • {func['name']}: {func['call_count']} calls")
    
    # Show functions making most calls
    if results['functions_making_most_calls']:
        print(f"\n📤 Functions Making Most Calls:")
        for func in results['functions_making_most_calls'][:5]:
            print(f"  • {func['name']}: {func['calls_made']} calls")
    
    # Show recursive functions
    if results['recursive_functions']:
        print(f"\n🔄 Recursive Functions:")
        for func in results['recursive_functions']:
            print(f"  • {func['name']} in {func['file']}")
    
    # Show unused functions
    if results['unused_functions']:
        print(f"\n💀 Unused Functions:")
        for func in results['unused_functions'][:5]:
            print(f"  • {func['name']} in {func['file']}")
    
    # Analyze hotspots
    print(f"\n🌡️ Analyzing function hotspots...")
    hotspots = find_hotspot_functions(codebase)
    if hotspots:
        print(f"Function hotspots (frequently called):")
        for hotspot in hotspots[:3]:
            print(f"  • {hotspot['name']}: {hotspot['call_count']} calls from {hotspot['unique_callers']} callers")

