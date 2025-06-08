#!/usr/bin/env python3
"""
Graph-Sitter API Demo

Demonstrates the new consolidated graph-sitter API based on the official
graph-sitter.com documentation and features.
"""

from contexten.extensions.graph_sitter import (
    # Main API functions
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    
    # Pre-computed graph element access
    CodebaseElements,
    
    # Configuration
    CodebaseConfig,
    PresetConfigs,
    
    # Enhanced analyzers
    EnhancedCodebaseAnalyzer,
    EnhancedResolver,
)


def demo_main_api():
    """Demonstrate the main API functions."""
    print("=== Graph-Sitter Main API Demo ===\n")
    
    # Configuration as shown in the documentation
    config = CodebaseConfig(
        # Performance optimizations
        method_usages=True,          # Enable method usage resolution
        generics=True,               # Enable generic type resolution
        sync_enabled=True,           # Enable graph sync during commits
        
        # Advanced analysis
        full_range_index=True,       # Full range-to-node mapping
        py_resolve_syspath=True,     # Resolve sys.path imports
        
        # Experimental features
        exp_lazy_graph=False,        # Lazy graph construction
    )
    
    codebase_path = "./src"  # Example path
    
    try:
        # 1. Get comprehensive codebase summary
        print("1. Getting codebase summary...")
        summary = get_codebase_summary(codebase_path, config)
        print(f"   Total files: {summary.total_files}")
        print(f"   Total functions: {summary.total_functions}")
        print(f"   Total classes: {summary.total_classes}")
        print(f"   Languages: {summary.languages}")
        print(f"   External modules: {len(summary.external_modules)}")
        print()
        
        # 2. Analyze a specific file
        print("2. Analyzing specific file...")
        file_summary = get_file_summary(codebase_path, "src/main.py", config)
        print(f"   File: {file_summary.filepath}")
        print(f"   Language: {file_summary.language}")
        print(f"   Functions: {len(file_summary.functions)}")
        print(f"   Classes: {len(file_summary.classes)}")
        print(f"   Complexity score: {file_summary.complexity_score}")
        print()
        
        # 3. Analyze a specific class
        print("3. Analyzing specific class...")
        class_summary = get_class_summary(codebase_path, "MyClass", config)
        print(f"   Class: {class_summary.name}")
        print(f"   Methods: {len(class_summary.methods)}")
        print(f"   Superclasses: {class_summary.superclasses}")
        print(f"   Is abstract: {class_summary.is_abstract}")
        print()
        
        # 4. Analyze a specific function
        print("4. Analyzing specific function...")
        func_summary = get_function_summary(codebase_path, "my_function", config)
        print(f"   Function: {func_summary.name}")
        print(f"   Usages: {len(func_summary.usages)}")
        print(f"   Is async: {func_summary.is_async}")
        print(f"   Is generator: {func_summary.is_generator}")
        print()
        
        # 5. Analyze a specific symbol
        print("5. Analyzing specific symbol...")
        symbol_summary = get_symbol_summary(codebase_path, "my_variable", config)
        print(f"   Symbol: {symbol_summary.name}")
        print(f"   Type: {symbol_summary.symbol_type}")
        print(f"   Scope: {symbol_summary.scope}")
        print(f"   Is exported: {symbol_summary.is_exported}")
        print()
        
    except Exception as e:
        print(f"Error in main API demo: {e}")


def demo_precomputed_graph_access():
    """Demonstrate pre-computed graph element access."""
    print("=== Pre-computed Graph Element Access Demo ===\n")
    
    config = CodebaseConfig.performance_optimized()
    codebase_path = "./src"
    
    try:
        # Access all codebase elements through graph-sitter's optimized graph structure
        codebase = CodebaseElements(codebase_path, config)
        
        print("1. Advanced Function Analysis:")
        for function in codebase.functions[:3]:  # Show first 3 functions
            print(f"   Function: {function['name']}")
            print(f"   - Usages: {len(function.get('usages', []))}")
            print(f"   - Call sites: {len(function.get('call_sites', []))}")
            print(f"   - Dependencies: {len(function.get('dependencies', []))}")
            print(f"   - Function calls: {len(function.get('function_calls', []))}")
            print(f"   - Parameters: {function.get('parameters', [])}")
            print(f"   - Return statements: {len(function.get('return_statements', []))}")
            print(f"   - Decorators: {function.get('decorators', [])}")
            print(f"   - Is async: {function.get('is_async', False)}")
            print(f"   - Is generator: {function.get('is_generator', False)}")
            print()
        
        print("2. Class Hierarchy Analysis:")
        for cls in codebase.classes[:3]:  # Show first 3 classes
            print(f"   Class: {cls['name']}")
            print(f"   - Superclasses: {cls.get('superclasses', [])}")
            print(f"   - Subclasses: {cls.get('subclasses', [])}")
            print(f"   - Methods: {len(cls.get('methods', []))}")
            print(f"   - Attributes: {len(cls.get('attributes', []))}")
            print(f"   - Decorators: {cls.get('decorators', [])}")
            print(f"   - Usages: {len(cls.get('usages', []))}")
            print(f"   - Dependencies: {len(cls.get('dependencies', []))}")
            print(f"   - Is abstract: {cls.get('is_abstract', False)}")
            print()
        
        print("3. Import Relationship Analysis:")
        for file in codebase.files[:3]:  # Show first 3 files
            print(f"   File: {file['path']}")
            print(f"   - Imports: {len(file.get('imports', []))}")
            print(f"   - Inbound imports: {len(file.get('inbound_imports', []))}")
            print(f"   - Symbols: {len(file.get('symbols', []))}")
            print(f"   - External modules: {len(file.get('external_modules', []))}")
            print()
        
        print(f"4. External Dependencies: {len(codebase.external_modules)} modules")
        print(f"   Sample modules: {codebase.external_modules[:5]}")
        print()
        
    except Exception as e:
        print(f"Error in graph access demo: {e}")


