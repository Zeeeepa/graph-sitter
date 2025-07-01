"""
Dependency analysis implementation following graph-sitter.com patterns.

This module provides comprehensive dependency analysis including:
- Import resolution and hop-through-imports functionality
- Dependency mapping and visualization
- Circular dependency detection
- Dependency impact analysis
"""

import networkx as nx
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.import_resolution import Import


@dataclass
class DependencyPath:
    """Represents a dependency path between two symbols."""
    source: str
    target: str
    path: List[str]
    path_type: str  # 'import', 'call', 'inheritance', 'usage'
    strength: float  # 0.0 to 1.0
    is_circular: bool
    
    @property
    def path_description(self) -> str:
        """Get human-readable path description."""
        return " -> ".join(self.path)


@dataclass
class CircularDependency:
    """Represents a circular dependency."""
    cycle: List[str]
    cycle_type: str  # 'import', 'call', 'mixed'
    severity: str  # 'low', 'medium', 'high'
    impact_score: float
    suggested_fixes: List[str]
    
    @property
    def cycle_description(self) -> str:
        """Get human-readable cycle description."""
        return " -> ".join(self.cycle + [self.cycle[0]])


@dataclass
class DependencyMetrics:
    """Comprehensive dependency metrics."""
    total_dependencies: int
    import_dependencies: int
    call_dependencies: int
    inheritance_dependencies: int
    circular_dependencies: int
    max_dependency_depth: int
    average_dependencies_per_symbol: float
    most_depended_upon: str
    most_dependent: str
    dependency_clusters: int


@dataclass
class ImportAnalysis:
    """Analysis of import patterns and dependencies."""
    total_imports: int
    external_imports: int
    internal_imports: int
    relative_imports: int
    unused_imports: int
    circular_import_chains: List[List[str]]
    import_depth_map: Dict[str, int]
    
    @property
    def external_dependency_ratio(self) -> float:
        """Ratio of external to total imports."""
        return self.external_imports / max(self.total_imports, 1)


