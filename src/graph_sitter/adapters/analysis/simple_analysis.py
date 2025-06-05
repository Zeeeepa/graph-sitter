"""
Simple Analysis - Using Graph-Sitter's Built-in Capabilities

This implements the actual patterns from graph-sitter.com documentation,
replacing all the complex custom analyzers with simple property access.

Key insight: Graph-sitter pre-computes all relationships, so analysis is
instant property access, not computation.
"""

from typing import Dict, List, Any, Optional, Set
from collections import Counter, defaultdict
import networkx as nx

from graph_sitter.core.codebase import Codebase


def analyze_codebase(repo_path: str) -> Dict[str, Any]:
    """
    Comprehensive codebase analysis using graph-sitter's built-in capabilities.
    
    This is the main analysis function that replaces all complex analyzers
    with simple property access patterns from graph-sitter.com.
    """
    codebase = Codebase(repo_path)
    
    # Basic stats using instant property access
    stats = get_codebase_stats(codebase)
    
    # Issues using simple property checks
    issues = []
    
    # Dead code detection (exact pattern from graph-sitter.com)
    dead_functions = get_dead_code(codebase)
    for func_name in dead_functions:
        issues.append({
            'type': 'dead_code',
            'severity': 'high',
            'description': f"Function '{func_name}' is never used",
            'category': 'unused_code'
        })
    
    # Missing docstrings
    for function in codebase.functions:
        if not function.docstring and not function.name.startswith('_'):
            issues.append({
                'type': 'missing_docstring',
                'severity': 'low', 
                'description': f"Function '{function.name}' missing docstring",
                'category': 'documentation'
            })
    
    # Complex functions (using pre-computed call graph)
    for function in codebase.functions:
        call_count = len(function.function_calls)
        if call_count > 10:
            issues.append({
                'type': 'high_complexity',
                'severity': 'medium',
                'description': f"Function '{function.name}' has high complexity ({call_count} calls)",
                'category': 'complexity'
            })
    
    # Deep inheritance (using pre-computed inheritance)
    for cls in codebase.classes:
        if len(cls.superclasses) > 3:
            issues.append({
                'type': 'deep_inheritance',
                'severity': 'medium',
                'description': f"Class '{cls.name}' has deep inheritance ({len(cls.superclasses)} levels)",
                'category': 'design'
            })
    
    return {
        'stats': stats,
        'issues': issues,
        'summary': {
            'total_issues': len(issues),
            'by_severity': Counter(issue['severity'] for issue in issues),
            'by_category': Counter(issue['category'] for issue in issues)
        }
    }


def get_codebase_stats(codebase: Codebase) -> Dict[str, Any]:
    """Get basic codebase statistics using graph-sitter's instant lookups."""
    
    # All of these are instant property access - no computation needed!
    total_lines = sum(
        len(file.source.split('\n')) 
        for file in codebase.files 
        if hasattr(file, 'source') and file.source
    )
    
    return {
        'total_files': len(codebase.files),
        'total_functions': len(codebase.functions),
        'total_classes': len(codebase.classes),
        'total_imports': len(codebase.imports),
        'total_lines': total_lines,
        'functions_with_docstrings': len([f for f in codebase.functions if f.docstring]),
        'classes_with_docstrings': len([c for c in codebase.classes if c.docstring]),
        'test_functions': len([f for f in codebase.functions if f.name.startswith('test_')]),
        'private_functions': len([f for f in codebase.functions if f.name.startswith('_')])
    }


def get_dead_code(codebase_or_path) -> List[str]:
    """
    Get dead code using graph-sitter's simple pattern.
    
    This is the exact pattern from graph-sitter.com documentation:
    "for function in codebase.functions:
        if not function.usages:
            # This function is dead code"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Exact pattern from graph-sitter.com
    return [f.name for f in codebase.functions if not f.usages]


def remove_dead_code(codebase_or_path) -> int:
    """
    Remove dead code using graph-sitter's built-in removal.
    
    This is the exact pattern from graph-sitter.com documentation:
    "for function in codebase.functions:
        if not function.usages:
            function.remove()"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    removed_count = 0
    
    # Exact pattern from graph-sitter.com
    for function in codebase.functions:
        if not function.usages:
            function.remove()
            removed_count += 1
    
    codebase.commit()
    return removed_count


