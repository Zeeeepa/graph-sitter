"""
Unified Diagnostic Engine for Graph-sitter
==========================================

This module consolidates CodebaseDiagnostics, SerenaLSPBridge, and 
TransactionAwareLSPManager into a single, comprehensive diagnostic system
that provides real-time LSP integration with transaction awareness.
"""

import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Callable, Generator, TYPE_CHECKING
from weakref import WeakKeyDictionary
from dataclasses import dataclass
from enum import IntEnum

from graph_sitter.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase

logger = get_logger(__name__)

# Global registry of diagnostic engines
_diagnostic_engines: WeakKeyDictionary = WeakKeyDictionary()
_engine_lock = threading.RLock()

# LSP integration imports (optional)
try:
    from graph_sitter.extensions.lsp.protocol.lsp_types import DiagnosticSeverity, Diagnostic, Position, Range
    from graph_sitter.extensions.lsp.language_servers.base import BaseLanguageServer
    from graph_sitter.extensions.lsp.language_servers.python_server import PythonLanguageServer
    LSP_AVAILABLE = True
except ImportError:
    logger.info("LSP integration not available. Install Serena dependencies for error detection.")
    LSP_AVAILABLE = False
    
    # Fallback types
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
        code: Optional[str] = None
        source: Optional[str] = None


@dataclass
class ErrorInfo:
    """Standardized error information for graph-sitter."""
    file_path: str
    line: int
    character: int
    message: str
    severity: DiagnosticSeverity
    source: Optional[str] = None
    code: Optional[str] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    id: Optional[str] = None
    
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
    def has_quick_fix(self) -> bool:
        """Check if this error has available quick fixes."""
        # This would be determined by the LSP server
        return self.source in ['pylsp', 'pyright', 'mypy'] and self.is_error
    
    def __str__(self) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "ERROR",
            DiagnosticSeverity.WARNING: "WARNING", 
            DiagnosticSeverity.INFORMATION: "INFO",
            DiagnosticSeverity.HINT: "HINT"
        }.get(self.severity, "UNKNOWN")
        
        return f"{severity_str} {self.file_path}:{self.line}:{self.character} - {self.message}"


