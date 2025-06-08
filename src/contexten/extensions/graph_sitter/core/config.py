"""
Core Configuration Module

Provides CodebaseConfig class based on the official graph-sitter.com advanced settings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class CodebaseConfig:
    """
    Configuration for codebase analysis based on graph-sitter.com advanced settings.
    
    These flags are helpful for debugging problematic repos, optimizing performance,
    or testing unreleased or experimental features.
    """
    
    # Performance optimizations
    method_usages: bool = True
    """Enable method usage resolution for comprehensive static analysis."""
    
    generics: bool = True
    """Enable generic type resolution for better type analysis."""
    
    sync_enabled: bool = False
    """Enable graph sync during codebase.commit() operations."""
    
    # Advanced analysis
    full_range_index: bool = False
    """Create full range-to-node mapping for all tree-sitter ranges."""
    
    py_resolve_syspath: bool = False
    """Resolve imports from sys.path for Python codebases."""
    
    # Experimental features
    exp_lazy_graph: bool = False
    """Push graph creation back until the graph is needed (experimental)."""
    
    # Debug and verification
    debug: bool = False
    """Enable verbose logging for debugging purposes."""
    
    verify_graph: bool = False
    """Add assertions for graph state during reset resync."""
    
    track_graph: bool = False
    """Keep a copy of the original graph before a resync."""
    
    # Graph control
    disable_graph: bool = False
    """Disable the graph construction process entirely."""
    
    disable_file_parse: bool = False
    """Disable ALL parsing, including file and graph parsing."""
    
    # Error handling
    ignore_process_errors: bool = True
    """Ignore errors that occur during external process execution."""
    
    # Import resolution
    import_resolution_paths: List[str] = None
    """Alternative paths to resolve imports from."""
    
    import_resolution_overrides: Dict[str, str] = None
    """Import path overrides during import resolution."""
    
    allow_external: bool = False
    """Enable resolving imports, files, modules from outside repo path."""
    
    # TypeScript specific
    ts_dependency_manager: bool = False
    """Enable internal dependency installer for TypeScript."""
    
    ts_language_engine: bool = False
    """Enable TypeScript compiler for type information extraction."""
    
    v8_ts_engine: bool = False
    """Enable V8-based TypeScript compiler (less stable, more features)."""
    
    # Advanced features
    unpacking_assignment_partial_removal: bool = False
    """Enable smarter removal of unpacking assignments."""
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.import_resolution_paths is None:
            self.import_resolution_paths = []
        if self.import_resolution_overrides is None:
            self.import_resolution_overrides = {}
    
    @classmethod
    def performance_optimized(cls) -> 'CodebaseConfig':
        """
        Create a configuration optimized for performance.
        
        Returns:
            CodebaseConfig with performance-focused settings
        """
        return cls(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
            exp_lazy_graph=False,
            debug=False,
            ignore_process_errors=True,
        )
    
    @classmethod
    def comprehensive_analysis(cls) -> 'CodebaseConfig':
        """
        Create a configuration for comprehensive analysis.
        
        Returns:
            CodebaseConfig with all analysis features enabled
        """
        return cls(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
            exp_lazy_graph=False,
            debug=False,
            verify_graph=False,
            track_graph=False,
            allow_external=True,
            unpacking_assignment_partial_removal=True,
        )
    
    @classmethod
    def debug_mode(cls) -> 'CodebaseConfig':
        """
        Create a configuration for debugging.
        
        Returns:
            CodebaseConfig with debug features enabled
        """
        return cls(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
            debug=True,
            verify_graph=True,
            track_graph=True,
            ignore_process_errors=False,
        )
    
    @classmethod
    def typescript_optimized(cls) -> 'CodebaseConfig':
        """
        Create a configuration optimized for TypeScript analysis.
        
        Returns:
            CodebaseConfig with TypeScript-specific settings
        """
        return cls(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            ts_dependency_manager=True,
            ts_language_engine=True,
            allow_external=True,
        )
    
    @classmethod
    def minimal(cls) -> 'CodebaseConfig':
        """
        Create a minimal configuration for basic analysis.
        
        Returns:
            CodebaseConfig with minimal features enabled
        """
        return cls(
            method_usages=False,
            generics=False,
            sync_enabled=False,
            full_range_index=False,
            py_resolve_syspath=False,
            exp_lazy_graph=True,
            debug=False,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'method_usages': self.method_usages,
            'generics': self.generics,
            'sync_enabled': self.sync_enabled,
            'full_range_index': self.full_range_index,
            'py_resolve_syspath': self.py_resolve_syspath,
            'exp_lazy_graph': self.exp_lazy_graph,
            'debug': self.debug,
            'verify_graph': self.verify_graph,
            'track_graph': self.track_graph,
            'disable_graph': self.disable_graph,
            'disable_file_parse': self.disable_file_parse,
            'ignore_process_errors': self.ignore_process_errors,
            'import_resolution_paths': self.import_resolution_paths,
            'import_resolution_overrides': self.import_resolution_overrides,
            'allow_external': self.allow_external,
            'ts_dependency_manager': self.ts_dependency_manager,
            'ts_language_engine': self.ts_language_engine,
            'v8_ts_engine': self.v8_ts_engine,
            'unpacking_assignment_partial_removal': self.unpacking_assignment_partial_removal,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'CodebaseConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)


# Preset configurations for common use cases
class PresetConfigs:
    """Preset configurations for common analysis scenarios."""
    
    @staticmethod
    def default() -> CodebaseConfig:
        """Default configuration with balanced settings."""
        return CodebaseConfig()
    
    @staticmethod
    def performance() -> CodebaseConfig:
        """Performance-optimized configuration."""
        return CodebaseConfig.performance_optimized()
    
    @staticmethod
    def comprehensive() -> CodebaseConfig:
        """Comprehensive analysis configuration."""
        return CodebaseConfig.comprehensive_analysis()
    
    @staticmethod
    def debug() -> CodebaseConfig:
        """Debug-enabled configuration."""
        return CodebaseConfig.debug_mode()
    
    @staticmethod
    def typescript() -> CodebaseConfig:
        """TypeScript-optimized configuration."""
        return CodebaseConfig.typescript_optimized()
    
    @staticmethod
    def minimal() -> CodebaseConfig:
        """Minimal configuration for basic analysis."""
        return CodebaseConfig.minimal()


__all__ = ['CodebaseConfig', 'PresetConfigs']

