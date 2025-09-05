from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType
from graph_sitter.core.dataclasses.usage import UsageType
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import networkx as nx


def get_codebase_summary(codebase: Codebase) -> str:
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


def get_file_summary(file: SourceFile) -> str:
    # Handle missing attributes gracefully
    interfaces_count = len(getattr(file, 'interfaces', []))
    
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {interfaces_count} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
- File path: {getattr(file, 'filepath', 'Unknown')}
- Lines of code: {len(getattr(file, 'source', '').split('\n')) if hasattr(file, 'source') else 'Unknown'}
"""


def get_class_summary(cls: Class) -> str:
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
    return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """


def get_symbol_summary(symbol: Symbol) -> str:
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


# ============================================================================
# COMPREHENSIVE CODEBASE ANALYSIS FUNCTIONS
# ============================================================================

def identify_entry_points(codebase: Codebase) -> Dict[str, List[Symbol]]:
    """
    Identify entry points in the codebase using graph analysis.
    
    Returns:
        Dict with entry point categories and their symbols
    """
    entry_points = {
        'main_functions': [],
        'cli_commands': [],
        'exported_symbols': [],
        'top_level_classes': [],
        'web_routes': [],
        'decorated_functions': []
    }
    
    # Find main functions and __name__ == "__main__" patterns
    for func in codebase.functions:
        if func.name == 'main' or 'main' in func.name.lower():
            entry_points['main_functions'].append(func)
            
        # Check for CLI decorators or patterns
        for decorator in getattr(func, 'decorators', []):
            decorator_name = getattr(decorator, 'name', str(decorator)).lower()
            if any(cli_pattern in decorator_name for cli_pattern in ['command', 'click', 'argparse', 'cli']):
                entry_points['cli_commands'].append(func)
                
        # Check for web framework decorators
        for decorator in getattr(func, 'decorators', []):
            decorator_name = getattr(decorator, 'name', str(decorator)).lower()
            if any(web_pattern in decorator_name for web_pattern in ['route', 'get', 'post', 'put', 'delete', 'api']):
                entry_points['web_routes'].append(func)
                
        # Check for other important decorators
        if getattr(func, 'decorators', []):
            entry_points['decorated_functions'].append(func)
    
    # Find top-level classes (not inherited by others)
    all_classes = list(codebase.classes)
    inherited_classes = set()
    
    for cls in all_classes:
        for parent_name in getattr(cls, 'parent_class_names', []):
            # Find classes that are inherited from
            for potential_parent in all_classes:
                if potential_parent.name == str(parent_name):
                    inherited_classes.add(potential_parent)
    
    entry_points['top_level_classes'] = [cls for cls in all_classes if cls not in inherited_classes]
    
    # Find exported symbols
    for symbol in codebase.symbols:
        # Check if symbol has export edges
        out_edges = codebase.ctx.out_edges(symbol.node_id) if hasattr(symbol, 'node_id') else []
        for edge in out_edges:
            if edge[2].type == EdgeType.EXPORT:
                entry_points['exported_symbols'].append(symbol)
                break
    
    return entry_points


def detect_dead_code(codebase: Codebase) -> Dict[str, List[Symbol]]:
    """
    Detect dead code using graph traversal from entry points.
    
    Returns:
        Dict with categories of potentially dead code
    """
    entry_points = identify_entry_points(codebase)
    
    # Collect all entry point symbols
    reachable_symbols = set()
    queue = deque()
    
    for category, symbols in entry_points.items():
        for symbol in symbols:
            if symbol not in reachable_symbols:
                reachable_symbols.add(symbol)
                queue.append(symbol)
    
    # Traverse the graph from entry points
    while queue:
        current_symbol = queue.popleft()
        
        # Get all symbols this symbol depends on or calls
        try:
            dependencies = current_symbol.dependencies(UsageType.DIRECT | UsageType.INDIRECT)
            for dep in dependencies:
                if isinstance(dep, Symbol) and dep not in reachable_symbols:
                    reachable_symbols.add(dep)
                    queue.append(dep)
        except:
            pass
            
        # For functions, also check call sites and function calls
        if isinstance(current_symbol, Function):
            try:
                # Add functions called by this function
                for call in getattr(current_symbol, 'function_calls', []):
                    if hasattr(call, 'resolved_symbol') and call.resolved_symbol:
                        if call.resolved_symbol not in reachable_symbols:
                            reachable_symbols.add(call.resolved_symbol)
                            queue.append(call.resolved_symbol)
            except:
                pass
    
    # Find unreachable symbols
    all_symbols = set(codebase.symbols)
    dead_symbols = all_symbols - reachable_symbols
    
    dead_code = {
        'dead_functions': [s for s in dead_symbols if isinstance(s, Function)],
        'dead_classes': [s for s in dead_symbols if isinstance(s, Class)],
        'dead_variables': [s for s in dead_symbols if s.symbol_type == SymbolType.GlobalVar],
        'potentially_dead': []
    }
    
    # Additional check: functions/classes with no usages and no call sites
    for symbol in all_symbols:
        if symbol not in dead_symbols:  # Not already marked as dead
            try:
                usages = symbol.symbol_usages
                if isinstance(symbol, Function):
                    call_sites = getattr(symbol, 'call_sites', [])
                    if not usages and not call_sites:
                        dead_code['potentially_dead'].append(symbol)
                elif not usages:
                    dead_code['potentially_dead'].append(symbol)
            except:
                pass
    
    return dead_code