def demo_enhanced_analysis():
    """Demonstrate enhanced analysis capabilities."""
    print("=== Enhanced Analysis Demo ===\n")
    
    config = CodebaseConfig.comprehensive_analysis()
    codebase_path = "./src"
    
    try:
        # Enhanced analyzer with comprehensive features
        analyzer = EnhancedCodebaseAnalyzer(codebase_path, config)
        
        print("1. Complexity Analysis:")
        complexity = analyzer.analyze_complexity()
        print(f"   Average complexity: {complexity.get('average_complexity', 0)}")
        print(f"   High complexity functions: {len(complexity.get('high_complexity_functions', []))}")
        print()
        
        print("2. Quality Metrics:")
        quality = analyzer.analyze_quality()
        print(f"   Code coverage: {quality.get('code_coverage', 0)}%")
        print(f"   Documentation coverage: {quality.get('doc_coverage', 0)}%")
        print(f"   Test coverage: {quality.get('test_coverage', 0)}%")
        print()
        
        print("3. Dependency Analysis:")
        deps = analyzer.analyze_dependencies()
        print(f"   Circular dependencies: {len(deps.get('circular_deps', []))}")
        print(f"   External dependencies: {len(deps.get('external_deps', []))}")
        print()
        
    except Exception as e:
        print(f"Error in enhanced analysis demo: {e}")


def demo_symbol_resolution():
    """Demonstrate enhanced symbol resolution."""
    print("=== Enhanced Symbol Resolution Demo ===\n")
    
    config = CodebaseConfig.comprehensive_analysis()
    codebase_path = "./src"
    
    try:
        resolver = EnhancedResolver(codebase_path, config)
        
        print("1. Import Relationship Analysis:")
        relationships = resolver.analyze_import_relationships()
        print(f"   Total import relationships: {len(relationships)}")
        
        for rel in relationships[:3]:  # Show first 3 relationships
            print(f"   - {rel.source_file} -> {rel.target_file}")
            print(f"     Symbols: {rel.imported_symbols}")
            print(f"     Type: {rel.import_type}")
            print()
        
        print("2. Circular Import Detection:")
        circular = resolver.detect_circular_imports()
        if circular:
            print(f"   Found {len(circular)} circular import chains:")
            for chain in circular[:2]:  # Show first 2 chains
                print(f"   - {' -> '.join(chain)}")
        else:
            print("   No circular imports detected!")
        print()
        
        print("3. Symbol Resolution:")
        # Try to resolve a common symbol
        symbol = resolver.resolve_symbol("main")
        if symbol:
            print(f"   Symbol: {symbol.name}")
            print(f"   Type: {symbol.symbol_type}")
            print(f"   File: {symbol.filepath}")
            print(f"   Line: {symbol.line_number}")
            print(f"   Usages: {len(symbol.usages)}")
            print(f"   Dependencies: {len(symbol.dependencies)}")
        else:
            print("   Symbol 'main' not found")
        print()
        
    except Exception as e:
        print(f"Error in symbol resolution demo: {e}")


def demo_preset_configurations():
    """Demonstrate preset configurations."""
    print("=== Preset Configurations Demo ===\n")
    
    presets = {
        "Performance": PresetConfigs.performance(),
        "Comprehensive": PresetConfigs.comprehensive(),
        "Debug": PresetConfigs.debug(),
        "TypeScript": PresetConfigs.typescript(),
        "Minimal": PresetConfigs.minimal(),
    }
    
    for name, config in presets.items():
        print(f"{name} Configuration:")
        print(f"   Method usages: {config.method_usages}")
        print(f"   Generics: {config.generics}")
        print(f"   Sync enabled: {config.sync_enabled}")
        print(f"   Full range index: {config.full_range_index}")
        print(f"   Debug: {config.debug}")
        print(f"   Lazy graph: {config.exp_lazy_graph}")
        print()


if __name__ == "__main__":
    print("Graph-Sitter API Demonstration")
    print("=" * 50)
    print()
    
    # Run all demos
    demo_main_api()
    demo_precomputed_graph_access()
    demo_enhanced_analysis()
    demo_symbol_resolution()
    demo_preset_configurations()
    
    print("Demo completed!")
    print("\nFor more information, visit: https://graph-sitter.com")

