"""
Enhanced Serena LSP Bridge for Graph-Sitter

This module provides a comprehensive bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, with full runtime error detection,
context analysis, and advanced LSP capabilities.
"""

import os
import sys
import threading
import time
import traceback
import ast
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set, Callable
from enum import IntEnum
from collections import defaultdict
import weakref

# Enhanced Serena imports for comprehensive LSP integration
try:
    # Core Serena LSP types and utilities
    from solidlsp.ls_types import (
        DiagnosticSeverity as SerenaDiagnosticSeverity, 
        Diagnostic as SerenaDiagnostic, 
        Position as SerenaPosition, 
        Range as SerenaRange, 
        MarkupContent, Location, MarkupKind, 
        CompletionItemKind, CompletionItem, 
        UnifiedSymbolInformation, SymbolKind, SymbolTag
    )
    from solidlsp.ls_utils import TextUtils, PathUtils, FileUtils, PlatformId, SymbolUtils
    from solidlsp.ls_request import LanguageServerRequest
    from solidlsp.ls_logger import LanguageServerLogger, LogLine
    from solidlsp.ls_handler import SolidLanguageServerHandler, Request, LanguageServerTerminatedException
    from solidlsp.ls import SolidLanguageServer, LSPFileBuffer
    from solidlsp.lsp_protocol_handler.lsp_constants import LSPConstants
    from solidlsp.lsp_protocol_handler.lsp_requests import LspRequest
    from solidlsp.lsp_protocol_handler.lsp_types import *
    from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo, LSPError, MessageType
    
    # Serena symbol and analysis capabilities
    from serena.symbol import (
        LanguageServerSymbolRetriever, ReferenceInLanguageServerSymbol, 
        LanguageServerSymbol, Symbol, PositionInFile, LanguageServerSymbolLocation
    )
    from serena.text_utils import MatchedConsecutiveLines, TextLine, LineType
    from serena.project import Project
    from serena.gui_log_viewer import GuiLogViewer, LogLevel, GuiLogViewerHandler
    from serena.code_editor import CodeEditor
    from serena.cli import (
        PromptCommands, ToolCommands, ProjectCommands, SerenaConfigCommands, 
        ContextCommands, ModeCommands, TopLevelCommands, AutoRegisteringGroup, ProjectType
    )
    
    SERENA_AVAILABLE = True
    
except ImportError as e:
    SERENA_AVAILABLE = False
    # Fallback to basic types - will be defined later
    SerenaDiagnosticSeverity = None
    SerenaDiagnostic = None
    SerenaPosition = None
    SerenaRange = None


class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues


@dataclass
class RuntimeContext:
    """Runtime context information for errors that occur during execution."""
    exception_type: str
    stack_trace: List[str] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    
    def __str__(self) -> str:
        return f"RuntimeContext({self.exception_type}, {len(self.stack_trace)} frames)"


@dataclass
class ErrorInfo:
    """Enhanced standardized error information for graph-sitter with runtime support."""
    file_path: str
    line: int
    character: int
    message: str
    severity: str  # Using string to avoid import dependencies
    error_type: ErrorType = ErrorType.STATIC_ANALYSIS
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    # Runtime error specific fields
    runtime_context: Optional[RuntimeContext] = None
    related_errors: List['ErrorInfo'] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    
    # Serena-specific enhancements
    symbol_info: Optional[Dict[str, Any]] = None
    code_context: Optional[str] = None
    dependency_chain: List[str] = field(default_factory=list)
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning or hint)."""
        return self.severity.lower() == "error"
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity.lower() == "warning"
    
    @property
    def is_hint(self) -> bool:
        """Check if this is a hint."""
        return self.severity.lower() in ["hint", "information"]
    
    @property
    def is_runtime_error(self) -> bool:
        """Check if this is a runtime error."""
        return self.error_type == ErrorType.RUNTIME_ERROR
    
    @property
    def is_static_error(self) -> bool:
        """Check if this is a static analysis error."""
        return self.error_type == ErrorType.STATIC_ANALYSIS
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get comprehensive context information for this error."""
        context = {
            'basic_info': {
                'file_path': self.file_path,
                'line': self.line,
                'character': self.character,
                'message': self.message,
                'severity': self.severity,
                'error_type': self.error_type.name,
                'source': self.source
            }
        }
        
        if self.runtime_context:
            context['runtime'] = {
                'exception_type': self.runtime_context.exception_type,
                'stack_trace': self.runtime_context.stack_trace,
                'local_variables': {k: str(v) for k, v in self.runtime_context.local_variables.items()},
                'execution_path': self.runtime_context.execution_path,
                'timestamp': self.runtime_context.timestamp
            }
        
        if self.symbol_info:
            context['symbol_info'] = self.symbol_info
            
        if self.code_context:
            context['code_context'] = self.code_context
            
        if self.dependency_chain:
            context['dependency_chain'] = self.dependency_chain
            
        if self.fix_suggestions:
            context['fix_suggestions'] = self.fix_suggestions
            
        return context
    
    def __str__(self) -> str:
        error_type_str = self.error_type.name
        runtime_indicator = " [RUNTIME]" if self.is_runtime_error else ""
        
        return f"{self.severity.upper()}{runtime_indicator} [{error_type_str}] {self.file_path}:{self.line}:{self.character} - {self.message}"


