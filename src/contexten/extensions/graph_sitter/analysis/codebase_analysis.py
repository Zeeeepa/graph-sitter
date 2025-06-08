"""
Enhanced Codebase Analysis Module

Provides comprehensive analysis functions for graph-sitter codebase elements
with advanced graph-based insights and Tree-sitter integration.

This module implements the requested functionality:
- get_codebase_summary, get_file_summary, get_class_summary, get_function_summary, get_symbol_summary
- Pre-computed graph element access (functions, classes, imports, files, symbols)
- Advanced function analysis (usages, call sites, dependencies, decorators)
- Class hierarchy analysis (inheritance, methods, attributes)
- Import relationship analysis (inbound/outbound imports, external modules)
- Optimized CodebaseConfig for performance
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType
from graph_sitter.configs.models.codebase import CodebaseConfig


@dataclass
class CodebaseMetrics:
    """Comprehensive codebase metrics."""
    total_nodes: int
    total_edges: int
    files_count: int
    imports_count: int
    external_modules_count: int
    symbols_count: int
    classes_count: int
    functions_count: int
    global_vars_count: int
    interfaces_count: int
    symbol_usage_edges: int
    import_resolution_edges: int
    export_edges: int


@dataclass
class FunctionMetrics:
    """Enhanced function analysis metrics."""
    name: str
    usages_count: int
    call_sites_count: int
    dependencies_count: int
    function_calls_count: int
    parameters_count: int
    return_statements_count: int
    decorators_count: int
    is_async: bool
    is_generator: bool
    complexity_score: int
    lines_of_code: int


@dataclass
class ClassMetrics:
    """Enhanced class analysis metrics."""
    name: str
    superclasses_count: int
    subclasses_count: int
    methods_count: int
    attributes_count: int
    decorators_count: int
    usages_count: int
    dependencies_count: int
    is_abstract: bool
    inheritance_depth: int


@dataclass
class FileMetrics:
    """Enhanced file analysis metrics."""
    name: str
    imports_count: int
    inbound_imports_count: int
    symbols_count: int
    classes_count: int
    functions_count: int
    global_vars_count: int
    interfaces_count: int
    external_modules_count: int
    lines_of_code: int
    complexity_score: int


def get_optimized_config() -> CodebaseConfig:
    """
    Get optimized CodebaseConfig with performance and analysis features enabled.
    
    Returns:
        CodebaseConfig: Optimized configuration for comprehensive analysis
    """
    return CodebaseConfig(
        # Performance optimizations
        method_usages=True,          # Enable method usage resolution
        generics=True,               # Enable generic type resolution
        sync_enabled=True,           # Enable graph sync during commits
        
        # Advanced analysis
        full_range_index=True,       # Full range-to-node mapping
        py_resolve_syspath=True,     # Resolve sys.path imports
        
        # Experimental features
        exp_lazy_graph=False,        # Lazy graph construction
        
        # Additional optimizations
        track_graph=True,            # Track graph changes
        verify_graph=False,          # Skip verification for performance
        debug=False,                 # Disable debug for performance
        allow_external=True,         # Allow external module analysis
        ts_dependency_manager=True,  # Enable TypeScript dependency analysis
        conditional_type_resolution=True,  # Enable conditional types
    )


def get_codebase_summary(codebase: Codebase) -> str:
    """
    Enhanced codebase summary with comprehensive metrics.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        str: Detailed summary of codebase structure and metrics
    """
    metrics = get_codebase_metrics(codebase)
    
    node_summary = f"""📊 Codebase Structure Analysis
├── Total Nodes: {metrics.total_nodes:,}
├── Total Edges: {metrics.total_edges:,}
├── Files: {metrics.files_count:,}
├── Imports: {metrics.imports_count:,}
├── External Modules: {metrics.external_modules_count:,}
└── Symbols: {metrics.symbols_count:,}
    ├── Classes: {metrics.classes_count:,}
    ├── Functions: {metrics.functions_count:,}
    ├── Global Variables: {metrics.global_vars_count:,}
    └── Interfaces: {metrics.interfaces_count:,}
