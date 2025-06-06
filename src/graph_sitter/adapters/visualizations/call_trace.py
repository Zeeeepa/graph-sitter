"""
Function call relationships visualization adapter.

This module provides visualization of downstream function call relationships,
tracing execution flow and identifying complex call chains.
"""

from typing import Optional, Set
import logging

from graph_sitter import Codebase
from graph_sitter.core.base_symbol import BaseSymbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.external_module import ExternalModule

from .base import BaseVisualizationAdapter, VisualizationResult, FunctionCallMixin
from .config import CallTraceConfig, VisualizationType


logger = logging.getLogger(__name__)


class CallTraceVisualizer(BaseVisualizationAdapter, FunctionCallMixin):
    """
    Visualizer for function call relationships and execution flow.
    
    This visualizer creates call graphs by recursively traversing function calls
    from a target function, showing downstream execution paths and call chains.
    """
    
    def __init__(self, config: Optional[CallTraceConfig] = None):
        """Initialize the call trace visualizer."""
        super().__init__(config or CallTraceConfig())
        self.call_depth_map: dict = {}
    
    def get_visualization_type(self) -> str:
        """Return the visualization type identifier."""
        return VisualizationType.CALL_TRACE.value
    
    def visualize(self, codebase: Codebase, target: Optional[BaseSymbol] = None) -> VisualizationResult:
        """
        Create call trace visualization for the given target function.
        
        Args:
            codebase: The codebase to analyze
            target: Target function to trace calls from (if None, analyzes all functions)
            
        Returns:
            VisualizationResult containing the call graph
        """
        self.reset()
        
        if target is None:
            # Analyze all functions if no target specified
            self._analyze_all_functions(codebase)
        else:
            # Analyze specific target
            if isinstance(target, Function):
                self._trace_function_calls(target, depth=0)
            elif isinstance(target, Class):
                self._trace_class_methods(target)
            else:
                logger.warning(f"Unsupported target type for call trace: {type(target)}")
                return self._finalize_result()
        
        # Update metadata
        self._update_metadata("target", str(target) if target else "all_functions")
        self._update_metadata("max_depth_reached", max(self.call_depth_map.values()) if self.call_depth_map else 0)
        self._update_metadata("total_call_chains", len(self.call_depth_map))
        
        return self._finalize_result()
    
    def _analyze_all_functions(self, codebase: Codebase) -> None:
        """Analyze call relationships for all functions in the codebase."""
        logger.info("Analyzing call relationships for all functions")
        
        # Get entry point functions (functions not called by others)
        all_functions = set(codebase.functions)
        called_functions = set()
        
        # Find all called functions
        for func in codebase.functions:
            for call in func.function_calls:
                if call.function_definition and isinstance(call.function_definition, Function):
                    called_functions.add(call.function_definition)
        
        # Entry points are functions not called by others
        entry_points = all_functions - called_functions
        
        # If no clear entry points, use functions with specific patterns
        if not entry_points:
            entry_points = self._find_likely_entry_points(codebase.functions)
        
        # Trace from each entry point
        for entry_point in entry_points:
            if entry_point not in self.visited:
                self._trace_function_calls(entry_point, depth=0, is_entry_point=True)
    
    def _find_likely_entry_points(self, functions) -> Set[Function]:
        """Find likely entry point functions based on naming patterns."""
        entry_points = set()
        entry_patterns = ['main', 'run', 'start', 'execute', 'init', '__init__']
        
        for func in functions:
            if any(pattern in func.name.lower() for pattern in entry_patterns):
                entry_points.add(func)
        
        # If still no entry points, take first few functions
        if not entry_points:
            entry_points = set(list(functions)[:5])
        
        return entry_points
    
    def _trace_class_methods(self, target_class: Class) -> None:
        """Trace call relationships for all methods in a class."""
        logger.info(f"Tracing method calls for class: {target_class.name}")
        
        # Add the class as root node
        self.add_node(target_class, color=self.config.color_palette.get("StartClass", "#FFE082"))
        
        # Add all methods and trace their calls
        for method in target_class.methods:
            method_name = f"{target_class.name}.{method.name}"
            self.add_node(method, name=method_name, color=self.config.color_palette.get("StartMethod", "#9cdcfe"))
            self.add_edge(target_class, method, relationship_type="contains")
            
            # Trace calls from this method
            self._trace_function_calls(method, depth=0)
    
    def _trace_function_calls(self, source_func: Function, depth: int = 0, is_entry_point: bool = False) -> None:
        """
        Recursively trace function calls from a source function.
        
        Args:
            source_func: The function to trace calls from
            depth: Current recursion depth
            is_entry_point: Whether this is an entry point function
        """
        # Check depth limit
        if depth >= self.config.max_depth:
            logger.debug(f"Reached max depth {self.config.max_depth} for function {source_func.name}")
            return
        
        # Skip external modules if configured
        if isinstance(source_func, ExternalModule):
            return
        
        # Track depth for this function
        self.call_depth_map[source_func] = max(self.call_depth_map.get(source_func, 0), depth)
        
        # Add source function node if not already added
        if source_func not in self.visited:
            node_color = self.config.color_palette.get("StartFunction" if is_entry_point else "PyFunction")
            self.add_node(source_func, 
                         color=node_color,
                         depth=depth,
                         is_entry_point=is_entry_point)
        
        # Trace all function calls from this function
        for call in source_func.function_calls:
            # Skip recursive calls if configured
            if self.should_skip_recursive_call(call, source_func):
                continue
            
            target_func = call.function_definition
            if not target_func:
                continue
            
            # Skip based on configuration
            if self._should_ignore_node(target_func):
                continue
            
            # Determine node color and name
            if isinstance(target_func, ExternalModule):
                node_color = self.config.color_palette.get("ExternalModule", "#f694ff")
                node_name = target_func.name
            elif isinstance(target_func, Class):
                node_color = self.config.color_palette.get("PyClass", "#ffca85")
                node_name = target_func.name
            elif isinstance(target_func, Function):
                node_color = self.config.color_palette.get("PyFunction", "#a277ff")
                node_name = (f"{target_func.parent_class.name}.{target_func.name}" 
                           if target_func.is_method and hasattr(target_func, 'parent_class')
                           else target_func.name)
            else:
                node_color = "#cccccc"
                node_name = str(target_func)
            
            # Add target node if not already visited
            if target_func not in self.visited:
                self.add_node(target_func, 
                             name=node_name,
                             color=node_color,
                             depth=depth + 1)
            
            # Add edge with call metadata
            edge_attrs = self.generate_function_call_metadata(call)
            edge_attrs.update({
                "depth": depth,
                "weight": 1.0,
                "call_frequency": getattr(call, 'frequency', 1)
            })
            
            self.add_edge(source_func, target_func, **edge_attrs)
            
            # Recursively trace calls from the target function
            if isinstance(target_func, Function):
                self._trace_function_calls(target_func, depth + 1)
    
    def get_call_chains(self) -> list:
        """Get all call chains in the visualization."""
        chains = []
        
        # Find all simple paths in the graph
        try:
            # Get all nodes with no incoming edges (entry points)
            entry_points = [node for node in self.graph.nodes() 
                          if self.graph.in_degree(node) == 0]
            
            # Get all nodes with no outgoing edges (leaf nodes)
            leaf_nodes = [node for node in self.graph.nodes() 
                         if self.graph.out_degree(node) == 0]
            
            # Find paths from entry points to leaf nodes
            for entry in entry_points:
                for leaf in leaf_nodes:
                    try:
                        paths = list(nx.all_simple_paths(self.graph, entry, leaf))
                        chains.extend(paths)
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Error computing call chains: {e}")
        
        return chains
    
    def get_critical_functions(self) -> list:
        """Get functions that are critical in the call graph (high centrality)."""
        try:
            # Calculate betweenness centrality
            centrality = nx.betweenness_centrality(self.graph)
            
            # Sort by centrality score
            critical_functions = sorted(centrality.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)
            
            return critical_functions[:10]  # Top 10 critical functions
            
        except Exception as e:
            logger.warning(f"Error computing critical functions: {e}")
            return []

