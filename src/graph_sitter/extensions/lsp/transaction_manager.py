"""
Transaction-Aware LSP Manager

This module provides transaction-aware LSP integration that stays synchronized
with graph-sitter's file change tracking and transaction system.
"""

import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from weakref import WeakKeyDictionary

from graph_sitter.shared.logging.get_logger import get_logger
from .serena_bridge import SerenaLSPBridge, ErrorInfo, ErrorType, RuntimeContext, DiagnosticSeverity

logger = get_logger(__name__)

# Global registry of LSP managers
_lsp_managers: WeakKeyDictionary = WeakKeyDictionary()
_manager_lock = threading.RLock()


class TransactionAwareLSPManager:
    """
    LSP manager that integrates with graph-sitter's transaction system
    to provide real-time diagnostic updates.
    """
    
    def __init__(self, repo_path: str, enable_lsp: bool = True):
        self.repo_path = Path(repo_path)
        self.enable_lsp = enable_lsp
        self._bridge: Optional[SerenaLSPBridge] = None
        self._diagnostics_cache: List[ErrorInfo] = []
        self._file_diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self._last_refresh = 0.0
        self._refresh_interval = 5.0  # Refresh every 5 seconds
        self._lock = threading.RLock()
        self._shutdown = False
        
        if self.enable_lsp:
            self._initialize_bridge()
    
    def _initialize_bridge(self) -> None:
        """Initialize the Serena LSP bridge."""
        try:
            self._bridge = SerenaLSPBridge(str(self.repo_path))
            if self._bridge.is_initialized:
                logger.info(f"LSP manager initialized for {self.repo_path}")
                self._refresh_diagnostics_async()
            else:
                logger.warning(f"LSP bridge failed to initialize for {self.repo_path}")
                self.enable_lsp = False
        except Exception as e:
            logger.error(f"Failed to initialize LSP bridge: {e}")
            self.enable_lsp = False
    
    def _refresh_diagnostics_async(self) -> None:
        """Refresh diagnostics in background thread."""
        def refresh_worker():
            try:
                if self._bridge and not self._shutdown:
                    diagnostics = self._bridge.get_diagnostics()
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
    
    def _should_refresh(self) -> bool:
        """Check if diagnostics should be refreshed."""
        return (time.time() - self._last_refresh) > self._refresh_interval
    
    @property
    def errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase."""
        if not self.enable_lsp:
            return []
        
        if self._should_refresh():
            self._refresh_diagnostics_async()
        
        with self._lock:
            return [d for d in self._diagnostics_cache if d.is_error]
    
    @property
    def warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        if not self.enable_lsp:
            return []
        
        if self._should_refresh():
            self._refresh_diagnostics_async()
        
        with self._lock:
            return [d for d in self._diagnostics_cache if d.is_warning]
    
    @property
    def hints(self) -> List[ErrorInfo]:
        """Get all hints in the codebase."""
        if not self.enable_lsp:
            return []
        
        if self._should_refresh():
            self._refresh_diagnostics_async()
        
        with self._lock:
            return [d for d in self._diagnostics_cache if d.is_hint]
    
    @property
    def diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) in the codebase."""
        if not self.enable_lsp:
            return []
        
        if self._should_refresh():
            self._refresh_diagnostics_async()
        
        with self._lock:
            return self._diagnostics_cache.copy()
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        if not self.enable_lsp:
            return []
        
        file_diagnostics = self.get_file_diagnostics(file_path)
        return [d for d in file_diagnostics if d.is_error]
    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get all diagnostics for a specific file."""
        if not self.enable_lsp:
            return []
        
        # Normalize file path
        try:
            file_path = str(Path(file_path).relative_to(self.repo_path))
        except ValueError:
            # If not relative to repo, use as-is
            pass
        
        with self._lock:
            if file_path in self._file_diagnostics_cache:
                return self._file_diagnostics_cache[file_path].copy()
        
        # If not in cache, try to get from bridge directly
        if self._bridge:
            try:
                diagnostics = self._bridge.get_file_diagnostics(file_path)
                with self._lock:
                    self._file_diagnostics_cache[file_path] = diagnostics
                return diagnostics
            except Exception as e:
                logger.error(f"Error getting file diagnostics: {e}")
        
        return []
    
    def apply_diffs(self, diffs: Any) -> None:
        """
        Handle file changes from graph-sitter's diff system.
        This method is called when files are modified through graph-sitter.
        """
        if not self.enable_lsp or not self._bridge:
            return
        
        try:
            # Extract changed files from diffs
            changed_files: Set[str] = set()
            
            # Handle different diff formats
            if hasattr(diffs, '__iter__'):
                for diff in diffs:
                    if hasattr(diff, 'file_path'):
                        changed_files.add(diff.file_path)
                    elif hasattr(diff, 'path'):
                        changed_files.add(diff.path)
            
            if changed_files:
                logger.debug(f"Files changed: {changed_files}")
                
                # Clear cache for changed files
                with self._lock:
                    for file_path in changed_files:
                        self._file_diagnostics_cache.pop(file_path, None)
                
                # Trigger refresh
                self._refresh_diagnostics_async()
        
        except Exception as e:
            logger.error(f"Error handling diff changes: {e}")
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.enable_lsp or not self._bridge:
            return
        
        try:
            self._bridge.refresh_diagnostics()
            with self._lock:
                self._diagnostics_cache.clear()
                self._file_diagnostics_cache.clear()
                self._last_refresh = 0.0  # Force refresh
            
            self._refresh_diagnostics_async()
            
        except Exception as e:
            logger.error(f"Error refreshing diagnostics: {e}")
    
    def get_lsp_status(self) -> Dict[str, Any]:
        """Get status information about the LSP integration."""
        status = {
            'enabled': self.enable_lsp,
            'repo_path': str(self.repo_path),
            'last_refresh': self._last_refresh,
            'diagnostics_count': len(self._diagnostics_cache),
            'errors_count': len([d for d in self._diagnostics_cache if d.is_error]),
            'warnings_count': len([d for d in self._diagnostics_cache if d.is_warning]),
            'hints_count': len([d for d in self._diagnostics_cache if d.is_hint])
        }
        
        if self._bridge:
            bridge_status = self._bridge.get_status()
            status.update(bridge_status)
        
        return status
    
    def shutdown(self) -> None:
        """Shutdown the LSP manager and clean up resources."""
        self._shutdown = True
        
        if self._bridge:
            try:
                self._bridge.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down LSP bridge: {e}")
        
        with self._lock:
            self._diagnostics_cache.clear()
            self._file_diagnostics_cache.clear()
        
        logger.info(f"LSP manager shutdown for {self.repo_path}")


def get_lsp_manager(repo_path: str, enable_lsp: bool = True) -> TransactionAwareLSPManager:
    """
    Get or create an LSP manager for a repository.
    
    This function maintains a registry of LSP managers to avoid creating
    multiple managers for the same repository.
    """
    repo_path = str(Path(repo_path).resolve())
    
    with _manager_lock:
        # Check if we already have a manager for this repo
        for existing_manager in _lsp_managers.values():
            if str(existing_manager.repo_path) == repo_path:
                return existing_manager
        
        # Create new manager
        manager = TransactionAwareLSPManager(repo_path, enable_lsp)
        
        # Store in registry (using a dummy key since we can't use the manager as its own key)
        _lsp_managers[object()] = manager
        
        return manager


def shutdown_all_lsp_managers() -> None:
    """Shutdown all active LSP managers."""
    with _manager_lock:
        for manager in list(_lsp_managers.values()):
            try:
                manager.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down LSP manager: {e}")
        
        _lsp_managers.clear()
        logger.info("All LSP managers shutdown")
