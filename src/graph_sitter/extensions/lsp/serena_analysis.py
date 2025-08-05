"""
Comprehensive Error Analysis System for Graph-Sitter & Serena

This module provides comprehensive error detection, context analysis, and dependency tracking
using existing graph-sitter and Serena capabilities, integrating with the existing codebase
analysis functions.
"""

import ast
import inspect
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary
)

# Import our enhanced bridge components
from .serena_bridge import (
    SerenaLSPBridge, ErrorInfo, ErrorSeverity, ErrorCategory, 
    ComprehensiveErrorList, ErrorLocation
)

logger = get_logger(__name__)


@dataclass
class ErrorContext:
    """Comprehensive error context information using graph-sitter analysis."""
    error_info: ErrorInfo
    
    # Graph-sitter context
    codebase_context: Optional[str] = None
    file_context: Optional[str] = None
    symbol_context: Optional[str] = None
    function_context: Optional[str] = None
    class_context: Optional[str] = None
    
    # Enhanced analysis
    calling_functions: List[Dict[str, Any]] = field(default_factory=list)
    called_functions: List[Dict[str, Any]] = field(default_factory=list)
    parameter_issues: List[Dict[str, Any]] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    related_symbols: List[Dict[str, Any]] = field(default_factory=list)
    code_context: Optional[str] = None
    fix_suggestions: List[str] = field(default_factory=list)
    blast_radius: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParameterIssue:
    """Parameter usage issue."""
    issue_type: str  # unused, wrong_type, missing, invalid_value
    parameter_name: str
    function_name: str
    file_path: str
    line_number: int
    expected_type: Optional[str] = None
    actual_type: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class FunctionCallInfo:
    """Information about function calls."""
    function_name: str
    file_path: str
    line_number: int
    parameters: List[str]
    return_type: Optional[str] = None
    is_caller: bool = True  # True if this function calls the error point, False if called by error point


