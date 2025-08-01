"""
Unified LSP Error Manager

This module consolidates all LSP error retrieval logic into a single,
efficient system that handles all LSP communication, diagnostic collection,
and error transformation into standardized formats.
"""

import asyncio
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Any, Callable
from collections import defaultdict
import weakref

from graph_sitter.shared.logging.get_logger import get_logger
from .unified_error_models import (
    UnifiedError, ErrorLocation, ErrorSeverity, ErrorCategory,
    ErrorFix, FixConfidence, RelatedSymbol, ErrorSummary
)

# Import LSP components
try:
    from ..lsp.serena_bridge import SerenaLSPBridge, ErrorInfo
    from ..lsp.protocol.lsp_types import DiagnosticSeverity, Diagnostic
    from ..lsp.language_servers.base import BaseLanguageServer
    LSP_AVAILABLE = True
except ImportError:
    logger = get_logger(__name__)
    logger.warning("LSP components not available")
    LSP_AVAILABLE = False
    # Fallback classes
    class SerenaLSPBridge:
        def __init__(self, *args, **kwargs): pass
    class ErrorInfo:
        def __init__(self, **kwargs): pass
    class DiagnosticSeverity:
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4

logger = get_logger(__name__)


class LSPErrorCache:
    """Intelligent caching system for LSP diagnostics."""
    
    def __init__(self, ttl: float = 30.0):
        self.ttl = ttl  # Time to live in seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._file_timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, file_path: str) -> Optional[List[UnifiedError]]:
        """Get cached errors for a file."""
        with self._lock:
            if file_path not in self._cache:
                return None
            
            cache_entry = self._cache[file_path]
            if time.time() - cache_entry['timestamp'] > self.ttl:
                # Cache expired
                del self._cache[file_path]
                return None
            
            return cache_entry['errors']
    
    def set(self, file_path: str, errors: List[UnifiedError]) -> None:
        """Cache errors for a file."""
        with self._lock:
            self._cache[file_path] = {
                'errors': errors,
                'timestamp': time.time()
            }
    
    def invalidate(self, file_path: str) -> None:
        """Invalidate cache for a specific file."""
        with self._lock:
            self._cache.pop(file_path, None)
    
    def invalidate_all(self) -> None:
        """Invalidate entire cache."""
        with self._lock:
            self._cache.clear()
    
    def is_file_modified(self, file_path: str) -> bool:
        """Check if file has been modified since last cache."""
        try:
            current_mtime = Path(file_path).stat().st_mtime
            last_mtime = self._file_timestamps.get(file_path, 0)
            
            if current_mtime > last_mtime:
                self._file_timestamps[file_path] = current_mtime
                return True
            return False
        except (OSError, IOError):
            return True  # Assume modified if we can't check


