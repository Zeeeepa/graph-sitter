"""
Comprehensive Serena LSP Bridge for Graph-Sitter

This module provides a comprehensive bridge between Serena's LSP implementation
and graph-sitter's codebase analysis system, with advanced error detection,
categorization, and real-time monitoring capabilities.
"""

import asyncio
import os
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set, Callable, Deque
import logging

from graph_sitter.shared.logging.get_logger import get_logger

# Try to import LSP protocol types, with fallbacks
try:
    from .protocol.lsp_types import DiagnosticSeverity, Diagnostic, Position, Range
except ImportError:
    # Fallback definitions if LSP protocol types are not available
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

# Try to import language servers, with fallbacks
try:
    from .language_servers.base import BaseLanguageServer
    from .language_servers.python_server import PythonLanguageServer
    LSP_SERVERS_AVAILABLE = True
except ImportError:
    LSP_SERVERS_AVAILABLE = False
    # Fallback base class
    class BaseLanguageServer:
        def __init__(self, *args, **kwargs):
            pass
        def initialize(self):
            return False
        def get_diagnostics(self):
            return []
        def supports_file(self, file_path):
            return False
        def shutdown(self):
            pass
    
    class PythonLanguageServer(BaseLanguageServer):
        pass

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Enhanced error severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class ErrorCategory(Enum):
    """Comprehensive error categories for 24+ error types."""
    # Core Language Errors
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    RUNTIME = "runtime"
    
    # Code Quality
    STYLE = "style"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    
    # Security & Safety
    SECURITY = "security"
    VULNERABILITY = "vulnerability"
    SAFETY = "safety"
    
    # Performance
    PERFORMANCE = "performance"
    MEMORY = "memory"
    OPTIMIZATION = "optimization"
    
    # Dependencies & Imports
    DEPENDENCY = "dependency"
    IMPORT = "import"
    COMPATIBILITY = "compatibility"
    
    # Code Organization
    UNUSED = "unused"
    DUPLICATE = "duplicate"
    DEAD_CODE = "dead_code"
    
    # Documentation & Testing
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    
    # Unknown/Other
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
class ErrorInfo:
    """Comprehensive error information with enhanced categorization."""
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
    
    # Legacy compatibility properties
    @property
    def file_path(self) -> str:
        return self.location.file_path
    
    @property
    def line(self) -> int:
        return self.location.line
    
    @property
    def character(self) -> int:
        return self.location.column
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning or hint)."""
        return self.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity == ErrorSeverity.WARNING
    
    @property
    def is_hint(self) -> bool:
        """Check if this is a hint."""
        return self.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT]
    
    @property
    def is_critical(self) -> bool:
        """Check if error is critical."""
        return self.severity == ErrorSeverity.CRITICAL
    
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
    def from_lsp_diagnostic(cls, diagnostic: Diagnostic, file_path: str) -> 'ErrorInfo':
        """Create ErrorInfo from LSP diagnostic data."""
        range_data = diagnostic.range
        start = range_data.start
        end = range_data.end
        
        location = ErrorLocation(
            file_path=file_path,
            line=start.line + 1,  # LSP is 0-based, we use 1-based
            column=start.character + 1,
            end_line=end.line + 1 if end else None,
            end_column=end.character + 1 if end else None
        )
        
        # Map LSP severity to our severity
        lsp_severity = diagnostic.severity or DiagnosticSeverity.ERROR
        severity_map = {
            DiagnosticSeverity.ERROR: ErrorSeverity.ERROR,
            DiagnosticSeverity.WARNING: ErrorSeverity.WARNING,
            DiagnosticSeverity.INFORMATION: ErrorSeverity.INFO,
            DiagnosticSeverity.HINT: ErrorSeverity.HINT
        }
        severity = severity_map.get(lsp_severity, ErrorSeverity.ERROR)
        
        # Determine category from diagnostic data
        category = cls._determine_category(diagnostic)
        
        return cls(
            id=f"{file_path}_{start.line}_{start.character}",
            message=diagnostic.message,
            severity=severity,
            category=category,
            location=location,
            code=str(diagnostic.code) if diagnostic.code else None,
            source=diagnostic.source or 'serena'
        )
    
    @staticmethod
    def _determine_category(diagnostic: Diagnostic) -> ErrorCategory:
        """Determine error category from diagnostic data."""
        source = (diagnostic.source or '').lower()
        code = str(diagnostic.code or '').lower()
        message = diagnostic.message.lower()
        
        # Category determination logic based on common patterns
        if 'syntax' in source or 'parse' in message or 'syntax' in message:
            return ErrorCategory.SYNTAX
        elif 'type' in source or 'type' in message:
            return ErrorCategory.TYPE
        elif 'security' in source or 'security' in message:
            return ErrorCategory.SECURITY
        elif 'performance' in source or 'performance' in message:
            return ErrorCategory.PERFORMANCE
        elif 'style' in source or 'lint' in source or 'format' in message:
            return ErrorCategory.STYLE
        elif 'import' in message or 'dependency' in message:
            return ErrorCategory.IMPORT
        elif 'unused' in message or 'not used' in message:
            return ErrorCategory.UNUSED
        elif 'duplicate' in message or 'redefined' in message:
            return ErrorCategory.DUPLICATE
        elif 'complexity' in message:
            return ErrorCategory.COMPLEXITY
        elif 'compatibility' in message:
            return ErrorCategory.COMPATIBILITY
        elif 'memory' in message:
            return ErrorCategory.MEMORY
        elif 'vulnerability' in message or 'vulnerable' in message:
            return ErrorCategory.VULNERABILITY
        elif 'test' in message:
            return ErrorCategory.TESTING
        elif 'doc' in message or 'comment' in message:
            return ErrorCategory.DOCUMENTATION
        else:
            return ErrorCategory.LOGIC
    
    def __str__(self) -> str:
        return self.display_text


@dataclass
class ComprehensiveErrorList:
    """Comprehensive list of code errors with metadata and analysis."""
    errors: List[ErrorInfo] = field(default_factory=list)
    total_count: int = 0
    critical_count: int = 0
    error_count: int = 0
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
        self.critical_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.CRITICAL)
        self.error_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.ERROR)
        self.warning_count = sum(1 for e in self.errors if e.severity == ErrorSeverity.WARNING)
        self.info_count = sum(1 for e in self.errors if e.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT])
        self.files_analyzed = {e.location.file_path for e in self.errors}
    
    def add_error(self, error: ErrorInfo):
        """Add an error to the list."""
        self.errors.append(error)
        self._update_counts()
    
    def add_errors(self, errors: List[ErrorInfo]):
        """Add multiple errors to the list."""
        self.errors.extend(errors)
        self._update_counts()
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """Get errors filtered by severity."""
        return [e for e in self.errors if e.severity == severity]
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """Get errors filtered by category."""
        return [e for e in self.errors if e.category == category]
    
    def get_errors_by_file(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        return [e for e in self.errors if e.location.file_path == file_path]
    
    def get_critical_errors(self) -> List[ErrorInfo]:
        """Get only critical errors."""
        return self.get_errors_by_severity(ErrorSeverity.CRITICAL)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = len(self.get_errors_by_category(category))
        
        return {
            'total_errors': self.total_count,
            'critical_errors': self.critical_count,
            'error_count': self.error_count,
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


class SerenaLSPBridge:
    """Comprehensive bridge between Serena's LSP implementation and graph-sitter."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.language_servers: Dict[str, BaseLanguageServer] = {}
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.is_initialized = False
        self._lock = threading.RLock()
        
        # Enhanced error tracking
        self._error_history: Deque[ErrorInfo] = deque(maxlen=1000)
        self._error_listeners: List[Callable[[List[ErrorInfo]], None]] = []
        self._last_analysis_time = 0.0
        self._analysis_count = 0
        
        # Real-time monitoring
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        self._initialize_language_servers()
    
    def _initialize_language_servers(self) -> None:
        """Initialize language servers for detected languages."""
        try:
            # Detect Python files
            if self._has_python_files():
                self._initialize_python_server()
            
            # Detect TypeScript/JavaScript files
            if self._has_typescript_files():
                self._initialize_typescript_server()
            
            # TODO: Add more language servers as needed
            
            self.is_initialized = len(self.language_servers) > 0 or not LSP_SERVERS_AVAILABLE
            logger.info(f"LSP bridge initialized for {self.repo_path} with {len(self.language_servers)} servers")
            
        except Exception as e:
            logger.error(f"Failed to initialize LSP bridge: {e}")
    
    def _has_python_files(self) -> bool:
        """Check if repository contains Python files."""
        for py_file in self.repo_path.rglob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):
                return True
        return False
    
    def _has_typescript_files(self) -> bool:
        """Check if repository contains TypeScript/JavaScript files."""
        for ext in ["*.ts", "*.tsx", "*.js", "*.jsx"]:
            for file in self.repo_path.rglob(ext):
                if not any(part.startswith('.') for part in file.parts):
                    return True
        return False
    
    def _initialize_python_server(self) -> None:
        """Initialize Python language server."""
        if not LSP_SERVERS_AVAILABLE:
            return
            
        try:
            server = PythonLanguageServer(str(self.repo_path))
            if server.initialize():
                self.language_servers['python'] = server
                logger.info("Python language server initialized")
            else:
                logger.warning("Failed to initialize Python language server")
            
        except Exception as e:
            logger.error(f"Failed to initialize Python language server: {e}")
    
    def _initialize_typescript_server(self) -> None:
        """Initialize TypeScript language server."""
        if not LSP_SERVERS_AVAILABLE:
            return
            
        try:
            # TODO: Implement TypeScript server initialization
            logger.info("TypeScript language server support not yet implemented")
        except Exception as e:
            logger.error(f"Failed to initialize TypeScript language server: {e}")
    
    def get_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics from all language servers."""
        if not self.is_initialized:
            return self._get_fallback_diagnostics()
        
        all_diagnostics = []
        
        with self._lock:
            for lang, server in self.language_servers.items():
                try:
                    diagnostics = server.get_diagnostics()
                    # Convert to ErrorInfo if needed
                    converted_diagnostics = []
                    for diag in diagnostics:
                        if isinstance(diag, ErrorInfo):
                            converted_diagnostics.append(diag)
                        else:
                            # Convert from LSP diagnostic
                            converted_diagnostics.append(
                                ErrorInfo.from_lsp_diagnostic(diag, diag.get('file_path', ''))
                            )
                    all_diagnostics.extend(converted_diagnostics)
                except Exception as e:
                    logger.error(f"Error getting diagnostics from {lang} server: {e}")
        
        # Update error history
        self._update_error_history(all_diagnostics)
        
        return all_diagnostics
    
    def _get_fallback_diagnostics(self) -> List[ErrorInfo]:
        """Get fallback diagnostics when LSP servers are not available."""
        # This could implement basic static analysis or return cached results
        return []
    
    def _update_error_history(self, errors: List[ErrorInfo]) -> None:
        """Update error history and notify listeners."""
        with self._lock:
            # Add new errors to history
            for error in errors:
                self._error_history.append(error)
            
            self._last_analysis_time = time.time()
            self._analysis_count += 1
            
            # Notify listeners
            for listener in self._error_listeners:
                try:
                    listener(errors)
                except Exception as e:
                    logger.error(f"Error in error listener: {e}")
    
    def get_comprehensive_errors(
        self,
        include_context: bool = True,
        include_suggestions: bool = True,
        max_errors: Optional[int] = None,
        severity_filter: Optional[List[ErrorSeverity]] = None
    ) -> ComprehensiveErrorList:
        """
        Get comprehensive error analysis with enhanced categorization.
        
        Args:
            include_context: Whether to include error context
            include_suggestions: Whether to include fix suggestions
            max_errors: Maximum number of errors to return
            severity_filter: Filter by error severities
            
        Returns:
            Comprehensive error list with analysis
        """
        start_time = time.time()
        
        # Get all diagnostics
        all_errors = self.get_diagnostics()
        
        # Apply severity filter
        if severity_filter:
            all_errors = [e for e in all_errors if e.severity in severity_filter]
        
        # Apply max errors limit
        if max_errors and len(all_errors) > max_errors:
            # Prioritize critical and error severity
            critical_errors = [e for e in all_errors if e.severity == ErrorSeverity.CRITICAL]
            error_errors = [e for e in all_errors if e.severity == ErrorSeverity.ERROR]
            other_errors = [e for e in all_errors if e.severity not in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]]
            
            # Take up to max_errors, prioritizing critical and errors
            filtered_errors = []
            remaining = max_errors
            
            for error_list in [critical_errors, error_errors, other_errors]:
                if remaining <= 0:
                    break
                take = min(len(error_list), remaining)
                filtered_errors.extend(error_list[:take])
                remaining -= take
            
            all_errors = filtered_errors
        
        # Enhance errors with context and suggestions if requested
        if include_context or include_suggestions:
            all_errors = self._enhance_errors(all_errors, include_context, include_suggestions)
        
        # Create comprehensive error list
        error_list = ComprehensiveErrorList(errors=all_errors)
        error_list.analysis_duration = time.time() - start_time
        
        return error_list
    
    def _enhance_errors(
        self,
        errors: List[ErrorInfo],
        include_context: bool,
        include_suggestions: bool
    ) -> List[ErrorInfo]:
        """Enhance errors with additional context and suggestions."""
        enhanced_errors = []
        
        for error in errors:
            enhanced_error = error
            
            if include_context:
                enhanced_error = self._add_error_context(enhanced_error)
            
            if include_suggestions:
                enhanced_error = self._add_error_suggestions(enhanced_error)
            
            enhanced_errors.append(enhanced_error)
        
        return enhanced_errors
    
    def _add_error_context(self, error: ErrorInfo) -> ErrorInfo:
        """Add contextual information to an error."""
        try:
            # Read file content around error location
            file_path = Path(error.location.file_path)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Get context lines (5 before and after)
                start_line = max(0, error.location.line - 6)
                end_line = min(len(lines), error.location.line + 5)
                context_lines = lines[start_line:end_line]
                
                error.context['surrounding_code'] = {
                    'lines': [line.rstrip() for line in context_lines],
                    'start_line': start_line + 1,
                    'error_line': error.location.line
                }
        except Exception as e:
            logger.debug(f"Could not add context to error: {e}")
        
        return error
    
    def _add_error_suggestions(self, error: ErrorInfo) -> ErrorInfo:
        """Add fix suggestions to an error based on its category and message."""
        suggestions = []
        
        # Category-based suggestions
        if error.category == ErrorCategory.SYNTAX:
            suggestions.extend([
                "Check for missing parentheses, brackets, or quotes",
                "Verify proper indentation",
                "Look for typos in keywords"
            ])
        elif error.category == ErrorCategory.TYPE:
            suggestions.extend([
                "Check parameter types and function signatures",
                "Verify return type annotations",
                "Consider using type hints"
            ])
        elif error.category == ErrorCategory.IMPORT:
            suggestions.extend([
                "Check if the module is installed",
                "Verify the import path is correct",
                "Look for circular imports"
            ])
        elif error.category == ErrorCategory.UNUSED:
            suggestions.extend([
                "Remove unused variables or functions",
                "Consider prefixing with underscore if intentionally unused"
            ])
        elif error.category == ErrorCategory.SECURITY:
            suggestions.extend([
                "Review security implications",
                "Consider input validation",
                "Check for potential vulnerabilities"
            ])
        elif error.category == ErrorCategory.PERFORMANCE:
            suggestions.extend([
                "Consider optimizing algorithm complexity",
                "Look for unnecessary computations",
                "Consider caching frequently used values"
            ])
        
        # Message-based suggestions
        message_lower = error.message.lower()
        if "undefined" in message_lower or "not defined" in message_lower:
            suggestions.append("Check if the variable or function is properly imported or defined")
        
        if "indentation" in message_lower:
            suggestions.append("Fix indentation to match Python standards")
        
        if suggestions:
            error.suggestions = suggestions[:3]  # Limit to top 3 suggestions
        
        return error
    
    def add_error_listener(self, listener: Callable[[List[ErrorInfo]], None]) -> None:
        """Add a listener for error updates."""
        with self._lock:
            self._error_listeners.append(listener)
    
    def remove_error_listener(self, listener: Callable[[List[ErrorInfo]], None]) -> None:
        """Remove an error listener."""
        with self._lock:
            if listener in self._error_listeners:
                self._error_listeners.remove(listener)
    
    def start_real_time_monitoring(self, interval: float = 5.0) -> None:
        """Start real-time error monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        def monitor_loop():
            while self._monitoring_active:
                try:
                    # Get fresh diagnostics
                    errors = self.get_diagnostics()
                    
                    # Sleep for the specified interval
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info(f"Started real-time error monitoring with {interval}s interval")
    
    def stop_real_time_monitoring(self) -> None:
        """Stop real-time error monitoring."""
        self._monitoring_active = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        
        logger.info("Stopped real-time error monitoring")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        with self._lock:
            errors = list(self._error_history)
        
        if not errors:
            return {
                'total_errors': 0,
                'by_severity': {},
                'by_category': {},
                'by_file': {},
                'analysis_count': self._analysis_count,
                'last_analysis': self._last_analysis_time
            }
        
        # Count by severity
        severity_counts = defaultdict(int)
        for error in errors:
            severity_counts[error.severity.value] += 1
        
        # Count by category
        category_counts = defaultdict(int)
        for error in errors:
            category_counts[error.category.value] += 1
        
        # Count by file
        file_counts = defaultdict(int)
        for error in errors:
            file_counts[error.location.file_path] += 1
        
        # Get top problematic files
        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_errors': len(errors),
            'by_severity': dict(severity_counts),
            'by_category': dict(category_counts),
            'by_file': dict(file_counts),
            'top_problematic_files': top_files,
            'analysis_count': self._analysis_count,
            'last_analysis': self._last_analysis_time,
            'monitoring_active': self._monitoring_active
        }
    
    def analyze_codebase(
        self,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> ComprehensiveErrorList:
        """
        Analyze entire codebase for errors.
        
        Args:
            file_patterns: File patterns to include (e.g., ['*.py', '*.ts'])
            exclude_patterns: File patterns to exclude
            
        Returns:
            Comprehensive error analysis of the codebase
        """
        start_time = time.time()
        
        # Get all files to analyze
        files_to_analyze = self._get_files_to_analyze(file_patterns, exclude_patterns)
        
        all_errors = []
        
        # Analyze each file
        for file_path in files_to_analyze:
            try:
                file_errors = self.get_file_diagnostics(str(file_path))
                all_errors.extend(file_errors)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
        
        # Create comprehensive error list
        error_list = ComprehensiveErrorList(errors=all_errors)
        error_list.analysis_duration = time.time() - start_time
        
        return error_list
    
    def _get_files_to_analyze(
        self,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Path]:
        """Get list of files to analyze based on patterns."""
        files = []
        
        # Default patterns if none provided
        if not file_patterns:
            file_patterns = ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx']
        
        # Find files matching patterns
        for pattern in file_patterns:
            for file_path in self.repo_path.rglob(pattern):
                # Skip hidden files and directories
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                
                # Skip excluded patterns
                if exclude_patterns:
                    skip = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            skip = True
                            break
                    if skip:
                        continue
                
                files.append(file_path)
        
        return files
    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        if not self.is_initialized:
            return []
        
        file_diagnostics = []
        
        with self._lock:
            for lang, server in self.language_servers.items():
                try:
                    if server.supports_file(file_path):
                        diagnostics = server.get_file_diagnostics(file_path)
                        file_diagnostics.extend(diagnostics)
                except Exception as e:
                    logger.error(f"Error getting file diagnostics from {lang} server: {e}")
        
        return file_diagnostics
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.is_initialized:
            return
        
        with self._lock:
            self.diagnostics_cache.clear()
            
            for lang, server in self.language_servers.items():
                try:
                    server.refresh_diagnostics()
                except Exception as e:
                    logger.error(f"Error refreshing diagnostics for {lang} server: {e}")
    
    def shutdown(self) -> None:
        """Shutdown all language servers and cleanup resources."""
        # Stop real-time monitoring
        self.stop_real_time_monitoring()
        
        with self._lock:
            # Shutdown language servers
            for lang, server in self.language_servers.items():
                try:
                    server.shutdown()
                    logger.info(f"Shutdown {lang} language server")
                except Exception as e:
                    logger.error(f"Error shutting down {lang} server: {e}")
            
            # Clear all caches and listeners
            self.language_servers.clear()
            self.diagnostics_cache.clear()
            self._error_history.clear()
            self._error_listeners.clear()
            self.is_initialized = False
            
        logger.info("SerenaLSPBridge shutdown complete")
    
    def get_completions(self, file_path: str, line: int, character: int) -> List[Any]:
        """Get code completions at the specified position."""
        if not self.is_initialized:
            return []
        
        # Find appropriate language server
        for server in self.language_servers.values():
            if server.supports_file(file_path):
                return server.get_completions(file_path, line, character)
        
        return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Any]:
        """Get hover information at the specified position."""
        if not self.is_initialized:
            return None
        
        # Find appropriate language server
        for server in self.language_servers.values():
            if server.supports_file(file_path):
                return server.get_hover_info(file_path, line, character)
        
        return None
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[Any]:
        """Get signature help at the specified position."""
        if not self.is_initialized:
            return None
        
        # Find appropriate language server
        for server in self.language_servers.values():
            if server.supports_file(file_path):
                return server.get_signature_help(file_path, line, character)
        
        return None
    
    def initialize_language_servers(self) -> None:
        """Initialize all language servers."""
        with self._lock:
            for server in self.language_servers.values():
                if not server.is_running:
                    server.initialize()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the LSP bridge."""
        server_status = {}
        for lang, server in self.language_servers.items():
            server_status[lang] = server.get_status()
        
        return {
            'initialized': self.is_initialized,
            'language_servers': list(self.language_servers.keys()),
            'repo_path': str(self.repo_path),
            'server_details': server_status
        }
