"""
Runtime Error Collection for Graph-Sitter

This module provides runtime error collection capabilities that integrate
with graph-sitter's codebase analysis system. It collects errors that occur
during code execution and provides them in a format compatible with
LSP diagnostics.
"""

import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from collections import defaultdict
from types import FrameType, TracebackType

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
            'process_id': self.process_id
        }
    
    def __str__(self) -> str:
        return f"RuntimeContext({self.exception_type}, {len(self.stack_trace)} frames)"


@dataclass
class RuntimeError:
    """Runtime error information compatible with LSP diagnostics."""
    file_path: str
    line: int
    character: int
    message: str
    severity: str = "error"  # error, warning, info, hint
    context: RuntimeContext = field(default_factory=lambda: RuntimeContext("Unknown"))
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'file_path': self.file_path,
            'line': self.line,
            'character': self.character,
            'message': self.message,
            'severity': self.severity,
            'context': self.context.to_dict(),
            'timestamp': self.timestamp
        }
    
    def __str__(self) -> str:
        return f"{self.severity.upper()} {self.file_path}:{self.line}:{self.character} - {self.message}"


class RuntimeErrorCollector:
    """
    Collects runtime errors during code execution using various Python hooks.
    
    Features:
    - Exception hook integration
    - Thread-safe error collection
    - Context information gathering
    - Variable state capture
    - Configurable collection limits
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.runtime_errors: List[RuntimeError] = []
        self.error_handlers: List[Callable[[RuntimeError], None]] = []
        self._lock = threading.RLock()
        self._original_excepthook: Optional[Callable[[type, BaseException, Optional[TracebackType]], Any]] = None
        self._original_threading_excepthook: Optional[Callable[..., Any]] = None
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
            logger.info("Runtime error collection started")
            
        except Exception as e:
            logger.error(f"Failed to start runtime error collection: {e}")
    
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
            logger.info("Runtime error collection stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop runtime error collection: {e}")
    
    def _handle_exception(self, exc_type: type, exc_value: BaseException, exc_traceback: Optional[TracebackType]) -> None:
        """Handle main thread exceptions."""
        try:
            self._collect_error(exc_type, exc_value, exc_traceback)
        except Exception as e:
            logger.error(f"Error in exception handler: {e}")
        
        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _handle_thread_exception(self, args: Any) -> None:
        """Handle thread exceptions."""
        try:
            self._collect_error(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception as e:
            logger.error(f"Error in thread exception handler: {e}")
        
        # Call original handler
        if self._original_threading_excepthook:
            self._original_threading_excepthook(args)
    
    def _collect_error(self, exc_type: type, exc_value: BaseException, exc_traceback: Optional[TracebackType]) -> None:
        """Collect error information from exception."""
        try:
            # Extract traceback information
            if exc_traceback is None:
                return
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
                    frame: Optional[FrameType] = exc_traceback.tb_frame
                    if frame:
                        runtime_context.local_variables = self._safe_extract_variables(frame.f_locals)
                        runtime_context.global_variables = self._safe_extract_variables(frame.f_globals)
                except Exception as e:
                    logger.debug(f"Failed to collect variables: {e}")
            
            # Create RuntimeError with proper type handling
            line_number = target_frame.lineno if target_frame.lineno is not None else 1
            runtime_error = RuntimeError(
                file_path=str(Path(target_frame.filename).relative_to(self.repo_path)) if self._is_repo_file(target_frame.filename) else target_frame.filename,
                line=line_number,  # Ensure we have a valid int
                character=0,  # We don't have character info from traceback
                message=f"{exc_type.__name__}: {str(exc_value)}",
                severity="error",
                context=runtime_context
            )
            
            # Add to collection
            with self._lock:
                self.runtime_errors.append(runtime_error)
                
                # Limit collection size
                if len(self.runtime_errors) > self.max_errors:
                    self.runtime_errors = self.runtime_errors[-self.max_errors:]
            
            # Notify handlers
            for handler in self.error_handlers:
                try:
                    handler(runtime_error)
                except Exception as e:
                    logger.error(f"Error in error handler: {e}")
            
            logger.debug(f"Collected runtime error: {runtime_error}")
            
        except Exception as e:
            logger.error(f"Failed to collect error: {e}")
    
    def _is_repo_file(self, file_path: str) -> bool:
        """Check if file is within the repository."""
        try:
            Path(file_path).relative_to(self.repo_path)
            return True
        except ValueError:
            return False
    
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
    
    def get_runtime_errors(self) -> List[RuntimeError]:
        """Get all collected runtime errors."""
        with self._lock:
            return self.runtime_errors.copy()
    
    def get_runtime_errors_for_file(self, file_path: str) -> List[RuntimeError]:
        """Get runtime errors for a specific file."""
        with self._lock:
            return [error for error in self.runtime_errors if error.file_path == file_path]
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        with self._lock:
            self.runtime_errors.clear()
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
            errors_by_type: Dict[str, int] = defaultdict(int)
            errors_by_file: Dict[str, int] = defaultdict(int)
            
            for error in self.runtime_errors:
                errors_by_type[error.context.exception_type] += 1
                errors_by_file[error.file_path] += 1
            
            return {
                'total_errors': len(self.runtime_errors),
                'errors_by_type': dict(errors_by_type),
                'errors_by_file': dict(errors_by_file),
                'collection_active': self._active,
                'max_errors': self.max_errors
            }


# Global registry of runtime error collectors
_runtime_collectors: Dict[str, RuntimeErrorCollector] = {}
_collector_lock = threading.RLock()


def get_runtime_collector(repo_path: str) -> RuntimeErrorCollector:
    """
    Get or create a runtime error collector for a repository.
    
    This function maintains a registry of collectors to avoid creating
    multiple collectors for the same repository.
    """
    repo_path = str(Path(repo_path).resolve())
    
    with _collector_lock:
        if repo_path not in _runtime_collectors:
            _runtime_collectors[repo_path] = RuntimeErrorCollector(repo_path)
        
        return _runtime_collectors[repo_path]


def shutdown_all_runtime_collectors() -> None:
    """Shutdown all active runtime error collectors."""
    with _collector_lock:
        for collector in _runtime_collectors.values():
            try:
                collector.stop_collection()
            except Exception as e:
                logger.error(f"Error shutting down runtime collector: {e}")
        
        _runtime_collectors.clear()
        logger.info("All runtime error collectors shutdown")


# Convenience functions
def start_runtime_collection(repo_path: str) -> RuntimeErrorCollector:
    """Start runtime error collection for a repository."""
    collector = get_runtime_collector(repo_path)
    collector.start_collection()
    return collector


def stop_runtime_collection(repo_path: str) -> None:
    """Stop runtime error collection for a repository."""
    collector = get_runtime_collector(repo_path)
    collector.stop_collection()


def get_runtime_errors(repo_path: str) -> List[RuntimeError]:
    """Get runtime errors for a repository."""
    collector = get_runtime_collector(repo_path)
    return collector.get_runtime_errors()


def clear_runtime_errors(repo_path: str) -> None:
    """Clear runtime errors for a repository."""
    collector = get_runtime_collector(repo_path)
    collector.clear_runtime_errors()