class UnifiedLSPErrorManager:
    """
    Unified manager for all LSP error operations.
    
    This class consolidates error retrieval from multiple LSP servers,
    provides caching and performance optimizations, and transforms
    raw LSP diagnostics into unified error objects.
    """
    
    def __init__(self, repo_path: str, enable_background_refresh: bool = True):
        self.repo_path = Path(repo_path)
        self.enable_background_refresh = enable_background_refresh
        
        # LSP integration
        self._lsp_bridge: Optional[SerenaLSPBridge] = None
        self._is_initialized = False
        
        # Caching and performance
        self._cache = LSPErrorCache()
        self._error_registry: Dict[str, UnifiedError] = {}
        self._file_errors: Dict[str, List[str]] = defaultdict(list)  # file -> error_ids
        
        # Background processing
        self._background_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._refresh_interval = 10.0  # seconds
        
        # Callbacks for real-time updates
        self._error_callbacks: List[Callable[[List[UnifiedError]], None]] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the LSP error manager."""
        if not LSP_AVAILABLE:
            logger.warning("LSP not available, error manager will have limited functionality")
            return
        
        try:
            self._lsp_bridge = SerenaLSPBridge(str(self.repo_path))
            self._is_initialized = self._lsp_bridge.is_initialized
            
            if self._is_initialized:
                logger.info(f"LSP error manager initialized for {self.repo_path}")
                
                if self.enable_background_refresh:
                    self._start_background_refresh()
            else:
                logger.warning(f"LSP bridge failed to initialize for {self.repo_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize LSP error manager: {e}")
            self._is_initialized = False
    
    def _start_background_refresh(self) -> None:
        """Start background thread for periodic error refresh."""
        if self._background_thread and self._background_thread.is_alive():
            return
        
        def refresh_worker():
            while not self._shutdown_event.wait(self._refresh_interval):
                try:
                    self._refresh_all_errors_background()
                except Exception as e:
                    logger.error(f"Error in background refresh: {e}")
        
        self._background_thread = threading.Thread(target=refresh_worker, daemon=True)
        self._background_thread.start()
        logger.debug("Background error refresh started")
    
    def _refresh_all_errors_background(self) -> None:
        """Refresh all errors in background thread."""
        if not self._is_initialized:
            return
        
        try:
            # Get all Python files that might have changed
            python_files = list(self.repo_path.rglob("*.py"))
            modified_files = [
                str(f.relative_to(self.repo_path))
                for f in python_files
                if self._cache.is_file_modified(str(f))
            ]
            
            if modified_files:
                logger.debug(f"Refreshing errors for {len(modified_files)} modified files")
                
                # Refresh errors for modified files
                for file_path in modified_files:
                    self._cache.invalidate(file_path)
                    self._get_file_errors_internal(file_path, use_cache=False)
                
                # Notify callbacks
                all_errors = self.get_all_errors()
                for callback in self._error_callbacks:
                    try:
                        callback(all_errors)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error refreshing background errors: {e}")
    
    def add_error_callback(self, callback: Callable[[List[UnifiedError]], None]) -> None:
        """Add callback for real-time error updates."""
        self._error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[List[UnifiedError]], None]) -> None:
        """Remove error callback."""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)
    
    def get_all_errors(self, include_warnings: bool = True, include_hints: bool = False) -> List[UnifiedError]:
        """
        Get all errors in the codebase.
        
        Args:
            include_warnings: Include warnings in results
            include_hints: Include hints/info in results
            
        Returns:
            List of unified errors
        """
        if not self._is_initialized:
            return []
        
        all_errors = []
        
        # Get all Python files
        python_files = [
            str(f.relative_to(self.repo_path))
            for f in self.repo_path.rglob("*.py")
            if not any(part.startswith('.') for part in f.parts)
            and not any(part in ['__pycache__', 'node_modules', 'venv', 'env'] for part in f.parts)
        ]
        
        # Collect errors from all files
        for file_path in python_files:
            file_errors = self._get_file_errors_internal(file_path)
            
            for error in file_errors:
                # Filter by severity
                if error.severity == ErrorSeverity.ERROR:
                    all_errors.append(error)
                elif error.severity == ErrorSeverity.WARNING and include_warnings:
                    all_errors.append(error)
                elif error.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT] and include_hints:
                    all_errors.append(error)
        
        return all_errors
    
    def get_file_errors(self, file_path: str) -> List[UnifiedError]:
        """
        Get errors for a specific file.
        
        Args:
            file_path: Path to the file (relative to repo root)
            
        Returns:
            List of errors in the file
        """
        return self._get_file_errors_internal(file_path)
    
    def _get_file_errors_internal(self, file_path: str, use_cache: bool = True) -> List[UnifiedError]:
        """Internal method to get file errors with caching."""
        if not self._is_initialized:
            return []
        
        # Check cache first
        if use_cache:
            cached_errors = self._cache.get(file_path)
            if cached_errors is not None:
                return cached_errors
        
        try:
            # Get diagnostics from LSP bridge
            raw_diagnostics = self._lsp_bridge.get_file_diagnostics(file_path)
            
            # Transform to unified errors
            unified_errors = []
            for diag in raw_diagnostics:
                unified_error = self._transform_diagnostic_to_error(diag, file_path)
                if unified_error:
                    unified_errors.append(unified_error)
                    
                    # Update registry
                    with self._lock:
                        self._error_registry[unified_error.id] = unified_error
                        self._file_errors[file_path].append(unified_error.id)
            
            # Cache the results
            self._cache.set(file_path, unified_errors)
            
            return unified_errors
            
        except Exception as e:
            logger.error(f"Error getting diagnostics for {file_path}: {e}")
            return []
    
    def _transform_diagnostic_to_error(self, diagnostic: Any, file_path: str) -> Optional[UnifiedError]:
        """Transform LSP diagnostic to unified error."""
        try:
            # Handle different diagnostic formats
            if hasattr(diagnostic, 'range'):
                # LSP Diagnostic object
                location = ErrorLocation(
                    file_path=file_path,
                    line=diagnostic.range.start.line + 1,  # Convert to 1-based
                    character=diagnostic.range.start.character,
                    end_line=diagnostic.range.end.line + 1,
                    end_character=diagnostic.range.end.character
                )
                message = diagnostic.message
                severity = self._convert_lsp_severity(diagnostic.severity)
                source = diagnostic.source or "lsp"
                code = diagnostic.code
                
            elif isinstance(diagnostic, ErrorInfo):
                # ErrorInfo object
                location = ErrorLocation(
                    file_path=file_path,
                    line=diagnostic.line,
                    character=diagnostic.character,
                    end_line=diagnostic.end_line,
                    end_character=diagnostic.end_character
                )
                message = diagnostic.message
                severity = self._convert_lsp_severity(diagnostic.severity)
                source = diagnostic.source or "lsp"
                code = diagnostic.code
                
            elif isinstance(diagnostic, dict):
                # Dictionary format
                range_info = diagnostic.get('range', {})
                start_pos = range_info.get('start', {})
                end_pos = range_info.get('end', {})
                
                location = ErrorLocation(
                    file_path=file_path,
                    line=start_pos.get('line', 0) + 1,  # Convert to 1-based
                    character=start_pos.get('character', 0),
                    end_line=end_pos.get('line', 0) + 1 if end_pos else None,
                    end_character=end_pos.get('character', 0) if end_pos else None
                )
                message = diagnostic.get('message', 'Unknown error')
                severity = self._convert_lsp_severity(diagnostic.get('severity', 1))
                source = diagnostic.get('source', 'lsp')
                code = diagnostic.get('code')
                
            else:
                logger.warning(f"Unknown diagnostic format: {type(diagnostic)}")
                return None
            
            # Create unified error
            error = UnifiedError(
                id="",  # Will be generated in __post_init__
                message=message,
                severity=severity,
                category=ErrorCategory.OTHER,  # Will be auto-categorized
                location=location,
                source=source,
                code=str(code) if code else None
            )
            
            # Add context lines
            error.context_lines = self._get_context_lines(file_path, location.line)
            
            # Generate potential fixes
            error.fixes = self._generate_fixes(error)
            
            return error
            
        except Exception as e:
            logger.error(f"Error transforming diagnostic: {e}")
            return None
    
    def _convert_lsp_severity(self, lsp_severity: Any) -> ErrorSeverity:
        """Convert LSP severity to unified severity."""
        if isinstance(lsp_severity, int):
            severity_map = {
                1: ErrorSeverity.ERROR,
                2: ErrorSeverity.WARNING,
                3: ErrorSeverity.INFO,
                4: ErrorSeverity.HINT
            }
            return severity_map.get(lsp_severity, ErrorSeverity.ERROR)
        elif hasattr(lsp_severity, 'value'):
            return ErrorSeverity(lsp_severity.value)
        else:
            return ErrorSeverity.ERROR
    
    def _get_context_lines(self, file_path: str, line_number: int, context_size: int = 3) -> List[str]:
        """Get context lines around an error."""
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                return []
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_size - 1)
            end_line = min(len(lines), line_number + context_size)
            
            return [line.rstrip() for line in lines[start_line:end_line]]
            
        except Exception as e:
            logger.error(f"Error getting context lines for {file_path}:{line_number}: {e}")
            return []
    
    def _generate_fixes(self, error: UnifiedError) -> List[ErrorFix]:
        """Generate potential fixes for an error."""
        fixes = []
        
        # Basic fix patterns based on error message
        message_lower = error.message.lower()
        
        if "unused import" in message_lower:
            fixes.append(ErrorFix(
                id=f"remove_unused_import_{error.id}",
                title="Remove unused import",
                description="Remove the unused import statement",
                confidence=FixConfidence.HIGH,
                changes=[{
                    'type': 'delete_line',
                    'file': error.location.file_path,
                    'line': error.location.line
                }]
            ))
        
        elif "undefined name" in message_lower or "not defined" in message_lower:
            # Extract the undefined name
            import re
            match = re.search(r"'([^']+)'", error.message)
            if match:
                undefined_name = match.group(1)
                fixes.append(ErrorFix(
                    id=f"add_import_{error.id}",
                    title=f"Add import for '{undefined_name}'",
                    description=f"Add an import statement for '{undefined_name}'",
                    confidence=FixConfidence.MEDIUM,
                    requires_user_input=True,
                    changes=[{
                        'type': 'add_import',
                        'file': error.location.file_path,
                        'symbol': undefined_name
                    }]
                ))
        
        elif "missing whitespace" in message_lower or "expected 2 blank lines" in message_lower:
            fixes.append(ErrorFix(
                id=f"fix_whitespace_{error.id}",
                title="Fix whitespace",
                description="Fix whitespace formatting issue",
                confidence=FixConfidence.HIGH,
                changes=[{
                    'type': 'fix_whitespace',
                    'file': error.location.file_path,
                    'line': error.location.line
                }]
            ))
        
        return fixes
    
    def get_error_summary(self) -> ErrorSummary:
        """Get summary of all errors in the codebase."""
        all_errors = self.get_all_errors(include_warnings=True, include_hints=True)
        
        summary = ErrorSummary()
        
        # Count by severity
        for error in all_errors:
            if error.severity == ErrorSeverity.ERROR:
                summary.total_errors += 1
            elif error.severity == ErrorSeverity.WARNING:
                summary.total_warnings += 1
            elif error.severity == ErrorSeverity.INFO:
                summary.total_info += 1
            elif error.severity == ErrorSeverity.HINT:
                summary.total_hints += 1
        
        # Count by category
        for error in all_errors:
            category = error.category.value
            summary.by_category[category] = summary.by_category.get(category, 0) + 1
        
        # Count by file
        for error in all_errors:
            file_path = error.location.file_path
            summary.by_file[file_path] = summary.by_file.get(file_path, 0) + 1
        
        # Count by source
        for error in all_errors:
            source = error.source
            summary.by_source[source] = summary.by_source.get(source, 0) + 1
        
        # Count fixable errors
        for error in all_errors:
            if error.auto_fixable:
                summary.auto_fixable += 1
            elif error.is_fixable:
                summary.manually_fixable += 1
            else:
                summary.unfixable += 1
        
        # Find most common errors
        error_messages = defaultdict(int)
        for error in all_errors:
            # Normalize message for grouping
            normalized_msg = error.message.split(':')[0].strip()
            error_messages[normalized_msg] += 1
        
        summary.most_common_errors = [
            {'message': msg, 'count': count}
            for msg, count in sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Find error hotspots
        summary.error_hotspots = [
            {'file': file_path, 'error_count': count}
            for file_path, count in sorted(summary.by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return summary
    
    def get_error_by_id(self, error_id: str) -> Optional[UnifiedError]:
        """Get a specific error by ID."""
        with self._lock:
            return self._error_registry.get(error_id)
    
    def refresh_errors(self, file_path: Optional[str] = None) -> None:
        """
        Refresh error information.
        
        Args:
            file_path: Specific file to refresh, or None for all files
        """
        if file_path:
            self._cache.invalidate(file_path)
            self._get_file_errors_internal(file_path, use_cache=False)
        else:
            self._cache.invalidate_all()
            with self._lock:
                self._error_registry.clear()
                self._file_errors.clear()
    
    def shutdown(self) -> None:
        """Shutdown the error manager."""
        self._shutdown_event.set()
        
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=5.0)
        
        if self._lsp_bridge:
            try:
                self._lsp_bridge.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down LSP bridge: {e}")
        
        logger.info("LSP error manager shutdown complete")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except Exception:
            pass

