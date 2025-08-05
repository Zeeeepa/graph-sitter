"""
Runtime Error Collection for Graph-Sitter

This module provides comprehensive runtime error collection and analysis
capabilities, integrating with Python's exception handling system and
providing detailed context for debugging.
"""

import os
import sys
import threading
import time
import traceback
import inspect
import ast
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from types import FrameType, TracebackType
import weakref

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


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
    
    # Additional context
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    code_context: Optional[str] = None
    
    def __str__(self) -> str:
        return f"RuntimeContext({self.exception_type}, {len(self.stack_trace)} frames)"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'exception_type': self.exception_type,
            'stack_trace': self.stack_trace,
            'local_variables': {k: str(v) for k, v in self.local_variables.items()},
            'global_variables': {k: str(v) for k, v in self.global_variables.items()},
            'execution_path': self.execution_path,
            'timestamp': self.timestamp,
            'thread_id': self.thread_id,
            'process_id': self.process_id,
            'function_name': self.function_name,
            'module_name': self.module_name,
            'code_context': self.code_context
        }


@dataclass
class RuntimeError:
    """Represents a runtime error with comprehensive context."""
    file_path: str
    line: int
    character: int
    message: str
    context: RuntimeContext
    error_id: str = field(default_factory=lambda: f"runtime_{int(time.time() * 1000000)}")
    
    # Error classification
    is_recoverable: bool = True
    severity: str = "error"
    category: str = "runtime"
    
    # Additional metadata
    first_occurrence: float = field(default_factory=time.time)
    last_occurrence: float = field(default_factory=time.time)
    occurrence_count: int = 1
    
    def update_occurrence(self):
        """Update occurrence tracking."""
        self.last_occurrence = time.time()
        self.occurrence_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'error_id': self.error_id,
            'file_path': self.file_path,
            'line': self.line,
            'character': self.character,
            'message': self.message,
            'context': self.context.to_dict(),
            'is_recoverable': self.is_recoverable,
            'severity': self.severity,
            'category': self.category,
            'first_occurrence': self.first_occurrence,
            'last_occurrence': self.last_occurrence,
            'occurrence_count': self.occurrence_count
        }


