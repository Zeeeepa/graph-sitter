#!/usr/bin/env python3
"""
🎛️ ADVANCED CODEBASE CONFIGURATION 🎛️

Advanced CodebaseConfig usage based on graph-sitter.com/introduction/advanced-settings
with comprehensive flag management and optimization strategies.

This module provides:
- Complete CodebaseConfig flag management
- Performance optimization configurations
- Debug and development configurations
- Production-ready configurations
- Language-specific optimizations
- Custom configuration builders
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import graph-sitter configuration
try:
    from graph_sitter.configs.models.codebase import CodebaseConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    logger.warning("Graph-sitter not available - using mock configuration")
    
    # Mock CodebaseConfig for development
    class CodebaseConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


@dataclass
class AdvancedCodebaseConfig:
    """
    Advanced wrapper for CodebaseConfig with additional features.
    
    Based on all available flags from graph-sitter.com/introduction/advanced-settings
    """
    
    # Core flags from graph-sitter.com
    debug: bool = False
    verify_graph: bool = False
    track_graph: bool = False
    method_usages: bool = True
    sync_enabled: bool = False
    full_range_index: bool = False
    ignore_process_errors: bool = True
    disable_graph: bool = False
    disable_file_parse: bool = False
    exp_lazy_graph: bool = False
    generics: bool = True
    
    # Import resolution flags
    import_resolution_paths: List[str] = field(default_factory=list)
    import_resolution_overrides: Dict[str, str] = field(default_factory=dict)
    py_resolve_syspath: bool = False
    allow_external: bool = False
    
    # TypeScript specific flags
    ts_dependency_manager: bool = False
    ts_language_engine: bool = False
    v8_ts_engine: bool = False
    
    # Advanced flags
    unpacking_assignment_partial_removal: bool = False
    
    # Custom extensions
    optimization_level: str = "balanced"  # minimal, balanced, aggressive
    language_specific_optimizations: bool = True
    custom_parsers: Dict[str, Any] = field(default_factory=dict)
    analysis_timeout: Optional[int] = None  # seconds
    memory_limit_mb: Optional[int] = None
    
    def to_codebase_config(self) -> CodebaseConfig:
        """Convert to standard CodebaseConfig object."""
        if not GRAPH_SITTER_AVAILABLE:
            return CodebaseConfig(**self.__dict__)
        
        # Map to actual CodebaseConfig parameters
        config_params = {
            "debug": self.debug,
            "verify_graph": self.verify_graph,
            "track_graph": self.track_graph,
            "method_usages": self.method_usages,
            "sync_enabled": self.sync_enabled,
            "full_range_index": self.full_range_index,
            "ignore_process_errors": self.ignore_process_errors,
            "disable_graph": self.disable_graph,
            "disable_file_parse": self.disable_file_parse,
            "exp_lazy_graph": self.exp_lazy_graph,
            "generics": self.generics,
            "import_resolution_paths": self.import_resolution_paths,
            "import_resolution_overrides": self.import_resolution_overrides,
            "py_resolve_syspath": self.py_resolve_syspath,
            "allow_external": self.allow_external,
            "ts_dependency_manager": self.ts_dependency_manager,
            "ts_language_engine": self.ts_language_engine,
            "v8_ts_engine": self.v8_ts_engine,
            "unpacking_assignment_partial_removal": self.unpacking_assignment_partial_removal
        }
        
        return CodebaseConfig(**config_params)
    
    def optimize_for_language(self, language: str):
        """Optimize configuration for specific language."""
        if not self.language_specific_optimizations:
            return
        
        if language.lower() == "python":
            self.py_resolve_syspath = True
            self.generics = True
            self.method_usages = True
            
        elif language.lower() in ["typescript", "javascript"]:
            self.ts_language_engine = True
            self.generics = True
            self.method_usages = True
            
        elif language.lower() in ["java", "kotlin"]:
            self.generics = True
            self.method_usages = True
            
        logger.info(f"Optimized configuration for {language}")
    
    def optimize_for_size(self, codebase_size: str):
        """Optimize configuration based on codebase size."""
        if codebase_size == "small":  # < 10k lines
            self.exp_lazy_graph = False
            self.full_range_index = True
            self.optimization_level = "aggressive"
            
        elif codebase_size == "medium":  # 10k - 100k lines
            self.exp_lazy_graph = True
            self.full_range_index = False
            self.optimization_level = "balanced"
            
        elif codebase_size == "large":  # > 100k lines
            self.exp_lazy_graph = True
            self.full_range_index = False
            self.disable_graph = False  # Keep graph for large codebases
            self.optimization_level = "minimal"
            self.memory_limit_mb = 2048  # 2GB limit
            
        logger.info(f"Optimized configuration for {codebase_size} codebase")
    
    def enable_debug_mode(self):
        """Enable comprehensive debugging."""
        self.debug = True
        self.verify_graph = True
        self.track_graph = True
        self.ignore_process_errors = False
        logger.info("Debug mode enabled")
    
    def enable_production_mode(self):
        """Enable production optimizations."""
        self.debug = False
        self.verify_graph = False
        self.track_graph = False
        self.ignore_process_errors = True
        self.exp_lazy_graph = True
        logger.info("Production mode enabled")
    
    def validate(self) -> List[str]:
        """Validate configuration and return warnings."""
        warnings = []
        
        # Check for conflicting flags
        if self.disable_graph and self.method_usages:
            warnings.append("method_usages requires graph - will be disabled")
        
        if self.disable_file_parse and not self.disable_graph:
            warnings.append("disable_file_parse implies disable_graph")
        
        if self.track_graph and not self.verify_graph:
            warnings.append("track_graph is only useful with verify_graph")
        
        # Check for performance implications
        if self.debug and self.optimization_level == "aggressive":
            warnings.append("Debug mode may conflict with aggressive optimization")
        
        if self.full_range_index and self.optimization_level == "minimal":
            warnings.append("full_range_index increases memory usage")
        
        # Check TypeScript flags
        if self.ts_dependency_manager and not self.ts_language_engine:
            warnings.append("ts_dependency_manager works best with ts_language_engine")
        
        if self.v8_ts_engine and self.ts_language_engine:
            warnings.append("v8_ts_engine and ts_language_engine are mutually exclusive")
        
        return warnings


def create_optimized_config(
    language: Optional[str] = None,
    codebase_size: str = "medium",
    optimization_level: str = "balanced"
) -> AdvancedCodebaseConfig:
    """
    Create an optimized configuration for analysis.
    
    Args:
        language: Primary language of the codebase
        codebase_size: Size category (small, medium, large)
        optimization_level: Optimization level (minimal, balanced, aggressive)
    
    Returns:
        Optimized AdvancedCodebaseConfig
    """
    config = AdvancedCodebaseConfig(optimization_level=optimization_level)
    
    # Apply size-based optimizations
    config.optimize_for_size(codebase_size)
    
    # Apply language-specific optimizations
    if language:
        config.optimize_for_language(language)
    
    # Apply optimization level
    if optimization_level == "aggressive":
        config.method_usages = True
        config.generics = True
        config.full_range_index = True
        config.exp_lazy_graph = False
        
    elif optimization_level == "minimal":
        config.method_usages = False
        config.generics = False
        config.full_range_index = False
        config.exp_lazy_graph = True
        
    # Validate and log warnings
    warnings = config.validate()
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    logger.info(f"Created optimized config: {language or 'multi-language'}, {codebase_size}, {optimization_level}")
    return config


def create_debug_config() -> AdvancedCodebaseConfig:
    """
    Create a configuration optimized for debugging and development.
    
    Returns:
        Debug-optimized AdvancedCodebaseConfig
    """
    config = AdvancedCodebaseConfig()
    config.enable_debug_mode()
    
    # Enable comprehensive tracking
    config.method_usages = True
    config.generics = True
    config.full_range_index = True
    config.sync_enabled = True
    
    # Disable optimizations that might hide issues
    config.exp_lazy_graph = False
    config.ignore_process_errors = False
    
    logger.info("Created debug configuration")
    return config


def create_production_config(
    language: Optional[str] = None,
    enable_caching: bool = True
) -> AdvancedCodebaseConfig:
    """
    Create a configuration optimized for production use.
    
    Args:
        language: Primary language of the codebase
        enable_caching: Whether to enable aggressive caching
    
    Returns:
        Production-optimized AdvancedCodebaseConfig
    """
    config = AdvancedCodebaseConfig()
    config.enable_production_mode()
    
    # Enable performance optimizations
    config.exp_lazy_graph = True
    config.method_usages = True  # Keep for analysis quality
    config.generics = True
    
    # Disable expensive features
    config.full_range_index = False
    config.sync_enabled = False
    
    # Language-specific optimizations
    if language:
        config.optimize_for_language(language)
    
    # Memory management
    config.memory_limit_mb = 4096  # 4GB limit for production
    config.analysis_timeout = 3600  # 1 hour timeout
    
    logger.info(f"Created production configuration for {language or 'multi-language'}")
    return config


def create_minimal_config() -> AdvancedCodebaseConfig:
    """
    Create a minimal configuration for basic analysis.
    
    Returns:
        Minimal AdvancedCodebaseConfig
    """
    config = AdvancedCodebaseConfig()
    
    # Disable expensive features
    config.method_usages = False
    config.generics = False
    config.full_range_index = False
    config.exp_lazy_graph = True
    config.sync_enabled = False
    
    # Keep essential features
    config.ignore_process_errors = True
    
    logger.info("Created minimal configuration")
    return config


def create_security_focused_config() -> AdvancedCodebaseConfig:
    """
    Create a configuration focused on security analysis.
    
    Returns:
        Security-focused AdvancedCodebaseConfig
    """
    config = AdvancedCodebaseConfig()
    
    # Enable comprehensive analysis
    config.method_usages = True
    config.generics = True
    config.full_range_index = True
    config.allow_external = True  # Analyze external dependencies
    
    # Enable detailed tracking
    config.sync_enabled = True
    config.py_resolve_syspath = True
    
    # Language engines for better analysis
    config.ts_language_engine = True
    
    logger.info("Created security-focused configuration")
    return config


def create_performance_config() -> AdvancedCodebaseConfig:
    """
    Create a configuration optimized for performance analysis.
    
    Returns:
        Performance-optimized AdvancedCodebaseConfig
    """
    config = AdvancedCodebaseConfig()
    
    # Enable features needed for performance analysis
    config.method_usages = True
    config.generics = True
    config.exp_lazy_graph = True
    
    # Enable language engines for better analysis
    config.ts_language_engine = True
    config.py_resolve_syspath = True
    
    # Optimize for speed
    config.full_range_index = False
    config.sync_enabled = False
    
    logger.info("Created performance analysis configuration")
    return config


def create_config_from_template(template_name: str, **overrides) -> AdvancedCodebaseConfig:
    """
    Create configuration from a named template.
    
    Args:
        template_name: Name of the template (optimized, debug, production, etc.)
        **overrides: Override specific configuration values
    
    Returns:
        AdvancedCodebaseConfig based on template
    """
    templates = {
        "optimized": create_optimized_config,
        "debug": create_debug_config,
        "production": create_production_config,
        "minimal": create_minimal_config,
        "security": create_security_focused_config,
        "performance": create_performance_config
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")
    
    config = templates[template_name]()
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            logger.warning(f"Unknown configuration option: {key}")
    
    logger.info(f"Created configuration from template: {template_name}")
    return config


if __name__ == "__main__":
    # Example usage and testing
    print("🎛️ Advanced Codebase Configuration")
    print("=" * 50)
    
    # Test different configurations
    configs = {
        "Optimized (Python, Large)": create_optimized_config("python", "large", "balanced"),
        "Debug": create_debug_config(),
        "Production": create_production_config("typescript"),
        "Minimal": create_minimal_config(),
        "Security": create_security_focused_config(),
        "Performance": create_performance_config()
    }
    
    for name, config in configs.items():
        print(f"\n{name}:")
        print(f"  Debug: {config.debug}")
        print(f"  Lazy Graph: {config.exp_lazy_graph}")
        print(f"  Method Usages: {config.method_usages}")
        print(f"  Generics: {config.generics}")
        print(f"  Optimization: {config.optimization_level}")
        
        warnings = config.validate()
        if warnings:
            print(f"  Warnings: {len(warnings)}")
    
    if GRAPH_SITTER_AVAILABLE:
        print("\n✅ Graph-sitter available - Full configuration support")
    else:
        print("\n⚠️ Graph-sitter not available - Using mock configuration")

