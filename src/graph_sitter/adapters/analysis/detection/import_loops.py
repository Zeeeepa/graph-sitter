"""
Import Loop Detection Module

Detects circular import dependencies in codebases.
Identifies problematic import cycles that can cause runtime errors.
"""

import os
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class ImportLoopDetector:
    """Detects circular import dependencies."""
    
    def __init__(self):
        self.import_graph = defaultdict(set)
        self.file_imports = defaultdict(list)
        self.cycles = []
        
    def detect_loops(self, codebase) -> List[Dict[str, Any]]:
        """Detect all import loops in the codebase."""
        try:
            if hasattr(codebase, 'files'):
                return self._detect_loops_graph_sitter(codebase)
            else:
                return self._detect_loops_ast(codebase)
        except Exception as e:
            logger.error(f"Import loop detection failed: {e}")
            return []
    
    def _detect_loops_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Detect import loops using graph-sitter."""
        # Build import graph
        self._build_import_graph_graph_sitter(codebase)
        
        # Find cycles
        cycles = self._find_cycles_in_graph()
        
        # Convert cycles to structured format
        return self._format_cycles(cycles)
    
    def _detect_loops_ast(self, file_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect import loops using AST data."""
        # Build import graph from AST data
        self._build_import_graph_ast(file_analyses)
        
        # Find cycles
        cycles = self._find_cycles_in_graph()
        
        # Convert cycles to structured format
        return self._format_cycles(cycles)
    
    def _build_import_graph_graph_sitter(self, codebase):
        """Build import dependency graph using graph-sitter."""
        self.import_graph.clear()
        self.file_imports.clear()
        
        for file in codebase.files:
            file_path = self._normalize_path(file.filepath)
            
            for import_stmt in getattr(file, 'imports', []):
                imported_module = self._resolve_import_path(import_stmt, file_path)
                
                if imported_module:
                    self.import_graph[file_path].add(imported_module)
                    self.file_imports[file_path].append({
                        'module': imported_module,
                        'line': getattr(import_stmt, 'line_number', 0),
                        'type': self._get_import_type(import_stmt),
                        'symbols': self._get_imported_symbols(import_stmt)
                    })
    
    def _build_import_graph_ast(self, file_analyses: Dict[str, Any]):
        """Build import dependency graph using AST data."""
        self.import_graph.clear()
        self.file_imports.clear()
        
        for file_path, analysis in file_analyses.items():
            normalized_path = self._normalize_path(file_path)
            
            for import_info in analysis.get('imports', []):
                imported_module = self._resolve_import_path_ast(import_info, file_path)
                
                if imported_module:
                    self.import_graph[normalized_path].add(imported_module)
                    self.file_imports[normalized_path].append({
                        'module': imported_module,
                        'line': import_info.get('line_number', 0),
                        'type': 'from_import' if import_info.get('is_relative') else 'import',
                        'symbols': import_info.get('symbols', [])
                    })
    
    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path for consistent comparison."""
        # Convert to relative path and normalize separators
        normalized = os.path.normpath(file_path)
        
        # Remove common prefixes
        for prefix in ['src/', './src/', '../src/', 'lib/', './lib/']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        return normalized
    
    def _resolve_import_path(self, import_stmt, current_file: str) -> Optional[str]:
        """Resolve import statement to actual file path."""
        try:
            # Get module name
            if hasattr(import_stmt, 'module_name'):
                module_name = import_stmt.module_name
            elif hasattr(import_stmt, 'resolved_symbol') and import_stmt.resolved_symbol:
                if hasattr(import_stmt.resolved_symbol, 'file'):
                    return self._normalize_path(import_stmt.resolved_symbol.file.filepath)
                else:
                    return None
            else:
                return None
            
            if not module_name:
                return None
            
            # Handle relative imports
            if hasattr(import_stmt, 'is_relative') and import_stmt.is_relative:
                return self._resolve_relative_import(module_name, current_file)
            
            # Handle absolute imports
            return self._resolve_absolute_import(module_name, current_file)
        
        except Exception as e:
            logger.debug(f"Failed to resolve import: {e}")
            return None
    
    def _resolve_import_path_ast(self, import_info: Dict[str, Any], current_file: str) -> Optional[str]:
        """Resolve import from AST data."""
        module_name = import_info.get('module', '')
        
        if not module_name:
            return None
        
        # Handle relative imports
        if import_info.get('is_relative', False):
            return self._resolve_relative_import(module_name, current_file)
        
        # Handle absolute imports
        return self._resolve_absolute_import(module_name, current_file)
    
    def _resolve_relative_import(self, module_name: str, current_file: str) -> Optional[str]:
        """Resolve relative import to file path."""
        try:
            current_dir = os.path.dirname(current_file)
            
            # Handle different levels of relative imports
            if module_name.startswith('..'):
                # Go up directories
                parts = module_name.split('.')
                up_levels = len([p for p in parts if p == ''])
                module_parts = [p for p in parts if p]
                
                target_dir = current_dir
                for _ in range(up_levels):
                    target_dir = os.path.dirname(target_dir)
                
                if module_parts:
                    target_path = os.path.join(target_dir, *module_parts)
                else:
                    target_path = target_dir
            else:
                # Same directory or subdirectory
                if module_name.startswith('.'):
                    module_name = module_name[1:]  # Remove leading dot
                
                if module_name:
                    target_path = os.path.join(current_dir, module_name.replace('.', os.sep))
                else:
                    target_path = current_dir
            
            # Try different file extensions
            for ext in ['.py', '__init__.py']:
                if ext == '__init__.py':
                    candidate = os.path.join(target_path, ext)
                else:
                    candidate = target_path + ext
                
                normalized = self._normalize_path(candidate)
                if self._file_exists_in_codebase(normalized):
                    return normalized
            
            return None
        
        except Exception as e:
            logger.debug(f"Failed to resolve relative import {module_name}: {e}")
            return None
    
    def _resolve_absolute_import(self, module_name: str, current_file: str) -> Optional[str]:
        """Resolve absolute import to file path."""
        try:
            # Convert module name to file path
            module_path = module_name.replace('.', os.sep)
            
            # Try different locations relative to current file
            current_dir = os.path.dirname(current_file)
            
            # Look for the module in various locations
            search_paths = [
                current_dir,
                os.path.dirname(current_dir),
                os.path.join(os.path.dirname(current_dir), 'src'),
                os.path.join(os.path.dirname(current_dir), 'lib'),
            ]
            
            for search_path in search_paths:
                # Try as file
                candidate = os.path.join(search_path, module_path + '.py')
                normalized = self._normalize_path(candidate)
                if self._file_exists_in_codebase(normalized):
                    return normalized
                
                # Try as package
                candidate = os.path.join(search_path, module_path, '__init__.py')
                normalized = self._normalize_path(candidate)
                if self._file_exists_in_codebase(normalized):
                    return normalized
            
            return None
        
        except Exception as e:
            logger.debug(f"Failed to resolve absolute import {module_name}: {e}")
            return None
    
    def _file_exists_in_codebase(self, file_path: str) -> bool:
        """Check if file exists in the analyzed codebase."""
        # This is a simplified check - in practice we'd check against
        # the actual files in the codebase
        return file_path.endswith('.py')
    
    def _get_import_type(self, import_stmt) -> str:
        """Get the type of import statement."""
        if hasattr(import_stmt, 'is_from_import') and import_stmt.is_from_import:
            return 'from_import'
        else:
            return 'import'
    
    def _get_imported_symbols(self, import_stmt) -> List[str]:
        """Get the symbols imported by the import statement."""
        if hasattr(import_stmt, 'imported_symbols'):
            return [s.name for s in import_stmt.imported_symbols]
        elif hasattr(import_stmt, 'imported_symbol') and import_stmt.imported_symbol:
            return [import_stmt.imported_symbol.name]
        else:
            return []
    
    def _find_cycles_in_graph(self) -> List[List[str]]:
        """Find all cycles in the import graph using DFS."""
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
        
        # Check all nodes for cycles
        for node in self.import_graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _format_cycles(self, cycles: List[List[str]]) -> List[Dict[str, Any]]:
        """Format cycles into structured data."""
        formatted_cycles = []
        
        for i, cycle in enumerate(cycles):
            cycle_info = {
                'id': f"cycle_{i + 1}",
                'type': 'circular_import',
                'severity': self._calculate_cycle_severity(cycle),
                'confidence': 0.9,
                'message': f"Circular import detected involving {len(cycle)} files",
                'files': cycle,
                'cycle_length': len(cycle),
                'imports': self._get_cycle_imports(cycle),
                'suggestions': self._get_cycle_suggestions(cycle)
            }
            
            formatted_cycles.append(cycle_info)
        
        return formatted_cycles
    
    def _calculate_cycle_severity(self, cycle: List[str]) -> str:
        """Calculate the severity of a cycle."""
        cycle_length = len(cycle)
        
        if cycle_length <= 2:
            return 'major'  # Direct circular imports are serious
        elif cycle_length <= 4:
            return 'minor'  # Longer cycles are less critical but still problematic
        else:
            return 'info'   # Very long cycles might be acceptable in some cases
    
    def _get_cycle_imports(self, cycle: List[str]) -> List[Dict[str, Any]]:
        """Get detailed import information for a cycle."""
        cycle_imports = []
        
        for i in range(len(cycle)):
            current_file = cycle[i]
            next_file = cycle[(i + 1) % len(cycle)]
            
            # Find the import that creates this edge
            for import_info in self.file_imports.get(current_file, []):
                if import_info['module'] == next_file:
                    cycle_imports.append({
                        'from_file': current_file,
                        'to_file': next_file,
                        'line': import_info['line'],
                        'type': import_info['type'],
                        'symbols': import_info['symbols']
                    })
                    break
        
        return cycle_imports
    
    def _get_cycle_suggestions(self, cycle: List[str]) -> List[str]:
        """Get suggestions for resolving a cycle."""
        suggestions = []
        
        if len(cycle) == 2:
            suggestions.append("Consider moving shared code to a separate module")
            suggestions.append("Use dependency injection to break the circular dependency")
            suggestions.append("Refactor one module to not depend on the other")
        else:
            suggestions.append("Analyze the dependency chain to find the weakest link")
            suggestions.append("Consider using interfaces or abstract base classes")
            suggestions.append("Move common functionality to a shared utility module")
        
        suggestions.append("Use lazy imports (import inside functions) as a temporary fix")
        
        return suggestions
    
    def generate_import_loop_report(self, loops: List[Dict[str, Any]]) -> str:
        """Generate a human-readable import loop report."""
        if not loops:
            return "✅ No circular imports detected!"
        
        report = []
        report.append("🔄 CIRCULAR IMPORT ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Summary
        report.append(f"📊 Total Circular Imports: {len(loops)}")
        
        severity_counts = {}
        for loop in loops:
            severity = loop.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in severity_counts.items():
            report.append(f"  • {severity.title()}: {count}")
        
        report.append("")
        
        # Details for each cycle
        for i, loop in enumerate(loops, 1):
            report.append(f"🔄 CYCLE #{i} ({loop.get('severity', 'unknown').upper()})")
            report.append("-" * 30)
            report.append(f"Files involved: {loop['cycle_length']}")
            
            # Show the cycle path
            files = loop['files']
            for j, file in enumerate(files):
                next_file = files[(j + 1) % len(files)]
                report.append(f"  {j + 1}. {file}")
                report.append(f"     ↓ imports")
            report.append(f"  {len(files) + 1}. {files[0]} (completes cycle)")
            
            # Show suggestions
            if loop.get('suggestions'):
                report.append("\n💡 Suggestions:")
                for suggestion in loop['suggestions'][:3]:  # Limit to top 3
                    report.append(f"  • {suggestion}")
            
            report.append("")
        
        # General recommendations
        report.append("🎯 GENERAL RECOMMENDATIONS")
        report.append("-" * 30)
        report.append("• Refactor code to reduce coupling between modules")
        report.append("• Use dependency injection patterns")
        report.append("• Move shared functionality to separate modules")
        report.append("• Consider using interfaces or abstract base classes")
        report.append("• Use lazy imports as a temporary workaround")
        
        return "\n".join(report)
    
    def get_resolution_strategies(self, loops: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Get specific resolution strategies for the detected cycles."""
        strategies = {
            'immediate': [],
            'refactoring': [],
            'architectural': []
        }
        
        for loop in loops:
            cycle_length = loop['cycle_length']
            severity = loop.get('severity', 'unknown')
            
            if severity == 'major':
                strategies['immediate'].append(
                    f"Break cycle in {' → '.join(loop['files'][:2])} using lazy imports"
                )
            
            if cycle_length == 2:
                strategies['refactoring'].append(
                    f"Extract common code from {loop['files'][0]} and {loop['files'][1]}"
                )
            
            if cycle_length > 3:
                strategies['architectural'].append(
                    f"Redesign module structure for {len(loop['files'])}-file cycle"
                )
        
        return strategies