def get_call_graph(codebase_or_path) -> Dict[str, List[str]]:
    """
    Get call graph using graph-sitter's pre-computed function calls.
    
    Uses the pattern from graph-sitter.com:
    "for call in function.function_calls:
        print(f'Calls: {call.function_definition.name}')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    call_graph = {}
    
    for function in codebase.functions:
        calls = []
        # Use graph-sitter's pre-computed function calls
        for call in function.function_calls:
            if hasattr(call, 'function_definition') and call.function_definition:
                calls.append(call.function_definition.name)
        call_graph[function.name] = calls
    
    return call_graph


def get_inheritance_hierarchy(codebase_or_path) -> Dict[str, List[str]]:
    """
    Get inheritance hierarchy using graph-sitter's pre-computed inheritance.
    
    Uses the pattern from graph-sitter.com:
    "for cls in codebase.classes:
        print(f'Superclasses: {cls.superclasses}')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    hierarchy = {}
    
    for cls in codebase.classes:
        # Use graph-sitter's pre-computed superclasses
        superclass_names = [sc.name for sc in cls.superclasses]
        hierarchy[cls.name] = superclass_names
    
    return hierarchy


def get_dependencies(codebase_or_path, symbol_name: str) -> List[str]:
    """
    Get dependencies using graph-sitter's pre-computed dependencies.
    
    Uses the pattern from graph-sitter.com:
    "function = codebase.get_symbol('process_data')
     print(f'Dependencies: {function.dependencies}')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    symbol = codebase.get_symbol(symbol_name)
    if symbol and hasattr(symbol, 'dependencies'):
        return [dep.name for dep in symbol.dependencies]
    return []


def get_usages(codebase_or_path, symbol_name: str) -> List[str]:
    """
    Get usages using graph-sitter's pre-computed usages.
    
    Uses the pattern from graph-sitter.com:
    "function = codebase.get_symbol('process_data')
     print(f'Usages: {function.usages}')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    symbol = codebase.get_symbol(symbol_name)
    if symbol and hasattr(symbol, 'usages'):
        return [usage.name for usage in symbol.usages]
    return []


def find_recursive_functions(codebase_or_path) -> List[str]:
    """
    Find recursive functions using graph-sitter's pre-computed call graph.
    
    Uses the pattern from graph-sitter.com getting started guide:
    "recursive = [f for f in codebase.functions 
                 if any(call.name == f.name for call in f.function_calls)]"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Exact pattern from graph-sitter.com getting started guide
    recursive = [
        f.name for f in codebase.functions 
        if any(call.name == f.name for call in f.function_calls)
    ]
    
    return recursive


def analyze_test_coverage(codebase_or_path) -> Dict[str, Any]:
    """
    Analyze test coverage using graph-sitter's built-in properties.
    
    Based on the test analysis example from graph-sitter.com getting started guide.
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Pattern from graph-sitter.com getting started guide
    test_functions = [f for f in codebase.functions if f.name.startswith('test_')]
    test_classes = [c for c in codebase.classes if c.name.startswith('Test')]
    
    # Find files with the most tests (from getting started guide)
    file_test_counts = Counter([f.file for f in test_functions])
    
    return {
        'total_test_functions': len(test_functions),
        'total_test_classes': len(test_classes),
        'tests_per_file': len(test_functions) / len(codebase.files) if codebase.files else 0,
        'files_with_most_tests': [
            {'file': file.filepath, 'test_count': count}
            for file, count in file_test_counts.most_common(5)
        ]
    }


def get_blast_radius(codebase_or_path, symbol_name: str) -> Dict[str, Any]:
    """
    Get blast radius analysis for a symbol using graph-sitter's pre-computed relationships.
    
    This shows what would be affected if the symbol changes.
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    symbol = codebase.get_symbol(symbol_name)
    if not symbol:
        return {'error': f"Symbol '{symbol_name}' not found"}
    
    # Use graph-sitter's pre-computed relationships
    direct_usages = get_usages(codebase, symbol_name)
    dependencies = get_dependencies(codebase, symbol_name)
    
    # Find transitive dependencies
    affected_symbols = set(direct_usages)
    for usage in direct_usages:
        affected_symbols.update(get_usages(codebase, usage))
    
    return {
        'symbol': symbol_name,
        'direct_usages': direct_usages,
        'dependencies': dependencies,
        'total_affected': len(affected_symbols),
        'affected_symbols': list(affected_symbols)
    }

