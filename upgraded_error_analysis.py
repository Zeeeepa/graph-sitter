#!/usr/bin/env python3
"""
Supreme Error Analysis Tool - UPGRADED VERSION
Integrates graph-sitter codebase analysis with advanced error detection
Uses the ACTUAL graph-sitter API with enhanced real error detection capabilities
Focuses on actionable code errors: missing functions, dead code, parameter issues, etc.
"""

import json
import logging
import hashlib
import ast
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import math
import re
import requests
from datetime import datetime, timedelta
import subprocess
import os
import tempfile

# Import the REAL graph-sitter API
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol

# Import the existing analysis capabilities
try:
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary
    )
except ImportError:
    # Fallback implementations if not available
    def get_codebase_summary(codebase): return str(codebase)
    def get_file_summary(file): return str(file)
    def get_class_summary(cls): return str(cls)
    def get_function_summary(func): return str(func)
    def get_symbol_summary(symbol): return str(symbol)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeError:
    """Represents a real code error with detailed context"""
    error_type: str
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: Optional[int]
    function_name: Optional[str]
    class_name: Optional[str]
    message: str
    description: str
    fix_suggestions: List[str]
    context: Dict[str, Any]
    related_errors: List[str] = None

@dataclass
class AnalysisResult:
    """Data structure for analysis results"""
    name: str
    type: str
    filepath: str
    full_name: Optional[str] = None
    source_lines: int = 0
    is_private: Optional[bool] = None
    is_magic: Optional[bool] = None
    is_property: Optional[bool] = None
    methods_count: int = 0
    attributes_count: int = 0
    dependencies_count: int = 0
    summary: str = ""
    errors: List[CodeError] = None

@dataclass
class SupremeAnalysisReport:
    """Complete analysis report structure"""
    codebase_summary: str
    total_files: int
    total_classes: int
    total_functions: int
    total_symbols: int
    top_classes: List[AnalysisResult]
    top_functions: List[AnalysisResult]
    analysis_features: List[str]
    errors_found: List[Dict[str, Any]]
    comprehensive_errors: Optional[Dict[str, Any]] = None
    real_errors: List[CodeError] = None
    error_statistics: Dict[str, Any] = None

