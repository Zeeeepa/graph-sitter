"""
Unified Error Interface

This module provides the main interface methods that will be added
to the Codebase class to provide unified error functionality.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger
from .unified_error_models import (
    UnifiedError, ErrorContext, ErrorSummary, ErrorResolutionResult
)
from .lsp_error_manager import UnifiedLSPErrorManager
from .unified_error_context import ErrorContextEngine
from .error_resolver import ErrorResolver

logger = get_logger(__name__)


class UnifiedErrorInterface:
    """
    Unified error interface that provides all error-related functionality
    through a single, consistent API.
    
    This class will be integrated into the Codebase class to provide:
    - codebase.errors()
    - codebase.full_error_context(error_id)
    - codebase.resolve_errors()
    - codebase.resolve_error(error_id)
    """
    
    def __init__(self, codebase):
        self.codebase = codebase
        self._error_manager: Optional[UnifiedLSPErrorManager] = None
        self._context_engine: Optional[ErrorContextEngine] = None
        self._error_resolver: Optional[ErrorResolver] = None
        self._initialized = False
        
        # Lazy initialization flag
        self._initialization_attempted = False
    
    def _ensure_initialized(self) -> bool:
        """Ensure all components are initialized (lazy loading)."""
        if self._initialized:
            return True
        
        if self._initialization_attempted:
            return self._initialized
        
        self._initialization_attempted = True
        
        try:
            # Initialize error manager
            repo_path = str(getattr(self.codebase, 'repo_path', '.'))
            self._error_manager = UnifiedLSPErrorManager(repo_path)
            
            # Initialize context engine
            self._context_engine = ErrorContextEngine(self.codebase)
            
            # Initialize error resolver
            self._error_resolver = ErrorResolver(
                self.codebase, 
                self._error_manager, 
                self._context_engine
            )
            
            self._initialized = True
            logger.info("✅ Unified error interface initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize unified error interface: {e}")
            self._initialized = False
        
        return self._initialized
    
    def errors(
        self, 
        include_warnings: bool = True, 
        include_hints: bool = False,
        file_path: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[UnifiedError]:
        """
        Get all errors in the codebase.
        
        Args:
            include_warnings: Include warnings in results
            include_hints: Include hints/info in results
            file_path: Filter by specific file path
            category: Filter by error category
            source: Filter by error source (e.g., 'pylsp', 'mypy')
            
        Returns:
            List of unified errors matching the criteria
        """
        if not self._ensure_initialized():
            logger.warning("Error interface not initialized, returning empty list")
            return []
        
        try:
            if file_path:
                # Get errors for specific file
                all_errors = self._error_manager.get_file_errors(file_path)
            else:
                # Get all errors
                all_errors = self._error_manager.get_all_errors(
                    include_warnings=include_warnings,
                    include_hints=include_hints
                )
            
            # Apply additional filters
            filtered_errors = all_errors
            
            if category:
                filtered_errors = [e for e in filtered_errors if e.category.value == category]
            
            if source:
                filtered_errors = [e for e in filtered_errors if e.source == source]
            
            return filtered_errors
            
        except Exception as e:
            logger.error(f"Error retrieving errors: {e}")
            return []
    
    def full_error_context(self, error_id: str) -> Optional[ErrorContext]:
        """
        Get comprehensive context for a specific error.
        
        Args:
            error_id: ID of the error to analyze
            
        Returns:
            Complete error context information, or None if error not found
        """
        if not self._ensure_initialized():
            logger.warning("Error interface not initialized")
            return None
        
        try:
            # Get the error first
            error = self._error_manager.get_error_by_id(error_id)
            if not error:
                logger.warning(f"Error {error_id} not found")
                return None
            
            # Get full context
            context = self._context_engine.get_full_error_context(error)
            return context
            
        except Exception as e:
            logger.error(f"Error getting context for {error_id}: {e}")
            return None
    
    def resolve_errors(
        self, 
        error_ids: Optional[List[str]] = None,
        auto_fixable_only: bool = True,
        max_fixes: Optional[int] = None
    ) -> List[ErrorResolutionResult]:
        """
        Resolve multiple errors automatically.
        
        Args:
            error_ids: Specific error IDs to resolve, or None for all eligible errors
            auto_fixable_only: Only attempt to fix errors with high-confidence fixes
            max_fixes: Maximum number of fixes to apply (for safety)
            
        Returns:
            List of resolution results
        """
        if not self._ensure_initialized():
            logger.warning("Error interface not initialized")
            return []
        
        try:
            # Determine which errors to fix
            if error_ids is None:
                # Get all errors and filter for auto-fixable ones
                all_errors = self._error_manager.get_all_errors()
                if auto_fixable_only:
                    target_errors = [e for e in all_errors if e.auto_fixable]
                else:
                    target_errors = [e for e in all_errors if e.is_fixable]
                
                error_ids = [e.id for e in target_errors]
            
            # Apply max_fixes limit
            if max_fixes and len(error_ids) > max_fixes:
                logger.info(f"Limiting fixes to {max_fixes} out of {len(error_ids)} eligible errors")
                error_ids = error_ids[:max_fixes]
            
            # Resolve the errors
            results = self._error_resolver.resolve_errors(error_ids)
            
            # Log summary
            successful = sum(1 for r in results if r.success)
            logger.info(f"Resolved {successful}/{len(results)} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Error resolving errors: {e}")
            return []
    
    def resolve_error(self, error_id: str) -> ErrorResolutionResult:
        """
        Resolve a specific error by ID.
        
        Args:
            error_id: ID of the error to resolve
            
        Returns:
            Result of the resolution attempt
        """
        if not self._ensure_initialized():
            logger.warning("Error interface not initialized")
            return ErrorResolutionResult(
                error_id=error_id,
                success=False,
                message="Error interface not initialized"
            )
        
        try:
            result = self._error_resolver.resolve_error(error_id)
            
            if result.success:
                logger.info(f"✅ Successfully resolved error {error_id}")
            else:
                logger.warning(f"❌ Failed to resolve error {error_id}: {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error resolving {error_id}: {e}")
            return ErrorResolutionResult(
                error_id=error_id,
                success=False,
                message=f"Exception during resolution: {str(e)}"
            )
    
    def error_summary(self) -> ErrorSummary:
        """
        Get a comprehensive summary of all errors in the codebase.
        
        Returns:
            Summary of error statistics and hotspots
        """
        if not self._ensure_initialized():
            logger.warning("Error interface not initialized")
            return ErrorSummary()
        
        try:
            return self._error_manager.get_error_summary()
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return ErrorSummary()
    
    def refresh_errors(self, file_path: Optional[str] = None) -> None:
        """
        Refresh error information from LSP servers.
        
        Args:
            file_path: Specific file to refresh, or None for all files
        """
        if not self._ensure_initialized():
            logger.warning("Error interface not initialized")
            return
        
        try:
            self._error_manager.refresh_errors(file_path)
            
            # Clear context cache since errors may have changed
            self._context_engine.clear_cache()
            
            logger.info(f"Refreshed errors for {'all files' if not file_path else file_path}")
            
        except Exception as e:
            logger.error(f"Error refreshing errors: {e}")
    
    def get_fixable_errors(self, auto_fixable_only: bool = True) -> List[UnifiedError]:
        """
        Get all errors that can be automatically fixed.
        
        Args:
            auto_fixable_only: Only return errors with high-confidence fixes
            
        Returns:
            List of fixable errors
        """
        all_errors = self.errors()
        
        if auto_fixable_only:
            return [e for e in all_errors if e.auto_fixable]
        else:
            return [e for e in all_errors if e.is_fixable]
    
    def preview_fix(self, error_id: str) -> Dict[str, Any]:
        """
        Preview what would happen if we tried to fix an error.
        
        Args:
            error_id: ID of the error to preview
            
        Returns:
            Preview information about the potential fix
        """
        if not self._ensure_initialized():
            return {'error': 'Error interface not initialized'}
        
        try:
            return self._error_resolver.preview_resolution(error_id)
        except Exception as e:
            logger.error(f"Error previewing fix for {error_id}: {e}")
            return {'error': str(e)}
    
    def get_resolution_stats(self) -> Dict[str, Any]:
        """
        Get statistics about error resolution attempts.
        
        Returns:
            Dictionary with resolution statistics
        """
        if not self._ensure_initialized():
            return {}
        
        try:
            return self._error_resolver.get_resolution_stats()
        except Exception as e:
            logger.error(f"Error getting resolution stats: {e}")
            return {}
    
    def add_error_callback(self, callback) -> None:
        """
        Add a callback for real-time error updates.
        
        Args:
            callback: Function to call when errors are updated
        """
        if self._ensure_initialized():
            self._error_manager.add_error_callback(callback)
    
    def remove_error_callback(self, callback) -> None:
        """
        Remove an error callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if self._ensure_initialized():
            self._error_manager.remove_error_callback(callback)
    
    def shutdown(self) -> None:
        """Shutdown the error interface and cleanup resources."""
        try:
            if self._error_manager:
                self._error_manager.shutdown()
            
            if self._context_engine:
                self._context_engine.clear_cache()
            
            self._initialized = False
            logger.info("Unified error interface shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.shutdown()
        except Exception:
            pass


def add_unified_error_interface_to_codebase(codebase_class: type) -> None:
    """
    Add the unified error interface methods to the Codebase class.
    
    This function is called during Serena initialization to add the
    error methods directly to the Codebase class.
    """
    
    def _get_error_interface(self) -> UnifiedErrorInterface:
        """Get or create the error interface instance."""
        if not hasattr(self, '_unified_error_interface'):
            self._unified_error_interface = UnifiedErrorInterface(self)
        return self._unified_error_interface
    
    def errors(
        self, 
        include_warnings: bool = True, 
        include_hints: bool = False,
        file_path: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[UnifiedError]:
        """Get all errors in the codebase."""
        return self._get_error_interface().errors(
            include_warnings=include_warnings,
            include_hints=include_hints,
            file_path=file_path,
            category=category,
            source=source
        )
    
    def full_error_context(self, error_id: str) -> Optional[ErrorContext]:
        """Get comprehensive context for a specific error."""
        return self._get_error_interface().full_error_context(error_id)
    
    def resolve_errors(
        self, 
        error_ids: Optional[List[str]] = None,
        auto_fixable_only: bool = True,
        max_fixes: Optional[int] = None
    ) -> List[ErrorResolutionResult]:
        """Resolve multiple errors automatically."""
        return self._get_error_interface().resolve_errors(
            error_ids=error_ids,
            auto_fixable_only=auto_fixable_only,
            max_fixes=max_fixes
        )
    
    def resolve_error(self, error_id: str) -> ErrorResolutionResult:
        """Resolve a specific error by ID."""
        return self._get_error_interface().resolve_error(error_id)
    
    def error_summary(self) -> ErrorSummary:
        """Get a comprehensive summary of all errors."""
        return self._get_error_interface().error_summary()
    
    def refresh_errors(self, file_path: Optional[str] = None) -> None:
        """Refresh error information from LSP servers."""
        return self._get_error_interface().refresh_errors(file_path)
    
    def get_fixable_errors(self, auto_fixable_only: bool = True) -> List[UnifiedError]:
        """Get all errors that can be automatically fixed."""
        return self._get_error_interface().get_fixable_errors(auto_fixable_only)
    
    def preview_fix(self, error_id: str) -> Dict[str, Any]:
        """Preview what would happen if we tried to fix an error."""
        return self._get_error_interface().preview_fix(error_id)
    
    # Add methods to the codebase class
    codebase_class._get_error_interface = _get_error_interface
    codebase_class.errors = errors
    codebase_class.full_error_context = full_error_context
    codebase_class.resolve_errors = resolve_errors
    codebase_class.resolve_error = resolve_error
    codebase_class.error_summary = error_summary
    codebase_class.refresh_errors = refresh_errors
    codebase_class.get_fixable_errors = get_fixable_errors
    codebase_class.preview_fix = preview_fix
    
    logger.info("✅ Unified error interface methods added to Codebase class")

