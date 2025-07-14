"""
Transaction-Aware LSP Context Manager

This module provides a transaction-aware context manager that keeps Serena's LSP
synchronized with Graph-Sitter's file changes, ensuring diagnostic information
is always current with the codebase state.
"""

import threading
import weakref
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable
from contextlib import contextmanager

from graph_sitter.codebase.diff_lite import DiffLite
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge, ErrorInfo
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class TransactionAwareLSPManager:
    """
    Manages LSP context in a transaction-aware manner, ensuring that diagnostic
    information stays synchronized with Graph-Sitter's codebase changes.
    """
    
    def __init__(self, repo_path: Path, enable_lsp: bool = True):
        self.repo_path = repo_path
        self.enable_lsp = enable_lsp
        self._lock = threading.RLock()
        self._lsp_bridge: Optional[SerenaLSPBridge] = None
        self._transaction_stack: List[List[DiffLite]] = []
        self._change_listeners: Set[Callable[[List[DiffLite]], None]] = set()
        
        if self.enable_lsp:
            self._initialize_bridge()
    
    def _initialize_bridge(self) -> None:
        """Initialize the Serena LSP bridge."""
        try:
            self._lsp_bridge = SerenaLSPBridge(self.repo_path, self.enable_lsp)
            logger.info(f"Transaction-aware LSP manager initialized for {self.repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LSP bridge: {e}")
            self.enable_lsp = False
    
    def add_change_listener(self, listener: Callable[[List[DiffLite]], None]) -> None:
        """Add a listener for file changes."""
        with self._lock:
            self._change_listeners.add(listener)
    
    def remove_change_listener(self, listener: Callable[[List[DiffLite]], None]) -> None:
        """Remove a change listener."""
        with self._lock:
            self._change_listeners.discard(listener)
    
    def apply_diffs(self, diffs: List[DiffLite]) -> None:
        """
        Apply file changes and update LSP context.
        This is called by Graph-Sitter's transaction system.
        """
        if not self.enable_lsp or not self._lsp_bridge:
            return
        
        with self._lock:
            try:
                # Process each diff through the LSP bridge
                for diff in diffs:
                    self._lsp_bridge.handle_file_change(diff)
                
                # Notify change listeners
                for listener in self._change_listeners:
                    try:
                        listener(diffs)
                    except Exception as e:
                        logger.warning(f"Change listener failed: {e}")
                
                logger.debug(f"Applied {len(diffs)} diffs to LSP context")
                
            except Exception as e:
                logger.error(f"Error applying diffs to LSP: {e}")
    
    @contextmanager
    def transaction(self):
        """
        Context manager for LSP transactions.
        Changes are batched and applied atomically.
        """
        with self._lock:
            # Start a new transaction
            self._transaction_stack.append([])
            
            try:
                yield self
            except Exception as e:
                # Rollback transaction on error
                self._rollback_transaction()
                raise
            else:
                # Commit transaction on success
                self._commit_transaction()
    
    def _commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self._transaction_stack:
            return
        
        diffs = self._transaction_stack.pop()
        if diffs:
            self.apply_diffs(diffs)
    
    def _rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if self._transaction_stack:
            diffs = self._transaction_stack.pop()
            logger.info(f"Rolled back transaction with {len(diffs)} changes")
    
    def add_transaction_diff(self, diff: DiffLite) -> None:
        """Add a diff to the current transaction."""
        with self._lock:
            if self._transaction_stack:
                self._transaction_stack[-1].append(diff)
            else:
                # No active transaction, apply immediately
                self.apply_diffs([diff])
    
    @property
    def errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase."""
        if not self.enable_lsp or not self._lsp_bridge:
            return []
        return self._lsp_bridge.get_errors()
    
    @property
    def warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        if not self.enable_lsp or not self._lsp_bridge:
            return []
        return self._lsp_bridge.get_warnings()
    
    @property
    def hints(self) -> List[ErrorInfo]:
        """Get all hints in the codebase."""
        if not self.enable_lsp or not self._lsp_bridge:
            return []
        return self._lsp_bridge.get_hints()
    
    @property
    def diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) in the codebase."""
        if not self.enable_lsp or not self._lsp_bridge:
            return []
        return self._lsp_bridge.get_diagnostics()
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        if not self.enable_lsp or not self._lsp_bridge:
            return []
        
        all_errors = self._lsp_bridge.get_errors()
        return [error for error in all_errors if error.file_path == file_path]
    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get all diagnostics for a specific file."""
        if not self.enable_lsp or not self._lsp_bridge:
            return []
        
        all_diagnostics = self._lsp_bridge.get_diagnostics()
        return [diag for diag in all_diagnostics if diag.file_path == file_path]
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.enable_lsp or not self._lsp_bridge:
            return
        
        with self._lock:
            # Clear cache to force refresh
            self._lsp_bridge._diagnostics_cache.clear()
            logger.info("Forced refresh of LSP diagnostics")
    
    def is_lsp_enabled(self) -> bool:
        """Check if LSP integration is enabled and working."""
        return self.enable_lsp and self._lsp_bridge is not None
    
    def get_lsp_status(self) -> Dict[str, any]:
        """Get status information about the LSP integration."""
        status = {
            'enabled': self.enable_lsp,
            'bridge_initialized': self._lsp_bridge is not None,
            'active_transactions': len(self._transaction_stack),
            'change_listeners': len(self._change_listeners)
        }
        
        if self._lsp_bridge:
            status.update({
                'serena_available': self._lsp_bridge.enable_lsp,
                'cached_files': len(self._lsp_bridge._diagnostics_cache)
            })
        
        return status
    
    def shutdown(self) -> None:
        """Shutdown the LSP manager and clean up resources."""
        with self._lock:
            if self._lsp_bridge:
                self._lsp_bridge.shutdown()
                self._lsp_bridge = None
            
            self._transaction_stack.clear()
            self._change_listeners.clear()
            logger.info("Transaction-aware LSP manager shut down")


# Global registry for LSP managers to prevent multiple instances
_lsp_managers: Dict[str, weakref.ReferenceType] = {}
_registry_lock = threading.Lock()


def get_lsp_manager(repo_path: Path, enable_lsp: bool = True) -> TransactionAwareLSPManager:
    """
    Get or create an LSP manager for a repository.
    Uses a global registry to ensure only one manager per repository.
    """
    repo_key = str(repo_path.resolve())
    
    with _registry_lock:
        # Check if we already have a manager for this repo
        if repo_key in _lsp_managers:
            manager_ref = _lsp_managers[repo_key]
            manager = manager_ref()
            if manager is not None:
                return manager
            else:
                # Manager was garbage collected, remove from registry
                del _lsp_managers[repo_key]
        
        # Create new manager
        manager = TransactionAwareLSPManager(repo_path, enable_lsp)
        _lsp_managers[repo_key] = weakref.ref(manager, lambda ref: _cleanup_manager(repo_key))
        
        return manager


def _cleanup_manager(repo_key: str) -> None:
    """Clean up manager from registry when it's garbage collected."""
    with _registry_lock:
        _lsp_managers.pop(repo_key, None)