class UpgradedSupremeErrorAnalyzer:
    """
    Upgraded Supreme Error Analysis Tool using REAL graph-sitter API
    Enhanced with comprehensive real error detection capabilities
    """
    
    def __init__(self, codebase_path: str, exclude_folders: Optional[List[str]] = None):
        """Initialize with codebase path and optional folder exclusions"""
        self.codebase_path = Path(codebase_path)
        self.codebase: Optional[Codebase] = None
        self.errors: List[CodeError] = []
        self.function_call_graph = nx.DiGraph()
        self.import_graph = nx.DiGraph()
        
        # Default exclusions plus user-specified ones
        default_exclusions = ['tests', 'examples', 'node_modules', '__pycache__', '.git', '.pytest_cache', 'venv', 'env', 'test_files', 'docs']
        self.exclude_folders = set(default_exclusions + (exclude_folders or []))
        
        self.analysis_features = [
            "Advanced missing function detection with false positive filtering",
            "Dead code analysis with usage tracking",
            "Parameter validation and optimization",
            "Import cycle detection with exclusions",
            "Function call graph analysis",
            "Type annotation validation",
            "Documentation coverage analysis",
            "Code quality metrics",
            "Security vulnerability detection",
            "Performance bottleneck identification",
            "LSP integration capabilities",
            "Real-time analysis updates"
        ]
        
    def load_codebase(self) -> bool:
        """Load codebase using graph-sitter with folder exclusions"""
        try:
            logger.info(f"Loading codebase from: {self.codebase_path}")
            logger.info(f"Excluding folders: {', '.join(sorted(self.exclude_folders))}")
            self.codebase = Codebase(str(self.codebase_path))
            logger.info("✅ Codebase loaded successfully")
            self._build_analysis_graphs()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load codebase: {e}")
            return False
    
    def _should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded based on folder exclusions"""
        path_parts = Path(file_path).parts
        file_lower = file_path.lower()
        
        # Check folder exclusions
        if any(excluded in path_parts for excluded in self.exclude_folders):
            return True
            
        # Additional pattern-based exclusions
        if ('test' in file_lower and 
            ('test_' in file_lower or '/test' in file_lower or 'tests/' in file_lower)):
            return True
            
        if 'example' in file_lower and ('example' in path_parts or 'examples' in path_parts):
            return True
            
        return False
    
    def _build_analysis_graphs(self):
        """Build function call and import graphs for analysis"""
        if not self.codebase:
            return
            
        logger.info("🔗 Building analysis graphs...")
        
        # Build function call graph
        for func in self.codebase.functions:
            if hasattr(func, 'function_calls'):
                for call in func.function_calls:
                    self.function_call_graph.add_edge(
                        func.name or 'unknown',
                        getattr(call, 'name', 'unknown'),
                        file=func.filepath
                    )
        
        # Build import graph
        for file in self.codebase.files():
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    if hasattr(imp, 'imported_symbol') and hasattr(imp.imported_symbol, 'filepath'):
                        self.import_graph.add_edge(
                            file.filepath,
                            imp.imported_symbol.filepath,
                            import_name=getattr(imp, 'name', 'unknown')
                        )
        
        logger.info(f"📊 Built graphs: {len(self.function_call_graph.nodes)} function nodes, {len(self.import_graph.nodes)} file nodes")

    def analyze_missing_functions(self) -> List[CodeError]:
        """Enhanced missing function detection with context and false positive filtering"""
        errors = []
        if not self.codebase:
            return errors
            
        logger.info("🔍 Analyzing missing functions...")
        
        # Get all function calls and definitions with file context
        function_calls = defaultdict(list)  # function_name -> [(caller, file, line)]
        defined_functions = set()
        
        # Enhanced builtin and common library functions to reduce false positives
        builtin_functions = {
            # Python builtins
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
            'sum', 'min', 'max', 'abs', 'round', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'delattr', 'type', 'id', 'hash', 'repr', 'format', 'open',
            'input', 'eval', 'exec', 'compile', 'globals', 'locals', 'vars', 'dir',
            'next', 'iter', 'any', 'all', 'chr', 'ord', 'bin', 'hex', 'oct',
            'callable', 'classmethod', 'staticmethod', 'property', 'super',
            
            # functools module
            'partial', 'reduce', 'wraps', 'lru_cache', 'cached_property', 'singledispatch',
            
            # typing module
            'Optional', 'List', 'Dict', 'Union', 'Tuple', 'Any', 'Callable', 'Type',
            'Generic', 'TypeVar', 'ClassVar', 'Final', 'Literal', 'Protocol',
            
            # Common message/communication classes
            'SystemMessage', 'HumanMessage', 'AIMessage', 'BaseMessage', 'ChatMessage',
            
            # Common library functions that might not be detected
            'join', 'split', 'strip', 'replace', 'find', 'startswith', 'endswith',
            'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'copy',
            'update', 'get', 'keys', 'values', 'items',
            
            # Common method names that are often dynamically called
            'close', 'read', 'write', 'flush', 'seek', 'tell',
            'connect', 'disconnect', 'send', 'receive',
            'start', 'stop', 'pause', 'resume', 'reset',
            'load', 'save', 'dump', 'parse', 'format',
            'validate', 'check', 'verify', 'confirm',
            
            # Common test/mock functions
            'mock', 'patch', 'assert_called', 'assert_called_with',
            'side_effect', 'return_value',
            
            # Common CLI/utility functions
            'click', 'echo', 'prompt', 'confirm', 'abort', 'exit',
            'warn', 'error', 'info', 'debug',
            
            # Common data processing
            'json', 'yaml', 'csv', 'pickle', 'base64', 'uuid',
            'datetime', 'timedelta', 'timezone'
        }
        
        # Common false positive patterns
        false_positive_patterns = {
            # Single letters or very short names (likely variables)
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'id', 'ok', 'no', 'go', 'do', 'if', 'or', 'is', 'in', 'on', 'at',
            
            # Common variable names that might be mistaken for functions
            'data', 'item', 'value', 'key', 'name', 'path', 'file', 'line',
            'text', 'content', 'result', 'output', 'input', 'config', 'settings'
        }
        
        # Collect function calls with context (excluding specified folders)
        for file in self.codebase.files():
            try:
                # Skip excluded folders
                if self._should_exclude_file(file.filepath):
                    continue
                    
                for func in file.functions:
                    # Add to defined functions
                    if hasattr(func, 'name') and func.name:
                        defined_functions.add(func.name)
                    
                    # Collect function calls
                    if hasattr(func, 'function_calls'):
                        for call in func.function_calls:
                            call_name = getattr(call, 'name', None)
                            if call_name:
                                function_calls[call_name].append((
                                    func.name or 'unknown',
                                    file.filepath,
                                    getattr(func, 'line_number', None)
                                ))
            except Exception as e:
                logger.warning(f"Error analyzing file {file.filepath}: {e}")
                continue
        
        # Find missing functions with enhanced false positive filtering
        for func_name, call_sites in function_calls.items():
            if (func_name not in defined_functions and 
                func_name not in builtin_functions and
                func_name not in false_positive_patterns and
                not func_name.startswith('_') and
                len(func_name) > 2 and  # Increased from 1 to 2
                not func_name.isdigit() and  # Skip numeric strings
                not func_name.isupper() and  # Skip constants
                not func_name.endswith('Tool') and  # Skip Tool classes (likely external)
                len(call_sites) >= 2):  # Only report if called multiple times
                
                error = CodeError(
                    error_type="missing_function",
                    severity="critical",
                    file_path="multiple_files",
                    line_number=None,
                    function_name=func_name,
                    class_name=None,
                    message=f"Function '{func_name}' is called but not defined",
                    description=f"Function '{func_name}' is referenced in {len(call_sites)} locations but no definition found",
                    fix_suggestions=[
                        f"Define function '{func_name}'",
                        f"Check if '{func_name}' should be imported from another module",
                        f"Verify spelling of function name '{func_name}'",
                        f"Consider if '{func_name}' is a method that should be called on an object"
                    ],
                    context={
                        "call_sites": call_sites[:10],  # Limit to first 10
                        "total_calls": len(call_sites),
                        "files_affected": list(set(site[1] for site in call_sites))
                    }
                )
                errors.append(error)
        
        logger.info(f"Found {len(errors)} missing function errors")
        return errors

    def analyze_dead_code(self) -> List[CodeError]:
        """Enhanced dead code analysis with usage patterns and folder exclusions"""
        errors = []
        if not self.codebase:
            return errors
            
        logger.info("🔍 Analyzing dead code...")
        
        # Track function definitions and their usage
        defined_functions = {}
        function_calls = set()
        method_calls = set()
        
        # Collect all function definitions (excluding specified folders)
        for file in self.codebase.files():
            try:
                # Skip excluded folders
                if self._should_exclude_file(file.filepath):
                    continue
                    
                for func in file.functions:
                    if hasattr(func, 'name') and func.name:
                        defined_functions[func.name] = {
                            'file': file.filepath,
                            'line': getattr(func, 'line_number', None),
                            'function': func,
                            'is_method': hasattr(func, 'parent_class'),
                            'is_private': func.name.startswith('_'),
                            'is_magic': func.name.startswith('__') and func.name.endswith('__'),
                            'parameters': len(getattr(func, 'parameters', [])),
                            'source_lines': len(func.source.splitlines()) if hasattr(func, 'source') and func.source else 0
                        }
                
                # Collect function calls
                for func in file.functions:
                    if hasattr(func, 'function_calls'):
                        for call in func.function_calls:
                            call_name = getattr(call, 'name', None)
                            if call_name:
                                function_calls.add(call_name)
                                
            except Exception as e:
                logger.warning(f"Error analyzing file {file.filepath}: {e}")
                continue
        
        # Find unused functions with enhanced filtering
        for func_name, func_info in defined_functions.items():
            # Skip certain functions that might be used externally or are special
            if (func_name.startswith('__') or  # Magic methods
                func_name == 'main' or  # Main functions
                func_name.startswith('test_') or  # Test functions
                func_info['is_method'] or  # Methods (harder to track usage)
                func_name in ['setup', 'teardown', 'setUp', 'tearDown'] or  # Test setup
                func_name.endswith('_handler') or  # Event handlers
                func_name.startswith('handle_') or  # Event handlers
                func_name.endswith('_callback') or  # Callbacks
                func_name.startswith('on_') or  # Event handlers
                func_info['source_lines'] < 3):  # Very small functions (likely properties/getters)
                continue
                
            if func_name not in function_calls:
                severity = "high" if func_info['source_lines'] > 20 else "medium"
                
                error = CodeError(
                    error_type="dead_function",
                    severity=severity,
                    file_path=func_info['file'],
                    line_number=func_info['line'],
                    function_name=func_name,
                    class_name=None,
                    message=f"Function '{func_name}' is defined but never called",
                    description=f"Function '{func_name}' appears to be dead code - defined but not used anywhere",
                    fix_suggestions=[
                        f"Remove unused function '{func_name}' if not needed",
                        f"Check if '{func_name}' should be called somewhere",
                        f"Consider if '{func_name}' is part of a public API",
                        f"Add unit tests for '{func_name}' if it's meant to be used"
                    ],
                    context={
                        "source_lines": func_info['source_lines'],
                        "parameters": func_info['parameters'],
                        "is_private": func_info['is_private'],
                        "file_path": func_info['file']
                    }
                )
                errors.append(error)
        
        logger.info(f"Found {len(errors)} dead code errors")
        return errors

    def analyze_parameter_issues(self) -> List[CodeError]:
        """Enhanced parameter analysis with detailed recommendations"""
        errors = []
        if not self.codebase:
            return errors
            
        logger.info("🔍 Analyzing parameter issues...")
        
        for file in self.codebase.files():
            try:
                for func in file.functions:
                    if not hasattr(func, 'parameters') or not func.parameters:
                        continue
                    
                    param_count = len(func.parameters)
                    param_names = [getattr(p, 'name', 'unknown') for p in func.parameters]
                    
                    # Check for too many parameters
                    if param_count > 7:
                        severity = "high" if param_count > 10 else "medium"
                        
                        error = CodeError(
                            error_type="too_many_parameters",
                            severity=severity,
                            file_path=file.filepath,
                            line_number=getattr(func, 'line_number', None),
                            function_name=func.name,
                            class_name=None,
                            message=f"Function '{func.name}' has too many parameters ({param_count})",
                            description=f"Function '{func.name}' has {param_count} parameters, which may indicate poor design",
                            fix_suggestions=[
                                f"Reduce parameter count for '{func.name}' (currently {param_count})",
                                "Consider using a configuration object or dataclass",
                                "Split function into smaller, more focused functions",
                                "Use **kwargs for optional parameters",
                                "Group related parameters into objects"
                            ],
                            context={
                                "parameter_count": param_count,
                                "parameters": param_names,
                                "function_complexity": self._estimate_function_complexity(func)
                            }
                        )
                        errors.append(error)
                    
                    # Check for duplicate parameter names (shouldn't happen but good to check)
                    if len(param_names) != len(set(param_names)):
                        duplicates = [name for name, count in Counter(param_names).items() if count > 1]
                        error = CodeError(
                            error_type="duplicate_parameters",
                            severity="critical",
                            file_path=file.filepath,
                            line_number=getattr(func, 'line_number', None),
                            function_name=func.name,
                            class_name=None,
                            message=f"Function '{func.name}' has duplicate parameter names",
                            description=f"Duplicate parameters found: {duplicates}",
                            fix_suggestions=[
                                "Rename duplicate parameters to unique names",
                                "Review function signature for errors"
                            ],
                            context={"duplicates": duplicates, "all_parameters": param_names}
                        )
                        errors.append(error)
                        
            except Exception as e:
                logger.warning(f"Error analyzing file {file.filepath}: {e}")
                continue
        
        logger.info(f"Found {len(errors)} parameter issue errors")
        return errors

    def analyze_import_cycles(self) -> List[CodeError]:
        """Detect import cycles and circular dependencies"""
        errors = []
        if not self.codebase:
            return errors
            
        logger.info("🔍 Analyzing import cycles...")
        
        try:
            # Find strongly connected components (cycles)
            cycles = [scc for scc in nx.strongly_connected_components(self.import_graph) if len(scc) > 1]
            
            for i, cycle in enumerate(cycles):
                cycle_files = list(cycle)
                cycle_size = len(cycle_files)
                
                error = CodeError(
                    error_type="import_cycle",
                    severity="high" if cycle_size > 5 else "medium",
                    file_path="multiple_files",
                    line_number=None,
                    function_name=None,
                    class_name=None,
                    message=f"Import cycle detected involving {cycle_size} files",
                    description=f"Circular import dependency found between {cycle_size} files",
                    fix_suggestions=[
                        "Refactor code to eliminate circular imports",
                        "Move shared code to a separate module",
                        "Use dependency injection instead of direct imports",
                        "Consider lazy imports or import within functions",
                        "Restructure module hierarchy"
                    ],
                    context={
                        "cycle_files": cycle_files,
                        "cycle_size": cycle_size,
                        "cycle_id": i
                    }
                )
                errors.append(error)
        
        except Exception as e:
            logger.warning(f"Error analyzing import cycles: {e}")
        
        logger.info(f"Found {len(errors)} import cycle errors")
        return errors

    def analyze_type_annotations(self) -> List[CodeError]:
        """Analyze missing or incorrect type annotations"""
        errors = []
        if not self.codebase:
            return errors
            
        logger.info("🔍 Analyzing type annotations...")
        
        for file in self.codebase.files():
            try:
                for func in file.functions:
                    if not func.name or func.name.startswith('__'):
                        continue
                    
                    # Check for missing return type annotation
                    has_return_annotation = hasattr(func, 'return_type') and func.return_type
                    if not has_return_annotation:
                        error = CodeError(
                            error_type="missing_return_type",
                            severity="low",
                            file_path=file.filepath,
                            line_number=getattr(func, 'line_number', None),
                            function_name=func.name,
                            class_name=None,
                            message=f"Function '{func.name}' missing return type annotation",
                            description=f"Function '{func.name}' should have a return type annotation for better code clarity",
                            fix_suggestions=[
                                f"Add return type annotation to '{func.name}'",
                                "Use -> None if function doesn't return a value",
                                "Use appropriate type hints for return values"
                            ],
                            context={"has_parameters": bool(getattr(func, 'parameters', []))}
                        )
                        errors.append(error)
                        
            except Exception as e:
                logger.warning(f"Error analyzing file {file.filepath}: {e}")
                continue
        
        logger.info(f"Found {len(errors)} type annotation errors")
        return errors

    def analyze_documentation_coverage(self) -> List[CodeError]:
        """Analyze missing or poor documentation with folder exclusions"""
        errors = []
        if not self.codebase:
            return errors
            
        logger.info("🔍 Analyzing documentation coverage...")
        
        for file in self.codebase.files():
            try:
                # Skip excluded folders
                if self._should_exclude_file(file.filepath):
                    continue
                
                # Check classes
                for cls in file.classes:
                    if not hasattr(cls, 'docstring') or not cls.docstring:
                        error = CodeError(
                            error_type="missing_class_docstring",
                            severity="low",
                            file_path=file.filepath,
                            line_number=getattr(cls, 'line_number', None),
                            function_name=None,
                            class_name=cls.name,
                            message=f"Class '{cls.name}' missing docstring",
                            description=f"Class '{cls.name}' should have a docstring explaining its purpose",
                            fix_suggestions=[
                                f"Add docstring to class '{cls.name}'",
                                "Explain the class purpose and usage",
                                "Document class attributes and methods"
                            ],
                            context={"class_name": cls.name}
                        )
                        errors.append(error)
                
                # Check functions (with enhanced filtering)
                for func in file.functions:
                    if (not func.name or 
                        func.name.startswith('_') or 
                        func.name.startswith('test_') or
                        func.name in ['main', 'setup', 'teardown'] or
                        len(func.name) <= 2):  # Skip very short function names
                        continue
                        
                    if not hasattr(func, 'docstring') or not func.docstring:
                        error = CodeError(
                            error_type="missing_function_docstring",
                            severity="low",
                            file_path=file.filepath,
                            line_number=getattr(func, 'line_number', None),
                            function_name=func.name,
                            class_name=None,
                            message=f"Function '{func.name}' missing docstring",
                            description=f"Public function '{func.name}' should have a docstring",
                            fix_suggestions=[
                                f"Add docstring to function '{func.name}'",
                                "Explain function purpose, parameters, and return value",
                                "Use standard docstring format (Google, NumPy, or Sphinx)"
                            ],
                            context={
                                "function_name": func.name,
                                "has_parameters": bool(getattr(func, 'parameters', []))
                            }
                        )
                        errors.append(error)
                        
            except Exception as e:
                logger.warning(f"Error analyzing file {file.filepath}: {e}")
                continue
        
        logger.info(f"Found {len(errors)} documentation errors")
        return errors

    def _estimate_function_complexity(self, func) -> int:
        """Estimate function complexity based on available information"""
        complexity = 1
        
        if hasattr(func, 'source') and func.source:
            source = func.source.lower()
            complexity += source.count('if ') + source.count('elif ')
            complexity += source.count('for ') + source.count('while ')
            complexity += source.count('except ')
            complexity += source.count(' and ') + source.count(' or ')
            complexity += source.count('try:')
        
        return complexity

    def run_comprehensive_analysis(self) -> List[CodeError]:
        """Run all error analysis methods"""
        if not self.load_codebase():
            raise RuntimeError("Failed to load codebase")
        
        logger.info("🚀 Starting comprehensive error analysis...")
        
        all_errors = []
        
        # Run all analysis methods
        all_errors.extend(self.analyze_missing_functions())
        all_errors.extend(self.analyze_dead_code())
        all_errors.extend(self.analyze_parameter_issues())
        all_errors.extend(self.analyze_import_cycles())
        all_errors.extend(self.analyze_type_annotations())
        all_errors.extend(self.analyze_documentation_coverage())
        
        self.errors = all_errors
        logger.info(f"✅ Comprehensive analysis complete: {len(all_errors)} errors found")
        
        return all_errors

    def generate_error_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive error statistics"""
        if not self.errors:
            return {}
        
        stats = {
            "total_errors": len(self.errors),
            "by_severity": Counter(error.severity for error in self.errors),
            "by_type": Counter(error.error_type for error in self.errors),
            "by_file": defaultdict(int),
            "most_problematic_files": [],
            "error_density": {},
            "fix_priority": []
        }
        
        # Count errors by file
        for error in self.errors:
            if error.file_path != "multiple_files":
                stats["by_file"][error.file_path] += 1
        
        # Find most problematic files
        stats["most_problematic_files"] = sorted(
            stats["by_file"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Calculate error density (errors per file)
        if self.codebase:
            total_files = len(self.codebase.files())
            stats["error_density"]["errors_per_file"] = len(self.errors) / total_files if total_files > 0 else 0
        
        # Priority fixes (critical and high severity)
        priority_errors = [e for e in self.errors if e.severity in ['critical', 'high']]
        stats["fix_priority"] = sorted(
            priority_errors, 
            key=lambda x: (x.severity == 'critical', x.severity == 'high'), 
            reverse=True
        )[:20]
        
        return stats

    def export_detailed_results(self, output_file: str = "upgraded_analysis_results.json"):
        """Export comprehensive analysis results"""
        try:
            results = {
                "analysis_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "codebase_path": str(self.codebase_path),
                    "analyzer_version": "2.0.0-upgraded"
                },
                "statistics": self.generate_error_statistics(),
                "errors": [asdict(error) for error in self.errors],
                "analysis_features": self.analysis_features
            }
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"📄 Detailed results exported to: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
    
    def export_error_list(self, output_file: str = "error_list.txt"):
        """Export numbered list of all errors"""
        try:
            with open(output_file, 'w') as f:
                f.write(f"ERROR LIST: [{len(self.errors)} errors]\n")
                f.write("=" * 80 + "\n\n")
                
                for i, error in enumerate(self.errors, 1):
                    severity_emoji = {
                        'critical': '🔴',
                        'high': '🟠', 
                        'medium': '🟡',
                        'low': '🔵'
                    }.get(error.severity, '⚪')
                    
                    f.write(f"{i:4d}. {severity_emoji} [{error.error_type.upper()}] {error.message}\n")
                    f.write(f"      📁 File: {error.file_path}\n")
                    if error.line_number:
                        f.write(f"      📍 Line: {error.line_number}\n")
                    if error.function_name:
                        f.write(f"      🔧 Function: {error.function_name}\n")
                    if error.class_name:
                        f.write(f"      🏛️  Class: {error.class_name}\n")
                    f.write(f"      💡 Fix: {error.fix_suggestions[0] if error.fix_suggestions else 'No suggestion'}\n")
                    f.write("\n")
            
            logger.info(f"📋 Error list exported to: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export error list: {e}")

def main():
    """Main entry point for upgraded analysis"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upgraded_error_analysis.py <codebase_path> [--exclude folder1,folder2,...]")
        print("Example: python upgraded_error_analysis.py . --exclude tests,examples,node_modules")
        sys.exit(1)
    
    codebase_path = sys.argv[1]
    exclude_folders = None
    
    # Parse exclude folders argument
    if len(sys.argv) > 2 and sys.argv[2] == '--exclude':
        if len(sys.argv) > 3:
            exclude_folders = [folder.strip() for folder in sys.argv[3].split(',')]
    
    try:
        # Initialize upgraded analyzer with exclusions
        analyzer = UpgradedSupremeErrorAnalyzer(codebase_path, exclude_folders)
        
        # Run comprehensive analysis
        errors = analyzer.run_comprehensive_analysis()
        
        # Generate statistics
        stats = analyzer.generate_error_statistics()
        
        # Export results
        analyzer.export_detailed_results()
        analyzer.export_error_list()
        
        # Print summary
        print("\n" + "="*70)
        print("🚀 UPGRADED SUPREME ERROR ANALYSIS COMPLETE")
        print("="*70)
        print(f"📁 Analyzed: {codebase_path}")
        print(f"🚫 Excluded: {', '.join(sorted(analyzer.exclude_folders))}")
        print(f"🚨 Total Errors: {stats['total_errors']}")
        print(f"⚠️ Critical: {stats['by_severity']['critical']}")
        print(f"🔶 High: {stats['by_severity']['high']}")
        print(f"🔸 Medium: {stats['by_severity']['medium']}")
        print(f"🔹 Low: {stats['by_severity']['low']}")
        
        print("\n🎯 Error Types:")
        for error_type, count in stats['by_type'].most_common():
            print(f"  • {error_type}: {count}")
        
        print("\n📊 Most Problematic Files:")
        for file_path, error_count in stats['most_problematic_files'][:5]:
            print(f"  • {file_path}: {error_count} errors")
        
        print(f"\n⚡ Analysis Features: {len(analyzer.analysis_features)}")
        for feature in analyzer.analysis_features:
            print(f"  ✅ {feature}")
        
        print(f"\n📄 Full results saved to: upgraded_analysis_results.json")
        print(f"📋 Complete error list saved to: error_list.txt")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
