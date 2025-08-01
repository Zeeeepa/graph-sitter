"""
Diagnostic Extensions for Codebase

This module provides diagnostic capabilities for the Codebase class,
integrating Serena's LSP for real-time error detection and semantic analysis.
"""

from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from graph_sitter.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase

logger = get_logger(__name__)

# LSP integration imports (optional)
try:
    from graph_sitter.extensions.lsp.transaction_manager import get_lsp_manager, TransactionAwareLSPManager
    from graph_sitter.extensions.lsp.protocol.lsp_types import ErrorInfo
    LSP_AVAILABLE = True
except ImportError:
    logger.info("LSP integration not available. Install Serena dependencies for error detection.")
    LSP_AVAILABLE = False
    # Fallback types
    class ErrorInfo:
        def __init__(self, **kwargs):
            pass
    class TransactionAwareLSPManager:
        def __init__(self, *args, **kwargs):
            pass


class CodebaseDiagnostics:
    """Diagnostic capabilities for Codebase instances."""
    
    def __init__(self, codebase: "Codebase", enable_lsp: bool = True):
        self.codebase = codebase
        self.enable_lsp = enable_lsp and LSP_AVAILABLE
        self._lsp_manager: Optional[TransactionAwareLSPManager] = None
        
        if self.enable_lsp:
            self._initialize_lsp()
    
    def _initialize_lsp(self) -> None:
        """Initialize LSP integration."""
        try:
            self._lsp_manager = get_lsp_manager(self.codebase.repo_path, self.enable_lsp)
            
            # Only hook into apply_diffs if the method exists
            if hasattr(self.codebase, 'ctx') and hasattr(self.codebase.ctx, 'apply_diffs'):
                original_apply_diffs = self.codebase.ctx.apply_diffs
                
                def enhanced_apply_diffs(diffs):
                    # Call original method
                    result = original_apply_diffs(diffs)
                    
                    # Update LSP context
                    if self._lsp_manager:
                        try:
                            self._lsp_manager.apply_diffs(diffs)
                        except Exception as e:
                            logger.warning(f"Failed to update LSP context: {e}")
                    
                    return result
                
                # Replace the method
                self.codebase.ctx.apply_diffs = enhanced_apply_diffs
            
            logger.info(f"LSP diagnostics enabled for {self.codebase.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LSP diagnostics: {e}")
            import traceback
            logger.error(f"LSP initialization traceback: {traceback.format_exc()}")
            self.enable_lsp = False
            self._lsp_manager = None
    
    @property
    def errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase."""
        if not self.enable_lsp or not self._lsp_manager:
            return []
        return self._lsp_manager.errors
    
    @property
    def warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        if not self.enable_lsp or not self._lsp_manager:
            return []
        return self._lsp_manager.warnings
    
    @property
    def hints(self) -> List[ErrorInfo]:
        """Get all hints in the codebase."""
        if not self.enable_lsp or not self._lsp_manager:
            return []
        return self._lsp_manager.hints
    
    @property
    def diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) in the codebase."""
        if not self.enable_lsp or not self._lsp_manager:
            return []
        return self._lsp_manager.diagnostics
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        if not self.enable_lsp or not self._lsp_manager:
            return []
        return self._lsp_manager.get_file_errors(file_path)
    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get all diagnostics for a specific file."""
        if not self.enable_lsp or not self._lsp_manager:
            return []
        return self._lsp_manager.get_file_diagnostics(file_path)
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.enable_lsp or not self._lsp_manager:
            return
        self._lsp_manager.refresh_diagnostics()
    
    def is_lsp_enabled(self) -> bool:
        """Check if LSP integration is enabled and working."""
        return self.enable_lsp and self._lsp_manager is not None
    
    def get_lsp_status(self) -> dict:
        """Get status information about the LSP integration."""
        if not self.enable_lsp or not self._lsp_manager:
            return {'enabled': False, 'available': LSP_AVAILABLE}
        
        status = self._lsp_manager.get_lsp_status()
        status['available'] = LSP_AVAILABLE
        return status
    
    def shutdown(self) -> None:
        """Shutdown diagnostic services."""
        if self._lsp_manager:
            self._lsp_manager.shutdown()
            self._lsp_manager = None


def add_diagnostic_capabilities(codebase: "Codebase", enable_lsp: bool = True) -> None:
    """
    Add diagnostic capabilities to a Codebase instance.
    
    This function extends the codebase with LSP-based error detection and
    diagnostic capabilities that stay synchronized with file changes.
    
    Args:
        codebase: The Codebase instance to extend
        enable_lsp: Whether to enable LSP integration (default: True)
    """
    if hasattr(codebase, '_diagnostics'):
        # Already has diagnostics
        return
    
    # Create diagnostics instance
    diagnostics = CodebaseDiagnostics(codebase, enable_lsp)
    codebase._diagnostics = diagnostics
    
    # Add properties to codebase
    def _get_errors(self):
        return self._diagnostics.errors
    
    def _get_warnings(self):
        return self._diagnostics.warnings
    
    def _get_hints(self):
        return self._diagnostics.hints
    
    def _get_diagnostics(self):
        return self._diagnostics.diagnostics
    
    def _get_file_errors(file_path: str):
        return codebase._diagnostics.get_file_errors(file_path)
    
    def _get_file_diagnostics(file_path: str):
        return codebase._diagnostics.get_file_diagnostics(file_path)
    
    def _refresh_diagnostics():
        return codebase._diagnostics.refresh_diagnostics()
    
    def _is_lsp_enabled():
        return codebase._diagnostics.is_lsp_enabled()
    
    def _get_lsp_status():
        return codebase._diagnostics.get_lsp_status()
    
    # Add properties and methods to codebase instance
    # Use type() to add properties to the instance's class
    codebase_class = type(codebase)
    
    # Add properties if they don't already exist
    if not hasattr(codebase_class, 'errors'):
        codebase_class.errors = property(_get_errors)
    if not hasattr(codebase_class, 'warnings'):
        codebase_class.warnings = property(_get_warnings)
    if not hasattr(codebase_class, 'hints'):
        codebase_class.hints = property(_get_hints)
    if not hasattr(codebase_class, 'diagnostics'):
        codebase_class.diagnostics = property(_get_diagnostics)
    
    # Add methods directly to the instance
    codebase.get_file_errors = _get_file_errors
    codebase.get_file_diagnostics = _get_file_diagnostics
    codebase.refresh_diagnostics = _refresh_diagnostics
    codebase.is_lsp_enabled = _is_lsp_enabled
    codebase.get_lsp_status = _get_lsp_status
    
    # Add cleanup to existing shutdown method if it exists
    original_shutdown = getattr(codebase, 'shutdown', None)
    
    def enhanced_shutdown():
        if original_shutdown:
            original_shutdown()
        codebase._diagnostics.shutdown()
    
    codebase.shutdown = enhanced_shutdown
    
    logger.info(f"Diagnostic capabilities added to codebase: {codebase.repo_path}")


# Monkey patch to automatically add diagnostics to new Codebase instances
def _patch_codebase_init():
    """Monkey patch Codebase.__init__ to automatically add diagnostics."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        # Check if already patched
        if hasattr(Codebase, '_diagnostics_patched'):
            return
        
        original_init = Codebase.__init__
        
        def enhanced_init(self, *args, enable_lsp: bool = True, **kwargs):
            # Call original init
            original_init(self, *args, **kwargs)
            
            # Add diagnostic capabilities
            try:
                add_diagnostic_capabilities(self, enable_lsp)
            except Exception as e:
                logger.warning(f"Failed to add diagnostic capabilities: {e}")
        
        # Replace the __init__ method
        Codebase.__init__ = enhanced_init
        Codebase._diagnostics_patched = True
        
        logger.info("Codebase class patched with diagnostic capabilities")
        
    except ImportError:
        logger.warning("Could not patch Codebase class - import failed")
    except Exception as e:
        logger.error(f"Failed to patch Codebase class: {e}")


# Auto-patch when module is imported (always try, even without Serena)
_patch_codebase_init()