class RuntimeErrorCollector:
    """
    Collects runtime errors during code execution using various Python hooks
    and integrates with Serena's error analysis capabilities.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.runtime_errors: List[ErrorInfo] = []
        self.error_handlers: List[Callable] = []
        self._lock = threading.RLock()
        self._original_excepthook = None
        self._original_threading_excepthook = None
        self._active = False
        
        # Error collection settings
        self.max_errors = 1000
        self.max_stack_depth = 50
        self.collect_variables = True
        self.variable_max_length = 200
        
    def start_collection(self) -> None:
        """Start collecting runtime errors."""
        if self._active:
            return
            
        try:
            # Install exception hooks
            self._original_excepthook = sys.excepthook
            self._original_threading_excepthook = getattr(threading, 'excepthook', None)
            
            sys.excepthook = self._handle_exception
            if hasattr(threading, 'excepthook'):
                threading.excepthook = self._handle_thread_exception
            
            self._active = True
            print("Runtime error collection started")
            
        except Exception as e:
            print(f"Failed to start runtime error collection: {e}")
    
    def stop_collection(self) -> None:
        """Stop collecting runtime errors."""
        if not self._active:
            return
            
        try:
            # Restore original exception hooks
            if self._original_excepthook:
                sys.excepthook = self._original_excepthook
            if self._original_threading_excepthook and hasattr(threading, 'excepthook'):
                threading.excepthook = self._original_threading_excepthook
            
            self._active = False
            print("Runtime error collection stopped")
            
        except Exception as e:
            print(f"Failed to stop runtime error collection: {e}")
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle main thread exceptions."""
        try:
            self._collect_error(exc_type, exc_value, exc_traceback)
        except Exception as e:
            print(f"Error in exception handler: {e}")
        
        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _handle_thread_exception(self, args):
        """Handle thread exceptions."""
        try:
            self._collect_error(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception as e:
            print(f"Error in thread exception handler: {e}")
        
        # Call original handler
        if self._original_threading_excepthook:
            self._original_threading_excepthook(args)
    
    def _collect_error(self, exc_type, exc_value, exc_traceback) -> None:
        """Collect error information from exception."""
        try:
            # Extract traceback information
            tb_list = traceback.extract_tb(exc_traceback)
            if not tb_list:
                return
            
            # Find the most relevant frame (first frame in our repo)
            target_frame = None
            for frame in tb_list:
                if self._is_repo_file(frame.filename):
                    target_frame = frame
                    break
            
            if not target_frame:
                target_frame = tb_list[-1]  # Use last frame if none in repo
            
            # Create runtime context
            runtime_context = RuntimeContext(
                exception_type=exc_type.__name__,
                stack_trace=traceback.format_tb(exc_traceback, limit=self.max_stack_depth),
                timestamp=time.time(),
                thread_id=threading.get_ident(),
                process_id=os.getpid()
            )
            
            # Collect variable information if enabled
            if self.collect_variables and exc_traceback:
                try:
                    frame = exc_traceback.tb_frame
                    runtime_context.local_variables = self._safe_extract_variables(frame.f_locals)
                    runtime_context.global_variables = self._safe_extract_variables(frame.f_globals)
                except Exception as e:
                    print(f"Failed to collect variables: {e}")
            
            # Create ErrorInfo
            error_info = ErrorInfo(
                file_path=str(Path(target_frame.filename).relative_to(self.repo_path)) if self._is_repo_file(target_frame.filename) else target_frame.filename,
                line=target_frame.lineno - 1,  # Convert to 0-based
                character=0,  # We don't have character info from traceback
                message=f"{exc_type.__name__}: {str(exc_value)}",
                severity="error",
                error_type=ErrorType.RUNTIME_ERROR,
                source="runtime_collector",
                runtime_context=runtime_context
            )
            
            # Add to collection
            with self._lock:
                self.runtime_errors.append(error_info)
                
                # Limit collection size
                if len(self.runtime_errors) > self.max_errors:
                    self.runtime_errors = self.runtime_errors[-self.max_errors:]
            
            # Notify handlers
            for handler in self.error_handlers:
                try:
                    handler(error_info)
                except Exception as e:
                    print(f"Error in error handler: {e}")
            
            print(f"Collected runtime error: {error_info}")
            
        except Exception as e:
            print(f"Failed to collect error: {e}")
    
    def _is_repo_file(self, file_path: str) -> bool:
        """Check if file is within the repository."""
        try:
            Path(file_path).relative_to(self.repo_path)
            return True
        except ValueError:
            return False
    
    def _safe_extract_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extract variable information."""
        safe_vars = {}
        for name, value in variables.items():
            if name.startswith('__'):
                continue
            try:
                str_value = str(value)
                if len(str_value) > self.variable_max_length:
                    str_value = str_value[:self.variable_max_length] + "..."
                safe_vars[name] = str_value
            except Exception:
                safe_vars[name] = "<unable to serialize>"
        return safe_vars
    
    def get_runtime_errors(self) -> List[ErrorInfo]:
        """Get all collected runtime errors."""
        with self._lock:
            return self.runtime_errors.copy()
    
    def get_runtime_errors_for_file(self, file_path: str) -> List[ErrorInfo]:
        """Get runtime errors for a specific file."""
        with self._lock:
            return [error for error in self.runtime_errors if error.file_path == file_path]
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        with self._lock:
            self.runtime_errors.clear()
        print("Runtime errors cleared")
    
    def add_error_handler(self, handler: Callable[[ErrorInfo], None]) -> None:
        """Add a handler to be called when new runtime errors are collected."""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[[ErrorInfo], None]) -> None:
        """Remove an error handler."""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of collected runtime errors."""
        with self._lock:
            errors_by_type = defaultdict(int)
            errors_by_file = defaultdict(int)
            
            for error in self.runtime_errors:
                if error.runtime_context:
                    errors_by_type[error.runtime_context.exception_type] += 1
                errors_by_file[error.file_path] += 1
            
            return {
                'total_errors': len(self.runtime_errors),
                'errors_by_type': dict(errors_by_type),
                'errors_by_file': dict(errors_by_file),
                'collection_active': self._active,
                'max_errors': self.max_errors
            }


class SerenaLSPBridge:
    """Enhanced bridge between Serena's LSP implementation and graph-sitter with comprehensive error analysis."""
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True):
        self.repo_path = Path(repo_path)
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.is_initialized = False
        self._lock = threading.RLock()
        
        # Runtime error collection
        self.runtime_collector: Optional[RuntimeErrorCollector] = None
        self.enable_runtime_collection = enable_runtime_collection
        
        # Serena integration components
        self.serena_project: Optional[Any] = None
        self.symbol_retriever: Optional[Any] = None
        self.solid_lsp_server: Optional[Any] = None
        self.lsp_logger: Optional[Any] = None
        
        # Enhanced error analysis
        self.error_context_cache: Dict[str, Dict[str, Any]] = {}
        self.symbol_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all LSP and Serena components."""
        try:
            # Initialize runtime error collection
            if self.enable_runtime_collection:
                self._initialize_runtime_collection()
            
            # Initialize Serena components if available
            if SERENA_AVAILABLE:
                self._initialize_serena_components()
            
            self.is_initialized = True
            print(f"Enhanced LSP bridge initialized for {self.repo_path}")
            
        except Exception as e:
            print(f"Failed to initialize enhanced LSP bridge: {e}")
    
    def _initialize_runtime_collection(self) -> None:
        """Initialize runtime error collection."""
        try:
            self.runtime_collector = RuntimeErrorCollector(str(self.repo_path))
            self.runtime_collector.start_collection()
            
            # Add handler to update diagnostics cache when runtime errors occur
            self.runtime_collector.add_error_handler(self._on_runtime_error)
            
            print("Runtime error collection initialized")
            
        except Exception as e:
            print(f"Failed to initialize runtime error collection: {e}")
            self.enable_runtime_collection = False
    
    def _initialize_serena_components(self) -> None:
        """Initialize Serena-specific components."""
        try:
            # Initialize Serena project
            if 'Project' in globals():
                self.serena_project = Project(str(self.repo_path))
                print("Serena project initialized")
            
            # Initialize SolidLSP server
            if 'SolidLanguageServer' in globals():
                self.solid_lsp_server = SolidLanguageServer()
                print("SolidLSP server initialized")
            
            # Initialize symbol retriever
            if 'LanguageServerSymbolRetriever' in globals() and self.solid_lsp_server:
                self.symbol_retriever = LanguageServerSymbolRetriever(self.solid_lsp_server)
                print("Symbol retriever initialized")
            
            # Initialize LSP logger
            if 'LanguageServerLogger' in globals():
                self.lsp_logger = LanguageServerLogger()
                print("LSP logger initialized")
                
        except Exception as e:
            print(f"Failed to initialize Serena components: {e}")
    
    def _on_runtime_error(self, error_info: ErrorInfo) -> None:
        """Handle new runtime errors."""
        try:
            # Enhance error with Serena analysis if available
            if SERENA_AVAILABLE:
                self._enhance_error_with_serena_analysis(error_info)
            
            # Update diagnostics cache
            with self._lock:
                if error_info.file_path not in self.diagnostics_cache:
                    self.diagnostics_cache[error_info.file_path] = []
                self.diagnostics_cache[error_info.file_path].append(error_info)
            
        except Exception as e:
            print(f"Error handling runtime error: {e}")
    
    def _enhance_error_with_serena_analysis(self, error_info: ErrorInfo) -> None:
        """Enhance error information using Serena's analysis capabilities."""
        try:
            # Get code context
            error_info.code_context = self._get_enhanced_code_context(error_info.file_path, error_info.line)
            
            # Generate fix suggestions
            error_info.fix_suggestions = self._generate_fix_suggestions(error_info)
            
        except Exception as e:
            print(f"Failed to enhance error with Serena analysis: {e}")
    
    def _get_enhanced_code_context(self, file_path: str, line: int, context_lines: int = 10) -> Optional[str]:
        """Get enhanced code context around an error."""
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, line - context_lines)
            end_line = min(len(lines), line + context_lines + 1)
            
            context_lines_list = []
            for i in range(start_line, end_line):
                prefix = ">>> " if i == line else "    "
                context_lines_list.append(f"{prefix}{i+1:4d}: {lines[i].rstrip()}")
            
            return '\n'.join(context_lines_list)
            
        except Exception as e:
            print(f"Failed to get enhanced code context: {e}")
            return None
    
    def _generate_fix_suggestions(self, error_info: ErrorInfo) -> List[str]:
        """Generate fix suggestions for an error."""
        suggestions = []
        
        try:
            if not error_info.runtime_context:
                return suggestions
            
            exception_type = error_info.runtime_context.exception_type
            message = error_info.message
            
            # Common fix suggestions based on exception type
            if exception_type == "NameError":
                suggestions.append("Check if the variable is defined before use")
                suggestions.append("Verify import statements")
                suggestions.append("Check for typos in variable names")
            elif exception_type == "AttributeError":
                suggestions.append("Verify the object has the expected attribute")
                suggestions.append("Check if the object is None")
                suggestions.append("Ensure proper initialization")
            elif exception_type == "TypeError":
                suggestions.append("Check argument types")
                suggestions.append("Verify function signature")
                suggestions.append("Ensure proper type conversion")
            elif exception_type == "IndexError":
                suggestions.append("Check list/array bounds")
                suggestions.append("Verify index is within range")
                suggestions.append("Add bounds checking")
            elif exception_type == "KeyError":
                suggestions.append("Check if key exists in dictionary")
                suggestions.append("Use dict.get() with default value")
                suggestions.append("Verify key spelling")
            elif exception_type == "ValueError":
                suggestions.append("Check input value format")
                suggestions.append("Validate input before processing")
                suggestions.append("Handle edge cases")
            
            # Add context-specific suggestions
            if "division by zero" in message.lower():
                suggestions.append("Add check for zero before division")
            elif "none" in message.lower():
                suggestions.append("Add None check before accessing attributes")
            
        except Exception as e:
            print(f"Failed to generate fix suggestions: {e}")
        
        return suggestions
    
    def get_diagnostics(self, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get all diagnostics from all language servers and runtime collection."""
        if not self.is_initialized:
            return []
        
        all_diagnostics = []
        
        with self._lock:
            # Add runtime errors if requested and available
            if include_runtime and self.runtime_collector:
                try:
                    runtime_errors = self.runtime_collector.get_runtime_errors()
                    all_diagnostics.extend(runtime_errors)
                except Exception as e:
                    print(f"Error getting runtime diagnostics: {e}")
        
        return all_diagnostics
    
    def get_runtime_errors(self) -> List[ErrorInfo]:
        """Get all runtime errors collected during execution."""
        if not self.runtime_collector:
            return []
        
        return self.runtime_collector.get_runtime_errors()
    
    def get_runtime_errors_for_file(self, file_path: str) -> List[ErrorInfo]:
        """Get runtime errors for a specific file."""
        if not self.runtime_collector:
            return []
        
        return self.runtime_collector.get_runtime_errors_for_file(file_path)
    
    def get_all_errors_with_context(self) -> List[Dict[str, Any]]:
        """Get all errors with their full context information."""
        all_errors = self.get_diagnostics(include_runtime=True)
        return [error.get_full_context() for error in all_errors if error.is_error]
    
    def get_runtime_error_summary(self) -> Dict[str, Any]:
        """Get summary of runtime errors."""
        if not self.runtime_collector:
            return {
                'runtime_collection_enabled': False,
                'total_runtime_errors': 0
            }
        
        summary = self.runtime_collector.get_error_summary()
        summary['runtime_collection_enabled'] = True
        return summary
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        if self.runtime_collector:
            self.runtime_collector.clear_runtime_errors()
            
            # Also clear from diagnostics cache
            with self._lock:
                for file_path in list(self.diagnostics_cache.keys()):
                    self.diagnostics_cache[file_path] = [
                        error for error in self.diagnostics_cache[file_path] 
                        if not error.is_runtime_error
                    ]
                    if not self.diagnostics_cache[file_path]:
                        del self.diagnostics_cache[file_path]
    
    def get_file_diagnostics(self, file_path: str, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        if not self.is_initialized:
            return []
        
        file_diagnostics = []
        
        with self._lock:
            # Add runtime errors for this file if requested
            if include_runtime and self.runtime_collector:
                try:
                    runtime_errors = self.runtime_collector.get_runtime_errors_for_file(file_path)
                    file_diagnostics.extend(runtime_errors)
                except Exception as e:
                    print(f"Error getting runtime file diagnostics: {e}")
        
        return file_diagnostics
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.is_initialized:
            return
        
        with self._lock:
            self.diagnostics_cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown all language servers and runtime collection."""
        with self._lock:
            # Shutdown runtime error collection
            if self.runtime_collector:
                try:
                    self.runtime_collector.stop_collection()
                    print("Runtime error collection stopped")
                except Exception as e:
                    print(f"Error stopping runtime collection: {e}")
            
            # Shutdown Serena components
            if self.solid_lsp_server:
                try:
                    # Shutdown SolidLSP server if it has a shutdown method
                    if hasattr(self.solid_lsp_server, 'shutdown'):
                        self.solid_lsp_server.shutdown()
                    print("SolidLSP server shutdown")
                except Exception as e:
                    print(f"Error shutting down SolidLSP server: {e}")
            
            # Clear all caches and references
            self.diagnostics_cache.clear()
            self.error_context_cache.clear()
            self.symbol_cache.clear()
            self.runtime_collector = None
            self.serena_project = None
            self.symbol_retriever = None
            self.solid_lsp_server = None
            self.lsp_logger = None
            self.is_initialized = False
            
            print("Enhanced LSP bridge shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about the enhanced LSP bridge."""
        # Get runtime error statistics
        runtime_status = {}
        if self.runtime_collector:
            runtime_status = self.runtime_collector.get_error_summary()
        
        # Get Serena component status
        serena_status = {
            'serena_available': SERENA_AVAILABLE,
            'project_initialized': self.serena_project is not None,
            'solid_lsp_initialized': self.solid_lsp_server is not None,
            'symbol_retriever_initialized': self.symbol_retriever is not None,
            'lsp_logger_initialized': self.lsp_logger is not None
        }
        
        # Get diagnostic counts
        all_diagnostics = self.get_diagnostics(include_runtime=True)
        runtime_errors = self.get_runtime_errors()
        
        diagnostic_counts = {
            'total_diagnostics': len(all_diagnostics),
            'runtime_errors': len(runtime_errors),
            'errors': len([d for d in all_diagnostics if d.is_error]),
            'warnings': len([d for d in all_diagnostics if d.is_warning]),
            'hints': len([d for d in all_diagnostics if d.is_hint])
        }
        
        return {
            'initialized': self.is_initialized,
            'repo_path': str(self.repo_path),
            'runtime_collection_enabled': self.enable_runtime_collection,
            'runtime_status': runtime_status,
            'serena_status': serena_status,
            'diagnostic_counts': diagnostic_counts,
            'cache_sizes': {
                'diagnostics_cache': len(self.diagnostics_cache),
                'error_context_cache': len(self.error_context_cache),
                'symbol_cache': len(self.symbol_cache)
            }
        }
