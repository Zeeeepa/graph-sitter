"""
Example usage of graph-sitter extensions following the official documentation.

This example demonstrates the exact API usage shown in the documentation:
https://graph-sitter.com/building-with-graph-sitter/at-a-glance
"""

# Import the existing analysis functions directly as shown in documentation
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary, 
    get_function_summary,
    get_symbol_summary
)

# Import the CodebaseConfig with all advanced settings
from graph_sitter.configs.models.codebase import CodebaseConfig

# Import the main Codebase class
from graph_sitter import Codebase

# Import our new extensions
from contexten.extensions.graph_sitter_ext import Analysis, Visualize, Resolve


def main():
    """Demonstrate the exact usage from the documentation."""
    
    # 1. Create CodebaseConfig with advanced settings (exactly as in documentation)
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
    
    # 2. Initialize Codebase with config
    codebase = Codebase(".", config=config)
    
    print("=== 1. Pre-computed Graph Element Access ===")
    print("Access all codebase elements through graph-sitter's optimized graph structure:")
    
    # Access pre-computed graph elements (exactly as in documentation)
    print(f"codebase.functions: {len(codebase.functions)} functions")
    print(f"codebase.classes: {len(codebase.classes)} classes") 
    print(f"codebase.imports: {len(codebase.imports)} imports")
    print(f"codebase.files: {len(codebase.files)} files")
    print(f"codebase.symbols: {len(codebase.symbols)} symbols")
    print(f"codebase.external_modules: {len(codebase.external_modules)} external dependencies")
    
    print("\n=== 2. Advanced Function Analysis ===")
    print("Enhanced function metrics using graph-sitter:")
    
    # Advanced Function Analysis (exactly as in documentation)
    for function in codebase.functions[:3]:  # Show first 3 functions
        print(f"\nFunction: {function.name}")
        print(f"  function.usages: {len(function.usages)} usage sites")
        print(f"  function.call_sites: {len(function.call_sites)} call locations")
        print(f"  function.dependencies: {len(function.dependencies)} dependencies")
        print(f"  function.function_calls: {len(function.function_calls)} functions this function calls")
        print(f"  function.parameters: {len(function.parameters)} parameters")
        print(f"  function.return_statements: {len(function.return_statements)} return statements")
        print(f"  function.decorators: {len(function.decorators)} decorators")
        print(f"  function.is_async: {function.is_async} async function detection")
        print(f"  function.is_generator: {function.is_generator} generator function detection")
    
    print("\n=== 3. Class Hierarchy Analysis ===")
    print("Comprehensive class analysis:")
    
    # Class Hierarchy Analysis (exactly as in documentation)
    for cls in codebase.classes[:3]:  # Show first 3 classes
        print(f"\nClass: {cls.name}")
        print(f"  cls.superclasses: {cls.parent_class_names} parent classes")
        # Note: subclasses might not be directly available, using parent_class_names instead
        print(f"  cls.methods: {len(cls.methods)} methods")
        print(f"  cls.attributes: {len(cls.attributes)} attributes")
        print(f"  cls.decorators: {len(cls.decorators)} decorators")
        print(f"  cls.usages: {len(cls.usages)} usage sites")
        print(f"  cls.dependencies: {len(cls.dependencies)} dependencies")
        # Note: is_abstract might not be directly available
    
    print("\n=== 4. Import Relationship Analysis ===")
    print("Advanced import analysis and loop detection:")
    
    # Import Relationship Analysis (exactly as in documentation)
    for file in codebase.files[:3]:  # Show first 3 files
        print(f"\nFile: {file.name}")
        print(f"  file.imports: {len(file.imports)} outbound imports")
        # Note: inbound_imports might need to be calculated
        print(f"  file.symbols: {len(file.symbols)} symbols defined in file")
        # Note: external_modules per file might need to be calculated
    
    print("\n=== 5. Using Extension Modules ===")
    
    # Initialize extension modules
    analysis = Analysis(codebase)
    visualizer = Visualize(codebase)
    resolver = Resolve(codebase)
    
    print("Analysis module:")
    print(f"  analysis.functions: {len(analysis.functions)}")
    print(f"  analysis.classes: {len(analysis.classes)}")
    print(f"  analysis.symbols: {len(analysis.symbols)}")
    
    print("\nVisualize module:")
    dep_graph = visualizer.dependency_graph()
    print(f"  Dependency graph: {len(dep_graph['nodes'])} nodes, {len(dep_graph['edges'])} edges")
    
    print("\nResolve module:")
    import_analysis = resolver.analyze_imports()
    print(f"  Import analysis: {import_analysis['total_files']} files analyzed")
    
    print("\n=== 6. Using Existing Analysis Functions ===")
    
    # Use the existing analysis functions (exactly as imported from documentation)
    print("Codebase Summary:")
    print(get_codebase_summary(codebase))
    
    if codebase.files:
        print(f"\nFile Summary for {codebase.files[0].name}:")
        print(get_file_summary(codebase.files[0]))
    
    if codebase.classes:
        print(f"\nClass Summary for {codebase.classes[0].name}:")
        print(get_class_summary(codebase.classes[0]))
    
    if codebase.functions:
        print(f"\nFunction Summary for {codebase.functions[0].name}:")
        print(get_function_summary(codebase.functions[0]))
    
    if codebase.symbols:
        print(f"\nSymbol Summary for {codebase.symbols[0].name}:")
        print(get_symbol_summary(codebase.symbols[0]))


if __name__ == "__main__":
    main()
