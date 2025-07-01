"""
🔢 Complexity Analysis

Consolidated complexity metrics from all existing analysis tools.
"""

import ast
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ComplexityMetrics:
    """Complexity metrics results"""
    total_complexity: int = 0
    average_complexity: float = 0.0
    max_complexity: int = 0
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    high_complexity_functions: List[str] = field(default_factory=list)
    complexity_by_file: Dict[str, float] = field(default_factory=dict)


class ComplexityAnalyzer:
    """Analyzer for code complexity metrics"""
    
    def __init__(self, complexity_threshold: int = 10):
        self.complexity_threshold = complexity_threshold
    
    def analyze_codebase(self, codebase) -> ComplexityMetrics:
        """Analyze complexity for entire codebase"""
        metrics = ComplexityMetrics()
        
        try:
            if hasattr(codebase, 'files'):
                for file in codebase.files:
                    if hasattr(file, 'source'):
                        file_complexity = self.analyze_file_source(file.source)
                        metrics.complexity_by_file[file.filepath] = file_complexity['average_complexity']
                        metrics.total_complexity += file_complexity['total_complexity']
                        
                        if file_complexity['max_complexity'] > metrics.max_complexity:
                            metrics.max_complexity = file_complexity['max_complexity']
                        
                        # Add high complexity functions
                        for func_name in file_complexity['high_complexity_functions']:
                            metrics.high_complexity_functions.append(f"{file.filepath}:{func_name}")
            
            # Calculate overall average
            if metrics.complexity_by_file:
                metrics.average_complexity = sum(metrics.complexity_by_file.values()) / len(metrics.complexity_by_file)
            
            # Calculate distribution
            metrics.complexity_distribution = self._calculate_distribution(metrics.complexity_by_file)
            
        except Exception as e:
            # Handle errors gracefully
            pass
        
        return metrics
    
    def analyze_file_source(self, source_code: str) -> Dict[str, Any]:
        """Analyze complexity for source code"""
        try:
            tree = ast.parse(source_code)
            return self.analyze_ast(tree)
        except:
            return {
                'total_complexity': 0,
                'average_complexity': 0.0,
                'max_complexity': 0,
                'high_complexity_functions': []
            }
    
    def analyze_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze complexity from AST"""
        function_complexities = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                function_complexities[node.name] = complexity
        
        if not function_complexities:
            return {
                'total_complexity': 0,
                'average_complexity': 0.0,
                'max_complexity': 0,
                'high_complexity_functions': []
            }
        
        total_complexity = sum(function_complexities.values())
        average_complexity = total_complexity / len(function_complexities)
        max_complexity = max(function_complexities.values())
        
        high_complexity_functions = [
            name for name, complexity in function_complexities.items()
            if complexity > self.complexity_threshold
        ]
        
        return {
            'total_complexity': total_complexity,
            'average_complexity': average_complexity,
            'max_complexity': max_complexity,
            'high_complexity_functions': high_complexity_functions,
            'function_complexities': function_complexities
        }
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            # Decision points that increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
            elif isinstance(node, ast.Lambda):
                complexity += 1
        
        return complexity
    
    def _calculate_distribution(self, complexity_by_file: Dict[str, float]) -> Dict[str, int]:
        """Calculate complexity distribution"""
        distribution = {
            'low': 0,      # 1-5
            'medium': 0,   # 6-10
            'high': 0,     # 11-20
            'very_high': 0 # 21+
        }
        
        for complexity in complexity_by_file.values():
            if complexity <= 5:
                distribution['low'] += 1
            elif complexity <= 10:
                distribution['medium'] += 1
            elif complexity <= 20:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1
        
        return distribution


def calculate_complexity_metrics(source_code: str, threshold: int = 10) -> Dict[str, Any]:
    """Calculate complexity metrics for source code"""
    analyzer = ComplexityAnalyzer(threshold)
    return analyzer.analyze_file_source(source_code)

