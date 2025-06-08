#!/usr/bin/env python3
"""
Complexity Analyzer

Analyzes code complexity using cyclomatic complexity, Halstead metrics, and maintainability index.
Uses the actual graph_sitter API for statement analysis.
"""

import math
import graph_sitter
from graph_sitter import Codebase
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.if_block_statement import IfBlockStatement
from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
from graph_sitter.core.statements.while_statement import WhileStatement


def calculate_cyclomatic_complexity(function):
    """Calculate cyclomatic complexity for a function."""
    complexity = 1  # Base complexity
    
    def analyze_statement(statement):
        complexity = 0
        
        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)
        
        elif isinstance(statement, (ForLoopStatement, WhileStatement)):
            complexity += 1
        
        elif isinstance(statement, TryCatchStatement):
            complexity += 1
            if hasattr(statement, "catch_blocks"):
                complexity += len(statement.catch_blocks)
        
        return complexity
    
    # Analyze all statements in the function
    if hasattr(function, 'code_block') and hasattr(function.code_block, 'statements'):
        for statement in function.code_block.statements:
            complexity += analyze_statement(statement)
    
    return complexity


def calculate_halstead_volume(operators, operands):
    """Calculate Halstead volume metrics."""
    n1 = len(set(operators))  # Unique operators
    n2 = len(set(operands))   # Unique operands
    
    N1 = len(operators)       # Total operators
    N2 = len(operands)        # Total operands
    
    N = N1 + N2              # Program length
    n = n1 + n2              # Program vocabulary
    
    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2


def extract_operators_operands(function):
    """Extract operators and operands from function source."""
    # Simple extraction - could be enhanced with proper AST parsing
    source = function.source
    
    # Common operators
    operators = []
    operands = []
    
    # This is a simplified version - in practice you'd use the AST
    operator_symbols = ['+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not']
    
    words = source.split()
    for word in words:
        if word in operator_symbols:
            operators.append(word)
        elif word.isidentifier():
            operands.append(word)
    
    return operators, operands


def calculate_maintainability_index(halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
    """Calculate the normalized maintainability index for a given function."""
    if loc <= 0:
        return 100
    
    try:
        raw_mi = (
            171
            - 5.2 * math.log(max(1, halstead_volume))
            - 0.23 * cyclomatic_complexity
            - 16.2 * math.log(max(1, loc))
        )
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0


def calculate_doi(cls):
    """Calculate Depth of Inheritance for a class."""
    return len(cls.superclasses)


@graph_sitter.function("analyze-complexity")
def analyze_complexity(codebase: Codebase):
    """Analyze complexity metrics for all functions and classes in the codebase."""
    results = {
        'functions': [],
        'classes': [],
        'summary': {
            'total_functions': 0,
            'avg_complexity': 0,
            'high_complexity_functions': 0,
            'avg_maintainability': 0
        }
    }
    
    total_complexity = 0
    total_maintainability = 0
    
    # Analyze functions
    for function in codebase.functions:
        # Skip test files
        if "test" in function.file.filepath:
            continue
        
        # Calculate metrics
        complexity = calculate_cyclomatic_complexity(function)
        operators, operands = extract_operators_operands(function)
        halstead_volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
        loc = len(function.source.split('\n'))
        maintainability = calculate_maintainability_index(halstead_volume, complexity, loc)
        
        function_result = {
            'name': function.name,
            'file': function.file.filepath,
            'line': function.start_point[0] if function.start_point else 0,
            'cyclomatic_complexity': complexity,
            'halstead_volume': halstead_volume,
            'lines_of_code': loc,
            'maintainability_index': maintainability,
            'halstead_metrics': {
                'total_operators': N1,
                'total_operands': N2,
                'unique_operators': n1,
                'unique_operands': n2
            }
        }
        
        results['functions'].append(function_result)
        total_complexity += complexity
        total_maintainability += maintainability
        
        if complexity > 10:  # High complexity threshold
            results['summary']['high_complexity_functions'] += 1
    
    # Analyze classes
    for cls in codebase.classes:
        if "test" in cls.file.filepath:
            continue
        
        doi = calculate_doi(cls)
        method_count = len(cls.methods) if hasattr(cls, 'methods') else 0
        
        class_result = {
            'name': cls.name,
            'file': cls.file.filepath,
            'line': cls.start_point[0] if cls.start_point else 0,
            'depth_of_inheritance': doi,
            'method_count': method_count,
            'superclasses': [parent.name for parent in cls.superclasses] if cls.superclasses else []
        }
        
        results['classes'].append(class_result)
    
    # Calculate summary statistics
    function_count = len(results['functions'])
    if function_count > 0:
        results['summary']['total_functions'] = function_count
        results['summary']['avg_complexity'] = total_complexity / function_count
        results['summary']['avg_maintainability'] = total_maintainability / function_count
    
    return results


def find_complex_functions(codebase: Codebase, complexity_threshold: int = 10):
    """Find functions with high cyclomatic complexity."""
    complex_functions = []
    
    for function in codebase.functions:
        if "test" in function.file.filepath:
            continue
        
        complexity = calculate_cyclomatic_complexity(function)
        if complexity > complexity_threshold:
            complex_functions.append({
                'name': function.name,
                'file': function.file.filepath,
                'complexity': complexity,
                'lines': len(function.source.split('\n'))
            })
    
    return sorted(complex_functions, key=lambda x: x['complexity'], reverse=True)


def find_large_functions(codebase: Codebase, line_threshold: int = 50):
    """Find functions that are too large."""
    large_functions = []
    
    for function in codebase.functions:
        if "test" in function.file.filepath:
            continue
        
        lines = len(function.source.split('\n'))
        if lines > line_threshold:
            large_functions.append({
                'name': function.name,
                'file': function.file.filepath,
                'lines': lines,
                'complexity': calculate_cyclomatic_complexity(function)
            })
    
    return sorted(large_functions, key=lambda x: x['lines'], reverse=True)


if __name__ == "__main__":
    # Example usage
    codebase = Codebase("./")
    
    print("🔍 Analyzing code complexity...")
    results = analyze_complexity(codebase)
    
    print(f"\n📊 Complexity Analysis Results:")
    print(f"Total functions analyzed: {results['summary']['total_functions']}")
    print(f"Average complexity: {results['summary']['avg_complexity']:.2f}")
    print(f"High complexity functions: {results['summary']['high_complexity_functions']}")
    print(f"Average maintainability: {results['summary']['avg_maintainability']:.1f}")
    
    # Show most complex functions
    complex_funcs = find_complex_functions(codebase)
    if complex_funcs:
        print(f"\n🚨 Most complex functions:")
        for func in complex_funcs[:5]:
            print(f"  • {func['name']} (complexity: {func['complexity']}, lines: {func['lines']})")
    
    # Show largest functions
    large_funcs = find_large_functions(codebase)
    if large_funcs:
        print(f"\n📏 Largest functions:")
        for func in large_funcs[:5]:
            print(f"  • {func['name']} ({func['lines']} lines, complexity: {func['complexity']})")

