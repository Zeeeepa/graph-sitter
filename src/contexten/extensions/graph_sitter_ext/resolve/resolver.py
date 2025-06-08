"""
Resolve class for graph-sitter symbol resolution and import analysis

This module provides symbol resolution, import relationship analysis,
and dependency tracking functionality using the actual graph-sitter API.
"""

from graph_sitter import Codebase
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque
from graph_sitter.configs.models.codebase import CodebaseConfig


class Resolve:
    """
    Resolve class providing symbol resolution and import relationship analysis.
    
    Usage example:
    
    from graph_sitter import Codebase
    from .resolver import Resolve
    
    codebase = Codebase.from_path("./my_project")
    resolver = Resolve(codebase)
    
    # Get all symbols in the codebase
    symbols = resolver.get_all_symbols()
    
    # Resolve a specific symbol
    resolved = resolver.resolve_symbol("MyClass")
    
    # Analyze import relationships
    imports = resolver.analyze_imports()
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize Resolve with a Codebase instance."""
        self.codebase = codebase
    
    def analyze_imports(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze import relationships for a specific file or entire codebase."""
        if file_path:
            return self._analyze_file_imports(file_path)
        else:
            return self._analyze_codebase_imports()
    
    def _analyze_file_imports(self, file_path: str) -> Dict[str, Any]:
        """Analyze imports for a specific file."""
        file = self.codebase.get_file(file_path)
        if not file:
            return {"error": f"File not found: {file_path}"}
        
        imports_data: Dict[str, Any] = {
            "file": file.name,
            "outbound_imports": [],
            "inbound_imports": [],
            "external_dependencies": []
        }
        
        # Analyze outbound imports
        imports = getattr(file, 'imports', [])
        if hasattr(imports, '__iter__'):
            imports_list = list(imports)
            for import_stmt in imports_list:
                import_info = {
                    "module": getattr(import_stmt, 'module', 'unknown'),
                    "symbol": getattr(import_stmt, 'symbol', None),
                    "alias": getattr(import_stmt, 'alias', None),
                    "is_external": getattr(import_stmt, 'is_external', False)
                }
                
                if import_info["is_external"]:
                    imports_data["external_dependencies"].append(import_info)
                else:
                    imports_data["outbound_imports"].append(import_info)
        
        return imports_data
    
    def _analyze_codebase_imports(self) -> Dict[str, Any]:
        """Analyze imports for the entire codebase."""
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        total_imports = len(files)
        
        # Count different types of imports
        internal_imports = 0
        external_imports = 0
        
        # Analyze each file
        for file in files:
            imports = getattr(file, 'imports', [])
            if hasattr(imports, '__iter__'):
                imports_list = list(imports)
                for import_stmt in imports_list:
                    if getattr(import_stmt, 'is_external', False):
                        external_imports += 1
                    else:
                        internal_imports += 1
        
        # Count symbol imports
        symbol_import_count: Dict[str, int] = {}
        for file in files:
            imports = getattr(file, 'imports', [])
            if hasattr(imports, '__iter__'):
                imports_list = list(imports)
                for import_stmt in imports_list:
                    symbol = getattr(import_stmt, 'symbol', None)
                    if symbol:
                        symbol_import_count[symbol] = symbol_import_count.get(symbol, 0) + 1
        
        # Find most imported symbols
        most_imported = sorted(symbol_import_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Detect circular imports
        circular_imports = self.detect_import_loops()
        
        return {
            "total_files": total_imports,
            "internal_imports": internal_imports,
            "external_imports": external_imports,
            "most_imported_symbols": most_imported,
            "circular_imports": len(circular_imports),
            "circular_import_details": circular_imports
        }
    
    def detect_import_loops(self) -> List[List[str]]:
        """Detect circular import dependencies."""
        # Build dependency graph
        graph = defaultdict(list)
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        for file in files:
            imports = getattr(file, 'imports', [])
            if hasattr(imports, '__iter__'):
                imports_list = list(imports)
                for import_stmt in imports_list:
                    target = getattr(import_stmt, 'target_file', None)
                    if target and not getattr(import_stmt, 'is_external', False):
                        graph[file.path].append(target)
        
        # Find cycles using DFS
        def find_cycles():
            visited = set()
            rec_stack = set()
            cycles = []
            
            def dfs(node, path):
                if node in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    cycles.append(cycle)
                    return
                
                if node in visited:
                    return
                
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in graph.get(node, []):
                    dfs(neighbor, path[:])
                
                rec_stack.remove(node)
                path.pop()
            
            for node in graph:
                if node not in visited:
                    dfs(node, [])
            
            return cycles
        
        return find_cycles()
    
    def resolve_symbol_usages(self, symbol_name: str) -> Dict[str, Any]:
        """Find all usages of a specific symbol across the codebase."""
        usages: Dict[str, Any] = {
            "symbol_name": symbol_name,
            "definitions": [],
            "usages": [],
            "total_usages": 0
        }
        
        # Find symbol definitions
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        for file in files:
            symbols = getattr(file, 'symbols', [])
            if hasattr(symbols, '__iter__'):
                symbols_list = list(symbols)
                for symbol in symbols_list:
                    if getattr(symbol, 'name', '') == symbol_name:
                        usages["definitions"].append({
                            "file": file.path,
                            "line": getattr(symbol, 'line', 0),
                            "type": getattr(symbol, 'symbol_type', 'unknown')
                        })
        
        # Find symbol usages
        for file in files:
            imports = getattr(file, 'imports', [])
            if hasattr(imports, '__iter__'):
                imports_list = list(imports)
                for import_stmt in imports_list:
                    if getattr(import_stmt, 'symbol', '') == symbol_name:
                        usages["usages"].append({
                            "file": file.path,
                            "line": getattr(import_stmt, 'line', 0),
                            "context": "import"
                        })
        
        usages["total_usages"] = len(usages["usages"])
        return usages
    
    def get_symbol_dependencies(self, symbol_name: str, depth: int = 1) -> Dict[str, Any]:
        """
        Get dependencies of a symbol up to a specified depth.
        
        Args:
            symbol_name: Name of the symbol to analyze
            depth: How deep to traverse dependencies
            
        Returns:
            Dictionary containing dependency tree
        """
        symbol = self.codebase.get_symbol(symbol_name)
        if not symbol:
            return {"error": f"Symbol not found: {symbol_name}"}
        
        def get_deps_recursive(sym, current_depth, visited):
            if current_depth <= 0 or sym.name in visited:
                return []
            
            visited.add(sym.name)
            deps = []
            
            if hasattr(sym, 'dependencies'):
                for dep in sym.dependencies:
                    if hasattr(dep, 'name'):
                        dep_info = {
                            "name": dep.name,
                            "type": str(type(dep).__name__),
                            "dependencies": get_deps_recursive(dep, current_depth - 1, visited.copy())
                        }
                        deps.append(dep_info)
            
            return deps
        
        return {
            "symbol_name": symbol_name,
            "dependencies": get_deps_recursive(symbol, depth, set())
        }
    
    def find_unused_symbols(self) -> List[Dict[str, Any]]:
        """Find symbols that are defined but never used."""
        unused_symbols = []
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        for file in files:
            symbols = getattr(file, 'symbols', [])
            if hasattr(symbols, '__iter__'):
                symbols_list = list(symbols)
                for symbol in symbols_list:
                    symbol_name = getattr(symbol, 'name', '')
                    if symbol_name:
                        # Check if symbol is used anywhere
                        is_used = False
                        for other_file in files:
                            if other_file != file:
                                imports = getattr(other_file, 'imports', [])
                                if hasattr(imports, '__iter__'):
                                    imports_list = list(imports)
                                    for import_stmt in imports_list:
                                        if getattr(import_stmt, 'symbol', '') == symbol_name:
                                            is_used = True
                                            break
                                    if is_used:
                                        break
                        
                        if not is_used:
                            unused_symbols.append({
                                "name": symbol_name,
                                "file": file.path,
                                "type": getattr(symbol, 'symbol_type', 'unknown'),
                                "line": getattr(symbol, 'line', 0)
                            })
        
        return unused_symbols

    def get_external_dependencies(self) -> Dict[str, Any]:
        """Get information about external dependencies."""
        dep_info: Dict[str, Any] = {
            "total_external_modules": 0,
            "external_modules": [],
            "import_frequency": {},
            "files_using_external": []
        }
        
        external_modules = set()
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        for file in files:
            imports = getattr(file, 'imports', [])
            file_externals = []
            
            if hasattr(imports, '__iter__'):
                imports_list = list(imports)
                for import_stmt in imports_list:
                    if getattr(import_stmt, 'is_external', False):
                        module = getattr(import_stmt, 'module', 'unknown')
                        external_modules.add(module)
                        file_externals.append(module)
                        
                        # Count frequency
                        if module in dep_info["import_frequency"]:
                            dep_info["import_frequency"][module] += 1
                        else:
                            dep_info["import_frequency"][module] = 1
            
            if file_externals:
                dep_info["files_using_external"].append({
                    "file": file.path,
                    "external_modules": file_externals
                })
        
        dep_info["total_external_modules"] = len(external_modules)
        dep_info["external_modules"] = list(external_modules)
        
        return dep_info
    
    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """Get all symbols in the codebase."""
        symbols = []
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        for file in files:
            symbols.extend(getattr(file, 'symbols', []))
        
        return symbols
    
    def resolve_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """Resolve a specific symbol."""
        symbol = self.codebase.get_symbol(symbol_name)
        if not symbol:
            return {"error": f"Symbol not found: {symbol_name}"}
        
        return {
            "name": symbol.name,
            "line": getattr(symbol, 'line', 0),
            "type": getattr(symbol, 'symbol_type', 'unknown')
        }
