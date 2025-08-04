"""
Runtime Error Collector for Graph-Sitter LSP

This module provides runtime error collection capabilities that can be optionally
integrated with the SerenaLSPBridge for comprehensive error detection.
"""

import sys
import threading
import traceback
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Set
from enum import IntEnum

from graph_sitter.shared.logging.get_logger import get_logger
from .protocol.lsp_types import DiagnosticSeverity

logger = get_logger(__name__)


class ErrorType(IntEnum):
    """Types of errors that can be collected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues


@dataclass
class RuntimeContext:
    """Context information for runtime errors."""
    exception_type: str
    stack_trace: List[str] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    thread_id: Optional[int] = None
    process_id: Optional[int] = None


@dataclass
class RuntimeErrorInfo:
    """Enhanced error information with runtime context."""
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    error_type: ErrorType = ErrorType.RUNTIME_ERROR
    runtime_context: Optional[RuntimeContext] = None
    fix_suggestions: List[str] = field(default_factory=list)
    source: Optional[str] = "runtime_collector"
    code: Optional[str] = None
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning or hint)."""
        return self.severity == DiagnosticSeverity.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity == DiagnosticSeverity.WARNING
    
    @property
    def is_runtime_error(self) -> bool:
        """Check if this is a runtime error."""
        return self.error_type == ErrorType.RUNTIME_ERROR
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get comprehensive context information."""
        context = {
            'basic_info': {
                'file_path': self.file_path,
                'line': self.line,
                'character': self.character,
                'message': self.message,
                'severity': self.severity.name,
                'error_type': self.error_type.name,
                'source': self.source,
                'code': self.code
            },
            'fix_suggestions': self.fix_suggestions
        }
        
        if self.runtime_context:
            context['runtime'] = {
                'exception_type': self.runtime_context.exception_type,
                'stack_trace': self.runtime_context.stack_trace,
                'local_variables': self.runtime_context.local_variables,
                'global_variables': self.runtime_context.global_variables,
                'execution_path': self.runtime_context.execution_path,
                'timestamp': self.runtime_context.timestamp,
                'thread_id': self.runtime_context.thread_id,
                'process_id': self.runtime_context.process_id
            }
        
        return context


class RuntimeErrorCollector:
    """Collects runtime errors during code execution."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.errors: List[RuntimeErrorInfo] = []
        self.error_handlers: List[Callable[[RuntimeErrorInfo], None]] = []
        self.max_errors = 1000
        self.max_stack_depth = 50
        self.collect_variables = True
        self.variable_max_length = 200
        self._lock = threading.RLock()
        self._active = False
        self._original_excepthook = None
        self._original_threading_excepthook = None
        
        # Track files we care about (within repo)
        self._repo_files: Set[str] = set()
        self._update_repo_files()
    
    def _update_repo_files(self) -> None:
        """Update the set of files within the repository."""
        try:
            for py_file in self.repo_path.rglob("*.py"):
                if not any(part.startswith('.') for part in py_file.parts):
                    self._repo_files.add(str(py_file.absolute()))
        except Exception as e:
            logger.warning(f"Failed to update repo files: {e}")
    
    def start_collection(self) -> None:
        """Start collecting runtime errors."""
        if self._active:
            return
        
        with self._lock:
            # Store original exception hooks
            self._original_excepthook = sys.excepthook
            if hasattr(threading, 'excepthook'):
                self._original_threading_excepthook = threading.excepthook
            
            # Install our exception hooks
            sys.excepthook = self._handle_exception
            if hasattr(threading, 'excepthook'):
                threading.excepthook = self._handle_threading_exception
            
            self._active = True
            logger.info("Runtime error collection started")
    
    def stop_collection(self) -> None:
        """Stop collecting runtime errors."""
        if not self._active:
            return
        
        with self._lock:
            # Restore original exception hooks
            if self._original_excepthook:
                sys.excepthook = self._original_excepthook
            if self._original_threading_excepthook and hasattr(threading, 'excepthook'):
                threading.excepthook = self._original_threading_excepthook
            
            self._active = False
            logger.info("Runtime error collection stopped")
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle main thread exceptions."""
        try:
            self._process_exception(exc_type, exc_value, exc_traceback)
        except Exception as e:
            logger.error(f"Error processing exception: {e}")
        
        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _handle_threading_exception(self, args):
        """Handle threading exceptions."""
        try:
            self._process_exception(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception as e:
            logger.error(f"Error processing threading exception: {e}")
        
        # Call original handler
        if self._original_threading_excepthook:
            self._original_threading_excepthook(args)
    
    def _process_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """Process an exception and create error info."""
        if not self._active or not exc_traceback:
            return
        
        try:
            # Extract stack trace information
            stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
            
            # Find the most relevant frame (within our repo)
            relevant_frame = None
            for frame in traceback.extract_tb(exc_traceback):
                if str(Path(frame.filename).absolute()) in self._repo_files:
                    relevant_frame = frame
                    break
            
            if not relevant_frame:
                # Use the last frame if no repo frame found
                frames = traceback.extract_tb(exc_traceback)
                if frames:
                    relevant_frame = frames[-1]
            
            if not relevant_frame:
                return
            
            # Create runtime context
            runtime_context = RuntimeContext(
                exception_type=exc_type.__name__,
                stack_trace=stack_trace,
                timestamp=time.time(),
                thread_id=threading.get_ident(),
                process_id=os.getpid() if hasattr(os, 'getpid') else None
            )
            
            # Collect variable information if enabled
            if self.collect_variables and exc_traceback:
                try:
                    frame = exc_traceback.tb_frame
                    runtime_context.local_variables = self._safe_extract_variables(frame.f_locals)
                    runtime_context.global_variables = self._safe_extract_variables(frame.f_globals)
                    
                    # Extract execution path
                    execution_path = []
                    current_tb = exc_traceback
                    depth = 0
                    while current_tb and depth < self.max_stack_depth:
                        frame_info = current_tb.tb_frame
                        func_name = frame_info.f_code.co_name
                        execution_path.append(func_name)
                        current_tb = current_tb.tb_next
                        depth += 1
                    runtime_context.execution_path = execution_path
                    
                except Exception as e:
                    logger.warning(f"Failed to collect variable information: {e}")
            
            # Create error info
            error_info = RuntimeErrorInfo(
                file_path=str(Path(relevant_frame.filename).absolute()),
                line=relevant_frame.lineno - 1,  # Convert to 0-based
                character=0,  # We don't have column info from traceback
                message=str(exc_value),
                severity=DiagnosticSeverity.ERROR,
                error_type=ErrorType.RUNTIME_ERROR,
                runtime_context=runtime_context,
                fix_suggestions=self._generate_fix_suggestions(exc_type, exc_value)
            )
            
            # Add to collection
            with self._lock:
                self.errors.append(error_info)
                
                # Limit collection size
                if len(self.errors) > self.max_errors:
                    self.errors = self.errors[-self.max_errors:]
                
                # Notify handlers
                for handler in self.error_handlers:
                    try:
                        handler(error_info)
                    except Exception as e:
                        logger.error(f"Error in error handler: {e}")
        
        except Exception as e:
            logger.error(f"Failed to process exception: {e}")
    
    def _safe_extract_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extract variable information."""
        safe_vars = {}
        
        for name, value in variables.items():
            if name.startswith('__') and name.endswith('__'):
                continue  # Skip dunder variables
            
            try:
                # Convert to string safely
                str_value = str(value)
                if len(str_value) > self.variable_max_length:
                    str_value = str_value[:self.variable_max_length] + "..."
                safe_vars[name] = str_value
            except Exception:
                safe_vars[name] = "<unable to convert>"
        
        return safe_vars
    
    def _generate_fix_suggestions(self, exc_type, exc_value) -> List[str]:
        """Generate fix suggestions based on exception type."""
        suggestions = []
        
        if exc_type == NameError:
            suggestions.extend([
                "Check if the variable is defined before use",
                "Verify import statements are correct",
                "Check for typos in variable names"
            ])
        elif exc_type == AttributeError:
            suggestions.extend([
                "Check if the object is None before accessing attributes",
                "Verify the object has the expected attribute",
                "Use hasattr() to check attribute existence",
                "Use getattr() with a default value"
            ])
        elif exc_type == TypeError:
            suggestions.extend([
                "Check argument types match function expectations",
                "Verify object supports the operation being performed",
                "Check for None values where objects are expected"
            ])
        elif exc_type == IndexError:
            suggestions.extend([
                "Check list/array bounds before accessing",
                "Verify the collection is not empty",
                "Use len() to check collection size"
            ])
        elif exc_type == KeyError:
            suggestions.extend([
                "Check if key exists before accessing",
                "Use dict.get() with default value",
                "Verify dictionary structure matches expectations"
            ])
        elif exc_type == ZeroDivisionError:
            suggestions.extend([
                "Check denominator is not zero before division",
                "Add conditional logic to handle zero case",
                "Use try/except for division operations"
            ])
        elif exc_type == FileNotFoundError:
            suggestions.extend([
                "Verify file path is correct",
                "Check if file exists before opening",
                "Use absolute paths when possible"
            ])
        else:
            suggestions.append(f"Handle {exc_type.__name__} with appropriate error checking")
        
        return suggestions
    
    def get_runtime_errors(self) -> List[RuntimeErrorInfo]:
        """Get all collected runtime errors."""
        with self._lock:
            return self.errors.copy()
    
    def get_runtime_errors_for_file(self, file_path: str) -> List[RuntimeErrorInfo]:
        """Get runtime errors for a specific file."""
        file_path = str(Path(file_path).absolute())
        with self._lock:
            return [error for error in self.errors if error.file_path == file_path]
    
    def clear_runtime_errors(self) -> None:
        """Clear all collected runtime errors."""
        with self._lock:
            self.errors.clear()
    
    def add_error_handler(self, handler: Callable[[RuntimeErrorInfo], None]) -> None:
        """Add a handler for new runtime errors."""
        with self._lock:
            self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable[[RuntimeErrorInfo], None]) -> None:
        """Remove an error handler."""
        with self._lock:
            if handler in self.error_handlers:
                self.error_handlers.remove(handler)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary statistics about collected errors."""
        with self._lock:
            errors_by_type = {}
            errors_by_file = {}
            
            for error in self.errors:
                # Count by exception type
                if error.runtime_context:
                    exc_type = error.runtime_context.exception_type
                    errors_by_type[exc_type] = errors_by_type.get(exc_type, 0) + 1
                
                # Count by file
                file_name = Path(error.file_path).name
                errors_by_file[file_name] = errors_by_file.get(file_name, 0) + 1
            
            return {
                'total_errors': len(self.errors),
                'collection_active': self._active,
                'errors_by_type': errors_by_type,
                'errors_by_file': errors_by_file,
                'max_errors': self.max_errors,
                'collect_variables': self.collect_variables
            }
    
    def shutdown(self) -> None:
        """Shutdown the collector and clean up resources."""
        self.stop_collection()
        with self._lock:
            self.errors.clear()
            self.error_handlers.clear()
            self._repo_files.clear()


# Import os for process ID
import os

