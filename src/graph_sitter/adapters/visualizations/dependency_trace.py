"""
Symbol dependencies visualization adapter.

This module provides visualization of symbol dependencies throughout the codebase,
helping identify tightly coupled components and understand the impact of modifying
shared dependencies.
"""

from typing import Optional, Set, List, Dict
import logging
import networkx as nx

from graph_sitter import Codebase
from graph_sitter.core.base_symbol import BaseSymbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_statement import Import

from .base import BaseVisualizationAdapter, VisualizationResult, DependencyMixin
from .config import DependencyTraceConfig, VisualizationType


logger = logging.getLogger(__name__)


class DependencyTraceVisualizer(BaseVisualizationAdapter, DependencyMixin):
    """
    Visualizer for symbol dependencies and import relationships.
    
    This visualizer maps symbol dependencies throughout the codebase,
    helping identify tightly coupled components and architectural issues.
    """
    
    def __init__(self, config: Optional[DependencyTraceConfig] = None):
        """Initialize the dependency trace visualizer."""
        super().__init__(config or DependencyTraceConfig())
        self.dependency_levels: Dict[BaseSymbol, int] = {}
        self.circular_dependencies: List[List[BaseSymbol]] = []
    
    def get_visualization_type(self) -> str:
        """Return the visualization type identifier."""
        return VisualizationType.DEPENDENCY_TRACE.value
    
    def visualize(self, codebase: Codebase, target: Optional[BaseSymbol] = None) -> VisualizationResult:
        """
        Create dependency trace visualization for the given target symbol.
        
        Args:
            codebase: The codebase to analyze
            target: Target symbol to trace dependencies from (if None, analyzes all symbols)
            
        Returns:
            VisualizationResult containing the dependency graph
        """
        self.reset()
        
        if target is None:
            # Analyze dependencies for all symbols
            self._analyze_all_dependencies(codebase)
        else:
            # Analyze specific target
            self._trace_symbol_dependencies(target, depth=0)
        
        # Detect circular dependencies if configured
        if self.config.show_circular_dependencies:
            self._detect_circular_dependencies()
        
        # Update metadata
        self._update_metadata("target", str(target) if target else "all_symbols")
        self._update_metadata("max_dependency_level", max(self.dependency_levels.values()) if self.dependency_levels else 0)
        self._update_metadata("circular_dependencies_count", len(self.circular_dependencies))
        self._update_metadata("circular_dependencies", [
            [str(symbol) for symbol in cycle] for cycle in self.circular_dependencies
        ])
        
        return self._finalize_result()
    
    def _analyze_all_dependencies(self, codebase: Codebase) -> None:
        """Analyze dependencies for all symbols in the codebase."""
        logger.info("Analyzing dependencies for all symbols")
        
        # Collect all symbols
        all_symbols = []
        all_symbols.extend(codebase.functions)
        all_symbols.extend(codebase.classes)
        
        # Add file-level symbols if available
        for file in codebase.files:
            if hasattr(file, 'symbols'):
                all_symbols.extend(file.symbols)
        
        # Group symbols by package/module if configured
        if self.config.group_by_package:
            self._group_symbols_by_package(all_symbols)
        
        # Trace dependencies for each symbol
        for symbol in all_symbols:
            if symbol not in self.visited:
                self._trace_symbol_dependencies(symbol, depth=0)
    
    def _group_symbols_by_package(self, symbols: List[BaseSymbol]) -> None:
        """Group symbols by their package/module for better visualization."""
        package_groups = {}
        
        for symbol in symbols:
            if hasattr(symbol, 'filepath'):
                # Extract package name from filepath
                filepath = symbol.filepath
                if filepath:
                    package = self._extract_package_name(filepath)
                    if package not in package_groups:
                        package_groups[package] = []
                    package_groups[package].append(symbol)
        
        # Add package nodes to the graph
        for package, package_symbols in package_groups.items():
            if len(package_symbols) > 1:  # Only create package nodes for multi-symbol packages
                package_node = f"package:{package}"
                self.graph.add_node(package_node, 
                                  name=package,
                                  type="Package",
                                  color=self.config.color_palette.get("Package", "#e1f5fe"))
                
                # Connect symbols to their package
                for symbol in package_symbols:
                    if symbol in self.graph:
                        self.add_edge(package_node, symbol, relationship_type="contains")
    
    def _extract_package_name(self, filepath: str) -> str:
        """Extract package name from a file path."""
        # Simple package extraction - can be enhanced
        parts = filepath.split('/')
        if len(parts) > 1:
            return parts[-2]  # Parent directory
        return "root"
    
    def _trace_symbol_dependencies(self, symbol: BaseSymbol, depth: int = 0) -> None:
        """
        Recursively trace dependencies for a symbol.
        
        Args:
            symbol: The symbol to trace dependencies from
            depth: Current recursion depth
        """
        # Check depth limit
        if depth >= self.config.max_depth:
            logger.debug(f"Reached max depth {self.config.max_depth} for symbol {symbol}")
            return
        
        # Skip if already visited
        if symbol in self.visited:
            return
        
        # Track dependency level
        self.dependency_levels[symbol] = depth
        
        # Add symbol node
        self.add_node(symbol, 
                     depth=depth,
                     dependency_level=depth)
        
        # Analyze different types of dependencies
        dependencies = []
        
        # Symbol dependencies
        if self.config.include_symbol_dependencies:
            dependencies.extend(self.analyze_symbol_dependencies(symbol))
        
        # Import dependencies
        if self.config.include_import_dependencies:
            dependencies.extend(self.analyze_import_dependencies(symbol))
        
        # Additional dependency types based on symbol type
        if isinstance(symbol, Class):
            dependencies.extend(self._analyze_class_dependencies(symbol))
        elif isinstance(symbol, Function):
            dependencies.extend(self._analyze_function_dependencies(symbol))
        
        # Process each dependency
        for dep_symbol in dependencies:
            if dep_symbol and not self._should_ignore_node(dep_symbol):
                # Add dependency node if not already added
                if dep_symbol not in self.visited:
                    self._trace_symbol_dependencies(dep_symbol, depth + 1)
                
                # Add dependency edge
                edge_attrs = {
                    "relationship_type": "depends_on",
                    "dependency_type": self._get_dependency_type(symbol, dep_symbol),
                    "depth": depth,
                    "weight": self._calculate_dependency_weight(symbol, dep_symbol)
                }
                
                self.add_edge(symbol, dep_symbol, **edge_attrs)
    
    def _analyze_class_dependencies(self, class_symbol: Class) -> List[BaseSymbol]:
        """Analyze dependencies specific to class symbols."""
        dependencies = []
        
        # Inheritance dependencies
        if hasattr(class_symbol, 'superclasses'):
            dependencies.extend(class_symbol.superclasses)
        
        # Method dependencies
        if hasattr(class_symbol, 'methods'):
            for method in class_symbol.methods:
                dependencies.extend(self.analyze_symbol_dependencies(method))
        
        # Attribute dependencies
        if hasattr(class_symbol, 'attributes'):
            for attr in class_symbol.attributes:
                if hasattr(attr, 'type_annotation'):
                    # Add type annotation as dependency
                    dependencies.append(attr.type_annotation)
        
        return dependencies
    
    def _analyze_function_dependencies(self, function_symbol: Function) -> List[BaseSymbol]:
        """Analyze dependencies specific to function symbols."""
        dependencies = []
        
        # Parameter type dependencies
        if hasattr(function_symbol, 'parameters'):
            for param in function_symbol.parameters:
                if hasattr(param, 'type_annotation') and param.type_annotation:
                    dependencies.append(param.type_annotation)
        
        # Return type dependencies
        if hasattr(function_symbol, 'return_type') and function_symbol.return_type:
            dependencies.append(function_symbol.return_type)
        
        # Function call dependencies (different from call trace - focuses on symbols)
        if hasattr(function_symbol, 'function_calls'):
            for call in function_symbol.function_calls:
                if call.function_definition:
                    dependencies.append(call.function_definition)
        
        return dependencies
    
    def _get_dependency_type(self, source: BaseSymbol, target: BaseSymbol) -> str:
        """Determine the type of dependency relationship."""
        if isinstance(source, Class) and isinstance(target, Class):
            # Check if it's inheritance
            if hasattr(source, 'superclasses') and target in source.superclasses:
                return "inherits"
            return "class_dependency"
        
        elif isinstance(source, Function) and isinstance(target, Function):
            return "function_call"
        
        elif isinstance(target, ExternalModule):
            return "import"
        
        else:
            return "generic_dependency"
    
    def _calculate_dependency_weight(self, source: BaseSymbol, target: BaseSymbol) -> float:
        """Calculate the weight/strength of a dependency relationship."""
        # Base weight
        weight = 1.0
        
        # Increase weight for inheritance relationships
        if self._get_dependency_type(source, target) == "inherits":
            weight = 3.0
        
        # Increase weight for same-module dependencies
        if (hasattr(source, 'filepath') and hasattr(target, 'filepath') and 
            source.filepath == target.filepath):
            weight *= 1.5
        
        # Decrease weight for external dependencies
        if isinstance(target, ExternalModule):
            weight *= 0.5
        
        return weight
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies in the graph."""
        try:
            # Find strongly connected components
            strongly_connected = list(nx.strongly_connected_components(self.graph))
            
            # Filter out single-node components (not circular)
            self.circular_dependencies = [
                list(component) for component in strongly_connected 
                if len(component) > 1
            ]
            
            # Mark circular dependency nodes
            for cycle in self.circular_dependencies:
                for node in cycle:
                    if node in self.graph:
                        self.graph.nodes[node]['is_circular'] = True
                        self.graph.nodes[node]['color'] = self.config.color_palette.get("CircularDependency", "#ff6b6b")
            
            logger.info(f"Detected {len(self.circular_dependencies)} circular dependencies")
            
        except Exception as e:
            logger.warning(f"Error detecting circular dependencies: {e}")
    
    def get_dependency_metrics(self) -> Dict[str, any]:
        """Calculate dependency metrics for the visualization."""
        metrics = {}
        
        try:
            # In-degree and out-degree analysis
            in_degrees = dict(self.graph.in_degree())
            out_degrees = dict(self.graph.out_degree())
            
            # Most depended upon symbols (high in-degree)
            most_depended = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Most dependent symbols (high out-degree)
            most_dependent = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Dependency depth analysis
            max_depth = max(self.dependency_levels.values()) if self.dependency_levels else 0
            depth_distribution = {}
            for depth in self.dependency_levels.values():
                depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
            
            metrics.update({
                "most_depended_upon": [(str(symbol), count) for symbol, count in most_depended],
                "most_dependent": [(str(symbol), count) for symbol, count in most_dependent],
                "max_dependency_depth": max_depth,
                "depth_distribution": depth_distribution,
                "total_dependencies": self.graph.number_of_edges(),
                "dependency_density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0
            })
            
        except Exception as e:
            logger.warning(f"Error calculating dependency metrics: {e}")
        
        return metrics

