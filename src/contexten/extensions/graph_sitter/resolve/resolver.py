"""
Resolve class for graph-sitter symbol resolution and import analysis

This module provides symbol resolution, import relationship analysis,
and dependency tracking functionality using the actual graph-sitter API.
"""

from graph_sitter import Codebase
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict, deque


class Resolve:
    """
    Resolve class providing symbol resolution and import relationship analysis.
    
    Usage example:
    
    from graph_sitter import Codebase
    from contexten.extensions.graph_sitter.resolve import Resolve
    
    codebase = Codebase("path/to/repo")
    resolver = Resolve(codebase)
    
    # Analyze import relationships
    import_analysis = resolver.analyze_imports()
    
    # Detect import loops
    loops = resolver.detect_import_loops()
    
    # Resolve symbol usages
    usages = resolver.resolve_symbol_usages("MyClass")
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize Resolve with a Codebase instance."""
        self.codebase = codebase
    
    def analyze_imports(self, file_path: str = None) -> Dict[str, Any]:
        """
        Analyze import relationships for a specific file or entire codebase.
        
        Args:
            file_path: If specified, analyze imports for specific file
            
        Returns:
            Dictionary containing import analysis results
        """
        if file_path:
            file = self.codebase.get_file(file_path)
            if not file:
                return {"error": f"File not found: {file_path}"}
            
            return self._analyze_file_imports(file)
        else:
            return self._analyze_codebase_imports()
    
    def _analyze_file_imports(self, file) -> Dict[str, Any]:
        """Analyze imports for a specific file."""
        imports_data = {
            "file": file.name,
            "outbound_imports": [],
            "inbound_imports": [],
            "symbols_defined": [],
            "external_modules": []
        }
        
        # Outbound imports (what this file imports)
        for import_stmt in file.imports:
            import_info = {
                "import_statement": str(import_stmt),
                "imported_symbol": import_stmt.imported_symbol.name if import_stmt.imported_symbol and hasattr(import_stmt.imported_symbol, 'name') else None,
                "is_external": hasattr(import_stmt.imported_symbol, 'is_external') and import_stmt.imported_symbol.is_external if import_stmt.imported_symbol else False
            }
            imports_data["outbound_imports"].append(import_info)
        
        # Symbols defined in this file
        for symbol in file.symbols:
            imports_data["symbols_defined"].append({
                "name": symbol.name,
                "type": str(symbol.symbol_type) if hasattr(symbol, 'symbol_type') else "unknown",
                "usages_count": len(symbol.usages) if hasattr(symbol, 'usages') else 0
            })
        
        # Find inbound imports (files that import from this file)
        for other_file in self.codebase.files:
            if other_file.name != file.name:
                for import_stmt in other_file.imports:
                    if (import_stmt.imported_symbol and 
                        hasattr(import_stmt.imported_symbol, 'file') and 
                        import_stmt.imported_symbol.file == file):
                        imports_data["inbound_imports"].append({
                            "from_file": other_file.name,
                            "imported_symbol": import_stmt.imported_symbol.name
                        })
        
        return imports_data
    
    def _analyze_codebase_imports(self) -> Dict[str, Any]:
        """Analyze imports for the entire codebase."""
        analysis = {
            "total_files": len(self.codebase.files),
            "total_imports": len(self.codebase.imports),
            "total_external_modules": len(self.codebase.external_modules),
            "files_with_imports": 0,
            "most_imported_symbols": [],
            "most_importing_files": [],
            "external_dependencies": []
        }
        
        # Count files with imports
        analysis["files_with_imports"] = len([f for f in self.codebase.files if f.imports])
        
        # Find most imported symbols
        symbol_import_count = defaultdict(int)
        for file in self.codebase.files:
            for import_stmt in file.imports:
                if import_stmt.imported_symbol and hasattr(import_stmt.imported_symbol, 'name'):
                    symbol_import_count[import_stmt.imported_symbol.name] += 1
        
        analysis["most_imported_symbols"] = sorted(
            symbol_import_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Find files with most imports
        file_import_count = [(f.name, len(f.imports)) for f in self.codebase.files]
        analysis["most_importing_files"] = sorted(
            file_import_count, 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # External dependencies
        analysis["external_dependencies"] = [
            {"name": ext_mod.name, "type": "external_module"}
            for ext_mod in self.codebase.external_modules
        ]
        
        return analysis
    
    def detect_import_loops(self) -> List[List[str]]:
        """
        Detect circular import dependencies in the codebase.
        
        Returns:
            List of import loops, where each loop is a list of file names
        """
        # Build import graph
        import_graph = defaultdict(set)
        
        for file in self.codebase.files:
            for import_stmt in file.imports:
                if (import_stmt.imported_symbol and 
                    hasattr(import_stmt.imported_symbol, 'file') and
                    import_stmt.imported_symbol.file != file):
                    import_graph[file.name].add(import_stmt.imported_symbol.file.name)
        
        # Find cycles using DFS
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
            
            for neighbor in import_graph[node]:
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for file_name in import_graph:
            if file_name not in visited:
                dfs(file_name, [])
        
        return cycles
    
    def resolve_symbol_usages(self, symbol_name: str) -> Dict[str, Any]:
        """
        Resolve all usages of a specific symbol across the codebase.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            Dictionary containing symbol usage information
        """
        symbol = self.codebase.get_symbol(symbol_name)
        if not symbol:
            return {"error": f"Symbol not found: {symbol_name}"}
        
        usage_info = {
            "symbol_name": symbol_name,
            "symbol_type": str(symbol.symbol_type) if hasattr(symbol, 'symbol_type') else "unknown",
            "defined_in": symbol.file.name if hasattr(symbol, 'file') else "unknown",
            "total_usages": len(symbol.usages) if hasattr(symbol, 'usages') else 0,
            "usage_locations": [],
            "imported_by": [],
            "dependencies": []
        }
        
        # Collect usage locations
        if hasattr(symbol, 'usages'):
            for usage in symbol.usages:
                if hasattr(usage, 'file') and hasattr(usage, 'name'):
                    usage_info["usage_locations"].append({
                        "file": usage.file.name,
                        "context": usage.name,
                        "type": str(type(usage).__name__)
                    })
        
        # Find imports of this symbol
        for file in self.codebase.files:
            for import_stmt in file.imports:
                if (import_stmt.imported_symbol and 
                    hasattr(import_stmt.imported_symbol, 'name') and
                    import_stmt.imported_symbol.name == symbol_name):
                    usage_info["imported_by"].append({
                        "file": file.name,
                        "import_statement": str(import_stmt)
                    })
        
        # Get dependencies
        if hasattr(symbol, 'dependencies'):
            usage_info["dependencies"] = [
                {"name": dep.name, "type": str(type(dep).__name__)}
                for dep in symbol.dependencies
                if hasattr(dep, 'name')
            ]
        
        return usage_info
    
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
        """
        Find symbols that are defined but never used in the codebase.
        
        Returns:
            List of unused symbols with their information
        """
        unused_symbols = []
        
        for symbol in self.codebase.symbols:
            usage_count = len(symbol.usages) if hasattr(symbol, 'usages') else 0
            
            # Check if symbol is imported anywhere
            is_imported = False
            for file in self.codebase.files:
                for import_stmt in file.imports:
                    if (import_stmt.imported_symbol and 
                        hasattr(import_stmt.imported_symbol, 'name') and
                        import_stmt.imported_symbol.name == symbol.name):
                        is_imported = True
                        break
                if is_imported:
                    break
            
            if usage_count == 0 and not is_imported:
                unused_symbols.append({
                    "name": symbol.name,
                    "type": str(symbol.symbol_type) if hasattr(symbol, 'symbol_type') else "unknown",
                    "file": symbol.file.name if hasattr(symbol, 'file') else "unknown"
                })
        
        return unused_symbols
    
    def get_external_dependencies(self) -> Dict[str, Any]:
        """
        Get detailed information about external dependencies.
        
        Returns:
            Dictionary containing external dependency analysis
        """
        external_deps = {
            "total_external_modules": len(self.codebase.external_modules),
            "dependencies": [],
            "usage_by_file": defaultdict(list)
        }
        
        # Collect external module information
        for ext_mod in self.codebase.external_modules:
            dep_info = {
                "name": ext_mod.name,
                "imported_by_files": []
            }
            
            # Find which files import this external module
            for file in self.codebase.files:
                for import_stmt in file.imports:
                    if (import_stmt.imported_symbol and 
                        import_stmt.imported_symbol == ext_mod):
                        dep_info["imported_by_files"].append(file.name)
                        external_deps["usage_by_file"][file.name].append(ext_mod.name)
            
            external_deps["dependencies"].append(dep_info)
        
        return external_deps

