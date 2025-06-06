"""
Graph-sitter Configuration

Advanced configuration options for graph-sitter based on:
https://graph-sitter.com/introduction/advanced-settings
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class GraphSitterConfig:
    """
    Configuration for graph-sitter advanced settings.
    
    Based on CodebaseConfig from graph-sitter documentation.
    """
    
    # Debug and Development
    debug: bool = False
    """Enables verbose logging for debugging purposes"""
    
    verify_graph: bool = False
    """Adds assertions for graph state during reset resync"""
    
    track_graph: bool = False
    """Keeps a copy of the original graph before a resync"""
    
    # Performance and Optimization
    sync_enabled: bool = False
    """Enables or disables graph sync during codebase.commit"""
    
    full_range_index: bool = False
    """Creates additional index that maps all tree-sitter ranges to nodes"""
    
    ignore_process_errors: bool = True
    """Controls whether to ignore errors during external process execution"""
    
    exp_lazy_graph: bool = False
    """Experimental flag that pushes graph creation back until needed"""
    
    # Graph Construction Control
    disable_graph: bool = False
    """Disables the graph construction process entirely"""
    
    disable_file_parse: bool = False
    """Disables ALL parsing, including file and graph parsing"""
    
    # Feature Flags
    method_usages: bool = True
    """Enables and disables resolving method usages"""
    
    generics: bool = True
    """Enables and disables generic type resolution"""
    
    allow_external: bool = False
    """Enables resolving imports, files, modules from outside repo path"""
    
    # Import Resolution
    import_resolution_paths: List[str] = field(default_factory=list)
    """Alternative paths to resolve imports from"""
    
    import_resolution_overrides: Dict[str, str] = field(default_factory=dict)
    """Import path overrides during import resolution"""
    
    py_resolve_syspath: bool = False
    """Enables resolution of imports from sys.path"""
    
    # TypeScript Specific
    ts_dependency_manager: bool = False
    """Enables internal dependency installer for TypeScript"""
    
    ts_language_engine: bool = False
    """Enables using TypeScript compiler to extract information"""
    
    v8_ts_engine: bool = False
    """Enables V8-based TypeScript compiler"""
    
    # Advanced Features
    unpacking_assignment_partial_removal: bool = False
    """Enables smarter removal of unpacking assignments"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GraphSitterConfig':
        """Create configuration from dictionary."""
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in cls.__dataclass_fields__
        })
    
    def get_performance_config(self) -> 'GraphSitterConfig':
        """Get a performance-optimized configuration."""
        config = GraphSitterConfig()
        config.sync_enabled = True
        config.method_usages = True
        config.generics = True
        config.ignore_process_errors = True
        config.exp_lazy_graph = True
        return config
    
    def get_debug_config(self) -> 'GraphSitterConfig':
        """Get a debug-enabled configuration."""
        config = GraphSitterConfig()
        config.debug = True
        config.verify_graph = True
        config.track_graph = True
        config.full_range_index = True
        return config
    
    def get_minimal_config(self) -> 'GraphSitterConfig':
        """Get a minimal configuration for basic analysis."""
        config = GraphSitterConfig()
        config.method_usages = False
        config.generics = False
        config.sync_enabled = False
        return config

