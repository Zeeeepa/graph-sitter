"""
Always-Available LSP Manager

This module provides a centralized LSP manager that ensures LSP functionality
is always available with lazy loading and efficient caching.
"""

import threading
import time
import weakref
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger
from .lsp_types import (
    ErrorInfo, ErrorCollection, ErrorSummary, ErrorContext, QuickFix,
    CompletionItem, HoverInfo, SignatureHelp, SymbolInfo, LSPCapabilities,
    LSPStatus, HealthCheck, ErrorSeverity, ErrorType, Position, Range,
    ErrorCallback
)
from .unified_diagnostics import UnifiedDiagnosticCollector

logger = get_logger(__name__)

# Global registry of LSP managers (one per codebase)
_lsp_managers: Dict[str, 'LSPManager'] = {}
_manager_lock = threading.RLock()


class LSPManager:
    """
    Centralized LSP manager that ensures LSP is always available
    with lazy loading and efficient caching.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self._initialized = False
        self._initializing = False
        self._lock = threading.RLock()
        self._shutdown = False
        
        # Lazy-loaded components
        self._serena_bridge = None
        self._transaction_manager = None
        self._unified_diagnostics: Optional[UnifiedDiagnosticCollector] = None
        
        # Caching
        self._error_cache: Optional[ErrorCollection] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)  # 30 second cache
        
        # Real-time monitoring
        self._error_callbacks: Set[ErrorCallback] = set()
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        
        # Performance metrics
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(f"LSP Manager created for {self.repo_path}")
    
    def _ensure_initialized(self) -> bool:
        """Ensure LSP components are initialized (lazy loading)."""
        if self._initialized:
            return True
        
        if self._shutdown:
            return False
        
        with self._lock:
            if self._initialized:
                return True
            
            if self._initializing:
                # Wait for initialization to complete
                while self._initializing and not self._shutdown:
                    time.sleep(0.1)
                return self._initialized
            
            self._initializing = True
            
            try:
                logger.info(f"Initializing LSP components for {self.repo_path}")
                
                # Import and initialize Serena bridge
                from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
                self._serena_bridge = SerenaLSPBridge(str(self.repo_path))
                
                # Import and initialize transaction manager
                from graph_sitter.extensions.lsp.transaction_manager import TransactionAwareLSPManager
                self._transaction_manager = TransactionAwareLSPManager(str(self.repo_path))
                
                # Initialize unified diagnostic collector
                # Note: We need a codebase object for this, so we'll initialize it lazily when needed
                
                self._initialized = True
                logger.info(f"LSP components initialized successfully for {self.repo_path}")
                
                # Start monitoring if there are callbacks
                if self._error_callbacks and not self._monitoring_active:
                    self._start_monitoring()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize LSP components: {e}")
                self._initialized = False
                return False
            finally:
                self._initializing = False
    
    def _ensure_unified_diagnostics(self, codebase) -> bool:
        """Ensure unified diagnostics collector is initialized."""
        if self._unified_diagnostics is not None:
            return True
        
        if not self._ensure_initialized():
            return False
        
        try:
            self._unified_diagnostics = UnifiedDiagnosticCollector(
                codebase=codebase,
                enable_lsp=True,
                enable_transaction_awareness=True
            )
            logger.info("Unified diagnostic collector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize unified diagnostics: {e}")
            return False
    
    def _is_cache_valid(self) -> bool:
        """Check if the current cache is still valid."""
        if self._error_cache is None or self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    def _update_cache(self, errors: ErrorCollection) -> None:
        """Update the error cache."""
        self._error_cache = errors
        self._cache_timestamp = datetime.now()
    
    def _get_cached_errors(self) -> Optional[ErrorCollection]:
        """Get cached errors if valid."""
        if self._is_cache_valid():
            self._cache_hits += 1
            return self._error_cache
        self._cache_misses += 1
        return None
    
    # Core Error Retrieval Methods
    
    def get_all_errors(self, codebase=None) -> ErrorCollection:
        """Get all errors in the codebase."""
        self._request_count += 1
        
        # Check cache first
        cached = self._get_cached_errors()
        if cached is not None:
            return cached
        
        if not self._ensure_initialized():
            return ErrorCollection(errors=[], total_count=0, error_count=0, warning_count=0, info_count=0, hint_count=0, files_with_errors=0)
        
        try:
            # Use unified diagnostics if available and codebase is provided
            if codebase and self._ensure_unified_diagnostics(codebase):
                error_collection = self._unified_diagnostics.get_all_diagnostics()
                self._update_cache(error_collection)
                return error_collection
            
            # Fallback to Serena bridge
            raw_errors = self._serena_bridge.get_all_diagnostics()
            errors = self._convert_raw_errors(raw_errors)
            
            # Update cache
            error_collection = ErrorCollection(
                errors=errors, 
                total_count=len(errors),
                error_count=sum(1 for e in errors if e.severity == ErrorSeverity.ERROR),
                warning_count=sum(1 for e in errors if e.severity == ErrorSeverity.WARNING),
                info_count=sum(1 for e in errors if e.severity == ErrorSeverity.INFO),
                hint_count=sum(1 for e in errors if e.severity == ErrorSeverity.HINT),
                files_with_errors=len(set(e.file_path for e in errors))
            )
            self._update_cache(error_collection)
            
            return error_collection
            
        except Exception as e:
            logger.error(f"Error retrieving all errors: {e}")
            return ErrorCollection(errors=[], total_count=0, error_count=0, warning_count=0, info_count=0, hint_count=0, files_with_errors=0)
    
    def get_errors_by_file(self, file_path: str) -> ErrorCollection:
        """Get errors for a specific file."""
        all_errors = self.get_all_errors()
        return all_errors.filter_by_file(file_path)
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> ErrorCollection:
        """Get errors filtered by severity."""
        all_errors = self.get_all_errors()
        return all_errors.filter_by_severity(severity)
    
    def get_errors_by_type(self, error_type: ErrorType) -> ErrorCollection:
        """Get errors filtered by type."""
        all_errors = self.get_all_errors()
        return all_errors.filter_by_type(error_type)
    
    def get_recent_errors(self, since_timestamp: datetime) -> ErrorCollection:
        """Get errors since a specific timestamp."""
        all_errors = self.get_all_errors()
        recent = [e for e in all_errors.errors if e.timestamp >= since_timestamp]
        return ErrorCollection(errors=recent, total_count=len(recent))
    
    def get_full_error_context(self, error_id: str) -> Optional[ErrorContext]:
        """Get full context for a specific error."""
        if not self._ensure_initialized():
            return None
        
        try:
            # Find the error
            all_errors = self.get_all_errors()
            error = next((e for e in all_errors.errors if e.id == error_id), None)
            if not error:
                return None
            
            # Get surrounding code context
            surrounding_code = self._get_surrounding_code(error.file_path, error.range)
            
            # Get related errors
            related_errors = self._find_related_errors(error)
            
            # Get symbol context
            symbol_context = self._get_symbol_context(error)
            
            # Get fix suggestions
            fix_suggestions = self._get_fix_suggestions(error)
            
            # Get impact analysis
            impact_analysis = self._analyze_error_impact(error)
            
            return ErrorContext(
                error=error,
                surrounding_code=surrounding_code,
                related_errors=related_errors,
                symbol_context=symbol_context,
                fix_suggestions=fix_suggestions,
                impact_analysis=impact_analysis
            )
            
        except Exception as e:
            logger.error(f"Error getting full context for {error_id}: {e}")
            return None
    
    # Error Analytics Methods
    
    def get_error_summary(self) -> ErrorSummary:
        """Get summary statistics of all errors."""
        all_errors = self.get_all_errors()
        
        # Calculate file count with errors
        files_with_errors = len(set(e.file_path for e in all_errors.errors))
        
        # Calculate most common error types
        type_counts = defaultdict(int)
        for error in all_errors.errors:
            type_counts[error.error_type.value] += 1
        
        most_common_types = [
            {"type": error_type, "count": count}
            for error_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Error distribution by severity
        error_distribution = {
            "error": all_errors.error_count,
            "warning": all_errors.warning_count,
            "info": all_errors.info_count,
            "hint": all_errors.hint_count
        }
        
        return ErrorSummary(
            total_errors=all_errors.total_count,
            error_count=all_errors.error_count,
            warning_count=all_errors.warning_count,
            info_count=all_errors.info_count,
            hint_count=all_errors.hint_count,
            files_with_errors=files_with_errors,
            most_common_error_types=most_common_types,
            error_distribution=error_distribution
        )
    
    def get_error_hotspots(self) -> List[Dict[str, Any]]:
        """Get files/areas with the most errors."""
        all_errors = self.get_all_errors()
        
        file_counts = defaultdict(int)
        for error in all_errors.errors:
            file_counts[error.file_path] += 1
        
        hotspots = [
            {"file_path": file_path, "error_count": count}
            for file_path, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return hotspots
    
    # Real-time Monitoring
    
    def watch_errors(self, callback: ErrorCallback) -> None:
        """Register a callback for real-time error monitoring."""
        self._error_callbacks.add(callback)
        
        if not self._monitoring_active:
            self._start_monitoring()
    
    def unwatch_errors(self, callback: ErrorCallback) -> None:
        """Unregister an error monitoring callback."""
        self._error_callbacks.discard(callback)
        
        if not self._error_callbacks and self._monitoring_active:
            self._stop_monitoring()
    
    def _start_monitoring(self) -> None:
        """Start the error monitoring thread."""
        if self._monitoring_active or not self._ensure_initialized():
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Started error monitoring")
    
    def _stop_monitoring(self) -> None:
        """Stop the error monitoring thread."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=1.0)
        logger.info("Stopped error monitoring")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        last_errors = None
        
        while self._monitoring_active and not self._shutdown:
            try:
                current_errors = self.get_all_errors()
                
                # Check if errors have changed
                if last_errors is None or self._errors_changed(last_errors, current_errors):
                    # Notify all callbacks
                    for callback in self._error_callbacks.copy():  # Copy to avoid modification during iteration
                        try:
                            callback(current_errors)
                        except Exception as e:
                            logger.error(f"Error in monitoring callback: {e}")
                
                last_errors = current_errors
                time.sleep(2.0)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def _errors_changed(self, old_errors: ErrorCollection, new_errors: ErrorCollection) -> bool:
        """Check if error collections have changed."""
        if old_errors.total_count != new_errors.total_count:
            return True
        
        old_ids = set(e.id for e in old_errors.errors)
        new_ids = set(e.id for e in new_errors.errors)
        
        return old_ids != new_ids
    
    def refresh_errors(self) -> ErrorCollection:
        """Force refresh of error detection."""
        # Clear cache to force refresh
        self._error_cache = None
        self._cache_timestamp = None
        
        return self.get_all_errors()
    
    # Helper methods
    
    def _convert_raw_errors(self, raw_errors: List[Any]) -> List[ErrorInfo]:
        """Convert raw LSP errors to ErrorInfo objects."""
        errors = []
        
        for i, raw_error in enumerate(raw_errors):
            try:
                # Convert raw error to ErrorInfo
                # This is a simplified conversion - in practice, you'd parse the actual LSP diagnostic format
                error_info = ErrorInfo(
                    id=f"error_{i}_{hash(str(raw_error))}",
                    message=getattr(raw_error, 'message', str(raw_error)),
                    severity=self._convert_severity(getattr(raw_error, 'severity', 1)),
                    error_type=self._infer_error_type(getattr(raw_error, 'message', '')),
                    file_path=getattr(raw_error, 'file_path', ''),
                    range=self._convert_range(getattr(raw_error, 'range', None)),
                    code=getattr(raw_error, 'code', None),
                    has_quick_fix=getattr(raw_error, 'has_quick_fix', False)
                )
                errors.append(error_info)
                
            except Exception as e:
                logger.error(f"Error converting raw error: {e}")
                continue
        
        return errors
    
    def _convert_severity(self, severity: int) -> ErrorSeverity:
        """Convert LSP severity to ErrorSeverity."""
        severity_map = {
            1: ErrorSeverity.ERROR,
            2: ErrorSeverity.WARNING,
            3: ErrorSeverity.INFO,
            4: ErrorSeverity.HINT
        }
        return severity_map.get(severity, ErrorSeverity.ERROR)
    
    def _infer_error_type(self, message: str) -> ErrorType:
        """Infer error type from message."""
        message_lower = message.lower()
        
        if 'syntax' in message_lower or 'parse' in message_lower:
            return ErrorType.SYNTAX
        elif 'import' in message_lower or 'module' in message_lower:
            return ErrorType.IMPORT
        elif 'undefined' in message_lower or 'not defined' in message_lower:
            return ErrorType.UNDEFINED
        elif 'type' in message_lower:
            return ErrorType.TYPE_CHECK
        else:
            return ErrorType.SEMANTIC
    
    def _convert_range(self, raw_range: Any) -> Range:
        """Convert raw LSP range to Range object."""
        if raw_range is None:
            return Range(Position(0, 0), Position(0, 0))
        
        try:
            start = Position(
                line=getattr(raw_range.start, 'line', 0),
                character=getattr(raw_range.start, 'character', 0)
            )
            end = Position(
                line=getattr(raw_range.end, 'line', 0),
                character=getattr(raw_range.end, 'character', 0)
            )
            return Range(start, end)
        except Exception:
            return Range(Position(0, 0), Position(0, 0))
    
    def _get_surrounding_code(self, file_path: str, range_obj: Range) -> str:
        """Get surrounding code context for an error."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return ""
            
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Get context around the error (5 lines before and after)
            start_line = max(0, range_obj.start.line - 5)
            end_line = min(len(lines), range_obj.end.line + 6)
            
            context_lines = lines[start_line:end_line]
            return ''.join(context_lines)
            
        except Exception as e:
            logger.error(f"Error getting surrounding code: {e}")
            return ""
    
    def _find_related_errors(self, error: ErrorInfo) -> List[ErrorInfo]:
        """Find errors related to the given error."""
        all_errors = self.get_all_errors()
        
        # Find errors in the same file or with similar messages
        related = []
        for other_error in all_errors.errors:
            if other_error.id == error.id:
                continue
            
            if (other_error.file_path == error.file_path or 
                any(symbol in other_error.message for symbol in error.related_symbols)):
                related.append(other_error)
        
        return related[:5]  # Limit to 5 related errors
    
    def _get_symbol_context(self, error: ErrorInfo) -> Dict[str, Any]:
        """Get symbol context for an error."""
        # This would integrate with LSP symbol information
        return {
            "symbols_in_scope": [],
            "imported_modules": [],
            "class_context": None,
            "function_context": None
        }
    
    def _get_fix_suggestions(self, error: ErrorInfo) -> List[str]:
        """Get fix suggestions for an error."""
        # This would integrate with LSP code actions
        suggestions = []
        
        if error.error_type == ErrorType.IMPORT:
            suggestions.append("Add missing import statement")
        elif error.error_type == ErrorType.UNDEFINED:
            suggestions.append("Define the missing variable or function")
        elif error.error_type == ErrorType.SYNTAX:
            suggestions.append("Fix syntax error")
        
        return suggestions
    
    def _analyze_error_impact(self, error: ErrorInfo) -> Dict[str, Any]:
        """Analyze the impact of an error."""
        return {
            "blocking": error.severity == ErrorSeverity.ERROR,
            "affects_compilation": error.error_type in [ErrorType.SYNTAX, ErrorType.IMPORT],
            "affects_runtime": error.error_type in [ErrorType.UNDEFINED, ErrorType.TYPE_CHECK],
            "estimated_fix_time": "5-15 minutes",
            "priority": "high" if error.severity == ErrorSeverity.ERROR else "medium"
        }
    
    # Status and Health
    
    def get_lsp_status(self) -> LSPStatus:
        """Get LSP server status."""
        if not self._ensure_initialized():
            return LSPStatus(
                is_running=False,
                server_info={},
                capabilities=LSPCapabilities(),
                error_message="LSP not initialized"
            )
        
        try:
            # Get status from Serena bridge
            is_running = self._serena_bridge.is_initialized if self._serena_bridge else False
            
            return LSPStatus(
                is_running=is_running,
                server_info={"version": "1.0.0", "name": "Serena LSP"},
                capabilities=LSPCapabilities(
                    completion=True,
                    hover=True,
                    signature_help=True,
                    definition=True,
                    references=True,
                    document_symbols=True,
                    workspace_symbols=True,
                    code_actions=True,
                    rename=True,
                    diagnostics=True
                )
            )
            
        except Exception as e:
            logger.error(f"Error getting LSP status: {e}")
            return LSPStatus(
                is_running=False,
                server_info={},
                capabilities=LSPCapabilities(),
                error_message=str(e)
            )
    
    def get_health_check(self) -> HealthCheck:
        """Get overall codebase health check."""
        try:
            errors = self.get_all_errors()
            lsp_status = self.get_lsp_status()
            
            # Calculate scores
            total_issues = errors.total_count
            error_score = max(0.0, 1.0 - (errors.error_count / max(1, total_issues)))
            warning_score = max(0.0, 1.0 - (errors.warning_count / max(1, total_issues)))
            
            # Overall score (weighted average)
            overall_score = (error_score * 0.6 + warning_score * 0.3 + (1.0 if lsp_status.is_running else 0.0) * 0.1)
            
            recommendations = []
            if errors.error_count > 0:
                recommendations.append(f"Fix {errors.error_count} critical errors")
            if errors.warning_count > 10:
                recommendations.append(f"Address {errors.warning_count} warnings")
            if not lsp_status.is_running:
                recommendations.append("LSP server is not running")
            
            return HealthCheck(
                overall_score=overall_score,
                error_score=error_score,
                warning_score=warning_score,
                code_quality_score=0.8,  # Placeholder
                lsp_health=lsp_status.is_running,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return HealthCheck(
                overall_score=0.0,
                error_score=0.0,
                warning_score=0.0,
                code_quality_score=0.0,
                lsp_health=False,
                recommendations=["Health check failed"]
            )
    
    def shutdown(self) -> None:
        """Shutdown the LSP manager."""
        self._shutdown = True
        self._stop_monitoring()
        
        if self._serena_bridge:
            try:
                self._serena_bridge.shutdown()
            except Exception:
                pass
        
        logger.info(f"LSP Manager shut down for {self.repo_path}")


def get_lsp_manager(repo_path: str) -> LSPManager:
    """Get or create an LSP manager for the given repository path."""
    repo_path = str(Path(repo_path).resolve())
    
    with _manager_lock:
        if repo_path not in _lsp_managers:
            _lsp_managers[repo_path] = LSPManager(repo_path)
        return _lsp_managers[repo_path]


def shutdown_all_managers() -> None:
    """Shutdown all LSP managers."""
    with _manager_lock:
        for manager in _lsp_managers.values():
            manager.shutdown()
        _lsp_managers.clear()


# Export main classes
__all__ = ['LSPManager', 'get_lsp_manager', 'shutdown_all_managers']
