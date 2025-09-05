"""
Serena LSP Bridge for Graph-Sitter

This module provides a comprehensive bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, including runtime error collection,
context analysis, and intelligent fix suggestions.
"""

import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set, Callable
from collections import defaultdict
from enum import IntEnum
import weakref

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary, get_file_summary, get_class_summary, get_function_summary, get_symbol_summary
from .runtime_collector import RuntimeErrorCollector, RuntimeContext

logger = get_logger(__name__)

# Error type enumeration for runtime error classification
class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues

# Optional Serena imports with graceful fallback
SERENA_AVAILABLE = False
try:
    # Core solidlsp imports
    from solidlsp.ls_types import DiagnosticSeverity, Diagnostic, Position, Range, MarkupContent, Location, MarkupKind, CompletionItemKind, CompletionItem, UnifiedSymbolInformation, SymbolKind, SymbolTag
    from solidlsp.ls_utils import TextUtils, PathUtils, FileUtils, PlatformId, SymbolUtils
    from solidlsp.ls_request import LanguageServerRequest
    from solidlsp.ls_logger import LanguageServerLogger, LogLine
    from solidlsp.ls_handler import SolidLanguageServerHandler, Request, LanguageServerTerminatedException
    from solidlsp.ls import SolidLanguageServer, LSPFileBuffer
    from solidlsp.lsp_protocol_handler.lsp_constants import LSPConstants
    from solidlsp.lsp_protocol_handler.lsp_requests import LspRequest
    from solidlsp.lsp_protocol_handler.lsp_types import *
    from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo, LSPError, MessageType
    
    # Serena imports
    from serena.symbol import LanguageServerSymbolRetriever, ReferenceInLanguageServerSymbol, LanguageServerSymbol, Symbol, PositionInFile, LanguageServerSymbolLocation
    from serena.text_utils import MatchedConsecutiveLines, TextLine, LineType
    from serena.project import Project
    from serena.gui_log_viewer import GuiLogViewer, LogLevel, GuiLogViewerHandler
    from serena.code_editor import CodeEditor
    from serena.cli import PromptCommands, ToolCommands, ProjectCommands, SerenaConfigCommands, ContextCommands, ModeCommands, TopLevelCommands, AutoRegisteringGroup, ProjectType
    
    SERENA_AVAILABLE = True
    logger.info("Serena components successfully imported")
    
