#!/usr/bin/env python
"""
Codebase Analyzer

This module provides utility functions for analyzing and manipulating codebases,
focusing on call graphs, modularity, and type coverage.
"""

import os
import re
import sys
import networkx as nx
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from collections import defaultdict
from pathlib import Path


def find_all_paths_between_functions(start_func, end_func, max_depth: int = 10) -> List[List]:
    """
    Find all possible paths between two functions in the call graph.
    
    Args:
        start_func: The starting function object
        end_func: The ending function object
        max_depth: Maximum depth to search (default: 10)
        
    Returns:
        List of paths, where each path is a list of function objects
        
    Example:
        ```python
        start = codebase.get_function("create_skill")
        end = codebase.get_function("auto_define_skill_description")
        paths = find_all_paths_between_functions(start, end)
        for path in paths:
            print(" -> ".join([func.name for func in path]))
        ```
    """
    G = nx.DiGraph()
    
    def traverse_calls(parent_func, current_depth):
        if current_depth > max_depth:
            return
        
        # Determine source node
        if hasattr(parent_func, 'function_calls'):
            src_func = parent_func
        else:
            src_func = parent_func.function_definition
        
        # Skip external modules
        if hasattr(src_func, 'is_external') and src_func.is_external:
            return
        
        # Add the current node
        G.add_node(src_func)
        
        # Traverse all function calls
        if hasattr(src_func, 'function_calls'):
            for call in src_func.function_calls:
                func = call.function_definition
                
                # Skip recursive calls
                if func == src_func:
                    continue
                
                # Add nodes and edges
                G.add_node(func)
                G.add_edge(src_func, func)
                
                # Continue traversal
                traverse_calls(func, current_depth + 1)
    
    # Initialize graph
    G.add_node(start_func)
    G.add_node(end_func)
    
    # Start traversal
    traverse_calls(start_func, 1)
    
    # Find all paths
    try:
        all_paths = list(nx.all_simple_paths(G, source=start_func, target=end_func))
        return all_paths
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def get_max_call_chain(function, max_depth: int = 10) -> List:
    """
    Find the longest call chain in the codebase starting from the given function.
    
    Args:
        function: The starting function object
        max_depth: Maximum depth to search (default: 10)
        
    Returns:
        List of functions representing the longest call chain
        
    Example:
        ```python
        start_func = codebase.get_function("main")
        longest_chain = get_max_call_chain(start_func)
        print("Longest call chain:")
        print(" -> ".join([func.name for func in longest_chain]))
        ```
    """
    G = nx.DiGraph()
    
    def build_graph(func, depth=0):
        if depth > max_depth:  # Prevent infinite recursion
            return
        
        # Skip if not a valid function
        if not hasattr(func, 'function_calls'):
            return
            
        # Add the current node
        G.add_node(func)
        
        for call in func.function_calls:
            if hasattr(call, 'function_definition'):
                called_func = call.function_definition
                
                # Skip recursive calls
                if called_func == func:
                    continue
                    
                # Skip external modules
                if hasattr(called_func, 'is_external') and called_func.is_external:
                    continue
                
                G.add_node(called_func)
                G.add_edge(func, called_func)
                build_graph(called_func, depth + 1)
    
    # Build the call graph
    build_graph(function)
    
    # Find the longest path
    try:
        # If the graph is not a DAG, convert it by removing cycles
        if not nx.is_directed_acyclic_graph(G):
            # Find and remove back edges to make it a DAG
            back_edges = []
            for cycle in nx.simple_cycles(G):
                back_edges.append((cycle[-1], cycle[0]))
            
            for source, target in back_edges:
                if G.has_edge(source, target):
                    G.remove_edge(source, target)
        
        # Find the longest path in the DAG
        longest_path = nx.dag_longest_path(G)
        return longest_path
    except (nx.NetworkXError, nx.NetworkXUnfeasible):
        # If we can't find a longest path, return the nodes in topological order
        try:
            return list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            # If there are still cycles, return the nodes in some order
            return list(G.nodes())


