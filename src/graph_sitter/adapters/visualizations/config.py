"""
Configuration settings for graph_sitter visualization adapters.

This module provides configuration classes and constants used across
all visualization adapters to ensure consistency and customizability.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class VisualizationType(Enum):
    """Enumeration of available visualization types."""
    CALL_TRACE = "call_trace"
    DEPENDENCY_TRACE = "dependency_trace"
    BLAST_RADIUS = "blast_radius"
    METHOD_RELATIONSHIPS = "method_relationships"


class OutputFormat(Enum):
    """Supported output formats for visualizations."""
    NETWORKX = "networkx"
    HTML = "html"
    JSON = "json"
    PNG = "png"
    SVG = "svg"
    GRAPHML = "graphml"


@dataclass
class VisualizationConfig:
    """Base configuration for all visualization adapters."""
    
    # Depth and traversal settings
    max_depth: int = 100
    ignore_external_modules: bool = False
    ignore_class_calls: bool = True
    
    # Visual styling
    color_palette: Dict[str, str] = None
    node_size_range: tuple = (100, 1000)
    edge_width_range: tuple = (1, 5)
    
    # Output settings
    output_format: OutputFormat = OutputFormat.NETWORKX
    include_metadata: bool = True
    include_source_locations: bool = True
    
    # Performance settings
    enable_caching: bool = True
    batch_size: int = 1000
    
    def __post_init__(self):
        """Initialize default color palette if not provided."""
        if self.color_palette is None:
            self.color_palette = DEFAULT_COLOR_PALETTE.copy()


# Default color palette for consistent styling across visualizations
DEFAULT_COLOR_PALETTE = {
    # Core node types
    "StartFunction": "#9cdcfe",      # Light blue for entry point functions
    "StartMethod": "#9cdcfe",        # Light blue for entry point methods
    "StartClass": "#FFE082",         # Yellow for starting classes
    "PyFunction": "#a277ff",         # Purple for regular Python functions
    "PyClass": "#ffca85",            # Warm peach for class definitions
    "ExternalModule": "#f694ff",     # Pink for external module calls
    
    # Special patterns
    "HTTP_METHOD": "#ff6b6b",        # Red for HTTP methods
    "Database": "#4ecdc4",           # Teal for database operations
    "API_Endpoint": "#45b7d1",       # Blue for API endpoints
    "Test": "#96ceb4",               # Green for test functions
    "Utility": "#feca57",            # Orange for utility functions
    
    # Dependency types
    "Import": "#dda0dd",             # Plum for imports
    "Symbol": "#98d8c8",             # Mint for symbols
    "Usage": "#f7dc6f",              # Light yellow for usages
    
    # Relationship types
    "Calls": "#85c1e9",              # Light blue for function calls
    "Inherits": "#f8c471",           # Light orange for inheritance
    "Depends": "#bb8fce",            # Light purple for dependencies
    "Uses": "#82e0aa",               # Light green for usage relationships
}


@dataclass
class CallTraceConfig(VisualizationConfig):
    """Configuration specific to call trace visualizations."""
    
    # Call trace specific settings
    include_recursive_calls: bool = False
    highlight_entry_points: bool = True
    group_by_module: bool = False
    show_call_frequency: bool = False


@dataclass
class DependencyTraceConfig(VisualizationConfig):
    """Configuration specific to dependency trace visualizations."""
    
    # Dependency specific settings
    include_import_dependencies: bool = True
    include_symbol_dependencies: bool = True
    show_circular_dependencies: bool = True
    group_by_package: bool = True


@dataclass
class BlastRadiusConfig(VisualizationConfig):
    """Configuration specific to blast radius visualizations."""
    
    # Blast radius specific settings
    include_test_usages: bool = True
    highlight_critical_paths: bool = True
    show_impact_metrics: bool = True
    weight_by_usage_frequency: bool = False


@dataclass
class MethodRelationshipsConfig(VisualizationConfig):
    """Configuration specific to method relationships visualizations."""
    
    # Method relationships specific settings
    include_private_methods: bool = True
    show_inheritance_chain: bool = True
    highlight_overridden_methods: bool = True
    group_by_access_level: bool = False


# Configuration factory for creating specific configs
CONFIG_FACTORY = {
    VisualizationType.CALL_TRACE: CallTraceConfig,
    VisualizationType.DEPENDENCY_TRACE: DependencyTraceConfig,
    VisualizationType.BLAST_RADIUS: BlastRadiusConfig,
    VisualizationType.METHOD_RELATIONSHIPS: MethodRelationshipsConfig,
}


def create_config(visualization_type: VisualizationType, **kwargs) -> VisualizationConfig:
    """Create a configuration instance for the specified visualization type."""
    config_class = CONFIG_FACTORY.get(visualization_type, VisualizationConfig)
    return config_class(**kwargs)


def get_default_config(visualization_type: VisualizationType) -> VisualizationConfig:
    """Get the default configuration for a visualization type."""
    return create_config(visualization_type)

