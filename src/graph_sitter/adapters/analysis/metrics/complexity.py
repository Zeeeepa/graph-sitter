"""
Complexity Analysis Module

Provides detailed complexity analysis including cyclomatic complexity,
cognitive complexity, and other complexity metrics.
"""

import ast
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Analyzes code complexity metrics for a codebase."""
    
    def __init__(self, config=None):
        """Initialize complexity analyzer."""
        self.config = config
    
    def analyze(self, codebase=None, path: Union[str, Path] = None) -> Dict[str, Any]:
        """
        Analyze complexity metrics for the codebase.
        
        Args:
            codebase: Graph-sitter codebase object (if available)
            path: Path to codebase for fallback analysis
            
        Returns:
            Dictionary containing complexity metrics
        """
        logger.info("Starting complexity analysis")
        
        if codebase:
            return self._analyze_with_graph_sitter(codebase)
        else:
            return self._analyze_fallback(Path(path))
    
    def _analyze_with_graph_sitter(self, codebase) -> Dict[str, Any]:
        """Analyze using graph-sitter codebase."""
        metrics = {
            'overall_complexity': {},
            'file_complexity': {},
            'function_complexity': {},
            'class_complexity': {},
            'complexity_distribution': {},
            'hotspots': []
        }
        
        try:
            file_complexities = {}
            function_complexities = {}
            class_complexities = {}
            
            # Analyze each file
            for file in codebase.files:
                try:
                    if file.filepath.endswith('.py'):
                        file_complexity = self._analyze_file_complexity(file.content, file.filepath)
                        file_complexities[file.filepath] = file_complexity
                        
                        # Analyze functions in the file
                        for func in file.functions:
                            func_key = f"{file.filepath}::{func.name}"
                            func_source = getattr(func, 'source', '') or getattr(func, 'content', '')
                            if func_source:
                                func_complexity = self._analyze_function_complexity(func_source, func.name)
                                function_complexities[func_key] = func_complexity
                        
                        # Analyze classes in the file
                        for cls in file.classes:
                            cls_key = f"{file.filepath}::{cls.name}"
                            cls_source = getattr(cls, 'source', '') or getattr(cls, 'content', '')
                            if cls_source:
                                cls_complexity = self._analyze_class_complexity(cls_source, cls.name, cls)
                                class_complexities[cls_key] = cls_complexity
                
                except Exception as e:
                    logger.warning(f"Failed to analyze complexity for {file.filepath}: {e}")
            
            metrics['file_complexity'] = file_complexities
            metrics['function_complexity'] = function_complexities
            metrics['class_complexity'] = class_complexities
            
            # Calculate overall metrics
            metrics['overall_complexity'] = self._calculate_overall_complexity(metrics)
            metrics['complexity_distribution'] = self._calculate_complexity_distribution(metrics)
            metrics['hotspots'] = self._identify_complexity_hotspots(metrics)
            
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _analyze_fallback(self, path: Path) -> Dict[str, Any]:
        """Fallback analysis without graph-sitter."""
        metrics = {
            'overall_complexity': {},
            'file_complexity': {},
            'function_complexity': {},
            'complexity_distribution': {},
            'hotspots': []
        }
        
        try:
            file_complexities = {}
            function_complexities = {}
            
            # Analyze Python files
            for py_file in path.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        rel_path = str(py_file.relative_to(path))
                        file_complexity = self._analyze_file_complexity(content, rel_path)
                        file_complexities[rel_path] = file_complexity
                        
                        # Analyze functions in the file
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    func_source = ast.get_source_segment(content, node)
                                    if func_source:
                                        func_key = f"{rel_path}::{node.name}"
                                        func_complexity = self._analyze_function_complexity(func_source, node.name)
                                        function_complexities[func_key] = func_complexity
                        except:
                            pass
                    
                    except Exception as e:
                        logger.warning(f"Failed to analyze complexity for {py_file}: {e}")
            
            metrics['file_complexity'] = file_complexities
            metrics['function_complexity'] = function_complexities
            
            # Calculate overall metrics
            metrics['overall_complexity'] = self._calculate_overall_complexity(metrics)
            metrics['complexity_distribution'] = self._calculate_complexity_distribution(metrics)
            metrics['hotspots'] = self._identify_complexity_hotspots(metrics)
            
        except Exception as e:
            logger.error(f"Fallback complexity analysis failed: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _analyze_file_complexity(self, content: str, filepath: str) -> Dict[str, Any]:
        """Analyze complexity metrics for a single file."""
        try:
            tree = ast.parse(content)
            
            # Calculate various complexity metrics
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            cognitive = self._calculate_cognitive_complexity(tree)
            nesting_depth = self._calculate_max_nesting_depth(tree)
            
            # Count different constructs
            constructs = self._count_constructs(tree)
            
            # Lines of code
            lines = content.splitlines()
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            return {
                'filepath': filepath,
                'cyclomatic_complexity': cyclomatic,
                'cognitive_complexity': cognitive,
                'max_nesting_depth': nesting_depth,
                'total_lines': total_lines,
                'code_lines': code_lines,
                'constructs': constructs,
                'complexity_density': cyclomatic / max(code_lines, 1),
                'complexity_score': self._calculate_complexity_score(cyclomatic, cognitive, nesting_depth)
            }
        
        except SyntaxError as e:
            logger.warning(f"Syntax error in {filepath}: {e}")
            return {
                'filepath': filepath,
                'error': f"Syntax error: {e}",
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'max_nesting_depth': 0,
                'complexity_score': 0
            }
        except Exception as e:
            logger.warning(f"Failed to analyze {filepath}: {e}")
            return {
                'filepath': filepath,
                'error': str(e),
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'max_nesting_depth': 0,
                'complexity_score': 0
            }
    
    def _analyze_function_complexity(self, source: str, func_name: str) -> Dict[str, Any]:
        """Analyze complexity metrics for a single function."""
        try:
            tree = ast.parse(source)
            
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            cognitive = self._calculate_cognitive_complexity(tree)
            nesting_depth = self._calculate_max_nesting_depth(tree)
            
            # Count parameters and local variables
            params_count = 0
            local_vars = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    params_count = len(node.args.args)
                elif isinstance(node, ast.Assign):
                    local_vars += len(node.targets)
            
            lines = source.splitlines()
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            return {
                'name': func_name,
                'cyclomatic_complexity': cyclomatic,
                'cognitive_complexity': cognitive,
                'max_nesting_depth': nesting_depth,
                'code_lines': code_lines,
                'parameters_count': params_count,
                'local_variables': local_vars,
                'complexity_density': cyclomatic / max(code_lines, 1),
                'complexity_score': self._calculate_complexity_score(cyclomatic, cognitive, nesting_depth)
            }
        
        except Exception as e:
            logger.warning(f"Failed to analyze function {func_name}: {e}")
            return {
                'name': func_name,
                'error': str(e),
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'complexity_score': 0
            }
    
    def _analyze_class_complexity(self, source: str, class_name: str, cls_obj=None) -> Dict[str, Any]:
        """Analyze complexity metrics for a single class."""
        try:
            tree = ast.parse(source)
            
            # Count methods and attributes
            methods_count = 0
            attributes_count = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    methods_count += 1
                elif isinstance(node, ast.Assign):
                    # Count class-level assignments as attributes
                    if isinstance(node.targets[0], ast.Name):
                        attributes_count += 1
            
            # Calculate overall class complexity
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            cognitive = self._calculate_cognitive_complexity(tree)
            nesting_depth = self._calculate_max_nesting_depth(tree)
            
            # Inheritance complexity
            inheritance_depth = 0
            if cls_obj and hasattr(cls_obj, 'base_classes'):
                inheritance_depth = len(cls_obj.base_classes)
            
            lines = source.splitlines()
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            return {
                'name': class_name,
                'cyclomatic_complexity': cyclomatic,
                'cognitive_complexity': cognitive,
                'max_nesting_depth': nesting_depth,
                'code_lines': code_lines,
                'methods_count': methods_count,
                'attributes_count': attributes_count,
                'inheritance_depth': inheritance_depth,
                'complexity_density': cyclomatic / max(code_lines, 1),
                'complexity_score': self._calculate_complexity_score(cyclomatic, cognitive, nesting_depth),
                'cohesion_score': self._calculate_class_cohesion(methods_count, attributes_count)
            }
        
        except Exception as e:
            logger.warning(f"Failed to analyze class {class_name}: {e}")
            return {
                'name': class_name,
                'error': str(e),
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'complexity_score': 0
            }
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity (McCabe complexity)."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)  # Each except clause
                if node.orelse:  # else clause
                    complexity += 1
                if node.finalbody:  # finally clause
                    complexity += 1
            elif isinstance(node, (ast.BoolOp)):
                # Each additional boolean operator
                complexity += len(node.values) - 1
            elif isinstance(node, ast.Compare):
                # Each comparison operator
                complexity += len(node.ops)
            elif isinstance(node, ast.comprehension):
                # List/dict/set comprehensions
                complexity += 1
                if node.ifs:  # Conditional in comprehension
                    complexity += len(node.ifs)
            elif isinstance(node, (ast.Lambda)):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity."""
        complexity = 0
        nesting_level = 0
        
        def visit_node(node, level=0):
            nonlocal complexity, nesting_level
            
            # Increment for control structures
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + level  # Base + nesting increment
                level += 1
            elif isinstance(node, ast.Try):
                complexity += 1 + level
                level += 1
            elif isinstance(node, (ast.BoolOp)):
                # Binary logical operators
                complexity += len(node.values) - 1
            elif isinstance(node, ast.Lambda):
                complexity += 1 + level
            elif isinstance(node, (ast.Break, ast.Continue)):
                complexity += 1 + level
            
            # Recursively visit child nodes
            for child in ast.iter_child_nodes(node):
                visit_node(child, level)
        
        visit_node(tree)
        return complexity
    
    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        
        def visit_node(node, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            # Increment depth for nesting constructs
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                               ast.Try, ast.With, ast.AsyncWith, ast.FunctionDef, 
                               ast.AsyncFunctionDef, ast.ClassDef)):
                depth += 1
            
            # Recursively visit child nodes
            for child in ast.iter_child_nodes(node):
                visit_node(child, depth)
        
        visit_node(tree)
        return max_depth
    
    def _count_constructs(self, tree: ast.AST) -> Dict[str, int]:
        """Count different language constructs."""
        constructs = defaultdict(int)
        
        for node in ast.walk(tree):
            node_type = type(node).__name__
            constructs[node_type] += 1
        
        # Group into meaningful categories
        return {
            'functions': constructs.get('FunctionDef', 0) + constructs.get('AsyncFunctionDef', 0),
            'classes': constructs.get('ClassDef', 0),
            'if_statements': constructs.get('If', 0),
            'loops': constructs.get('For', 0) + constructs.get('While', 0) + constructs.get('AsyncFor', 0),
            'try_blocks': constructs.get('Try', 0),
            'with_statements': constructs.get('With', 0) + constructs.get('AsyncWith', 0),
            'lambda_functions': constructs.get('Lambda', 0),
            'comprehensions': constructs.get('ListComp', 0) + constructs.get('DictComp', 0) + constructs.get('SetComp', 0),
            'assignments': constructs.get('Assign', 0) + constructs.get('AugAssign', 0),
            'function_calls': constructs.get('Call', 0),
            'imports': constructs.get('Import', 0) + constructs.get('ImportFrom', 0)
        }
    
    def _calculate_complexity_score(self, cyclomatic: int, cognitive: int, nesting: int) -> float:
        """Calculate a combined complexity score."""
        # Weighted combination of different complexity metrics
        score = (cyclomatic * 0.4) + (cognitive * 0.4) + (nesting * 0.2)
        return round(score, 2)
    
    def _calculate_class_cohesion(self, methods_count: int, attributes_count: int) -> float:
        """Calculate a simple cohesion score for a class."""
        if methods_count == 0:
            return 0.0
        
        # Simple heuristic: classes with balanced methods/attributes have better cohesion
        if attributes_count == 0:
            return 0.5  # Methods without attributes
        
        ratio = min(methods_count, attributes_count) / max(methods_count, attributes_count)
        return round(ratio, 2)
    
    def _calculate_overall_complexity(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall complexity statistics."""
        file_complexities = metrics.get('file_complexity', {})
        function_complexities = metrics.get('function_complexity', {})
        
        if not file_complexities:
            return {}
        
        # File-level statistics
        file_cyclomatic = [fc.get('cyclomatic_complexity', 0) for fc in file_complexities.values()]
        file_cognitive = [fc.get('cognitive_complexity', 0) for fc in file_complexities.values()]
        file_nesting = [fc.get('max_nesting_depth', 0) for fc in file_complexities.values()]
        
        # Function-level statistics
        func_cyclomatic = [fc.get('cyclomatic_complexity', 0) for fc in function_complexities.values()]
        func_cognitive = [fc.get('cognitive_complexity', 0) for fc in function_complexities.values()]
        
        return {
            'files': {
                'total_files': len(file_complexities),
                'avg_cyclomatic': sum(file_cyclomatic) / len(file_cyclomatic) if file_cyclomatic else 0,
                'max_cyclomatic': max(file_cyclomatic) if file_cyclomatic else 0,
                'avg_cognitive': sum(file_cognitive) / len(file_cognitive) if file_cognitive else 0,
                'max_cognitive': max(file_cognitive) if file_cognitive else 0,
                'avg_nesting': sum(file_nesting) / len(file_nesting) if file_nesting else 0,
                'max_nesting': max(file_nesting) if file_nesting else 0
            },
            'functions': {
                'total_functions': len(function_complexities),
                'avg_cyclomatic': sum(func_cyclomatic) / len(func_cyclomatic) if func_cyclomatic else 0,
                'max_cyclomatic': max(func_cyclomatic) if func_cyclomatic else 0,
                'avg_cognitive': sum(func_cognitive) / len(func_cognitive) if func_cognitive else 0,
                'max_cognitive': max(func_cognitive) if func_cognitive else 0
            }
        }
    
    def _calculate_complexity_distribution(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate complexity distribution statistics."""
        function_complexities = metrics.get('function_complexity', {})
        
        if not function_complexities:
            return {}
        
        cyclomatic_values = [fc.get('cyclomatic_complexity', 0) for fc in function_complexities.values()]
        
        # Categorize by complexity levels
        low = len([c for c in cyclomatic_values if c <= 5])
        medium = len([c for c in cyclomatic_values if 6 <= c <= 10])
        high = len([c for c in cyclomatic_values if 11 <= c <= 20])
        very_high = len([c for c in cyclomatic_values if c > 20])
        
        total = len(cyclomatic_values)
        
        return {
            'low_complexity': {'count': low, 'percentage': (low / total * 100) if total > 0 else 0},
            'medium_complexity': {'count': medium, 'percentage': (medium / total * 100) if total > 0 else 0},
            'high_complexity': {'count': high, 'percentage': (high / total * 100) if total > 0 else 0},
            'very_high_complexity': {'count': very_high, 'percentage': (very_high / total * 100) if total > 0 else 0}
        }
    
    def _identify_complexity_hotspots(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify complexity hotspots that need attention."""
        hotspots = []
        
        # Check file-level hotspots
        file_complexities = metrics.get('file_complexity', {})
        for filepath, file_metrics in file_complexities.items():
            cyclomatic = file_metrics.get('cyclomatic_complexity', 0)
            cognitive = file_metrics.get('cognitive_complexity', 0)
            nesting = file_metrics.get('max_nesting_depth', 0)
            
            if cyclomatic > 20 or cognitive > 25 or nesting > 6:
                hotspots.append({
                    'type': 'file',
                    'name': filepath,
                    'cyclomatic_complexity': cyclomatic,
                    'cognitive_complexity': cognitive,
                    'max_nesting_depth': nesting,
                    'severity': 'high' if cyclomatic > 30 or cognitive > 35 else 'medium'
                })
        
        # Check function-level hotspots
        function_complexities = metrics.get('function_complexity', {})
        for func_key, func_metrics in function_complexities.items():
            cyclomatic = func_metrics.get('cyclomatic_complexity', 0)
            cognitive = func_metrics.get('cognitive_complexity', 0)
            
            if cyclomatic > 10 or cognitive > 15:
                hotspots.append({
                    'type': 'function',
                    'name': func_key,
                    'cyclomatic_complexity': cyclomatic,
                    'cognitive_complexity': cognitive,
                    'severity': 'high' if cyclomatic > 20 or cognitive > 25 else 'medium'
                })
        
        # Sort by severity and complexity
        hotspots.sort(key=lambda x: (
            x['severity'] == 'high',
            x.get('cyclomatic_complexity', 0) + x.get('cognitive_complexity', 0)
        ), reverse=True)
        
        return hotspots[:20]  # Return top 20 hotspots
    
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

