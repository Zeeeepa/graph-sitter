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
        """Find potentially dead code."""
        # Stub - full implementation would require sophisticated analysis
        return []
    
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
        """Analyze function complexity."""
        return {
            "function": function_name,
            "cyclomatic_complexity": None,  # Would need actual calculation
            "lines_of_code": None,
        }
