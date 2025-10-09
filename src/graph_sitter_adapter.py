"""Unified Graph-Sitter Adapter for code analysis.

Consolidates graph_sitter_analysis.py and graph_sitter_backend.py
into a single coherent adapter.
"""

import logging
from typing import Any, Dict, List, Optional
from functools import lru_cache

from graph_sitter import Codebase
from graph_sitter.extensions.tools.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_function_summary,
    get_class_summary,
    get_symbol_summary
)
from graph_sitter.extensions.tools.reveal_symbol import reveal_symbol
from graph_sitter.extensions.tools.blast_radius import create_blast_radius_visualization
from graph_sitter.extensions.tools.call_trace import create_downstream_call_trace
from graph_sitter.extensions.tools.dependency_trace import create_dependencies_visualization

from protocols import GraphSitterAnalyzerProtocol
from analysis_utils import AnalysisError, setup_logger

logger = setup_logger(__name__)


class GraphSitterAdapter:
    """Unified adapter for graph-sitter based code analysis.
    
    Consolidates functionality from GraphSitterAnalyzer and AnalysisEngine.
    Implements GraphSitterAnalyzerProtocol for type safety.
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize adapter with codebase."""
        self.codebase = codebase
        self._analysis_cache: Dict[str, Any] = {}
        self._visualization_cache: Dict[str, Any] = {}
        logger.info(f"Initialized GraphSitterAdapter for: {codebase.path}")
    
    # Core Analysis Methods (Protocol Implementation)
    
    @lru_cache(maxsize=1)
    def get_codebase_overview(self) -> Dict[str, Any]:
        """Get comprehensive overview of codebase structure.
        
        Returns:
            Dictionary with:
                - summary: str - High-level summary
                - files_count: int
                - functions_count: int
                - classes_count: int
                - symbols_count: int
                - imports_count: int
        """
        try:
            summary_str = get_codebase_summary(self.codebase)
            
            overview = {
                "summary": summary_str,
                "files_count": len(list(self.codebase.files)),
                "functions_count": len(list(self.codebase.functions)),
                "classes_count": len(list(self.codebase.classes)),
                "symbols_count": len(list(self.codebase.symbols)),
                "imports_count": len(list(self.codebase.imports)),
                "external_modules_count": len(list(self.codebase.external_modules)),
            }
            
            logger.debug(f"Codebase overview: {overview['files_count']} files")
            return overview
            
        except Exception as e:
            logger.error(f"Error getting codebase overview: {e}")
            return {"error": str(e)}
    
    def get_file_details(self, file_path: str) -> Dict[str, Any]:
        """Get detailed analysis of specific file.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            Dictionary with file metrics, symbols, dependencies
        """
        cache_key = f"file_details_{file_path}"
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        
        try:
            file_obj = self.codebase.get_file(file_path)
            summary = get_file_summary(file_obj)
            
            details = {
                "filepath": file_path,
                "summary": summary,
                "functions": [f.name for f in file_obj.functions],
                "classes": [c.name for c in file_obj.classes],
                "imports": [str(i) for i in file_obj.imports],
                "lines_of_code": len(file_obj.source.splitlines()) if hasattr(file_obj, "source") else 0,
            }
            
            self._analysis_cache[cache_key] = details
            return details
            
        except ValueError:
            return {"filepath": file_path, "error": "File not found"}
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {"filepath": file_path, "error": str(e)}
    
    def get_function_details(self, function_name: str, file_path: str) -> Dict[str, Any]:
        """Get detailed analysis of specific function.
        
        Args:
            function_name: Name of function
            file_path: File containing function
            
        Returns:
            Dictionary with function metrics and analysis
        """
        try:
            symbols = self.codebase.get_symbols(symbol_name=function_name)
            if not symbols:
                return {"function_name": function_name, "error": "Function not found"}
            
            # Find matching symbol
            target_symbol = None
            for symbol in symbols:
                if hasattr(symbol, 'file') and symbol.file.filepath == file_path:
                    target_symbol = symbol
                    break
            
            if not target_symbol:
                return {"function_name": function_name, "error": "Function not found in file"}
            
            summary = get_function_summary(target_symbol)
            
            return {
                "function_name": function_name,
                "filepath": file_path,
                "summary": summary,
                "line_number": getattr(target_symbol, 'line_number', None),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing function {function_name}: {e}")
            return {"function_name": function_name, "error": str(e)}
    
    def get_class_details(self, class_name: str, file_path: str) -> Dict[str, Any]:
        """Get detailed analysis of specific class."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=class_name)
            if not symbols:
                return {"class_name": class_name, "error": "Class not found"}
            
            target_symbol = None
            for symbol in symbols:
                if hasattr(symbol, 'file') and symbol.file.filepath == file_path:
                    target_symbol = symbol
                    break
            
            if not target_symbol:
                return {"class_name": class_name, "error": "Class not found in file"}
            
            summary = get_class_summary(target_symbol)
            
            return {
                "class_name": class_name,
                "filepath": file_path,
                "summary": summary,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing class {class_name}: {e}")
            return {"class_name": class_name, "error": str(e)}
    
    def get_symbol_details(self, symbol_name: str) -> Dict[str, Any]:
        """Get detailed analysis of symbol."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=symbol_name)
            if not symbols:
                return {"symbol_name": symbol_name, "error": "Symbol not found"}
            
            symbol = symbols[0]
            summary = get_symbol_summary(symbol)
            
            return {
                "symbol_name": symbol_name,
                "summary": summary,
                "type": type(symbol).__name__,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing symbol {symbol_name}: {e}")
            return {"symbol_name": symbol_name, "error": str(e)}
    
    # Visualization Methods
    
    def create_blast_radius_visualization(self, symbol_name: str) -> Dict[str, Any]:
        """Create visualization showing impact of changing a symbol."""
        try:
            result = create_blast_radius_visualization(
                codebase=self.codebase,
                symbol_name=symbol_name,
                max_depth=3
            )
            return {"symbol_name": symbol_name, "visualization": result}
        except Exception as e:
            logger.error(f"Error creating blast radius: {e}")
            return {"symbol_name": symbol_name, "error": str(e)}
    
    def create_call_trace_visualization(self, function_name: str) -> Dict[str, Any]:
        """Create visualization showing function call relationships."""
        try:
            result = create_downstream_call_trace(
                codebase=self.codebase,
                symbol_name=function_name,
                max_depth=3
            )
            return {"function_name": function_name, "visualization": result}
        except Exception as e:
            logger.error(f"Error creating call trace: {e}")
            return {"function_name": function_name, "error": str(e)}
    
    def create_dependency_trace_visualization(self, module_name: str) -> Dict[str, Any]:
        """Create visualization showing module dependencies."""
        try:
            result = create_dependencies_visualization(
                codebase=self.codebase,
                symbol_name=module_name
            )
            return {"module_name": module_name, "visualization": result}
        except Exception as e:
            logger.error(f"Error creating dependency trace: {e}")
            return {"module_name": module_name, "error": str(e)}
    
    def find_dead_code(self) -> List[Dict[str, Any]]:
        """Identify unused code that can be removed.
        
        TODO: Implement dead code detection algorithm
        """
        logger.warning("Dead code detection not yet implemented")
        return []


# Backward compatibility alias
GraphSitterAnalyzer = GraphSitterAdapter