def detect_unused_parameters(codebase: Codebase) -> Dict[Function, List[str]]:
    """
    Detect unused parameters in functions.
    
    Returns:
        Dict mapping functions to their unused parameter names
    """
    unused_params = {}
    
    for func in codebase.functions:
        try:
            parameters = getattr(func, 'parameters', [])
            if not parameters:
                continue
                
            unused_in_func = []
            
            for param in parameters:
                param_name = getattr(param, 'name', str(param))
                
                # Skip special parameters
                if param_name in ['self', 'cls', '*args', '**kwargs'] or param_name.startswith('*'):
                    continue
                
                # Check if parameter is used within the function
                param_used = False
                
                # Get function's internal symbol usages
                try:
                    # Check if the function's code block contains references to this parameter
                    if hasattr(func, 'code_block'):
                        # This is a simplified check - in practice, you'd need to analyze
                        # the function's internal scope more thoroughly
                        func_source = getattr(func, 'source', '')
                        if param_name in func_source:
                            # More sophisticated check would be needed to avoid false positives
                            # from comments, strings, etc.
                            param_used = True
                except:
                    pass
                
                if not param_used:
                    unused_in_func.append(param_name)
            
            if unused_in_func:
                unused_params[func] = unused_in_func
                
        except Exception:
            continue
    
    return unused_params


