"""
📊 Advanced Metrics and Quality Analysis

Comprehensive code quality metrics including:
- Cyclomatic complexity analysis
- Halstead metrics for program difficulty and effort
- Maintainability index calculation
- Code quality indicators and technical debt assessment
- Performance and scalability metrics

Based on industry-standard software metrics and quality assessment techniques.
"""

import ast
import math
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from pathlib import Path


@dataclass
class QualityMetrics:
    """Container for code quality metrics"""
    cyclomatic_complexity: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_volume: float = 0.0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    comment_ratio: float = 0.0
    duplication_ratio: float = 0.0
    test_coverage_estimate: float = 0.0
    technical_debt_ratio: float = 0.0
    complexity_density: float = 0.0


@dataclass
class HalsteadMetrics:
    """Halstead complexity metrics"""
    distinct_operators: int = 0
    distinct_operands: int = 0
    total_operators: int = 0
    total_operands: int = 0
    vocabulary: int = 0
    length: int = 0
    volume: float = 0.0
    difficulty: float = 0.0
    effort: float = 0.0
    time_to_implement: float = 0.0
    bugs_estimate: float = 0.0


@dataclass
class ComplexityMetrics:
    """Complexity analysis metrics"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    function_length: int = 0
    parameter_count: int = 0
    return_points: int = 0


class MetricsCalculator:
    """
    Advanced metrics calculator for code quality assessment
    """
    
    def __init__(self):
        self.operators = {
            # Arithmetic operators
            '+', '-', '*', '/', '//', '%', '**',
            # Comparison operators
            '==', '!=', '<', '>', '<=', '>=', 'is', 'is not', 'in', 'not in',
            # Logical operators
            'and', 'or', 'not',
            # Bitwise operators
            '&', '|', '^', '~', '<<', '>>',
            # Assignment operators
            '=', '+=', '-=', '*=', '/=', '//=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=',
            # Control flow
            'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with',
            'break', 'continue', 'return', 'yield', 'raise', 'assert',
            # Function/class definition
            'def', 'class', 'lambda',
            # Import statements
            'import', 'from', 'as',
            # Other keywords
            'del', 'global', 'nonlocal', 'pass'
        }
    
    def calculate_quality_metrics(self, source_code: str, file_path: str = "") -> QualityMetrics:
        """Calculate comprehensive quality metrics for source code"""
        try:
            tree = ast.parse(source_code)
            
            # Calculate individual metrics
            cyclomatic = self.calculate_cyclomatic_complexity(tree)
            halstead = self.calculate_halstead_metrics(source_code)
            maintainability = self.calculate_maintainability_index(
                cyclomatic, halstead.volume, len(source_code.splitlines())
            )
            
            lines_of_code = len([line for line in source_code.splitlines() if line.strip()])
            comment_ratio = self._calculate_comment_ratio(source_code)
            complexity_density = cyclomatic / max(lines_of_code, 1)
            
            return QualityMetrics(
                cyclomatic_complexity=cyclomatic,
                halstead_difficulty=halstead.difficulty,
                halstead_effort=halstead.effort,
                halstead_volume=halstead.volume,
                maintainability_index=maintainability,
                lines_of_code=lines_of_code,
                comment_ratio=comment_ratio,
                complexity_density=complexity_density,
                technical_debt_ratio=self._estimate_technical_debt(cyclomatic, maintainability)
            )
            
        except Exception as e:
            print(f"Error calculating quality metrics: {e}")
            return QualityMetrics()
    
    def calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points that increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
            elif isinstance(node, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'name'):  # Skip lambda for base count
                    complexity += 0  # Functions don't add to base complexity
        
        return complexity
    
    def calculate_halstead_metrics(self, source_code: str) -> HalsteadMetrics:
        """Calculate Halstead complexity metrics"""
        try:
            tree = ast.parse(source_code)
            
            operators = Counter()
            operands = Counter()
            
            for node in ast.walk(tree):
                self._extract_operators_operands(node, operators, operands)
            
            # Calculate Halstead metrics
            n1 = len(operators)  # Distinct operators
            n2 = len(operands)   # Distinct operands
            N1 = sum(operators.values())  # Total operators
            N2 = sum(operands.values())   # Total operands
            
            vocabulary = n1 + n2
            length = N1 + N2
            volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
            time_to_implement = effort / 18  # Seconds (Halstead's constant)
            bugs_estimate = volume / 3000    # Estimated bugs
            
            return HalsteadMetrics(
                distinct_operators=n1,
                distinct_operands=n2,
                total_operators=N1,
                total_operands=N2,
                vocabulary=vocabulary,
                length=length,
                volume=volume,
                difficulty=difficulty,
                effort=effort,
                time_to_implement=time_to_implement,
                bugs_estimate=bugs_estimate
            )
            
        except Exception as e:
            print(f"Error calculating Halstead metrics: {e}")
            return HalsteadMetrics()
    
    def calculate_maintainability_index(self, cyclomatic_complexity: float, 
                                      halstead_volume: float, lines_of_code: int) -> float:
        """Calculate maintainability index"""
        try:
            # Microsoft's maintainability index formula
            if lines_of_code == 0:
                return 100.0
            
            mi = (171 - 5.2 * math.log(halstead_volume) - 
                  0.23 * cyclomatic_complexity - 
                  16.2 * math.log(lines_of_code))
            
            # Normalize to 0-100 scale
            return max(0, min(100, mi))
            
        except Exception as e:
            print(f"Error calculating maintainability index: {e}")
            return 0.0
    
    def calculate_function_complexity(self, function_node: ast.FunctionDef) -> ComplexityMetrics:
        """Calculate complexity metrics for a specific function"""
        try:
            cyclomatic = self.calculate_cyclomatic_complexity(function_node)
            cognitive = self._calculate_cognitive_complexity(function_node)
            nesting_depth = self._calculate_nesting_depth(function_node)
            function_length = len(function_node.body)
            parameter_count = len(function_node.args.args)
            return_points = self._count_return_points(function_node)
            
            return ComplexityMetrics(
                cyclomatic_complexity=cyclomatic,
                cognitive_complexity=cognitive,
                nesting_depth=nesting_depth,
                function_length=function_length,
                parameter_count=parameter_count,
                return_points=return_points
            )
            
        except Exception as e:
            print(f"Error calculating function complexity: {e}")
            return ComplexityMetrics()
    
    def _extract_operators_operands(self, node: ast.AST, operators: Counter, operands: Counter):
        """Extract operators and operands from AST node"""
        # Operators
        if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
            operators[type(node).__name__] += 1
        elif isinstance(node, (ast.And, ast.Or, ast.Not)):
            operators[type(node).__name__] += 1
        elif isinstance(node, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
            operators[type(node).__name__] += 1
        elif isinstance(node, (ast.Is, ast.IsNot, ast.In, ast.NotIn)):
            operators[type(node).__name__] += 1
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            operators[type(node).__name__] += 1
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            operators[type(node).__name__] += 1
        
        # Operands
        elif isinstance(node, ast.Name):
            operands[node.id] += 1
        elif isinstance(node, ast.Constant):
            operands[str(node.value)] += 1
        elif isinstance(node, ast.Attribute):
            operands[node.attr] += 1
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity (more human-oriented than cyclomatic)"""
        complexity = 0
        nesting_level = 0
        
        def visit_node(n, level):
            nonlocal complexity
            
            # Increment for control structures
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + level
            elif isinstance(n, ast.ExceptHandler):
                complexity += 1 + level
            elif isinstance(n, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(n, ast.comprehension):
                complexity += 1
            
            # Increase nesting level for certain structures
            new_level = level
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With)):
                new_level += 1
            
            for child in ast.iter_child_nodes(n):
                visit_node(child, new_level)
        
        visit_node(node, 0)
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        
        def visit_node(n, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            new_depth = depth
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With)):
                new_depth += 1
            
            for child in ast.iter_child_nodes(n):
                visit_node(child, new_depth)
        
        visit_node(node, 0)
        return max_depth
    
    def _count_return_points(self, node: ast.AST) -> int:
        """Count number of return points in function"""
        return len([n for n in ast.walk(node) if isinstance(n, ast.Return)])
    
    def _calculate_comment_ratio(self, source_code: str) -> float:
        """Calculate ratio of comment lines to total lines"""
        lines = source_code.splitlines()
        comment_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                comment_lines += 1
        
        total_lines = len([line for line in lines if line.strip()])
        return comment_lines / max(total_lines, 1)
    
    def _estimate_technical_debt(self, cyclomatic_complexity: float, maintainability_index: float) -> float:
        """Estimate technical debt ratio based on complexity and maintainability"""
        # Simple heuristic: higher complexity and lower maintainability = more debt
        complexity_factor = min(cyclomatic_complexity / 10, 1.0)  # Normalize to 0-1
        maintainability_factor = (100 - maintainability_index) / 100  # Invert and normalize
        
        return (complexity_factor + maintainability_factor) / 2


