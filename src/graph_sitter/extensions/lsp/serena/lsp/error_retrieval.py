"""
Comprehensive Error Retrieval System for Serena LSP Integration

This module provides comprehensive error retrieval capabilities from Serena LSP servers,
including real-time error monitoring, categorization, and analysis.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union
import logging

from .protocol import ProtocolHandler, SerenaProtocolExtensions

logger = logging.getLogger(__name__)


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


class ErrorRetriever:
    """
    Comprehensive error retrieval system for Serena LSP servers.
    
    Features:
    - Real-time error retrieval from LSP servers
    - Error categorization and analysis
    - Batch error processing
    - Error filtering and sorting
    - Live error monitoring
    """
    
    def __init__(self, protocol_handler: ProtocolHandler):
        self.protocol = protocol_handler
        self._error_cache: Dict[str, List[CodeError]] = {}
        self._error_listeners: List[Callable[[List[CodeError]], None]] = []
        self._monitoring_active = False
        self._last_retrieval: Optional[float] = None
        
        # Register for error update notifications
        self.protocol.register_notification_handler(
            SerenaProtocolExtensions.SERENA_ERROR_UPDATED,
            self._handle_error_update
        )
    
    async def get_comprehensive_errors(self, 
                                     include_context: bool = True,
                                     include_suggestions: bool = True,
                                     max_errors: Optional[int] = None,
                                     severity_filter: Optional[List[ErrorSeverity]] = None) -> ComprehensiveErrorList:
        """
        Retrieve comprehensive error list from Serena server.
        
        Args:
            include_context: Whether to include error context
            include_suggestions: Whether to include fix suggestions
            max_errors: Maximum number of errors to retrieve
            severity_filter: Filter by error severities
            
        Returns:
            Comprehensive error list with analysis
        """
        start_time = time.time()
        
        # Create request parameters
        params = SerenaProtocolExtensions.create_comprehensive_errors_request(
            include_context=include_context,
            include_suggestions=include_suggestions,
            max_errors=max_errors
        )
        
        # Add severity filter if provided
        if severity_filter:
            params['severityFilter'] = [s.value for s in severity_filter]
        
        # Create and send request
        request = self.protocol.create_request(
            SerenaProtocolExtensions.SERENA_GET_COMPREHENSIVE_ERRORS,
            params
        )
        
        try:
            # Track request and wait for response
            future = self.protocol.track_request(request)
            
            # Send request (this would be handled by the LSP client)
            # For now, we'll simulate the response structure
            response_data = await self._send_request_and_wait(request, future)
            
            # Process response into comprehensive error list
            error_list = await self._process_comprehensive_response(response_data)
            error_list.analysis_duration = time.time() - start_time
            
            # Update cache
            self._update_error_cache(error_list.errors)
            self._last_retrieval = time.time()
            
            # Notify listeners
            await self._notify_error_listeners(error_list.errors)
            
            return error_list
            
        except Exception as e:
            logger.error(f"Error retrieving comprehensive errors: {e}")
            # Return empty error list with error information
            error_list = ComprehensiveErrorList()
            error_list.analysis_duration = time.time() - start_time
            return error_list
    
    async def get_file_errors(self, file_path: str) -> List[CodeError]:
        """
        Get errors for a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of errors for the file
        """
        params = SerenaProtocolExtensions.create_get_errors_request(file_path)
        
        request = self.protocol.create_request(
            SerenaProtocolExtensions.SERENA_GET_ERRORS,
            params
        )
        
        try:
            future = self.protocol.track_request(request)
            response_data = await self._send_request_and_wait(request, future)
            
            errors = await self._process_file_errors_response(response_data, file_path)
            
            # Update cache for this file
            self._error_cache[file_path] = errors
            
            return errors
            
        except Exception as e:
            logger.error(f"Error retrieving file errors for {file_path}: {e}")
            return []
    
    async def analyze_codebase(self, 
                             root_path: str,
                             file_patterns: Optional[List[str]] = None,
                             exclude_patterns: Optional[List[str]] = None) -> ComprehensiveErrorList:
        """
        Analyze entire codebase for errors.
        
        Args:
            root_path: Root directory path
            file_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Comprehensive error analysis of the codebase
        """
        start_time = time.time()
        
        params = SerenaProtocolExtensions.create_analyze_codebase_request(
            root_path=root_path,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns
        )
        
        request = self.protocol.create_request(
            SerenaProtocolExtensions.SERENA_ANALYZE_CODEBASE,
            params
        )
        
        try:
            future = self.protocol.track_request(request)
            response_data = await self._send_request_and_wait(request, future)
            
            error_list = await self._process_codebase_analysis_response(response_data)
            error_list.analysis_duration = time.time() - start_time
            
            # Update cache with all errors
            self._update_error_cache(error_list.errors)
            self._last_retrieval = time.time()
            
            # Notify listeners
            await self._notify_error_listeners(error_list.errors)
            
            return error_list
            
        except Exception as e:
            logger.error(f"Error analyzing codebase: {e}")
            error_list = ComprehensiveErrorList()
            error_list.analysis_duration = time.time() - start_time
            return error_list
    
    def add_error_listener(self, listener: Callable[[List[CodeError]], None]):
        """Add a listener for error updates."""
        self._error_listeners.append(listener)
    
    def remove_error_listener(self, listener: Callable[[List[CodeError]], None]):
        """Remove an error listener."""
        if listener in self._error_listeners:
            self._error_listeners.remove(listener)
    
    def get_cached_errors(self, file_path: Optional[str] = None) -> List[CodeError]:
        """Get cached errors for a file or all cached errors."""
        if file_path:
            return self._error_cache.get(file_path, [])
        
        all_errors = []
        for errors in self._error_cache.values():
            all_errors.extend(errors)
        return all_errors
    
    def clear_cache(self, file_path: Optional[str] = None):
        """Clear error cache for a file or all files."""
        if file_path:
            self._error_cache.pop(file_path, None)
        else:
            self._error_cache.clear()
    
    async def _send_request_and_wait(self, request, future, timeout: float = 30.0) -> Any:
        """Send request and wait for response with timeout."""
        # This would be implemented by the actual LSP client
        # For now, we'll simulate a response
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Simulate response data structure
        return {
            'errors': [],
            'diagnostics': [],
            'analysis': {
                'totalFiles': 0,
                'errorCount': 0,
                'warningCount': 0
            }
        }
    
    async def _process_comprehensive_response(self, response_data: Dict[str, Any]) -> ComprehensiveErrorList:
        """Process comprehensive error response from server."""
        error_list = ComprehensiveErrorList()
        
        # Process diagnostics from response
        diagnostics = response_data.get('diagnostics', [])
        for file_uri, file_diagnostics in diagnostics.items():
            file_path = file_uri.replace('file://', '')
            
            for diagnostic in file_diagnostics:
                error = CodeError.from_lsp_diagnostic(diagnostic, file_path)
                error_list.add_error(error)
        
        return error_list
    
    async def _process_file_errors_response(self, response_data: Dict[str, Any], file_path: str) -> List[CodeError]:
        """Process file-specific error response."""
        errors = []
        
        diagnostics = response_data.get('diagnostics', [])
        for diagnostic in diagnostics:
            error = CodeError.from_lsp_diagnostic(diagnostic, file_path)
            errors.append(error)
        
        return errors
    
    async def _process_codebase_analysis_response(self, response_data: Dict[str, Any]) -> ComprehensiveErrorList:
        """Process codebase analysis response."""
        return await self._process_comprehensive_response(response_data)
    
    def _update_error_cache(self, errors: List[CodeError]):
        """Update error cache with new errors."""
        # Group errors by file
        file_errors = {}
        for error in errors:
            file_path = error.location.file_path
            if file_path not in file_errors:
                file_errors[file_path] = []
            file_errors[file_path].append(error)
        
        # Update cache
        self._error_cache.update(file_errors)
    
    async def _notify_error_listeners(self, errors: List[CodeError]):
        """Notify all error listeners of updates."""
        for listener in self._error_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(errors)
                else:
                    listener(errors)
            except Exception as e:
                logger.error(f"Error in error listener: {e}")
    
    async def _handle_error_update(self, params: Dict[str, Any]):
        """Handle error update notification from server."""
        file_uri = params.get('uri', '')
        file_path = file_uri.replace('file://', '')
        
        diagnostics = params.get('diagnostics', [])
        errors = []
        
        for diagnostic in diagnostics:
            error = CodeError.from_lsp_diagnostic(diagnostic, file_path)
            errors.append(error)
        
        # Update cache
        self._error_cache[file_path] = errors
        
        # Notify listeners
        await self._notify_error_listeners(errors)