except ImportError as e:
    logger.info(f"Serena components not available, using basic LSP functionality: {e}")
    # Define minimal fallback classes for essential types
    from enum import IntEnum
    
    class DiagnosticSeverity(IntEnum):
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4
    
    @dataclass
    class Position:
        line: int
        character: int
    
    @dataclass
    class Range:
        start: Position
        end: Position
    
    @dataclass
    class Diagnostic:
        range: Range
        message: str
        severity: Optional[DiagnosticSeverity] = None
        code: Optional[Union[str, int]] = None
        source: Optional[str] = None
    
    class SolidLanguageServer:
        def __init__(self, *args, **kwargs):
            pass
    
    class Project:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class ErrorInfo:
    """
    Comprehensive error information for graph-sitter with runtime context support.
    
    This class extends basic error information with runtime context, fix suggestions,
    and comprehensive analysis capabilities.
    """
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    error_type: ErrorType = ErrorType.STATIC_ANALYSIS
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    # Enhanced runtime context support
    runtime_context: Optional[RuntimeContext] = None
    fix_suggestions: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    context_lines: List[str] = field(default_factory=list)
    
    # Serena-specific enhancements
    symbol_info: Optional[Dict[str, Any]] = None
    dependency_info: Optional[Dict[str, Any]] = None
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning or hint)."""
        return self.severity == DiagnosticSeverity.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity == DiagnosticSeverity.WARNING
    
    @property
    def is_hint(self) -> bool:
        """Check if this is a hint."""
        return self.severity == DiagnosticSeverity.HINT
    
    @property
    def is_runtime_error(self) -> bool:
        """Check if this is a runtime error."""
        return self.error_type == ErrorType.RUNTIME_ERROR
    
    @property
    def has_runtime_context(self) -> bool:
        """Check if runtime context is available."""
        return self.runtime_context is not None
    
    @property
    def has_fix_suggestions(self) -> bool:
        """Check if fix suggestions are available."""
        return len(self.fix_suggestions) > 0
    
    def get_position(self) -> Position:
        """Get LSP Position object."""
        return Position(line=self.line, character=self.character)
    
    def get_range(self) -> Range:
        """Get LSP Range object."""
        start = Position(line=self.line, character=self.character)
        end = Position(
            line=self.end_line if self.end_line is not None else self.line,
            character=self.end_character if self.end_character is not None else self.character + 1
        )
        return Range(start=start, end=end)
    
    def to_diagnostic(self) -> Diagnostic:
        """Convert to LSP Diagnostic object."""
        return Diagnostic(
            range=self.get_range(),
            message=self.message,
            severity=self.severity,
            code=self.code,
            source=self.source
        )
    
    def get_context_summary(self) -> str:
        """Get a summary of the error context."""
        summary_parts = [f"{self.severity.name}: {self.message}"]
        
        if self.runtime_context:
            summary_parts.append(f"Runtime: {self.runtime_context.exception_type}")
            if self.runtime_context.stack_trace:
                summary_parts.append(f"Stack depth: {len(self.runtime_context.stack_trace)}")
        
        if self.fix_suggestions:
            summary_parts.append(f"Suggestions: {len(self.fix_suggestions)}")
        
        return " | ".join(summary_parts)
    
    def __str__(self) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "ERROR",
            DiagnosticSeverity.WARNING: "WARNING", 
            DiagnosticSeverity.INFORMATION: "INFO",
            DiagnosticSeverity.HINT: "HINT"
        }.get(self.severity, "UNKNOWN")
        
        context_str = ""
        if self.runtime_context:
            context_str = f" [{self.runtime_context.exception_type}]"
        
        return f"{severity_str} {self.file_path}:{self.line}:{self.character} - {self.message}{context_str}"


class SerenaLSPBridge:
    """
    Comprehensive bridge between Serena's LSP implementation and graph-sitter.
    
    This class provides:
    - Runtime error collection and analysis
    - Serena LSP integration with graceful fallback
    - Comprehensive error context analysis
    - Intelligent fix suggestion generation
    - Thread-safe operations with proper resource management
    """
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True):
        self.repo_path = Path(repo_path)
        self.enable_runtime_collection = enable_runtime_collection
        
        # Core components
        self.runtime_collector: Optional[RuntimeErrorCollector] = None
        self.serena_server: Optional[SolidLanguageServer] = None
        self.project: Optional[Project] = None
        self.codebase: Optional[Codebase] = None
        
        # Error storage and management
        self.static_errors: List[ErrorInfo] = []
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.error_handlers: List[Callable[[ErrorInfo], None]] = []
        
        # State management
        self.is_initialized = False
        self._lock = threading.RLock()
        self._shutdown_requested = False
        
        # Performance tracking
        self._stats = {
            'total_errors_collected': 0,
            'runtime_errors_collected': 0,
            'static_errors_collected': 0,
            'fix_suggestions_generated': 0,
            'serena_queries': 0,
            'initialization_time': 0.0
        }
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the LSP bridge with all components."""
        start_time = time.time()
        
        try:
            # Initialize runtime error collection
            if self.enable_runtime_collection:
                self._initialize_runtime_collector()
            
            # Initialize Serena components if available
            if SERENA_AVAILABLE:
                self._initialize_serena_components()
            
            self.is_initialized = True
            self._stats['initialization_time'] = time.time() - start_time
            
            logger.info(f"SerenaLSPBridge initialized for {self.repo_path} "
                       f"(runtime_collection={self.enable_runtime_collection}, "
                       f"serena_available={SERENA_AVAILABLE}) "
                       f"in {self._stats['initialization_time']:.3f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize SerenaLSPBridge: {e}")
            self.is_initialized = False
    
    def _initialize_runtime_collector(self) -> None:
        """Initialize the runtime error collector."""
        try:
            self.runtime_collector = RuntimeErrorCollector(str(self.repo_path))
            self.runtime_collector.add_error_handler(self._handle_runtime_error)
            self.runtime_collector.start_collection()
            logger.info("Runtime error collector initialized and started")
            
        except Exception as e:
            logger.error(f"Failed to initialize runtime error collector: {e}")
            self.runtime_collector = None
    
    def _initialize_serena_components(self) -> None:
        """Initialize Serena LSP components."""
        try:
            # Initialize graph-sitter codebase
            self.codebase = Codebase(repo_path=str(self.repo_path))
            
            # Create Serena project
            if SERENA_AVAILABLE:
                self.project = Project(str(self.repo_path))
            
            # Initialize Serena language server
            # Note: This is a placeholder - actual initialization depends on Serena setup
            # self.serena_server = SolidLanguageServer(str(self.repo_path))
            
            logger.info("Serena components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Serena components: {e}")
            self.serena_server = None
            self.project = None
            self.codebase = None
    
    def _handle_runtime_error(self, error_info: ErrorInfo) -> None:
        """Handle runtime errors from the collector."""
        try:
            with self._lock:
                # Update statistics
                self._stats['total_errors_collected'] += 1
                self._stats['runtime_errors_collected'] += 1
                
                # Enhance error with additional context if Serena is available
                if SERENA_AVAILABLE and self.serena_server:
                    self._enhance_error_with_serena(error_info)
                
                # Generate additional fix suggestions
                additional_suggestions = self._generate_contextual_fix_suggestions(error_info)
                error_info.fix_suggestions.extend(additional_suggestions)
                
                if additional_suggestions:
                    self._stats['fix_suggestions_generated'] += len(additional_suggestions)
                
                # Notify external handlers
                for handler in self.error_handlers:
                    try:
                        handler(error_info)
                    except Exception as e:
                        logger.error(f"Error in external error handler: {e}")
            
            logger.debug(f"Processed runtime error: {error_info}")
            
        except Exception as e:
            logger.error(f"Failed to handle runtime error: {e}")
    
    def _enhance_error_with_serena(self, error_info: ErrorInfo) -> None:
        """Enhance error information using Serena capabilities."""
        try:
            # Use graph-sitter codebase analysis
            if self.codebase:
                try:
                    # Get file summary for context
                    file_summary = get_file_summary(self.codebase, error_info.file_path)
                    if file_summary:
                        error_info.context_lines = file_summary.get('content_preview', [])
                        error_info.related_symbols = [s['name'] for s in file_summary.get('symbols', [])]
                    
                    # Get symbol information if available
                    symbol_summary = get_symbol_summary(self.codebase, error_info.file_path, error_info.line)
                    if symbol_summary:
                        error_info.symbol_info = symbol_summary
                        
                except Exception as e:
                    logger.debug(f"Graph-sitter analysis failed: {e}")
            
            # Use Serena-specific enhancements if available
            if SERENA_AVAILABLE and self.project:
                try:
                    # Serena symbol retrieval
                    symbol_retriever = LanguageServerSymbolRetriever(self.project)
                    position = PositionInFile(error_info.file_path, error_info.line, error_info.character)
                    
                    # Get symbol at position
                    symbols = symbol_retriever.get_symbols_at_position(position)
                    if symbols:
                        error_info.symbol_info = {
                            'serena_symbols': [s.to_dict() for s in symbols if hasattr(s, 'to_dict')]
                        }
                        
                except Exception as e:
                    logger.debug(f"Serena symbol analysis failed: {e}")
            
            self._stats['serena_queries'] += 1
            logger.debug(f"Enhanced error with analysis: {error_info.file_path}:{error_info.line}")
            
        except Exception as e:
            logger.error(f"Failed to enhance error with analysis: {e}")
    
    def _generate_contextual_fix_suggestions(self, error_info: ErrorInfo) -> List[str]:
        """Generate contextual fix suggestions based on error analysis."""
        suggestions = []
        
        try:
            # Analyze error context for additional suggestions
            if error_info.runtime_context:
                context = error_info.runtime_context
                
                # Analyze stack trace for patterns
                if context.stack_trace:
                    suggestions.extend(self._analyze_stack_trace_patterns(context.stack_trace))
                
                # Analyze variable states
                if context.local_variables:
                    suggestions.extend(self._analyze_variable_states(context.local_variables))
                
                # Analyze execution path
                if context.execution_path:
                    suggestions.extend(self._analyze_execution_path(context.execution_path))
            
            # File-specific analysis
            suggestions.extend(self._analyze_file_context(error_info))
            
        except Exception as e:
            logger.error(f"Failed to generate contextual fix suggestions: {e}")
        
        return suggestions[:3]  # Limit to top 3 additional suggestions
    
    def _analyze_stack_trace_patterns(self, stack_trace: List[str]) -> List[str]:
        """Analyze stack trace for common patterns and suggest fixes."""
        suggestions = []
        
        try:
            stack_text = "\n".join(stack_trace).lower()
            
            if "recursion" in stack_text or "maximum recursion depth" in stack_text:
                suggestions.append("Add base case to prevent infinite recursion")
            
            if "import" in stack_text and "error" in stack_text:
                suggestions.append("Check module installation and import paths")
            
            if "connection" in stack_text or "network" in stack_text:
                suggestions.append("Add network error handling and retry logic")
            
        except Exception as e:
            logger.debug(f"Failed to analyze stack trace patterns: {e}")
        
        return suggestions
    
    def _analyze_variable_states(self, variables: Dict[str, Any]) -> List[str]:
        """Analyze variable states for potential issues."""
        suggestions = []
        
        try:
            for name, value in variables.items():
                value_str = str(value).lower()
                
                if value_str == "none":
                    suggestions.append(f"Check if {name} should be None - add None check")
                elif value_str == "[]" or value_str == "{}":
                    suggestions.append(f"Check if empty {name} is expected - add empty check")
                elif "error" in value_str or "exception" in value_str:
                    suggestions.append(f"Handle {name} error condition properly")
            
        except Exception as e:
            logger.debug(f"Failed to analyze variable states: {e}")
        
        return suggestions[:2]  # Limit suggestions
    
    def _analyze_execution_path(self, execution_path: List[str]) -> List[str]:
        """Analyze execution path for patterns."""
        suggestions = []
        
        try:
            if len(execution_path) > 10:
                suggestions.append("Consider breaking down complex execution path")
            
            if execution_path.count("<module>") > 3:
                suggestions.append("Consider organizing code into functions/classes")
            
        except Exception as e:
            logger.debug(f"Failed to analyze execution path: {e}")
        
        return suggestions
    
    def _analyze_file_context(self, error_info: ErrorInfo) -> List[str]:
        """Analyze file context around the error."""
        suggestions = []
        
        try:
            file_path = self.repo_path / error_info.file_path
            if file_path.exists() and file_path.suffix == '.py':
                # Read file content around error line
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                error_line_idx = error_info.line
                if 0 <= error_line_idx < len(lines):
                    error_line = lines[error_line_idx].strip()
                    
                    # Analyze the error line for common patterns
                    if error_line.startswith('import ') or error_line.startswith('from '):
                        suggestions.append("Verify module is installed and accessible")
                    elif '=' in error_line and 'None' in error_line:
                        suggestions.append("Consider initializing with a default value")
                    elif error_line.endswith(':') and not error_line.strip().startswith('#'):
                        suggestions.append("Check for missing implementation in code block")
            
        except Exception as e:
            logger.debug(f"Failed to analyze file context: {e}")
        
        return suggestions
    
    def get_all_errors(self) -> List[ErrorInfo]:
        """Get all errors (static + runtime)."""
        with self._lock:
            all_errors = self.static_errors.copy()
            
            if self.runtime_collector:
                runtime_errors = self.runtime_collector.get_runtime_errors()
                all_errors.extend(runtime_errors)
            
            return all_errors
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get all errors for a specific file."""
        with self._lock:
            file_errors = [error for error in self.static_errors if error.file_path == file_path]
            
            if self.runtime_collector:
                runtime_errors = self.runtime_collector.get_runtime_errors_for_file(file_path)
                file_errors.extend(runtime_errors)
            
            return file_errors
    
    def get_runtime_errors(self) -> List[ErrorInfo]:
        """Get only runtime errors."""
        if self.runtime_collector:
            return self.runtime_collector.get_runtime_errors()
        return []
    
    def get_static_errors(self) -> List[ErrorInfo]:
        """Get only static analysis errors."""
        with self._lock:
            return self.static_errors.copy()
    
    def add_static_error(self, error_info: ErrorInfo) -> None:
        """Add a static analysis error."""
        with self._lock:
            self.static_errors.append(error_info)
            self._stats['total_errors_collected'] += 1
            self._stats['static_errors_collected'] += 1
    
    def clear_static_errors(self) -> None:
        """Clear all static errors."""
        with self._lock:
            self.static_errors.clear()
        logger.info("Static errors cleared")
    
    def clear_runtime_errors(self) -> None:
        """Clear all runtime errors."""
        if self.runtime_collector:
            self.runtime_collector.clear_runtime_errors()
        logger.info("Runtime errors cleared")
    
    def clear_all_errors(self) -> None:
        """Clear all errors."""
        self.clear_static_errors()
        self.clear_runtime_errors()
        with self._lock:
            self.diagnostics_cache.clear()
        logger.info("All errors cleared")
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        with self._lock:
            self.diagnostics_cache.clear()
        
        if self.runtime_collector:
            # Runtime errors are collected automatically
            pass
        
        logger.info("Diagnostics refreshed")
    
    def add_error_handler(self, handler: Callable[[ErrorInfo], None]) -> None:
        """Add a handler to be called when new errors are detected."""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[[ErrorInfo], None]) -> None:
        """Remove an error handler."""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary."""
        with self._lock:
            all_errors = self.get_all_errors()
            
            errors_by_type = defaultdict(int)
            errors_by_severity = defaultdict(int)
            errors_by_file = defaultdict(int)
            errors_with_suggestions = 0
            errors_with_runtime_context = 0
            
            for error in all_errors:
                errors_by_type[error.error_type.name] += 1
                errors_by_severity[error.severity.name] += 1
                errors_by_file[error.file_path] += 1
                
                if error.has_fix_suggestions:
                    errors_with_suggestions += 1
                if error.has_runtime_context:
                    errors_with_runtime_context += 1
            
            runtime_summary = {}
            if self.runtime_collector:
                runtime_summary = self.runtime_collector.get_error_summary()
            
            return {
                'total_errors': len(all_errors),
                'static_errors': len(self.static_errors),
                'runtime_errors': len(self.get_runtime_errors()),
                'errors_by_type': dict(errors_by_type),
                'errors_by_severity': dict(errors_by_severity),
                'errors_by_file': dict(errors_by_file),
                'errors_with_suggestions': errors_with_suggestions,
                'errors_with_runtime_context': errors_with_runtime_context,
                'runtime_collection_active': self.runtime_collector.is_active if self.runtime_collector else False,
                'serena_available': SERENA_AVAILABLE,
                'serena_initialized': self.serena_server is not None,
                'bridge_initialized': self.is_initialized,
                'runtime_collector_summary': runtime_summary,
                'performance_stats': self._stats.copy()
            }
    
    def get_diagnostics_for_lsp(self, file_path: Optional[str] = None) -> List[Diagnostic]:
        """Get diagnostics in LSP format."""
        if file_path:
            errors = self.get_file_errors(file_path)
        else:
            errors = self.get_all_errors()
        
        return [error.to_diagnostic() for error in errors]
    
    def configure_runtime_collection(self, **kwargs) -> None:
        """Configure runtime error collection parameters."""
        if self.runtime_collector:
            self.runtime_collector.configure_collection(**kwargs)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self._stats.copy()
        
        if self.runtime_collector:
            runtime_stats = self.runtime_collector.get_collection_stats()
            stats['runtime_collection_stats'] = runtime_stats
        
        return stats
    
    def shutdown(self) -> None:
        """Shutdown the LSP bridge and all components."""
        if self._shutdown_requested:
            return
        
        self._shutdown_requested = True
        
        try:
            # Stop runtime collection
            if self.runtime_collector:
                self.runtime_collector.shutdown()
                self.runtime_collector = None
            
            # Shutdown Serena components
            if self.serena_server:
                # Add Serena-specific shutdown logic here
                self.serena_server = None
            
            # Clear all data
            with self._lock:
                self.static_errors.clear()
                self.diagnostics_cache.clear()
                self.error_handlers.clear()
            
            self.is_initialized = False
            logger.info("SerenaLSPBridge shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during SerenaLSPBridge shutdown: {e}")
    
    def __del__(self):
        """Ensure proper cleanup on deletion."""
        try:
            self.shutdown()
        except Exception:
            pass  # Ignore errors during cleanup


# Convenience functions for easy integration
def create_serena_bridge(repo_path: str, enable_runtime_collection: bool = True) -> SerenaLSPBridge:
    """Create a Serena LSP bridge with default configuration."""
    return SerenaLSPBridge(repo_path, enable_runtime_collection)


def create_error_info(file_path: str, line: int, character: int, message: str, 
                     severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
                     error_type: ErrorType = ErrorType.STATIC_ANALYSIS,
                     **kwargs) -> ErrorInfo:
    """Create an ErrorInfo object with default values."""
    return ErrorInfo(
        file_path=file_path,
        line=line,
        character=character,
        message=message,
        severity=severity,
        error_type=error_type,
        **kwargs
    )