class ComplexityAnalyzer:
    """
    Specialized analyzer for complexity metrics
    """
    
    def __init__(self):
        self.calculator = MetricsCalculator()
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze complexity metrics for a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Overall file metrics
            file_metrics = self.calculator.calculate_quality_metrics(source_code, file_path)
            
            # Function-level metrics
            function_metrics = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_metrics = self.calculator.calculate_function_complexity(node)
                    function_metrics[node.name] = func_metrics
            
            # Class-level metrics
            class_metrics = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_complexity = 0
                    method_count = 0
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_count += 1
                            class_complexity += self.calculator.calculate_cyclomatic_complexity(child)
                    
                    class_metrics[node.name] = {
                        'total_complexity': class_complexity,
                        'method_count': method_count,
                        'average_complexity': class_complexity / max(method_count, 1)
                    }
            
            return {
                'file_path': file_path,
                'file_metrics': file_metrics,
                'function_metrics': function_metrics,
                'class_metrics': class_metrics,
                'summary': {
                    'total_functions': len(function_metrics),
                    'total_classes': len(class_metrics),
                    'average_function_complexity': sum(
                        m.cyclomatic_complexity for m in function_metrics.values()
                    ) / max(len(function_metrics), 1),
                    'highest_complexity_function': max(
                        function_metrics.items(),
                        key=lambda x: x[1].cyclomatic_complexity,
                        default=('none', ComplexityMetrics())
                    )[0]
                }
            }
            
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return {'file_path': file_path, 'error': str(e)}
    
    def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """Analyze complexity metrics for all Python files in a directory"""
        results = {}
        directory = Path(directory_path)
        
        for py_file in directory.rglob('*.py'):
            try:
                file_results = self.analyze_file(str(py_file))
                results[str(py_file)] = file_results
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
                results[str(py_file)] = {'error': str(e)}
        
        # Calculate directory-level summary
        total_complexity = 0
        total_functions = 0
        total_classes = 0
        
        for file_result in results.values():
            if 'error' not in file_result:
                if 'summary' in file_result:
                    total_functions += file_result['summary']['total_functions']
                    total_classes += file_result['summary']['total_classes']
                if 'function_metrics' in file_result:
                    total_complexity += sum(
                        m.cyclomatic_complexity for m in file_result['function_metrics'].values()
                    )
        
        results['_directory_summary'] = {
            'total_files': len([r for r in results.values() if 'error' not in r]),
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_complexity': total_complexity,
            'average_complexity_per_function': total_complexity / max(total_functions, 1)
        }
        
        return results


