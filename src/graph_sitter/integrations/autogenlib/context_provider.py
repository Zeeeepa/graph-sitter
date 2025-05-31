"""Context provider that enhances autogenlib with graph-sitter analysis."""

import ast
import inspect
from typing import Dict, Any, Optional, List
from pathlib import Path

from graph_sitter.core.interfaces.codebase import Codebase
from graph_sitter.python.interfaces.python_codebase import PythonCodebase
from graph_sitter.core.interfaces.symbol import Symbol
from .config import AutogenLibConfig


class GraphSitterContextProvider:
    """Provides enhanced context for autogenlib using graph-sitter analysis."""
    
    def __init__(self, config: AutogenLibConfig, codebase: Optional[Codebase] = None):
        self.config = config
        self.codebase = codebase
        
    def get_enhanced_context(
        self,
        module_name: str,
        function_name: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None,
        existing_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get enhanced context for code generation."""
        context = {
            "module_name": module_name,
            "function_name": function_name,
            "graph_sitter_analysis": {},
            "symbol_information": {},
            "dependencies": {},
            "patterns": {},
            "caller_analysis": {}
        }
        
        # Add caller analysis if available
        if caller_info:
            context["caller_analysis"] = self._analyze_caller_code(caller_info)
            
        # Add existing code analysis
        if existing_code:
            context["existing_code_analysis"] = self._analyze_existing_code(existing_code)
            
        # Add codebase context if available
        if self.codebase and self.config.use_graph_sitter_context:
            context["graph_sitter_analysis"] = self._get_codebase_analysis(module_name)
            context["symbol_information"] = self._get_symbol_information(module_name, function_name)
            context["dependencies"] = self._get_dependency_analysis(module_name)
            
        # Add pattern analysis
        context["patterns"] = self._get_pattern_suggestions(module_name, function_name)
        
        return context
        
    def _analyze_caller_code(self, caller_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the caller code using graph-sitter."""
        analysis = {
            "filename": caller_info.get("filename", ""),
            "imports": [],
            "function_calls": [],
            "variable_usage": [],
            "data_structures": [],
            "error_handling": []
        }
        
        code = caller_info.get("code", "")
        if not code:
            return analysis
            
        try:
            # Parse the code using AST
            tree = ast.parse(code)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "type": "import"
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        analysis["imports"].append({
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "type": "from_import"
                        })
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        analysis["function_calls"].append({
                            "function": node.func.id,
                            "args": len(node.args),
                            "kwargs": len(node.keywords)
                        })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            analysis["variable_usage"].append({
                                "name": target.id,
                                "type": "assignment"
                            })
                elif isinstance(node, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
                    analysis["data_structures"].append({
                        "type": type(node).__name__.lower(),
                        "line": getattr(node, "lineno", 0)
                    })
                elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                    analysis["error_handling"].append({
                        "type": type(node).__name__.lower(),
                        "line": getattr(node, "lineno", 0)
                    })
                    
        except SyntaxError as e:
            analysis["parse_error"] = str(e)
            
        return analysis
        
    def _analyze_existing_code(self, code: str) -> Dict[str, Any]:
        """Analyze existing code structure."""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "constants": [],
            "complexity": 0
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                        "docstring": ast.get_docstring(node),
                        "line": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "bases": [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                        "decorators": [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                        "docstring": ast.get_docstring(node),
                        "line": node.lineno
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Already handled in caller analysis
                    pass
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            analysis["constants"].append({
                                "name": target.id,
                                "line": node.lineno
                            })
                            
            # Calculate basic complexity
            analysis["complexity"] = len([n for n in ast.walk(tree) 
                                        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try))])
                                        
        except SyntaxError as e:
            analysis["parse_error"] = str(e)
            
        return analysis
        
    def _get_codebase_analysis(self, module_name: str) -> Dict[str, Any]:
        """Get codebase analysis using graph-sitter."""
        if not self.codebase:
            return {}
            
        analysis = {
            "related_modules": [],
            "similar_patterns": [],
            "dependencies": [],
            "architecture_info": {}
        }
        
        try:
            # Find related modules
            if hasattr(self.codebase, "get_modules"):
                modules = self.codebase.get_modules()
                for module in modules:
                    if module_name.split(".")[-1] in module.name:
                        analysis["related_modules"].append({
                            "name": module.name,
                            "path": str(module.path) if hasattr(module, "path") else "",
                            "symbols": len(module.symbols) if hasattr(module, "symbols") else 0
                        })
                        
        except Exception as e:
            analysis["error"] = str(e)
            
        return analysis
        
    def _get_symbol_information(self, module_name: str, function_name: Optional[str]) -> Dict[str, Any]:
        """Get symbol information from the codebase."""
        if not self.codebase:
            return {}
            
        symbols = {
            "available_symbols": [],
            "similar_functions": [],
            "type_information": {},
            "usage_patterns": []
        }
        
        try:
            if hasattr(self.codebase, "get_symbols"):
                all_symbols = self.codebase.get_symbols()
                
                for symbol in all_symbols:
                    if function_name and function_name.lower() in symbol.name.lower():
                        symbols["similar_functions"].append({
                            "name": symbol.name,
                            "type": symbol.type if hasattr(symbol, "type") else "unknown",
                            "module": symbol.module if hasattr(symbol, "module") else "",
                            "signature": symbol.signature if hasattr(symbol, "signature") else ""
                        })
                    
                    symbols["available_symbols"].append({
                        "name": symbol.name,
                        "type": symbol.type if hasattr(symbol, "type") else "unknown"
                    })
                    
        except Exception as e:
            symbols["error"] = str(e)
            
        return symbols
        
    def _get_dependency_analysis(self, module_name: str) -> Dict[str, Any]:
        """Analyze dependencies for the module."""
        dependencies = {
            "imports": [],
            "external_dependencies": [],
            "internal_dependencies": [],
            "circular_dependencies": []
        }
        
        # This would integrate with graph-sitter's dependency analysis
        # For now, return basic structure
        return dependencies
        
    def _get_pattern_suggestions(self, module_name: str, function_name: Optional[str]) -> Dict[str, Any]:
        """Get pattern suggestions based on module and function names."""
        patterns = {
            "naming_conventions": [],
            "common_patterns": [],
            "best_practices": [],
            "similar_implementations": []
        }
        
        # Analyze naming patterns
        if function_name:
            if function_name.startswith("get_"):
                patterns["common_patterns"].append("getter_pattern")
            elif function_name.startswith("set_"):
                patterns["common_patterns"].append("setter_pattern")
            elif function_name.startswith("is_") or function_name.startswith("has_"):
                patterns["common_patterns"].append("predicate_pattern")
            elif function_name.startswith("create_") or function_name.startswith("make_"):
                patterns["common_patterns"].append("factory_pattern")
                
        # Module-based patterns
        if "utils" in module_name:
            patterns["common_patterns"].append("utility_module")
        elif "config" in module_name:
            patterns["common_patterns"].append("configuration_module")
        elif "client" in module_name:
            patterns["common_patterns"].append("client_module")
            
        return patterns
        
    def format_context_for_autogenlib(self, context: Dict[str, Any]) -> str:
        """Format the enhanced context for autogenlib consumption."""
        formatted_parts = []
        
        # Add graph-sitter analysis
        if context.get("graph_sitter_analysis"):
            formatted_parts.append("## Graph-Sitter Analysis")
            analysis = context["graph_sitter_analysis"]
            if analysis.get("related_modules"):
                formatted_parts.append("### Related Modules:")
                for module in analysis["related_modules"]:
                    formatted_parts.append(f"- {module['name']}: {module.get('symbols', 0)} symbols")
                    
        # Add symbol information
        if context.get("symbol_information"):
            symbols = context["symbol_information"]
            if symbols.get("similar_functions"):
                formatted_parts.append("### Similar Functions:")
                for func in symbols["similar_functions"]:
                    formatted_parts.append(f"- {func['name']} ({func['type']}): {func.get('signature', '')}")
                    
        # Add caller analysis
        if context.get("caller_analysis"):
            caller = context["caller_analysis"]
            if caller.get("function_calls"):
                formatted_parts.append("### Function Usage Patterns:")
                for call in caller["function_calls"]:
                    formatted_parts.append(f"- {call['function']}({call['args']} args, {call['kwargs']} kwargs)")
                    
        # Add patterns
        if context.get("patterns"):
            patterns = context["patterns"]
            if patterns.get("common_patterns"):
                formatted_parts.append("### Detected Patterns:")
                for pattern in patterns["common_patterns"]:
                    formatted_parts.append(f"- {pattern}")
                    
        return "\n".join(formatted_parts)

