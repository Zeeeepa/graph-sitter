"""
Function blast radius visualization adapter.

This module provides visualization of the impact radius of potential changes,
showing all code paths that could be affected by modifying a particular
function or symbol.
"""

from typing import Optional, Set, List, Dict
import logging
import networkx as nx

from graph_sitter import Codebase
from graph_sitter.core.base_symbol import BaseSymbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.external_module import ExternalModule

from .base import BaseVisualizationAdapter, VisualizationResult, UsageMixin
from .config import BlastRadiusConfig, VisualizationType


logger = logging.getLogger(__name__)


class BlastRadiusVisualizer(BaseVisualizationAdapter, UsageMixin):
    """
    Visualizer for function/symbol blast radius and impact analysis.
    
    This visualizer shows the impact radius of potential changes by revealing
    all code paths that could be affected by modifying a particular function or symbol.
    """
    
    def __init__(self, config: Optional[BlastRadiusConfig] = None):
        """Initialize the blast radius visualizer."""
        super().__init__(config or BlastRadiusConfig())
        self.impact_levels: Dict[BaseSymbol, int] = {}
        self.critical_paths: List[List[BaseSymbol]] = []
        self.usage_frequency: Dict[BaseSymbol, int] = {}
    
    def get_visualization_type(self) -> str:
        """Return the visualization type identifier."""
        return VisualizationType.BLAST_RADIUS.value
    
    def visualize(self, codebase: Codebase, target: Optional[BaseSymbol] = None) -> VisualizationResult:
        """
        Create blast radius visualization for the given target symbol.
        
        Args:
            codebase: The codebase to analyze
            target: Target symbol to analyze blast radius for
            
        Returns:
            VisualizationResult containing the blast radius graph
        """
        self.reset()
        
        if target is None:
            logger.warning("Blast radius visualization requires a target symbol")
            return self._finalize_result()
        
        # Start blast radius analysis from the target
        self._analyze_blast_radius(target, depth=0)
        
        # Calculate impact metrics
        self._calculate_impact_metrics()
        
        # Find critical paths if configured
        if self.config.highlight_critical_paths:
            self._find_critical_paths(target)
        
        # Update metadata
        self._update_metadata("target", str(target))
        self._update_metadata("max_impact_level", max(self.impact_levels.values()) if self.impact_levels else 0)
        self._update_metadata("total_affected_symbols", len(self.impact_levels))
        self._update_metadata("critical_paths_count", len(self.critical_paths))
        
        if self.config.show_impact_metrics:
            self._update_metadata("impact_metrics", self._get_impact_metrics())
        
        return self._finalize_result()
    
    def _analyze_blast_radius(self, symbol: BaseSymbol, depth: int = 0) -> None:
        """
        Recursively analyze the blast radius of a symbol.
        
        Args:
            symbol: The symbol to analyze blast radius for
            depth: Current analysis depth (impact level)
        """
        # Check depth limit
        if depth >= self.config.max_depth:
            logger.debug(f"Reached max depth {self.config.max_depth} for symbol {symbol}")
            return
        
        # Skip if already visited at a lower or equal impact level
        if symbol in self.impact_levels and self.impact_levels[symbol] <= depth:
            return
        
        # Track impact level
        self.impact_levels[symbol] = depth
        
        # Add symbol node with impact level styling
        node_color = self._get_impact_color(depth)
        if depth == 0:
            # Target symbol gets special styling
            node_color = self.config.color_palette.get("StartFunction", "#ff6b6b")
        
        self.add_node(symbol, 
                     impact_level=depth,
                     color=node_color,
                     is_target=(depth == 0))
        
        # Analyze usages of this symbol
        usages = self.analyze_symbol_usages(symbol)
        
        # Filter usages based on configuration
        filtered_usages = self._filter_usages(usages)
        
        # Process each usage
        for usage_symbol in filtered_usages:
            if usage_symbol and not self._should_ignore_node(usage_symbol):
                # Track usage frequency
                self.usage_frequency[usage_symbol] = self.usage_frequency.get(usage_symbol, 0) + 1
                
                # Recursively analyze the usage
                self._analyze_blast_radius(usage_symbol, depth + 1)
                
                # Add edge showing impact relationship
                edge_attrs = {
                    "relationship_type": "impacts",
                    "impact_level": depth,
                    "usage_type": self._get_usage_type(symbol, usage_symbol),
                    "weight": self._calculate_impact_weight(symbol, usage_symbol),
                    "is_critical": self._is_critical_usage(symbol, usage_symbol)
                }
                
                self.add_edge(symbol, usage_symbol, **edge_attrs)
    
    def _filter_usages(self, usages: List[BaseSymbol]) -> List[BaseSymbol]:
        """Filter usages based on configuration settings."""
        filtered = []
        
        for usage in usages:
            # Skip test usages if configured
            if not self.config.include_test_usages and self._is_test_symbol(usage):
                continue
            
            # Include the usage
            filtered.append(usage)
        
        return filtered
    
    def _is_test_symbol(self, symbol: BaseSymbol) -> bool:
        """Check if a symbol is related to testing."""
        if not hasattr(symbol, 'name'):
            return False
        
        name_lower = symbol.name.lower()
        test_patterns = ['test_', '_test', 'test', 'spec_', '_spec']
        
        # Check name patterns
        if any(pattern in name_lower for pattern in test_patterns):
            return True
        
        # Check file path patterns
        if hasattr(symbol, 'filepath') and symbol.filepath:
            filepath_lower = symbol.filepath.lower()
            if any(pattern in filepath_lower for pattern in ['test', 'spec']):
                return True
        
        return False
    
    def _get_usage_type(self, source: BaseSymbol, target: BaseSymbol) -> str:
        """Determine the type of usage relationship."""
        if isinstance(target, Function):
            if self.is_http_method(target):
                return "http_endpoint"
            elif self._is_test_symbol(target):
                return "test_usage"
            else:
                return "function_usage"
        
        elif isinstance(target, Class):
            return "class_usage"
        
        elif isinstance(target, ExternalModule):
            return "external_usage"
        
        else:
            return "generic_usage"
    
    def _calculate_impact_weight(self, source: BaseSymbol, target: BaseSymbol) -> float:
        """Calculate the impact weight of a usage relationship."""
        base_weight = 1.0
        
        # Weight by usage frequency if configured
        if self.config.weight_by_usage_frequency:
            frequency = self.usage_frequency.get(target, 1)
            base_weight *= min(frequency / 10.0, 3.0)  # Cap at 3x weight
        
        # Increase weight for critical usage types
        usage_type = self._get_usage_type(source, target)
        if usage_type == "http_endpoint":
            base_weight *= 2.0
        elif usage_type == "test_usage":
            base_weight *= 0.5  # Tests are less critical for impact
        
        # Increase weight for same-file usages (tighter coupling)
        if (hasattr(source, 'filepath') and hasattr(target, 'filepath') and 
            source.filepath == target.filepath):
            base_weight *= 1.5
        
        return base_weight
    
    def _is_critical_usage(self, source: BaseSymbol, target: BaseSymbol) -> bool:
        """Determine if a usage relationship is critical."""
        # HTTP endpoints are critical
        if self.is_http_method(target):
            return True
        
        # High-frequency usages are critical
        if self.usage_frequency.get(target, 0) > 5:
            return True
        
        # Public API methods are critical
        if isinstance(target, Function) and hasattr(target, 'name'):
            if not target.name.startswith('_'):  # Public method
                return True
        
        return False
    
    def _get_impact_color(self, impact_level: int) -> str:
        """Get color based on impact level."""
        # Color gradient from red (high impact) to yellow (low impact)
        if impact_level == 0:
            return "#ff0000"  # Red for target
        elif impact_level == 1:
            return "#ff4500"  # Orange-red for immediate impact
        elif impact_level == 2:
            return "#ff8c00"  # Orange for secondary impact
        elif impact_level == 3:
            return "#ffd700"  # Gold for tertiary impact
        else:
            return "#ffff99"  # Light yellow for distant impact
    
    def _calculate_impact_metrics(self) -> None:
        """Calculate various impact metrics for the blast radius."""
        if not self.impact_levels:
            return
        
        # Impact level distribution
        level_distribution = {}
        for level in self.impact_levels.values():
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # Critical symbols (high usage frequency)
        critical_symbols = [
            symbol for symbol, freq in self.usage_frequency.items() 
            if freq > 3
        ]
        
        # Update metadata
        self._update_metadata("impact_level_distribution", level_distribution)
        self._update_metadata("critical_symbols", [str(s) for s in critical_symbols])
        self._update_metadata("usage_frequency_stats", {
            "max_frequency": max(self.usage_frequency.values()) if self.usage_frequency else 0,
            "avg_frequency": sum(self.usage_frequency.values()) / len(self.usage_frequency) if self.usage_frequency else 0
        })
    
    def _find_critical_paths(self, target: BaseSymbol) -> None:
        """Find critical paths from the target to high-impact symbols."""
        try:
            # Find symbols with high impact (high usage frequency or critical usage types)
            high_impact_symbols = []
            
            for symbol in self.graph.nodes():
                if symbol == target:
                    continue
                
                # Check if it's a critical symbol
                if (self.usage_frequency.get(symbol, 0) > 3 or 
                    self.is_http_method(symbol) or
                    self._is_public_api(symbol)):
                    high_impact_symbols.append(symbol)
            
            # Find paths from target to high-impact symbols
            for high_impact_symbol in high_impact_symbols:
                try:
                    # Find shortest path
                    if nx.has_path(self.graph, target, high_impact_symbol):
                        path = nx.shortest_path(self.graph, target, high_impact_symbol)
                        if len(path) > 1:  # Exclude direct connections
                            self.critical_paths.append(path)
                except:
                    continue
            
            # Mark critical path edges
            for path in self.critical_paths:
                for i in range(len(path) - 1):
                    if self.graph.has_edge(path[i], path[i + 1]):
                        self.graph.edges[path[i], path[i + 1]]['is_critical_path'] = True
                        self.graph.edges[path[i], path[i + 1]]['color'] = "#ff0000"
            
        except Exception as e:
            logger.warning(f"Error finding critical paths: {e}")
    
    def _is_public_api(self, symbol: BaseSymbol) -> bool:
        """Check if a symbol is part of the public API."""
        if not isinstance(symbol, Function):
            return False
        
        # Public methods don't start with underscore
        if hasattr(symbol, 'name') and not symbol.name.startswith('_'):
            return True
        
        return False
    
    def _get_impact_metrics(self) -> Dict[str, any]:
        """Get comprehensive impact metrics."""
        metrics = {}
        
        try:
            # Blast radius size
            metrics["blast_radius_size"] = len(self.impact_levels)
            
            # Impact distribution by level
            level_counts = {}
            for level in self.impact_levels.values():
                level_counts[level] = level_counts.get(level, 0) + 1
            metrics["impact_by_level"] = level_counts
            
            # Critical impact analysis
            critical_count = sum(1 for symbol in self.graph.nodes() 
                               if self.graph.nodes[symbol].get('is_critical', False))
            metrics["critical_impacts"] = critical_count
            
            # Usage frequency analysis
            if self.usage_frequency:
                metrics["usage_frequency"] = {
                    "max": max(self.usage_frequency.values()),
                    "avg": sum(self.usage_frequency.values()) / len(self.usage_frequency),
                    "total_usages": sum(self.usage_frequency.values())
                }
            
            # Path analysis
            metrics["critical_paths_count"] = len(self.critical_paths)
            if self.critical_paths:
                metrics["longest_critical_path"] = max(len(path) for path in self.critical_paths)
                metrics["shortest_critical_path"] = min(len(path) for path in self.critical_paths)
            
        except Exception as e:
            logger.warning(f"Error calculating impact metrics: {e}")
        
        return metrics

