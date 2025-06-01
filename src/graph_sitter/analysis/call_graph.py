"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Tuple
import re

import matplotlib.pyplot as plt
import networkx as nx

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.function import Function

Call graph analysis implementation following graph-sitter.com patterns.

This module provides comprehensive call graph analysis including:
- Call graph construction and traversal
- Path finding between functions
- Call chain analysis
- Method chaining detection
"""

@dataclass
class CallPath:
    """Represents a path between two functions in the call graph."""
    start_function: str
    end_function: str
    path: List[str]
    length: int
    is_recursive: bool
    
    @property
    def path_description(self) -> str:
        """Get human-readable path description."""
        return " -> ".join(self.path)

@dataclass
class CallChain:
    """Represents a method call chain."""
    base_object: str
    chain_calls: List[str]
    total_length: int
    file_location: str
    line_number: int
    
    @property
    def chain_description(self) -> str:
        """Get human-readable chain description."""
        return f"{self.base_object}.{'.'.join(self.chain_calls)}"

@dataclass
class CallGraphMetrics:
    """Metrics for the call graph."""
    total_functions: int
    total_calls: int
    max_call_depth: int
    average_calls_per_function: float
    most_called_function: str
    most_calling_function: str
    recursive_functions: List[str]
    dead_end_functions: List[str]
    entry_point_functions: List[str]
    strongly_connected_components: int

class CallGraphAnalyzer:
    """
    Call graph analyzer following graph-sitter.com patterns.
    
    Provides comprehensive call graph analysis including:
    - Graph construction and traversal
    - Path analysis between functions
    - Call pattern detection
    - Performance metrics
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize call graph analyzer with codebase."""
        self.codebase = codebase
        self.call_graph: Optional[nx.DiGraph] = None
        self._function_map: Dict[str, Function] = {}
        self._build_function_map()
    
    def _build_function_map(self):
        """Build mapping of function names to Function objects."""
        for function in self.codebase.functions:
            self._function_map[function.qualified_name] = function
            # Also map by simple name for lookup
            self._function_map[function.name] = function
    
    def build_call_graph(self) -> nx.DiGraph:
        """
        Build directed graph of function calls.
        
        Based on graph-sitter.com call graph construction patterns.
        """
        if self.call_graph is not None:
            return self.call_graph
        
        self.call_graph = nx.DiGraph()
        
        # Add all functions as nodes
        for function in self.codebase.functions:
            self.call_graph.add_node(
                function.qualified_name,
                function_obj=function,
                name=function.name,
                file=function.filepath if hasattr(function, 'filepath') else '',
                is_external=False
            )
        
        # Add edges for function calls
        for function in self.codebase.functions:
            if hasattr(function, 'function_calls'):
                for call in function.function_calls:
                    target_name = self._get_call_target_name(call)
                    if target_name:
                        # Add edge with call metadata
                        self.call_graph.add_edge(
                            function.qualified_name,
                            target_name,
                            call_obj=call,
                            call_name=getattr(call, 'name', target_name),
                            is_external=self._is_external_call(call),
                            line_number=getattr(call, 'start_point', [0])[0] if hasattr(call, 'start_point') else 0
                        )
        
        return self.call_graph
    
    def find_call_paths(self, start_function: str, end_function: str, max_depth: int = 10) -> List[CallPath]:
        """
        Find all paths between two functions in the call graph.
        
        Args:
            start_function: Starting function name
            end_function: Target function name
            max_depth: Maximum path depth to search
            
        Returns:
            List of CallPath objects representing paths between functions
        """
        if self.call_graph is None:
            self.build_call_graph()
        
        paths = []
        
        try:
            # Find all simple paths (no cycles)
            all_paths = nx.all_simple_paths(
                self.call_graph, 
                start_function, 
                end_function, 
                cutoff=max_depth
            )
            
            for path in all_paths:
                is_recursive = self._path_has_recursion(path)
                paths.append(CallPath(
                    start_function=start_function,
                    end_function=end_function,
                    path=path,
                    length=len(path) - 1,
                    is_recursive=is_recursive
                ))
                
        except nx.NetworkXNoPath:
            # No path exists between the functions
            pass
        
        return sorted(paths, key=lambda p: p.length)
    
    def find_shortest_path(self, start_function: str, end_function: str) -> Optional[CallPath]:
        """Find the shortest path between two functions."""
        paths = self.find_call_paths(start_function, end_function)
        return paths[0] if paths else None
    
    def get_function_call_depth(self, function_name: str, max_depth: int = 20) -> int:
        """
        Calculate the maximum call depth from a function.
        
        Args:
            function_name: Function to analyze
            max_depth: Maximum depth to prevent infinite recursion
            
        Returns:
            Maximum call depth from the function
        """
        if self.call_graph is None:
            self.build_call_graph()
        
        if function_name not in self.call_graph:
            return 0
        
        def dfs_depth(node: str, current_depth: int, visited: Set[str]) -> int:
            if current_depth >= max_depth or node in visited:
                return current_depth
            
            visited.add(node)
            max_child_depth = current_depth
            
            for successor in self.call_graph.successors(node):
                child_depth = dfs_depth(successor, current_depth + 1, visited.copy())
                max_child_depth = max(max_child_depth, child_depth)
            
            return max_child_depth
        
        return dfs_depth(function_name, 0, set())
    
    def find_recursive_functions(self) -> List[str]:
        """Find all recursive functions in the call graph."""
        if self.call_graph is None:
            self.build_call_graph()
        
        recursive_functions = []
        
        # Find self-loops (direct recursion)
        for node in self.call_graph.nodes():
            if self.call_graph.has_edge(node, node):
                recursive_functions.append(node)
        
        # Find cycles (indirect recursion)
        try:
            cycles = list(nx.simple_cycles(self.call_graph))
            for cycle in cycles:
                recursive_functions.extend(cycle)
        except:
            # Handle any issues with cycle detection
            pass
        
        return list(set(recursive_functions))
    
    def find_dead_end_functions(self) -> List[str]:
        """Find functions that don't call any other functions."""
        if self.call_graph is None:
            self.build_call_graph()
        
        dead_end_functions = []
        for node in self.call_graph.nodes():
            if self.call_graph.out_degree(node) == 0:
                dead_end_functions.append(node)
        
        return dead_end_functions
    
    def find_entry_point_functions(self) -> List[str]:
        """Find functions that are not called by any other functions."""
        if self.call_graph is None:
            self.build_call_graph()
        
        entry_points = []
        for node in self.call_graph.nodes():
            if self.call_graph.in_degree(node) == 0:
                entry_points.append(node)
        
        return entry_points
    
    def get_most_called_function(self) -> Tuple[str, int]:
        """Find the function with the most incoming calls."""
        if self.call_graph is None:
            self.build_call_graph()
        
        if not self.call_graph.nodes():
            return "", 0
        
        most_called = max(
            self.call_graph.nodes(),
            key=lambda n: self.call_graph.in_degree(n)
        )
        call_count = self.call_graph.in_degree(most_called)
        
        return most_called, call_count
    
    def get_most_calling_function(self) -> Tuple[str, int]:
        """Find the function that makes the most calls."""
        if self.call_graph is None:
            self.build_call_graph()
        
        if not self.call_graph.nodes():
            return "", 0
        
        most_calling = max(
            self.call_graph.nodes(),
            key=lambda n: self.call_graph.out_degree(n)
        )
        call_count = self.call_graph.out_degree(most_calling)
        
        return most_calling, call_count
    
    def analyze_call_chains(self) -> List[CallChain]:
        """
        Analyze method call chains in the codebase.
        
        Based on graph-sitter.com method chaining patterns.
        """
        call_chains = []
        
        for function in self.codebase.functions:
            if hasattr(function, 'function_calls'):
                chains = self._extract_call_chains_from_function(function)
                call_chains.extend(chains)
        
        return sorted(call_chains, key=lambda c: c.total_length, reverse=True)
    
    def get_call_graph_metrics(self) -> CallGraphMetrics:
        """Get comprehensive metrics for the call graph."""
        if self.call_graph is None:
            self.build_call_graph()
        
        total_functions = self.call_graph.number_of_nodes()
        total_calls = self.call_graph.number_of_edges()
        
        # Calculate average calls per function
        avg_calls = total_calls / max(total_functions, 1)
        
        # Find max call depth
        max_depth = 0
        for node in self.call_graph.nodes():
            depth = self.get_function_call_depth(node)
            max_depth = max(max_depth, depth)
        
        # Get most called and most calling functions
        most_called, _ = self.get_most_called_function()
        most_calling, _ = self.get_most_calling_function()
        
        # Find various function categories
        recursive_functions = self.find_recursive_functions()
        dead_end_functions = self.find_dead_end_functions()
        entry_point_functions = self.find_entry_point_functions()
        
        # Count strongly connected components
        scc_count = nx.number_strongly_connected_components(self.call_graph)
        
        return CallGraphMetrics(
            total_functions=total_functions,
            total_calls=total_calls,
            max_call_depth=max_depth,
            average_calls_per_function=avg_calls,
            most_called_function=most_called,
            most_calling_function=most_calling,
            recursive_functions=recursive_functions,
            dead_end_functions=dead_end_functions,
            entry_point_functions=entry_point_functions,
            strongly_connected_components=scc_count
        )
    
    def visualize_call_graph(self, output_file: str = "call_graph.png", 
                           include_external: bool = False,
                           max_nodes: int = 50) -> str:
        """
        Create a visualization of the call graph.
        
        Args:
            output_file: Output file path for the visualization
            include_external: Whether to include external function calls
            max_nodes: Maximum number of nodes to include in visualization
            
        Returns:
            Path to the generated visualization file
        """
        if self.call_graph is None:
            self.build_call_graph()
        
        # Create a subgraph for visualization
        viz_graph = self.call_graph.copy()
        
        # Filter external calls if requested
        if not include_external:
            external_nodes = [
                node for node, data in viz_graph.nodes(data=True)
                if data.get('is_external', False)
            ]
            viz_graph.remove_nodes_from(external_nodes)
        
        # Limit number of nodes for readability
        if viz_graph.number_of_nodes() > max_nodes:
            # Keep the most connected nodes
            node_degrees = dict(viz_graph.degree())
            top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            nodes_to_keep = [node for node, _ in top_nodes]
            viz_graph = viz_graph.subgraph(nodes_to_keep).copy()
        
        try:
            
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(viz_graph, k=1, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(viz_graph, pos, node_color='lightblue', 
                                 node_size=500, alpha=0.7)
            
            # Draw edges
            nx.draw_networkx_edges(viz_graph, pos, edge_color='gray', 
                                 arrows=True, arrowsize=20, alpha=0.5)
            
            # Draw labels
            labels = {node: node.split('.')[-1] for node in viz_graph.nodes()}  # Use short names
            nx.draw_networkx_labels(viz_graph, pos, labels, font_size=8)
            
            plt.title("Function Call Graph")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return output_file
            
        except ImportError:
            # Fallback to text-based representation
            return self._create_text_visualization(viz_graph, output_file.replace('.png', '.txt'))
    
    # Private helper methods
    
    def _get_call_target_name(self, call) -> Optional[str]:
        """Extract target function name from a function call."""
        if hasattr(call, 'function_definition'):
            func_def = call.function_definition
            if hasattr(func_def, 'qualified_name'):
                return func_def.qualified_name
            elif hasattr(func_def, 'name'):
                return func_def.name
        
        if hasattr(call, 'name'):
            return call.name
        
        return None
    
    def _is_external_call(self, call) -> bool:
        """Check if a function call is to an external module."""
        if hasattr(call, 'function_definition'):
            return isinstance(call.function_definition, ExternalModule)
        return False
    
    def _path_has_recursion(self, path: List[str]) -> bool:
        """Check if a path contains recursive calls."""
        return len(path) != len(set(path))
    
    def _extract_call_chains_from_function(self, function: Function) -> List[CallChain]:
        """Extract method call chains from a function's source code."""
        chains = []
        
        if not hasattr(function, 'source'):
            return chains
        
        # Simple regex-based chain detection
        
        # Look for chained method calls like obj.method1().method2().method3()
        chain_pattern = r'(\\w+)(\\.\\w+\\(\\))+' 
        
        for line_num, line in enumerate(function.source.split('\\n'), 1):
            matches = re.finditer(chain_pattern, line)
            for match in matches:
                full_chain = match.group(0)
                parts = full_chain.split('.')
                
                if len(parts) > 2:  # At least obj.method1().method2()
                    base_object = parts[0]
                    chain_calls = [part.replace('()', '') for part in parts[1:]]
                    
                    chains.append(CallChain(
                        base_object=base_object,
                        chain_calls=chain_calls,
                        total_length=len(chain_calls),
                        file_location=function.filepath if hasattr(function, 'filepath') else '',
                        line_number=line_num
                    ))
        
        return chains
    
    def _create_text_visualization(self, graph: nx.DiGraph, output_file: str) -> str:
        """Create a text-based visualization of the call graph."""
        with open(output_file, 'w') as f:
            f.write("Function Call Graph\\n")
            f.write("=" * 50 + "\\n\\n")
            
            # Write nodes
            f.write("Functions:\\n")
            for node in sorted(graph.nodes()):
                in_degree = graph.in_degree(node)
                out_degree = graph.out_degree(node)
                f.write(f"  {node} (calls: {out_degree}, called by: {in_degree})\\n")
            
            f.write("\\nCall Relationships:\\n")
            for edge in sorted(graph.edges()):
                f.write(f"  {edge[0]} -> {edge[1]}\\n")
        
        return output_file
