"""
📈 Code Quality Metrics

Consolidated quality metrics from all existing analysis tools.
"""

import ast
import math
import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class QualityMetrics:
    """Quality metrics for code analysis"""
    maintainability_index: float = 0.0
    cyclomatic_complexity: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_volume: float = 0.0
    halstead_bugs: float = 0.0
    comment_ratio: float = 0.0
    documentation_coverage: float = 0.0
    test_coverage_estimate: float = 0.0
    technical_debt_ratio: float = 0.0
    quality_score: float = 0.0
    
    def calculate_file_metrics(self, source_code: str, file_path: str) -> 'QualityMetrics':
        """Calculate quality metrics for a file"""
        try:
            tree = ast.parse(source_code)
            
            # Calculate various metrics
            self.cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
            self.comment_ratio = self._calculate_comment_ratio(source_code)
            self.documentation_coverage = self._calculate_documentation_coverage(tree)
            
            # Calculate Halstead metrics
            halstead = self._calculate_halstead_metrics(tree)
            self.halstead_difficulty = halstead['difficulty']
            self.halstead_effort = halstead['effort']
            self.halstead_volume = halstead['volume']
            self.halstead_bugs = halstead['bugs']
            
            # Calculate maintainability index
            self.maintainability_index = self._calculate_maintainability_index()
            
            # Calculate overall quality score
            self.quality_score = self._calculate_quality_score()
            
        except Exception as e:
            # Handle parsing errors gracefully
            self.quality_score = 0.0
        
        return self
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return float(complexity)
    
    def _calculate_comment_ratio(self, source_code: str) -> float:
        """Calculate ratio of comment lines to total lines"""
        lines = source_code.splitlines()
        if not lines:
            return 0.0
        
        comment_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                comment_lines += 1
        
        return comment_lines / len(lines)
    
    def _calculate_documentation_coverage(self, tree: ast.AST) -> float:
        """Calculate documentation coverage"""
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        total_items = len(functions) + len(classes)
        if total_items == 0:
            return 1.0
        
        documented_items = 0
        
        for func in functions:
            if ast.get_docstring(func):
                documented_items += 1
        
        for cls in classes:
            if ast.get_docstring(cls):
                documented_items += 1
        
        return documented_items / total_items
    
    def _calculate_halstead_metrics(self, tree: ast.AST) -> Dict[str, float]:
        """Calculate Halstead complexity metrics"""
        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                operators.add(type(node.op).__name__)
                operator_count += 1
            elif isinstance(node, ast.UnaryOp):
                operators.add(type(node.op).__name__)
                operator_count += 1
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    operators.add(type(op).__name__)
                    operator_count += 1
            elif isinstance(node, ast.Name):
                operands.add(node.id)
                operand_count += 1
            elif isinstance(node, ast.Constant):
                operands.add(str(node.value))
                operand_count += 1
        
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)   # Number of distinct operands
        N1 = operator_count  # Total number of operators
        N2 = operand_count   # Total number of operands
        
        if n1 == 0 or n2 == 0:
            return {'difficulty': 0, 'effort': 0, 'volume': 0, 'bugs': 0}
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if vocabulary <= 0:
            return {'difficulty': 0, 'effort': 0, 'volume': 0, 'bugs': 0}
        
        volume = length * math.log2(vocabulary)
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        bugs = volume / 3000  # Estimated bugs
        
        return {
            'difficulty': difficulty,
            'effort': effort,
            'volume': volume,
            'bugs': bugs
        }
    
    def _calculate_maintainability_index(self) -> float:
        """Calculate maintainability index"""
        # Simplified maintainability index calculation
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        
        if self.halstead_volume <= 0:
            halstead_component = 0
        else:
            halstead_component = 5.2 * math.log(self.halstead_volume)
        
        complexity_component = 0.23 * self.cyclomatic_complexity
        
        # Estimate lines of code (simplified)
        loc_component = 16.2 * math.log(max(1, self.cyclomatic_complexity * 10))
        
        mi = 171 - halstead_component - complexity_component - loc_component
        
        # Normalize to 0-100 scale
        return max(0, min(100, mi))
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-10)"""
        # Weighted combination of various metrics
        weights = {
            'maintainability': 0.3,
            'complexity': 0.2,
            'documentation': 0.2,
            'comments': 0.1,
            'halstead': 0.2
        }
        
        # Normalize maintainability index (0-100) to 0-10
        maintainability_score = self.maintainability_index / 10
        
        # Complexity score (lower is better)
        complexity_score = max(0, 10 - (self.cyclomatic_complexity / 5))
        
        # Documentation score
        documentation_score = self.documentation_coverage * 10
        
        # Comment score
        comment_score = min(10, self.comment_ratio * 50)  # Cap at reasonable level
        
        # Halstead score (lower difficulty is better)
        halstead_score = max(0, 10 - (self.halstead_difficulty / 10))
        
        # Calculate weighted average
        quality_score = (
            weights['maintainability'] * maintainability_score +
            weights['complexity'] * complexity_score +
            weights['documentation'] * documentation_score +
            weights['comments'] * comment_score +
            weights['halstead'] * halstead_score
        )
        
        return round(quality_score, 2)


def calculate_quality_metrics(source_code: str, file_path: str = "") -> QualityMetrics:
    """Calculate quality metrics for source code"""
    metrics = QualityMetrics()
    return metrics.calculate_file_metrics(source_code, file_path)