def organize_imports(file, sort_by: str = 'type') -> bool:
    """
    Organize imports in a file by type and name.
    
    Args:
        file: The file object to organize imports in
        sort_by: How to sort imports - 'type' (standard, third-party, local) or 'name' (alphabetical)
        
    Returns:
        True if imports were organized successfully, False otherwise
        
    Example:
        ```python
        file = codebase.get_file("app/main.py")
        organize_imports(file)
        ```
    """
    if not hasattr(file, 'imports'):
        return False
    
    # Group imports by type
    std_lib_imports = []
    third_party_imports = []
    local_imports = []
    
    for imp in file.imports:
        if hasattr(imp, 'is_standard_library') and imp.is_standard_library:
            std_lib_imports.append(imp)
        elif hasattr(imp, 'is_third_party') and imp.is_third_party:
            third_party_imports.append(imp)
        else:
            local_imports.append(imp)
    
    # Sort each group
    if sort_by == 'type':
        for group in [std_lib_imports, third_party_imports, local_imports]:
            if hasattr(group[0], 'module_name') if group else False:
                group.sort(key=lambda x: x.module_name)
            else:
                group.sort(key=lambda x: str(x))
    else:  # sort_by == 'name'
        all_imports = std_lib_imports + third_party_imports + local_imports
        if hasattr(all_imports[0], 'module_name') if all_imports else False:
            all_imports.sort(key=lambda x: x.module_name)
        else:
            all_imports.sort(key=lambda x: str(x))
        return all_imports
    
    try:
        # Remove all existing imports
        for imp in file.imports:
            if hasattr(imp, 'remove'):
                imp.remove()
        
        # Add imports back in organized groups
        if std_lib_imports:
            for imp in std_lib_imports:
                if hasattr(file, 'add_import') and hasattr(imp, 'source'):
                    file.add_import(imp.source)
            if hasattr(file, 'insert_after_imports'):
                file.insert_after_imports("")  # Add newline
            
        if third_party_imports:
            for imp in third_party_imports:
                if hasattr(file, 'add_import') and hasattr(imp, 'source'):
                    file.add_import(imp.source)
            if hasattr(file, 'insert_after_imports'):
                file.insert_after_imports("")  # Add newline
            
        if local_imports:
            for imp in local_imports:
                if hasattr(file, 'add_import') and hasattr(imp, 'source'):
                    file.add_import(imp.source)
        
        return True
    except Exception as e:
        print(f"Error organizing imports: {str(e)}")
        return False


def extract_shared_code(codebase, min_usages: int = 3, shared_dir: str = "shared") -> Dict[str, List[str]]:
    """
    Extract shared code into common modules.
    
    Args:
        codebase: The codebase object
        min_usages: Minimum number of usages to consider a symbol as shared (default: 3)
        shared_dir: Directory to place shared modules (default: "shared")
        
    Returns:
        Dictionary mapping shared module names to lists of extracted symbols
        
    Example:
        ```python
        extracted = extract_shared_code(codebase, min_usages=4)
        for module, symbols in extracted.items():
            print(f"Extracted {len(symbols)} symbols to {module}")
        ```
    """
    # Create shared directory if it doesn't exist
    if hasattr(codebase, 'has_directory') and not codebase.has_directory(shared_dir):
        if hasattr(codebase, 'create_directory'):
            codebase.create_directory(shared_dir)
    
    extracted_symbols = defaultdict(list)
    
    # Iterate through all files
    for file in codebase.files:
        # Skip files in the shared directory
        if shared_dir in str(file.filepath) if hasattr(file, 'filepath') else False:
            continue
        
        # Find symbols used by multiple files
        if hasattr(file, 'symbols'):
            for symbol in file.symbols:
                # Get unique files using this symbol
                using_files = set()
                if hasattr(symbol, 'usages'):
                    for usage in symbol.usages:
                        if hasattr(usage, 'file') and usage.file != file:
                            using_files.add(usage.file)
                
                if len(using_files) >= min_usages:
                    # Determine appropriate shared module
                    module_name = determine_appropriate_shared_module(symbol)
                    shared_file_path = f"{shared_dir}/{module_name}.py"
                    
                    # Create shared file if it doesn't exist
                    if hasattr(codebase, 'has_file') and not codebase.has_file(shared_file_path):
                        if hasattr(codebase, 'create_file'):
                            shared_file = codebase.create_file(shared_file_path)
                    else:
                        if hasattr(codebase, 'get_file'):
                            shared_file = codebase.get_file(shared_file_path)
                    
                    # Move symbol to shared module
                    if hasattr(symbol, 'move_to_file'):
                        symbol.move_to_file(shared_file, strategy="update_all_imports")
                        extracted_symbols[module_name].append(symbol.name if hasattr(symbol, 'name') else str(symbol))
    
    return dict(extracted_symbols)


