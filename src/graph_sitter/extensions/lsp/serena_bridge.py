"""
Comprehensive Serena LSP Bridge for Graph-Sitter

This module provides a complete bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, with full runtime error detection,
context analysis, advanced LSP capabilities, symbol intelligence, error retrieval,
real-time diagnostics processing, and comprehensive error analysis.

Features:
- Runtime error collection with variable extraction
- Symbol intelligence and dependency tracking
- Comprehensive error retrieval and categorization
- Real-time diagnostics processing with filtering
- Advanced context analysis for errors
- LSP protocol implementation for Serena communication
- Thread-safe operations with graceful fallback
"""

import os
import sys
import threading
import time
import traceback
import ast
import inspect
import asyncio
import json
import uuid
import re
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set, Callable, Tuple, Deque
from enum import IntEnum, Enum
from collections import defaultdict, deque
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

logger = logging.getLogger(__name__)


# ============================================================================
# CORE ENUMS AND DATA STRUCTURES
# ============================================================================

class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues


class ErrorSeverity(Enum):
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    COMPATIBILITY = "compatibility"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


class MessageType(Enum):
    """LSP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class LSPErrorCode(Enum):
    """LSP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    REQUEST_CANCELLED = -32800
    CONTENT_MODIFIED = -32801


class DiagnosticEvent(Enum):
    """Diagnostic event types."""
    ERROR_ADDED = "error_added"
    ERROR_REMOVED = "error_removed"
    ERROR_UPDATED = "error_updated"
    BATCH_PROCESSED = "batch_processed"
    ANALYSIS_COMPLETE = "analysis_complete"


# ============================================================================
# CORE DATA CLASSES
# ============================================================================

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
class ErrorLocation:
    """Represents the location of an error in code."""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    @property
    def range_text(self) -> str:
        """Get human-readable range text."""
        if self.end_line and self.end_column:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"
    
    @property
    def file_name(self) -> str:
        """Get just the filename."""
        return Path(self.file_path).name


@dataclass
class SymbolInfo:
    """Information about a code symbol."""
    name: str
    symbol_type: str
    file_path: str
    line_number: int
    character: int
    signature: Optional[str] = None
    scope: Optional[str] = None
    references: List[Dict[str, Any]] = field(default_factory=list)
    usages: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AnalysisContext:
    """Context for analysis operations."""
    file_path: Optional[str] = None
    include_dependencies: bool = False
    include_usages: bool = False
    max_depth: int = 5


@dataclass
class DiagnosticFilter:
    """Filter configuration for diagnostics."""
    severities: Optional[Set[ErrorSeverity]] = None
    categories: Optional[Set[ErrorCategory]] = None
    file_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    min_line: Optional[int] = None
    max_line: Optional[int] = None
    sources: Optional[Set[str]] = None
    
    def matches(self, error: 'CodeError') -> bool:
        """Check if error matches filter criteria."""
        # Check severity
        if self.severities and error.severity not in self.severities:
            return False
        
        # Check category
        if self.categories and error.category not in self.categories:
            return False
        
        # Check file patterns
        if self.file_patterns:
            import fnmatch
            file_path = error.location.file_path
            if not any(fnmatch.fnmatch(file_path, pattern) for pattern in self.file_patterns):
                return False
        
        # Check exclude patterns
        if self.exclude_patterns:
            import fnmatch
            file_path = error.location.file_path
            if any(fnmatch.fnmatch(file_path, pattern) for pattern in self.exclude_patterns):
                return False
        
        # Check line range
        if self.min_line is not None and error.location.line < self.min_line:
            return False
        if self.max_line is not None and error.location.line > self.max_line:
            return False
        
        # Check sources
        if self.sources and error.source not in self.sources:
            return False
        
        return True


