"""
Analysis engine for the Graph-Sitter Code Analytics API.
"""

import os
import tempfile
import shutil
import subprocess
import uuid
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import asyncio
from functools import lru_cache
import networkx as nx

# Check if graph-sitter is available
try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary,
    )
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False

# Configure logging
logger = logging.getLogger("graph_sitter_backend.engine")


class GraphSitterAnalysisEngine:
    """
    Production graph-sitter implementation for comprehensive codebase analysis.
    
    This class provides methods for analyzing a codebase using graph-sitter,
    including error detection, dead code analysis, complexity metrics, and
    dependency visualization.
    """

    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """
        Initialize the analysis engine.
        
        Args:
            repo_path: Path to the repository to analyze
            config: Optional configuration options
        """
        self.repo_path = Path(repo_path)
        self.config = config or {}
        self.codebase = None
        self.analysis_results = {}
        self._log_level = self.config.get("log_level", "info")
        
        # Configure logging based on config
        if self._log_level == "debug":
            logger.setLevel(logging.DEBUG)
        elif self._log_level == "info":
            logger.setLevel(logging.INFO)
        elif self._log_level == "warning":
            logger.setLevel(logging.WARNING)
        elif self._log_level == "error":
            logger.setLevel(logging.ERROR)
            
        logger.info(f"Initialized GraphSitterAnalysisEngine for {self.repo_path}")

    async def initialize_codebase(self):
        """
        Initialize the graph-sitter codebase.
        
        This method initializes the codebase using graph-sitter if available,
        or falls back to a mock implementation for development.
        
        Raises:
            Exception: If initialization fails
        """
        try:
            if GRAPH_SITTER_AVAILABLE:
                # Initialize codebase using graph-sitter
                self.codebase = Codebase(str(self.repo_path))
                logger.info(f"✅ Initialized graph-sitter codebase for {self.repo_path}")
                logger.info("🔍 Codebase Analysis")
                logger.info("=" * 50)
                logger.info(f"📚 Total Classes: {len(list(self.codebase.classes))}")
                logger.info(f"⚡ Total Functions: {len(list(self.codebase.functions))}")
                logger.info(f"📄 Total Files: {len(list(self.codebase.files))}")
                if hasattr(self.codebase, "imports"):
                    logger.info(f"🔄 Total Imports: {len(list(self.codebase.imports))}")
            else:
                # Mock implementation for development
                self.codebase = MockCodebase(str(self.repo_path))
                logger.warning(f"⚠️ Using mock implementation for {self.repo_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize graph-sitter codebase: {e}")
            # Fallback to mock implementation
            self.codebase = MockCodebase(str(self.repo_path))
            raise

    async def analyze_codebase(self) -> Dict[str, Any]:
        """
        Perform comprehensive codebase analysis.
        
        This method analyzes the codebase using graph-sitter, including error detection,
        dead code analysis, complexity metrics, and dependency visualization.
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        await self.initialize_codebase()

        # Comprehensive analysis
        codebase_summary = await self._get_comprehensive_metrics()
        tree_structure = await self._build_enhanced_tree_structure()
        errors = await self._find_comprehensive_errors()
        dead_code = await self._find_comprehensive_dead_code()
        entry_points = await self._find_entry_points()
        complexity_analysis = await self._analyze_complexity()
        dependency_analysis = await self._analyze_dependencies()
        most_important_functions = await self._find_most_important_functions()
        
        # Store results for future reference
        self.analysis_results = {
            "codebase_summary": codebase_summary,
            "tree_structure": tree_structure,
            "errors": errors,
            "dead_code": dead_code,
            "entry_points": entry_points,
            "complexity_analysis": complexity_analysis,
            "dependency_analysis": dependency_analysis,
            "most_important_functions": most_important_functions,
        }
        
        return self.analysis_results

    async def get_symbol_details(self, symbol_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific symbol.
        
        Args:
            symbol_path: Path to the symbol in format "file_path:symbol_name"
            
        Returns:
            Dict[str, Any]: Symbol details
            
        Raises:
            ValueError: If symbol path format is invalid
            HTTPException: If symbol is not found
        """
        if not self.codebase:
            await self.initialize_codebase()

        # Parse symbol path
        parts = symbol_path.split(":")
        if len(parts) == 1:
            # File path only
            return await self._get_file_details(parts[0])
        elif len(parts) == 2:
            # File:symbol format
            file_path, symbol_name = parts
            return await self._get_symbol_details(file_path, symbol_name)
        else:
            raise ValueError("Invalid symbol path format")
            
    async def _get_file_details(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed file information with symbol tree.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict[str, Any]: File details
            
        Raises:
            HTTPException: If file is not found
        """
        target_file = self._find_file(file_path)
        if not target_file:
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # Build symbol tree for file
        symbols = []

        # Add functions
        if hasattr(target_file, "functions"):
            for func in target_file.functions:
                func_name = func.name if hasattr(func, "name") else str(func)
                symbols.append(
                    {
                        "name": func_name,
                        "type": "function",
                        "path": f"{file_path}:{func_name}",
                        "line": getattr(func, "start_line", 1),
                        "summary": await self._get_function_summary_text(func),
                        "metrics": await self._get_function_metrics(func),
                    }
                )

        # Add classes
        if hasattr(target_file, "classes"):
            for cls in target_file.classes:
                cls_name = cls.name if hasattr(cls, "name") else str(cls)
                class_symbols = []

                # Add methods to class
                if hasattr(cls, "methods"):
                    for method in cls.methods:
                        method_name = (
                            method.name if hasattr(method, "name") else str(method)
                        )
                        class_symbols.append(
                            {
                                "name": method_name,
                                "type": "method",
                                "path": f"{file_path}:{cls_name}:{method_name}",
                                "line": getattr(method, "start_line", 1),
                                "summary": await self._get_function_summary_text(
                                    method
                                ),
                            }
                        )

                symbols.append(
                    {
                        "name": cls_name,
                        "type": "class",
                        "path": f"{file_path}:{cls_name}",
                        "line": getattr(cls, "start_line", 1),
                        "summary": await self._get_class_summary_text(cls),
                        "metrics": await self._get_class_metrics(cls),
                        "children": class_symbols,
                    }
                )

        # Get file content
        file_content = ""
        if hasattr(target_file, "content"):
            file_content = target_file.content
        elif hasattr(target_file, "source"):
            file_content = target_file.source

        return {
            "type": "file",
            "path": file_path,
            "summary": await self._get_file_summary_text(target_file),
            "symbols": symbols,
            "source_code": file_content,
            "metrics": {
                "lines": len(file_content.split("\n")) if file_content else 0,
                "functions": len(list(target_file.functions)) if hasattr(target_file, "functions") else 0,
                "classes": len(list(target_file.classes)) if hasattr(target_file, "classes") else 0,
                "imports": len(list(target_file.imports)) if hasattr(target_file, "imports") else 0,
            },
        }
        
    async def _get_symbol_details(
        self, file_path: str, symbol_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed symbol information.
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol
            
        Returns:
            Dict[str, Any]: Symbol details
            
        Raises:
            HTTPException: If symbol is not found
        """
        target_file = self._find_file(file_path)
        if not target_file:
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # Find symbol in file
        target_symbol = None
        symbol_type = "unknown"

        # Check functions
        if hasattr(target_file, "functions"):
            for func in target_file.functions:
                func_name = func.name if hasattr(func, "name") else str(func)
                if func_name == symbol_name:
                    target_symbol = func
                    symbol_type = "function"
                    break

        # Check classes
        if not target_symbol and hasattr(target_file, "classes"):
            for cls in target_file.classes:
                cls_name = cls.name if hasattr(cls, "name") else str(cls)
                if cls_name == symbol_name:
                    target_symbol = cls
                    symbol_type = "class"
                    break

                # Check methods within class
                if hasattr(cls, "methods"):
                    for method in cls.methods:
                        method_name = (
                            method.name if hasattr(method, "name") else str(method)
                        )
                        if method_name == symbol_name:
                            target_symbol = method
                            symbol_type = "method"
                            break

        if not target_symbol:
            logger.error(f"Symbol not found: {symbol_name} in {file_path}")
            raise ValueError(f"Symbol not found: {symbol_name} in {file_path}")

        # Get symbol source code
        source_code = ""
        if hasattr(target_symbol, "source"):
            source_code = target_symbol.source
        elif hasattr(target_symbol, "content"):
            source_code = target_symbol.content

        # Get dependencies
        dependencies = []
        if hasattr(target_symbol, "dependencies"):
            for dep in target_symbol.dependencies:
                dep_name = dep.name if hasattr(dep, "name") else str(dep)
                dependencies.append(dep_name)

        # Get usages
        usages = []
        if hasattr(target_symbol, "usages"):
            for usage in target_symbol.usages:
                usage_info = str(usage)
                if hasattr(usage, "file") and hasattr(usage.file, "filepath"):
                    usage_info = f"{usage.file.filepath}:{getattr(usage, 'line', 1)}"
                usages.append(usage_info)

        return {
            "type": symbol_type,
            "name": symbol_name,
            "path": f"{file_path}:{symbol_name}",
            "summary": await self._get_symbol_summary_text(target_symbol, symbol_type),
            "source_code": source_code,
            "dependencies": dependencies,
            "usages": usages,
            "metrics": await self._get_symbol_metrics(target_symbol, symbol_type),
        }
        
    def _find_file(self, file_path: str):
        """
        Find file in codebase.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File object or None if not found
        """
        if not self.codebase:
            return None

        if hasattr(self.codebase, "files"):
            for file in self.codebase.files:
                current_path = ""
                if hasattr(file, "filepath"):
                    current_path = str(file.filepath)
                elif hasattr(file, "path"):
                    current_path = str(file.path)
                elif hasattr(file, "name"):
                    current_path = file.name

                if current_path == file_path or current_path.endswith(file_path):
                    return file
        return None
        
    async def _get_file_summary_text(self, file) -> str:
        """
        Generate file summary text.
        
        Args:
            file: File object
            
        Returns:
            str: Summary text
        """
        if GRAPH_SITTER_AVAILABLE:
            try:
                return get_file_summary(file)
            except Exception as e:
                logger.warning(f"Failed to get file summary: {e}")

        # Fallback implementation
        file_name = ""
        if hasattr(file, "name"):
            file_name = file.name
        elif hasattr(file, "filepath"):
            file_name = Path(file.filepath).name

        functions_count = 0
        classes_count = 0
        if hasattr(file, "functions"):
            functions_count = len(list(file.functions))
        if hasattr(file, "classes"):
            classes_count = len(list(file.classes))

        return f"File '{file_name}' contains {functions_count} functions and {classes_count} classes with comprehensive analysis capabilities."

    async def _get_function_summary_text(self, func) -> str:
        """
        Generate function summary text.
        
        Args:
            func: Function object
            
        Returns:
            str: Summary text
        """
        if GRAPH_SITTER_AVAILABLE:
            try:
                return get_function_summary(func)
            except Exception as e:
                logger.warning(f"Failed to get function summary: {e}")

        # Fallback implementation
        func_name = func.name if hasattr(func, "name") else str(func)
        params_count = 0
        if hasattr(func, "parameters"):
            params_count = len(func.parameters)

        complexity = await self._calculate_cyclomatic_complexity(func)

        return f"Function '{func_name}' with {params_count} parameters and complexity score of {complexity}."

    async def _get_class_summary_text(self, cls) -> str:
        """
        Generate class summary text.
        
        Args:
            cls: Class object
            
        Returns:
            str: Summary text
        """
        if GRAPH_SITTER_AVAILABLE:
            try:
                return get_class_summary(cls)
            except Exception as e:
                logger.warning(f"Failed to get class summary: {e}")

        # Fallback implementation
        cls_name = cls.name if hasattr(cls, "name") else str(cls)
        methods_count = 0
        if hasattr(cls, "methods"):
            methods_count = len(cls.methods)

        return f"Class '{cls_name}' with {methods_count} methods implementing core analysis features."

    async def _get_symbol_summary_text(self, symbol, symbol_type: str) -> str:
        """
        Generate symbol summary text.
        
        Args:
            symbol: Symbol object
            symbol_type: Type of symbol
            
        Returns:
            str: Summary text
        """
        if GRAPH_SITTER_AVAILABLE:
            try:
                return get_symbol_summary(symbol)
            except Exception as e:
                logger.warning(f"Failed to get symbol summary: {e}")

        # Fallback implementation
        symbol_name = symbol.name if hasattr(symbol, "name") else str(symbol)
        dependencies_count = 0
        usages_count = 0

        if hasattr(symbol, "dependencies"):
            dependencies_count = len(symbol.dependencies)
        if hasattr(symbol, "usages"):
            usages_count = len(symbol.usages)

        return f"{symbol_type.title()} '{symbol_name}' with {dependencies_count} dependencies and {usages_count} usages throughout the codebase."
        
    async def _get_function_metrics(self, func) -> Dict[str, Any]:
        """
        Get detailed function metrics.
        
        Args:
            func: Function object
            
        Returns:
            Dict[str, Any]: Function metrics
        """
        complexity = await self._calculate_cyclomatic_complexity(func)

        params_count = 0
        if hasattr(func, "parameters"):
            params_count = len(func.parameters)

        lines_count = 0
        if hasattr(func, "source"):
            lines_count = len(func.source.split("\n"))
        elif hasattr(func, "content"):
            lines_count = len(func.content.split("\n"))

        calls_made = 0
        if hasattr(func, "function_calls"):
            calls_made = len(func.function_calls)

        times_called = 0
        if hasattr(func, "call_sites"):
            times_called = len(func.call_sites)
        elif hasattr(func, "usages"):
            times_called = len(func.usages)

        is_recursive = await self._is_recursive(func)

        has_decorators = False
        if hasattr(func, "decorators"):
            has_decorators = len(func.decorators) > 0

        is_async = False
        if hasattr(func, "is_async"):
            is_async = func.is_async

        return {
            "complexity": complexity,
            "parameters": params_count,
            "lines": lines_count,
            "calls_made": calls_made,
            "times_called": times_called,
            "is_recursive": is_recursive,
            "has_decorators": has_decorators,
            "is_async": is_async,
        }
        
    async def _get_class_metrics(self, cls) -> Dict[str, Any]:
        """
        Get detailed class metrics.
        
        Args:
            cls: Class object
            
        Returns:
            Dict[str, Any]: Class metrics
        """
        methods_count = 0
        if hasattr(cls, "methods"):
            methods_count = len(cls.methods)

        attributes_count = 0
        if hasattr(cls, "attributes"):
            attributes_count = len(cls.attributes)

        inheritance_depth = 0
        if hasattr(cls, "superclasses"):
            inheritance_depth = len(cls.superclasses)
        elif hasattr(cls, "parent_classes"):
            inheritance_depth = len(cls.parent_classes)

        subclasses_count = 0
        if hasattr(cls, "subclasses"):
            subclasses_count = len(cls.subclasses)

        is_abstract = False
        if hasattr(cls, "is_abstract"):
            is_abstract = cls.is_abstract
            
        is_dataclass = False
        if hasattr(cls, "decorators"):
            is_dataclass = any(d.name == "dataclass" for d in cls.decorators if hasattr(d, "name"))

        return {
            "methods": methods_count,
            "attributes": attributes_count,
            "inheritance_depth": inheritance_depth,
            "subclasses": subclasses_count,
            "is_abstract": is_abstract,
            "is_dataclass": is_dataclass,
        }
        
    async def _get_symbol_metrics(self, symbol, symbol_type: str) -> Dict[str, Any]:
        """
        Get metrics for any symbol type.
        
        Args:
            symbol: Symbol object
            symbol_type: Type of symbol
            
        Returns:
            Dict[str, Any]: Symbol metrics
        """
        if symbol_type == "function" or symbol_type == "method":
            return await self._get_function_metrics(symbol)
        elif symbol_type == "class":
            return await self._get_class_metrics(symbol)
        else:
            return {}
            
    async def _calculate_cyclomatic_complexity(self, func) -> int:
        """
        Calculate cyclomatic complexity for a function.
        
        Args:
            func: Function object
            
        Returns:
            int: Cyclomatic complexity
        """
        complexity = 1  # Base complexity

        try:
            source = ""
            if hasattr(func, "source"):
                source = func.source
            elif hasattr(func, "content"):
                source = func.content

            if source:
                # Count decision points
                complexity += source.count("if ")
                complexity += source.count("elif ")
                complexity += source.count("for ")
                complexity += source.count("while ")
                complexity += source.count("except ")
                complexity += source.count(" and ")
                complexity += source.count(" or ")
                complexity += source.count("&&")
                complexity += source.count("||")
                complexity += source.count("case ")
                complexity += source.count("when ")
                complexity += source.count("?")  # Ternary operator
        except Exception as e:
            logger.warning(f"Error calculating complexity: {e}")

        return min(complexity, 50)  # Cap at 50 to avoid extreme values
        
    async def _is_recursive(self, func) -> bool:
        """
        Check if function is recursive.
        
        Args:
            func: Function object
            
        Returns:
            bool: True if function is recursive
        """
        try:
            func_name = func.name if hasattr(func, "name") else str(func)

            # Check function calls
            if hasattr(func, "function_calls"):
                for call in func.function_calls:
                    call_name = call.name if hasattr(call, "name") else str(call)
                    if call_name == func_name:
                        return True

            # Check source code for recursive calls
            source = ""
            if hasattr(func, "source"):
                source = func.source
            elif hasattr(func, "content"):
                source = func.content

            if source and func_name in source:
                # Simple check for function name in its own body
                lines = source.split("\n")
                for line in lines[1:]:  # Skip function definition line
                    if func_name + "(" in line:
                        return True
        except Exception as e:
            logger.warning(f"Error checking recursion: {e}")
            
        return False
        
    async def _get_comprehensive_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive codebase metrics.
        
        Returns:
            Dict[str, Any]: Codebase metrics
        """
        from graph_sitter_backend_models import CodebaseMetrics
        
        files_count = (
            len(list(self.codebase.files)) if hasattr(self.codebase, "files") else 0
        )
        functions_count = (
            len(list(self.codebase.functions))
            if hasattr(self.codebase, "functions")
            else 0
        )
        classes_count = (
            len(list(self.codebase.classes)) if hasattr(self.codebase, "classes") else 0
        )
        imports_count = (
            len(list(self.codebase.imports)) if hasattr(self.codebase, "imports") else 0
        )

        lines_of_code = 0
        if hasattr(self.codebase, "files"):
            for file in self.codebase.files:
                if hasattr(file, "content"):
                    lines_of_code += len(file.content.split("\n"))
                elif hasattr(file, "source"):
                    lines_of_code += len(file.source.split("\n"))

        return CodebaseMetrics(
            files=files_count,
            functions=functions_count,
            classes=classes_count,
            imports=imports_count,
            lines_of_code=lines_of_code,
        )
        
    async def _find_comprehensive_errors(self) -> List[Dict[str, Any]]:
        """
        Find comprehensive errors using graph-sitter analysis.
        
        Returns:
            List[Dict[str, Any]]: List of errors
        """
        from graph_sitter_backend_models import ErrorItem
        
        errors = []
        error_id = 1

        if not hasattr(self.codebase, "functions"):
            return errors

        # Find missing type annotations
        for func in self.codebase.functions:
            try:
                func_name = func.name if hasattr(func, "name") else str(func)
                file_path = ""
                if hasattr(func, "file") and hasattr(func.file, "filepath"):
                    file_path = str(func.file.filepath)
                elif hasattr(func, "filepath"):
                    file_path = str(func.filepath)

                line = getattr(func, "start_line", 1)

                # Check parameters without type annotations
                if hasattr(func, "parameters"):
                    for param in func.parameters:
                        param_name = (
                            param.name if hasattr(param, "name") else str(param)
                        )
                        has_type = False

                        if hasattr(param, "type") and param.type:
                            has_type = True
                        elif (
                            hasattr(param, "type_annotation") and param.type_annotation
                        ):
                            has_type = True

                        if not has_type and param_name not in ["self", "cls"]:
                            errors.append(
                                ErrorItem(
                                    id=str(error_id),
                                    type="missing_type",
                                    severity="major",
                                    file=file_path,
                                    symbol=func_name,
                                    line=line,
                                    message=f"Parameter '{param_name}' missing type annotation",
                                    context=f"Function parameter lacks type annotation in {func_name}",
                                    suggestion="Add type annotation to improve code clarity",
                                )
                            )
                            error_id += 1

                # Check return type annotations
                has_return_type = False
                if hasattr(func, "return_type") and func.return_type:
                    has_return_type = True
                elif hasattr(func, "return_annotation") and func.return_annotation:
                    has_return_type = True

                if not has_return_type and func_name not in [
                    "__init__",
                    "__str__",
                    "__repr__",
                ]:
                    errors.append(
                        ErrorItem(
                            id=str(error_id),
                            type="missing_return_type",
                            severity="minor",
                            file=file_path,
                            symbol=func_name,
                            line=line,
                            message=f"Function '{func_name}' missing return type annotation",
                            context="Function lacks return type annotation",
                            suggestion="Add return type annotation",
                        )
                    )
                    error_id += 1
            except Exception as e:
                logger.warning(f"Error analyzing function {func_name}: {e}")
                continue

        return errors
        
    async def _find_comprehensive_dead_code(self) -> List[Dict[str, Any]]:
        """
        Find comprehensive dead code using graph-sitter analysis.
        
        Returns:
            List[Dict[str, Any]]: List of dead code items
        """
        from graph_sitter_backend_models import DeadCodeItem
        
        dead_code = []

        if not hasattr(self.codebase, "functions"):
            return dead_code

        # Find unused functions
        for func in self.codebase.functions:
            try:
                func_name = func.name if hasattr(func, "name") else str(func)
                file_path = ""
                if hasattr(func, "file") and hasattr(func.file, "filepath"):
                    file_path = str(func.file.filepath)
                elif hasattr(func, "filepath"):
                    file_path = str(func.filepath)

                line = getattr(func, "start_line", 1)

                # Skip test functions, main functions, and special methods
                if (
                    func_name.startswith("test_")
                    or func_name in ["main", "__main__", "__init__"]
                    or (func_name.startswith("_") and func_name.endswith("_"))
                ):
                    continue

                # Check if function has any call sites
                has_usages = False
                if hasattr(func, "call_sites"):
                    has_usages = len(func.call_sites) > 0
                elif hasattr(func, "usages"):
                    has_usages = len(func.usages) > 0

                if not has_usages:
                    dead_code.append(
                        DeadCodeItem(
                            type="unused_function",
                            name=func_name,
                            file=file_path,
                            line=line,
                            reason="No call sites found in reachability analysis",
                            safe_to_remove=True,
                        )
                    )
            except Exception as e:
                logger.warning(f"Error analyzing function for dead code {func_name}: {e}")
                continue

        # Find unused classes
        if hasattr(self.codebase, "classes"):
            for cls in self.codebase.classes:
                try:
                    cls_name = cls.name if hasattr(cls, "name") else str(cls)
                    file_path = ""
                    if hasattr(cls, "file") and hasattr(cls.file, "filepath"):
                        file_path = str(cls.file.filepath)
                    elif hasattr(cls, "filepath"):
                        file_path = str(cls.filepath)

                    line = getattr(cls, "start_line", 1)

                    # Skip test classes and special classes
                    if cls_name.startswith("Test") or (
                        cls_name.startswith("_") and cls_name.endswith("_")
                    ):
                        continue

                    # Check if class is instantiated or inherited
                    has_usages = False
                    if hasattr(cls, "subclasses"):
                        has_usages = len(cls.subclasses) > 0
                    if hasattr(cls, "usages"):
                        has_usages = has_usages or len(cls.usages) > 0

                    if not has_usages:
                        dead_code.append(
                            DeadCodeItem(
                                type="unused_class",
                                name=cls_name,
                                file=file_path,
                                line=line,
                                reason="Not instantiated or inherited anywhere in codebase",
                                safe_to_remove=True,
                            )
                        )
                except Exception as e:
                    logger.warning(f"Error analyzing class for dead code {cls_name}: {e}")
                    continue

        # Find unused imports
        if hasattr(self.codebase, "files"):
            for file in self.codebase.files:
                try:
                    file_path = ""
                    if hasattr(file, "filepath"):
                        file_path = str(file.filepath)
                    elif hasattr(file, "path"):
                        file_path = str(file.path)
                    elif hasattr(file, "name"):
                        file_path = file.name

                    if hasattr(file, "imports"):
                        for imp in file.imports:
                            try:
                                import_name = ""
                                if hasattr(imp, "name"):
                                    import_name = imp.name
                                elif hasattr(imp, "module_name"):
                                    import_name = imp.module_name
                                else:
                                    import_name = str(imp)

                                line = getattr(imp, "start_line", 1)

                                # Check if import has usages
                                has_usages = True  # Default to used to be safe
                                if hasattr(imp, "usages"):
                                    has_usages = len(imp.usages) > 0

                                if not has_usages:
                                    dead_code.append(
                                        DeadCodeItem(
                                            type="unused_import",
                                            name=import_name,
                                            file=file_path,
                                            line=line,
                                            reason="Import never used in file",
                                            safe_to_remove=True,
                                        )
                                    )
                            except Exception as e:
                                logger.warning(f"Error analyzing import for dead code {import_name}: {e}")
                                continue
                except Exception as e:
                    logger.warning(f"Error analyzing file for dead code {file_path}: {e}")
                    continue

        return dead_code
        
    async def _find_entry_points(self) -> List[Dict[str, Any]]:
        """
        Find entry points in the codebase.
        
        Returns:
            List[Dict[str, Any]]: List of entry points
        """
        from graph_sitter_backend_models import EntryPoint
        
        entry_points = []

        if not hasattr(self.codebase, "functions"):
            return entry_points

        for func in self.codebase.functions:
            try:
                func_name = func.name if hasattr(func, "name") else str(func)
                file_path = ""
                if hasattr(func, "file") and hasattr(func.file, "filepath"):
                    file_path = str(func.file.filepath)
                elif hasattr(func, "filepath"):
                    file_path = str(func.filepath)

                line = getattr(func, "start_line", 1)

                # Check if it's a main function
                is_entry_point = False
                if func_name in ["main", "__main__", "cli_main", "run_main"]:
                    is_entry_point = True

                # Check if it's in a main file
                if "main" in file_path.lower() or "__main__" in file_path:
                    is_entry_point = True

                # Check if it has no callers (potential entry point)
                has_callers = False
                if hasattr(func, "call_sites"):
                    has_callers = len(func.call_sites) > 0
                elif hasattr(func, "usages"):
                    has_callers = len(func.usages) > 0

                # If function starts with 'cli_' or has no callers and specific patterns
                if (
                    func_name.startswith("cli_")
                    or func_name.startswith("run_")
                    or (
                        not has_callers
                        and func_name not in ["__init__", "__str__", "__repr__"]
                    )
                ):
                    is_entry_point = True

                if is_entry_point:
                    entry_points.append(
                        EntryPoint(
                            name=func_name,
                            type="function",
                            file=file_path,
                            line=line,
                            description=f"Entry point function: {func_name}",
                        )
                    )
            except Exception as e:
                logger.warning(f"Error analyzing entry point {func_name}: {e}")
                continue

        return entry_points
        
    async def _analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity using graph-sitter.
        
        Returns:
            Dict[str, Any]: Complexity analysis results
        """
        complex_functions = []

        if hasattr(self.codebase, "functions"):
            for func in self.codebase.functions:
                try:
                    func_name = func.name if hasattr(func, "name") else str(func)
                    file_path = ""
                    if hasattr(func, "file") and hasattr(func.file, "filepath"):
                        file_path = str(func.file.filepath)
                    elif hasattr(func, "filepath"):
                        file_path = str(func.filepath)

                    # Calculate cyclomatic complexity
                    complexity = await self._calculate_cyclomatic_complexity(func)

                    # Calculate Halstead metrics
                    operators, operands = await self._get_operators_and_operands(func)
                    halstead_metrics = self._calculate_halstead_metrics(operators, operands)

                    # Get function metrics
                    function_metrics = await self._get_function_metrics(func)

                    complex_functions.append(
                        {
                            "name": func_name,
                            "file": file_path,
                            "metrics": function_metrics,
                            "halstead": halstead_metrics,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error analyzing complexity for {func_name}: {e}")
                    continue

        # Sort by complexity
        complex_functions.sort(key=lambda x: x["metrics"]["complexity"], reverse=True)

        # Calculate distribution
        complexity_distribution = self._get_complexity_distribution(complex_functions)
        avg_complexity = (
            sum(f["metrics"]["complexity"] for f in complex_functions)
            / len(complex_functions)
            if complex_functions
            else 0
        )

        return {
            "most_complex_functions": complex_functions[:20],
            "average_complexity": avg_complexity,
            "complexity_distribution": complexity_distribution,
        }
        
    async def _get_operators_and_operands(self, func) -> Tuple[List[str], List[str]]:
        """
        Extract operators and operands for Halstead metrics.
        
        Args:
            func: Function object
            
        Returns:
            Tuple[List[str], List[str]]: Operators and operands
        """
        operators = []
        operands = []

        try:
            source = ""
            if hasattr(func, "source"):
                source = func.source
            elif hasattr(func, "content"):
                source = func.content

            if source:
                # Basic operators
                for op in [
                    "+", "-", "*", "/", "=", "==", "!=", "<", ">", "<=", ">=",
                    "and", "or", "not", "in", "is", "+=", "-=", "*=", "/=",
                ]:
                    count = source.count(op)
                    operators.extend([op] * count)

                # Extract function calls as operators
                import re
                func_calls = re.findall(r"(\w+)\(", source)
                operators.extend(func_calls)

                # Extract variables as operands
                variables = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", source)
                operands.extend(variables)

                # Extract string literals as operands
                strings = re.findall(r'["\'][^"\']*["\']', source)
                operands.extend(strings)

                # Extract numbers as operands
                numbers = re.findall(r"\b\d+\b", source)
                operands.extend(numbers)
        except Exception as e:
            logger.warning(f"Error extracting operators and operands: {e}")

        return operators, operands
        
    def _calculate_halstead_metrics(
        self, operators: List[str], operands: List[str]
    ) -> Dict[str, float]:
        """
        Calculate Halstead complexity metrics.
        
        Args:
            operators: List of operators
            operands: List of operands
            
        Returns:
            Dict[str, float]: Halstead metrics
        """
        n1 = len(set(operators))  # Unique operators
        n2 = len(set(operands))  # Unique operands
        N1 = len(operators)  # Total operators
        N2 = len(operands)  # Total operands

        N = N1 + N2  # Total tokens
        n = n1 + n2  # Unique tokens

        if n > 0 and n2 > 0:
            volume = N * math.log2(n) if n > 1 else 0
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
        else:
            volume = difficulty = effort = 0

        return {
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "unique_operators": n1,
            "unique_operands": n2,
            "total_operators": N1,
            "total_operands": N2,
        }
        
    def _get_complexity_distribution(self, functions: List[Dict]) -> Dict[str, int]:
        """
        Get distribution of complexity levels.
        
        Args:
            functions: List of function data
            
        Returns:
            Dict[str, int]: Complexity distribution
        """
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}

        for func in functions:
            complexity = func["metrics"]["complexity"]
            rank = self._cc_rank(complexity)
            distribution[rank] += 1

        return distribution
        
    def _cc_rank(self, complexity: int) -> str:
        """
        Rank complexity according to standard scale.
        
        Args:
            complexity: Cyclomatic complexity
            
        Returns:
            str: Complexity rank
        """
        if complexity <= 5:
            return "A"  # Simple
        elif complexity <= 10:
            return "B"  # Moderate
        elif complexity <= 20:
            return "C"  # Complex
        elif complexity <= 30:
            return "D"  # Very Complex
        elif complexity <= 40:
            return "E"  # Extremely Complex
        else:
            return "F"  # Unmaintainable
            
    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """
        Analyze dependencies between files and modules.
        
        Returns:
            Dict[str, Any]: Dependency analysis results
        """
        # Build dependency graph
        dependency_graph = nx.DiGraph()

        # Add nodes for files
        if hasattr(self.codebase, "files"):
            for file in self.codebase.files:
                file_path = ""
                if hasattr(file, "filepath"):
                    file_path = str(file.filepath)
                elif hasattr(file, "path"):
                    file_path = str(file.path)
                elif hasattr(file, "name"):
                    file_path = file.name

                dependency_graph.add_node(file_path, type="file")

                # Add edges for imports
                if hasattr(file, "imports"):
                    for imp in file.imports:
                        try:
                            import_name = ""
                            if hasattr(imp, "name"):
                                import_name = imp.name
                            elif hasattr(imp, "module_name"):
                                import_name = imp.module_name
                            else:
                                import_name = str(imp)

                            # Add edge for import dependency
                            if import_name:
                                dependency_graph.add_edge(file_path, import_name, type="import")
                        except Exception as e:
                            logger.warning(f"Error analyzing import dependency: {e}")
                            continue

        # Calculate centrality metrics
        try:
            centrality = nx.degree_centrality(dependency_graph)
            betweenness = nx.betweenness_centrality(dependency_graph)
            closeness = nx.closeness_centrality(dependency_graph)
        except Exception as e:
            logger.warning(f"Error calculating centrality metrics: {e}")
            centrality = {}
            betweenness = {}
            closeness = {}

        # Find circular dependencies
        circular_deps = []
        try:
            cycles = list(nx.simple_cycles(dependency_graph))
            for cycle in cycles:
                if len(cycle) > 1:
                    circular_deps.append(cycle)
        except Exception as e:
            logger.warning(f"Error finding circular dependencies: {e}")

        # Find most central files
        central_files = []
        for node, cent in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:20]:
            central_files.append(
                {
                    "file": node,
                    "centrality": cent,
                    "betweenness": betweenness.get(node, 0),
                    "closeness": closeness.get(node, 0),
                }
            )

        return {
            "central_files": central_files,
            "circular_dependencies": circular_deps[:20],
            "total_dependencies": dependency_graph.number_of_edges(),
            "total_files": dependency_graph.number_of_nodes(),
        }
        
    async def _find_most_important_functions(self) -> List[Dict[str, Any]]:
        """
        Find most important functions based on usage and complexity.
        
        Returns:
            List[Dict[str, Any]]: List of important functions
        """
        important_functions = []

        if not hasattr(self.codebase, "functions"):
            return important_functions

        for func in self.codebase.functions:
            try:
                func_name = func.name if hasattr(func, "name") else str(func)
                file_path = ""
                if hasattr(func, "file") and hasattr(func.file, "filepath"):
                    file_path = str(func.file.filepath)
                elif hasattr(func, "filepath"):
                    file_path = str(func.filepath)

                line = getattr(func, "start_line", 1)

                # Count usages
                usage_count = 0
                if hasattr(func, "call_sites"):
                    usage_count = len(func.call_sites)
                elif hasattr(func, "usages"):
                    usage_count = len(func.usages)

                # Calculate complexity
                complexity = await self._calculate_cyclomatic_complexity(func)

                # Calculate importance score
                importance_score = (usage_count * 0.7) + (complexity * 0.3)

                important_functions.append(
                    {
                        "name": func_name,
                        "file": file_path,
                        "line": line,
                        "usage_count": usage_count,
                        "complexity": complexity,
                        "importance_score": importance_score,
                    }
                )
            except Exception as e:
                logger.warning(f"Error analyzing important function {func_name}: {e}")
                continue

        # Sort by importance score
        important_functions.sort(key=lambda x: x["importance_score"], reverse=True)

        return important_functions[:20]
        
    async def _build_enhanced_tree_structure(self) -> Dict[str, Any]:
        """
        Build enhanced tree structure of the codebase.
        
        Returns:
            Dict[str, Any]: Tree structure
        """
        # Build file tree
        tree = {}

        if hasattr(self.codebase, "files"):
            for file in self.codebase.files:
                try:
                    file_path = ""
                    if hasattr(file, "filepath"):
                        file_path = str(file.filepath)
                    elif hasattr(file, "path"):
                        file_path = str(file.path)
                    elif hasattr(file, "name"):
                        file_path = file.name

                    # Skip non-source files
                    if not file_path or not any(
                        file_path.endswith(ext)
                        for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp"]
                    ):
                        continue

                    # Split path into components
                    path_parts = file_path.split("/")
                    current = tree
                    for i, part in enumerate(path_parts):
                        if i == len(path_parts) - 1:
                            # Leaf node (file)
                            current[part] = {
                                "type": "file",
                                "path": file_path,
                                "metrics": {
                                    "functions": len(list(file.functions)) if hasattr(file, "functions") else 0,
                                    "classes": len(list(file.classes)) if hasattr(file, "classes") else 0,
                                    "imports": len(list(file.imports)) if hasattr(file, "imports") else 0,
                                },
                            }
                        else:
                            # Directory node
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                except Exception as e:
                    logger.warning(f"Error building tree for {file_path}: {e}")
                    continue

        return tree
        
class MockCodebase:
    """
    Mock implementation of Codebase for development and testing.
    
    This class provides a mock implementation of the Codebase class
    for development and testing when graph-sitter is not available.
    """

    def __init__(self, repo_path: str):
        """
        Initialize the mock codebase.
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = repo_path
        self._files = []
        self._functions = []
        self._classes = []
        self._imports = []
        
        # Scan repository for files
        self._scan_repo()
        
    def _scan_repo(self):
        """Scan repository for files."""
        try:
            repo_path = Path(self.repo_path)
            for file_path in repo_path.glob("**/*"):
                if file_path.is_file() and file_path.suffix in [
                    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp"
                ]:
                    self._files.append(MockFile(file_path))
        except Exception as e:
            logger.error(f"Error scanning repository: {e}")
            
    @property
    def files(self):
        """Get files in the codebase."""
        return self._files
        
    @property
    def functions(self):
        """Get functions in the codebase."""
        # Lazily collect functions from files
        if not self._functions:
            for file in self._files:
                self._functions.extend(file.functions)
        return self._functions
        
    @property
    def classes(self):
        """Get classes in the codebase."""
        # Lazily collect classes from files
        if not self._classes:
            for file in self._files:
                self._classes.extend(file.classes)
        return self._classes
        
    @property
    def imports(self):
        """Get imports in the codebase."""
        # Lazily collect imports from files
        if not self._imports:
            for file in self._files:
                self._imports.extend(file.imports)
        return self._imports
        
        
class MockFile:
    """Mock implementation of File for development and testing."""

    def __init__(self, file_path: Path):
        """
        Initialize the mock file.
        
        Args:
            file_path: Path to the file
        """
        self.filepath = str(file_path)
        self.name = file_path.name
        self._content = None
        self._functions = []
        self._classes = []
        self._imports = []
        
        # Parse file content
        self._parse_file()
        
    def _parse_file(self):
        """Parse file content to extract functions, classes, and imports."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._content = f.read()
                
            # Simple regex-based parsing for demonstration
            import re
            
            # Find functions
            function_matches = re.finditer(r"def\s+(\w+)\s*\(", self._content)
            for match in function_matches:
                self._functions.append(MockFunction(match.group(1), self))
                
            # Find classes
            class_matches = re.finditer(r"class\s+(\w+)", self._content)
            for match in class_matches:
                self._classes.append(MockClass(match.group(1), self))
                
            # Find imports
            import_matches = re.finditer(r"import\s+(\w+)|from\s+(\w+)", self._content)
            for match in import_matches:
                import_name = match.group(1) or match.group(2)
                self._imports.append(MockImport(import_name, self))
        except Exception as e:
            logger.error(f"Error parsing file {self.filepath}: {e}")
            
    @property
    def content(self):
        """Get file content."""
        return self._content
        
    @property
    def functions(self):
        """Get functions in the file."""
        return self._functions
        
    @property
    def classes(self):
        """Get classes in the file."""
        return self._classes
        
    @property
    def imports(self):
        """Get imports in the file."""
        return self._imports
        
        
class MockFunction:
    """Mock implementation of Function for development and testing."""

    def __init__(self, name: str, file: MockFile):
        """
        Initialize the mock function.
        
        Args:
            name: Name of the function
            file: File containing the function
        """
        self.name = name
        self.file = file
        self.parameters = []
        self.usages = []
        self.start_line = 1
        
        
class MockClass:
    """Mock implementation of Class for development and testing."""

    def __init__(self, name: str, file: MockFile):
        """
        Initialize the mock class.
        
        Args:
            name: Name of the class
            file: File containing the class
        """
        self.name = name
        self.file = file
        self.methods = []
        self.attributes = []
        self.usages = []
        self.start_line = 1
        
        
class MockImport:
    """Mock implementation of Import for development and testing."""

    def __init__(self, name: str, file: MockFile):
        """
        Initialize the mock import.
        
        Args:
            name: Name of the import
            file: File containing the import
        """
        self.name = name
        self.file = file
        self.usages = []
        self.start_line = 1