def determine_appropriate_shared_module(symbol) -> str:
    """
    Determine the appropriate module for shared code.
    
    Args:
        symbol: The symbol object to analyze
        
    Returns:
        String name of the appropriate shared module
        
    Example:
        ```python
        symbol = file.get_symbol("UserType")
        module = determine_appropriate_shared_module(symbol)
        print(f"Symbol should be moved to {module}.py")
        ```
    """
    # Check if it's a type
    if hasattr(symbol, 'is_type') and symbol.is_type:
        return "types"
    
    # Check if it's a constant
    if hasattr(symbol, 'is_constant') and symbol.is_constant:
        return "constants"
    
    # Check if it's a utility function
    if hasattr(symbol, 'is_function') and symbol.is_function:
        # Check function name for utility patterns
        name = symbol.name.lower() if hasattr(symbol, 'name') else ""
        utility_patterns = ['util', 'helper', 'format', 'convert', 'parse', 'validate', 'check']
        if any(pattern in name for pattern in utility_patterns):
            return "utils"
    
    # Check if it's a configuration
    if hasattr(symbol, 'name'):
        name = symbol.name.lower()
        config_patterns = ['config', 'setting', 'option', 'env', 'environment']
        if any(pattern in name for pattern in config_patterns):
            return "config"
    
    # Default to common
    return "common"


def break_circular_dependencies(codebase, shared_dir: str = "shared") -> List[List[str]]:
    """
    Break circular dependencies by extracting shared code.
    
    Args:
        codebase: The codebase object
        shared_dir: Directory to place shared modules (default: "shared")
        
    Returns:
        List of broken dependency cycles, each represented as a list of file paths
        
    Example:
        ```python
        broken_cycles = break_circular_dependencies(codebase)
        print(f"Broke {len(broken_cycles)} circular dependencies")
        ```
    """
    # Create dependency graph
    G = nx.DiGraph()
    
    for file in codebase.files:
        # Skip files that don't have a filepath attribute
        if not hasattr(file, 'filepath'):
            continue
            
        # Add node for this file
        file_path = str(file.filepath)
        G.add_node(file_path)
        
        # Add edges for each import
        if hasattr(file, 'imports'):
            for imp in file.imports:
                if hasattr(imp, 'from_file') and imp.from_file:
                    imported_file_path = str(imp.from_file.filepath) if hasattr(imp.from_file, 'filepath') else ""
                    if imported_file_path:
                        G.add_edge(file_path, imported_file_path)
    
    # Find circular dependencies
    cycles = list(nx.simple_cycles(G))
    broken_cycles = []
    
    # Create shared directory if it doesn't exist
    if hasattr(codebase, 'has_directory') and not codebase.has_directory(shared_dir):
        if hasattr(codebase, 'create_directory'):
            codebase.create_directory(shared_dir)
    
    # Break each cycle
    for cycle in cycles:
        # Get the first two files in the cycle
        if len(cycle) < 2:
            continue
            
        file1_path = cycle[0]
        file2_path = cycle[1]
        
        if hasattr(codebase, 'get_file'):
            file1 = codebase.get_file(file1_path)
            file2 = codebase.get_file(file2_path)
            
            # Find symbols used by both files
            shared_symbols = []
            if hasattr(file1, 'symbols'):
                for symbol in file1.symbols:
                    if hasattr(symbol, 'usages'):
                        if any(hasattr(usage, 'file') and usage.file == file2 for usage in symbol.usages):
                            shared_symbols.append(symbol)
            
            # Move shared symbols to a new file
            if shared_symbols:
                module_name = f"shared_{Path(file1_path).stem}_{Path(file2_path).stem}"
                shared_file_path = f"{shared_dir}/{module_name}.py"
                
                if hasattr(codebase, 'create_file'):
                    shared_file = codebase.create_file(shared_file_path)
                    
                    for symbol in shared_symbols:
                        if hasattr(symbol, 'move_to_file'):
                            symbol.move_to_file(shared_file, strategy="update_all_imports")
                
                broken_cycles.append(cycle)
    
    return broken_cycles


