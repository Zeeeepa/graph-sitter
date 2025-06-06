#!/usr/bin/env python3
"""
Advanced Graph-sitter Configuration Settings

This module implements comprehensive configuration support for all advanced
graph-sitter settings as documented at:
https://graph-sitter.com/introduction/advanced-settings

Features:
- Complete coverage of all advanced configuration flags
- Hierarchical configuration with validation
- Performance optimization settings
- Debug and development options
- Language-specific configurations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class DebugSettings:
    """Debug and development configuration settings."""
    
    # Core debug flags
    debug: bool = False
    """Enables verbose logging for debugging purposes"""
    
    verify_graph: bool = False
    """Adds assertions for graph state during reset resync"""
    
    track_graph: bool = False
    """Keeps a copy of the original graph before a resync"""
    
    ignore_process_errors: bool = True
    """Controls whether to ignore errors during external process execution"""


@dataclass
class PerformanceSettings:
    """Performance optimization configuration settings."""
    
    # Core performance flags
    sync_enabled: bool = False
    """Enables or disables graph sync during codebase.commit"""
    
    full_range_index: bool = False
    """Creates additional index that maps all tree-sitter ranges to nodes"""
    
    exp_lazy_graph: bool = False
    """Experimental flag that pushes graph creation back until needed"""
    
    # Processing control
    disable_graph: bool = False
    """Disables the graph construction process entirely"""
    
    disable_file_parse: bool = False
    """Disables ALL parsing, including file and graph parsing"""


@dataclass
class LanguageSettings:
    """Language-specific configuration settings."""
    
    # Generic language features
    generics: bool = True
    """Enables and disables generic type resolution"""
    
    method_usages: bool = True
    """Enables and disables resolving method usages"""
    
    # Python-specific settings
    py_resolve_syspath: bool = False
    """Enables resolution of imports from sys.path"""
    
    # TypeScript-specific settings
    ts_dependency_manager: bool = False
    """Enables Codegen's internal dependency installer for TypeScript"""
    
    ts_language_engine: bool = False
    """Enables using the TypeScript compiler to extract information"""
    
    v8_ts_engine: bool = False
    """Enables using the V8-based TypeScript compiler"""


@dataclass
class ImportResolutionSettings:
    """Import resolution configuration settings."""
    
    import_resolution_paths: List[str] = field(default_factory=list)
    """Controls alternative paths to resolve imports from"""
    
    import_resolution_overrides: Dict[str, str] = field(default_factory=dict)
    """Controls import path overrides during import resolution"""
    
    allow_external: bool = False
    """Enables resolving imports from outside of the repo path"""


@dataclass
class ExperimentalSettings:
    """Experimental and advanced feature settings."""
    
    unpacking_assignment_partial_removal: bool = False
    """Enables smarter removal of unpacking assignments"""
    
    # Additional experimental flags can be added here
    experimental_features: Dict[str, Any] = field(default_factory=dict)
    """Dictionary for additional experimental features"""