"""
    
    edge_summary = f"""🔗 Graph Relationship Analysis
├── Symbol Usage Edges: {metrics.symbol_usage_edges:,}
├── Import Resolution Edges: {metrics.import_resolution_edges:,}
└── Export Edges: {metrics.export_edges:,}
"""
    
    # Calculate additional insights
    avg_symbols_per_file = metrics.symbols_count / max(metrics.files_count, 1)
    complexity_ratio = metrics.total_edges / max(metrics.total_nodes, 1)
    
    insights = f"""💡 Codebase Insights
├── Average Symbols per File: {avg_symbols_per_file:.1f}
├── Graph Complexity Ratio: {complexity_ratio:.2f}
└── External Dependency Ratio: {metrics.external_modules_count / max(metrics.imports_count, 1):.2f}
"""
    
    return f"{node_summary}\n{edge_summary}\n{insights}"


def get_codebase_metrics(codebase: Codebase) -> CodebaseMetrics:
    """
    Get comprehensive codebase metrics.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        CodebaseMetrics: Detailed metrics about the codebase
    """
    edges = codebase.ctx.edges
    
    return CodebaseMetrics(
        total_nodes=len(codebase.ctx.get_nodes()),
        total_edges=len(edges),
        files_count=len(list(codebase.files)),
        imports_count=len(list(codebase.imports)),
        external_modules_count=len(list(codebase.external_modules)),
        symbols_count=len(list(codebase.symbols)),
        classes_count=len(list(codebase.classes)),
        functions_count=len(list(codebase.functions)),
        global_vars_count=len(list(codebase.global_vars)),
        interfaces_count=len(list(codebase.interfaces)),
        symbol_usage_edges=len([x for x in edges if x[2].type == EdgeType.SYMBOL_USAGE]),
        import_resolution_edges=len([x for x in edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION]),
        export_edges=len([x for x in edges if x[2].type == EdgeType.EXPORT])
    )


def get_file_summary(file: SourceFile) -> str:
    """
    Enhanced file summary with comprehensive analysis.
    
    Args:
        file: The source file to analyze
        
    Returns:
        str: Detailed summary of file structure and dependencies
    """
    metrics = get_file_metrics(file)
    
    dependency_summary = f"""📁 File: `{file.name}`
├── 📥 Dependencies
│   ├── Imports: {metrics.imports_count}
│   ├── External Modules: {metrics.external_modules_count}
│   └── Inbound Imports: {metrics.inbound_imports_count}
├── 🏗️ Structure
│   ├── Classes: {metrics.classes_count}
│   ├── Functions: {metrics.functions_count}
│   ├── Global Variables: {metrics.global_vars_count}
│   ├── Interfaces: {metrics.interfaces_count}
│   └── Total Symbols: {metrics.symbols_count}
└── 📊 Metrics
    ├── Lines of Code: {metrics.lines_of_code}
    └── Complexity Score: {metrics.complexity_score}