class DependencyAnalyzer:
    """
    Dependency analyzer following graph-sitter.com patterns.
    
    Provides comprehensive dependency analysis including:
    - Import resolution and tracking
    - Dependency graph construction
    - Circular dependency detection
    - Impact analysis
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize dependency analyzer with codebase."""
        self.codebase = codebase
        self.dependency_graph: Optional[nx.DiGraph] = None
        self.import_graph: Optional[nx.DiGraph] = None
        self._symbol_map: Dict[str, Symbol] = {}
        self._file_map: Dict[str, SourceFile] = {}
        self._build_symbol_maps()
    
    def _build_symbol_maps(self):
        """Build mappings for symbols and files."""
        for symbol in self.codebase.symbols:
            self._symbol_map[symbol.qualified_name] = symbol
            
        for file in self.codebase.files:
            self._file_map[file.filepath] = file
    
    def build_dependency_graph(self) -> nx.DiGraph:
        """
        Build comprehensive dependency graph.
        
        Based on graph-sitter.com dependency analysis patterns.
        """
        if self.dependency_graph is not None:
            return self.dependency_graph
        
        self.dependency_graph = nx.DiGraph()
        
        # Add all symbols as nodes
        for symbol in self.codebase.symbols:
            self.dependency_graph.add_node(
                symbol.qualified_name,
                symbol_obj=symbol,
                symbol_type=type(symbol).__name__,
                file=getattr(symbol, 'filepath', ''),
                is_external=self._is_external_symbol(symbol)
            )
        
        # Add dependency edges
        self._add_import_dependencies()
        self._add_call_dependencies()
        self._add_inheritance_dependencies()
        self._add_usage_dependencies()
        
        return self.dependency_graph
    
    def build_import_graph(self) -> nx.DiGraph:
        """Build import-specific dependency graph."""
        if self.import_graph is not None:
            return self.import_graph
        
        self.import_graph = nx.DiGraph()
        
        # Add files as nodes
        for file in self.codebase.files:
            self.import_graph.add_node(
                file.filepath,
                file_obj=file,
                file_type=self._get_file_type(file)
            )
        
        # Add import edges
        for file in self.codebase.files:
            if hasattr(file, 'imports'):
                for import_stmt in file.imports:
                    target_file = self._get_import_target_file(import_stmt)
                    if target_file:
                        self.import_graph.add_edge(
                            file.filepath,
                            target_file,
                            import_obj=import_stmt,
                            import_type=self._get_import_type(import_stmt),
                            is_external=self._is_external_import(import_stmt)
                        )
        
        return self.import_graph
    
    def analyze_imports(self) -> ImportAnalysis:
        """Analyze import patterns and dependencies."""
        if self.import_graph is None:
            self.build_import_graph()
        
        total_imports = 0
        external_imports = 0
        internal_imports = 0
        relative_imports = 0
        
        for file in self.codebase.files:
            if hasattr(file, 'imports'):
                for import_stmt in file.imports:
                    total_imports += 1
                    
                    if self._is_external_import(import_stmt):
                        external_imports += 1
                    else:
                        internal_imports += 1
                    
                    if self._is_relative_import(import_stmt):
                        relative_imports += 1
        
        # Find circular import chains
        circular_chains = self.find_circular_imports()
        
        # Calculate import depth map
        import_depth_map = self._calculate_import_depths()
        
        return ImportAnalysis(
            total_imports=total_imports,
            external_imports=external_imports,
            internal_imports=internal_imports,
            relative_imports=relative_imports,
            unused_imports=0,  # Would need additional analysis
            circular_import_chains=circular_chains,
            import_depth_map=import_depth_map
        )
    
    def find_dependency_paths(self, source: str, target: str, 
                            max_depth: int = 10) -> List[DependencyPath]:
        """Find all dependency paths between two symbols."""
        if self.dependency_graph is None:
            self.build_dependency_graph()
        
        paths = []
        
        try:
            all_paths = nx.all_simple_paths(
                self.dependency_graph, source, target, cutoff=max_depth
            )
            
            for path in all_paths:
                path_type = self._determine_path_type(path)
                strength = self._calculate_path_strength(path)
                is_circular = len(path) != len(set(path))
                
                paths.append(DependencyPath(
                    source=source,
                    target=target,
                    path=path,
                    path_type=path_type,
                    strength=strength,
                    is_circular=is_circular
                ))
        
        except nx.NetworkXNoPath:
            pass
        
        return sorted(paths, key=lambda p: (p.strength, -len(p.path)), reverse=True)
    
    def find_circular_dependencies(self) -> List[CircularDependency]:
        """Find all circular dependencies in the codebase."""
        if self.dependency_graph is None:
            self.build_dependency_graph()
        
        circular_deps = []
        
        try:
            # Find strongly connected components with more than one node
            sccs = [scc for scc in nx.strongly_connected_components(self.dependency_graph) 
                   if len(scc) > 1]
            
            for scc in sccs:
                # Find the actual cycle within the SCC
                subgraph = self.dependency_graph.subgraph(scc)
                cycles = list(nx.simple_cycles(subgraph))
                
                for cycle in cycles:
                    cycle_type = self._determine_cycle_type(cycle)
                    severity = self._assess_cycle_severity(cycle)
                    impact_score = self._calculate_cycle_impact(cycle)
                    suggested_fixes = self._suggest_cycle_fixes(cycle)
                    
                    circular_deps.append(CircularDependency(
                        cycle=cycle,
                        cycle_type=cycle_type,
                        severity=severity,
                        impact_score=impact_score,
                        suggested_fixes=suggested_fixes
                    ))
        
        except:
            pass
        
        return sorted(circular_deps, key=lambda cd: cd.impact_score, reverse=True)
    
    def find_circular_imports(self) -> List[List[str]]:
        """Find circular import dependencies."""
        if self.import_graph is None:
            self.build_import_graph()
        
        try:
            cycles = list(nx.simple_cycles(self.import_graph))
            return cycles
        except:
            return []
    
    def hop_through_imports(self, symbol_name: str, max_hops: int = 5) -> List[str]:
        """
        Follow import chain to find the ultimate source of a symbol.
        
        Based on graph-sitter.com hop-through-imports functionality.
        """
        visited = set()
        current_symbol = symbol_name
        path = [current_symbol]
        
        for _ in range(max_hops):
            if current_symbol in visited:
                break  # Circular import detected
            
            visited.add(current_symbol)
            
            # Find where this symbol is imported from
            import_source = self._find_symbol_import_source(current_symbol)
            if not import_source or import_source == current_symbol:
                break
            
            current_symbol = import_source
            path.append(current_symbol)
        
        return path
    
    def get_dependency_metrics(self) -> DependencyMetrics:
        """Get comprehensive dependency metrics."""
        if self.dependency_graph is None:
            self.build_dependency_graph()
        
        total_deps = self.dependency_graph.number_of_edges()
        
        # Count different types of dependencies
        import_deps = len([e for e in self.dependency_graph.edges(data=True) 
                          if e[2].get('dep_type') == 'import'])
        call_deps = len([e for e in self.dependency_graph.edges(data=True) 
                        if e[2].get('dep_type') == 'call'])
        inheritance_deps = len([e for e in self.dependency_graph.edges(data=True) 
                               if e[2].get('dep_type') == 'inheritance'])
        
        # Find circular dependencies
        circular_deps = len(self.find_circular_dependencies())
        
        # Calculate max dependency depth
        max_depth = 0
        for node in self.dependency_graph.nodes():
            try:
                depths = nx.single_source_shortest_path_length(
                    self.dependency_graph, node, cutoff=20
                )
                max_depth = max(max_depth, max(depths.values()) if depths else 0)
            except:
                pass
        
        # Calculate average dependencies per symbol
        avg_deps = total_deps / max(self.dependency_graph.number_of_nodes(), 1)
        
        # Find most depended upon and most dependent symbols
        most_depended = max(self.dependency_graph.nodes(), 
                           key=lambda n: self.dependency_graph.in_degree(n),
                           default="")
        most_dependent = max(self.dependency_graph.nodes(),
                            key=lambda n: self.dependency_graph.out_degree(n),
                            default="")
        
        # Count dependency clusters (weakly connected components)
        clusters = nx.number_weakly_connected_components(self.dependency_graph)
        
        return DependencyMetrics(
            total_dependencies=total_deps,
            import_dependencies=import_deps,
            call_dependencies=call_deps,
            inheritance_dependencies=inheritance_deps,
            circular_dependencies=circular_deps,
            max_dependency_depth=max_depth,
            average_dependencies_per_symbol=avg_deps,
            most_depended_upon=most_depended,
            most_dependent=most_dependent,
            dependency_clusters=clusters
        )
    
    def analyze_symbol_dependencies(self, symbol_name: str) -> Dict[str, Any]:
        """Analyze dependencies for a specific symbol."""
        if self.dependency_graph is None:
            self.build_dependency_graph()
        
        if symbol_name not in self.dependency_graph:
            return {}
        
        # Direct dependencies (what this symbol depends on)
        dependencies = list(self.dependency_graph.successors(symbol_name))
        
        # Direct dependents (what depends on this symbol)
        dependents = list(self.dependency_graph.predecessors(symbol_name))
        
        # Transitive dependencies
        try:
            transitive_deps = set(nx.descendants(self.dependency_graph, symbol_name))
            transitive_dependents = set(nx.ancestors(self.dependency_graph, symbol_name))
        except:
            transitive_deps = set()
            transitive_dependents = set()
        
        return {
            'symbol': symbol_name,
            'direct_dependencies': dependencies,
            'direct_dependents': dependents,
            'transitive_dependencies': list(transitive_deps),
            'transitive_dependents': list(transitive_dependents),
            'dependency_count': len(dependencies),
            'dependent_count': len(dependents),
            'impact_score': len(transitive_dependents),
            'complexity_score': len(transitive_deps)
        }
    
    # Private helper methods
    
    def _add_import_dependencies(self):
        """Add import-based dependencies to the graph."""
        for file in self.codebase.files:
            if hasattr(file, 'imports'):
                for import_stmt in file.imports:
                    if hasattr(import_stmt, 'imported_symbol'):
                        imported_symbol = import_stmt.imported_symbol
                        if hasattr(imported_symbol, 'qualified_name'):
                            # Add edge from importing file's symbols to imported symbol
                            for symbol in file.symbols if hasattr(file, 'symbols') else []:
                                self.dependency_graph.add_edge(
                                    symbol.qualified_name,
                                    imported_symbol.qualified_name,
                                    dep_type='import',
                                    import_obj=import_stmt
                                )
    
    def _add_call_dependencies(self):
        """Add function call dependencies to the graph."""
        for function in self.codebase.functions:
            if hasattr(function, 'function_calls'):
                for call in function.function_calls:
                    if hasattr(call, 'function_definition'):
                        called_func = call.function_definition
                        if hasattr(called_func, 'qualified_name'):
                            self.dependency_graph.add_edge(
                                function.qualified_name,
                                called_func.qualified_name,
                                dep_type='call',
                                call_obj=call
                            )
    
    def _add_inheritance_dependencies(self):
        """Add inheritance dependencies to the graph."""
        for class_def in self.codebase.classes:
            if hasattr(class_def, 'superclasses'):
                for parent_class in class_def.superclasses:
                    if hasattr(parent_class, 'qualified_name'):
                        self.dependency_graph.add_edge(
                            class_def.qualified_name,
                            parent_class.qualified_name,
                            dep_type='inheritance'
                        )
    
    def _add_usage_dependencies(self):
        """Add general usage dependencies to the graph."""
        for symbol in self.codebase.symbols:
            if hasattr(symbol, 'dependencies'):
                for dependency in symbol.dependencies:
                    if hasattr(dependency, 'qualified_name'):
                        self.dependency_graph.add_edge(
                            symbol.qualified_name,
                            dependency.qualified_name,
                            dep_type='usage'
                        )
    
    def _is_external_symbol(self, symbol: Symbol) -> bool:
        """Check if a symbol is external to the codebase."""
        # Simple heuristic: check if symbol file is in the codebase
        if hasattr(symbol, 'filepath'):
            return symbol.filepath not in self._file_map
        return False
    
    def _get_file_type(self, file: SourceFile) -> str:
        """Get file type based on extension."""
        if hasattr(file, 'name'):
            if file.name.endswith('.py'):
                return 'python'
            elif file.name.endswith(('.ts', '.tsx')):
                return 'typescript'
            elif file.name.endswith(('.js', '.jsx')):
                return 'javascript'
        return 'unknown'
    
    def _get_import_target_file(self, import_stmt) -> Optional[str]:
        """Get the target file path for an import statement."""
        if hasattr(import_stmt, 'imported_symbol'):
            imported_symbol = import_stmt.imported_symbol
            if hasattr(imported_symbol, 'filepath'):
                return imported_symbol.filepath
        return None
    
    def _get_import_type(self, import_stmt) -> str:
        """Determine the type of import statement."""
        # This would need to be implemented based on the actual import structure
        return 'module'  # Default
    
    def _is_external_import(self, import_stmt) -> bool:
        """Check if an import is external to the codebase."""
        target_file = self._get_import_target_file(import_stmt)
        return target_file is None or target_file not in self._file_map
    
    def _is_relative_import(self, import_stmt) -> bool:
        """Check if an import is a relative import."""
        # This would need to be implemented based on import syntax
        if hasattr(import_stmt, 'source'):
            return import_stmt.source.startswith('.')
        return False
    
    def _calculate_import_depths(self) -> Dict[str, int]:
        """Calculate import depth for each file."""
        if self.import_graph is None:
            self.build_import_graph()
        
        depth_map = {}
        
        for file_path in self.import_graph.nodes():
            try:
                # Calculate the longest path from this file
                lengths = nx.single_source_shortest_path_length(
                    self.import_graph, file_path, cutoff=20
                )
                depth_map[file_path] = max(lengths.values()) if lengths else 0
            except:
                depth_map[file_path] = 0
        
        return depth_map
    
    def _determine_path_type(self, path: List[str]) -> str:
        """Determine the primary type of a dependency path."""
        if self.dependency_graph is None:
            return 'unknown'
        
        edge_types = []
        for i in range(len(path) - 1):
            edge_data = self.dependency_graph.get_edge_data(path[i], path[i + 1])
            if edge_data:
                edge_types.append(edge_data.get('dep_type', 'unknown'))
        
        # Return the most common edge type
        if edge_types:
            return max(set(edge_types), key=edge_types.count)
        return 'unknown'
    
    def _calculate_path_strength(self, path: List[str]) -> float:
        """Calculate the strength of a dependency path."""
        # Simple heuristic: shorter paths are stronger
        base_strength = 1.0 / max(len(path), 1)
        
        # Adjust based on path type
        path_type = self._determine_path_type(path)
        type_multipliers = {
            'import': 1.0,
            'call': 0.8,
            'inheritance': 0.9,
            'usage': 0.6
        }
        
        return base_strength * type_multipliers.get(path_type, 0.5)
    
    def _determine_cycle_type(self, cycle: List[str]) -> str:
        """Determine the type of a circular dependency."""
        return self._determine_path_type(cycle)
    
    def _assess_cycle_severity(self, cycle: List[str]) -> str:
        """Assess the severity of a circular dependency."""
        cycle_length = len(cycle)
        
        if cycle_length <= 2:
            return 'high'  # Direct circular dependency
        elif cycle_length <= 4:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_cycle_impact(self, cycle: List[str]) -> float:
        """Calculate the impact score of a circular dependency."""
        # Impact is based on cycle length and node importance
        cycle_length = len(cycle)
        
        # Calculate average node importance (in-degree + out-degree)
        avg_importance = 0
        for node in cycle:
            if node in self.dependency_graph:
                importance = (self.dependency_graph.in_degree(node) + 
                            self.dependency_graph.out_degree(node))
                avg_importance += importance
        
        avg_importance /= max(cycle_length, 1)
        
        # Higher impact for shorter cycles and more important nodes
        return (10.0 / cycle_length) * (avg_importance / 10.0)
    
    def _suggest_cycle_fixes(self, cycle: List[str]) -> List[str]:
        """Suggest fixes for a circular dependency."""
        suggestions = []
        
        cycle_type = self._determine_cycle_type(cycle)
        
        if cycle_type == 'import':
            suggestions.append("Consider using dependency injection")
            suggestions.append("Move shared code to a separate module")
            suggestions.append("Use lazy imports")
        elif cycle_type == 'inheritance':
            suggestions.append("Consider composition over inheritance")
            suggestions.append("Extract common interface or base class")
        elif cycle_type == 'call':
            suggestions.append("Use callback functions or events")
            suggestions.append("Implement observer pattern")
            suggestions.append("Extract shared functionality")
        
        return suggestions
    
    def _find_symbol_import_source(self, symbol_name: str) -> Optional[str]:
        """Find where a symbol is imported from."""
        # This would need to traverse the import graph to find the source
        # For now, return None as this requires more sophisticated analysis
        return None

