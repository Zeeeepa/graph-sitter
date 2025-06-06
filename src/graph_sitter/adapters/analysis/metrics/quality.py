"""
Code Quality Metrics Module

Provides comprehensive code quality analysis including maintainability index,
Halstead metrics, and other quality indicators.
"""

import ast
import math
import logging
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set

logger = logging.getLogger(__name__)


class QualityMetrics:
    """Analyzes code quality metrics for a codebase."""
    
    def __init__(self, config=None):
        """Initialize quality metrics analyzer."""
        self.config = config
        self.metrics = {}
    
    def analyze(self, codebase=None, path: Union[str, Path] = None) -> Dict[str, Any]:
        """
        Analyze code quality metrics for the codebase.
        
        Args:
            codebase: Graph-sitter codebase object (if available)
            path: Path to codebase for fallback analysis
            
        Returns:
            Dictionary containing quality metrics
        """
        logger.info("Starting quality metrics analysis")
        
        if codebase:
            return self._analyze_with_graph_sitter(codebase)
        else:
            return self._analyze_fallback(Path(path))
    
    def _analyze_with_graph_sitter(self, codebase) -> Dict[str, Any]:
        """Analyze using graph-sitter codebase."""
        metrics = {
            'maintainability_index': 0.0,
            'halstead_metrics': {},
            'code_quality_score': 0.0,
            'file_metrics': {},
            'function_metrics': {},
            'class_metrics': {},
            'overall_stats': {}
        }
        
        try:
            # Analyze each file
            file_metrics = {}
            total_maintainability = 0.0
            total_files = 0
            
            for file in codebase.files:
                try:
                    file_metric = self._analyze_file_graph_sitter(file)
                    file_metrics[file.filepath] = file_metric
                    total_maintainability += file_metric.get('maintainability_index', 0)
                    total_files += 1
                except Exception as e:
                    logger.warning(f"Failed to analyze file {file.filepath}: {e}")
            
            metrics['file_metrics'] = file_metrics
            
            # Calculate overall maintainability
            if total_files > 0:
                metrics['maintainability_index'] = total_maintainability / total_files
            
            # Analyze functions
            function_metrics = {}
            for file in codebase.files:
                try:
                    for func in file.functions:
                        func_key = f"{file.filepath}::{func.name}"
                        function_metrics[func_key] = self._analyze_function_graph_sitter(func)
                except Exception as e:
                    logger.warning(f"Failed to analyze functions in {file.filepath}: {e}")
            
            metrics['function_metrics'] = function_metrics
            
            # Analyze classes
            class_metrics = {}
            for file in codebase.files:
                try:
                    for cls in file.classes:
                        cls_key = f"{file.filepath}::{cls.name}"
                        class_metrics[cls_key] = self._analyze_class_graph_sitter(cls)
                except Exception as e:
                    logger.warning(f"Failed to analyze classes in {file.filepath}: {e}")
            
            metrics['class_metrics'] = class_metrics
            
            # Calculate overall stats
            metrics['overall_stats'] = self._calculate_overall_stats(metrics)
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _analyze_fallback(self, path: Path) -> Dict[str, Any]:
        """Fallback analysis without graph-sitter."""
        metrics = {
            'maintainability_index': 0.0,
            'halstead_metrics': {},
            'code_quality_score': 0.0,
            'file_metrics': {},
            'overall_stats': {}
        }
        
        try:
            file_metrics = {}
            total_maintainability = 0.0
            total_files = 0
            
            # Analyze Python files
            for py_file in path.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    try:
                        file_metric = self._analyze_python_file(py_file)
                        file_metrics[str(py_file.relative_to(path))] = file_metric
                        total_maintainability += file_metric.get('maintainability_index', 0)
                        total_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to analyze file {py_file}: {e}")
            
            metrics['file_metrics'] = file_metrics
            
            # Calculate overall maintainability
            if total_files > 0:
                metrics['maintainability_index'] = total_maintainability / total_files
            
            # Calculate overall stats
            metrics['overall_stats'] = self._calculate_overall_stats(metrics)
            
        except Exception as e:
            logger.error(f"Fallback quality analysis failed: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _analyze_file_graph_sitter(self, file) -> Dict[str, Any]:
        """Analyze a single file using graph-sitter."""
        try:
            content = file.content
            lines = content.splitlines()
            
            # Basic metrics
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            blank_lines = total_lines - code_lines - comment_lines
            
            # Calculate Halstead metrics if it's a Python file
            halstead = {}
            maintainability = 0.0
            
            if file.filepath.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    halstead = self._calculate_halstead_metrics(tree)
                    maintainability = self._calculate_maintainability_index(
                        code_lines, halstead.get('volume', 0), 
                        self._calculate_cyclomatic_complexity(tree)
                    )
                except SyntaxError:
                    logger.warning(f"Syntax error in {file.filepath}")
            
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'comment_ratio': comment_lines / max(code_lines, 1),
                'halstead_metrics': halstead,
                'maintainability_index': maintainability,
                'functions_count': len(file.functions) if hasattr(file, 'functions') else 0,
                'classes_count': len(file.classes) if hasattr(file, 'classes') else 0
            }
        except Exception as e:
            logger.warning(f"Failed to analyze file {file.filepath}: {e}")
            return {'error': str(e)}
    
    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file without graph-sitter."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.splitlines()
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            blank_lines = total_lines - code_lines - comment_lines
            
            # Parse AST for more detailed analysis
            try:
                tree = ast.parse(content)
                halstead = self._calculate_halstead_metrics(tree)
                complexity = self._calculate_cyclomatic_complexity(tree)
                maintainability = self._calculate_maintainability_index(code_lines, halstead.get('volume', 0), complexity)
                
                # Count functions and classes
                functions_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
                classes_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                
            except SyntaxError:
                halstead = {}
                complexity = 0
                maintainability = 0.0
                functions_count = 0
                classes_count = 0
            
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'comment_ratio': comment_lines / max(code_lines, 1),
                'halstead_metrics': halstead,
                'cyclomatic_complexity': complexity,
                'maintainability_index': maintainability,
                'functions_count': functions_count,
                'classes_count': classes_count
            }
        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            return {'error': str(e)}
    
    def _analyze_function_graph_sitter(self, func) -> Dict[str, Any]:
        """Analyze a function using graph-sitter."""
        try:
            # Get function source code
            source = getattr(func, 'source', '') or getattr(func, 'content', '')
            lines = source.splitlines()
            
            # Basic metrics
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Parameters and return type
            params_count = len(func.parameters) if hasattr(func, 'parameters') else 0
            has_return_type = hasattr(func, 'return_type') and func.return_type is not None
            
            # Calculate complexity if possible
            complexity = 1  # Base complexity
            try:
                if source:
                    tree = ast.parse(source)
                    complexity = self._calculate_cyclomatic_complexity(tree)
            except:
                pass
            
            return {
                'name': func.name,
                'total_lines': total_lines,
                'code_lines': code_lines,
                'parameters_count': params_count,
                'has_return_type': has_return_type,
                'cyclomatic_complexity': complexity,
                'quality_score': self._calculate_function_quality_score(
                    code_lines, params_count, complexity, has_return_type
                )
            }
        except Exception as e:
            logger.warning(f"Failed to analyze function {func.name}: {e}")
            return {'error': str(e)}
    
    def _analyze_class_graph_sitter(self, cls) -> Dict[str, Any]:
        """Analyze a class using graph-sitter."""
        try:
            # Get class source code
            source = getattr(cls, 'source', '') or getattr(cls, 'content', '')
            lines = source.splitlines()
            
            # Basic metrics
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Methods and attributes
            methods_count = len(cls.methods) if hasattr(cls, 'methods') else 0
            attributes_count = len(cls.attributes) if hasattr(cls, 'attributes') else 0
            
            # Inheritance
            base_classes = getattr(cls, 'base_classes', [])
            inheritance_depth = len(base_classes)
            
            return {
                'name': cls.name,
                'total_lines': total_lines,
                'code_lines': code_lines,
                'methods_count': methods_count,
                'attributes_count': attributes_count,
                'inheritance_depth': inheritance_depth,
                'base_classes': [str(base) for base in base_classes],
                'quality_score': self._calculate_class_quality_score(
                    code_lines, methods_count, attributes_count, inheritance_depth
                )
            }
        except Exception as e:
            logger.warning(f"Failed to analyze class {cls.name}: {e}")
            return {'error': str(e)}
    
    def _calculate_halstead_metrics(self, tree: ast.AST) -> Dict[str, float]:
        """Calculate Halstead complexity metrics."""
        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0
        
        for node in ast.walk(tree):
            # Operators
            if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, 
                               ast.Pow, ast.LShift, ast.RShift, ast.BitOr, 
                               ast.BitXor, ast.BitAnd, ast.FloorDiv)):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, (ast.And, ast.Or, ast.Not)):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, 
                                 ast.Gt, ast.GtE, ast.Is, ast.IsNot, 
                                 ast.In, ast.NotIn)):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.If, 
                                 ast.For, ast.While, ast.Try, ast.With)):
                operators.add(type(node).__name__)
                operator_count += 1
            
            # Operands
            elif isinstance(node, ast.Name):
                operands.add(node.id)
                operand_count += 1
            elif isinstance(node, (ast.Constant, ast.Num, ast.Str)):
                value = getattr(node, 'value', getattr(node, 'n', getattr(node, 's', 'unknown')))
                operands.add(str(value))
                operand_count += 1
        
        # Halstead metrics
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)   # Number of distinct operands
        N1 = operator_count  # Total number of operators
        N2 = operand_count   # Total number of operands
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if n2 == 0:
            volume = 0
            difficulty = 0
            effort = 0
        else:
            volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
        
        return {
            'distinct_operators': n1,
            'distinct_operands': n2,
            'total_operators': N1,
            'total_operands': N2,
            'vocabulary': vocabulary,
            'length': length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort
        }
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, (ast.BoolOp, ast.Compare)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_maintainability_index(self, lines_of_code: int, halstead_volume: float, 
                                       cyclomatic_complexity: int) -> float:
        """Calculate maintainability index."""
        if lines_of_code == 0:
            return 100.0
        
        # Microsoft's maintainability index formula
        mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * cyclomatic_complexity - 16.2 * math.log(lines_of_code)
        
        # Normalize to 0-100 scale
        mi = max(0, min(100, mi))
        
        return mi
    
    def _calculate_function_quality_score(self, code_lines: int, params_count: int, 
                                        complexity: int, has_return_type: bool) -> float:
        """Calculate a quality score for a function."""
        score = 100.0
        
        # Penalize long functions
        if code_lines > 50:
            score -= (code_lines - 50) * 0.5
        
        # Penalize too many parameters
        if params_count > 5:
            score -= (params_count - 5) * 5
        
        # Penalize high complexity
        if complexity > 10:
            score -= (complexity - 10) * 3
        
        # Reward type hints
        if has_return_type:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_class_quality_score(self, code_lines: int, methods_count: int, 
                                     attributes_count: int, inheritance_depth: int) -> float:
        """Calculate a quality score for a class."""
        score = 100.0
        
        # Penalize very large classes
        if code_lines > 200:
            score -= (code_lines - 200) * 0.1
        
        # Penalize too many methods
        if methods_count > 20:
            score -= (methods_count - 20) * 2
        
        # Penalize too many attributes
        if attributes_count > 15:
            score -= (attributes_count - 15) * 2
        
        # Penalize deep inheritance
        if inheritance_depth > 3:
            score -= (inheritance_depth - 3) * 10
        
        return max(0, min(100, score))
    
    def _calculate_overall_stats(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall statistics from file metrics."""
        file_metrics = metrics.get('file_metrics', {})
        
        if not file_metrics:
            return {}
        
        total_lines = sum(fm.get('total_lines', 0) for fm in file_metrics.values())
        total_code_lines = sum(fm.get('code_lines', 0) for fm in file_metrics.values())
        total_comment_lines = sum(fm.get('comment_lines', 0) for fm in file_metrics.values())
        total_functions = sum(fm.get('functions_count', 0) for fm in file_metrics.values())
        total_classes = sum(fm.get('classes_count', 0) for fm in file_metrics.values())
        
        # Average comment ratio
        comment_ratios = [fm.get('comment_ratio', 0) for fm in file_metrics.values() if 'comment_ratio' in fm]
        avg_comment_ratio = sum(comment_ratios) / len(comment_ratios) if comment_ratios else 0
        
        return {
            'total_lines': total_lines,
            'total_code_lines': total_code_lines,
            'total_comment_lines': total_comment_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'average_comment_ratio': avg_comment_ratio,
            'files_analyzed': len(file_metrics)
        }
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        if self.config and hasattr(self.config, 'exclude_patterns'):
            for pattern in self.config.exclude_patterns:
                if pattern in str(file_path):
                    return False
        
        # Skip common non-source directories
        exclude_dirs = {'__pycache__', '.git', '.venv', 'venv', 'node_modules', '.pytest_cache'}
        if any(part in exclude_dirs for part in file_path.parts):
            return False
        
        return True