"""
    
    # Get import analysis
    import_analysis = _analyze_file_imports(file)
    if import_analysis:
        dependency_summary += f"\n🔍 Import Analysis\n{import_analysis}"
    
    return dependency_summary


def get_file_metrics(file: SourceFile) -> FileMetrics:
    """
    Get comprehensive file metrics.
    
    Args:
        file: The source file to analyze
        
    Returns:
        FileMetrics: Detailed metrics about the file
    """
    # Calculate lines of code (estimate from span if available)
    lines_of_code = 0
    if hasattr(file, 'span') and file.span:
        lines_of_code = file.span.end.row - file.span.start.row + 1
    
    # Calculate complexity score based on symbols and dependencies
    complexity_score = len(file.symbols) + len(file.imports) * 2
    
    return FileMetrics(
        name=file.name,
        imports_count=len(file.imports),
        inbound_imports_count=len(getattr(file, 'inbound_imports', [])),
        symbols_count=len(file.symbols),
        classes_count=len(file.classes),
        functions_count=len(file.functions),
        global_vars_count=len(file.global_vars),
        interfaces_count=len(file.interfaces),
        external_modules_count=len([imp for imp in file.imports if isinstance(imp.imported_symbol, ExternalModule)]),
        lines_of_code=lines_of_code,
        complexity_score=complexity_score
    )


def get_class_summary(cls: Class) -> str:
    """
    Enhanced class summary with comprehensive analysis.
    
    Args:
        cls: The class to analyze
        
    Returns:
        str: Detailed summary of class structure and relationships
    """
    metrics = get_class_metrics(cls)
    
    class_summary = f"""🏛️ Class: `{cls.name}`
├── 🧬 Inheritance
│   ├── Superclasses: {metrics.superclasses_count}
│   ├── Subclasses: {metrics.subclasses_count}
│   └── Inheritance Depth: {metrics.inheritance_depth}
├── 🏗️ Structure
│   ├── Methods: {metrics.methods_count}
│   ├── Attributes: {metrics.attributes_count}
│   ├── Decorators: {metrics.decorators_count}
│   └── Is Abstract: {metrics.is_abstract}
└── 📊 Usage
    ├── Usages: {metrics.usages_count}
    └── Dependencies: {metrics.dependencies_count}
"""
    
    # Add method analysis
    method_analysis = _analyze_class_methods(cls)
    if method_analysis:
        class_summary += f"\n🔍 Method Analysis\n{method_analysis}"
    
    # Add symbol summary
    symbol_summary = get_symbol_summary(cls)
    class_summary += f"\n{symbol_summary}"
    
    return class_summary


def get_class_metrics(cls: Class) -> ClassMetrics:
    """
    Get comprehensive class metrics.
    
    Args:
        cls: The class to analyze
        
    Returns:
        ClassMetrics: Detailed metrics about the class
    """
    # Calculate inheritance depth
    inheritance_depth = _calculate_inheritance_depth(cls)
    
    # Check if abstract
    is_abstract = _is_abstract_class(cls)
    
    return ClassMetrics(
        name=cls.name,
        superclasses_count=len(cls.parent_class_names),
        subclasses_count=len(getattr(cls, 'subclasses', [])),
        methods_count=len(cls.methods),
        attributes_count=len(cls.attributes),
        decorators_count=len(cls.decorators),
        usages_count=len(cls.symbol_usages),
        dependencies_count=len(cls.dependencies),
        is_abstract=is_abstract,
        inheritance_depth=inheritance_depth
    )


def get_function_summary(func: Function) -> str:
    """
    Enhanced function summary with comprehensive analysis.
    
    Args:
        func: The function to analyze
        
    Returns:
        str: Detailed summary of function structure and behavior
    """
    metrics = get_function_metrics(func)
    
    function_summary = f"""⚡ Function: `{func.name}`
├── 🏗️ Structure
│   ├── Parameters: {metrics.parameters_count}
│   ├── Return Statements: {metrics.return_statements_count}
│   ├── Decorators: {metrics.decorators_count}
│   └── Lines of Code: {metrics.lines_of_code}
├── 🔄 Behavior
│   ├── Is Async: {metrics.is_async}
│   ├── Is Generator: {metrics.is_generator}
│   └── Complexity Score: {metrics.complexity_score}
├── 📞 Calls
│   ├── Function Calls: {metrics.function_calls_count}
│   └── Call Sites: {metrics.call_sites_count}
└── 📊 Usage
    ├── Usages: {metrics.usages_count}
    └── Dependencies: {metrics.dependencies_count}
