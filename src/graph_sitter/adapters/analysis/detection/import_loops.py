"""
Import Loop Detection Module

Detects circular import dependencies in the codebase.
"""

import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple

logger = logging.getLogger(__name__)


class ImportLoopDetector:
    """Detects circular import dependencies."""
    
    def __init__(self, config=None):
        """Initialize import loop detector."""
        self.config = config
        self.import_graph = defaultdict(set)
        self.file_imports = defaultdict(set)
    
    def detect(self, codebase=None, path: Union[str, Path] = None) -> List[Dict[str, Any]]:
        """
        Detect import loops in the codebase.
        
        Args:
            codebase: Graph-sitter codebase object (if available)
            path: Path to codebase for fallback analysis
            
        Returns:
            List of detected import loops
        """
        logger.info("Starting import loop detection")
        
        if codebase:
            return self._detect_with_graph_sitter(codebase)
        else:
            return self._detect_fallback(Path(path))
    
    def _detect_with_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Detect import loops using graph-sitter codebase."""
        loops = []
        
        try:
            # Build import graph
            self._build_import_graph_graph_sitter(codebase)
            
            # Detect cycles
            cycles = self._find_cycles()
            
            # Convert cycles to detailed loop information
            for cycle in cycles:
                loop_info = self._analyze_import_loop(cycle, codebase)
                loops.append(loop_info)
            
            logger.info(f"Found {len(loops)} import loops")
            
        except Exception as e:
            logger.error(f"Import loop detection failed: {e}")
            loops.append({'error': str(e)})
        
        return loops
    
    def _detect_fallback(self, path: Path) -> List[Dict[str, Any]]:
        """Fallback detection without graph-sitter."""
        loops = []
        
        try:
            # Build import graph from file system
            self._build_import_graph_fallback(path)
            
            # Detect cycles
            cycles = self._find_cycles()
            
            # Convert cycles to detailed loop information
            for cycle in cycles:
                loop_info = self._analyze_import_loop_fallback(cycle, path)
                loops.append(loop_info)
            
            logger.info(f"Found {len(loops)} import loops")
            
        except Exception as e:
            logger.error(f"Fallback import loop detection failed: {e}")
            loops.append({'error': str(e)})
        
        return loops
    
    def _build_import_graph_graph_sitter(self, codebase):
        """Build import dependency graph using graph-sitter."""
        self.import_graph.clear()
        self.file_imports.clear()
        
        for file in codebase.files:
            try:
                file_path = file.filepath
                
                # Get imports for this file
                imports = set()
                for imp in file.imports:
                    try:
                        # Handle different import types
                        module_name = getattr(imp, 'module', None)
                        if module_name:
                            # Try to resolve to actual file path
                            resolved_path = self._resolve_import_path(module_name, file_path, codebase)
                            if resolved_path:
                                imports.add(resolved_path)
                                self.import_graph[file_path].add(resolved_path)
                    except Exception as e:
                        logger.debug(f"Failed to process import in {file_path}: {e}")
                
                self.file_imports[file_path] = imports
                
            except Exception as e:
                logger.warning(f"Failed to analyze imports for {file.filepath}: {e}")
    
    def _build_import_graph_fallback(self, path: Path):
        """Build import dependency graph from file system."""
        import ast
        
        self.import_graph.clear()
        self.file_imports.clear()
        
        # Analyze Python files
        for py_file in path.rglob("*.py"):
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    rel_path = str(py_file.relative_to(path))
                    
                    # Parse imports
                    try:
                        tree = ast.parse(content)
                        imports = self._extract_imports_from_ast(tree, rel_path, path)
                        
                        self.file_imports[rel_path] = imports
                        self.import_graph[rel_path] = imports
                        
                    except SyntaxError:
                        logger.warning(f"Syntax error in {py_file}")
                
                except Exception as e:
                    logger.warning(f"Failed to analyze imports for {py_file}: {e}")
    
    def _extract_imports_from_ast(self, tree: ast.AST, current_file: str, base_path: Path) -> Set[str]:
        """Extract import dependencies from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolved = self._resolve_import_path_fallback(alias.name, current_file, base_path)
                    if resolved:
                        imports.add(resolved)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    resolved = self._resolve_import_path_fallback(node.module, current_file, base_path)
                    if resolved:
                        imports.add(resolved)
        
        return imports
    
    def _resolve_import_path(self, module_name: str, current_file: str, codebase) -> Optional[str]:
        """Resolve import module name to actual file path using graph-sitter."""
        try:
            # Try to find the module in the codebase
            # This is a simplified resolution - graph-sitter may have better methods
            
            # Handle relative imports
            if module_name.startswith('.'):
                current_dir = str(Path(current_file).parent)
                # Convert relative import to absolute path
                parts = module_name.split('.')
                level = len([p for p in parts if p == ''])
                module_parts = [p for p in parts if p]
                
                # Go up directories based on level
                target_dir = Path(current_dir)
                for _ in range(level - 1):
                    target_dir = target_dir.parent
                
                # Add module parts
                for part in module_parts:
                    target_dir = target_dir / part
                
                # Try to find corresponding file
                for ext in ['.py', '/__init__.py']:
                    candidate = str(target_dir) + ext
                    if codebase.has_file(candidate):
                        return candidate
            
            else:
                # Handle absolute imports
                # Try to find module in codebase
                module_parts = module_name.split('.')
                
                # Try different combinations
                for i in range(len(module_parts)):
                    partial_path = '/'.join(module_parts[:i+1])
                    
                    # Try as file
                    candidate = partial_path + '.py'
                    if codebase.has_file(candidate):
                        return candidate
                    
                    # Try as package
                    candidate = partial_path + '/__init__.py'
                    if codebase.has_file(candidate):
                        return candidate
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to resolve import {module_name}: {e}")
            return None
    
    def _resolve_import_path_fallback(self, module_name: str, current_file: str, base_path: Path) -> Optional[str]:
        """Resolve import module name to actual file path in fallback mode."""
        try:
            current_path = Path(current_file)
            current_dir = current_path.parent
            
            # Handle relative imports
            if module_name.startswith('.'):
                parts = module_name.split('.')
                level = len([p for p in parts if p == ''])
                module_parts = [p for p in parts if p]
                
                # Go up directories based on level
                target_dir = base_path / current_dir
                for _ in range(level - 1):
                    target_dir = target_dir.parent
                
                # Add module parts
                for part in module_parts:
                    target_dir = target_dir / part
                
                # Try to find corresponding file
                for ext in ['.py']:
                    candidate = target_dir.with_suffix(ext)
                    if candidate.exists():
                        return str(candidate.relative_to(base_path))
                
                # Try as package
                candidate = target_dir / '__init__.py'
                if candidate.exists():
                    return str(candidate.relative_to(base_path))
            
            else:
                # Handle absolute imports within the project
                module_parts = module_name.split('.')
                
                # Try different combinations
                for i in range(len(module_parts)):
                    partial_path = Path(*module_parts[:i+1])
                    
                    # Try as file
                    candidate = base_path / partial_path.with_suffix('.py')
                    if candidate.exists():
                        return str(candidate.relative_to(base_path))
                    
                    # Try as package
                    candidate = base_path / partial_path / '__init__.py'
                    if candidate.exists():
                        return str(candidate.relative_to(base_path))
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to resolve import {module_name}: {e}")
            return None
    
    def _find_cycles(self) -> List[List[str]]:
        """Find cycles in the import graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, []):
                if dfs(neighbor):
                    # Continue to find more cycles
                    pass
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        # Check all nodes
        for node in self.import_graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _analyze_import_loop(self, cycle: List[str], codebase) -> Dict[str, Any]:
        """Analyze a detected import loop with graph-sitter."""
        loop_info = {
            'type': 'import_loop',
            'files': cycle,
            'length': len(cycle) - 1,  # Exclude the repeated node
            'severity': self._calculate_loop_severity(cycle),
            'imports': []
        }
        
        try:
            # Get detailed import information
            for i in range(len(cycle) - 1):
                from_file = cycle[i]
                to_file = cycle[i + 1]
                
                # Find the specific import statement
                try:
                    file_obj = codebase.get_file(from_file)
                    for imp in file_obj.imports:
                        module_name = getattr(imp, 'module', None)
                        if module_name:
                            resolved = self._resolve_import_path(module_name, from_file, codebase)
                            if resolved == to_file:
                                loop_info['imports'].append({
                                    'from': from_file,
                                    'to': to_file,
                                    'module': module_name,
                                    'line': getattr(imp, 'line_number', None)
                                })
                                break
                except Exception as e:
                    logger.debug(f"Failed to get import details for {from_file}: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to analyze import loop: {e}")
            loop_info['error'] = str(e)
        
        return loop_info
    
    def _analyze_import_loop_fallback(self, cycle: List[str], base_path: Path) -> Dict[str, Any]:
        """Analyze a detected import loop in fallback mode."""
        loop_info = {
            'type': 'import_loop',
            'files': cycle,
            'length': len(cycle) - 1,
            'severity': self._calculate_loop_severity(cycle),
            'imports': []
        }
        
        try:
            # Get detailed import information
            for i in range(len(cycle) - 1):
                from_file = cycle[i]
                to_file = cycle[i + 1]
                
                # Find the specific import statement
                try:
                    file_path = base_path / from_file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import ast
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            module_name = None
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    resolved = self._resolve_import_path_fallback(alias.name, from_file, base_path)
                                    if resolved == to_file:
                                        module_name = alias.name
                                        break
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                resolved = self._resolve_import_path_fallback(node.module, from_file, base_path)
                                if resolved == to_file:
                                    module_name = node.module
                            
                            if module_name:
                                loop_info['imports'].append({
                                    'from': from_file,
                                    'to': to_file,
                                    'module': module_name,
                                    'line': node.lineno
                                })
                                break
                
                except Exception as e:
                    logger.debug(f"Failed to get import details for {from_file}: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to analyze import loop: {e}")
            loop_info['error'] = str(e)
        
        return loop_info
    
    def _calculate_loop_severity(self, cycle: List[str]) -> str:
        """Calculate the severity of an import loop."""
        length = len(cycle) - 1
        
        if length <= 2:
            return 'low'
        elif length <= 4:
            return 'medium'
        else:
            return 'high'
    
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

