"""
Graph-sitter Configuration

Advanced configuration options for graph-sitter based on:
https://graph-sitter.com/introduction/advanced-settings

This module provides backward compatibility while integrating with
the new comprehensive advanced settings system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

# Import the new advanced settings system
from .advanced_settings import (
    AdvancedGraphSitterSettings, 
    get_preset_config,
    create_codebase_config
)

logger = logging.getLogger(__name__)


@dataclass
class GraphSitterConfig:
    """
    Configuration for graph-sitter advanced settings.
    
    This class provides backward compatibility while leveraging
    the new comprehensive AdvancedGraphSitterSettings system.
    
    Based on CodebaseConfig from graph-sitter documentation.
    """
    
    # Core settings - delegated to AdvancedGraphSitterSettings
    _advanced_settings: AdvancedGraphSitterSettings = field(default_factory=AdvancedGraphSitterSettings)
    
    # Legacy properties for backward compatibility
    @property
    def debug(self) -> bool:
        return self._advanced_settings.debug.debug
    
    @debug.setter
    def debug(self, value: bool):
        self._advanced_settings.debug.debug = value
    
    @property
    def verify_graph(self) -> bool:
        return self._advanced_settings.debug.verify_graph
    
    @verify_graph.setter
    def verify_graph(self, value: bool):
        self._advanced_settings.debug.verify_graph = value
    
    @property
    def track_graph(self) -> bool:
        return self._advanced_settings.debug.track_graph
    
    @track_graph.setter
    def track_graph(self, value: bool):
        self._advanced_settings.debug.track_graph = value
    
    @property
    def sync_enabled(self) -> bool:
        return self._advanced_settings.performance.sync_enabled
    
    @sync_enabled.setter
    def sync_enabled(self, value: bool):
        self._advanced_settings.performance.sync_enabled = value
    
    @property
    def full_range_index(self) -> bool:
        return self._advanced_settings.performance.full_range_index
    
    @full_range_index.setter
    def full_range_index(self, value: bool):
        self._advanced_settings.performance.full_range_index = value
    
    @property
    def method_usages(self) -> bool:
        return self._advanced_settings.language.method_usages
    
    @method_usages.setter
    def method_usages(self, value: bool):
        self._advanced_settings.language.method_usages = value
    
    @property
    def generics(self) -> bool:
        return self._advanced_settings.language.generics
    
    @generics.setter
    def generics(self, value: bool):
        self._advanced_settings.language.generics = value
    
    @property
    def import_resolution_paths(self) -> List[str]:
        return self._advanced_settings.import_resolution.import_resolution_paths
    
    @import_resolution_paths.setter
    def import_resolution_paths(self, value: List[str]):
        self._advanced_settings.import_resolution.import_resolution_paths = value
    
    # Additional convenience properties
    @property
    def advanced_settings(self) -> AdvancedGraphSitterSettings:
        """Access to the full advanced settings system."""
        return self._advanced_settings
    
    @advanced_settings.setter
    def advanced_settings(self, value: AdvancedGraphSitterSettings):
        self._advanced_settings = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return self._advanced_settings.to_codebase_config_dict()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GraphSitterConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        # Update advanced settings from dictionary
        for key, value in config_dict.items():
            if hasattr(config._advanced_settings.debug, key):
                setattr(config._advanced_settings.debug, key, value)
            elif hasattr(config._advanced_settings.performance, key):
                setattr(config._advanced_settings.performance, key, value)
            elif hasattr(config._advanced_settings.language, key):
                setattr(config._advanced_settings.language, key, value)
            elif hasattr(config._advanced_settings.import_resolution, key):
                setattr(config._advanced_settings.import_resolution, key, value)
            elif hasattr(config._advanced_settings.experimental, key):
                setattr(config._advanced_settings.experimental, key, value)
        
        return config
    
    @classmethod
    def from_preset(cls, preset_name: str) -> 'GraphSitterConfig':
        """Create configuration from a preset."""
        config = cls()
        config._advanced_settings = get_preset_config(preset_name)
        return config
    
    def get_performance_config(self) -> 'GraphSitterConfig':
        """Get a performance-optimized configuration."""
        config = GraphSitterConfig()
        config._advanced_settings = AdvancedGraphSitterSettings.get_performance_config()
        return config
    
    def get_debug_config(self) -> 'GraphSitterConfig':
        """Get a debug-enabled configuration."""
        config = GraphSitterConfig()
        config._advanced_settings = AdvancedGraphSitterSettings.get_debug_config()
        return config
    
    def get_comprehensive_config(self) -> 'GraphSitterConfig':
        """Get a comprehensive configuration with most features enabled."""
        config = GraphSitterConfig()
        config._advanced_settings = AdvancedGraphSitterSettings.get_comprehensive_config()
        return config
    
    def get_typescript_config(self) -> 'GraphSitterConfig':
        """Get a TypeScript-optimized configuration."""
        config = GraphSitterConfig()
        config._advanced_settings = AdvancedGraphSitterSettings.get_typescript_config()
        return config
    
    def get_python_config(self) -> 'GraphSitterConfig':
        """Get a Python-optimized configuration."""
        config = GraphSitterConfig()
        config._advanced_settings = AdvancedGraphSitterSettings.get_python_config()
        return config
    
    def get_minimal_config(self) -> 'GraphSitterConfig':
        """Get a minimal configuration for basic analysis."""
        config = GraphSitterConfig()
        config._advanced_settings.language.method_usages = False
        config._advanced_settings.language.generics = False
        config._advanced_settings.performance.sync_enabled = False
        return config
    
    def create_codebase_config(self) -> Optional[Any]:
        """Create a CodebaseConfig object from current settings."""
        return create_codebase_config(self._advanced_settings)
    
    def validate(self) -> List[str]:
        """Validate configuration and return warnings."""
        return self._advanced_settings.validate()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return self._advanced_settings.get_summary()


# Legacy compatibility functions
def get_default_config() -> GraphSitterConfig:
    """Get default graph-sitter configuration."""
    return GraphSitterConfig()


def get_optimized_config() -> GraphSitterConfig:
    """Get performance-optimized configuration."""
    return GraphSitterConfig().get_performance_config()


def get_debug_config() -> GraphSitterConfig:
    """Get debug-enabled configuration."""
    return GraphSitterConfig().get_debug_config()

