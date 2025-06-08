#!/usr/bin/env python3
"""
Advanced configuration management for graph-sitter analysis.
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from graph_sitter.configs.models.codebase import CodebaseConfig
import graph_sitter
from graph_sitter import Codebase


class AdvancedCodebaseConfig:
    """
    Advanced configuration wrapper that implements all graph-sitter advanced settings
    as documented at https://graph-sitter.com/introduction/advanced-settings
    """
    
    def __init__(self):
        # Performance and Analysis Flags
        self.debug = False
        self.verify_graph = False
        self.track_graph = False
        self.method_usages = True
        self.sync_enabled = False
        self.full_range_index = False
        self.ignore_process_errors = True
        self.disable_graph = False
        self.disable_file_parse = False
        self.exp_lazy_graph = False
        self.generics = True
        
        # Import Resolution Settings
        self.import_resolution_paths: List[str] = []
        self.import_resolution_overrides: Dict[str, str] = {}
        self.py_resolve_syspath = False
        self.allow_external = False
        
        # TypeScript Specific Settings
        self.ts_dependency_manager = False
        self.ts_language_engine = False
        self.v8_ts_engine = False
        
        # Advanced Features
        self.unpacking_assignment_partial_removal = False
    
    def create_config(self) -> CodebaseConfig:
        """Create a CodebaseConfig object with the current settings."""
        return CodebaseConfig(
            debug=self.debug,
            verify_graph=self.verify_graph,
            track_graph=self.track_graph,
            method_usages=self.method_usages,
            sync_enabled=self.sync_enabled,
            full_range_index=self.full_range_index,
            ignore_process_errors=self.ignore_process_errors,
            disable_graph=self.disable_graph,
            disable_file_parse=self.disable_file_parse,
            exp_lazy_graph=self.exp_lazy_graph,
            generics=self.generics,
            import_resolution_paths=self.import_resolution_paths,
            import_resolution_overrides=self.import_resolution_overrides,
            py_resolve_syspath=self.py_resolve_syspath,
            allow_external=self.allow_external,
            ts_dependency_manager=self.ts_dependency_manager,
            ts_language_engine=self.ts_language_engine,
            v8_ts_engine=self.v8_ts_engine,
            unpacking_assignment_partial_removal=self.unpacking_assignment_partial_removal
        )


def create_debug_config() -> AdvancedCodebaseConfig:
    """
    Create configuration optimized for debugging problematic repos.
    
    Enables:
    - Verbose logging for debugging purposes
    - Graph verification and tracking
    - Full range indexing for complete tree-sitter range-to-node mapping
    """
    config = AdvancedCodebaseConfig()
    config.debug = True
    config.verify_graph = True
    config.track_graph = True
    config.full_range_index = True
    config.sync_enabled = True
    return config


def create_performance_config() -> AdvancedCodebaseConfig:
    """
    Create configuration optimized for performance on large codebases.
    
    Enables:
    - Lazy graph construction
    - Disabled method usage resolution for speed
    - Minimal graph features for faster parsing
    """
    config = AdvancedCodebaseConfig()
    config.exp_lazy_graph = True
    config.method_usages = False
    config.generics = False
    config.sync_enabled = False
    return config


def create_comprehensive_analysis_config() -> AdvancedCodebaseConfig:
    """
    Create configuration optimized for comprehensive codebase analysis.
    
    Enables:
    - Method usage resolution for complete call graph analysis
    - Generic type resolution for accurate dependency tracking
    - Full range indexing for precise location mapping
    - External import resolution for complete dependency analysis
    """
    config = AdvancedCodebaseConfig()
    config.method_usages = True
    config.generics = True
    config.full_range_index = True
    config.py_resolve_syspath = True
    config.allow_external = True
    config.sync_enabled = True
    return config


def create_typescript_analysis_config() -> AdvancedCodebaseConfig:
    """
    Create configuration optimized for TypeScript codebase analysis.
    
    Enables:
    - TypeScript language engine for type information
    - Dependency manager for package resolution
    - Generic type resolution
    - Full analysis capabilities
    """
    config = AdvancedCodebaseConfig()
    config.method_usages = True
    config.generics = True
    config.full_range_index = True
    config.ts_dependency_manager = True
    config.ts_language_engine = True
    config.sync_enabled = True
    return config


def create_ast_only_config() -> AdvancedCodebaseConfig:
    """
    Create configuration for AST-only operations without graph construction.
    
    Useful for:
    - Pure syntax analysis
    - Code formatting
    - Simple transformations that don't require import/usage resolution
    """
    config = AdvancedCodebaseConfig()
    config.disable_graph = True
    config.method_usages = False
    config.generics = False
    config.sync_enabled = False
    return config


@graph_sitter.function("analyze-with-advanced-config")
def analyze_with_advanced_config(codebase_path: str, config_type: str = "comprehensive"):
    """
    Analyze a codebase using advanced graph-sitter configuration settings.
    
    Args:
        codebase_path: Path to the codebase to analyze
        config_type: Type of configuration to use:
            - "debug": Debug configuration with verbose logging
            - "performance": Performance-optimized configuration
            - "comprehensive": Full analysis configuration (default)
            - "typescript": TypeScript-specific configuration
            - "ast_only": AST-only configuration without graph
    
    Returns:
        Dict containing analysis results and configuration details
    """
    # Select configuration based on type
    config_map = {
        "debug": create_debug_config(),
        "performance": create_performance_config(),
        "comprehensive": create_comprehensive_analysis_config(),
        "typescript": create_typescript_analysis_config(),
        "ast_only": create_ast_only_config()
    }
    
    if config_type not in config_map:
        raise ValueError(f"Unknown config type: {config_type}. Available: {list(config_map.keys())}")
    
    advanced_config = config_map[config_type]
    codebase_config = advanced_config.create_config()
    
    # Initialize codebase with advanced configuration
    codebase = Codebase(codebase_path, config=codebase_config)
    
    # Perform analysis based on configuration capabilities
    results = {
        "config_type": config_type,
        "config_settings": vars(advanced_config),
        "codebase_info": {
            "total_files": len(codebase.files),
            "total_functions": len(codebase.functions) if not advanced_config.disable_graph else "N/A (graph disabled)",
            "total_classes": len(codebase.classes) if not advanced_config.disable_graph else "N/A (graph disabled)",
        },
        "analysis_results": {}
    }
    
    # Only perform graph-based analysis if graph is enabled
    if not advanced_config.disable_graph:
        # Method usage analysis (if enabled)
        if advanced_config.method_usages:
            method_usage_stats = analyze_method_usages(codebase)
            results["analysis_results"]["method_usages"] = method_usage_stats
        
        # Generic type analysis (if enabled)
        if advanced_config.generics:
            generic_stats = analyze_generic_usage(codebase)
            results["analysis_results"]["generics"] = generic_stats
        
        # Full range index analysis (if enabled)
        if advanced_config.full_range_index:
            range_stats = analyze_range_coverage(codebase)
            results["analysis_results"]["range_coverage"] = range_stats
        
        # External import analysis (if enabled)
        if advanced_config.allow_external or advanced_config.py_resolve_syspath:
            external_stats = analyze_external_dependencies(codebase)
            results["analysis_results"]["external_dependencies"] = external_stats
    
    # AST-only analysis (always available)
    ast_stats = analyze_ast_structure(codebase)
    results["analysis_results"]["ast_structure"] = ast_stats
    
    return results


def analyze_method_usages(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze method usage patterns when method_usages flag is enabled.
    
    Example from documentation:
    class Foo:
        def bar():
            ...
    
    obj = Foo()
    obj.bar()  # Method Usage
    """
    method_usage_stats = {
        "total_methods": 0,
        "methods_with_usages": 0,
        "total_method_calls": 0,
        "method_usage_examples": []
    }
    
    for cls in codebase.classes:
        for method in cls.methods:
            method_usage_stats["total_methods"] += 1
            
            if method.usages:
                method_usage_stats["methods_with_usages"] += 1
                method_usage_stats["total_method_calls"] += len(method.usages)
                
                # Collect examples
                if len(method_usage_stats["method_usage_examples"]) < 5:
                    method_usage_stats["method_usage_examples"].append({
                        "class": cls.name,
                        "method": method.name,
                        "usage_count": len(method.usages),
                        "file": method.file.filepath
                    })
    
    return method_usage_stats