class ComprehensiveErrorAnalyzer:
    """
    Comprehensive error analyzer that leverages existing graph-sitter capabilities
    and integrates with Serena LSP for advanced error detection and analysis.
    """
    
    def __init__(self, codebase: Codebase, enable_lsp: bool = True):
        self.codebase = codebase
        self.enable_lsp = enable_lsp
        
        # Initialize Serena LSP bridge
        self.lsp_bridge = None
        if enable_lsp:
            try:
                self.lsp_bridge = SerenaLSPBridge(str(codebase.repo_path))
                logger.info("Serena LSP bridge initialized for error analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize Serena LSP bridge: {e}")
        
        # Error analysis cache
        self._error_cache: Dict[str, ErrorContext] = {}
        self._parameter_cache: Dict[str, List[ParameterIssue]] = {}
        self._call_graph_cache: Dict[str, List[FunctionCallInfo]] = {}
        
        logger.info("Comprehensive error analyzer initialized")
    
    def get_all_errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase using LSP bridge."""
        if self.lsp_bridge:
            return self.lsp_bridge.get_diagnostics()
        return []
    
    def get_all_warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        all_diagnostics = self.get_all_errors()
        return [e for e in all_diagnostics if e.is_warning]
    
    def get_all_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints)."""
        if self.lsp_bridge:
            return self.lsp_bridge.get_diagnostics()
        return []
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        if self.lsp_bridge:
            return self.lsp_bridge.get_file_diagnostics(file_path)
        return []
    
    def get_comprehensive_errors(
        self,
        include_context: bool = True,
        include_suggestions: bool = True,
        max_errors: Optional[int] = None,
        severity_filter: Optional[List[ErrorSeverity]] = None
    ) -> ComprehensiveErrorList:
        """Get comprehensive error analysis with graph-sitter context."""
        if self.lsp_bridge:
            return self.lsp_bridge.get_comprehensive_errors(
                include_context=include_context,
                include_suggestions=include_suggestions,
                max_errors=max_errors,
                severity_filter=severity_filter
            )
        
        # Fallback: return empty list
        return ComprehensiveErrorList()
    
    def analyze_error_context(self, error: ErrorInfo) -> ErrorContext:
        """
        Analyze comprehensive context for an error using graph-sitter capabilities.
        
        Args:
            error: ErrorInfo object from diagnostics
            
        Returns:
            ErrorContext with comprehensive information
        """
        error_key = f"{error.file_path}:{error.line}:{error.character}"
        
        # Check cache first
        if error_key in self._error_cache:
            return self._error_cache[error_key]
        
        logger.info(f"Analyzing error context: {error.message} at {error.file_path}:{error.line}")
        
        context = ErrorContext(error_info=error)
        
        try:
            # Get graph-sitter context using existing analysis functions
            context = self._add_graph_sitter_context(context)
            
            # Get code context around error
            context.code_context = self._get_code_context(error.file_path, error.line)
            
            # Analyze function call chains
            context.calling_functions = self._find_calling_functions(error.file_path, error.line)
            context.called_functions = self._find_called_functions(error.file_path, error.line)
            
            # Analyze parameter issues
            context.parameter_issues = self._analyze_parameter_issues(error.file_path, error.line)
            
            # Build dependency chain
            context.dependency_chain = self._build_dependency_chain(error.file_path)
            
            # Find related symbols
            context.related_symbols = self._find_related_symbols(error.file_path, error.line)
            
            # Calculate blast radius
            context.blast_radius = self._calculate_blast_radius(error)
            
            # Generate fix suggestions
            context.fix_suggestions = self._generate_fix_suggestions(error, context)
            
            # Cache the result
            self._error_cache[error_key] = context
            
        except Exception as e:
            logger.error(f"Error analyzing context for {error_key}: {e}")
            logger.debug(traceback.format_exc())
        
        return context
    
    def _add_graph_sitter_context(self, context: ErrorContext) -> ErrorContext:
        """Add graph-sitter context using existing analysis functions."""
        try:
            error = context.error_info
            
            # Get codebase context
            context.codebase_context = get_codebase_summary(self.codebase)
            
            # Get file context
            file_obj = self._get_file_object(error.file_path)
            if file_obj:
                context.file_context = get_file_summary(file_obj)
                
                # Get symbol context
                symbol = self._find_symbol_at_location(file_obj, error.line)
                if symbol:
                    context.symbol_context = get_symbol_summary(symbol)
                    
                    # Get function context if it's a function
                    if hasattr(symbol, 'parameters'):  # It's a function
                        context.function_context = get_function_summary(symbol)
                    
                    # Get class context if it's a class or method
                    parent_class = self._find_parent_class(file_obj, error.line)
                    if parent_class:
                        context.class_context = get_class_summary(parent_class)
            
        except Exception as e:
            logger.error(f"Error adding graph-sitter context: {e}")
        
        return context
    
    def _get_file_object(self, file_path: str):
        """Get file object from codebase."""
        try:
            # Normalize path
            file_path = str(Path(file_path).resolve())
            
            for file_obj in self.codebase.files:
                if str(Path(file_obj.filepath).resolve()) == file_path:
                    return file_obj
        except Exception as e:
            logger.debug(f"Could not get file object for {file_path}: {e}")
        
        return None
    
    def _find_symbol_at_location(self, file_obj, line: int):
        """Find symbol at specific line in file."""
        try:
            # Check functions
            for func in file_obj.functions:
                if hasattr(func, 'line_number') and func.line_number == line:
                    return func
                # Check if line is within function range
                if (hasattr(func, 'start_line') and hasattr(func, 'end_line') and
                    func.start_line <= line <= func.end_line):
                    return func
            
            # Check classes
            for cls in file_obj.classes:
                if hasattr(cls, 'line_number') and cls.line_number == line:
                    return cls
                # Check if line is within class range
                if (hasattr(cls, 'start_line') and hasattr(cls, 'end_line') and
                    cls.start_line <= line <= cls.end_line):
                    return cls
            
            # Check global variables
            for var in file_obj.global_vars:
                if hasattr(var, 'line_number') and var.line_number == line:
                    return var
            
        except Exception as e:
            logger.debug(f"Error finding symbol at location: {e}")
        
        return None
    
    def _find_parent_class(self, file_obj, line: int):
        """Find parent class containing the given line."""
        try:
            for cls in file_obj.classes:
                if (hasattr(cls, 'start_line') and hasattr(cls, 'end_line') and
                    cls.start_line <= line <= cls.end_line):
                    return cls
        except Exception as e:
            logger.debug(f"Error finding parent class: {e}")
        
        return None
    
    def _get_code_context(self, file_path: str, line: int, context_lines: int = 5) -> Optional[str]:
        """Get code context around an error line."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return None
            
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, line - context_lines - 1)
            end_line = min(len(lines), line + context_lines)
            
            context_lines_list = []
            for i in range(start_line, end_line):
                prefix = ">>> " if i == line - 1 else "    "
                context_lines_list.append(f"{prefix}{i+1:4d}: {lines[i].rstrip()}")
            
            return '\n'.join(context_lines_list)
            
        except Exception as e:
            logger.error(f"Error getting code context: {e}")
            return None
    
    def _find_calling_functions(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find functions that call the error point using graph-sitter analysis."""
        calling_functions = []
        
        try:
            # Get the function name at the error line
            function_name = self._get_function_at_line(file_path, line)
            if not function_name:
                return calling_functions
            
            # Search through all files for calls to this function
            for file_obj in self.codebase.files:
                try:
                    # Look for function calls in each function
                    for func in file_obj.functions:
                        if hasattr(func, 'function_calls'):
                            for call in func.function_calls:
                                if call.name == function_name:
                                    calling_functions.append({
                                        'function_name': func.name,
                                        'file_path': file_obj.filepath,
                                        'line_number': getattr(call, 'line_number', 0),
                                        'context': f"Call to {function_name} in {func.name}",
                                        'score': 1.0
                                    })
                except Exception as e:
                    logger.debug(f"Error analyzing file {file_obj.filepath}: {e}")
                    
        except Exception as e:
            logger.error(f"Error finding calling functions: {e}")
        
        return calling_functions
    
    def _find_called_functions(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find functions called by the error point using graph-sitter analysis."""
        called_functions = []
        
        try:
            # Find the function containing the error line
            file_obj = self._get_file_object(file_path)
            if not file_obj:
                return called_functions
            
            # Find the function at the error line
            target_function = None
            for func in file_obj.functions:
                if (hasattr(func, 'start_line') and hasattr(func, 'end_line') and
                    func.start_line <= line <= func.end_line):
                    target_function = func
                    break
            
            if target_function and hasattr(target_function, 'function_calls'):
                for call in target_function.function_calls:
                    called_functions.append({
                        'function_name': call.name,
                        'file_path': file_path,
                        'line_number': getattr(call, 'line_number', 0),
                        'parameters': getattr(call, 'parameters', []),
                        'return_type': getattr(call, 'return_type', None)
                    })
                    
        except Exception as e:
            logger.error(f"Error finding called functions: {e}")
        
        return called_functions
    
    def _analyze_parameter_issues(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Analyze parameter usage issues using graph-sitter analysis."""
        parameter_issues = []
        
        try:
            file_obj = self._get_file_object(file_path)
            if not file_obj:
                return parameter_issues
            
            # Find function containing the error line
            target_function = None
            for func in file_obj.functions:
                if (hasattr(func, 'start_line') and hasattr(func, 'end_line') and
                    func.start_line <= line <= func.end_line):
                    target_function = func
                    break
            
            if target_function and hasattr(target_function, 'parameters'):
                # Analyze each parameter
                for param in target_function.parameters:
                    # Check if parameter is used (simplified analysis)
                    param_name = param.name if hasattr(param, 'name') else str(param)
                    
                    # This is a simplified check - in a real implementation,
                    # you'd analyze the function body for parameter usage
                    parameter_issues.append({
                        'issue_type': 'analysis_needed',
                        'parameter_name': param_name,
                        'function_name': target_function.name,
                        'suggestion': f"Analyze usage of parameter '{param_name}'"
                    })
                    
        except Exception as e:
            logger.error(f"Error analyzing parameter issues: {e}")
        
        return parameter_issues
    
    def _build_dependency_chain(self, file_path: str) -> List[str]:
        """Build dependency chain for a file using graph-sitter analysis."""
        dependency_chain = []
        
        try:
            file_obj = self._get_file_object(file_path)
            if not file_obj:
                return dependency_chain
            
            # Get imports
            for import_obj in file_obj.imports:
                dependency_chain.append(import_obj.name)
                    
        except Exception as e:
            logger.error(f"Error building dependency chain: {e}")
        
        return dependency_chain
    
    def _find_related_symbols(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find symbols related to the error point using graph-sitter analysis."""
        related_symbols = []
        
        try:
            file_obj = self._get_file_object(file_path)
            if not file_obj:
                return related_symbols
            
            # Find symbol at error location
            error_symbol = self._find_symbol_at_location(file_obj, line)
            if not error_symbol:
                return related_symbols
            
            # Find related symbols in the same file
            for symbol in file_obj.symbols:
                if symbol != error_symbol:
                    related_symbols.append({
                        'symbol_name': symbol.name,
                        'symbol_type': getattr(symbol, 'symbol_type', 'unknown'),
                        'file_path': file_path,
                        'line_number': getattr(symbol, 'line_number', 0),
                        'relevance_score': 0.5,  # Simplified scoring
                        'context': f"Related symbol in same file"
                    })
                    
        except Exception as e:
            logger.error(f"Error finding related symbols: {e}")
        
        return related_symbols
    
    def _calculate_blast_radius(self, error: ErrorInfo) -> Dict[str, Any]:
        """Calculate the blast radius of an error."""
        try:
            blast_radius = {
                'scope': 'local',
                'affected_files': 1,
                'affected_functions': 0,
                'affected_classes': 0,
                'risk_level': 'low'
            }
            
            # Get file object
            file_obj = self._get_file_object(error.file_path)
            if not file_obj:
                return blast_radius
            
            # Find symbol at error location
            error_symbol = self._find_symbol_at_location(file_obj, error.line)
            if error_symbol:
                # Count usages to determine blast radius
                if hasattr(error_symbol, 'symbol_usages'):
                    usage_count = len(error_symbol.symbol_usages)
                    
                    if usage_count > 20:
                        blast_radius['scope'] = 'project'
                        blast_radius['risk_level'] = 'high'
                    elif usage_count > 5:
                        blast_radius['scope'] = 'module'
                        blast_radius['risk_level'] = 'medium'
                    
                    blast_radius['affected_functions'] = usage_count
            
            return blast_radius
            
        except Exception as e:
            logger.error(f"Error calculating blast radius: {e}")
            return {'scope': 'unknown', 'risk_level': 'unknown'}
    
    def _generate_fix_suggestions(self, error: ErrorInfo, context: ErrorContext) -> List[str]:
        """Generate fix suggestions based on error and context."""
        suggestions = []
        
        try:
            # Use existing suggestions from error
            if error.suggestions:
                suggestions.extend(error.suggestions)
            
            # Add context-based suggestions
            if context.parameter_issues:
                suggestions.append("Review parameter usage and types")
            
            if context.calling_functions:
                suggestions.append("Check how this function is being called")
            
            if context.blast_radius.get('risk_level') == 'high':
                suggestions.append("Consider the high impact of changes to this symbol")
            
            # Add graph-sitter specific suggestions
            if context.symbol_context:
                suggestions.append("Review symbol dependencies and usages")
            
            if not suggestions:
                suggestions.append("Review the code context and related functions")
                
        except Exception as e:
            logger.error(f"Error generating fix suggestions: {e}")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _get_function_at_line(self, file_path: str, line: int) -> Optional[str]:
        """Get the function name at a specific line."""
        try:
            file_obj = self._get_file_object(file_path)
            if not file_obj:
                return None
            
            for func in file_obj.functions:
                if (hasattr(func, 'start_line') and hasattr(func, 'end_line') and
                    func.start_line <= line <= func.end_line):
                    return func.name
                elif hasattr(func, 'line_number') and func.line_number == line:
                    return func.name
                        
        except Exception as e:
            logger.debug(f"Error getting function at line: {e}")
        
        return None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all errors in the codebase."""
        try:
            all_errors = self.get_all_errors()
            all_warnings = self.get_all_warnings()
            all_diagnostics = self.get_all_diagnostics()
            
            # Group errors by file
            errors_by_file = defaultdict(list)
            for error in all_errors:
                errors_by_file[error.file_path].append(error)
            
            # Group errors by category
            errors_by_category = defaultdict(int)
            for error in all_errors:
                errors_by_category[error.category.value] += 1
            
            # Get codebase context
            codebase_context = get_codebase_summary(self.codebase)
            
            return {
                'total_errors': len(all_errors),
                'total_warnings': len(all_warnings),
                'total_diagnostics': len(all_diagnostics),
                'errors_by_file': dict(errors_by_file),
                'errors_by_category': dict(errors_by_category),
                'most_problematic_files': self._get_most_problematic_files(errors_by_file),
                'codebase_context': codebase_context,
                'lsp_available': self.lsp_bridge is not None,
                'analysis_capabilities': {
                    'graph_sitter_integration': True,
                    'context_analysis': True,
                    'blast_radius_calculation': True,
                    'fix_suggestions': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {'error': str(e)}
    
    def _get_most_problematic_files(self, errors_by_file: Dict[str, List[ErrorInfo]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get the files with the most errors."""
        file_error_counts = [(file_path, len(errors)) for file_path, errors in errors_by_file.items()]
        file_error_counts.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {'file_path': file_path, 'error_count': count}
            for file_path, count in file_error_counts[:limit]
        ]
    
    def refresh_analysis(self) -> None:
        """Refresh all analysis data."""
        try:
            # Clear caches
            self._error_cache.clear()
            self._parameter_cache.clear()
            self._call_graph_cache.clear()
            
            # Refresh LSP diagnostics
            if self.lsp_bridge:
                self.lsp_bridge.refresh_diagnostics()
            
            logger.info("Error analysis refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing analysis: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the error analyzer."""
        try:
            if self.lsp_bridge:
                self.lsp_bridge.shutdown()
            
            logger.info("Error analyzer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Convenience functions for easy import
def analyze_codebase_errors(codebase: Codebase, enable_lsp: bool = True) -> ComprehensiveErrorAnalyzer:
    """Create and return a comprehensive error analyzer for a codebase."""
    return ComprehensiveErrorAnalyzer(codebase, enable_lsp)


def get_instant_error_context(codebase: Codebase, file_path: str, line: int) -> Optional[ErrorContext]:
    """Get instant error context for a specific location."""
    analyzer = ComprehensiveErrorAnalyzer(codebase)
    
    # Find error at the specified location
    file_errors = analyzer.get_file_errors(file_path)
    for error in file_errors:
        if error.line == line:
            return analyzer.analyze_error_context(error)
    
    return None


def get_all_codebase_errors_with_context(codebase: Codebase) -> List[ErrorContext]:
    """Get all errors in the codebase with their complete contexts."""
    analyzer = ComprehensiveErrorAnalyzer(codebase)
    all_errors = analyzer.get_all_errors()
    
    error_contexts = []
    for error in all_errors:
        context = analyzer.analyze_error_context(error)
        error_contexts.append(context)
    
    return error_contexts