def analyze_imports(codebase: Codebase) -> Dict[str, Any]:
    """
    Comprehensive import analysis: unused, circular, and unresolved imports.
    
    Returns:
        Dict with different types of import issues
    """
    import_analysis = {
        'unused_imports': [],
        'circular_imports': [],
        'unresolved_imports': [],
        'import_statistics': {}
    }
    
    # Analyze unused imports
    for file in codebase.files:
        try:
            file_imports = getattr(file, 'imports', [])
            for imp in file_imports:
                # Check if imported symbol is used in the file
                imported_symbol = getattr(imp, 'imported_symbol', None)
                if imported_symbol:
                    # Check for symbol usage within the file
                    symbol_used = False
                    for symbol in getattr(file, 'symbols', []):
                        try:
                            dependencies = symbol.dependencies(UsageType.DIRECT)
                            if imported_symbol in dependencies:
                                symbol_used = True
                                break
                        except:
                            pass
                    
                    if not symbol_used:
                        import_analysis['unused_imports'].append({
                            'file': file.name,
                            'import': str(imp),
                            'imported_symbol': str(imported_symbol)
                        })
        except:
            continue
    
    # Analyze circular imports using networkx
    try:
        import_graph = nx.DiGraph()
        
        # Build import dependency graph
        for file in codebase.files:
            file_name = getattr(file, 'name', str(file))
            import_graph.add_node(file_name)
            
            for imp in getattr(file, 'imports', []):
                try:
                    imported_symbol = getattr(imp, 'imported_symbol', None)
                    if imported_symbol and hasattr(imported_symbol, 'file'):
                        imported_file = getattr(imported_symbol.file, 'name', str(imported_symbol.file))
                        if imported_file != file_name:
                            import_graph.add_edge(file_name, imported_file)
                except:
                    pass
        
        # Find strongly connected components (cycles)
        cycles = list(nx.strongly_connected_components(import_graph))
        circular_imports = [cycle for cycle in cycles if len(cycle) > 1]
        
        import_analysis['circular_imports'] = [
            {'files': list(cycle), 'cycle_length': len(cycle)} 
            for cycle in circular_imports
        ]
        
    except Exception:
        pass
    
    # Analyze unresolved imports
    for file in codebase.files:
        try:
            for imp in getattr(file, 'imports', []):
                # Check if import has resolution
                has_resolution = False
                if hasattr(imp, 'node_id'):
                    out_edges = codebase.ctx.out_edges(imp.node_id)
                    for edge in out_edges:
                        if edge[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION:
                            has_resolution = True
                            break
                
                if not has_resolution:
                    import_analysis['unresolved_imports'].append({
                        'file': file.name,
                        'import': str(imp)
                    })
        except:
            continue
    
    # Import statistics
    import_analysis['import_statistics'] = {
        'total_imports': len(list(codebase.imports)),
        'total_files': len(list(codebase.files)),
        'unused_count': len(import_analysis['unused_imports']),
        'circular_count': len(import_analysis['circular_imports']),
        'unresolved_count': len(import_analysis['unresolved_imports'])
    }
    
    return import_analysis


def analyze_call_sites(codebase: Codebase) -> Dict[str, List[Dict[str, Any]]]:
    """
    Analyze function call sites for potential issues.
    
    Returns:
        Dict with call site analysis results
    """
    call_site_issues = {
        'argument_mismatches': [],
        'undefined_calls': [],
        'call_statistics': {}
    }
    
    total_calls = 0
    resolved_calls = 0
    
    for func in codebase.functions:
        try:
            call_sites = getattr(func, 'call_sites', [])
            total_calls += len(call_sites)
            
            for call_site in call_sites:
                try:
                    # Check if call can be resolved to a function
                    if hasattr(call_site, 'resolved_symbol') and call_site.resolved_symbol:
                        resolved_calls += 1
                        target_func = call_site.resolved_symbol
                        
                        # Compare arguments with parameters
                        if isinstance(target_func, Function):
                            call_args = getattr(call_site, 'arguments', [])
                            func_params = getattr(target_func, 'parameters', [])
                            
                            # Simple argument count check
                            if len(call_args) != len(func_params):
                                call_site_issues['argument_mismatches'].append({
                                    'caller': func.name,
                                    'called_function': target_func.name,
                                    'expected_args': len(func_params),
                                    'provided_args': len(call_args),
                                    'call_location': getattr(call_site, 'location', 'unknown')
                                })
                    else:
                        call_site_issues['undefined_calls'].append({
                            'caller': func.name,
                            'call_name': getattr(call_site, 'name', str(call_site)),
                            'call_location': getattr(call_site, 'location', 'unknown')
                        })
                except:
                    continue
        except:
            continue
    
    call_site_issues['call_statistics'] = {
        'total_calls': total_calls,
        'resolved_calls': resolved_calls,
        'unresolved_calls': total_calls - resolved_calls,
        'resolution_rate': resolved_calls / total_calls if total_calls > 0 else 0
    }
    
    return call_site_issues


def comprehensive_analysis(codebase: Codebase) -> Dict[str, Any]:
    """
    Perform comprehensive codebase analysis combining all analysis types.
    
    Returns:
        Complete analysis results
    """
    print("🔍 Starting comprehensive codebase analysis...")
    
    results = {
        'codebase_summary': {},
        'entry_points': {},
        'dead_code': {},
        'unused_parameters': {},
        'import_analysis': {},
        'call_site_analysis': {},
        'symbol_statistics': {},
        'recommendations': []
    }
    
    # Basic codebase summary
    print("📊 Analyzing codebase structure...")
    results['codebase_summary'] = {
        'total_files': len(list(codebase.files)),
        'total_functions': len(list(codebase.functions)),
        'total_classes': len(list(codebase.classes)),
        'total_symbols': len(list(codebase.symbols)),
        'total_imports': len(list(codebase.imports)),
        'total_external_modules': len(list(codebase.external_modules))
    }
    
    # Entry point analysis
    print("🚪 Identifying entry points...")
    results['entry_points'] = identify_entry_points(codebase)
    
    # Dead code detection
    print("💀 Detecting dead code...")
    results['dead_code'] = detect_dead_code(codebase)
    
    # Unused parameter detection
    print("🔧 Analyzing function parameters...")
    results['unused_parameters'] = detect_unused_parameters(codebase)
    
    # Import analysis
    print("📦 Analyzing imports...")
    results['import_analysis'] = analyze_imports(codebase)
    
    # Call site analysis
    print("📞 Analyzing function calls...")
    results['call_site_analysis'] = analyze_call_sites(codebase)
    
    # Symbol statistics
    print("🏷️ Generating symbol statistics...")
    symbol_usage_stats = {}
    for symbol in codebase.symbols:
        try:
            usages = symbol.symbol_usages
            symbol_usage_stats[symbol.name] = {
                'usage_count': len(usages),
                'symbol_type': str(symbol.symbol_type),
                'file': getattr(symbol.file, 'name', 'unknown') if hasattr(symbol, 'file') else 'unknown'
            }
        except:
            pass
    
    results['symbol_statistics'] = symbol_usage_stats
    
    # Generate recommendations
    print("💡 Generating recommendations...")
    recommendations = []
    
    # Dead code recommendations
    dead_functions = len(results['dead_code']['dead_functions'])
    dead_classes = len(results['dead_code']['dead_classes'])
    if dead_functions > 0 or dead_classes > 0:
        recommendations.append(f"Consider removing {dead_functions} dead functions and {dead_classes} dead classes")
    
    # Import recommendations
    unused_imports = len(results['import_analysis']['unused_imports'])
    if unused_imports > 0:
        recommendations.append(f"Remove {unused_imports} unused imports to clean up dependencies")
    
    circular_imports = len(results['import_analysis']['circular_imports'])
    if circular_imports > 0:
        recommendations.append(f"Resolve {circular_imports} circular import cycles to improve architecture")
    
    # Parameter recommendations
    functions_with_unused_params = len(results['unused_parameters'])
    if functions_with_unused_params > 0:
        recommendations.append(f"Review {functions_with_unused_params} functions with unused parameters")
    
    results['recommendations'] = recommendations
    
    print("✅ Comprehensive analysis complete!")
    return results


def print_analysis_report(analysis_results: Dict[str, Any]) -> None:
    """
    Print a formatted analysis report.
    """
    print("\n" + "="*80)
    print("🔍 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
    print("="*80)
    
    # Codebase Summary
    summary = analysis_results['codebase_summary']
    print(f"\n📊 CODEBASE OVERVIEW:")
    print(f"   Files: {summary['total_files']}")
    print(f"   Functions: {summary['total_functions']}")
    print(f"   Classes: {summary['total_classes']}")
    print(f"   Symbols: {summary['total_symbols']}")
    print(f"   Imports: {summary['total_imports']}")
    print(f"   External Modules: {summary['total_external_modules']}")
    
    # Entry Points
    entry_points = analysis_results['entry_points']
    print(f"\n🚪 ENTRY POINTS:")
    for category, symbols in entry_points.items():
        if symbols:
            print(f"   {category.replace('_', ' ').title()}: {len(symbols)}")
            for symbol in symbols[:3]:  # Show first 3
                print(f"     - {symbol.name}")
            if len(symbols) > 3:
                print(f"     ... and {len(symbols) - 3} more")
    
    # Dead Code
    dead_code = analysis_results['dead_code']
    print(f"\n💀 DEAD CODE ANALYSIS:")
    for category, symbols in dead_code.items():
        if symbols:
            print(f"   {category.replace('_', ' ').title()}: {len(symbols)}")
            for symbol in symbols[:3]:  # Show first 3
                print(f"     - {symbol.name}")
            if len(symbols) > 3:
                print(f"     ... and {len(symbols) - 3} more")
    
    # Import Analysis
    import_analysis = analysis_results['import_analysis']
    print(f"\n📦 IMPORT ANALYSIS:")
    stats = import_analysis['import_statistics']
    print(f"   Total Imports: {stats['total_imports']}")
    print(f"   Unused Imports: {stats['unused_count']}")
    print(f"   Circular Import Cycles: {stats['circular_count']}")
    print(f"   Unresolved Imports: {stats['unresolved_count']}")
    
    # Call Site Analysis
    call_analysis = analysis_results['call_site_analysis']
    print(f"\n📞 CALL SITE ANALYSIS:")
    call_stats = call_analysis['call_statistics']
    print(f"   Total Function Calls: {call_stats['total_calls']}")
    print(f"   Resolved Calls: {call_stats['resolved_calls']}")
    print(f"   Resolution Rate: {call_stats['resolution_rate']:.1%}")
    print(f"   Argument Mismatches: {len(call_analysis['argument_mismatches'])}")
    
    # Recommendations
    recommendations = analysis_results['recommendations']
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print("\n" + "="*80)
