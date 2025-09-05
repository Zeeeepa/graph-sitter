"""
Comprehensive Error Analysis System for Graph-Sitter & Serena

This module provides comprehensive error detection, context analysis, and dependency tracking
using existing graph-sitter and Serena capabilities without reinventing the wheel.
"""

import ast
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
import traceback

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.diagnostics import CodebaseDiagnostics, add_diagnostic_capabilities
from graph_sitter.extensions.lsp.serena_bridge import ErrorInfo, SerenaLSPBridge
from .mcp_bridge import SerenaMCPBridge, MCPToolResult
from .semantic_tools import SemanticTools
from .intelligence.code_intelligence import CodeIntelligence
from .symbols.symbol_intelligence import SymbolIntelligence
from .search.semantic_search import SemanticSearch

logger = get_logger(__name__)


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error_info: ErrorInfo
    calling_functions: List[Dict[str, Any]] = field(default_factory=list)
    called_functions: List[Dict[str, Any]] = field(default_factory=list)
    parameter_issues: List[Dict[str, Any]] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    related_symbols: List[Dict[str, Any]] = field(default_factory=list)
    code_context: Optional[str] = None
    fix_suggestions: List[str] = field(default_factory=list)


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
    Comprehensive error analyzer that leverages existing graph-sitter and Serena capabilities.
    
    Uses existing components:
    - CodebaseDiagnostics for error detection
    - SemanticTools for code analysis
    - CodeIntelligence for symbol information
    - SymbolIntelligence for dependency tracking
    - SemanticSearch for finding related code
    """
    
    def __init__(self, codebase: Codebase, enable_lsp: bool = True):
        self.codebase = codebase
        
        # Ensure diagnostic capabilities are added
        if not hasattr(codebase, '_diagnostics'):
            add_diagnostic_capabilities(codebase, enable_lsp)
        
        self.diagnostics = codebase._diagnostics
        
        # Initialize Serena components if available
        self.mcp_bridge = None
        self.semantic_tools = None
        self.code_intelligence = None
        self.symbol_intelligence = None
        self.semantic_search = None
        
        self._initialize_serena_components()
        
        # Error analysis cache
        self._error_cache: Dict[str, ErrorContext] = {}
        self._parameter_cache: Dict[str, List[ParameterIssue]] = {}
        self._call_graph_cache: Dict[str, List[FunctionCallInfo]] = {}
        
        logger.info("Comprehensive error analyzer initialized")
    
    def _initialize_serena_components(self) -> None:
        """Initialize Serena components if available."""
        try:
            # Initialize MCP bridge
            self.mcp_bridge = SerenaMCPBridge(str(self.codebase.repo_path))
            
            if self.mcp_bridge.is_initialized:
                # Initialize semantic tools
                self.semantic_tools = SemanticTools(self.mcp_bridge)
                
                # Initialize intelligence components
                self.code_intelligence = CodeIntelligence(self.codebase, self.mcp_bridge)
                
                # Initialize LSP bridge if available
                lsp_bridge = None
                if self.diagnostics.is_lsp_enabled():
                    lsp_bridge = self.diagnostics._lsp_manager.language_server if hasattr(self.diagnostics._lsp_manager, 'language_server') else None
                
                if lsp_bridge:
                    self.symbol_intelligence = SymbolIntelligence(self.codebase, lsp_bridge)
                    self.semantic_search = SemanticSearch(self.codebase, lsp_bridge)
                
                logger.info("Serena components initialized successfully")
            else:
                logger.warning("Serena MCP bridge not available - using basic analysis only")
                
        except Exception as e:
            logger.warning(f"Failed to initialize Serena components: {e}")
    
    def get_all_errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase using existing diagnostics."""
        return self.diagnostics.errors
    
    def get_all_warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase using existing diagnostics."""
        return self.diagnostics.warnings
    
    def get_all_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) using existing diagnostics."""
        return self.diagnostics.diagnostics
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file using existing diagnostics."""
        return self.diagnostics.get_file_errors(file_path)
    
    def analyze_error_context(self, error: ErrorInfo) -> ErrorContext:
        """
        Analyze comprehensive context for an error using existing capabilities.
        
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
            
            # Generate fix suggestions
            context.fix_suggestions = self._generate_fix_suggestions(error, context)
            
            # Cache the result
            self._error_cache[error_key] = context
            
        except Exception as e:
            logger.error(f"Error analyzing context for {error_key}: {e}")
            logger.debug(traceback.format_exc())
        
        return context
    
    def _get_code_context(self, file_path: str, line: int, context_lines: int = 5) -> Optional[str]:
        """Get code context around an error line."""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return None
            
            lines = file_obj.content.split('\n')
            start_line = max(0, line - context_lines - 1)
            end_line = min(len(lines), line + context_lines)
            
            context_lines_list = []
            for i in range(start_line, end_line):
                prefix = ">>> " if i == line - 1 else "    "
                context_lines_list.append(f"{prefix}{i+1:4d}: {lines[i]}")
            
            return '\n'.join(context_lines_list)
            
        except Exception as e:
            logger.error(f"Error getting code context: {e}")
            return None
    
    def _find_calling_functions(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find functions that call the error point using existing capabilities."""
        calling_functions = []
        
        try:
            # Use semantic search to find callers if available
            if self.semantic_search:
                # Get the function name at the error line
                function_name = self._get_function_at_line(file_path, line)
                if function_name:
                    # Search for calls to this function
                    search_results = self.semantic_search.semantic_search(
                        f"calls to {function_name}", max_results=20
                    )
                    
                    for result in search_results:
                        if result.get('file') != file_path or result.get('line') != line:
                            calling_functions.append({
                                'function_name': result.get('symbol_name', 'unknown'),
                                'file_path': result.get('file', ''),
                                'line_number': result.get('line', 0),
                                'context': result.get('context', ''),
                                'score': result.get('score', 0.0)
                            })
            
            # Fallback: analyze AST to find callers
            if not calling_functions:
                calling_functions = self._find_callers_via_ast(file_path, line)
                
        except Exception as e:
            logger.error(f"Error finding calling functions: {e}")
        
        return calling_functions
    
    def _find_called_functions(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find functions called by the error point using existing capabilities."""
        called_functions = []
        
        try:
            # Get code intelligence hover info if available
            if self.code_intelligence:
                hover_info = self.code_intelligence.get_hover_info(file_path, line, 0)
                if hover_info and 'calls' in hover_info:
                    for call in hover_info['calls']:
                        called_functions.append({
                            'function_name': call.get('name', 'unknown'),
                            'file_path': call.get('file', file_path),
                            'line_number': call.get('line', 0),
                            'parameters': call.get('parameters', []),
                            'return_type': call.get('return_type')
                        })
            
            # Fallback: analyze AST to find called functions
            if not called_functions:
                called_functions = self._find_called_via_ast(file_path, line)
                
        except Exception as e:
            logger.error(f"Error finding called functions: {e}")
        
        return called_functions
    
    def _analyze_parameter_issues(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Analyze parameter usage issues using existing capabilities."""
        parameter_issues = []
        
        try:
            # Use semantic tools to get symbol context if available
            if self.semantic_tools:
                symbol_context = self.semantic_tools.get_symbol_context(file_path, line, 0)
                if symbol_context and 'parameters' in symbol_context:
                    for param in symbol_context['parameters']:
                        if param.get('unused') or param.get('wrong_type'):
                            parameter_issues.append({
                                'issue_type': 'unused' if param.get('unused') else 'wrong_type',
                                'parameter_name': param.get('name', 'unknown'),
                                'function_name': symbol_context.get('function_name', 'unknown'),
                                'expected_type': param.get('expected_type'),
                                'actual_type': param.get('actual_type'),
                                'suggestion': param.get('suggestion')
                            })
            
            # Fallback: analyze AST for parameter issues
            if not parameter_issues:
                parameter_issues = self._analyze_parameters_via_ast(file_path, line)
                
        except Exception as e:
            logger.error(f"Error analyzing parameter issues: {e}")
        
        return parameter_issues
    
    def _build_dependency_chain(self, file_path: str) -> List[str]:
        """Build dependency chain for a file using existing capabilities."""
        dependency_chain = []
        
        try:
            # Use symbol intelligence if available
            if self.symbol_intelligence:
                # This would use the existing symbol intelligence to map dependencies
                # For now, we'll use a basic approach
                pass
            
            # Fallback: analyze imports
            file_obj = self.codebase.get_file(file_path)
            if file_obj:
                try:
                    tree = ast.parse(file_obj.content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                dependency_chain.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                dependency_chain.append(node.module)
                except SyntaxError:
                    pass  # Skip files with syntax errors
                    
        except Exception as e:
            logger.error(f"Error building dependency chain: {e}")
        
        return dependency_chain
    
    def _find_related_symbols(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find symbols related to the error point using existing capabilities."""
        related_symbols = []
        
        try:
            # Use semantic search to find related symbols
            if self.semantic_search:
                function_name = self._get_function_at_line(file_path, line)
                if function_name:
                    search_results = self.semantic_search.semantic_search(
                        f"related to {function_name}", max_results=10
                    )
                    
                    for result in search_results:
                        related_symbols.append({
                            'symbol_name': result.get('symbol_name', 'unknown'),
                            'symbol_type': result.get('symbol_type', 'unknown'),
                            'file_path': result.get('file', ''),
                            'line_number': result.get('line', 0),
                            'relevance_score': result.get('score', 0.0),
                            'context': result.get('context', '')
                        })
                        
        except Exception as e:
            logger.error(f"Error finding related symbols: {e}")
        
        return related_symbols
    
    def _generate_fix_suggestions(self, error: ErrorInfo, context: ErrorContext) -> List[str]:
        """Generate fix suggestions based on error and context."""
        suggestions = []
        
        try:
            # Basic suggestions based on error message
            error_msg = error.message.lower()
            
            if "undefined" in error_msg or "not defined" in error_msg:
                suggestions.append("Check if the variable or function is properly imported")
                suggestions.append("Verify the spelling of the identifier")
                
            if "syntax error" in error_msg:
                suggestions.append("Check for missing parentheses, brackets, or quotes")
                suggestions.append("Verify proper indentation")
                
            if "type" in error_msg and "error" in error_msg:
                suggestions.append("Check parameter types and function signatures")
                suggestions.append("Verify return type annotations")
                
            if "import" in error_msg:
                suggestions.append("Check if the module is installed")
                suggestions.append("Verify the import path is correct")
                
            # Context-based suggestions
            if context.parameter_issues:
                suggestions.append("Review parameter usage and types")
                
            if context.calling_functions:
                suggestions.append("Check how this function is being called")
                
            if not suggestions:
                suggestions.append("Review the code context and related functions")
                
        except Exception as e:
            logger.error(f"Error generating fix suggestions: {e}")
        
        return suggestions
    
    def _get_function_at_line(self, file_path: str, line: int) -> Optional[str]:
        """Get the function name at a specific line."""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return None
            
            tree = ast.parse(file_obj.content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno'):
                    if node.lineno <= line <= getattr(node, 'end_lineno', node.lineno):
                        return node.name
                        
        except Exception as e:
            logger.debug(f"Error getting function at line: {e}")
        
        return None
    
    def _find_callers_via_ast(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find callers using AST analysis as fallback."""
        callers = []
        
        try:
            function_name = self._get_function_at_line(file_path, line)
            if not function_name:
                return callers
            
            # Search through all Python files in the codebase
            for file_obj in self.codebase.files:
                if not file_obj.file_path.endswith('.py'):
                    continue
                    
                try:
                    tree = ast.parse(file_obj.content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name) and node.func.id == function_name:
                                callers.append({
                                    'function_name': self._get_function_at_line(file_obj.file_path, node.lineno) or 'module_level',
                                    'file_path': file_obj.file_path,
                                    'line_number': node.lineno,
                                    'context': f"Call to {function_name}",
                                    'score': 1.0
                                })
                except SyntaxError:
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding callers via AST: {e}")
        
        return callers
    
    def _find_called_via_ast(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Find called functions using AST analysis as fallback."""
        called = []
        
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return called
            
            tree = ast.parse(file_obj.content)
            
            # Find the function containing the error line
            target_function = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno'):
                    if node.lineno <= line <= getattr(node, 'end_lineno', node.lineno):
                        target_function = node
                        break
            
            if target_function:
                # Find all function calls within this function
                for node in ast.walk(target_function):
                    if isinstance(node, ast.Call):
                        func_name = None
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        
                        if func_name:
                            called.append({
                                'function_name': func_name,
                                'file_path': file_path,
                                'line_number': node.lineno,
                                'parameters': [arg.__class__.__name__ for arg in node.args],
                                'return_type': None
                            })
                            
        except Exception as e:
            logger.error(f"Error finding called functions via AST: {e}")
        
        return called
    
    def _analyze_parameters_via_ast(self, file_path: str, line: int) -> List[Dict[str, Any]]:
        """Analyze parameter issues using AST as fallback."""
        issues = []
        
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return issues
            
            tree = ast.parse(file_obj.content)
            
            # Find function definitions and analyze parameters
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno'):
                    if node.lineno <= line <= getattr(node, 'end_lineno', node.lineno):
                        # Analyze function parameters
                        used_params = set()
                        
                        # Find parameter usage in function body
                        for child in ast.walk(node):
                            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                                used_params.add(child.id)
                        
                        # Check for unused parameters
                        for arg in node.args.args:
                            if arg.arg not in used_params and not arg.arg.startswith('_'):
                                issues.append({
                                    'issue_type': 'unused',
                                    'parameter_name': arg.arg,
                                    'function_name': node.name,
                                    'suggestion': f"Remove unused parameter '{arg.arg}' or prefix with underscore"
                                })
                        
                        break
                        
        except Exception as e:
            logger.error(f"Error analyzing parameters via AST: {e}")
        
        return issues
    
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
            
            # Group errors by type
            errors_by_type = defaultdict(int)
            for error in all_errors:
                error_type = self._classify_error_type(error.message)
                errors_by_type[error_type] += 1
            
            return {
                'total_errors': len(all_errors),
                'total_warnings': len(all_warnings),
                'total_diagnostics': len(all_diagnostics),
                'errors_by_file': dict(errors_by_file),
                'errors_by_type': dict(errors_by_type),
                'most_problematic_files': self._get_most_problematic_files(errors_by_file),
                'lsp_status': self.diagnostics.get_lsp_status(),
                'serena_available': self.mcp_bridge is not None and self.mcp_bridge.is_initialized
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {'error': str(e)}
    
    def _classify_error_type(self, message: str) -> str:
        """Classify error type based on message."""
        message_lower = message.lower()
        
        if "syntax" in message_lower:
            return "syntax_error"
        elif "import" in message_lower:
            return "import_error"
        elif "undefined" in message_lower or "not defined" in message_lower:
            return "undefined_error"
        elif "type" in message_lower:
            return "type_error"
        elif "attribute" in message_lower:
            return "attribute_error"
        else:
            return "other_error"
    
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
            
            # Refresh diagnostics
            self.diagnostics.refresh_diagnostics()
            
            logger.info("Error analysis refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing analysis: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the error analyzer."""
        try:
            if self.mcp_bridge:
                self.mcp_bridge.shutdown()
            
            if hasattr(self.diagnostics, 'shutdown'):
                self.diagnostics.shutdown()
            
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
