"""
Serena Extension API

Main API interface for accessing all Serena error analysis and code intelligence capabilities.
Provides clean imports and easy access to comprehensive error analysis.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from .error_analysis import (
    ComprehensiveErrorAnalyzer,
    ErrorContext,
    ParameterIssue,
    FunctionCallInfo,
    analyze_codebase_errors,
    get_instant_error_context,
    get_all_codebase_errors_with_context
)
from .core import SerenaCore
from .semantic_tools import SemanticTools
from .mcp_bridge import SerenaMCPBridge, MCPToolResult
from .intelligence.code_intelligence import CodeIntelligence
from .symbols.symbol_intelligence import SymbolIntelligence
from .search.semantic_search import SemanticSearch

logger = get_logger(__name__)


class SerenaAPI:
    """
    Main API interface for Serena extension.
    
    Provides unified access to all error analysis and code intelligence capabilities.
    """
    
    def __init__(self, codebase: Codebase, enable_lsp: bool = True):
        """
        Initialize Serena API.
        
        Args:
            codebase: Graph-sitter codebase instance
            enable_lsp: Whether to enable LSP integration for enhanced analysis
        """
        self.codebase = codebase
        self.enable_lsp = enable_lsp
        
        # Initialize core components
        self.error_analyzer = ComprehensiveErrorAnalyzer(codebase, enable_lsp)
        self.core = SerenaCore(codebase)
        
        # Access to underlying components
        self.mcp_bridge = self.error_analyzer.mcp_bridge
        self.semantic_tools = self.error_analyzer.semantic_tools
        self.code_intelligence = self.error_analyzer.code_intelligence
        self.symbol_intelligence = self.error_analyzer.symbol_intelligence
        self.semantic_search = self.error_analyzer.semantic_search
        
        logger.info("Serena API initialized")
    
    # Error Analysis Methods
    def get_all_errors(self) -> List[Dict[str, Any]]:
        """Get all errors in the codebase with basic information."""
        errors = self.error_analyzer.get_all_errors()
        return [
            {
                'file_path': error.file_path,
                'line': error.line,
                'character': error.character,
                'message': error.message,
                'severity': error.severity.name if hasattr(error.severity, 'name') else str(error.severity),
                'source': error.source,
                'code': error.code
            }
            for error in errors
        ]
    
    def get_all_errors_with_context(self) -> List[Dict[str, Any]]:
        """Get all errors with comprehensive context analysis."""
        error_contexts = get_all_codebase_errors_with_context(self.codebase)
        
        return [
            {
                'error': {
                    'file_path': ctx.error_info.file_path,
                    'line': ctx.error_info.line,
                    'character': ctx.error_info.character,
                    'message': ctx.error_info.message,
                    'severity': ctx.error_info.severity.name if hasattr(ctx.error_info.severity, 'name') else str(ctx.error_info.severity)
                },
                'calling_functions': ctx.calling_functions,
                'called_functions': ctx.called_functions,
                'parameter_issues': ctx.parameter_issues,
                'dependency_chain': ctx.dependency_chain,
                'related_symbols': ctx.related_symbols,
                'code_context': ctx.code_context,
                'fix_suggestions': ctx.fix_suggestions
            }
            for ctx in error_contexts
        ]
    
    def get_file_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """Get errors for a specific file."""
        errors = self.error_analyzer.get_file_errors(file_path)
        return [
            {
                'file_path': error.file_path,
                'line': error.line,
                'character': error.character,
                'message': error.message,
                'severity': error.severity.name if hasattr(error.severity, 'name') else str(error.severity),
                'source': error.source,
                'code': error.code
            }
            for error in errors
        ]
    
    def get_error_context(self, file_path: str, line: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive context for an error at a specific location."""
        context = get_instant_error_context(self.codebase, file_path, line)
        
        if not context:
            return None
        
        return {
            'error': {
                'file_path': context.error_info.file_path,
                'line': context.error_info.line,
                'character': context.error_info.character,
                'message': context.error_info.message,
                'severity': context.error_info.severity.name if hasattr(context.error_info.severity, 'name') else str(context.error_info.severity)
            },
            'calling_functions': context.calling_functions,
            'called_functions': context.called_functions,
            'parameter_issues': context.parameter_issues,
            'dependency_chain': context.dependency_chain,
            'related_symbols': context.related_symbols,
            'code_context': context.code_context,
            'fix_suggestions': context.fix_suggestions
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all errors in the codebase."""
        return self.error_analyzer.get_error_summary()
    
    def get_unused_parameters(self) -> List[Dict[str, Any]]:
        """Get all unused parameters across the codebase."""
        unused_params = []
        
        # Analyze all errors to find parameter issues
        error_contexts = get_all_codebase_errors_with_context(self.codebase)
        
        for context in error_contexts:
            for param_issue in context.parameter_issues:
                if param_issue.get('issue_type') == 'unused':
                    unused_params.append({
                        'parameter_name': param_issue.get('parameter_name'),
                        'function_name': param_issue.get('function_name'),
                        'file_path': context.error_info.file_path,
                        'line_number': context.error_info.line,
                        'suggestion': param_issue.get('suggestion')
                    })
        
        return unused_params
    
    def get_wrong_parameters(self) -> List[Dict[str, Any]]:
        """Get all wrongly typed/set parameters across the codebase."""
        wrong_params = []
        
        # Analyze all errors to find parameter issues
        error_contexts = get_all_codebase_errors_with_context(self.codebase)
        
        for context in error_contexts:
            for param_issue in context.parameter_issues:
                if param_issue.get('issue_type') in ['wrong_type', 'invalid_value']:
                    wrong_params.append({
                        'parameter_name': param_issue.get('parameter_name'),
                        'function_name': param_issue.get('function_name'),
                        'file_path': context.error_info.file_path,
                        'line_number': context.error_info.line,
                        'issue_type': param_issue.get('issue_type'),
                        'expected_type': param_issue.get('expected_type'),
                        'actual_type': param_issue.get('actual_type'),
                        'suggestion': param_issue.get('suggestion')
                    })
        
        return wrong_params
    
    # Function Call Analysis Methods
    def get_function_callers(self, function_name: str, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all functions that call a specific function."""
        callers = []
        
        if self.semantic_search:
            search_results = self.semantic_search.semantic_search(
                f"calls to {function_name}", max_results=50
            )
            
            for result in search_results:
                if not file_path or result.get('file') != file_path:
                    callers.append({
                        'caller_function': result.get('symbol_name', 'unknown'),
                        'file_path': result.get('file', ''),
                        'line_number': result.get('line', 0),
                        'context': result.get('context', ''),
                        'relevance_score': result.get('score', 0.0)
                    })
        
        return callers
    
    def get_function_calls(self, function_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Get all functions called by a specific function."""
        calls = []
        
        if self.code_intelligence:
            # This would use code intelligence to find function calls
            # For now, we'll return empty list as this requires more complex analysis
            pass
        
        return calls
    
    # Dependency Analysis Methods
    def get_file_dependencies(self, file_path: str) -> List[str]:
        """Get all dependencies for a specific file."""
        if hasattr(self.error_analyzer, '_build_dependency_chain'):
            return self.error_analyzer._build_dependency_chain(file_path)
        return []
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get dependency graph for the entire codebase."""
        dependency_graph = {}
        
        for file_obj in self.codebase.files:
            if file_obj.file_path.endswith('.py'):
                dependencies = self.get_file_dependencies(file_obj.file_path)
                dependency_graph[file_obj.file_path] = dependencies
        
        return dependency_graph
    
    # Symbol Analysis Methods
    def find_symbol_usage(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find all usages of a symbol across the codebase."""
        usages = []
        
        if self.semantic_search:
            search_results = self.semantic_search.semantic_search(
                symbol_name, max_results=100
            )
            
            for result in search_results:
                usages.append({
                    'symbol_name': result.get('symbol_name', symbol_name),
                    'symbol_type': result.get('symbol_type', 'unknown'),
                    'file_path': result.get('file', ''),
                    'line_number': result.get('line', 0),
                    'context': result.get('context', ''),
                    'relevance_score': result.get('score', 0.0)
                })
        
        return usages
    
    def get_related_symbols(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Get symbols related to a given symbol."""
        related = []
        
        if self.semantic_search:
            search_results = self.semantic_search.semantic_search(
                f"related to {symbol_name}", max_results=20
            )
            
            for result in search_results:
                related.append({
                    'symbol_name': result.get('symbol_name', 'unknown'),
                    'symbol_type': result.get('symbol_type', 'unknown'),
                    'file_path': result.get('file', ''),
                    'line_number': result.get('line', 0),
                    'relationship': 'related',
                    'relevance_score': result.get('score', 0.0)
                })
        
        return related
    
    # Utility Methods
    def refresh_analysis(self) -> None:
        """Refresh all analysis data."""
        self.error_analyzer.refresh_analysis()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all Serena components."""
        return {
            'error_analyzer_initialized': self.error_analyzer is not None,
            'mcp_bridge_available': self.mcp_bridge is not None and self.mcp_bridge.is_initialized,
            'semantic_tools_available': self.semantic_tools is not None,
            'code_intelligence_available': self.code_intelligence is not None,
            'symbol_intelligence_available': self.symbol_intelligence is not None,
            'semantic_search_available': self.semantic_search is not None,
            'lsp_enabled': self.error_analyzer.diagnostics.is_lsp_enabled(),
            'lsp_status': self.error_analyzer.diagnostics.get_lsp_status(),
            'total_errors': len(self.error_analyzer.get_all_errors()),
            'total_warnings': len(self.error_analyzer.get_all_warnings()),
            'total_diagnostics': len(self.error_analyzer.get_all_diagnostics())
        }
    
    def shutdown(self) -> None:
        """Shutdown all Serena components."""
        if self.error_analyzer:
            self.error_analyzer.shutdown()
        
        if self.core:
            self.core.shutdown()
        
        logger.info("Serena API shutdown complete")


# Convenience functions for easy access
def create_serena_api(codebase: Codebase, enable_lsp: bool = True) -> SerenaAPI:
    """Create a Serena API instance for a codebase."""
    return SerenaAPI(codebase, enable_lsp)


def get_codebase_error_analysis(codebase: Codebase) -> Dict[str, Any]:
    """Get comprehensive error analysis for a codebase."""
    api = SerenaAPI(codebase)
    try:
        return {
            'error_summary': api.get_error_summary(),
            'all_errors_with_context': api.get_all_errors_with_context(),
            'unused_parameters': api.get_unused_parameters(),
            'wrong_parameters': api.get_wrong_parameters(),
            'dependency_graph': api.get_dependency_graph(),
            'status': api.get_status()
        }
    finally:
        api.shutdown()


def analyze_file_errors(codebase: Codebase, file_path: str) -> Dict[str, Any]:
    """Get comprehensive error analysis for a specific file."""
    api = SerenaAPI(codebase)
    try:
        file_errors = api.get_file_errors(file_path)
        error_contexts = []
        
        for error in file_errors:
            context = api.get_error_context(error['file_path'], error['line'])
            if context:
                error_contexts.append(context)
        
        return {
            'file_path': file_path,
            'errors': file_errors,
            'error_contexts': error_contexts,
            'dependencies': api.get_file_dependencies(file_path)
        }
    finally:
        api.shutdown()


def find_function_relationships(codebase: Codebase, function_name: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Find all relationships for a function (callers, callees, related symbols)."""
    api = SerenaAPI(codebase)
    try:
        return {
            'function_name': function_name,
            'file_path': file_path,
            'callers': api.get_function_callers(function_name, file_path),
            'calls': api.get_function_calls(function_name, file_path) if file_path else [],
            'symbol_usage': api.find_symbol_usage(function_name),
            'related_symbols': api.get_related_symbols(function_name)
        }
    finally:
        api.shutdown()
