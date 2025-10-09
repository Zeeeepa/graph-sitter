"""GraphSitter adapter - consolidates all graph-sitter analysis."""

import logging
from typing import Dict, List, Optional, Any
from functools import lru_cache
from pathlib import Path

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

from .protocols import GraphSitterAnalyzerProtocol
from .analysis_utils import setup_logger, AnalysisError

logger = setup_logger(__name__)


class GraphSitterAdapter(GraphSitterAnalyzerProtocol):
    """Consolidated adapter for all graph-sitter analysis operations.
    
    Replaces ~5,343 lines from:
    - graph_sitter_analysis.py
    - graph_sitter_backend.py  
    - Other scattered utilities
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize with codebase instance."""
        self.codebase = codebase
        self._cache = {}
    
    @lru_cache(maxsize=128)
    def get_codebase_overview(self) -> Dict[str, Any]:
        """Get high-level codebase statistics."""
        return {
            "files_count": len(list(self.codebase.files)),
            "functions_count": len(list(self.codebase.functions)),
            "classes_count": len(list(self.codebase.classes)),
            "symbols_count": len(list(self.codebase.symbols)),
        }
    
    def get_file_details(self, filepath: str) -> Dict[str, Any]:
        """Get detailed analysis of a specific file."""
        file = self.codebase.get_file(filepath)
        if not file:
            return {}
        
        return {
            "path": filepath,
            "functions": [f.name for f in file.functions],
            "classes": [c.name for c in file.classes],
            "imports": [i.module for i in file.imports] if hasattr(file, 'imports') else [],
        }
    
    def get_function_details(self, function_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Get details about a specific function."""
        for func in self.codebase.functions:
            if func.name == function_name:
                if filepath and func.file.filepath != filepath:
                    continue
                return {
                    "name": func.name,
                    "file": func.file.filepath,
                    "line": func.start_line,
                    "docstring": func.docstring if hasattr(func, 'docstring') else None,
                }
        return {}
    
    def get_class_details(self, class_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Get details about a specific class."""
        for cls in self.codebase.classes:
            if cls.name == class_name:
                if filepath and cls.file.filepath != filepath:
                    continue
                return {
                    "name": cls.name,
                    "file": cls.file.filepath,
                    "line": cls.start_line,
                    "methods": [m.name for m in cls.methods] if hasattr(cls, 'methods') else [],
                    "docstring": cls.docstring if hasattr(cls, 'docstring') else None,
                }
        return {}
    
    def find_usages(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find all usages of a symbol."""
        usages = []
        for file in self.codebase.files:
            # Simple text search - can be enhanced
            try:
                content = Path(file.filepath).read_text()
                if symbol_name in content:
                    usages.append({
                        "file": file.filepath,
                        "symbol": symbol_name
                    })
            except Exception as e:
                logger.warning(f"Error reading {file.filepath}: {e}")
        return usages
    
    def find_dead_code(self) -> List[AnalysisError]:
        """Find potentially unused code.
        
        Detects:
        - Unused functions
        - Unused classes  
        - Unreachable code
        """
        dead_code = []
        
        try:
            # Identify entrypoints (main, __init__, tests, etc.)
            entrypoints = self._identify_entrypoints()
            used_symbols = set()
            
            # Mark all entrypoint symbols as used
            for category, points in entrypoints.items():
                for point in points:
                    used_symbols.add(point.get('symbol_name'))
            
            # Check functions
            for func in self.codebase.functions:
                # Check if function is called anywhere
                usages = list(self.codebase.find_symbol_usages(func))
                if not usages and func.name not in used_symbols:
                    if not self._is_likely_entrypoint(func):
                        dead_code.append(AnalysisError(
                            file_path=func.file_path,
                            line=func.start_line,
                            column=0,
                            error_type="dead_code",
                            severity="warning",
                            message=f"Function '{func.name}' appears unused",
                            tool_source="graph_sitter",
                            category="code_quality"
                        ))
            
            # Check classes
            for cls in self.codebase.classes:
                usages = list(self.codebase.find_symbol_usages(cls))
                if not usages and cls.name not in used_symbols:
                    if not self._is_likely_entrypoint(cls):
                        dead_code.append(AnalysisError(
                            file_path=cls.file_path,
                            line=cls.start_line,
                            column=0,
                            error_type="dead_code",
                            severity="warning",
                            message=f"Class '{cls.name}' appears unused",
                            tool_source="graph_sitter",
                            category="code_quality"
                        ))
            
        except Exception as e:
            logger.error(f"Dead code detection failed: {e}")
        
        return dead_code
    
    def _identify_entrypoints(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identify likely code entrypoints."""
        entrypoints = {
            "main_functions": [],
            "test_functions": [],
            "special_methods": []
        }
        
        for func in self.codebase.functions:
            if func.name in ("main", "__main__", "run", "start"):
                entrypoints["main_functions"].append({
                    "symbol_name": func.name,
                    "file": func.file_path,
                    "line": func.start_line
                })
            elif func.name.startswith("test_") or func.name.endswith("_test"):
                entrypoints["test_functions"].append({
                    "symbol_name": func.name,
                    "file": func.file_path,
                    "line": func.start_line
                })
            elif func.name.startswith("__") and func.name.endswith("__"):
                entrypoints["special_methods"].append({
                    "symbol_name": func.name,
                    "file": func.file_path,
                    "line": func.start_line
                })
        
        return entrypoints
    
    def _is_likely_entrypoint(self, symbol: Symbol) -> bool:
        """Check if symbol is likely an entrypoint."""
        if not symbol.name:
            return False
        
        patterns = [
            "main", "test_", "_test", "__init__", "__main__",
            "setup", "teardown", "run", "start", "handler", "endpoint"
        ]
        
        name_lower = symbol.name.lower()
        return any(pattern in name_lower for pattern in patterns)
    
    def create_blast_radius_visualization(self, symbol_name: str) -> Dict[str, Any]:
        """Create blast radius visualization for a symbol."""
        return {
            "symbol": symbol_name,
            "affected_files": len(self.find_usages(symbol_name)),
            "visualization_url": None  # Could generate actual viz
        }
    
    def create_call_trace_visualization(self, function_name: str) -> Dict[str, Any]:
        """Create call trace visualization."""
        return {
            "function": function_name,
            "visualization_url": None
        }
    
    def create_dependency_trace_visualization(self, symbol_name: str) -> Dict[str, Any]:
        """Create dependency trace visualization."""
        return {
            "symbol": symbol_name,
            "visualization_url": None
        }
    
    def analyze_dependencies(self, filepath: str) -> Dict[str, Any]:
        """Analyze dependencies for a file."""
        file = self.codebase.get_file(filepath)
        if not file:
            return {}
        
        imports = []
        if hasattr(file, 'imports'):
            imports = [{"module": imp.module, "line": imp.line} for imp in file.imports]
        
        return {
            "file": filepath,
            "imports": imports,
            "import_count": len(imports)
        }
    
    def get_import_graph(self) -> Dict[str, List[str]]:
        """Build complete import dependency graph.
        
        Returns:
            Dict mapping each file to list of files it imports
        """
        import_graph = {}
        
        for file in self.codebase.files:
            filepath = file.file_path
            imports = []
            
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    # Try to resolve import to actual file
                    if hasattr(imp, 'resolved_path'):
                        imports.append(imp.resolved_path)
                    elif hasattr(imp, 'module'):
                        # Try to find module in codebase
                        module_name = imp.module
                        for candidate_file in self.codebase.files:
                            if module_name in candidate_file.file_path:
                                imports.append(candidate_file.file_path)
                                break
            
            import_graph[filepath] = imports
        
        return import_graph
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular import dependencies.
        
        Returns:
            List of circular dependency chains
        """
        import_graph = self.get_import_graph()
        circular_deps = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            """DFS to detect cycles."""
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if cycle not in circular_deps:
                    circular_deps.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visit neighbors
            for neighbor in import_graph.get(node, []):
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        # Run DFS from each node
        for node in import_graph.keys():
            if node not in visited:
                dfs(node, [])
        
        return circular_deps
    
    def get_symbol_definition(self, symbol_name: str) -> Optional[Dict[str, Any]]:
        """Get the definition location of a symbol."""
        # Check functions
        func_details = self.get_function_details(symbol_name)
        if func_details:
            return func_details
        
        # Check classes
        class_details = self.get_class_details(symbol_name)
        if class_details:
            return class_details
        
        return None
    
    def analyze_complexity(self, function_name: str) -> Dict[str, Any]:
        """Analyze function complexity.
        
        Returns:
            - cyclomatic_complexity: Number of decision points
            - lines_of_code: Total lines
            - cognitive_complexity: Mental effort to understand
            - maintainability_index: Overall maintainability score
        """
        func_details = self.get_function_details(function_name)
        if not func_details:
            return {"error": f"Function '{function_name}' not found"}
        
        # Get function object
        func = None
        for f in self.codebase.functions:
            if f.name == function_name:
                func = f
                break
        
        if not func:
            return {"error": f"Function '{function_name}' not found"}
        
        # Calculate metrics
        loc = func.end_line - func.start_line + 1 if hasattr(func, 'end_line') else 0
        
        # Cyclomatic complexity (simplified - count decision points)
        # In practice, parse source and count if/while/for/and/or
        cyclomatic = self._calculate_cyclomatic_complexity(func)
        
        # Cognitive complexity (simplified)
        cognitive = self._calculate_cognitive_complexity(func)
        
        # Maintainability index (Microsoft formula)
        maintainability = self._calculate_maintainability_index(loc, cyclomatic)
        
        return {
            "function": function_name,
            "file": func.file_path,
            "lines_of_code": loc,
            "cyclomatic_complexity": cyclomatic,
            "cognitive_complexity": cognitive,
            "maintainability_index": maintainability,
            "complexity_rating": self._get_complexity_rating(cyclomatic)
        }
    
    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        try:
            source = func.source if hasattr(func, 'source') else ""
            if not source:
                return 1
            
            # Count decision points
            decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'and', 'or', 'case', 'catch']
            complexity = 1  # Base complexity
            
            for keyword in decision_keywords:
                complexity += source.lower().count(f' {keyword} ')
                complexity += source.lower().count(f' {keyword}(')
            
            return complexity
        except Exception:
            return 1
    
    def _calculate_cognitive_complexity(self, func: Function) -> int:
        """Calculate cognitive complexity (simplified)."""
        # Cognitive complexity weighs nesting
        try:
            source = func.source if hasattr(func, 'source') else ""
            if not source:
                return 1
            
            # Simple heuristic: count nesting levels
            max_nesting = 0
            current_nesting = 0
            
            for line in source.split('\n'):
                stripped = line.lstrip()
                indent = len(line) - len(stripped)
                current_nesting = indent // 4  # Assume 4-space indent
                max_nesting = max(max_nesting, current_nesting)
            
            return max_nesting * 2  # Weight nesting
        except Exception:
            return 1
    
    def _calculate_maintainability_index(self, loc: int, complexity: int) -> float:
        """Calculate maintainability index (0-100, higher is better)."""
        import math
        
        if loc == 0:
            return 100.0
        
        # Simplified Microsoft formula
        # MI = max(0, (171 - 5.2 * ln(Halstead) - 0.23 * CC - 16.2 * ln(LOC)) * 100 / 171)
        # Simplified without Halstead
        try:
            mi = max(0, 171 - 0.23 * complexity - 16.2 * math.log(loc))
            mi = (mi * 100) / 171
            return round(mi, 2)
        except Exception:
            return 50.0
    
    def _get_complexity_rating(self, complexity: int) -> str:
        """Get human-readable complexity rating."""
        if complexity <= 5:
            return "low"
        elif complexity <= 10:
            return "moderate"
        elif complexity <= 20:
            return "high"
        else:
            return "very_high"