def analyze_module_coupling(codebase) -> Dict[str, Dict[str, Union[int, float, List[str]]]]:
    """
    Analyze coupling between modules.
    
    Args:
        codebase: The codebase object
        
    Returns:
        Dictionary mapping file paths to coupling metrics
        
    Example:
        ```python
        coupling = analyze_module_coupling(codebase)
        for file_path, metrics in sorted(coupling.items(), key=lambda x: x[1]['score'], reverse=True)[:5]:
            print(f"{file_path}: {metrics['score']} connections")
        ```
    """
    coupling_data = {}
    
    for file in codebase.files:
        if not hasattr(file, 'filepath'):
            continue
            
        file_path = str(file.filepath)
        imported_files = set()
        importing_files = set()
        
        # Count unique files imported from
        if hasattr(file, 'imports'):
            for imp in file.imports:
                if hasattr(imp, 'from_file') and imp.from_file and hasattr(imp.from_file, 'filepath'):
                    imported_files.add(str(imp.from_file.filepath))
        
        # Count files that import this file
        if hasattr(file, 'symbols'):
            for symbol in file.symbols:
                if hasattr(symbol, 'usages'):
                    for usage in symbol.usages:
                        if hasattr(usage, 'file') and usage.file != file and hasattr(usage.file, 'filepath'):
                            importing_files.add(str(usage.file.filepath))
        
        # Calculate coupling score
        afferent_coupling = len(importing_files)  # Files that depend on this file
        efferent_coupling = len(imported_files)   # Files this file depends on
        instability = efferent_coupling / (afferent_coupling + efferent_coupling) if (afferent_coupling + efferent_coupling) > 0 else 0
        
        coupling_data[file_path] = {
            'afferent': afferent_coupling,
            'efferent': efferent_coupling,
            'score': afferent_coupling + efferent_coupling,
            'instability': instability,
            'imported_by': list(importing_files),
            'imports': list(imported_files)
        }
    
    return coupling_data


def calculate_type_coverage_percentages(codebase) -> Dict[str, Dict[str, Union[int, float]]]:
    """
    Calculate type coverage percentages across the codebase.
    
    Args:
        codebase: The codebase object
        
    Returns:
        Dictionary with type coverage statistics
        
    Example:
        ```python
        coverage = calculate_type_coverage_percentages(codebase)
        print(f"Parameter type coverage: {coverage['parameters']['percentage']:.1f}%")
        print(f"Return type coverage: {coverage['returns']['percentage']:.1f}%")
        print(f"Attribute type coverage: {coverage['attributes']['percentage']:.1f}%")
        ```
    """
    # Initialize counters
    total_parameters = 0
    typed_parameters = 0
    
    total_functions = 0
    typed_returns = 0
    
    total_attributes = 0
    typed_attributes = 0
    
    # Count parameter and return type coverage
    for function in codebase.functions:
        # Count parameters
        if hasattr(function, 'parameters'):
            total_parameters += len(function.parameters)
            typed_parameters += sum(1 for param in function.parameters 
                                   if hasattr(param, 'is_typed') and param.is_typed)
        
        # Count return types
        total_functions += 1
        if hasattr(function, 'return_type') and function.return_type and hasattr(function.return_type, 'is_typed') and function.return_type.is_typed:
            typed_returns += 1
    
    # Count class attribute coverage
    for cls in codebase.classes:
        if hasattr(cls, 'attributes'):
            for attr in cls.attributes:
                total_attributes += 1
                if hasattr(attr, 'is_typed') and attr.is_typed:
                    typed_attributes += 1
    
    # Calculate percentages
    param_percentage = (typed_parameters / total_parameters * 100) if total_parameters > 0 else 0
    return_percentage = (typed_returns / total_functions * 100) if total_functions > 0 else 0
    attr_percentage = (typed_attributes / total_attributes * 100) if total_attributes > 0 else 0
    
    # Overall percentage
    total_elements = total_parameters + total_functions + total_attributes
    typed_elements = typed_parameters + typed_returns + typed_attributes
    overall_percentage = (typed_elements / total_elements * 100) if total_elements > 0 else 0
    
    return {
        'overall': {
            'total': total_elements,
            'typed': typed_elements,
            'percentage': overall_percentage
        },
        'parameters': {
            'total': total_parameters,
            'typed': typed_parameters,
            'percentage': param_percentage
        },
        'returns': {
            'total': total_functions,
            'typed': typed_returns,
            'percentage': return_percentage
        },
        'attributes': {
            'total': total_attributes,
            'typed': typed_attributes,
            'percentage': attr_percentage
        }
    }


if __name__ == "__main__":
    print("Codebase Analyzer Utility Functions")
    print("Use these functions by importing them into your analysis scripts.")