@dataclass
class DiagnosticStats:
    """Diagnostic statistics."""
    total_errors: int = 0
    critical_errors: int = 0
    warnings: int = 0
    info_hints: int = 0
    files_with_errors: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    sources: Dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0  # errors per minute
    last_updated: float = field(default_factory=time.time)
    
    def update_from_errors(self, errors: List['CodeError']):
        """Update statistics from error list."""
        self.total_errors = len(errors)
        self.critical_errors = sum(1 for e in errors if e.severity == ErrorSeverity.ERROR)
        self.warnings = sum(1 for e in errors if e.severity == ErrorSeverity.WARNING)
        self.info_hints = sum(1 for e in errors if e.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT])
        
        # Count files with errors
        files = set(e.location.file_path for e in errors)
        self.files_with_errors = len(files)
        
        # Count by category
        self.categories = {}
        for error in errors:
            category = error.category.value
            self.categories[category] = self.categories.get(category, 0) + 1
        
        # Count by source
        self.sources = {}
        for error in errors:
            source = error.source
            self.sources[source] = self.sources.get(source, 0) + 1
        
        self.last_updated = time.time()


@dataclass
class LSPError:
    """LSP error representation."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        error_dict: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            error_dict["data"] = self.data
        return error_dict


@dataclass
class LSPMessage:
    """Base LSP message."""
    jsonrpc: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class LSPRequest(LSPMessage):
    """LSP request message."""
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, method: str, params: Optional[Dict[str, Any]] = None) -> 'LSPRequest':
        return cls(
            jsonrpc="2.0",
            id=str(uuid.uuid4()),
            method=method,
            params=params
        )


@dataclass
class LSPResponse(LSPMessage):
    """LSP response message."""
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[LSPError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        response_dict: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            response_dict["error"] = self.error.to_dict()
        else:
            response_dict["result"] = self.result
        return response_dict


@dataclass
class LSPNotification(LSPMessage):
    """LSP notification message."""
    method: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class ContextualError:
    """Enhanced error with comprehensive context."""
    error_id: str
    error_type: str
    severity: str
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    message: str = ""
    description: str = ""
    
    # Context layers
    immediate_context: Dict[str, Any] = field(default_factory=dict)
    function_context: Dict[str, Any] = field(default_factory=dict)
    class_context: Dict[str, Any] = field(default_factory=dict)
    file_context: Dict[str, Any] = field(default_factory=dict)
    module_context: Dict[str, Any] = field(default_factory=dict)
    project_context: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships
    related_symbols: List[str] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Suggestions
    fix_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    code_examples: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error_info: 'ErrorInfo'
    calling_functions: List[Dict[str, Any]] = field(default_factory=list)
    called_functions: List[Dict[str, Any]] = field(default_factory=list)
    parameter_issues: List[Dict[str, Any]] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    related_symbols: List[Dict[str, Any]] = field(default_factory=list)
    code_context: Optional[str] = None
    fix_suggestions: List[str] = field(default_factory=list)


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


@dataclass
class CodeError:
    """Represents a comprehensive code error with context."""
    id: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    location: ErrorLocation
    code: Optional[str] = None
    source: str = "serena"
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_critical(self) -> bool:
        """Check if error is critical (error severity)."""
        return self.severity == ErrorSeverity.ERROR
    
    @property
    def display_text(self) -> str:
        """Get formatted display text for the error."""
        return f"[{self.severity.value.upper()}] {self.location.file_name}:{self.location.range_text} - {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            'id': self.id,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'location': {
                'file_path': self.location.file_path,
                'line': self.location.line,
                'column': self.location.column,
                'end_line': self.location.end_line,
                'end_column': self.location.end_column
            },
            'code': self.code,
            'source': self.source,
            'suggestions': self.suggestions,
            'context': self.context,
            'related_errors': self.related_errors,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_lsp_diagnostic(cls, diagnostic: Dict[str, Any], file_path: str) -> 'CodeError':
        """Create CodeError from LSP diagnostic data."""
        range_data = diagnostic.get('range', {})
        start = range_data.get('start', {})
        end = range_data.get('end', {})
        
        location = ErrorLocation(
            file_path=file_path,
            line=start.get('line', 0) + 1,  # LSP is 0-based, we use 1-based
            column=start.get('character', 0) + 1,
            end_line=end.get('line', 0) + 1 if end else None,
            end_column=end.get('character', 0) + 1 if end else None
        )
        
        # Map LSP severity to our severity
        lsp_severity = diagnostic.get('severity', 1)
        severity_map = {
            1: ErrorSeverity.ERROR,
            2: ErrorSeverity.WARNING,
            3: ErrorSeverity.INFO,
            4: ErrorSeverity.HINT
        }
        severity = severity_map.get(lsp_severity, ErrorSeverity.ERROR)
        
        # Determine category from diagnostic data
        category = cls._determine_category(diagnostic)
        
        return cls(
            id=diagnostic.get('id', f"{file_path}_{start.get('line', 0)}_{start.get('character', 0)}"),
            message=diagnostic.get('message', 'Unknown error'),
            severity=severity,
            category=category,
            location=location,
            code=diagnostic.get('code'),
            source=diagnostic.get('source', 'serena'),
            context=diagnostic.get('data', {})
        )
    
    @staticmethod
    def _determine_category(diagnostic: Dict[str, Any]) -> ErrorCategory:
        """Determine error category from diagnostic data."""
        source = diagnostic.get('source', '').lower()
        code = str(diagnostic.get('code', '')).lower()
        message = diagnostic.get('message', '').lower()
        
        # Category determination logic
        if 'syntax' in source or 'parse' in message:
            return ErrorCategory.SYNTAX
        elif 'type' in source or 'type' in message:
            return ErrorCategory.TYPE
        elif 'security' in source or 'security' in message:
            return ErrorCategory.SECURITY
        elif 'performance' in source or 'performance' in message:
            return ErrorCategory.PERFORMANCE
        elif 'style' in source or 'lint' in source:
            return ErrorCategory.STYLE
        elif 'import' in message or 'dependency' in message:
            return ErrorCategory.DEPENDENCY
        elif 'compatibility' in message:
            return ErrorCategory.COMPATIBILITY
        else:
            return ErrorCategory.LOGIC


@dataclass
class ComprehensiveErrorList:
    """Comprehensive list of code errors with metadata and analysis."""
    errors: List[CodeError] = field(default_factory=list)
    total_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    files_analyzed: Set[str] = field(default_factory=set)
    analysis_timestamp: float = field(default_factory=time.time)
    analysis_duration: float = 0.0
    
    def __post_init__(self):
        """Calculate counts after initialization."""
        self._update_counts()
    
    def _update_counts(self):
        """Update error counts."""
        self.total_count = len(self.errors)
        self.critical_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.ERROR)
        self.warning_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)
        self.info_count = sum(1 for e in self.errors if e.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT])
        self.files_analyzed = {e.location.file_path for e in self.errors}
    
    def add_error(self, error: CodeError):
        """Add an error to the list."""
        self.errors.append(error)
        self._update_counts()
    
    def add_errors(self, errors: List[CodeError]):
        """Add multiple errors to the list."""
        self.errors.extend(errors)
        self._update_counts()
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[CodeError]:
        """Get errors filtered by severity."""
        return [e for e in self.errors if e.severity == severity]
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[CodeError]:
        """Get errors filtered by category."""
        return [e for e in self.errors if e.category == category]
    
    def get_errors_by_file(self, file_path: str) -> List[CodeError]:
        """Get errors for a specific file."""
        return [e for e in self.errors if e.location.file_path == file_path]
    
    def get_critical_errors(self) -> List[CodeError]:
        """Get only critical errors."""
        return self.get_errors_by_severity(ErrorSeverity.ERROR)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = len(self.get_errors_by_category(category))
        
        return {
            'total_errors': self.total_count,
            'critical_errors': self.critical_count,
            'warnings': self.warning_count,
            'info_hints': self.info_count,
            'files_with_errors': len(self.files_analyzed),
            'category_breakdown': category_counts,
            'analysis_timestamp': self.analysis_timestamp,
            'analysis_duration': self.analysis_duration
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'errors': [error.to_dict() for error in self.errors],
            'summary': self.get_summary()
        }


# ============================================================================
# LSP PROTOCOL IMPLEMENTATION
# ============================================================================

class ProtocolHandler:
    """
    Handles LSP protocol message parsing, validation, and routing.
    
    Features:
    - Message parsing and validation
    - Request/response correlation
    - Notification handling
    - Error handling and reporting
    - Protocol compliance checking
    """
    
    def __init__(self):
        self._pending_requests: Dict[Union[str, int], asyncio.Future] = {}
        self._notification_handlers: Dict[str, List[Callable]] = {}
        self._request_handlers: Dict[str, Callable] = {}
        self._message_id_counter = 0
    
    def generate_message_id(self) -> str:
        """Generate a unique message ID."""
        self._message_id_counter += 1
        return f"serena_{self._message_id_counter}"
    
    def parse_message(self, raw_message: str) -> Union[LSPRequest, LSPResponse, LSPNotification]:
        """Parse a raw LSP message string into appropriate message object."""
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LSP message: {e}")
        
        # Validate jsonrpc version
        if data.get("jsonrpc") != "2.0":
            raise ValueError("Invalid or missing jsonrpc version")
        
        # Determine message type and parse accordingly
        if "id" in data:
            if "method" in data:
                # Request
                return LSPRequest(
                    jsonrpc="2.0",
                    id=data["id"],
                    method=data["method"],
                    params=data.get("params")
                )
            else:
                # Response
                error_data = data.get("error")
                error = None
                if error_data:
                    error = LSPError(
                        code=error_data["code"],
                        message=error_data["message"],
                        data=error_data.get("data")
                    )
                
                return LSPResponse(
                    jsonrpc="2.0",
                    id=data["id"],
                    result=data.get("result"),
                    error=error
                )
        else:
            # Notification
            if "method" not in data:
                raise ValueError("Notification missing method")
            
            return LSPNotification(
                jsonrpc="2.0",
                method=data["method"],
                params=data.get("params")
            )
    
    def create_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> LSPRequest:
        """Create a new LSP request with unique ID."""
        return LSPRequest(
            jsonrpc="2.0",
            id=self.generate_message_id(),
            method=method,
            params=params
        )
    
    def create_response(self, request_id: Union[str, int], 
                       result: Optional[Any] = None,
                       error: Optional[LSPError] = None) -> LSPResponse:
        """Create an LSP response for a given request."""
        return LSPResponse(
            jsonrpc="2.0",
            id=request_id,
            result=result,
            error=error
        )
    
    def create_notification(self, method: str, 
                          params: Optional[Dict[str, Any]] = None) -> LSPNotification:
        """Create an LSP notification."""
        return LSPNotification(
            jsonrpc="2.0",
            method=method,
            params=params
        )
    
    def create_error_response(self, request_id: Union[str, int], 
                            code: LSPErrorCode, message: str,
                            data: Optional[Any] = None) -> LSPResponse:
        """Create an error response."""
        error = LSPError(code=code.value, message=message, data=data)
        return LSPResponse(jsonrpc="2.0", id=request_id, error=error)
    
    def register_request_handler(self, method: str, handler: Callable):
        """Register a handler for incoming requests."""
        self._request_handlers[method] = handler
    
    def register_notification_handler(self, method: str, handler: Callable):
        """Register a handler for incoming notifications."""
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)
    
    async def handle_message(self, message: Union[LSPRequest, LSPResponse, LSPNotification]) -> Optional[LSPResponse]:
        """Handle an incoming LSP message."""
        try:
            if isinstance(message, LSPRequest):
                return await self._handle_request(message)
            elif isinstance(message, LSPResponse):
                await self._handle_response(message)
            elif isinstance(message, LSPNotification):
                await self._handle_notification(message)
        except Exception as e:
            logger.error(f"Error handling LSP message: {e}")
            if isinstance(message, LSPRequest):
                return self.create_error_response(
                    message.id,
                    LSPErrorCode.INTERNAL_ERROR,
                    f"Internal error: {str(e)}"
                )
        
        return None
    
    async def _handle_request(self, request: LSPRequest) -> LSPResponse:
        """Handle incoming request."""
        handler = self._request_handlers.get(request.method)
        
        if not handler:
            return self.create_error_response(
                request.id,
                LSPErrorCode.METHOD_NOT_FOUND,
                f"Method '{request.method}' not found"
            )
        
        try:
            result = await handler(request.params or {})
            return self.create_response(request.id, result=result)
        except Exception as e:
            return self.create_error_response(
                request.id,
                LSPErrorCode.INTERNAL_ERROR,
                f"Handler error: {str(e)}"
            )
    
    async def _handle_response(self, response: LSPResponse):
        """Handle incoming response."""
        future = self._pending_requests.get(response.id)
        if future and not future.done():
            if response.error:
                future.set_exception(
                    Exception(f"LSP Error {response.error.code}: {response.error.message}")
                )
            else:
                future.set_result(response.result)
            
            del self._pending_requests[response.id]
    
    async def _handle_notification(self, notification: LSPNotification):
        """Handle incoming notification."""
        handlers = self._notification_handlers.get(notification.method, [])
        
        for handler in handlers:
            try:
                await handler(notification.params or {})
            except Exception as e:
                logger.error(f"Error in notification handler for {notification.method}: {e}")
    
    def track_request(self, request: LSPRequest) -> asyncio.Future:
        """Track a request for response correlation."""
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request.id] = future
        return future
    
    def cancel_request(self, request_id: Union[str, int]):
        """Cancel a pending request."""
        future = self._pending_requests.get(request_id)
        if future and not future.done():
            future.cancel()
            del self._pending_requests[request_id]
    
    def get_pending_requests(self) -> List[Union[str, int]]:
        """Get list of pending request IDs."""
        return list(self._pending_requests.keys())
    
    def cleanup_completed_requests(self):
        """Clean up completed or cancelled requests."""
        completed_ids = [
            req_id for req_id, future in self._pending_requests.items()
            if future.done()
        ]
        
        for req_id in completed_ids:
            del self._pending_requests[req_id]


class SerenaProtocolExtensions:
    """Serena-specific LSP protocol extensions."""
    
    # Serena-specific methods
    SERENA_ANALYZE_FILE = "serena/analyzeFile"
    SERENA_GET_ERRORS = "serena/getErrors"
    SERENA_GET_COMPREHENSIVE_ERRORS = "serena/getComprehensiveErrors"
    SERENA_ANALYZE_CODEBASE = "serena/analyzeCodebase"
    SERENA_GET_CONTEXT = "serena/getContext"
    SERENA_REFRESH_ANALYSIS = "serena/refreshAnalysis"
    
    # Serena-specific notifications
    SERENA_ANALYSIS_COMPLETE = "serena/analysisComplete"
    SERENA_ERROR_UPDATED = "serena/errorUpdated"
    SERENA_PROGRESS = "serena/progress"
    
    @staticmethod
    def create_analyze_file_request(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Create parameters for file analysis request."""
        params: Dict[str, Any] = {"uri": f"file://{file_path}"}
        if content is not None:
            params["content"] = content
        return params
    
    @staticmethod
    def create_get_errors_request(file_path: Optional[str] = None, 
                                severity_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create parameters for error retrieval request."""
        params: Dict[str, Any] = {}
        if file_path:
            params["uri"] = f"file://{file_path}"
        if severity_filter:
            params["severityFilter"] = severity_filter
        return params
    
    @staticmethod
    def create_comprehensive_errors_request(include_context: bool = True,
                                          include_suggestions: bool = True,
                                          max_errors: Optional[int] = None) -> Dict[str, Any]:
        """Create parameters for comprehensive error analysis request."""
        params: Dict[str, Any] = {
            "includeContext": include_context,
            "includeSuggestions": include_suggestions
        }
        if max_errors is not None:
            params["maxErrors"] = max_errors
        return params
    
    @staticmethod
    def create_analyze_codebase_request(root_path: str, 
                                      file_patterns: Optional[List[str]] = None,
                                      exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create parameters for codebase analysis request."""
        params: Dict[str, Any] = {"rootUri": f"file://{root_path}"}
        if file_patterns:
            params["includePatterns"] = file_patterns
        if exclude_patterns:
            params["excludePatterns"] = exclude_patterns
        return params


# ============================================================================
# RUNTIME ERROR COLLECTION
# ============================================================================

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


# ============================================================================
# CONVENIENCE FUNCTIONS FOR EASY INTEGRATION
# ============================================================================

def create_serena_bridge(repo_path: str, enable_runtime_collection: bool = True) -> SerenaLSPBridge:
    """Create and return a Serena LSP bridge for a repository."""
    return SerenaLSPBridge(repo_path, enable_runtime_collection)


def get_comprehensive_errors(repo_path: str) -> List[ErrorInfo]:
    """Get comprehensive errors for a repository."""
    bridge = create_serena_bridge(repo_path)
    return bridge.get_diagnostics(include_runtime=True)


def analyze_runtime_errors(repo_path: str) -> Dict[str, Any]:
    """Analyze runtime errors for a repository."""
    bridge = create_serena_bridge(repo_path)
    return bridge.get_runtime_error_summary()


def create_protocol_handler() -> ProtocolHandler:
    """Create and return a protocol handler for LSP communication."""
    return ProtocolHandler()


# ============================================================================
# ENHANCED ERROR ANALYSIS INTEGRATION
# ============================================================================

class EnhancedSerenaIntegration:
    """
    Enhanced integration class that combines all Serena capabilities
    for comprehensive error analysis and LSP integration.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.lsp_bridge = None
        self.protocol_handler = None
        self.is_initialized = False
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components."""
        try:
            # Initialize LSP bridge
            self.lsp_bridge = SerenaLSPBridge(str(self.repo_path))
            
            # Initialize protocol handler
            self.protocol_handler = ProtocolHandler()
            
            self.is_initialized = True
            logger.info("Enhanced Serena integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced Serena integration: {e}")
    
    def get_all_errors(self) -> List[ErrorInfo]:
        """Get all errors from all sources."""
        all_errors = []
        
        if self.lsp_bridge:
            all_errors.extend(self.lsp_bridge.get_diagnostics(include_runtime=True))
        
        return all_errors
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive error analysis."""
        analysis = {
            'lsp_bridge_status': self.lsp_bridge.get_status() if self.lsp_bridge else None,
            'total_errors': 0,
            'error_breakdown': {},
            'runtime_errors': 0,
            'static_errors': 0
        }
        
        if self.lsp_bridge:
            all_errors = self.lsp_bridge.get_diagnostics(include_runtime=True)
            analysis['total_errors'] = len(all_errors)
            analysis['runtime_errors'] = len([e for e in all_errors if e.is_runtime_error])
            analysis['static_errors'] = len([e for e in all_errors if e.is_static_error])
            
            # Error breakdown by type
            error_types = {}
            for error in all_errors:
                error_type = error.error_type.name
                error_types[error_type] = error_types.get(error_type, 0) + 1
            analysis['error_breakdown'] = error_types
        
        return analysis
    
    def shutdown(self):
        """Shutdown all components."""
        if self.lsp_bridge:
            self.lsp_bridge.shutdown()
        
        self.is_initialized = False
        logger.info("Enhanced Serena integration shutdown complete")


# ============================================================================
# MAIN INTEGRATION FUNCTION
# ============================================================================

def create_enhanced_serena_integration(repo_path: str) -> EnhancedSerenaIntegration:
    """
    Create a comprehensive Serena integration for a repository.
    
    This is the main entry point for using all Serena LSP capabilities
    including error retrieval, runtime error collection, and comprehensive
    analysis.
    
    Args:
        repo_path: Path to the repository to analyze
        
    Returns:
        EnhancedSerenaIntegration instance with all capabilities
    """
    return EnhancedSerenaIntegration(repo_path)
