"""Dependency analysis and import resolution following graph-sitter.com patterns."""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol

logger = logging.getLogger(__name__)


@dataclass
class DependencyPath:
    """Path between two symbols in the dependency graph."""
    source: Symbol
    target: Symbol
    path: List[Symbol]
    import_chain: List[Import]
    depth: int


@dataclass
class CircularDependency:
    """Circular dependency detection result."""
    symbols: List[Symbol]
    import_chain: List[Import]
    severity: str  # 'low', 'medium', 'high'
    description: str


@dataclass
class ImportAnalysis:
    """Analysis of import patterns."""
    total_imports: int
    external_imports: int
    internal_imports: int
    unused_imports: int
    circular_imports: int
    import_depth_avg: float
    most_imported_modules: List[Tuple[str, int]]
    import_complexity_score: float


class DependencyAnalyzer:
    """Advanced dependency analysis and import resolution."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self._build_dependency_graph()
    
    def _build_dependency_graph(self):
        """Build the dependency and import graphs."""
        try:
            # Build symbol dependency graph
            for symbol in self.codebase.symbols:
                symbol_id = f"{symbol.__class__.__name__}:{symbol.name}"
                
                # Add dependencies
                dependencies = getattr(symbol, 'dependencies', [])
                for dep in dependencies:
                    dep_id = f"{dep.__class__.__name__}:{getattr(dep, 'name', str(dep))}"
                    self.dependency_graph[symbol_id].add(dep_id)
            
            # Build import graph
            for import_stmt in self.codebase.imports:
                source_file = getattr(import_stmt, 'file', None)
                imported_symbol = getattr(import_stmt, 'imported_symbol', None)
                
                if source_file and imported_symbol:
                    source_id = source_file.filepath
                    target_id = getattr(imported_symbol, 'filepath', str(imported_symbol))
                    self.import_graph[source_id].add(target_id)
                    
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
    
    def hop_through_imports(self, symbol: Union[Import, Symbol], max_hops: int = 10) -> Union[Symbol, ExternalModule]:
        """Follow import chains to find the root symbol source."""
        try:
            current = symbol
            hops = 0
            visited = set()
            
            while isinstance(current, Import) and hops < max_hops:
                # Prevent infinite loops
                current_id = id(current)
                if current_id in visited:
                    break
                visited.add(current_id)
                
                imported_symbol = getattr(current, 'imported_symbol', None)
                if imported_symbol:
                    current = imported_symbol
                else:
                    break
                hops += 1
            
            return current
        except Exception as e:
            logger.error(f"Error hopping through imports: {e}")
            return symbol
    
    def find_dependency_paths(self, source: str, target: str, max_depth: int = 10) -> List[DependencyPath]:
        """Find dependency paths between two symbols."""
        try:
            paths = []
            visited = set()
            
            def dfs(current: str, target_id: str, path: List[str], depth: int):
                if depth > max_depth or current in visited:
                    return
                
                if current == target_id:
                    # Convert path to symbols
                    symbol_path = []
                    for symbol_id in path:
                        symbol_name = symbol_id.split(':')[-1]
                        symbol = self._find_symbol_by_name(symbol_name)
                        if symbol:
                            symbol_path.append(symbol)
                    
                    if symbol_path:
                        paths.append(DependencyPath(
                            source=symbol_path[0],
                            target=symbol_path[-1],
                            path=symbol_path,
                            import_chain=[],  # TODO: Build import chain
                            depth=depth
                        ))
                    return
                
                visited.add(current)
                
                for dependency in self.dependency_graph.get(current, set()):
                    path.append(dependency)
                    dfs(dependency, target_id, path, depth + 1)
                    path.pop()
                
                visited.remove(current)
            
            dfs(source, target, [source], 0)
            return paths
            
        except Exception as e:
            logger.error(f"Error finding dependency paths: {e}")
            return []
    
    def analyze_symbol_dependencies(self, symbol: Symbol) -> Dict[str, Any]:
        """Analyze dependencies for a specific symbol."""
        try:
            symbol_id = f"{symbol.__class__.__name__}:{symbol.name}"
            
            # Direct dependencies
            direct_deps = list(self.dependency_graph.get(symbol_id, set()))
            
            # Transitive dependencies (BFS)
            transitive_deps = set()
            queue = deque(direct_deps)
            visited = {symbol_id}
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                
                visited.add(current)
                transitive_deps.add(current)
                
                # Add dependencies of current
                for dep in self.dependency_graph.get(current, set()):
                    if dep not in visited:
                        queue.append(dep)
            
            # Reverse dependencies (who depends on this symbol)
            reverse_deps = []
            for sym_id, deps in self.dependency_graph.items():
                if symbol_id in deps:
                    reverse_deps.append(sym_id)
            
            return {
                'symbol': symbol.name,
                'direct_dependencies': len(direct_deps),
                'transitive_dependencies': len(transitive_deps),
                'reverse_dependencies': len(reverse_deps),
                'dependency_depth': self._calculate_dependency_depth(symbol_id),
                'is_leaf': len(direct_deps) == 0,
                'is_root': len(reverse_deps) == 0,
                'dependency_list': direct_deps[:10],  # Top 10
                'reverse_dependency_list': reverse_deps[:10]  # Top 10
            }
        except Exception as e:
            logger.error(f"Error analyzing symbol dependencies: {e}")
            return {}
    
    def find_circular_dependencies(self) -> List[CircularDependency]:
        """Detect circular dependencies using DFS."""
        try:
            circular_deps = []
            visited = set()
            rec_stack = set()
            
            def dfs(node: str, path: List[str]):
                if node in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    
                    # Convert to symbols
                    cycle_symbols = []
                    for symbol_id in cycle[:-1]:  # Exclude duplicate
                        symbol_name = symbol_id.split(':')[-1]
                        symbol = self._find_symbol_by_name(symbol_name)
                        if symbol:
                            cycle_symbols.append(symbol)
                    
                    if cycle_symbols:
                        severity = self._assess_circular_dependency_severity(cycle_symbols)
                        circular_deps.append(CircularDependency(
                            symbols=cycle_symbols,
                            import_chain=[],  # TODO: Build import chain
                            severity=severity,
                            description=f"Circular dependency involving {len(cycle_symbols)} symbols"
                        ))
                    return
                
                if node in visited:
                    return
                
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in self.dependency_graph.get(node, set()):
                    dfs(neighbor, path)
                
                path.pop()
                rec_stack.remove(node)
            
            # Check all nodes
            for node in self.dependency_graph:
                if node not in visited:
                    dfs(node, [])
            
            return circular_deps
            
        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
            return []
    
    def build_dependency_graph(self) -> Dict[str, Any]:
        """Create dependency graph representation."""
        try:
            # Prepare nodes
            nodes = []
            for symbol in self.codebase.symbols:
                symbol_id = f"{symbol.__class__.__name__}:{symbol.name}"
                dependencies = len(self.dependency_graph.get(symbol_id, set()))
                
                # Count reverse dependencies
                reverse_deps = sum(
                    1 for deps in self.dependency_graph.values()
                    if symbol_id in deps
                )
                
                nodes.append({
                    'id': symbol_id,
                    'name': symbol.name,
                    'type': symbol.__class__.__name__,
                    'dependencies': dependencies,
                    'reverse_dependencies': reverse_deps,
                    'filepath': getattr(symbol, 'filepath', 'unknown')
                })
            
            # Prepare edges
            edges = []
            for source, targets in self.dependency_graph.items():
                for target in targets:
                    edges.append({
                        'source': source,
                        'target': target,
                        'type': 'dependency'
                    })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'total_symbols': len(nodes),
                    'total_dependencies': len(edges),
                    'average_dependencies': len(edges) / len(nodes) if nodes else 0,
                    'circular_dependencies': len(self.find_circular_dependencies())
                }
            }
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
            return {'nodes': [], 'edges': [], 'metadata': {}}
    
    def analyze_imports(self) -> ImportAnalysis:
        """Analyze import patterns across the codebase."""
        try:
            imports = list(self.codebase.imports)
            external_modules = list(self.codebase.external_modules)
            
            # Categorize imports
            external_imports = 0
            internal_imports = 0
            
            for import_stmt in imports:
                imported_symbol = getattr(import_stmt, 'imported_symbol', None)
                if isinstance(imported_symbol, ExternalModule):
                    external_imports += 1
                else:
                    internal_imports += 1
            
            # Find unused imports
            unused_imports = self._find_unused_imports()
            
            # Find circular imports
            circular_imports = len(self._find_circular_imports())
            
            # Calculate import depth
            import_depths = []
            for import_stmt in imports:
                depth = self._calculate_import_depth(import_stmt)
                import_depths.append(depth)
            
            avg_import_depth = sum(import_depths) / len(import_depths) if import_depths else 0
            
            # Most imported modules
            module_counts = defaultdict(int)
            for import_stmt in imports:
                module_name = getattr(import_stmt, 'module', 'unknown')
                module_counts[module_name] += 1
            
            most_imported = sorted(
                module_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Import complexity score
            complexity_score = self._calculate_import_complexity()
            
            return ImportAnalysis(
                total_imports=len(imports),
                external_imports=external_imports,
                internal_imports=internal_imports,
                unused_imports=len(unused_imports),
                circular_imports=circular_imports,
                import_depth_avg=avg_import_depth,
                most_imported_modules=most_imported,
                import_complexity_score=complexity_score
            )
        except Exception as e:
            logger.error(f"Error analyzing imports: {e}")
            return ImportAnalysis(
                total_imports=0, external_imports=0, internal_imports=0,
                unused_imports=0, circular_imports=0, import_depth_avg=0.0,
                most_imported_modules=[], import_complexity_score=0.0
            )
    
    def resolve_import_chain(self, import_stmt: Import) -> List[Union[Import, Symbol, ExternalModule]]:
        """Resolve the complete import dependency chain."""
        try:
            chain = [import_stmt]
            current = import_stmt
            visited = set()
            
            while isinstance(current, Import):
                current_id = id(current)
                if current_id in visited:
                    break  # Prevent infinite loops
                visited.add(current_id)
                
                imported_symbol = getattr(current, 'imported_symbol', None)
                if imported_symbol:
                    chain.append(imported_symbol)
                    current = imported_symbol
                else:
                    break
            
            return chain
        except Exception as e:
            logger.error(f"Error resolving import chain: {e}")
            return [import_stmt]
    
    def find_import_cycles(self) -> List[List[str]]:
        """Find circular imports."""
        try:
            return self._find_circular_imports()
        except Exception as e:
            logger.error(f"Error finding import cycles: {e}")
            return []
    
    def analyze_import_depth(self) -> Dict[str, int]:
        """Calculate import depth for all files."""
        try:
            depths = {}
            for file in self.codebase.files:
                depth = 0
                file_imports = getattr(file, 'imports', [])
                
                for import_stmt in file_imports:
                    import_depth = self._calculate_import_depth(import_stmt)
                    depth = max(depth, import_depth)
                
                depths[file.filepath] = depth
            
            return depths
        except Exception as e:
            logger.error(f"Error analyzing import depth: {e}")
            return {}
    
    def optimize_import_structure(self) -> Dict[str, Any]:
        """Suggest import optimizations."""
        try:
            suggestions = {
                'unused_imports': self._find_unused_imports(),
                'circular_imports': self._find_circular_imports(),
                'redundant_imports': self._find_redundant_imports(),
                'missing_imports': self._find_missing_imports(),
                'optimization_score': 0.0
            }
            
            # Calculate optimization score
            total_issues = (
                len(suggestions['unused_imports']) +
                len(suggestions['circular_imports']) +
                len(suggestions['redundant_imports']) +
                len(suggestions['missing_imports'])
            )
            
            total_imports = len(list(self.codebase.imports))
            if total_imports > 0:
                suggestions['optimization_score'] = max(0.0, 1.0 - (total_issues / total_imports))
            
            return suggestions
        except Exception as e:
            logger.error(f"Error optimizing import structure: {e}")
            return {}
    
    def _calculate_dependency_depth(self, symbol_id: str, visited: Optional[Set[str]] = None) -> int:
        """Calculate the maximum dependency depth for a symbol."""
        if visited is None:
            visited = set()
        
        if symbol_id in visited:
            return 0  # Circular dependency
        
        visited.add(symbol_id)
        
        dependencies = self.dependency_graph.get(symbol_id, set())
        if not dependencies:
            return 0
        
        max_depth = 0
        for dep in dependencies:
            depth = self._calculate_dependency_depth(dep, visited.copy())
            max_depth = max(max_depth, depth + 1)
        
        return max_depth
    
    def _find_symbol_by_name(self, name: str) -> Optional[Symbol]:
        """Find a symbol by name."""
        try:
            for symbol in self.codebase.symbols:
                if symbol.name == name:
                    return symbol
            return None
        except Exception:
            return None
    
    def _assess_circular_dependency_severity(self, symbols: List[Symbol]) -> str:
        """Assess the severity of a circular dependency."""
        try:
            # Simple heuristic based on number of symbols and their types
            if len(symbols) > 5:
                return 'high'
            elif len(symbols) > 2:
                return 'medium'
            else:
                return 'low'
        except Exception:
            return 'low'
    
    def _find_unused_imports(self) -> List[Import]:
        """Find imports that are not used."""
        try:
            unused = []
            for import_stmt in self.codebase.imports:
                # Check if the imported symbol is used
                imported_symbol = getattr(import_stmt, 'imported_symbol', None)
                if imported_symbol:
                    usages = getattr(imported_symbol, 'usages', [])
                    if not usages:
                        unused.append(import_stmt)
            return unused
        except Exception as e:
            logger.warning(f"Error finding unused imports: {e}")
            return []
    
    def _find_circular_imports(self) -> List[List[str]]:
        """Find circular import patterns."""
        try:
            cycles = []
            visited = set()
            rec_stack = set()
            
            def dfs(node: str, path: List[str]):
                if node in rec_stack:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:]
                    cycles.append(cycle)
                    return
                
                if node in visited:
                    return
                
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in self.import_graph.get(node, set()):
                    dfs(neighbor, path)
                
                path.pop()
                rec_stack.remove(node)
            
            for node in self.import_graph:
                if node not in visited:
                    dfs(node, [])
            
            return cycles
        except Exception as e:
            logger.warning(f"Error finding circular imports: {e}")
            return []
    
    def _find_redundant_imports(self) -> List[Import]:
        """Find redundant or duplicate imports."""
        try:
            # Group imports by file and module
            file_imports = defaultdict(list)
            for import_stmt in self.codebase.imports:
                source_file = getattr(import_stmt, 'file', None)
                if source_file:
                    file_imports[source_file.filepath].append(import_stmt)
            
            redundant = []
            for filepath, imports in file_imports.items():
                # Check for duplicate imports
                seen_modules = set()
                for import_stmt in imports:
                    module = getattr(import_stmt, 'module', '')
                    if module in seen_modules:
                        redundant.append(import_stmt)
                    else:
                        seen_modules.add(module)
            
            return redundant
        except Exception as e:
            logger.warning(f"Error finding redundant imports: {e}")
            return []
    
    def _find_missing_imports(self) -> List[str]:
        """Find potentially missing imports."""
        try:
            # This is a simplified heuristic
            # In practice, you'd analyze undefined symbols
            missing = []
            
            for symbol in self.codebase.symbols:
                dependencies = getattr(symbol, 'dependencies', [])
                for dep in dependencies:
                    # Check if dependency has a corresponding import
                    dep_name = getattr(dep, 'name', '')
                    if dep_name and not self._has_import_for_symbol(dep_name):
                        missing.append(dep_name)
            
            return list(set(missing))  # Remove duplicates
        except Exception as e:
            logger.warning(f"Error finding missing imports: {e}")
            return []
    
    def _calculate_import_depth(self, import_stmt: Import) -> int:
        """Calculate the depth of an import chain."""
        try:
            depth = 0
            current = import_stmt
            visited = set()
            
            while isinstance(current, Import):
                current_id = id(current)
                if current_id in visited:
                    break
                visited.add(current_id)
                
                imported_symbol = getattr(current, 'imported_symbol', None)
                if imported_symbol and isinstance(imported_symbol, Import):
                    current = imported_symbol
                    depth += 1
                else:
                    break
            
            return depth
        except Exception:
            return 0
    
    def _calculate_import_complexity(self) -> float:
        """Calculate overall import complexity score."""
        try:
            imports = list(self.codebase.imports)
            if not imports:
                return 0.0
            
            # Factors contributing to complexity
            total_imports = len(imports)
            circular_imports = len(self._find_circular_imports())
            unused_imports = len(self._find_unused_imports())
            
            # Calculate complexity score (0-1, lower is better)
            complexity = (
                (circular_imports / total_imports) * 0.4 +
                (unused_imports / total_imports) * 0.3 +
                min(1.0, total_imports / 100.0) * 0.3  # Penalize too many imports
            )
            
            return min(1.0, complexity)
        except Exception:
            return 0.0
    
    def _has_import_for_symbol(self, symbol_name: str) -> bool:
        """Check if there's an import for a given symbol."""
        try:
            for import_stmt in self.codebase.imports:
                imported_symbol = getattr(import_stmt, 'imported_symbol', None)
                if imported_symbol and getattr(imported_symbol, 'name', '') == symbol_name:
                    return True
            return False
        except Exception:
            return False


