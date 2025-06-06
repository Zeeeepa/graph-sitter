"""
Pattern Detection Module

Detects code patterns, anti-patterns, and best practices violations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects code patterns and anti-patterns."""
    
    def __init__(self, config=None):
        """Initialize pattern detector."""
        self.config = config
    
    def detect(self, codebase=None, path: Union[str, Path] = None) -> List[Dict[str, Any]]:
        """
        Detect patterns in the codebase.
        
        Args:
            codebase: Graph-sitter codebase object (if available)
            path: Path to codebase for fallback analysis
            
        Returns:
            List of detected patterns
        """
        logger.info("Starting pattern detection")
        
        if codebase:
            return self._detect_with_graph_sitter(codebase)
        else:
            return self._detect_fallback(Path(path))
    
    def _detect_with_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Detect patterns using graph-sitter codebase."""
        patterns = []
        
        try:
            for file in codebase.files:
                try:
                    file_patterns = self._analyze_file_patterns(file.content, file.filepath)
                    patterns.extend(file_patterns)
                except Exception as e:
                    logger.warning(f"Failed to analyze patterns in {file.filepath}: {e}")
            
            logger.info(f"Found {len(patterns)} patterns")
            
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            patterns.append({'error': str(e)})
        
        return patterns
    
    def _detect_fallback(self, path: Path) -> List[Dict[str, Any]]:
        """Fallback pattern detection."""
        patterns = []
        
        try:
            for py_file in path.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        rel_path = str(py_file.relative_to(path))
                        file_patterns = self._analyze_file_patterns(content, rel_path)
                        patterns.extend(file_patterns)
                    
                    except Exception as e:
                        logger.warning(f"Failed to analyze patterns in {py_file}: {e}")
            
            logger.info(f"Found {len(patterns)} patterns")
            
        except Exception as e:
            logger.error(f"Fallback pattern detection failed: {e}")
            patterns.append({'error': str(e)})
        
        return patterns
    
    def _analyze_file_patterns(self, content: str, filepath: str) -> List[Dict[str, Any]]:
        """Analyze patterns in a single file."""
        patterns = []
        
        try:
            import ast
            tree = ast.parse(content)
            
            # Detect various patterns
            patterns.extend(self._detect_long_functions(tree, filepath))
            patterns.extend(self._detect_too_many_parameters(tree, filepath))
            patterns.extend(self._detect_deep_nesting(tree, filepath))
            patterns.extend(self._detect_code_smells(tree, filepath))
            
        except SyntaxError:
            patterns.append({
                'type': 'syntax_error',
                'file': filepath,
                'severity': 'high',
                'description': 'File contains syntax errors'
            })
        except Exception as e:
            logger.warning(f"Failed to analyze patterns in {filepath}: {e}")
        
        return patterns
    
    def _detect_long_functions(self, tree: ast.AST, filepath: str) -> List[Dict[str, Any]]:
        """Detect functions that are too long."""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    func_lines = node.end_lineno - node.lineno + 1
                    
                    if func_lines > 50:  # Threshold for long function
                        patterns.append({
                            'type': 'long_function',
                            'file': filepath,
                            'function': node.name,
                            'line': node.lineno,
                            'lines': func_lines,
                            'severity': 'high' if func_lines > 100 else 'medium',
                            'description': f'Function {node.name} is {func_lines} lines long'
                        })
        
        return patterns
    
    def _detect_too_many_parameters(self, tree: ast.AST, filepath: str) -> List[Dict[str, Any]]:
        """Detect functions with too many parameters."""
        patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                
                if param_count > 5:  # Threshold for too many parameters
                    patterns.append({
                        'type': 'too_many_parameters',
                        'file': filepath,
                        'function': node.name,
                        'line': node.lineno,
                        'parameters': param_count,
                        'severity': 'high' if param_count > 8 else 'medium',
                        'description': f'Function {node.name} has {param_count} parameters'
                    })
        
        return patterns
    
    def _detect_deep_nesting(self, tree: ast.AST, filepath: str) -> List[Dict[str, Any]]:
        """Detect deeply nested code."""
        patterns = []
        
        def calculate_nesting_depth(node, depth=0):
            max_depth = depth
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    child_depth = calculate_nesting_depth(child, depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = calculate_nesting_depth(child, depth)
                    max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                nesting_depth = calculate_nesting_depth(node)
                
                if nesting_depth > 4:  # Threshold for deep nesting
                    patterns.append({
                        'type': 'deep_nesting',
                        'file': filepath,
                        'function': node.name,
                        'line': node.lineno,
                        'depth': nesting_depth,
                        'severity': 'high' if nesting_depth > 6 else 'medium',
                        'description': f'Function {node.name} has nesting depth of {nesting_depth}'
                    })
        
        return patterns
    
    def _detect_code_smells(self, tree: ast.AST, filepath: str) -> List[Dict[str, Any]]:
        """Detect various code smells."""
        patterns = []
        
        # Detect duplicate code (simplified)
        function_bodies = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Simple hash of function structure
                body_str = ast.dump(node)
                if body_str in function_bodies:
                    patterns.append({
                        'type': 'duplicate_code',
                        'file': filepath,
                        'function': node.name,
                        'line': node.lineno,
                        'duplicate_of': function_bodies[body_str],
                        'severity': 'medium',
                        'description': f'Function {node.name} appears to be duplicate code'
                    })
                else:
                    function_bodies[body_str] = node.name
        
        # Detect empty except blocks
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if not handler.body or (len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)):
                        patterns.append({
                            'type': 'empty_except',
                            'file': filepath,
                            'line': handler.lineno,
                            'severity': 'high',
                            'description': 'Empty except block found'
                        })
        
        # Detect bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        patterns.append({
                            'type': 'bare_except',
                            'file': filepath,
                            'line': handler.lineno,
                            'severity': 'medium',
                            'description': 'Bare except clause found'
                        })
        
        return patterns
    
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

