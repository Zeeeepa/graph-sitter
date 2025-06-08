"""
Graph-Sitter Resolution Module

Consolidated resolution features for Tree-sitter symbol resolution, import analysis,
and dependency tracking. Provides advanced resolution capabilities based on official
Tree-sitter patterns and graph-based analysis.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from collections import defaultdict
from pathlib import Path

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.enums import SymbolType, EdgeType


class Resolve:
    """
    Unified Resolution Interface
    
    Consolidates all resolution features for Tree-sitter symbol resolution,
    import analysis, and dependency tracking into a comprehensive system.
    """
    
    def __init__(self, codebase: Optional[Codebase] = None):
        """
        Initialize the Resolution system.
        
        Args:
            codebase: Optional codebase to analyze. Can be set later.
        """
        self.codebase = codebase
        self.resolution_cache = {}
        self._symbol_index = {}
        self._import_index = {}
        self._dependency_graph = None
    
    def set_codebase(self, codebase: Codebase) -> None:
        """
        Set the codebase for resolution.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.resolution_cache.clear()
        self._symbol_index.clear()
        self._import_index.clear()
        self._dependency_graph = None
        self._build_indices()
    
    def _build_indices(self) -> None:
        """Build internal indices for fast resolution."""
        if not self.codebase:
            return
        
        print("🔍 Building resolution indices...")
        
        # Build symbol index
        for symbol in self.codebase.symbols:
            self._symbol_index[symbol.name] = symbol
            
            # Index by file as well
            if hasattr(symbol, 'file') and symbol.file:
                file_key = f"{symbol.file.name}::{symbol.name}"
                self._symbol_index[file_key] = symbol
        
        # Build import index
        for imp in self.codebase.imports:
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                symbol = imp.imported_symbol
                if hasattr(symbol, 'name'):
                    self._import_index[symbol.name] = imp
        
        print(f"✅ Built indices: {len(self._symbol_index)} symbols, {len(self._import_index)} imports")
    
    def resolve_symbol(self, symbol_name: str, context_file: Optional[SourceFile] = None) -> Optional[Symbol]:
        """
        Resolve a symbol by name with optional file context.
        
        Args:
            symbol_name: Name of the symbol to resolve
            context_file: Optional file context for scoped resolution
            
        Returns:
            Optional[Symbol]: Resolved symbol or None if not found
        """
        if not self.codebase:
            raise ValueError("No codebase set for resolution")
        
        # Try exact match first
        if symbol_name in self._symbol_index:
            return self._symbol_index[symbol_name]
        
        # Try with file context
        if context_file:
            file_key = f"{context_file.name}::{symbol_name}"
            if file_key in self._symbol_index:
                return self._symbol_index[file_key]
        
        # Try fuzzy matching
        for key, symbol in self._symbol_index.items():
            if symbol_name in key or key.endswith(f"::{symbol_name}"):
                return symbol
        
        return None
    
    def resolve_import(self, import_name: str) -> Optional[Import]:
        """
        Resolve an import by name.
        
        Args:
            import_name: Name of the import to resolve
            
        Returns:
            Optional[Import]: Resolved import or None if not found
        """
        if not self.codebase:
            raise ValueError("No codebase set for resolution")
        
        return self._import_index.get(import_name)
    
    def get_symbol_usages(self, symbol: Symbol) -> List[Dict[str, Any]]:
        """
        Get all usages of a symbol with detailed context.
        
        Args:
            symbol: The symbol to find usages for
            
        Returns:
            List[Dict[str, Any]]: List of usage contexts
        """
        usages = []
        
        for usage in symbol.symbol_usages:
            usage_info = {
                'symbol_name': getattr(usage, 'name', 'unknown'),
                'symbol_type': getattr(usage, 'symbol_type', SymbolType.Unknown).name if hasattr(usage, 'symbol_type') else 'unknown',
                'file': getattr(usage, 'file', {}).get('name', 'unknown') if hasattr(usage, 'file') else 'unknown',
                'line': getattr(usage, 'span', {}).get('start', {}).get('row', 0) if hasattr(usage, 'span') else 0,
                'usage_type': 'direct'
            }
            usages.append(usage_info)
        
        # Also check import usages
        for imp in self.codebase.imports:
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol == symbol:
                usage_info = {
                    'symbol_name': symbol.name,
                    'symbol_type': symbol.symbol_type.name if hasattr(symbol, 'symbol_type') else 'unknown',
                    'file': getattr(imp, 'file', {}).get('name', 'unknown') if hasattr(imp, 'file') else 'unknown',
                    'line': getattr(imp, 'span', {}).get('start', {}).get('row', 0) if hasattr(imp, 'span') else 0,
                    'usage_type': 'import'
                }
                usages.append(usage_info)
        
        return usages
    
    def get_symbol_dependencies(self, symbol: Symbol) -> Dict[str, List[Symbol]]:
        """
        Get all dependencies of a symbol categorized by type.
        
        Args:
            symbol: The symbol to analyze dependencies for
            
        Returns:
            Dict[str, List[Symbol]]: Dependencies categorized by type
        """
        dependencies = {
            'functions': [],
            'classes': [],
            'variables': [],
            'imports': [],
            'external_modules': []
        }
        
        if hasattr(symbol, 'dependencies'):
            for dep in symbol.dependencies:
                if isinstance(dep, Function):
                    dependencies['functions'].append(dep)
                elif isinstance(dep, Class):
                    dependencies['classes'].append(dep)
                elif isinstance(dep, Symbol):
                    if hasattr(dep, 'symbol_type'):
                        if dep.symbol_type == SymbolType.Function:
                            dependencies['functions'].append(dep)
                        elif dep.symbol_type == SymbolType.Class:
                            dependencies['classes'].append(dep)
                        elif dep.symbol_type == SymbolType.GlobalVar:
                            dependencies['variables'].append(dep)
                elif isinstance(dep, Import):
                    dependencies['imports'].append(dep)
                elif isinstance(dep, ExternalModule):
                    dependencies['external_modules'].append(dep)
        
        return dependencies
    
    def analyze_import_patterns(self) -> Dict[str, Any]:
        """
        Analyze import patterns across the codebase.
        
        Returns:
            Dict[str, Any]: Import pattern analysis results
        """
        if not self.codebase:
            raise ValueError("No codebase set for resolution")
        
        print("🔍 Analyzing import patterns...")
        
        patterns = {
            'external_imports': defaultdict(int),
            'internal_imports': defaultdict(int),
            'import_frequency': defaultdict(int),
            'file_import_counts': defaultdict(int),
            'unused_imports': [],
            'circular_imports': [],
            'import_depth': defaultdict(int)
        }
        
        # Analyze each file's imports
        for file in self.codebase.files:
            file_import_count = 0
            
            for imp in file.imports:
                file_import_count += 1
                
                if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                    symbol = imp.imported_symbol
                    symbol_name = getattr(symbol, 'name', 'unknown')
                    
                    # Count import frequency
                    patterns['import_frequency'][symbol_name] += 1
                    
                    # Categorize import type
                    if isinstance(symbol, ExternalModule):
                        patterns['external_imports'][symbol_name] += 1
                    elif isinstance(symbol, SourceFile):
                        patterns['internal_imports'][symbol_name] += 1
                    
                    # Check if import is used
                    if hasattr(symbol, 'symbol_usages') and len(symbol.symbol_usages) == 0:
                        patterns['unused_imports'].append({
                            'import': symbol_name,
                            'file': file.name,
                            'line': getattr(imp, 'span', {}).get('start', {}).get('row', 0) if hasattr(imp, 'span') else 0
                        })
            
            patterns['file_import_counts'][file.name] = file_import_count
        
        # Detect circular imports
        patterns['circular_imports'] = self._detect_circular_imports()
        
        return dict(patterns)
    
    def _detect_circular_imports(self) -> List[List[str]]:
        """Detect circular import dependencies."""
        import_graph = defaultdict(set)
        
        # Build import dependency graph
        for file in self.codebase.files:
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol') and isinstance(imp.imported_symbol, SourceFile):
                    import_graph[file.name].add(imp.imported_symbol.name)
        
        # Detect cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in import_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in import_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def analyze_class_hierarchy(self, cls: Class) -> Dict[str, Any]:
        """
        Analyze the complete class hierarchy for a class.
        
        Args:
            cls: The class to analyze
            
        Returns:
            Dict[str, Any]: Complete hierarchy analysis
        """
        hierarchy = {
            'class_name': cls.name,
            'direct_parents': [],
            'all_ancestors': [],
            'direct_children': [],
            'all_descendants': [],
            'hierarchy_depth': 0,
            'method_resolution_order': [],
            'inherited_methods': [],
            'overridden_methods': []
        }
        
        # Get direct parents
        hierarchy['direct_parents'] = list(cls.parent_class_names)
        
        # Find all ancestors (recursive parent traversal)
        ancestors = set()
        to_visit = list(cls.parent_class_names)
        
        while to_visit:
            parent_name = to_visit.pop(0)
            if parent_name not in ancestors:
                ancestors.add(parent_name)
                
                # Find parent class and get its parents
                parent_class = self.resolve_symbol(parent_name)
                if parent_class and isinstance(parent_class, Class):
                    to_visit.extend(parent_class.parent_class_names)
        
        hierarchy['all_ancestors'] = list(ancestors)
        hierarchy['hierarchy_depth'] = len(ancestors)
        
        # Find direct children
        children = []
        for other_cls in self.codebase.classes:
            if cls.name in other_cls.parent_class_names:
                children.append(other_cls.name)
        
        hierarchy['direct_children'] = children
        
        # Find all descendants (recursive child traversal)
        descendants = set()
        to_visit = children.copy()
        
        while to_visit:
            child_name = to_visit.pop(0)
            if child_name not in descendants:
                descendants.add(child_name)
                
                # Find child class and get its children
                child_class = self.resolve_symbol(child_name)
                if child_class and isinstance(child_class, Class):
                    for other_cls in self.codebase.classes:
                        if child_class.name in other_cls.parent_class_names:
                            to_visit.append(other_cls.name)
        
        hierarchy['all_descendants'] = list(descendants)
        
        # Analyze method inheritance and overriding
        class_methods = {method.name for method in cls.methods}
        
        for ancestor_name in ancestors:
            ancestor_class = self.resolve_symbol(ancestor_name)
            if ancestor_class and isinstance(ancestor_class, Class):
                ancestor_methods = {method.name for method in ancestor_class.methods}
                
                # Find inherited methods
                for method_name in ancestor_methods:
                    if method_name not in class_methods:
                        hierarchy['inherited_methods'].append({
                            'method_name': method_name,
                            'inherited_from': ancestor_name
                        })
                
                # Find overridden methods
                for method_name in ancestor_methods.intersection(class_methods):
                    hierarchy['overridden_methods'].append({
                        'method_name': method_name,
                        'overridden_from': ancestor_name
                    })
        
        return hierarchy
    
    def get_file_dependencies(self, file: SourceFile) -> Dict[str, Any]:
        """
        Get comprehensive dependency analysis for a file.
        
        Args:
            file: The file to analyze
            
        Returns:
            Dict[str, Any]: Complete file dependency analysis
        """
        dependencies = {
            'file_name': file.name,
            'outbound_imports': [],
            'inbound_imports': [],
            'symbol_exports': [],
            'symbol_imports': [],
            'external_dependencies': [],
            'internal_dependencies': [],
            'dependency_depth': 0,
            'circular_dependencies': []
        }
        
        # Analyze outbound imports
        for imp in file.imports:
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                symbol = imp.imported_symbol
                import_info = {
                    'symbol_name': getattr(symbol, 'name', 'unknown'),
                    'import_type': type(symbol).__name__,
                    'is_external': isinstance(symbol, ExternalModule),
                    'line': getattr(imp, 'span', {}).get('start', {}).get('row', 0) if hasattr(imp, 'span') else 0
                }
                
                dependencies['outbound_imports'].append(import_info)
                
                if isinstance(symbol, ExternalModule):
                    dependencies['external_dependencies'].append(symbol.name)
                elif isinstance(symbol, SourceFile):
                    dependencies['internal_dependencies'].append(symbol.name)
        
        # Find inbound imports (files that import this file)
        for other_file in self.codebase.files:
            if other_file != file:
                for imp in other_file.imports:
                    if (hasattr(imp, 'imported_symbol') and 
                        imp.imported_symbol == file):
                        dependencies['inbound_imports'].append({
                            'importing_file': other_file.name,
                            'line': getattr(imp, 'span', {}).get('start', {}).get('row', 0) if hasattr(imp, 'span') else 0
                        })
        
        # Analyze symbol exports and imports
        for symbol in file.symbols:
            symbol_info = {
                'symbol_name': symbol.name,
                'symbol_type': getattr(symbol, 'symbol_type', SymbolType.Unknown).name if hasattr(symbol, 'symbol_type') else 'unknown',
                'usage_count': len(symbol.symbol_usages),
                'line': getattr(symbol, 'span', {}).get('start', {}).get('row', 0) if hasattr(symbol, 'span') else 0
            }
            
            # Check if symbol is used outside this file
            external_usage = False
            for usage in symbol.symbol_usages:
                if hasattr(usage, 'file') and usage.file != file:
                    external_usage = True
                    break
            
            if external_usage:
                dependencies['symbol_exports'].append(symbol_info)
            else:
                dependencies['symbol_imports'].append(symbol_info)
        
        # Calculate dependency depth (max depth of import chain)
        dependencies['dependency_depth'] = self._calculate_dependency_depth(file)
        
        # Check for circular dependencies involving this file
        all_cycles = self._detect_circular_imports()
        file_cycles = [cycle for cycle in all_cycles if file.name in cycle]
        dependencies['circular_dependencies'] = file_cycles
        
        return dependencies
    
    def _calculate_dependency_depth(self, file: SourceFile, visited: Optional[Set[str]] = None) -> int:
        """Calculate the maximum dependency depth for a file."""
        if visited is None:
            visited = set()
        
        if file.name in visited:
            return 0  # Circular dependency, stop here
        
        visited.add(file.name)
        max_depth = 0
        
        for imp in file.imports:
            if hasattr(imp, 'imported_symbol') and isinstance(imp.imported_symbol, SourceFile):
                imported_file = imp.imported_symbol
                depth = 1 + self._calculate_dependency_depth(imported_file, visited.copy())
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def generate_resolution_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive resolution analysis report.
        
        Returns:
            Dict[str, Any]: Complete resolution analysis
        """
        if not self.codebase:
            raise ValueError("No codebase set for resolution")
        
        print("🔍 Generating comprehensive resolution report...")
        
        report = {
            'metadata': {
                'total_symbols': len(self._symbol_index),
                'total_imports': len(self._import_index),
                'total_files': len(list(self.codebase.files)),
                'analysis_timestamp': str(Path.cwd())  # Placeholder
            },
            'import_patterns': self.analyze_import_patterns(),
            'symbol_resolution_stats': self._get_symbol_resolution_stats(),
            'dependency_analysis': self._get_dependency_analysis(),
            'resolution_issues': self._find_resolution_issues(),
            'recommendations': self._generate_resolution_recommendations()
        }
        
        print("✅ Resolution report generated")
        return report
    
    def _get_symbol_resolution_stats(self) -> Dict[str, Any]:
        """Get statistics about symbol resolution."""
        stats = {
            'total_symbols': len(list(self.codebase.symbols)),
            'resolvable_symbols': 0,
            'unresolvable_symbols': 0,
            'symbol_types': defaultdict(int),
            'resolution_success_rate': 0.0
        }
        
        resolvable_count = 0
        for symbol in self.codebase.symbols:
            if hasattr(symbol, 'symbol_type'):
                stats['symbol_types'][symbol.symbol_type.name] += 1
            
            # Check if symbol can be resolved
            resolved = self.resolve_symbol(symbol.name)
            if resolved:
                resolvable_count += 1
        
        stats['resolvable_symbols'] = resolvable_count
        stats['unresolvable_symbols'] = stats['total_symbols'] - resolvable_count
        stats['resolution_success_rate'] = resolvable_count / max(stats['total_symbols'], 1)
        
        return dict(stats)
    
    def _get_dependency_analysis(self) -> Dict[str, Any]:
        """Get comprehensive dependency analysis."""
        analysis = {
            'total_dependencies': 0,
            'circular_dependencies': len(self._detect_circular_imports()),
            'max_dependency_depth': 0,
            'avg_dependencies_per_file': 0.0,
            'external_dependency_ratio': 0.0
        }
        
        total_deps = 0
        max_depth = 0
        external_deps = 0
        total_imports = 0
        
        for file in self.codebase.files:
            file_deps = len(file.imports)
            total_deps += file_deps
            total_imports += file_deps
            
            depth = self._calculate_dependency_depth(file)
            max_depth = max(max_depth, depth)
            
            # Count external dependencies
            for imp in file.imports:
                if (hasattr(imp, 'imported_symbol') and 
                    isinstance(imp.imported_symbol, ExternalModule)):
                    external_deps += 1
        
        file_count = len(list(self.codebase.files))
        analysis['total_dependencies'] = total_deps
        analysis['max_dependency_depth'] = max_depth
        analysis['avg_dependencies_per_file'] = total_deps / max(file_count, 1)
        analysis['external_dependency_ratio'] = external_deps / max(total_imports, 1)
        
        return analysis
    
    def _find_resolution_issues(self) -> List[Dict[str, Any]]:
        """Find potential resolution issues."""
        issues = []
        
        # Find unresolved symbols
        for symbol in self.codebase.symbols:
            if not self.resolve_symbol(symbol.name):
                issues.append({
                    'type': 'unresolved_symbol',
                    'symbol_name': symbol.name,
                    'file': getattr(symbol, 'file', {}).get('name', 'unknown') if hasattr(symbol, 'file') else 'unknown',
                    'severity': 'medium'
                })
        
        # Find unused imports
        import_patterns = self.analyze_import_patterns()
        for unused in import_patterns['unused_imports']:
            issues.append({
                'type': 'unused_import',
                'import_name': unused['import'],
                'file': unused['file'],
                'line': unused['line'],
                'severity': 'low'
            })
        
        # Find circular imports
        for cycle in import_patterns['circular_imports']:
            issues.append({
                'type': 'circular_import',
                'cycle': cycle,
                'severity': 'high'
            })
        
        return issues
    
    def _generate_resolution_recommendations(self) -> List[str]:
        """Generate recommendations for improving resolution."""
        recommendations = []
        
        # Analyze resolution stats
        stats = self._get_symbol_resolution_stats()
        if stats['resolution_success_rate'] < 0.9:
            recommendations.append(f"Improve symbol resolution - only {stats['resolution_success_rate']:.1%} of symbols are resolvable")
        
        # Analyze dependency issues
        dep_analysis = self._get_dependency_analysis()
        if dep_analysis['circular_dependencies'] > 0:
            recommendations.append(f"Resolve {dep_analysis['circular_dependencies']} circular dependencies")
        
        if dep_analysis['max_dependency_depth'] > 10:
            recommendations.append(f"Consider reducing dependency depth (current max: {dep_analysis['max_dependency_depth']})")
        
        if dep_analysis['external_dependency_ratio'] > 0.5:
            recommendations.append("High external dependency ratio - consider reducing external dependencies")
        
        # Analyze import patterns
        import_patterns = self.analyze_import_patterns()
        if len(import_patterns['unused_imports']) > 0:
            recommendations.append(f"Remove {len(import_patterns['unused_imports'])} unused imports")
        
        return recommendations


# Export main class
__all__ = ['Resolve']

