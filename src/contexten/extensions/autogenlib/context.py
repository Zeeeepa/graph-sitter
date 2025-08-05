"""Context providers for enhanced code generation using graph-sitter analysis."""

from typing import Dict, Any, List, Optional
import inspect
import os

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GraphSitterContextProvider:
    """Provides rich context for code generation using graph-sitter codebase analysis."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a graph-sitter codebase.
        
        Args:
            codebase: Graph-sitter codebase instance
        """
        self.codebase = codebase
    
    def get_context(
        self,
        fullname: str,
        caller_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive context for code generation.
        
        Args:
            fullname: Full module name being generated
            caller_info: Information about the calling code
            
        Returns:
            Dictionary containing context information
        """
        context = {
            "codebase_stats": self._get_codebase_stats(),
            "related_functions": self._find_related_functions(fullname),
            "dependencies": self._analyze_dependencies(fullname),
            "usages": self._find_usage_patterns(fullname),
            "similar_modules": self._find_similar_modules(fullname),
            "caller_analysis": self._analyze_caller(caller_info) if caller_info else None
        }
        
        return context
    
    def _get_codebase_stats(self) -> Dict[str, Any]:
        """Get general statistics about the codebase."""
        try:
            stats = {
                "total_functions": len(self.codebase.functions),
                "total_classes": len(self.codebase.classes),
                "total_files": len(self.codebase.files),
                "languages": list(set(f.language for f in self.codebase.files if hasattr(f, 'language')))
            }
            
            # Find most common patterns
            if self.codebase.functions:
                # Most called function
                most_called = max(
                    self.codebase.functions,
                    key=lambda f: len(f.call_sites) if hasattr(f, 'call_sites') else 0
                )
                stats["most_called_function"] = {
                    "name": most_called.name,
                    "call_count": len(most_called.call_sites) if hasattr(most_called, 'call_sites') else 0
                }
                
                # Functions with most calls
                most_calls = max(
                    self.codebase.functions,
                    key=lambda f: len(f.function_calls) if hasattr(f, 'function_calls') else 0
                )
                stats["most_calling_function"] = {
                    "name": most_calls.name,
                    "calls_made": len(most_calls.function_calls) if hasattr(most_calls, 'function_calls') else 0
                }
            
            return stats
        except Exception as e:
            logger.warning(f"Failed to get codebase stats: {e}")
            return {}
    
    def _find_related_functions(self, fullname: str) -> List[Dict[str, Any]]:
        """Find functions related to the requested module/function."""
        try:
            parts = fullname.split(".")
            if len(parts) < 2:
                return []
            
            module_name = parts[1]
            function_name = parts[2] if len(parts) > 2 else None
            
            related = []
            
            # Find functions with similar names
            for func in self.codebase.functions:
                if not hasattr(func, 'name'):
                    continue
                    
                # Check for name similarity
                if (module_name.lower() in func.name.lower() or 
                    (function_name and function_name.lower() in func.name.lower())):
                    
                    related.append({
                        "name": func.name,
                        "source": getattr(func, 'source', '')[:500],  # Limit source length
                        "filepath": getattr(func, 'filepath', ''),
                        "docstring": getattr(func, 'docstring', ''),
                        "parameters": self._extract_parameters(func)
                    })
                    
                    if len(related) >= 5:  # Limit to avoid overwhelming context
                        break
            
            return related
        except Exception as e:
            logger.warning(f"Failed to find related functions for {fullname}: {e}")
            return []
    
    def _analyze_dependencies(self, fullname: str) -> List[Dict[str, Any]]:
        """Analyze dependencies that might be relevant."""
        try:
            dependencies = []
            
            # Look for import patterns in the codebase
            for file in self.codebase.files:
                if not hasattr(file, 'imports'):
                    continue
                    
                for imp in file.imports:
                    if hasattr(imp, 'module_name') and imp.module_name:
                        # Check if this import might be relevant
                        parts = fullname.split(".")
                        if len(parts) > 1 and parts[1] in imp.module_name:
                            dependencies.append({
                                "module": imp.module_name,
                                "imported_names": getattr(imp, 'imported_names', []),
                                "filepath": getattr(file, 'filepath', ''),
                                "source": getattr(imp, 'source', '')[:200]
                            })
                            
                            if len(dependencies) >= 10:
                                break
            
            return dependencies
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies for {fullname}: {e}")
            return []
    
    def _find_usage_patterns(self, fullname: str) -> List[Dict[str, Any]]:
        """Find usage patterns in the codebase that might inform generation."""
        try:
            patterns = []
            parts = fullname.split(".")
            
            if len(parts) < 2:
                return []
            
            module_name = parts[1]
            function_name = parts[2] if len(parts) > 2 else None
            
            # Look for similar usage patterns
            for func in self.codebase.functions:
                if not hasattr(func, 'function_calls'):
                    continue
                    
                for call in func.function_calls:
                    if hasattr(call, 'name') and call.name:
                        # Check if this call pattern might be relevant
                        if (module_name.lower() in call.name.lower() or
                            (function_name and function_name.lower() in call.name.lower())):
                            
                            patterns.append({
                                "caller": func.name,
                                "called_function": call.name,
                                "source": getattr(call, 'source', '')[:200],
                                "context": getattr(func, 'source', '')[:300]
                            })
                            
                            if len(patterns) >= 5:
                                break
            
            return patterns
        except Exception as e:
            logger.warning(f"Failed to find usage patterns for {fullname}: {e}")
            return []
    
    def _find_similar_modules(self, fullname: str) -> List[Dict[str, Any]]:
        """Find modules with similar functionality."""
        try:
            similar = []
            parts = fullname.split(".")
            
            if len(parts) < 2:
                return []
            
            module_name = parts[1]
            
            # Group functions by file/module
            modules = {}
            for func in self.codebase.functions:
                if not hasattr(func, 'filepath'):
                    continue
                    
                filepath = func.filepath
                if filepath not in modules:
                    modules[filepath] = []
                modules[filepath].append(func)
            
            # Find modules with similar names or functionality
            for filepath, functions in modules.items():
                if module_name.lower() in os.path.basename(filepath).lower():
                    similar.append({
                        "filepath": filepath,
                        "function_count": len(functions),
                        "function_names": [f.name for f in functions if hasattr(f, 'name')][:10],
                        "sample_source": functions[0].source[:300] if functions and hasattr(functions[0], 'source') else ""
                    })
                    
                    if len(similar) >= 3:
                        break
            
            return similar
        except Exception as e:
            logger.warning(f"Failed to find similar modules for {fullname}: {e}")
            return []
    
    def _analyze_caller(self, caller_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the calling code to understand usage intent."""
        try:
            analysis = {
                "filename": caller_info.get("filename", ""),
                "code_length": len(caller_info.get("code", "")),
                "imports": [],
                "function_calls": [],
                "variable_assignments": []
            }
            
            code = caller_info.get("code", "")
            if not code:
                return analysis
            
            # Simple pattern matching for imports
            import re
            
            # Find imports
            import_pattern = r"(?:from\s+[\w.]+\s+)?import\s+[\w.,\s]+"
            imports = re.findall(import_pattern, code)
            analysis["imports"] = imports[:10]
            
            # Find function calls
            call_pattern = r"(\w+)\s*\("
            calls = re.findall(call_pattern, code)
            analysis["function_calls"] = list(set(calls))[:10]
            
            # Find variable assignments
            assign_pattern = r"(\w+)\s*="
            assignments = re.findall(assign_pattern, code)
            analysis["variable_assignments"] = list(set(assignments))[:10]
            
            return analysis
        except Exception as e:
            logger.warning(f"Failed to analyze caller: {e}")
            return {}
    
    def _extract_parameters(self, func) -> List[str]:
        """Extract parameter information from a function."""
        try:
            if hasattr(func, 'parameters'):
                return [str(p) for p in func.parameters]
            elif hasattr(func, 'source'):
                # Try to extract from source using regex
                source = func.source
                match = re.search(r"def\s+\w+\s*\((.*?)\):", source)
                if match:
                    params = match.group(1).strip()
                    if params:
                        return [p.strip() for p in params.split(",")]
            return []
        except Exception:
            return []

