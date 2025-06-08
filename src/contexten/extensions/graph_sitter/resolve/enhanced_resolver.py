"""
Enhanced Resolver Module

Provides advanced symbol resolution and import analysis based on graph-sitter.com features.
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
from pathlib import Path
import ast
import os
from dataclasses import dataclass

from ..core.config import CodebaseConfig


@dataclass
class ResolvedSymbol:
    """Represents a resolved symbol with its metadata."""
    name: str
    symbol_type: str  # function, class, variable, import, etc.
    filepath: str
    line_number: int
    column_number: int
    scope: str
    definition: str
    usages: List[Dict[str, Any]]
    dependencies: List[str]
    is_exported: bool
    is_imported: bool
    import_source: Optional[str] = None


@dataclass
class ImportRelationship:
    """Represents an import relationship between files."""
    source_file: str
    target_file: str
    imported_symbols: List[str]
    import_type: str  # direct, star, alias
    is_circular: bool = False


class EnhancedResolver:
    """
    Enhanced symbol resolver with advanced import analysis.
    
    Based on graph-sitter.com's import relationship analysis and
    loop detection capabilities.
    """
    
    def __init__(self, codebase_path: Union[str, Path], config: Optional[CodebaseConfig] = None):
        self.codebase_path = Path(codebase_path)
        self.config = config or CodebaseConfig()
        self._symbol_cache: Dict[str, ResolvedSymbol] = {}
        self._import_cache: Dict[str, List[ImportRelationship]] = {}
        self._circular_imports: List[List[str]] = []
        self._external_modules: Set[str] = set()
        
    def resolve_symbol(self, symbol_name: str, context_file: Optional[str] = None) -> Optional[ResolvedSymbol]:
        """
        Resolve a symbol to its definition with comprehensive metadata.
        
        Args:
            symbol_name: Name of the symbol to resolve
            context_file: File context for resolution (optional)
            
        Returns:
            ResolvedSymbol if found, None otherwise
        """
        cache_key = f"{symbol_name}:{context_file or 'global'}"
        
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        # Search for symbol definition
        resolved = self._search_symbol_definition(symbol_name, context_file)
        
        if resolved:
            # Enhance with usage analysis
            resolved.usages = self._find_symbol_usages(symbol_name, resolved.filepath)
            resolved.dependencies = self._analyze_symbol_dependencies(symbol_name, resolved.filepath)
            
            self._symbol_cache[cache_key] = resolved
        
        return resolved
    
    def analyze_import_relationships(self) -> List[ImportRelationship]:
        """
        Analyze all import relationships in the codebase.
        
        Returns:
            List of ImportRelationship objects
        """
        if self._import_cache:
            return [rel for rels in self._import_cache.values() for rel in rels]
        
        relationships = []
        
        for py_file in self.codebase_path.rglob("*.py"):
            if py_file.is_file():
                file_relationships = self._analyze_file_imports(str(py_file))
                relationships.extend(file_relationships)
                self._import_cache[str(py_file)] = file_relationships
        
        # Detect circular imports
        self._detect_circular_imports(relationships)
        
        return relationships
    
    def detect_circular_imports(self) -> List[List[str]]:
        """
        Detect circular import dependencies.
        
        Returns:
            List of circular import chains
        """
        if not self._circular_imports:
            relationships = self.analyze_import_relationships()
            self._detect_circular_imports(relationships)
        
        return self._circular_imports
    
    def get_file_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Get all imports for a specific file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            List of import information dictionaries
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'is_external': self._is_external_module(alias.name)
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append({
                            'type': 'from_import',
                            'module': module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'level': node.level,
                            'is_external': self._is_external_module(module)
                        })
            
            return imports
            
        except Exception as e:
            print(f"Error analyzing imports in {filepath}: {e}")
            return []
    
    def get_file_inbound_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Get all files that import from the specified file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            List of inbound import information
        """
        inbound_imports = []
        target_module = self._filepath_to_module(filepath)
        
        for py_file in self.codebase_path.rglob("*.py"):
            if py_file.is_file() and str(py_file) != filepath:
                imports = self.get_file_imports(str(py_file))
                
                for imp in imports:
                    if (imp.get('module') == target_module or 
                        imp.get('module', '').startswith(target_module + '.')):
                        inbound_imports.append({
                            'source_file': str(py_file),
                            'import_info': imp
                        })
        
        return inbound_imports
    
    def get_file_symbols(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Get all symbols defined in a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            List of symbol information dictionaries
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            symbols = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append({
                        'name': node.name,
                        'type': 'function',
                        'line': node.lineno,
                        'is_async': isinstance(node, ast.AsyncFunctionDef),
                        'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.ClassDef):
                    symbols.append({
                        'name': node.name,
                        'type': 'class',
                        'line': node.lineno,
                        'bases': [self._get_base_name(base) for base in node.bases],
                        'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append({
                                'name': target.id,
                                'type': 'variable',
                                'line': node.lineno,
                                'scope': 'module'
                            })
            
            return symbols
            
        except Exception as e:
            print(f"Error analyzing symbols in {filepath}: {e}")
            return []
    
    def get_file_external_modules(self, filepath: str) -> List[str]:
        """
        Get external modules imported by a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            List of external module names
        """
        imports = self.get_file_imports(filepath)
        external_modules = []
        
        for imp in imports:
            if imp.get('is_external', False):
                module = imp.get('module', '')
                if module and module not in external_modules:
                    external_modules.append(module)
        
        return external_modules
    
    def resolve_import_path(self, import_path: str, context_file: str) -> Optional[str]:
        """
        Resolve an import path to an actual file path.
        
        Args:
            import_path: Import path to resolve
            context_file: File context for relative imports
            
        Returns:
            Resolved file path if found
        """
        # Handle relative imports
        if import_path.startswith('.'):
            context_dir = Path(context_file).parent
            # Convert relative import to absolute path
            parts = import_path.split('.')
            level = len([p for p in parts if p == ''])
            
            target_dir = context_dir
            for _ in range(level - 1):
                target_dir = target_dir.parent
            
            if len(parts) > level:
                module_parts = parts[level:]
                target_path = target_dir / '/'.join(module_parts)
            else:
                target_path = target_dir
        else:
            # Absolute import
            module_parts = import_path.split('.')
            target_path = self.codebase_path / '/'.join(module_parts)
        
        # Try different file extensions
        candidates = [
            target_path.with_suffix('.py'),
            target_path / '__init__.py'
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        return None
    
    def _search_symbol_definition(self, symbol_name: str, context_file: Optional[str]) -> Optional[ResolvedSymbol]:
        """Search for symbol definition across the codebase."""
        # First search in context file if provided
        if context_file:
            symbols = self.get_file_symbols(context_file)
            for symbol in symbols:
                if symbol['name'] == symbol_name:
                    return ResolvedSymbol(
                        name=symbol_name,
                        symbol_type=symbol['type'],
                        filepath=context_file,
                        line_number=symbol['line'],
                        column_number=0,
                        scope='local',
                        definition='',
                        usages=[],
                        dependencies=[],
                        is_exported=True,
                        is_imported=False
                    )
        
        # Search across all files
        for py_file in self.codebase_path.rglob("*.py"):
            if py_file.is_file():
                symbols = self.get_file_symbols(str(py_file))
                for symbol in symbols:
                    if symbol['name'] == symbol_name:
                        return ResolvedSymbol(
                            name=symbol_name,
                            symbol_type=symbol['type'],
                            filepath=str(py_file),
                            line_number=symbol['line'],
                            column_number=0,
                            scope='global',
                            definition='',
                            usages=[],
                            dependencies=[],
                            is_exported=True,
                            is_imported=False
                        )
        
        return None
    
    def _find_symbol_usages(self, symbol_name: str, definition_file: str) -> List[Dict[str, Any]]:
        """Find all usages of a symbol across the codebase."""
        usages = []
        
        for py_file in self.codebase_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if symbol_name in line:
                            usages.append({
                                'file': str(py_file),
                                'line': line_num,
                                'context': line.strip()
                            })
                except Exception:
                    continue
        
        return usages
    
    def _analyze_symbol_dependencies(self, symbol_name: str, filepath: str) -> List[str]:
        """Analyze dependencies of a symbol."""
        dependencies = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Find the symbol definition and analyze its dependencies
            for node in ast.walk(tree):
                if (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and 
                    node.name == symbol_name):
                    
                    # Analyze function/class body for dependencies
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name) and child.id != symbol_name:
                            if child.id not in dependencies:
                                dependencies.append(child.id)
        
        except Exception:
            pass
        
        return dependencies
    
    def _analyze_file_imports(self, filepath: str) -> List[ImportRelationship]:
        """Analyze import relationships for a single file."""
        relationships = []
        imports = self.get_file_imports(filepath)
        
        for imp in imports:
            if not imp.get('is_external', False):
                target_file = self.resolve_import_path(imp['module'], filepath)
                if target_file:
                    relationship = ImportRelationship(
                        source_file=filepath,
                        target_file=target_file,
                        imported_symbols=[imp.get('name', imp['module'])],
                        import_type=imp['type']
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _detect_circular_imports(self, relationships: List[ImportRelationship]):
        """Detect circular import dependencies using graph analysis."""
        # Build dependency graph
        graph = {}
        for rel in relationships:
            if rel.source_file not in graph:
                graph[rel.source_file] = []
            graph[rel.source_file].append(rel.target_file)
        
        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if cycle not in self._circular_imports:
                    self._circular_imports.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
    
    def _is_external_module(self, module_name: str) -> bool:
        """Check if a module is external (not part of the codebase)."""
        if not module_name:
            return False
        
        # Check if it's a standard library module
        try:
            import sys
            if module_name in sys.builtin_module_names:
                return True
        except:
            pass
        
        # Check if it resolves to a file in the codebase
        module_path = self.codebase_path / module_name.replace('.', '/')
        
        return not (
            (module_path.with_suffix('.py')).exists() or
            (module_path / '__init__.py').exists()
        )
    
    def _filepath_to_module(self, filepath: str) -> str:
        """Convert a file path to a module name."""
        rel_path = Path(filepath).relative_to(self.codebase_path)
        if rel_path.name == '__init__.py':
            module_parts = rel_path.parent.parts
        else:
            module_parts = rel_path.with_suffix('').parts
        
        return '.'.join(module_parts)
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        else:
            return str(decorator)
    
    def _get_base_name(self, base) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}"
        else:
            return str(base)


__all__ = ['EnhancedResolver', 'ResolvedSymbol', 'ImportRelationship']

