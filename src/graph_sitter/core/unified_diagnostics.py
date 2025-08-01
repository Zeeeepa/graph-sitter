"""
Unified Diagnostic System

This module consolidates diagnostic functionality from multiple sources:
- core/diagnostics.py (CodebaseDiagnostics)
- extensions/lsp/serena_bridge.py (LSP diagnostics)
- extensions/lsp/transaction_manager.py (Transaction-aware diagnostics)

Provides a single interface for all diagnostic operations.
"""

import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Set
from datetime import datetime, timedelta

from graph_sitter.shared.logging.get_logger import get_logger
from .lsp_types import ErrorInfo, ErrorCollection, ErrorSeverity, ErrorType
from .lsp_type_adapters import (
    LSPTypeAdapter, 
    convert_serena_errors_to_unified, 
    create_unified_error_collection
)

# Import diagnostic sources
from ..extensions.lsp.serena_bridge import SerenaLSPBridge, ErrorInfo as SerenaErrorInfo
from ..extensions.lsp.transaction_manager import TransactionAwareLSPManager
from ..core.diagnostics import CodebaseDiagnostics

logger = get_logger(__name__)


class UnifiedDiagnosticCollector:
    """
    Unified diagnostic collector that aggregates diagnostics from multiple sources.
    
    This class consolidates:
    - LSP server diagnostics via SerenaLSPBridge
    - Transaction-aware diagnostics via TransactionAwareLSPManager  
    - Core diagnostic capabilities via CodebaseDiagnostics
    - Custom diagnostic sources
    """
    
    def __init__(self, codebase, enable_lsp: bool = True, enable_transaction_awareness: bool = True):
        self.codebase = codebase
        self.repo_path = Path(codebase.repo_path)
        self.enable_lsp = enable_lsp
        self.enable_transaction_awareness = enable_transaction_awareness
        
        # Diagnostic sources
        self._serena_bridge: Optional[SerenaLSPBridge] = None
        self._transaction_manager: Optional[TransactionAwareLSPManager] = None
        self._core_diagnostics: Optional[CodebaseDiagnostics] = None
        
        # Caching and state
        self._unified_cache: List[ErrorInfo] = []
        self._file_cache: Dict[str, List[ErrorInfo]] = {}
        self._last_refresh = 0.0
        self._refresh_interval = 30.0  # 30 seconds
        self._lock = threading.RLock()
        
        # Monitoring
        self._watchers: List[Callable[[ErrorCollection], None]] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._shutdown = False
        
        self._initialize_sources()
    
    def _initialize_sources(self) -> None:
        """Initialize all diagnostic sources."""
        try:
            # Initialize Serena LSP Bridge
            if self.enable_lsp:
                self._serena_bridge = SerenaLSPBridge(str(self.repo_path))
                logger.info("Serena LSP Bridge initialized")
            
            # Initialize Transaction Manager
            if self.enable_transaction_awareness:
                self._transaction_manager = TransactionAwareLSPManager(
                    str(self.repo_path), 
                    enable_lsp=self.enable_lsp
                )
                logger.info("Transaction-aware LSP Manager initialized")
            
            # Initialize Core Diagnostics
            self._core_diagnostics = CodebaseDiagnostics(
                self.codebase, 
                enable_lsp=self.enable_lsp
            )
            logger.info("Core Diagnostics initialized")
            
        except Exception as e:
            logger.error(f"Error initializing diagnostic sources: {e}")
    
    def get_all_diagnostics(self) -> ErrorCollection:
        """Get all diagnostics from all sources."""
        with self._lock:
            # Check cache validity
            current_time = time.time()
            if (current_time - self._last_refresh) < self._refresh_interval and self._unified_cache:
                return create_unified_error_collection(self._unified_cache)
            
            # Collect from all sources
            all_errors = []
            
            # Collect from Serena LSP Bridge
            if self._serena_bridge:
                try:
                    serena_errors = self._serena_bridge.get_all_diagnostics()
                    unified_errors = convert_serena_errors_to_unified(serena_errors)
                    all_errors.extend(unified_errors)
                    logger.debug(f"Collected {len(unified_errors)} errors from Serena LSP Bridge")
                except Exception as e:
                    logger.error(f"Error collecting from Serena LSP Bridge: {e}")
            
            # Collect from Transaction Manager
            if self._transaction_manager:
                try:
                    transaction_errors = self._transaction_manager.get_all_diagnostics()
                    unified_errors = convert_serena_errors_to_unified(transaction_errors)
                    all_errors.extend(unified_errors)
                    logger.debug(f"Collected {len(unified_errors)} errors from Transaction Manager")
                except Exception as e:
                    logger.error(f"Error collecting from Transaction Manager: {e}")
            
            # Collect from Core Diagnostics
            if self._core_diagnostics:
                try:
                    core_errors = self._core_diagnostics.get_errors()
                    # Convert core errors to unified format if needed
                    if core_errors:
                        # Assume core errors are already in unified format or convert them
                        all_errors.extend(core_errors)
                        logger.debug(f"Collected {len(core_errors)} errors from Core Diagnostics")
                except Exception as e:
                    logger.error(f"Error collecting from Core Diagnostics: {e}")
            
            # Deduplicate errors based on file_path, line, character, and message
            deduplicated_errors = self._deduplicate_errors(all_errors)
            
            # Update cache
            self._unified_cache = deduplicated_errors
            self._last_refresh = current_time
            
            logger.info(f"Collected {len(deduplicated_errors)} total diagnostics from all sources")
            return create_unified_error_collection(deduplicated_errors)
    
    def get_file_diagnostics(self, file_path: str) -> ErrorCollection:
        """Get diagnostics for a specific file."""
        with self._lock:
            # Check file cache
            if file_path in self._file_cache:
                cached_errors = self._file_cache[file_path]
                return create_unified_error_collection(cached_errors)
            
            # Collect file-specific diagnostics
            file_errors = []
            
            # From Serena LSP Bridge
            if self._serena_bridge:
                try:
                    serena_errors = self._serena_bridge.get_file_diagnostics(file_path)
                    unified_errors = convert_serena_errors_to_unified(serena_errors)
                    file_errors.extend(unified_errors)
                except Exception as e:
                    logger.error(f"Error getting file diagnostics from Serena: {e}")
            
            # From Transaction Manager
            if self._transaction_manager:
                try:
                    transaction_errors = self._transaction_manager.get_file_diagnostics(file_path)
                    unified_errors = convert_serena_errors_to_unified(transaction_errors)
                    file_errors.extend(unified_errors)
                except Exception as e:
                    logger.error(f"Error getting file diagnostics from Transaction Manager: {e}")
            
            # Deduplicate
            deduplicated_errors = self._deduplicate_errors(file_errors)
            
            # Cache results
            self._file_cache[file_path] = deduplicated_errors
            
            return create_unified_error_collection(deduplicated_errors)
    
    def get_diagnostics_by_severity(self, severity: ErrorSeverity) -> ErrorCollection:
        """Get diagnostics filtered by severity."""
        all_diagnostics = self.get_all_diagnostics()
        filtered_errors = [e for e in all_diagnostics.errors if e.severity == severity]
        return create_unified_error_collection(filtered_errors)
    
    def get_diagnostics_by_type(self, error_type: ErrorType) -> ErrorCollection:
        """Get diagnostics filtered by error type."""
        all_diagnostics = self.get_all_diagnostics()
        filtered_errors = [e for e in all_diagnostics.errors if e.error_type == error_type]
        return create_unified_error_collection(filtered_errors)
    
    def get_recent_diagnostics(self, since: datetime) -> ErrorCollection:
        """Get diagnostics that occurred since a specific time."""
        # For now, return all diagnostics as we don't track timestamps
        # This can be enhanced to track diagnostic timestamps
        return self.get_all_diagnostics()
    
    def refresh_diagnostics(self) -> ErrorCollection:
        """Force refresh of all diagnostic sources."""
        with self._lock:
            # Clear caches
            self._unified_cache.clear()
            self._file_cache.clear()
            self._last_refresh = 0.0
            
            # Refresh all sources
            if self._serena_bridge:
                try:
                    self._serena_bridge.refresh_diagnostics()
                except Exception as e:
                    logger.error(f"Error refreshing Serena diagnostics: {e}")
            
            if self._transaction_manager:
                try:
                    self._transaction_manager.refresh_diagnostics()
                except Exception as e:
                    logger.error(f"Error refreshing Transaction Manager diagnostics: {e}")
            
            # Get fresh diagnostics
            return self.get_all_diagnostics()
    
    def watch_diagnostics(self, callback: Callable[[ErrorCollection], None]) -> None:
        """Start monitoring diagnostics for changes."""
        with self._lock:
            if callback not in self._watchers:
                self._watchers.append(callback)
            
            # Start monitoring thread if not already running
            if not self._monitoring_thread or not self._monitoring_thread.is_alive():
                self._start_monitoring()
    
    def unwatch_diagnostics(self, callback: Callable[[ErrorCollection], None]) -> None:
        """Stop monitoring diagnostics for a specific callback."""
        with self._lock:
            if callback in self._watchers:
                self._watchers.remove(callback)
    
    def _start_monitoring(self) -> None:
        """Start the diagnostic monitoring thread."""
        def monitor():
            last_error_count = 0
            
            while not self._shutdown:
                try:
                    current_diagnostics = self.get_all_diagnostics()
                    current_error_count = len(current_diagnostics.errors)
                    
                    # Notify watchers if there are changes
                    if current_error_count != last_error_count:
                        with self._lock:
                            for callback in self._watchers[:]:  # Copy to avoid modification during iteration
                                try:
                                    callback(current_diagnostics)
                                except Exception as e:
                                    logger.error(f"Error in diagnostic watcher callback: {e}")
                        
                        last_error_count = current_error_count
                    
                    time.sleep(5.0)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error in diagnostic monitoring: {e}")
                    time.sleep(10.0)  # Wait longer on error
        
        self._monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self._monitoring_thread.start()
        logger.info("Diagnostic monitoring started")
    
    def _deduplicate_errors(self, errors: List[ErrorInfo]) -> List[ErrorInfo]:
        """Remove duplicate errors based on key attributes."""
        seen = set()
        deduplicated = []
        
        for error in errors:
            # Create a key based on file, position, and message
            key = (error.file_path, error.line, error.character, error.message)
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(error)
        
        return deduplicated
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """Get a summary of diagnostic information."""
        diagnostics = self.get_all_diagnostics()
        
        # Group by file
        files_with_errors = {}
        for error in diagnostics.errors:
            if error.file_path not in files_with_errors:
                files_with_errors[error.file_path] = {
                    'errors': 0, 'warnings': 0, 'info': 0, 'hints': 0
                }
            
            if error.severity == ErrorSeverity.ERROR:
                files_with_errors[error.file_path]['errors'] += 1
            elif error.severity == ErrorSeverity.WARNING:
                files_with_errors[error.file_path]['warnings'] += 1
            elif error.severity == ErrorSeverity.INFO:
                files_with_errors[error.file_path]['info'] += 1
            elif error.severity == ErrorSeverity.HINT:
                files_with_errors[error.file_path]['hints'] += 1
        
        # Group by error type
        error_types = {}
        for error in diagnostics.errors:
            error_type = error.error_type.value if error.error_type else 'unknown'
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_diagnostics': diagnostics.total_count,
            'error_count': diagnostics.error_count,
            'warning_count': diagnostics.warning_count,
            'info_count': diagnostics.info_count,
            'hint_count': diagnostics.hint_count,
            'files_with_errors': len(files_with_errors),
            'files_breakdown': files_with_errors,
            'error_types': error_types,
            'sources_active': {
                'serena_bridge': self._serena_bridge is not None,
                'transaction_manager': self._transaction_manager is not None,
                'core_diagnostics': self._core_diagnostics is not None
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown the diagnostic collector."""
        self._shutdown = True
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
        
        # Shutdown sources
        if self._transaction_manager:
            try:
                self._transaction_manager.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down transaction manager: {e}")
        
        logger.info("Unified diagnostic collector shutdown complete")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except Exception:
            pass