class UnifiedDiagnosticEngine:
    """
    Unified diagnostic engine that consolidates all diagnostic capabilities.
    
    Combines:
    - Real-time LSP integration (from SerenaLSPBridge)
    - Transaction awareness (from TransactionAwareLSPManager)  
    - Codebase-level diagnostic access (from CodebaseDiagnostics)
    """
    
    def __init__(self, codebase: "Codebase", enable_lsp: bool = True):
        self.codebase = codebase
        self.repo_path = Path(codebase.repo_path)
        self.enable_lsp = enable_lsp and LSP_AVAILABLE
        
        # Language servers
        self.language_servers: Dict[str, BaseLanguageServer] = {}
        
        # Diagnostic caching and management
        self._diagnostics_cache: List[ErrorInfo] = []
        self._file_diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self._last_refresh = 0.0
        self._refresh_interval = 5.0  # Refresh every 5 seconds
        self._lock = threading.RLock()
        self._shutdown = False
        
        # Real-time monitoring
        self._error_callbacks: List[Callable[[List[ErrorInfo]], None]] = []
        self._monitoring_active = False
        
        if self.enable_lsp:
            self._initialize_lsp_integration()
            self._hook_into_codebase()
    
    def _initialize_lsp_integration(self) -> None:
        """Initialize LSP integration with language servers."""
        try:
            # Detect and initialize language servers
            if self._has_python_files():
                self._initialize_python_server()
            
            # TODO: Add TypeScript, JavaScript, etc.
            
            if self.language_servers:
                logger.info(f"Diagnostic engine initialized for {self.repo_path} with {len(self.language_servers)} servers")
                self._refresh_diagnostics_async()
            else:
                logger.warning(f"No language servers available for {self.repo_path}")
                self.enable_lsp = False
                
        except Exception as e:
            logger.error(f"Failed to initialize LSP integration: {e}")
            self.enable_lsp = False
    
    def _has_python_files(self) -> bool:
        """Check if repository contains Python files."""
        for py_file in self.repo_path.rglob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):
                return True
        return False
    
    def _initialize_python_server(self) -> None:
        """Initialize Python language server."""
        try:
            python_server = PythonLanguageServer(str(self.repo_path))
            if python_server.initialize():
                self.language_servers["python"] = python_server
                logger.info("Python language server initialized")
            else:
                logger.warning("Failed to initialize Python language server")
        except Exception as e:
            logger.error(f"Error initializing Python server: {e}")
    
    def _hook_into_codebase(self) -> None:
        """Hook into the codebase's apply_diffs method for transaction awareness."""
        try:
            original_apply_diffs = self.codebase.ctx.apply_diffs
            
            def enhanced_apply_diffs(diffs):
                # Call original method
                result = original_apply_diffs(diffs)
                
                # Update diagnostic context
                self._handle_codebase_changes(diffs)
                
                return result
            
            # Replace the method
            self.codebase.ctx.apply_diffs = enhanced_apply_diffs
            
            logger.info(f"Transaction-aware diagnostics enabled for {self.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to hook into codebase: {e}")
    
    def _handle_codebase_changes(self, diffs) -> None:
        """Handle codebase changes for real-time diagnostic updates."""
        try:
            # Force refresh diagnostics after changes
            self._refresh_diagnostics_async()
            
            # Notify callbacks if monitoring is active
            if self._monitoring_active and self._error_callbacks:
                # Get current diagnostics and notify callbacks
                current_diagnostics = self._get_current_diagnostics()
                for callback in self._error_callbacks:
                    try:
                        callback(current_diagnostics)
                    except Exception as e:
                        logger.error(f"Error in diagnostic callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error handling codebase changes: {e}")
    
    def _refresh_diagnostics_async(self) -> None:
        """Refresh diagnostics in background thread."""
        def refresh_worker():
            try:
                if not self._shutdown:
                    diagnostics = self._collect_diagnostics_from_servers()
                    with self._lock:
                        self._diagnostics_cache = diagnostics
                        self._last_refresh = time.time()
                        
                        # Update file-specific cache
                        self._file_diagnostics_cache.clear()
                        for diag in diagnostics:
                            if diag.file_path not in self._file_diagnostics_cache:
                                self._file_diagnostics_cache[diag.file_path] = []
                            self._file_diagnostics_cache[diag.file_path].append(diag)
                    
                    logger.debug(f"Refreshed {len(diagnostics)} diagnostics")
            except Exception as e:
                logger.error(f"Error refreshing diagnostics: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=refresh_worker, daemon=True)
        thread.start()
    
    def _collect_diagnostics_from_servers(self) -> List[ErrorInfo]:
        """Collect diagnostics from all language servers."""
        all_diagnostics = []
        
        for server_name, server in self.language_servers.items():
            try:
                if server.is_running:
                    # Get diagnostics from server
                    server_diagnostics = server.get_diagnostics()
                    
                    # Convert to ErrorInfo objects
                    for diag in server_diagnostics:
                        error_info = self._convert_diagnostic_to_error_info(diag, server_name)
                        if error_info:
                            all_diagnostics.append(error_info)
                            
            except Exception as e:
                logger.error(f"Error collecting diagnostics from {server_name}: {e}")
        
        return all_diagnostics
    
    def _convert_diagnostic_to_error_info(self, diagnostic: Diagnostic, source: str) -> Optional[ErrorInfo]:
        """Convert LSP Diagnostic to ErrorInfo."""
        try:
            # Generate unique ID for the error
            error_id = f"{source}_{hash(f'{diagnostic.range.start.line}_{diagnostic.range.start.character}_{diagnostic.message}')}"
            
            return ErrorInfo(
                id=error_id,
                file_path=getattr(diagnostic, 'file_path', 'unknown'),
                line=diagnostic.range.start.line,
                character=diagnostic.range.start.character,
                message=diagnostic.message,
                severity=diagnostic.severity or DiagnosticSeverity.ERROR,
                source=source,
                code=str(diagnostic.code) if diagnostic.code else None,
                end_line=diagnostic.range.end.line,
                end_character=diagnostic.range.end.character
            )
        except Exception as e:
            logger.error(f"Error converting diagnostic: {e}")
            return None
    
    def _should_refresh(self) -> bool:
        """Check if diagnostics should be refreshed."""
        return (time.time() - self._last_refresh) > self._refresh_interval
    
    def _get_current_diagnostics(self) -> List[ErrorInfo]:
        """Get current diagnostics with refresh if needed."""
        if not self.enable_lsp:
            return []
        
        if self._should_refresh():
            self._refresh_diagnostics_async()
        
        with self._lock:
            return self._diagnostics_cache.copy()
    
    # Public API - Core Error Retrieval
    
    @property
    def errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase."""
        diagnostics = self._get_current_diagnostics()
        return [d for d in diagnostics if d.is_error]
    
    @property
    def warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        diagnostics = self._get_current_diagnostics()
        return [d for d in diagnostics if d.is_warning]
    
    @property
    def hints(self) -> List[ErrorInfo]:
        """Get all hints in the codebase."""
        diagnostics = self._get_current_diagnostics()
        return [d for d in diagnostics if d.is_hint]
    
    @property
    def diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) in the codebase."""
        return self._get_current_diagnostics()
    
    def get_errors_by_file(self, file_path: str) -> List[ErrorInfo]:
        """Get errors in a specific file."""
        if not self.enable_lsp:
            return []
        
        if self._should_refresh():
            self._refresh_diagnostics_async()
        
        with self._lock:
            return self._file_diagnostics_cache.get(file_path, [])
    
    def get_errors_by_severity(self, severity: str) -> List[ErrorInfo]:
        """Get errors by severity level."""
        severity_map = {
            "ERROR": DiagnosticSeverity.ERROR,
            "WARNING": DiagnosticSeverity.WARNING,
            "INFO": DiagnosticSeverity.INFORMATION,
            "HINT": DiagnosticSeverity.HINT
        }
        
        target_severity = severity_map.get(severity.upper())
        if not target_severity:
            return []
        
        diagnostics = self._get_current_diagnostics()
        return [d for d in diagnostics if d.severity == target_severity]
    
    def get_errors_by_type(self, error_type: str) -> List[ErrorInfo]:
        """Get errors by type (syntax, semantic, lint)."""
        diagnostics = self._get_current_diagnostics()
        
        # Filter by source/type
        type_sources = {
            "syntax": ["pylsp", "pyright"],
            "semantic": ["mypy", "pyright"],
            "lint": ["flake8", "pylint", "ruff"]
        }
        
        sources = type_sources.get(error_type.lower(), [])
        if not sources:
            return diagnostics  # Return all if type not recognized
        
        return [d for d in diagnostics if d.source in sources]
    
    def get_recent_errors(self, since_timestamp: float) -> List[ErrorInfo]:
        """Get recent errors since a timestamp."""
        # For now, return current errors (would need timestamp tracking for full implementation)
        if time.time() - since_timestamp < self._refresh_interval * 2:
            return self._get_current_diagnostics()
        return []
    
    # Real-time Monitoring
    
    def watch_errors(self, callback: Callable[[List[ErrorInfo]], None]) -> bool:
        """Set up real-time error monitoring."""
        try:
            if callback not in self._error_callbacks:
                self._error_callbacks.append(callback)
            
            self._monitoring_active = True
            
            # Send initial callback with current diagnostics
            current_diagnostics = self._get_current_diagnostics()
            callback(current_diagnostics)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up error monitoring: {e}")
            return False
    
    def error_stream(self) -> Generator[List[ErrorInfo], None, None]:
        """Get a stream of error updates."""
        last_count = -1
        
        while not self._shutdown:
            try:
                current_diagnostics = self._get_current_diagnostics()
                
                # Yield if count changed
                if len(current_diagnostics) != last_count:
                    last_count = len(current_diagnostics)
                    yield current_diagnostics
                
                # Break if no errors
                if len(current_diagnostics) == 0:
                    break
                
                time.sleep(self._refresh_interval)
                
            except Exception as e:
                logger.error(f"Error in diagnostic stream: {e}")
                break
    
    def refresh_errors(self) -> bool:
        """Force refresh of error detection."""
        try:
            self._refresh_diagnostics_async()
            return True
        except Exception as e:
            logger.error(f"Error forcing refresh: {e}")
            return False
    
    # Error Context and Analysis
    
    def get_full_error_context(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive context for a specific error."""
        diagnostics = self._get_current_diagnostics()
        
        for error in diagnostics:
            if error.id == error_id:
                # Get file content around the error
                try:
                    file_path = Path(error.file_path)
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        # Get context lines
                        start_line = max(0, error.line - 3)
                        end_line = min(len(lines), error.line + 4)
                        
                        context_lines = {
                            "before": lines[start_line:error.line],
                            "error_line": lines[error.line] if error.line < len(lines) else "",
                            "after": lines[error.line + 1:end_line]
                        }
                        
                        return {
                            "error": error,
                            "file_path": error.file_path,
                            "line": error.line,
                            "character": error.character,
                            "message": error.message,
                            "severity": error.severity,
                            "source": error.source,
                            "code": error.code,
                            "context_lines": context_lines
                        }
                        
                except Exception as e:
                    logger.error(f"Error getting file context: {e}")
                
                # Return basic context if file reading fails
                return {
                    "error": error,
                    "file_path": error.file_path,
                    "line": error.line,
                    "character": error.character,
                    "message": error.message,
                    "severity": error.severity,
                    "source": error.source,
                    "code": error.code
                }
        
        return None
    
    def get_error_suggestions(self, error_id: str) -> List[str]:
        """Get fix suggestions for an error."""
        context = self.get_full_error_context(error_id)
        if not context:
            return []
        
        error = context["error"]
        suggestions = []
        
        # Generate suggestions based on error type and message
        message_lower = error.message.lower()
        
        if "undefined" in message_lower or "not defined" in message_lower:
            suggestions.append("Check if the variable or function is properly imported")
            suggestions.append("Verify the spelling of the identifier")
            suggestions.append("Ensure the variable is defined before use")
        
        elif "syntax error" in message_lower:
            suggestions.append("Check for missing parentheses, brackets, or quotes")
            suggestions.append("Verify proper indentation")
            suggestions.append("Look for missing colons after control statements")
        
        elif "type" in message_lower and "error" in message_lower:
            suggestions.append("Check the types of variables and function arguments")
            suggestions.append("Add type hints for better type checking")
            suggestions.append("Verify the return type matches the expected type")
        
        elif "import" in message_lower:
            suggestions.append("Check if the module is installed")
            suggestions.append("Verify the import path is correct")
            suggestions.append("Ensure the module is in the Python path")
        
        return suggestions
    
    def get_error_related_symbols(self, error_id: str) -> List[str]:
        """Get symbols related to the error."""
        context = self.get_full_error_context(error_id)
        if not context:
            return []
        
        # Extract symbols from error message and context
        error = context["error"]
        symbols = []
        
        # Simple symbol extraction from error message
        import re
        
        # Look for quoted identifiers
        quoted_symbols = re.findall(r"'([^']+)'", error.message)
        symbols.extend(quoted_symbols)
        
        # Look for common Python identifiers
        identifier_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        identifiers = re.findall(identifier_pattern, error.message)
        
        # Filter out common words
        common_words = {'error', 'undefined', 'not', 'found', 'type', 'syntax', 'import', 'module'}
        symbols.extend([id for id in identifiers if id.lower() not in common_words])
        
        return list(set(symbols))  # Remove duplicates
    
    def get_error_impact_analysis(self, error_id: str) -> Dict[str, Any]:
        """Get impact analysis of the error."""
        context = self.get_full_error_context(error_id)
        if not context:
            return {}
        
        error = context["error"]
        
        # Determine impact based on severity and type
        severity_impact = "High" if error.is_error else "Medium" if error.is_warning else "Low"
        
        # Determine fix complexity
        message_lower = error.message.lower()
        if any(keyword in message_lower for keyword in ["syntax", "missing", "typo"]):
            fix_complexity = "Simple"
        elif any(keyword in message_lower for keyword in ["type", "import", "undefined"]):
            fix_complexity = "Medium"
        else:
            fix_complexity = "Complex"
        
        # Check for potential cascade effects
        potential_cascade = error.is_error and any(
            keyword in message_lower for keyword in ["import", "undefined", "not found"]
        )
        
        return {
            "severity_impact": severity_impact,
            "affected_file": error.file_path,
            "potential_cascade": potential_cascade,
            "fix_complexity": fix_complexity
        }
    
    # Cleanup
    
    def shutdown(self) -> None:
        """Shutdown the diagnostic engine."""
        self._shutdown = True
        self._monitoring_active = False
        self._error_callbacks.clear()
        
        # Shutdown language servers
        for server in self.language_servers.values():
            try:
                if hasattr(server, 'shutdown'):
                    server.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down language server: {e}")
        
        logger.info("Diagnostic engine shut down")


def get_diagnostic_engine(codebase: "Codebase", enable_lsp: bool = True) -> UnifiedDiagnosticEngine:
    """Get or create a diagnostic engine for the codebase."""
    with _engine_lock:
        if codebase not in _diagnostic_engines:
            _diagnostic_engines[codebase] = UnifiedDiagnosticEngine(codebase, enable_lsp)
        return _diagnostic_engines[codebase]
