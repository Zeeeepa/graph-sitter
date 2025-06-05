"""
Base visualization adapter classes for graph_sitter.

This module provides the foundational classes and interfaces that all
specific visualization adapters inherit from, ensuring consistency
and providing common functionality.
"""

import networkx as nx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Set
from dataclasses import dataclass
import json
import logging
from pathlib import Path

from graph_sitter import Codebase
from graph_sitter.core.base_symbol import BaseSymbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.detached_symbols.function_call import FunctionCall

from .config import VisualizationConfig, OutputFormat, DEFAULT_COLOR_PALETTE


logger = logging.getLogger(__name__)


@dataclass
class VisualizationResult:
    """Container for visualization results and metadata."""
    
    graph: nx.DiGraph
    metadata: Dict[str, Any]
    config: VisualizationConfig
    visualization_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "nodes": [
                {
                    "id": str(node),
                    "attributes": data
                }
                for node, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": str(source),
                    "target": str(target),
                    "attributes": data
                }
                for source, target, data in self.graph.edges(data=True)
            ],
            "metadata": self.metadata,
            "visualization_type": self.visualization_type
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_json(self, filepath: Union[str, Path]) -> None:
        """Save result as JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    def save_graphml(self, filepath: Union[str, Path]) -> None:
        """Save graph as GraphML file."""
        nx.write_graphml(self.graph, filepath)


class BaseVisualizationAdapter(ABC):
    """
    Abstract base class for all visualization adapters.
    
    This class provides the common interface and shared functionality
    that all specific visualization adapters must implement.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize the visualization adapter with configuration."""
        self.config = config or VisualizationConfig()
        self.graph = nx.DiGraph()
        self.visited: Set[BaseSymbol] = set()
        self.metadata: Dict[str, Any] = {}
        
        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def visualize(self, codebase: Codebase, target: Optional[BaseSymbol] = None) -> VisualizationResult:
        """
        Create visualization for the given codebase and target.
        
        Args:
            codebase: The codebase to analyze
            target: Optional target symbol to focus the visualization on
            
        Returns:
            VisualizationResult containing the graph and metadata
        """
        pass
    
    @abstractmethod
    def get_visualization_type(self) -> str:
        """Return the type identifier for this visualization."""
        pass
    
    def reset(self) -> None:
        """Reset the adapter state for a new visualization."""
        self.graph = nx.DiGraph()
        self.visited.clear()
        self.metadata.clear()
    
    def add_node(self, node: BaseSymbol, **attributes) -> None:
        """Add a node to the graph with proper attributes."""
        # Generate node attributes
        node_attrs = self._generate_node_attributes(node)
        node_attrs.update(attributes)
        
        # Add to graph
        self.graph.add_node(node, **node_attrs)
        self.visited.add(node)
        
        self.logger.debug(f"Added node: {node} with attributes: {node_attrs}")
    
    def add_edge(self, source: BaseSymbol, target: BaseSymbol, **attributes) -> None:
        """Add an edge to the graph with proper attributes."""
        # Ensure both nodes exist
        if source not in self.graph:
            self.add_node(source)
        if target not in self.graph:
            self.add_node(target)
        
        # Generate edge attributes
        edge_attrs = self._generate_edge_attributes(source, target)
        edge_attrs.update(attributes)
        
        # Add to graph
        self.graph.add_edge(source, target, **edge_attrs)
        
        self.logger.debug(f"Added edge: {source} -> {target} with attributes: {edge_attrs}")
    
    def _generate_node_attributes(self, node: BaseSymbol) -> Dict[str, Any]:
        """Generate standard attributes for a node."""
        attrs = {
            "name": self._get_node_name(node),
            "type": node.__class__.__name__,
            "color": self._get_node_color(node),
        }
        
        # Add source location if available and configured
        if self.config.include_source_locations and hasattr(node, 'filepath'):
            attrs.update({
                "filepath": getattr(node, 'filepath', None),
                "start_point": getattr(node, 'start_point', None),
                "end_point": getattr(node, 'end_point', None),
            })
        
        return attrs
    
    def _generate_edge_attributes(self, source: BaseSymbol, target: BaseSymbol) -> Dict[str, Any]:
        """Generate standard attributes for an edge."""
        return {
            "relationship_type": "generic",
            "weight": 1.0,
        }
    
    def _get_node_name(self, node: BaseSymbol) -> str:
        """Get display name for a node."""
        if isinstance(node, Function):
            if node.is_method and hasattr(node, 'parent_class'):
                return f"{node.parent_class.name}.{node.name}"
            return node.name
        elif isinstance(node, Class):
            return node.name
        elif isinstance(node, ExternalModule):
            return node.name
        else:
            return str(node)
    
    def _get_node_color(self, node: BaseSymbol) -> str:
        """Get color for a node based on its type."""
        node_type = node.__class__.__name__
        return self.config.color_palette.get(node_type, "#cccccc")
    
    def _should_ignore_node(self, node: BaseSymbol) -> bool:
        """Check if a node should be ignored based on configuration."""
        if isinstance(node, ExternalModule) and self.config.ignore_external_modules:
            return True
        if isinstance(node, Class) and self.config.ignore_class_calls:
            return True
        return False
    
    def _update_metadata(self, key: str, value: Any) -> None:
        """Update metadata with a key-value pair."""
        self.metadata[key] = value
    
    def _finalize_result(self) -> VisualizationResult:
        """Create the final visualization result."""
        # Update metadata with graph statistics
        self.metadata.update({
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "is_directed": self.graph.is_directed(),
            "is_connected": nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
        })
        
        return VisualizationResult(
            graph=self.graph,
            metadata=self.metadata,
            config=self.config,
            visualization_type=self.get_visualization_type()
        )


class FunctionCallMixin:
    """Mixin providing common functionality for function call analysis."""
    
    def generate_function_call_metadata(self, call: FunctionCall) -> Dict[str, Any]:
        """Generate metadata for a function call edge."""
        return {
            "call_name": call.name,
            "filepath": call.filepath,
            "start_point": call.start_point,
            "end_point": call.end_point,
            "symbol_name": "FunctionCall",
            "relationship_type": "calls"
        }
    
    def should_skip_recursive_call(self, call: FunctionCall, source_func: Function) -> bool:
        """Check if a recursive call should be skipped."""
        return call.name == source_func.name and not getattr(self.config, 'include_recursive_calls', False)


class DependencyMixin:
    """Mixin providing common functionality for dependency analysis."""
    
    def analyze_symbol_dependencies(self, symbol: BaseSymbol) -> List[BaseSymbol]:
        """Get all dependencies for a symbol."""
        dependencies = []
        
        if hasattr(symbol, 'dependencies'):
            for dep in symbol.dependencies:
                if hasattr(dep, 'resolved_symbol') and dep.resolved_symbol:
                    dependencies.append(dep.resolved_symbol)
                elif isinstance(dep, BaseSymbol):
                    dependencies.append(dep)
        
        return dependencies
    
    def analyze_import_dependencies(self, symbol: BaseSymbol) -> List[BaseSymbol]:
        """Get import-based dependencies for a symbol."""
        dependencies = []
        
        if hasattr(symbol, 'imports'):
            for imp in symbol.imports:
                if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol:
                    dependencies.append(imp.resolved_symbol)
        
        return dependencies


class UsageMixin:
    """Mixin providing common functionality for usage analysis."""
    
    def analyze_symbol_usages(self, symbol: BaseSymbol) -> List[BaseSymbol]:
        """Get all usages of a symbol."""
        usages = []
        
        if hasattr(symbol, 'usages'):
            for usage in symbol.usages:
                if hasattr(usage, 'usage_symbol'):
                    usages.append(usage.usage_symbol)
        
        return usages
    
    def is_http_method(self, symbol: BaseSymbol) -> bool:
        """Check if a symbol represents an HTTP method."""
        if not isinstance(symbol, Function):
            return False
        
        # Common HTTP method patterns
        http_patterns = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        name_lower = symbol.name.lower()
        
        return any(pattern in name_lower for pattern in http_patterns)