# Convenience functions
def hop_through_imports(symbol: Union[Import, Symbol], max_hops: int = 10) -> Union[Symbol, ExternalModule]:
    """Follow import chains to find the root symbol source."""
    if hasattr(symbol, 'codebase'):
        analyzer = DependencyAnalyzer(symbol.codebase)
        return analyzer.hop_through_imports(symbol, max_hops)
    else:
        # Fallback for when codebase is not available
        current = symbol
        hops = 0
        while isinstance(current, Import) and hops < max_hops:
            imported_symbol = getattr(current, 'imported_symbol', None)
            if imported_symbol:
                current = imported_symbol
            else:
                break
            hops += 1
        return current


def find_dependency_paths(codebase: Codebase, source: str, target: str) -> List[DependencyPath]:
    """Find dependency paths between two symbols."""
    analyzer = DependencyAnalyzer(codebase)
    return analyzer.find_dependency_paths(source, target)


def analyze_symbol_dependencies(symbol: Symbol) -> Dict[str, Any]:
    """Analyze dependencies for a specific symbol."""
    if hasattr(symbol, 'codebase'):
        analyzer = DependencyAnalyzer(symbol.codebase)
        return analyzer.analyze_symbol_dependencies(symbol)
    return {}


def find_circular_dependencies(codebase: Codebase) -> List[CircularDependency]:
    """Detect circular dependencies."""
    analyzer = DependencyAnalyzer(codebase)
    return analyzer.find_circular_dependencies()


def build_dependency_graph(codebase: Codebase) -> Dict[str, Any]:
    """Create dependency graph representation."""
    analyzer = DependencyAnalyzer(codebase)
    return analyzer.build_dependency_graph()


def analyze_imports(codebase: Codebase) -> ImportAnalysis:
    """Analyze import patterns."""
    analyzer = DependencyAnalyzer(codebase)
    return analyzer.analyze_imports()