class RuntimeErrorCollector:
    """
    Collects runtime errors during code execution using various Python hooks
    and provides comprehensive error analysis capabilities.
    
    Features:
    - Exception hook integration
    - Variable capture at error points
    - Stack trace analysis
    - Error deduplication
    - Performance monitoring
    - Thread-safe operation
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.runtime_errors: List[RuntimeError] = []
        self.error_handlers: List[Callable[[RuntimeError], None]] = []
        self._lock = threading.RLock()
        
        # Original exception hooks
        self._original_excepthook: Optional[Callable[[type, BaseException, Optional[TracebackType]], Any]] = None
        self._original_threading_excepthook: Optional[Callable[..., Any]] = None
        self._active = False
        
        # Error collection settings
        self.max_errors = 1000
        self.max_stack_depth = 50
        self.collect_variables = True
        self.variable_max_length = 200
        self.deduplicate_errors = True
        
        # Error deduplication
        self._error_signatures: Dict[str, RuntimeError] = {}
        
        # Performance tracking
        self.collection_stats = {
            'total_exceptions_caught': 0,
            'errors_collected': 0,
            'errors_deduplicated': 0,
            'collection_start_time': None,
            'last_error_time': None
        }
        
        logger.info(f"Runtime error collector initialized for {self.repo_path}")
    
    def start_collection(self) -> None:
        """Start collecting runtime errors."""
        if self._active:
            logger.warning("Runtime error collection is already active")
            return
        
        try:
            # Install exception hooks
            self._original_excepthook = sys.excepthook
            self._original_threading_excepthook = getattr(threading, 'excepthook', None)
            
            sys.excepthook = self._handle_exception
            if hasattr(threading, 'excepthook'):
                threading.excepthook = self._handle_thread_exception
            
            self._active = True
            self.collection_stats['collection_start_time'] = time.time()
            
            logger.info("Runtime error collection started")
            
        except Exception as e:
            logger.error(f"Failed to start runtime error collection: {e}")
            raise
    
    def stop_collection(self) -> None:
        """Stop collecting runtime errors."""
        if not self._active:
            logger.warning("Runtime error collection is not active")
            return
        
        try:
            # Restore original exception hooks
            if self._original_excepthook:
                sys.excepthook = self._original_excepthook
            if self._original_threading_excepthook and hasattr(threading, 'excepthook'):
                threading.excepthook = self._original_threading_excepthook
            
            self._active = False
            logger.info("Runtime error collection stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop runtime error collection: {e}")
            raise
    
    def _handle_exception(self, exc_type: type, exc_value: BaseException, exc_traceback: Optional[TracebackType]) -> None:
        """Handle main thread exceptions."""
        try:
            self.collection_stats['total_exceptions_caught'] += 1
            self._collect_error(exc_type, exc_value, exc_traceback)
        except Exception as e:
            logger.error(f"Error in exception handler: {e}")
        
        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _handle_thread_exception(self, args: Any) -> None:
        """Handle thread exceptions."""
        try:
            self.collection_stats['total_exceptions_caught'] += 1
            self._collect_error(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception as e:
            logger.error(f"Error in thread exception handler: {e}")
        
        # Call original handler
        if self._original_threading_excepthook:
            self._original_threading_excepthook(args)
    
    def _collect_error(self, exc_type: type, exc_value: BaseException, exc_traceback: Optional[TracebackType]) -> None:
        """Collect error information from exception."""
        try:
            if exc_traceback is None:
                return
            
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
            runtime_context = self._create_runtime_context(
                exc_type, exc_value, exc_traceback, target_frame
            )
            
            # Create runtime error
            runtime_error = RuntimeError(
                file_path=self._get_relative_path(target_frame.filename),
                line=target_frame.lineno or 1,
                character=0,  # We don't have character info from traceback
                message=f"{exc_type.__name__}: {str(exc_value)}",
                context=runtime_context
            )
            
            # Classify error
            self._classify_error(runtime_error, exc_type, exc_value)
            
            # Handle deduplication
            if self.deduplicate_errors:
                signature = self._get_error_signature(runtime_error)
                if signature in self._error_signatures:
                    # Update existing error
                    existing_error = self._error_signatures[signature]
                    existing_error.update_occurrence()
                    self.collection_stats['errors_deduplicated'] += 1
                    
                    # Notify handlers with updated error
                    for handler in self.error_handlers:
                        try:
                            handler(existing_error)
                        except Exception as e:
                            logger.error(f"Error in error handler: {e}")
                    
                    return
                else:
                    self._error_signatures[signature] = runtime_error
            
            # Add to collection
            with self._lock:
                self.runtime_errors.append(runtime_error)
                
                # Limit collection size
                if len(self.runtime_errors) > self.max_errors:
                    removed_error = self.runtime_errors.pop(0)
                    # Remove from signatures if it was the only occurrence
                    if self.deduplicate_errors and removed_error.occurrence_count == 1:
                        signature = self._get_error_signature(removed_error)
                        self._error_signatures.pop(signature, None)
            
            self.collection_stats['errors_collected'] += 1
            self.collection_stats['last_error_time'] = time.time()
            
            # Notify handlers
            for handler in self.error_handlers:
                try:
                    handler(runtime_error)
                except Exception as e:
                    logger.error(f"Error in error handler: {e}")
            
            logger.debug(f"Collected runtime error: {runtime_error.error_id}")
            
        except Exception as e:
            logger.error(f"Failed to collect error: {e}")
    
    def _create_runtime_context(
        self, 
        exc_type: type, 
        exc_value: BaseException, 
        exc_traceback: TracebackType,
        target_frame: Any
    ) -> RuntimeContext:
        """Create comprehensive runtime context."""
        
        context = RuntimeContext(
            exception_type=exc_type.__name__,
            stack_trace=traceback.format_tb(exc_traceback, limit=self.max_stack_depth),
            timestamp=time.time(),
            thread_id=threading.get_ident(),
            process_id=os.getpid(),
            function_name=target_frame.name,
            module_name=self._get_module_name(target_frame.filename)
        )
        
        # Collect variable information if enabled
        if self.collect_variables and exc_traceback:
            try:
                frame: Optional[FrameType] = exc_traceback.tb_frame
                while frame:
                    if self._is_repo_file(frame.f_code.co_filename):
                        context.local_variables = self._safe_extract_variables(frame.f_locals)
                        context.global_variables = self._safe_extract_variables(frame.f_globals)
                        break
                    frame = frame.f_back
            except Exception as e:
                logger.debug(f"Failed to collect variables: {e}")
        
        # Get code context
        try:
            context.code_context = self._get_code_context(target_frame.filename, target_frame.lineno)
        except Exception as e:
            logger.debug(f"Failed to get code context: {e}")
        
        # Build execution path
        try:
            context.execution_path = self._build_execution_path(exc_traceback)
        except Exception as e:
            logger.debug(f"Failed to build execution path: {e}")
        
        return context
    
    def _classify_error(self, runtime_error: RuntimeError, exc_type: type, exc_value: BaseException):
        """Classify the runtime error."""
        
        # Determine if error is recoverable
        non_recoverable_types = {
            SystemExit, KeyboardInterrupt, MemoryError, RecursionError
        }
        runtime_error.is_recoverable = exc_type not in non_recoverable_types
        
        # Determine severity
        if exc_type in {SystemExit, KeyboardInterrupt}:
            runtime_error.severity = "critical"
        elif exc_type in {MemoryError, RecursionError}:
            runtime_error.severity = "critical"
        elif exc_type in {SyntaxError, ImportError, ModuleNotFoundError}:
            runtime_error.severity = "error"
        elif exc_type in {DeprecationWarning, FutureWarning}:
            runtime_error.severity = "warning"
        else:
            runtime_error.severity = "error"
        
        # Determine category
        if exc_type in {SyntaxError}:
            runtime_error.category = "syntax"
        elif exc_type in {ImportError, ModuleNotFoundError}:
            runtime_error.category = "import"
        elif exc_type in {TypeError, AttributeError, ValueError}:
            runtime_error.category = "type"
        elif exc_type in {IndexError, KeyError}:
            runtime_error.category = "access"
        elif exc_type in {IOError, OSError, FileNotFoundError}:
            runtime_error.category = "io"
        elif exc_type in {MemoryError, RecursionError}:
            runtime_error.category = "resource"
        else:
            runtime_error.category = "runtime"
    
    def _get_error_signature(self, runtime_error: RuntimeError) -> str:
        """Generate a signature for error deduplication."""
        return f"{runtime_error.context.exception_type}:{runtime_error.file_path}:{runtime_error.line}"
    
    def _is_repo_file(self, file_path: str) -> bool:
        """Check if file is within the repository."""
        try:
            Path(file_path).relative_to(self.repo_path)
            return True
        except ValueError:
            return False
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path within repository."""
        try:
            return str(Path(file_path).relative_to(self.repo_path))
        except ValueError:
            return file_path
    
    def _get_module_name(self, file_path: str) -> str:
        """Get module name from file path."""
        try:
            rel_path = self._get_relative_path(file_path)
            return rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        except Exception:
            return Path(file_path).stem
    
    def _safe_extract_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extract variable information."""
        safe_vars: Dict[str, Any] = {}
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
    
    def _get_code_context(self, file_path: str, line_number: int, context_lines: int = 5) -> Optional[str]:
        """Get code context around the error line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            context_lines_list = []
            for i in range(start_line, end_line):
                prefix = ">>> " if i == line_number - 1 else "    "
                context_lines_list.append(f"{prefix}{i+1:4d}: {lines[i].rstrip()}")
            
            return '\n'.join(context_lines_list)
            
        except Exception as e:
            logger.debug(f"Failed to get code context: {e}")
            return None
    
    def _build_execution_path(self, exc_traceback: TracebackType) -> List[str]:
        """Build execution path from traceback."""
        execution_path = []
        
        try:
            tb_list = traceback.extract_tb(exc_traceback)
            for frame in tb_list:
                if self._is_repo_file(frame.filename):
                    path_entry = f"{self._get_relative_path(frame.filename)}:{frame.name}:{frame.lineno}"
                    execution_path.append(path_entry)
        except Exception as e:
            logger.debug(f"Failed to build execution path: {e}")
        
        return execution_path
    
    def get_runtime_errors(self) -> List[RuntimeError]:
        """Get all collected runtime errors."""
        with self._lock:
            return self.runtime_errors.copy()
    
    def get_runtime_errors_for_file(self, file_path: str) -> List[RuntimeError]:
        """Get runtime errors for a specific file."""
        with self._lock:
            return [error for error in self.runtime_errors if error.file_path == file_path]
    
    def get_runtime_errors_by_category(self, category: str) -> List[RuntimeError]:
        """Get runtime errors filtered by category."""
        with self._lock:
            return [error for error in self.runtime_errors if error.category == category]
    
    def get_runtime_errors_by_severity(self, severity: str) -> List[RuntimeError]:
        """Get runtime errors filtered by severity."""
        with self._lock:
            return [error for error in self.runtime_errors if error.severity == severity]
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        with self._lock:
            self.runtime_errors.clear()
            self._error_signatures.clear()
        logger.info("Runtime errors cleared")
    
    def add_error_handler(self, handler: Callable[[RuntimeError], None]) -> None:
        """Add a handler to be called when new runtime errors are collected."""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[[RuntimeError], None]) -> None:
        """Remove an error handler."""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of collected runtime errors."""
        with self._lock:
            errors_by_type = defaultdict(int)
            errors_by_file = defaultdict(int)
            errors_by_category = defaultdict(int)
            errors_by_severity = defaultdict(int)
            
            for error in self.runtime_errors:
                errors_by_type[error.context.exception_type] += 1
                errors_by_file[error.file_path] += 1
                errors_by_category[error.category] += 1
                errors_by_severity[error.severity] += 1
            
            return {
                'total_errors': len(self.runtime_errors),
                'unique_errors': len(self._error_signatures),
                'errors_by_type': dict(errors_by_type),
                'errors_by_file': dict(errors_by_file),
                'errors_by_category': dict(errors_by_category),
                'errors_by_severity': dict(errors_by_severity),
                'collection_active': self._active,
                'collection_stats': self.collection_stats.copy(),
                'max_errors': self.max_errors
            }
    
    def get_most_frequent_errors(self, limit: int = 10) -> List[RuntimeError]:
        """Get the most frequently occurring errors."""
        with self._lock:
            sorted_errors = sorted(
                self.runtime_errors, 
                key=lambda x: x.occurrence_count, 
                reverse=True
            )
            return sorted_errors[:limit]
    
    def get_recent_errors(self, limit: int = 10) -> List[RuntimeError]:
        """Get the most recent errors."""
        with self._lock:
            sorted_errors = sorted(
                self.runtime_errors, 
                key=lambda x: x.last_occurrence, 
                reverse=True
            )
            return sorted_errors[:limit]
    
    def export_errors(self, format: str = "dict") -> Union[List[Dict[str, Any]], str]:
        """Export errors in various formats."""
        with self._lock:
            if format == "dict":
                return [error.to_dict() for error in self.runtime_errors]
            elif format == "json":
                import json
                return json.dumps([error.to_dict() for error in self.runtime_errors], indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")


# Global registry for runtime error collectors
_runtime_collectors: Dict[str, RuntimeErrorCollector] = {}
_collectors_lock = threading.RLock()


def get_runtime_collector(repo_path: str) -> RuntimeErrorCollector:
    """Get or create a runtime error collector for a repository."""
    repo_path = str(Path(repo_path).resolve())
    
    with _collectors_lock:
        if repo_path not in _runtime_collectors:
            _runtime_collectors[repo_path] = RuntimeErrorCollector(repo_path)
        
        return _runtime_collectors[repo_path]


def start_runtime_collection(repo_path: str) -> RuntimeErrorCollector:
    """Start runtime error collection for a repository."""
    collector = get_runtime_collector(repo_path)
    collector.start_collection()
    return collector


def stop_runtime_collection(repo_path: str) -> None:
    """Stop runtime error collection for a repository."""
    with _collectors_lock:
        if repo_path in _runtime_collectors:
            _runtime_collectors[repo_path].stop_collection()


def clear_runtime_collectors() -> None:
    """Clear all runtime error collectors."""
    with _collectors_lock:
        for collector in _runtime_collectors.values():
            try:
                collector.stop_collection()
            except Exception as e:
                logger.error(f"Error stopping collector: {e}")
        
        _runtime_collectors.clear()
        logger.info("All runtime error collectors cleared")


# Convenience functions for integration with existing LSP infrastructure
def integrate_with_lsp_bridge(lsp_bridge, repo_path: str) -> RuntimeErrorCollector:
    """Integrate runtime error collection with existing LSP bridge."""
    collector = get_runtime_collector(repo_path)
    
    def error_handler(runtime_error: RuntimeError):
        """Handle runtime errors by adding them to LSP diagnostics."""
        try:
            # Convert runtime error to LSP ErrorInfo format
            from .extensions.lsp.serena_bridge import ErrorInfo
            from .extensions.lsp.protocol.lsp_types import DiagnosticSeverity
            
            severity_map = {
                "critical": DiagnosticSeverity.ERROR,
                "error": DiagnosticSeverity.ERROR,
                "warning": DiagnosticSeverity.WARNING,
                "info": DiagnosticSeverity.INFORMATION,
                "hint": DiagnosticSeverity.HINT
            }
            
            error_info = ErrorInfo(
                file_path=runtime_error.file_path,
                line=runtime_error.line,
                character=runtime_error.character,
                message=runtime_error.message,
                severity=severity_map.get(runtime_error.severity, DiagnosticSeverity.ERROR),
                source="runtime_collector"
            )
            
            # Add to LSP bridge diagnostics cache
            if hasattr(lsp_bridge, '_add_runtime_diagnostic'):
                lsp_bridge._add_runtime_diagnostic(error_info)
                
        except Exception as e:
            logger.error(f"Error integrating runtime error with LSP bridge: {e}")
    
    collector.add_error_handler(error_handler)
    return collector
