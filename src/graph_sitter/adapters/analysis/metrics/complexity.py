"""
Complexity Metrics Analysis

Analyzes various complexity metrics including cyclomatic complexity, 
cognitive complexity, Halstead metrics, and maintainability index.
"""

import ast
import math
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Analyzes various complexity metrics for code."""
    
    def __init__(self):
        # Complexity thresholds
        self.complexity_thresholds = {
            'low': 5,
            'moderate': 10,
            'high': 20,
            'very_high': 50
        }
        
        # Halstead operators for Python
        self.operators = {
            '+', '-', '*', '/', '//', '%', '**',
            '=', '+=', '-=', '*=', '/=', '//=', '%=', '**=',
            '==', '!=', '<', '<=', '>', '>=',
            'and', 'or', 'not', 'is', 'in',
            'if', 'elif', 'else', 'for', 'while', 'break', 'continue',
            'def', 'class', 'return', 'yield', 'import', 'from',
            'try', 'except', 'finally', 'raise', 'assert',
            'with', 'as', 'lambda', 'global', 'nonlocal'
        }
    
    def analyze_codebase(self, codebase) -> Dict[str, Any]:
        """Analyze complexity metrics for entire codebase."""
        try:
            if hasattr(codebase, 'functions'):
                return self._analyze_graph_sitter_codebase(codebase)
            else:
                return self._analyze_ast_codebase(codebase)
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            return self._get_default_complexity_metrics()
    
    def _analyze_graph_sitter_codebase(self, codebase) -> Dict[str, Any]:
        """Analyze codebase using graph-sitter."""
        complexities = []
        halstead_metrics = []
        maintainability_scores = []
        
        function_details = []
        
        for function in codebase.functions:
            # Calculate cyclomatic complexity
            cyclomatic = self.calculate_cyclomatic_complexity(function)
            complexities.append(cyclomatic)
            
            # Calculate Halstead metrics
            halstead = self._calculate_halstead_metrics(function)
            halstead_metrics.append(halstead)
            
            # Calculate maintainability index
            maintainability = self._calculate_maintainability_index(function, cyclomatic, halstead)
            maintainability_scores.append(maintainability)
            
            function_details.append({
                'name': function.name,
                'file': function.filepath,
                'cyclomatic_complexity': cyclomatic,
                'halstead_volume': halstead.get('volume', 0),
                'maintainability_index': maintainability,
                'complexity_level': self._get_complexity_level(cyclomatic)
            })
        
        return self._compile_complexity_metrics(complexities, halstead_metrics, maintainability_scores, function_details)
    
    def _analyze_ast_codebase(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze codebase using AST data."""
        complexities = []
        function_details = []
        
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                complexity = func.get('complexity', 1)
                complexities.append(complexity)
                
                function_details.append({
                    'name': func.get('name', 'unknown'),
                    'file': filepath,
                    'cyclomatic_complexity': complexity,
                    'complexity_level': self._get_complexity_level(complexity)
                })
        
        # Generate basic metrics for AST mode
        halstead_metrics = [{'volume': 0} for _ in complexities]
        maintainability_scores = [50 for _ in complexities]  # Default score
        
        return self._compile_complexity_metrics(complexities, halstead_metrics, maintainability_scores, function_details)
    
    def calculate_cyclomatic_complexity(self, function) -> int:
        """Calculate cyclomatic complexity for a function."""
        try:
            if hasattr(function, 'source'):
                return self._calculate_cyclomatic_complexity_from_source(function.source)
            else:
                # Fallback: estimate from function calls and control structures
                return self._estimate_complexity_from_graph_sitter(function)
        except Exception as e:
            logger.warning(f"Failed to calculate complexity for {getattr(function, 'name', 'unknown')}: {e}")
            return 1
    
    def _calculate_cyclomatic_complexity_from_source(self, source: str) -> int:
        """Calculate cyclomatic complexity from source code."""
        try:
            tree = ast.parse(source)
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    # Each additional boolean operator adds complexity
                    complexity += len(node.values) - 1
                elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                    complexity += 1
            
            return complexity
        except SyntaxError:
            return 1
    
    def _estimate_complexity_from_graph_sitter(self, function) -> int:
        """Estimate complexity from graph-sitter function object."""
        complexity = 1
        
        # Count control flow statements if available
        if hasattr(function, 'statements'):
            for stmt in function.statements:
                if hasattr(stmt, 'statement_type'):
                    stmt_type = stmt.statement_type
                    if stmt_type in ['if', 'for', 'while', 'try', 'except']:
                        complexity += 1
        
        return complexity
    
    def _calculate_halstead_metrics(self, function) -> Dict[str, float]:
        """Calculate Halstead complexity metrics."""
        try:
            if not hasattr(function, 'source'):
                return {'volume': 0, 'difficulty': 0, 'effort': 0}
            
            source = function.source
            
            # Tokenize and count operators/operands
            operators = []
            operands = []
            
            try:
                tree = ast.parse(source)
                self._extract_halstead_elements(tree, operators, operands)
            except SyntaxError:
                return {'volume': 0, 'difficulty': 0, 'effort': 0}
            
            # Calculate Halstead metrics
            n1 = len(set(operators))  # Unique operators
            n2 = len(set(operands))   # Unique operands
            N1 = len(operators)       # Total operators
            N2 = len(operands)        # Total operands
            
            if n1 == 0 or n2 == 0:
                return {'volume': 0, 'difficulty': 0, 'effort': 0}
            
            vocabulary = n1 + n2
            length = N1 + N2
            
            volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
            
            return {
                'volume': volume,
                'difficulty': difficulty,
                'effort': effort,
                'vocabulary': vocabulary,
                'length': length
            }
        
        except Exception as e:
            logger.warning(f"Failed to calculate Halstead metrics: {e}")
            return {'volume': 0, 'difficulty': 0, 'effort': 0}
    
    def _extract_halstead_elements(self, node, operators: List[str], operands: List[str]):
        """Extract operators and operands from AST for Halstead metrics."""
        if isinstance(node, ast.BinOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.UnaryOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.Compare):
            operators.extend([type(op).__name__ for op in node.ops])
        elif isinstance(node, ast.BoolOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, (ast.If, ast.For, ast.While)):
            operators.append(type(node).__name__)
        elif isinstance(node, ast.Name):
            operands.append(node.id)
        elif isinstance(node, ast.Constant):
            operands.append(str(node.value))
        elif isinstance(node, (ast.Str, ast.Num)):  # For older Python versions
            operands.append(str(node.n if hasattr(node, 'n') else node.s))
        
        # Recursively process child nodes
        for child in ast.iter_child_nodes(node):
            self._extract_halstead_elements(child, operators, operands)
    
    def _calculate_maintainability_index(self, function, cyclomatic_complexity: int, halstead_metrics: Dict[str, float]) -> float:
        """Calculate maintainability index."""
        try:
            if not hasattr(function, 'source'):
                return 50.0  # Default score
            
            # Count lines of code
            loc = len(function.source.splitlines())
            
            # Get Halstead volume
            halstead_volume = halstead_metrics.get('volume', 1)
            
            # Calculate maintainability index using the standard formula
            # MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
            if halstead_volume <= 0 or loc <= 0:
                return 50.0
            
            mi = (171 
                  - 5.2 * math.log(halstead_volume) 
                  - 0.23 * cyclomatic_complexity 
                  - 16.2 * math.log(loc))
            
            # Normalize to 0-100 scale
            normalized_mi = max(0, min(100, mi))
            
            return normalized_mi
        
        except Exception as e:
            logger.warning(f"Failed to calculate maintainability index: {e}")
            return 50.0
    
    def _get_complexity_level(self, complexity: int) -> str:
        """Get complexity level description."""
        if complexity <= self.complexity_thresholds['low']:
            return 'low'
        elif complexity <= self.complexity_thresholds['moderate']:
            return 'moderate'
        elif complexity <= self.complexity_thresholds['high']:
            return 'high'
        else:
            return 'very_high'
    
    def _compile_complexity_metrics(self, complexities: List[int], 
                                   halstead_metrics: List[Dict[str, float]], 
                                   maintainability_scores: List[float],
                                   function_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compile all complexity metrics into a comprehensive report."""
        if not complexities:
            return self._get_default_complexity_metrics()
        
        # Basic statistics
        total_functions = len(complexities)
        max_complexity = max(complexities)
        min_complexity = min(complexities)
        avg_complexity = sum(complexities) / total_functions
        median_complexity = sorted(complexities)[total_functions // 2]
        
        # Complexity distribution
        complexity_distribution = Counter(complexities)
        complexity_levels = Counter(self._get_complexity_level(c) for c in complexities)
        
        # Halstead statistics
        halstead_volumes = [h.get('volume', 0) for h in halstead_metrics]
        avg_halstead_volume = sum(halstead_volumes) / len(halstead_volumes) if halstead_volumes else 0
        
        # Maintainability statistics
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0
        
        # Find most complex functions
        most_complex = sorted(function_details, key=lambda x: x['cyclomatic_complexity'], reverse=True)[:10]
        least_maintainable = sorted(function_details, key=lambda x: x.get('maintainability_index', 50))[:10]
        
        return {
            'total_functions': total_functions,
            'max_complexity': max_complexity,
            'min_complexity': min_complexity,
            'average_complexity': round(avg_complexity, 2),
            'median_complexity': median_complexity,
            'complexity_distribution': dict(complexity_distribution),
            'complexity_levels': dict(complexity_levels),
            'average_halstead_volume': round(avg_halstead_volume, 2),
            'average_maintainability': round(avg_maintainability, 2),
            'most_complex_functions': most_complex,
            'least_maintainable_functions': least_maintainable,
            'high_complexity_count': len([c for c in complexities if c > self.complexity_thresholds['high']]),
            'very_high_complexity_count': len([c for c in complexities if c > self.complexity_thresholds['very_high']]),
            'function_details': function_details
        }
    
    def _get_default_complexity_metrics(self) -> Dict[str, Any]:
        """Return default complexity metrics when analysis fails."""
        return {
            'total_functions': 0,
            'max_complexity': 0,
            'min_complexity': 0,
            'average_complexity': 0,
            'median_complexity': 0,
            'complexity_distribution': {},
            'complexity_levels': {},
            'average_halstead_volume': 0,
            'average_maintainability': 0,
            'most_complex_functions': [],
            'least_maintainable_functions': [],
            'high_complexity_count': 0,
            'very_high_complexity_count': 0,
            'function_details': []
        }
    
    def generate_complexity_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a human-readable complexity report."""
        report = []
        report.append("🔢 COMPLEXITY ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Overview
        report.append(f"📊 Total Functions Analyzed: {metrics['total_functions']}")
        report.append(f"📈 Average Complexity: {metrics['average_complexity']}")
        report.append(f"📊 Median Complexity: {metrics['median_complexity']}")
        report.append(f"🔺 Maximum Complexity: {metrics['max_complexity']}")
        report.append(f"🔻 Minimum Complexity: {metrics['min_complexity']}")
        report.append("")
        
        # Complexity levels
        report.append("📊 COMPLEXITY DISTRIBUTION")
        report.append("-" * 30)
        levels = metrics['complexity_levels']
        for level in ['low', 'moderate', 'high', 'very_high']:
            count = levels.get(level, 0)
            percentage = (count / metrics['total_functions'] * 100) if metrics['total_functions'] > 0 else 0
            report.append(f"{level.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        report.append("")
        
        # Quality metrics
        report.append("🎯 QUALITY METRICS")
        report.append("-" * 30)
        report.append(f"Average Halstead Volume: {metrics['average_halstead_volume']:.1f}")
        report.append(f"Average Maintainability: {metrics['average_maintainability']:.1f}")
        report.append("")
        
        # High complexity functions
        if metrics['high_complexity_count'] > 0:
            report.append("⚠️  HIGH COMPLEXITY FUNCTIONS")
            report.append("-" * 30)
            report.append(f"Functions with complexity > {self.complexity_thresholds['high']}: {metrics['high_complexity_count']}")
            
            if metrics['most_complex_functions']:
                report.append("\nMost Complex Functions:")
                for func in metrics['most_complex_functions'][:5]:
                    report.append(f"  • {func['name']} (complexity: {func['cyclomatic_complexity']})")
        
        return "\n".join(report)
    
    def get_complexity_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on complexity analysis."""
        recommendations = []
        
        if metrics['average_complexity'] > self.complexity_thresholds['moderate']:
            recommendations.append("🔄 Consider refactoring functions to reduce average complexity")
        
        if metrics['high_complexity_count'] > 0:
            recommendations.append(f"⚠️  {metrics['high_complexity_count']} functions have high complexity - prioritize refactoring")
        
        if metrics['very_high_complexity_count'] > 0:
            recommendations.append(f"🚨 {metrics['very_high_complexity_count']} functions have very high complexity - immediate attention needed")
        
        if metrics['average_maintainability'] < 50:
            recommendations.append("📉 Low maintainability score - focus on code quality improvements")
        
        # Specific function recommendations
        very_complex = [f for f in metrics['function_details'] if f['cyclomatic_complexity'] > self.complexity_thresholds['very_high']]
        if very_complex:
            recommendations.append(f"🎯 Priority refactoring targets: {', '.join([f['name'] for f in very_complex[:3]])}")
        
        if not recommendations:
            recommendations.append("✅ Complexity levels are within acceptable ranges")
        
        return recommendations

