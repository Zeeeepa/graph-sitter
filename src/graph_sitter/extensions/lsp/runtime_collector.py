"""
Runtime Error Collector for Graph-Sitter LSP Extension

This module provides comprehensive runtime error collection capabilities,
including real-time error capture, context analysis, and intelligent fix suggestions.
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

from graph_sitter.shared.logging.get_logger import get_logger
from .lsp_types import DiagnosticSeverity, ErrorType

logger = get_logger(__name__)


# ErrorType is now imported from lsp_types


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


class RuntimeErrorCollector:
    """
    Collects runtime errors during code execution using various Python hooks
    and provides comprehensive context analysis.
    
    Features:
    - Real-time error capture using exception hooks
    - Full execution context including stack traces and variable states
    - Intelligent fix suggestions based on error types
    - Thread-safe operations with proper resource management
    - Configurable collection limits for performance tuning
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.runtime_errors: List['ErrorInfo'] = []
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
        
        # Performance tracking
        self._collection_stats = {
            'total_collected': 0,
            'collection_time': 0.0,
            'last_collection_time': 0.0
        }
    
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
    
    def shutdown(self) -> None:
        """Shutdown the runtime error collector."""
        self.stop_collection()
        with self._lock:
            self.runtime_errors.clear()
            self.error_handlers.clear()
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle main thread exceptions."""
        try:
            self._collect_error(exc_type, exc_value, exc_traceback)
        except Exception as e:
            logger.error(f"Error in exception handler: {e}")
        
        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _handle_thread_exception(self, args):
        """Handle thread exceptions."""
        try:
            self._collect_error(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception as e:
            logger.error(f"Error in thread exception handler: {e}")
        
        # Call original handler
        if self._original_threading_excepthook:
            self._original_threading_excepthook(args)
    
    def _collect_error(self, exc_type, exc_value, exc_traceback) -> None:
        """Collect error information from exception."""
        start_time = time.time()
        
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
            
            # Build execution path
            runtime_context.execution_path = []
            for frame in tb_list:
                if hasattr(frame, 'name'):
                    runtime_context.execution_path.append(frame.name)
                else:
                    runtime_context.execution_path.append('<module>')
            
            # Collect variable information if enabled
            if self.collect_variables and exc_traceback:
                try:
                    frame = exc_traceback.tb_frame
                    runtime_context.local_variables = self._safe_extract_variables(frame.f_locals)
                    runtime_context.global_variables = self._safe_extract_variables(frame.f_globals)
                except Exception as e:
                    logger.debug(f"Failed to collect variables: {e}")
            
            # Import ErrorInfo here to avoid circular imports
            from .serena_bridge import ErrorInfo
            
            # Create ErrorInfo
            error_info = ErrorInfo(
                file_path=str(Path(target_frame.filename).relative_to(self.repo_path)) if self._is_repo_file(target_frame.filename) else target_frame.filename,
                line=target_frame.lineno - 1,  # Convert to 0-based
                character=0,  # We don't have character info from traceback
                message=f"{exc_type.__name__}: {str(exc_value)}",
                severity=DiagnosticSeverity.ERROR,
                error_type=ErrorType.RUNTIME_ERROR,
                source="runtime_collector",
                runtime_context=runtime_context,
                fix_suggestions=self._generate_fix_suggestions(exc_type.__name__, str(exc_value))
            )
            
            # Add to collection
            with self._lock:
                self.runtime_errors.append(error_info)
                
                # Limit collection size
                if len(self.runtime_errors) > self.max_errors:
                    self.runtime_errors = self.runtime_errors[-self.max_errors:]
                
                # Update stats
                self._collection_stats['total_collected'] += 1
                collection_time = time.time() - start_time
                self._collection_stats['collection_time'] += collection_time
                self._collection_stats['last_collection_time'] = collection_time
            
            # Notify handlers
            for handler in self.error_handlers:
                try:
                    handler(error_info)
                except Exception as e:
                    logger.error(f"Error in error handler: {e}")
            
            logger.debug(f"Collected runtime error: {error_info}")
            
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
    
    def _generate_fix_suggestions(self, exception_type: str, message: str) -> List[str]:
        """Generate fix suggestions based on exception type and message."""
        suggestions = []
        
        try:
            message_lower = message.lower()
            
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
            elif exception_type == "ImportError" or exception_type == "ModuleNotFoundError":
                suggestions.append("Check if the module is installed")
                suggestions.append("Verify the import path is correct")
                suggestions.append("Check virtual environment activation")
            elif exception_type == "FileNotFoundError":
                suggestions.append("Verify the file path is correct")
                suggestions.append("Check if the file exists")
                suggestions.append("Use absolute paths or proper relative paths")
            elif exception_type == "PermissionError":
                suggestions.append("Check file/directory permissions")
                suggestions.append("Run with appropriate privileges")
                suggestions.append("Verify file is not in use by another process")
            
            # Add context-specific suggestions
            if "division by zero" in message_lower:
                suggestions.append("Add check for zero before division")
            elif "none" in message_lower:
                suggestions.append("Add None check before accessing attributes")
            elif "list index out of range" in message_lower:
                suggestions.append("Check list length before accessing elements")
            elif "dictionary" in message_lower and "key" in message_lower:
                suggestions.append("Use 'in' operator to check key existence")
            
        except Exception as e:
            logger.debug(f"Failed to generate fix suggestions: {e}")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def get_runtime_errors(self) -> List['ErrorInfo']:
        """Get all collected runtime errors."""
        with self._lock:
            return self.runtime_errors.copy()
    
    def get_runtime_errors_for_file(self, file_path: str) -> List['ErrorInfo']:
        """Get runtime errors for a specific file."""
        with self._lock:
            return [error for error in self.runtime_errors if error.file_path == file_path]
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        with self._lock:
            self.runtime_errors.clear()
        logger.info("Runtime errors cleared")
    
    def add_error_handler(self, handler: Callable[['ErrorInfo'], None]) -> None:
        """Add a handler to be called when new runtime errors are collected."""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[['ErrorInfo'], None]) -> None:
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
                'max_errors': self.max_errors,
                'collection_stats': self._collection_stats.copy()
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection performance statistics."""
        with self._lock:
            stats = self._collection_stats.copy()
            stats['average_collection_time'] = (
                stats['collection_time'] / max(1, stats['total_collected'])
            )
            return stats
    
    def configure_collection(self, 
                           max_errors: Optional[int] = None,
                           max_stack_depth: Optional[int] = None,
                           collect_variables: Optional[bool] = None,
                           variable_max_length: Optional[int] = None) -> None:
        """Configure collection parameters."""
        if max_errors is not None:
            self.max_errors = max_errors
        if max_stack_depth is not None:
            self.max_stack_depth = max_stack_depth
        if collect_variables is not None:
            self.collect_variables = collect_variables
        if variable_max_length is not None:
            self.variable_max_length = variable_max_length
        
        logger.info(f"Runtime error collection configured: max_errors={self.max_errors}, "
                   f"max_stack_depth={self.max_stack_depth}, collect_variables={self.collect_variables}")
    
    @property
    def is_active(self) -> bool:
        """Check if error collection is active."""
        return self._active
    
    @property
    def error_count(self) -> int:
        """Get current error count."""
        with self._lock:
            return len(self.runtime_errors)


# Convenience functions for easy integration
def create_runtime_collector(repo_path: str, auto_start: bool = True) -> RuntimeErrorCollector:
    """Create and optionally start a runtime error collector."""
    collector = RuntimeErrorCollector(repo_path)
    if auto_start:
        collector.start_collection()
    return collector


def collect_runtime_errors_context_manager(repo_path: str):
    """Context manager for temporary runtime error collection."""
    class RuntimeErrorCollectionContext:
        def __init__(self, repo_path: str):
            self.collector = RuntimeErrorCollector(repo_path)
            
        def __enter__(self):
            self.collector.start_collection()
            return self.collector
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.collector.stop_collection()
    
    return RuntimeErrorCollectionContext(repo_path)
