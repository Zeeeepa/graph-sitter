"""
Codebase Summary Analysis

Provides comprehensive summary functions for analyzing codebase structure,
dependencies, and usage patterns. Based on features from README4.md.
"""

from typing import Dict, List, Any, Optional
from collections import Counter

try:
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types for when graph-sitter is not available
    Codebase = Any
    SourceFile = Any
    Class = Any
    Function = Any
    Symbol = Any


def get_codebase_summary(codebase: Codebase) -> str:
    """
    Generate a comprehensive summary of the codebase structure.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Formatted string with codebase statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "Graph-sitter not available for codebase analysis"
    
    try:
        node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
        
        edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
"""
        
        return f"{node_summary}\n{edge_summary}"
    except Exception as e:
        return f"Error generating codebase summary: {str(e)}"


def get_file_summary(file: SourceFile) -> str:
    """
    Generate a summary of a specific file's dependencies and usage.
    
    Args:
        file: The source file to analyze
        
    Returns:
        Formatted string with file statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "Graph-sitter not available for file analysis"
    
    try:
        return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""
    except Exception as e:
        return f"Error generating file summary for {file.name}: {str(e)}"


def get_class_summary(cls: Class) -> str:
    """
    Generate a summary of a class's structure and dependencies.
    
    Args:
        cls: The class to analyze
        
    Returns:
        Formatted string with class statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "Graph-sitter not available for class analysis"
    
    try:
        class_info = f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

"""
        return class_info + get_symbol_summary(cls)
    except Exception as e:
        return f"Error generating class summary for {cls.name}: {str(e)}"


def get_function_summary(func: Function) -> str:
    """
    Generate a summary of a function's structure and dependencies.
    
    Args:
        func: The function to analyze
        
    Returns:
        Formatted string with function statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "Graph-sitter not available for function analysis"
    
    try:
        function_info = f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

"""
        return function_info + get_symbol_summary(func)
    except Exception as e:
        return f"Error generating function summary for {func.name}: {str(e)}"


def get_symbol_summary(symbol: Symbol) -> str:
    """
    Generate a summary of a symbol's usage patterns.
    
    Args:
        symbol: The symbol to analyze
        
    Returns:
        Formatted string with symbol usage statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "Graph-sitter not available for symbol analysis"
    
    try:
        usages = symbol.symbol_usages
        imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

        return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
"""
    except Exception as e:
        return f"Error generating symbol summary for {symbol.name}: {str(e)}"


def get_codebase_statistics(codebase: Codebase) -> Dict[str, Any]:
    """
    Generate comprehensive statistics about the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with detailed statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        stats = {
            "overview": {
                "total_files": len(list(codebase.files)),
                "total_classes": len(list(codebase.classes)),
                "total_functions": len(list(codebase.functions)),
                "total_imports": len(list(codebase.imports)),
                "total_symbols": len(list(codebase.symbols))
            },
            "inheritance": {},
            "recursive_functions": [],
            "test_analysis": {}
        }
        
        # Find class with most inheritance
        if codebase.classes:
            classes_list = list(codebase.classes)
            deepest_class = max(classes_list, key=lambda x: len(x.superclasses))
            stats["inheritance"] = {
                "deepest_class": deepest_class.name,
                "chain_depth": len(deepest_class.superclasses),
                "chain": [s.name for s in deepest_class.superclasses]
            }
        
        # Find recursive functions
        functions_list = list(codebase.functions)
        recursive = [f for f in functions_list
                    if any(call.name == f.name for call in f.function_calls)][:5]
        stats["recursive_functions"] = [func.name for func in recursive]
        
        # Test analysis
        test_functions = [x for x in functions_list if x.name.startswith('test_')]
        test_classes = [x for x in list(codebase.classes) if x.name.startswith('Test')]
        
        stats["test_analysis"] = {
            "total_test_functions": len(test_functions),
            "total_test_classes": len(test_classes),
            "tests_per_file": len(test_functions) / len(list(codebase.files)) if codebase.files else 0
        }
        
        # Top test files by class count
        file_test_counts = Counter([x.file for x in test_classes])
        stats["test_analysis"]["top_test_files"] = [
            {
                "file": file.filepath,
                "test_count": count,
                "file_length": len(file.source),
                "functions": len(file.functions)
            }
            for file, count in file_test_counts.most_common(5)
        ]
        
        return stats
        
    except Exception as e:
        return {"error": f"Error generating statistics: {str(e)}"}


def print_codebase_overview(codebase: Codebase) -> None:
    """
    Print a formatted overview of the codebase with emojis and formatting.
    
    Args:
        codebase: The codebase to analyze
    """
    if not GRAPH_SITTER_AVAILABLE:
        print("❌ Graph-sitter not available for analysis")
        return
    
    try:
        # Print overall stats
        print("🔍 Codebase Analysis")
        print("=" * 50)
        print(f"📚 Total Classes: {len(list(codebase.classes))}")
        print(f"⚡ Total Functions: {len(list(codebase.functions))}")
        print(f"🔄 Total Imports: {len(list(codebase.imports))}")

        # Find class with most inheritance
        classes_list = list(codebase.classes)
        if classes_list:
            deepest_class = max(classes_list, key=lambda x: len(x.superclasses))
            print(f"\n🌳 Class with most inheritance: {deepest_class.name}")
            print(f"   📊 Chain Depth: {len(deepest_class.superclasses)}")
            print(f"   🔗 Chain: {' -> '.join(s.name for s in deepest_class.superclasses)}")

        # Find first 5 recursive functions
        functions_list = list(codebase.functions)
        recursive = [f for f in functions_list
                    if any(call.name == f.name for call in f.function_calls)][:5]
        if recursive:
            print(f"\n🔄 Recursive functions:")
            for func in recursive:
                print(f"  - {func.name}")

        # Test analysis
        test_functions = [x for x in functions_list if x.name.startswith('test_')]
        test_classes = [x for x in classes_list if x.name.startswith('Test')]

        print("\n🧪 Test Analysis")
        print("=" * 50)
        print(f"📝 Total Test Functions: {len(test_functions)}")
        print(f"🔬 Total Test Classes: {len(test_classes)}")
        print(f"📊 Tests per File: {len(test_functions) / len(list(codebase.files)):.1f}")

        # Find files with the most tests
        print("\n📚 Top Test Files by Class Count")
        print("-" * 50)
        file_test_counts = Counter([x.file for x in test_classes])
        for file, num_tests in file_test_counts.most_common(5):
            print(f"🔍 {num_tests} test classes: {file.filepath}")
            print(f"   📄 File Length: {len(file.source)} lines")
            print(f"   💡 Functions: {len(file.functions)}")
            
    except Exception as e:
        print(f"❌ Error printing codebase overview: {str(e)}")