# Convenience functions for direct use

def calculate_cyclomatic_complexity(source_code: str) -> int:
    """Calculate cyclomatic complexity for source code"""
    calculator = MetricsCalculator()
    try:
        tree = ast.parse(source_code)
        return calculator.calculate_cyclomatic_complexity(tree)
    except Exception as e:
        print(f"Error calculating cyclomatic complexity: {e}")
        return 0


def calculate_halstead_metrics(source_code: str) -> HalsteadMetrics:
    """Calculate Halstead metrics for source code"""
    calculator = MetricsCalculator()
    return calculator.calculate_halstead_metrics(source_code)


def calculate_maintainability_index(source_code: str) -> float:
    """Calculate maintainability index for source code"""
    calculator = MetricsCalculator()
    try:
        tree = ast.parse(source_code)
        cyclomatic = calculator.calculate_cyclomatic_complexity(tree)
        halstead = calculator.calculate_halstead_metrics(source_code)
        lines_of_code = len(source_code.splitlines())
        
        return calculator.calculate_maintainability_index(cyclomatic, halstead.volume, lines_of_code)
    except Exception as e:
        print(f"Error calculating maintainability index: {e}")
        return 0.0


class MaintainabilityIndex:
    """
    Specialized class for maintainability index calculation and interpretation
    """
    
    @staticmethod
    def calculate(cyclomatic_complexity: float, halstead_volume: float, lines_of_code: int) -> float:
        """Calculate maintainability index"""
        return calculate_maintainability_index(f"# {lines_of_code} lines of code")
    
    @staticmethod
    def interpret(mi_score: float) -> str:
        """Interpret maintainability index score"""
        if mi_score >= 85:
            return "Excellent maintainability"
        elif mi_score >= 70:
            return "Good maintainability"
        elif mi_score >= 50:
            return "Moderate maintainability"
        elif mi_score >= 25:
            return "Poor maintainability"
        else:
            return "Very poor maintainability"
    
    @staticmethod
    def get_recommendations(mi_score: float) -> List[str]:
        """Get recommendations based on maintainability index"""
        recommendations = []
        
        if mi_score < 50:
            recommendations.extend([
                "Consider refactoring complex functions",
                "Add comprehensive documentation",
                "Reduce cyclomatic complexity",
                "Break down large functions into smaller ones"
            ])
        
        if mi_score < 25:
            recommendations.extend([
                "Urgent refactoring needed",
                "Consider complete rewrite of problematic areas",
                "Implement comprehensive testing",
                "Review architectural decisions"
            ])
        
        return recommendations