@dataclass
class AdvancedGraphSitterSettings:
    """
    Comprehensive advanced graph-sitter configuration settings.
    
    This class consolidates all advanced configuration options available
    in graph-sitter, organized into logical groups for better management.
    """
    
    # Configuration groups
    debug: DebugSettings = field(default_factory=DebugSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    language: LanguageSettings = field(default_factory=LanguageSettings)
    import_resolution: ImportResolutionSettings = field(default_factory=ImportResolutionSettings)
    experimental: ExperimentalSettings = field(default_factory=ExperimentalSettings)
    
    def to_codebase_config_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format suitable for CodebaseConfig.
        
        Returns:
            Dictionary with all settings flattened for CodebaseConfig
        """
        config_dict = {}
        
        # Debug settings
        config_dict.update({
            'debug': self.debug.debug,
            'verify_graph': self.debug.verify_graph,
            'track_graph': self.debug.track_graph,
            'ignore_process_errors': self.debug.ignore_process_errors,
        })
        
        # Performance settings
        config_dict.update({
            'sync_enabled': self.performance.sync_enabled,
            'full_range_index': self.performance.full_range_index,
            'exp_lazy_graph': self.performance.exp_lazy_graph,
            'disable_graph': self.performance.disable_graph,
            'disable_file_parse': self.performance.disable_file_parse,
        })
        
        # Language settings
        config_dict.update({
            'generics': self.language.generics,
            'method_usages': self.language.method_usages,
            'py_resolve_syspath': self.language.py_resolve_syspath,
            'ts_dependency_manager': self.language.ts_dependency_manager,
            'ts_language_engine': self.language.ts_language_engine,
            'v8_ts_engine': self.language.v8_ts_engine,
        })
        
        # Import resolution settings
        config_dict.update({
            'import_resolution_paths': self.import_resolution.import_resolution_paths,
            'import_resolution_overrides': self.import_resolution.import_resolution_overrides,
            'allow_external': self.import_resolution.allow_external,
        })
        
        # Experimental settings
        config_dict.update({
            'unpacking_assignment_partial_removal': self.experimental.unpacking_assignment_partial_removal,
        })
        config_dict.update(self.experimental.experimental_features)
        
        return config_dict
    
    @classmethod
    def get_debug_config(cls) -> 'AdvancedGraphSitterSettings':
        """Get configuration optimized for debugging."""
        config = cls()
        config.debug.debug = True
        config.debug.verify_graph = True
        config.debug.track_graph = True
        config.performance.sync_enabled = True
        return config
    
    @classmethod
    def get_performance_config(cls) -> 'AdvancedGraphSitterSettings':
        """Get configuration optimized for performance."""
        config = cls()
        config.performance.exp_lazy_graph = True
        config.performance.sync_enabled = False
        config.debug.ignore_process_errors = True
        return config
    
    @classmethod
    def get_comprehensive_config(cls) -> 'AdvancedGraphSitterSettings':
        """Get configuration with most features enabled."""
        config = cls()
        config.language.method_usages = True
        config.language.generics = True
        config.performance.sync_enabled = True
        config.performance.full_range_index = True
        config.import_resolution.allow_external = True
        return config
    
    @classmethod
    def get_typescript_config(cls) -> 'AdvancedGraphSitterSettings':
        """Get configuration optimized for TypeScript projects."""
        config = cls()
        config.language.ts_dependency_manager = True
        config.language.ts_language_engine = True
        config.language.generics = True
        config.language.method_usages = True
        return config
    
    @classmethod
    def get_python_config(cls) -> 'AdvancedGraphSitterSettings':
        """Get configuration optimized for Python projects."""
        config = cls()
        config.language.py_resolve_syspath = True
        config.language.method_usages = True
        config.language.generics = True
        config.import_resolution.import_resolution_paths = ["src", "lib", "app"]
        return config
    
    def validate(self) -> List[str]:
        """
        Validate configuration settings and return any warnings.
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check for conflicting settings
        if self.performance.disable_graph and self.language.method_usages:
            warnings.append("method_usages requires graph construction but disable_graph is True")
        
        if self.performance.disable_file_parse and not self.performance.disable_graph:
            warnings.append("disable_file_parse implies disable_graph should also be True")
        
        if self.debug.track_graph and not self.debug.verify_graph:
            warnings.append("track_graph is most useful when verify_graph is also enabled")
        
        # Check for performance implications
        if self.debug.debug and self.performance.exp_lazy_graph:
            warnings.append("debug mode may interfere with lazy graph creation")
        
        if self.performance.full_range_index and self.performance.exp_lazy_graph:
            warnings.append("full_range_index may reduce benefits of lazy graph creation")
        
        # Check TypeScript settings
        if self.language.ts_language_engine and self.language.v8_ts_engine:
            warnings.append("Both ts_language_engine and v8_ts_engine are enabled - v8 will take precedence")
        
        return warnings
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration settings."""
        return {
            "debug_enabled": self.debug.debug,
            "performance_optimized": self.performance.exp_lazy_graph,
            "typescript_support": self.language.ts_language_engine or self.language.v8_ts_engine,
            "python_support": self.language.py_resolve_syspath,
            "method_tracking": self.language.method_usages,
            "generic_support": self.language.generics,
            "sync_enabled": self.performance.sync_enabled,
            "external_imports": self.import_resolution.allow_external,
            "validation_warnings": len(self.validate()),
        }


def create_codebase_config(settings: AdvancedGraphSitterSettings) -> Optional[Any]:
    """
    Create a CodebaseConfig object from advanced settings.
    
    Args:
        settings: Advanced graph-sitter settings
        
    Returns:
        CodebaseConfig object or None if graph-sitter not available
    """
    try:
        from graph_sitter.configs.models.codebase import CodebaseConfig
        
        config_dict = settings.to_codebase_config_dict()
        return CodebaseConfig(**config_dict)
    except ImportError:
        logger.warning("graph_sitter.configs.models.codebase not available")
        return None
    except Exception as e:
        logger.error(f"Failed to create CodebaseConfig: {e}")
        return None


# Predefined configurations for common use cases
PRESET_CONFIGS = {
    "default": AdvancedGraphSitterSettings(),
    "debug": AdvancedGraphSitterSettings.get_debug_config(),
    "performance": AdvancedGraphSitterSettings.get_performance_config(),
    "comprehensive": AdvancedGraphSitterSettings.get_comprehensive_config(),
    "typescript": AdvancedGraphSitterSettings.get_typescript_config(),
    "python": AdvancedGraphSitterSettings.get_python_config(),
}


def get_preset_config(preset_name: str) -> AdvancedGraphSitterSettings:
    """
    Get a predefined configuration by name.
    
    Args:
        preset_name: Name of the preset configuration
        
    Returns:
        Advanced graph-sitter settings
        
    Raises:
        ValueError: If preset name is not found
    """
    if preset_name not in PRESET_CONFIGS:
        available = ", ".join(PRESET_CONFIGS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
    
    return PRESET_CONFIGS[preset_name]