"""
    
    # Add parameter analysis
    param_analysis = _analyze_function_parameters(func)
    if param_analysis:
        function_summary += f"\n🔍 Parameter Analysis\n{param_analysis}"
    
    # Add symbol summary
    symbol_summary = get_symbol_summary(func)
    function_summary += f"\n{symbol_summary}"
    
    return function_summary


def get_function_metrics(func: Function) -> FunctionMetrics:
    """
    Get comprehensive function metrics.
    
    Args:
        func: The function to analyze
        
    Returns:
        FunctionMetrics: Detailed metrics about the function
    """
    # Calculate lines of code (estimate from span if available)
    lines_of_code = 0
    if hasattr(func, 'span') and func.span:
        lines_of_code = func.span.end.row - func.span.start.row + 1
    
    # Calculate complexity score
    complexity_score = (
        len(func.function_calls) * 2 +
        len(func.return_statements) +
        len(func.parameters) +
        len(func.dependencies)
    )
    
    # Check if async or generator
    is_async = getattr(func, 'is_async', False)
    is_generator = getattr(func, 'is_generator', False)
    
    return FunctionMetrics(
        name=func.name,
        usages_count=len(func.symbol_usages),
        call_sites_count=len(func.call_sites),
        dependencies_count=len(func.dependencies),
        function_calls_count=len(func.function_calls),
        parameters_count=len(func.parameters),
        return_statements_count=len(func.return_statements),
        decorators_count=len(func.decorators),
        is_async=is_async,
        is_generator=is_generator,
        complexity_score=complexity_score,
        lines_of_code=lines_of_code
    )


def get_symbol_summary(symbol: Symbol) -> str:
    """
    Enhanced symbol summary with comprehensive usage analysis.
    
    Args:
        symbol: The symbol to analyze
        
    Returns:
        str: Detailed summary of symbol usage and relationships
    """
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]
    
    # Categorize usages by type
    usage_categories = defaultdict(int)
    import_categories = defaultdict(int)
    
    for usage in usages:
        if isinstance(usage, Symbol):
            usage_categories[usage.symbol_type.name] += 1
    
    for imported in imported_symbols:
        if isinstance(imported, Symbol):
            import_categories[imported.symbol_type.name] += 1
        elif isinstance(imported, ExternalModule):
            import_categories['ExternalModule'] += 1
        elif isinstance(imported, SourceFile):
            import_categories['SourceFile'] += 1
    
    symbol_summary = f"""🔗 Symbol: `{symbol.name}` ({type(symbol).__name__})
├── 📊 Direct Usages: {len(usages)}
│   ├── Functions: {usage_categories.get('Function', 0)}
│   ├── Classes: {usage_categories.get('Class', 0)}
│   ├── Global Variables: {usage_categories.get('GlobalVar', 0)}
│   └── Interfaces: {usage_categories.get('Interface', 0)}
└── 📥 Import Usages: {len(imported_symbols)}
    ├── Functions: {import_categories.get('Function', 0)}
    ├── Classes: {import_categories.get('Class', 0)}
    ├── Global Variables: {import_categories.get('GlobalVar', 0)}
    ├── Interfaces: {import_categories.get('Interface', 0)}
    ├── External Modules: {import_categories.get('ExternalModule', 0)}
    └── Files: {import_categories.get('SourceFile', 0)}