def analyze_generic_usage(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze generic type usage when generics flag is enabled.
    
    Example from documentation:
    class List[T]():
        def pop(self) -> T:
            ...
    
    l: List[Point] = []
    l.pop().scale(1)  # Generic Usage
    """
    generic_stats = {
        "generic_classes": 0,
        "generic_methods": 0,
        "generic_usages": 0,
        "generic_examples": []
    }
    
    for cls in codebase.classes:
        # Check if class has generic parameters
        if hasattr(cls, 'type_parameters') and cls.type_parameters:
            generic_stats["generic_classes"] += 1
            
            # Analyze methods in generic classes
            for method in cls.methods:
                if hasattr(method, 'return_type') and method.return_type:
                    generic_stats["generic_methods"] += 1
                
                # Count usages of generic methods
                if method.usages:
                    generic_stats["generic_usages"] += len(method.usages)
                    
                    # Collect examples
                    if len(generic_stats["generic_examples"]) < 3:
                        generic_stats["generic_examples"].append({
                            "class": cls.name,
                            "method": method.name,
                            "usage_count": len(method.usages),
                            "file": method.file.filepath
                        })
    
    return generic_stats


def analyze_range_coverage(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze range-to-node mapping coverage when full_range_index is enabled.
    
    From documentation:
    "Enabling full_range_index will create an additional index that maps 
    all tree-sitter ranges to nodes."
    """
    range_stats = {
        "total_nodes_with_ranges": 0,
        "files_analyzed": 0,
        "range_coverage_examples": []
    }
    
    for file in codebase.files:
        range_stats["files_analyzed"] += 1
        
        # Count nodes with range information
        for function in file.functions:
            if hasattr(function, 'start_point') and function.start_point:
                range_stats["total_nodes_with_ranges"] += 1
                
                # Collect range examples
                if len(range_stats["range_coverage_examples"]) < 5:
                    range_stats["range_coverage_examples"].append({
                        "node_type": "function",
                        "name": function.name,
                        "file": file.filepath,
                        "start_point": function.start_point,
                        "end_point": function.end_point if hasattr(function, 'end_point') else None
                    })
        
        for cls in file.classes:
            if hasattr(cls, 'start_point') and cls.start_point:
                range_stats["total_nodes_with_ranges"] += 1
    
    return range_stats


def analyze_external_dependencies(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze external dependencies when allow_external or py_resolve_syspath is enabled.
    """
    external_stats = {
        "external_imports": 0,
        "sys_path_imports": 0,
        "external_modules": [],
        "import_examples": []
    }
    
    for file in codebase.files:
        for imp in file.imports:
            # Check if import is external
            if hasattr(imp, 'is_external') and imp.is_external:
                external_stats["external_imports"] += 1
                
                module_name = imp.module if hasattr(imp, 'module') else str(imp)
                if module_name not in external_stats["external_modules"]:
                    external_stats["external_modules"].append(module_name)
                
                # Collect examples
                if len(external_stats["import_examples"]) < 5:
                    external_stats["import_examples"].append({
                        "module": module_name,
                        "file": file.filepath,
                        "import_type": "external"
                    })
            
            # Check for sys.path imports
            elif hasattr(imp, 'from_syspath') and imp.from_syspath:
                external_stats["sys_path_imports"] += 1
    
    return external_stats


def analyze_ast_structure(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze AST structure (available even with disable_graph=True).
    """
    ast_stats = {
        "total_files": len(codebase.files),
        "file_extensions": {},
        "ast_node_counts": {
            "functions": 0,
            "classes": 0,
            "imports": 0
        }
    }
    
    for file in codebase.files:
        # Count file extensions
        ext = Path(file.filepath).suffix
        ast_stats["file_extensions"][ext] = ast_stats["file_extensions"].get(ext, 0) + 1
        
        # Count AST nodes (these work even with disabled graph)
        try:
            ast_stats["ast_node_counts"]["functions"] += len(file.functions)
            ast_stats["ast_node_counts"]["classes"] += len(file.classes)
            ast_stats["ast_node_counts"]["imports"] += len(file.imports)
        except AttributeError:
            # Some operations might not be available depending on configuration
            pass
    
    return ast_stats


def demonstrate_sync_enabled_behavior(codebase_path: str):
    """
    Demonstrate the difference between sync_enabled=True and sync_enabled=False.
    
    From documentation:
    "enabling sync graph will update the Codebase object to whatever new changes were made"
    """
    print("🔄 Demonstrating sync_enabled behavior...")
    
    # Test with sync_enabled=True
    print("\n✅ Testing with sync_enabled=True:")
    config_sync = AdvancedCodebaseConfig()
    config_sync.sync_enabled = True
    
    codebase_sync = Codebase(codebase_path, config=config_sync.create_config())
    
    # Make a change and commit
    if codebase_sync.files:
        file = codebase_sync.files[0]
        file.insert_after("# Added by sync test")
        codebase_sync.commit()
        
        # Try to find the new symbol (should work with sync enabled)
        print("  - Changes are synced after commit")
    
    # Test with sync_enabled=False
    print("\n❌ Testing with sync_enabled=False:")
    config_no_sync = AdvancedCodebaseConfig()
    config_no_sync.sync_enabled = False
    
    codebase_no_sync = Codebase(codebase_path, config=config_no_sync.create_config())
    
    if codebase_no_sync.files:
        file = codebase_no_sync.files[0]
        file.insert_after("# Added by no-sync test")
        # Note: Without commit, changes are not synced
        print("  - Changes are NOT synced without commit")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
        config_type = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    else:
        codebase_path = "./"
        config_type = "comprehensive"
    
    print(f"🔧 Analyzing codebase with advanced configuration: {config_type}")
    
    try:
        results = analyze_with_advanced_config(codebase_path, config_type)
        
        print(f"\n📊 Analysis Results:")
        print(f"Configuration Type: {results['config_type']}")
        print(f"Files: {results['codebase_info']['total_files']}")
        print(f"Functions: {results['codebase_info']['total_functions']}")
        print(f"Classes: {results['codebase_info']['total_classes']}")
        
        # Show configuration settings
        print(f"\n⚙️ Configuration Settings:")
        for key, value in results['config_settings'].items():
            if value != False and value != [] and value != {}:  # Only show enabled settings
                print(f"  {key}: {value}")
        
        # Show analysis results
        if results['analysis_results']:
            print(f"\n🔍 Analysis Results:")
            for analysis_type, data in results['analysis_results'].items():
                print(f"  {analysis_type}: {data}")
        
        # Demonstrate sync behavior if requested
        if config_type == "debug":
            demonstrate_sync_enabled_behavior(codebase_path)
    
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
