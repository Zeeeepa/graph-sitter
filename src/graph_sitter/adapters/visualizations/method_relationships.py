"""
Class method relationships visualization adapter.

This module provides comprehensive visualization of class method interactions,
helping developers understand class cohesion and identify architectural issues.
"""

from typing import Optional, Set, List, Dict
import logging
import networkx as nx

from graph_sitter import Codebase
from graph_sitter.core.base_symbol import BaseSymbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.external_module import ExternalModule

from .base import BaseVisualizationAdapter, VisualizationResult, FunctionCallMixin
from .config import MethodRelationshipsConfig, VisualizationType


logger = logging.getLogger(__name__)


class MethodRelationshipsVisualizer(BaseVisualizationAdapter, FunctionCallMixin):
    """
    Visualizer for class method relationships and interactions.
    
    This visualizer creates comprehensive views of class method interactions,
    helping understand class cohesion and identify architectural opportunities.
    """
    
    def __init__(self, config: Optional[MethodRelationshipsConfig] = None):
        """Initialize the method relationships visualizer."""
        super().__init__(config or MethodRelationshipsConfig())
        self.method_call_matrix: Dict[tuple, int] = {}
        self.cohesion_metrics: Dict[Class, float] = {}
        self.inheritance_chains: List[List[Class]] = []
    
    def get_visualization_type(self) -> str:
        """Return the visualization type identifier."""
        return VisualizationType.METHOD_RELATIONSHIPS.value
    
    def visualize(self, codebase: Codebase, target: Optional[BaseSymbol] = None) -> VisualizationResult:
        """
        Create method relationships visualization for the given target class.
        
        Args:
            codebase: The codebase to analyze
            target: Target class to analyze method relationships for
            
        Returns:
            VisualizationResult containing the method relationships graph
        """
        self.reset()
        
        if target is None:
            # Analyze all classes if no target specified
            self._analyze_all_classes(codebase)
        elif isinstance(target, Class):
            # Analyze specific target class
            self._analyze_class_methods(target)
        else:
            logger.warning(f"Method relationships visualization requires a Class target, got {type(target)}")
            return self._finalize_result()
        
        # Calculate cohesion metrics
        self._calculate_cohesion_metrics()
        
        # Analyze inheritance if configured
        if self.config.show_inheritance_chain:
            self._analyze_inheritance_chains(codebase)
        
        # Update metadata
        self._update_metadata("target", str(target) if target else "all_classes")
        self._update_metadata("classes_analyzed", len(self.cohesion_metrics))
        self._update_metadata("method_interactions", len(self.method_call_matrix))
        self._update_metadata("inheritance_chains", len(self.inheritance_chains))
        
        if self.cohesion_metrics:
            avg_cohesion = sum(self.cohesion_metrics.values()) / len(self.cohesion_metrics)
            self._update_metadata("average_cohesion", avg_cohesion)
            self._update_metadata("cohesion_metrics", {
                str(cls): metric for cls, metric in self.cohesion_metrics.items()
            })
        
        return self._finalize_result()
    
    def _analyze_all_classes(self, codebase: Codebase) -> None:
        """Analyze method relationships for all classes in the codebase."""
        logger.info("Analyzing method relationships for all classes")
        
        for class_obj in codebase.classes:
            self._analyze_class_methods(class_obj)
    
    def _analyze_class_methods(self, target_class: Class) -> None:
        """
        Analyze method relationships within a specific class.
        
        Args:
            target_class: The class to analyze
        """
        logger.info(f"Analyzing method relationships for class: {target_class.name}")
        
        # Add the class as root node
        self.add_node(target_class, 
                     color=self.config.color_palette.get("StartClass", "#FFE082"),
                     node_type="class",
                     is_target=True)
        
        # Get all methods (including private if configured)
        methods = self._get_methods_to_analyze(target_class)
        
        # Add method nodes and connect to class
        for method in methods:
            self._add_method_node(target_class, method)
        
        # Analyze method-to-method relationships
        for method in methods:
            self._analyze_method_calls(method, target_class)
        
        # Group methods by access level if configured
        if self.config.group_by_access_level:
            self._group_methods_by_access_level(target_class, methods)
    
    def _get_methods_to_analyze(self, class_obj: Class) -> List[Function]:
        """Get the list of methods to analyze based on configuration."""
        if not hasattr(class_obj, 'methods'):
            return []
        
        methods = []
        for method in class_obj.methods:
            # Include private methods if configured
            if not self.config.include_private_methods and method.name.startswith('_'):
                continue
            methods.append(method)
        
        return methods
    
    def _add_method_node(self, class_obj: Class, method: Function) -> None:
        """Add a method node to the graph."""
        method_name = f"{class_obj.name}.{method.name}"
        
        # Determine method color based on access level and type
        method_color = self._get_method_color(method)
        
        # Check if method is overridden
        is_overridden = self._is_overridden_method(class_obj, method)
        
        self.add_node(method,
                     name=method_name,
                     color=method_color,
                     node_type="method",
                     access_level=self._get_access_level(method),
                     is_overridden=is_overridden,
                     class_name=class_obj.name)
        
        # Connect method to its class
        self.add_edge(class_obj, method, 
                     relationship_type="contains",
                     edge_type="containment")
    
    def _get_method_color(self, method: Function) -> str:
        """Get color for a method based on its characteristics."""
        # Special method colors
        if method.name.startswith('__') and method.name.endswith('__'):
            return self.config.color_palette.get("SpecialMethod", "#ff9800")
        
        # Private method colors
        elif method.name.startswith('_'):
            return self.config.color_palette.get("PrivateMethod", "#9e9e9e")
        
        # Property methods
        elif self._is_property_method(method):
            return self.config.color_palette.get("PropertyMethod", "#4caf50")
        
        # Static/class methods
        elif self._is_static_or_class_method(method):
            return self.config.color_palette.get("StaticMethod", "#2196f3")
        
        # Regular public methods
        else:
            return self.config.color_palette.get("StartMethod", "#9cdcfe")
    
    def _get_access_level(self, method: Function) -> str:
        """Determine the access level of a method."""
        if method.name.startswith('__') and method.name.endswith('__'):
            return "special"
        elif method.name.startswith('_'):
            return "private"
        else:
            return "public"
    
    def _is_overridden_method(self, class_obj: Class, method: Function) -> bool:
        """Check if a method is overridden from a parent class."""
        if not hasattr(class_obj, 'superclasses'):
            return False
        
        for superclass in class_obj.superclasses:
            if hasattr(superclass, 'methods'):
                for parent_method in superclass.methods:
                    if parent_method.name == method.name:
                        return True
        
        return False
    
    def _is_property_method(self, method: Function) -> bool:
        """Check if a method is a property getter/setter."""
        # Simple heuristic - can be enhanced with decorator analysis
        property_patterns = ['get_', 'set_', '_get', '_set']
        return any(pattern in method.name.lower() for pattern in property_patterns)
    
    def _is_static_or_class_method(self, method: Function) -> bool:
        """Check if a method is static or a class method."""
        # This would need decorator analysis in a real implementation
        # For now, use naming heuristics
        if hasattr(method, 'decorators'):
            decorator_names = [d.name for d in method.decorators if hasattr(d, 'name')]
            return 'staticmethod' in decorator_names or 'classmethod' in decorator_names
        
        return False
    
    def _analyze_method_calls(self, method: Function, parent_class: Class) -> None:
        """Analyze calls made by a method to other methods."""
        if not hasattr(method, 'function_calls'):
            return
        
        for call in method.function_calls:
            # Skip recursive calls if configured
            if self.should_skip_recursive_call(call, method):
                continue
            
            target_func = call.function_definition
            if not target_func:
                continue
            
            # Skip external calls if configured
            if self._should_ignore_node(target_func):
                continue
            
            # Track method call relationships
            call_key = (method, target_func)
            self.method_call_matrix[call_key] = self.method_call_matrix.get(call_key, 0) + 1
            
            # Add target node if it's not already in the graph
            if target_func not in self.visited:
                self._add_external_call_node(target_func)
            
            # Add call relationship edge
            edge_attrs = self.generate_function_call_metadata(call)
            edge_attrs.update({
                "relationship_type": "calls",
                "call_frequency": self.method_call_matrix[call_key],
                "is_internal": self._is_internal_call(method, target_func, parent_class),
                "call_type": self._get_call_type(method, target_func, parent_class)
            })
            
            self.add_edge(method, target_func, **edge_attrs)
    
    def _add_external_call_node(self, target_func: BaseSymbol) -> None:
        """Add a node for an external function call."""
        if isinstance(target_func, Function):
            # Check if it's a method of another class
            if target_func.is_method and hasattr(target_func, 'parent_class'):
                node_name = f"{target_func.parent_class.name}.{target_func.name}"
                node_color = self.config.color_palette.get("ExternalMethod", "#ff9800")
            else:
                node_name = target_func.name
                node_color = self.config.color_palette.get("PyFunction", "#a277ff")
        
        elif isinstance(target_func, Class):
            node_name = target_func.name
            node_color = self.config.color_palette.get("PyClass", "#ffca85")
        
        elif isinstance(target_func, ExternalModule):
            node_name = target_func.name
            node_color = self.config.color_palette.get("ExternalModule", "#f694ff")
        
        else:
            node_name = str(target_func)
            node_color = "#cccccc"
        
        self.add_node(target_func,
                     name=node_name,
                     color=node_color,
                     node_type="external_call")
    
    def _is_internal_call(self, source_method: Function, target_func: BaseSymbol, parent_class: Class) -> bool:
        """Check if a call is internal to the class."""
        if not isinstance(target_func, Function):
            return False
        
        # Check if target is a method of the same class
        if (target_func.is_method and hasattr(target_func, 'parent_class') and 
            target_func.parent_class == parent_class):
            return True
        
        return False
    
    def _get_call_type(self, source_method: Function, target_func: BaseSymbol, parent_class: Class) -> str:
        """Determine the type of method call."""
        if self._is_internal_call(source_method, target_func, parent_class):
            return "internal"
        
        elif isinstance(target_func, Function) and target_func.is_method:
            return "external_method"
        
        elif isinstance(target_func, Function):
            return "function_call"
        
        elif isinstance(target_func, Class):
            return "constructor_call"
        
        else:
            return "other"
    
    def _group_methods_by_access_level(self, class_obj: Class, methods: List[Function]) -> None:
        """Group methods by access level for better visualization."""
        access_groups = {
            "public": [],
            "private": [],
            "special": []
        }
        
        for method in methods:
            access_level = self._get_access_level(method)
            access_groups[access_level].append(method)
        
        # Create group nodes
        for access_level, group_methods in access_groups.items():
            if group_methods:
                group_node = f"{class_obj.name}_{access_level}_methods"
                group_color = {
                    "public": "#e8f5e8",
                    "private": "#f5f5f5", 
                    "special": "#fff3e0"
                }.get(access_level, "#f0f0f0")
                
                self.graph.add_node(group_node,
                                  name=f"{access_level.title()} Methods",
                                  color=group_color,
                                  node_type="method_group")
                
                # Connect class to group
                self.add_edge(class_obj, group_node, 
                             relationship_type="contains_group",
                             edge_type="grouping")
                
                # Connect methods to group
                for method in group_methods:
                    self.add_edge(group_node, method,
                                 relationship_type="groups",
                                 edge_type="grouping")
    
    def _analyze_inheritance_chains(self, codebase: Codebase) -> None:
        """Analyze inheritance chains in the codebase."""
        try:
            # Build inheritance graph
            inheritance_graph = nx.DiGraph()
            
            for class_obj in codebase.classes:
                inheritance_graph.add_node(class_obj)
                
                if hasattr(class_obj, 'superclasses'):
                    for superclass in class_obj.superclasses:
                        inheritance_graph.add_edge(superclass, class_obj)
                        
                        # Add inheritance edge to main graph if both classes are present
                        if superclass in self.graph and class_obj in self.graph:
                            self.add_edge(superclass, class_obj,
                                         relationship_type="inherits",
                                         edge_type="inheritance",
                                         color="#ff5722")
            
            # Find inheritance chains
            for node in inheritance_graph.nodes():
                if inheritance_graph.in_degree(node) == 0:  # Root class
                    # Find all paths from this root
                    for target in inheritance_graph.nodes():
                        if inheritance_graph.out_degree(target) == 0:  # Leaf class
                            try:
                                paths = list(nx.all_simple_paths(inheritance_graph, node, target))
                                self.inheritance_chains.extend(paths)
                            except:
                                continue
            
        except Exception as e:
            logger.warning(f"Error analyzing inheritance chains: {e}")
    
    def _calculate_cohesion_metrics(self) -> None:
        """Calculate cohesion metrics for analyzed classes."""
        try:
            # Group methods by class
            class_methods = {}
            for node in self.graph.nodes():
                if isinstance(node, Function) and hasattr(node, 'parent_class'):
                    parent_class = node.parent_class
                    if parent_class not in class_methods:
                        class_methods[parent_class] = []
                    class_methods[parent_class].append(node)
            
            # Calculate cohesion for each class
            for class_obj, methods in class_methods.items():
                cohesion = self._calculate_class_cohesion(class_obj, methods)
                self.cohesion_metrics[class_obj] = cohesion
                
                # Update class node with cohesion info
                if class_obj in self.graph:
                    self.graph.nodes[class_obj]['cohesion'] = cohesion
                    self.graph.nodes[class_obj]['cohesion_level'] = self._get_cohesion_level(cohesion)
            
        except Exception as e:
            logger.warning(f"Error calculating cohesion metrics: {e}")
    
    def _calculate_class_cohesion(self, class_obj: Class, methods: List[Function]) -> float:
        """Calculate cohesion metric for a class based on method interactions."""
        if len(methods) <= 1:
            return 1.0  # Single method or no methods = perfect cohesion
        
        # Count internal method calls
        internal_calls = 0
        total_possible_calls = len(methods) * (len(methods) - 1)  # n * (n-1)
        
        for method in methods:
            for call_key, frequency in self.method_call_matrix.items():
                source, target = call_key
                if (source == method and target in methods and 
                    self._is_internal_call(source, target, class_obj)):
                    internal_calls += frequency
        
        # Cohesion = internal calls / total possible calls
        if total_possible_calls == 0:
            return 1.0
        
        cohesion = min(internal_calls / total_possible_calls, 1.0)
        return cohesion
    
    def _get_cohesion_level(self, cohesion: float) -> str:
        """Get cohesion level description."""
        if cohesion >= 0.8:
            return "high"
        elif cohesion >= 0.5:
            return "medium"
        elif cohesion >= 0.2:
            return "low"
        else:
            return "very_low"

