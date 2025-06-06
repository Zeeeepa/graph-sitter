"""
Dead Code Detection Module

Detects unused functions, classes, and variables in the codebase.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set

logger = logging.getLogger(__name__)


class DeadCodeDetector:
    """Detects dead/unused code in the codebase."""
    
    def __init__(self, config=None):
        """Initialize dead code detector."""
        self.config = config
    
    def detect(self, codebase=None, path: Union[str, Path] = None) -> List[Dict[str, Any]]:
        """
        Detect dead code in the codebase.
        
        Args:
            codebase: Graph-sitter codebase object (if available)
            path: Path to codebase for fallback analysis
            
        Returns:
            List of detected dead code items
        """
        logger.info("Starting dead code detection")
        
        if codebase:
            return self._detect_with_graph_sitter(codebase)
        else:
            return self._detect_fallback(Path(path))
    
    def _detect_with_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Detect dead code using graph-sitter codebase."""
        dead_code = []
        
        try:
            # Collect all defined symbols
            defined_symbols = {}
            used_symbols = set()
            
            # First pass: collect definitions
            for file in codebase.files:
                try:
                    # Functions
                    for func in file.functions:
                        symbol_key = f"{file.filepath}::{func.name}"
                        defined_symbols[symbol_key] = {
                            'type': 'function',
                            'name': func.name,
                            'file': file.filepath,
                            'line': getattr(func, 'line_number', None)
                        }
                    
                    # Classes
                    for cls in file.classes:
                        symbol_key = f"{file.filepath}::{cls.name}"
                        defined_symbols[symbol_key] = {
                            'type': 'class',
                            'name': cls.name,
                            'file': file.filepath,
                            'line': getattr(cls, 'line_number', None)
                        }
                
                except Exception as e:
                    logger.warning(f"Failed to collect symbols from {file.filepath}: {e}")
            
            # Second pass: collect usages
            for file in codebase.files:
                try:
                    # Check function usages
                    for func in file.functions:
                        for usage in getattr(func, 'usages', []):
                            # Mark function as used
                            symbol_key = f"{file.filepath}::{func.name}"
                            used_symbols.add(symbol_key)
                    
                    # Check class usages
                    for cls in file.classes:
                        for usage in getattr(cls, 'usages', []):
                            # Mark class as used
                            symbol_key = f"{file.filepath}::{cls.name}"
                            used_symbols.add(symbol_key)
                
                except Exception as e:
                    logger.warning(f"Failed to collect usages from {file.filepath}: {e}")
            
            # Find unused symbols
            for symbol_key, symbol_info in defined_symbols.items():
                if symbol_key not in used_symbols:
                    # Skip main functions and special methods
                    if symbol_info['name'] in ['main', '__init__', '__str__', '__repr__']:
                        continue
                    
                    dead_code.append({
                        'type': 'unused_symbol',
                        'symbol_type': symbol_info['type'],
                        'name': symbol_info['name'],
                        'file': symbol_info['file'],
                        'line': symbol_info['line'],
                        'severity': 'medium'
                    })
            
            logger.info(f"Found {len(dead_code)} dead code items")
            
        except Exception as e:
            logger.error(f"Dead code detection failed: {e}")
            dead_code.append({'error': str(e)})
        
        return dead_code
    
    def _detect_fallback(self, path: Path) -> List[Dict[str, Any]]:
        """Fallback detection without graph-sitter."""
        dead_code = []
        
        try:
            import ast
            
            # Collect all defined and used symbols
            defined_symbols = {}
            used_symbols = set()
            
            # Analyze Python files
            for py_file in path.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        rel_path = str(py_file.relative_to(path))
                        
                        try:
                            tree = ast.parse(content)
                            
                            # Collect definitions
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    symbol_key = f"{rel_path}::{node.name}"
                                    defined_symbols[symbol_key] = {
                                        'type': 'function',
                                        'name': node.name,
                                        'file': rel_path,
                                        'line': node.lineno
                                    }
                                elif isinstance(node, ast.ClassDef):
                                    symbol_key = f"{rel_path}::{node.name}"
                                    defined_symbols[symbol_key] = {
                                        'type': 'class',
                                        'name': node.name,
                                        'file': rel_path,
                                        'line': node.lineno
                                    }
                                elif isinstance(node, ast.Name):
                                    # Collect name usages
                                    used_symbols.add(node.id)
                        
                        except SyntaxError:
                            logger.warning(f"Syntax error in {py_file}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to analyze {py_file}: {e}")
            
            # Find unused symbols (simplified heuristic)
            for symbol_key, symbol_info in defined_symbols.items():
                if symbol_info['name'] not in used_symbols:
                    # Skip main functions and special methods
                    if symbol_info['name'] in ['main', '__init__', '__str__', '__repr__']:
                        continue
                    
                    dead_code.append({
                        'type': 'unused_symbol',
                        'symbol_type': symbol_info['type'],
                        'name': symbol_info['name'],
                        'file': symbol_info['file'],
                        'line': symbol_info['line'],
                        'severity': 'medium'
                    })
            
            logger.info(f"Found {len(dead_code)} potential dead code items")
            
        except Exception as e:
            logger.error(f"Fallback dead code detection failed: {e}")
            dead_code.append({'error': str(e)})
        
        return dead_code
    
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