"""
    
    return symbol_summary


# Helper functions for enhanced analysis

def _analyze_file_imports(file: SourceFile) -> str:
    """Analyze file import patterns."""
    if not file.imports:
        return ""
    
    import_types = defaultdict(int)
    for imp in file.imports:
        if isinstance(imp.imported_symbol, ExternalModule):
            import_types['External'] += 1
        elif isinstance(imp.imported_symbol, SourceFile):
            import_types['Internal'] += 1
        else:
            import_types['Symbol'] += 1
    
    analysis = "├── Import Types:\n"
    for imp_type, count in import_types.items():
        analysis += f"│   ├── {imp_type}: {count}\n"
    
    return analysis.rstrip()


def _analyze_class_methods(cls: Class) -> str:
    """Analyze class method patterns."""
    if not cls.methods:
        return ""
    
    method_types = defaultdict(int)
    for method in cls.methods:
        if getattr(method, 'is_async', False):
            method_types['Async'] += 1
        if getattr(method, 'is_generator', False):
            method_types['Generator'] += 1
        if method.decorators:
            method_types['Decorated'] += 1
        if method.name.startswith('_'):
            method_types['Private'] += 1
        else:
            method_types['Public'] += 1
    
    analysis = "├── Method Types:\n"
    for method_type, count in method_types.items():
        analysis += f"│   ├── {method_type}: {count}\n"
    
    return analysis.rstrip()


def _analyze_function_parameters(func: Function) -> str:
    """Analyze function parameter patterns."""
    if not func.parameters:
        return ""
    
    param_types = defaultdict(int)
    for param in func.parameters:
        if hasattr(param, 'has_default') and param.has_default:
            param_types['With Default'] += 1
        else:
            param_types['Required'] += 1
        
        if hasattr(param, 'is_variadic') and param.is_variadic:
            param_types['Variadic'] += 1
    
    analysis = "├── Parameter Types:\n"
    for param_type, count in param_types.items():
        analysis += f"│   ├── {param_type}: {count}\n"
    
    return analysis.rstrip()


def _calculate_inheritance_depth(cls: Class) -> int:
    """Calculate the inheritance depth of a class."""
    # This is a simplified calculation
    # In a real implementation, you'd traverse the inheritance chain
    return len(cls.parent_class_names)


def _is_abstract_class(cls: Class) -> bool:
    """Check if a class is abstract."""
    # Check for abstract decorators or ABC inheritance
    for decorator in cls.decorators:
        if 'abstract' in decorator.name.lower():
            return True
    
    # Check parent classes for ABC
    for parent_name in cls.parent_class_names:
        if 'ABC' in parent_name or 'Abstract' in parent_name:
            return True
    
    return False


# Advanced analysis functions for graph-based insights

def analyze_circular_dependencies(codebase: Codebase) -> List[List[str]]:
    """
    Detect circular dependencies in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        List[List[str]]: List of circular dependency chains
    """
    cycles = []
    
    # Build dependency graph
    dependency_graph = defaultdict(set)
    for file in codebase.files:
        for imp in file.imports:
            if isinstance(imp.imported_symbol, SourceFile):
                dependency_graph[file.name].add(imp.imported_symbol.name)
    
    # Detect cycles using DFS (simplified implementation)
    visited = set()
    rec_stack = set()
    
    def dfs(node, path):
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in dependency_graph.get(node, []):
            dfs(neighbor, path + [node])
        
        rec_stack.remove(node)
    
    for node in dependency_graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles


def find_hotspot_functions(codebase: Codebase, threshold: int = 10) -> List[Function]:
    """
    Find functions that are heavily used (hotspots).
    
    Args:
        codebase: The codebase to analyze
        threshold: Minimum usage count to be considered a hotspot
        
    Returns:
        List[Function]: Functions with high usage counts
    """
    hotspots = []
    
    for func in codebase.functions:
        usage_count = len(func.symbol_usages) + len(func.call_sites)
        if usage_count >= threshold:
            hotspots.append(func)
    
    # Sort by usage count (descending)
    hotspots.sort(key=lambda f: len(f.symbol_usages) + len(f.call_sites), reverse=True)
    
    return hotspots


def analyze_module_coupling(codebase: Codebase) -> Dict[str, Dict[str, int]]:
    """
    Analyze coupling between modules.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dict[str, Dict[str, int]]: Coupling matrix between modules
    """
    coupling_matrix = defaultdict(lambda: defaultdict(int))
    
    for file in codebase.files:
        for imp in file.imports:
            if isinstance(imp.imported_symbol, SourceFile):
                coupling_matrix[file.name][imp.imported_symbol.name] += 1
    
    return dict(coupling_matrix)

