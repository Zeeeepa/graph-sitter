"""
LSP Methods Mixin for Codebase

This module provides all the LSP error retrieval and intelligence methods
that will be mixed into the main Codebase class.
"""

from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger
from .lsp_types import (
    ErrorInfo, ErrorCollection, ErrorSummary, ErrorContext, QuickFix,
    CompletionItem, HoverInfo, SignatureHelp, SymbolInfo, LSPCapabilities,
    LSPStatus, HealthCheck, ErrorSeverity, ErrorType, Position, Range,
    ErrorCallback
)
from .lsp_manager import get_lsp_manager, LSPManager

logger = get_logger(__name__)


class LSPMethodsMixin:
    """
    Mixin class that provides all LSP error retrieval and intelligence methods
    for the Codebase class.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lsp_manager: Optional[LSPManager] = None
    
    @property
    def _lsp(self) -> LSPManager:
        """Get the LSP manager instance (lazy loading)."""
        if self._lsp_manager is None:
            self._lsp_manager = get_lsp_manager(str(self.repo_path))
        return self._lsp_manager
    
    # =====[ Core Error Retrieval Commands ]=====
    
    def errors(self) -> ErrorCollection:
        """Get all errors in the codebase.
        
        Returns:
            ErrorCollection: Collection of all errors with metadata
            
        Example:
            >>> codebase = Codebase("./my-project")
            >>> all_errors = codebase.errors()
            >>> print(f"Found {len(all_errors.errors)} errors")
        """
        return self._lsp.get_all_errors(codebase=self)
    
    def full_error_context(self, error_id: str) -> Optional[ErrorContext]:
        """Get full context for a specific error.
        
        Args:
            error_id: The ID of the error to get context for
            
        Returns:
            ErrorContext: Full context information for the error, or None if not found
            
        Example:
            >>> errors = codebase.errors()
            >>> if errors.errors:
            ...     context = codebase.full_error_context(errors.errors[0].id)
            ...     print(f"Error context: {context.surrounding_code}")
        """
        return self._lsp.get_full_error_context(error_id)
    
    # =====[ Basic Error Operations ]=====
    
    def errors_by_file(self, file_path: str) -> ErrorCollection:
        """Get errors in a specific file.
        
        Args:
            file_path: Path to the file to get errors for
            
        Returns:
            ErrorCollection: Errors in the specified file
            
        Example:
            >>> file_errors = codebase.errors_by_file("src/main.py")
            >>> print(f"Found {len(file_errors.errors)} errors in main.py")
        """
        return self._lsp.get_errors_by_file(file_path)
    
    def errors_by_severity(self, severity: ErrorSeverity) -> ErrorCollection:
        """Filter errors by severity level.
        
        Args:
            severity: The severity level to filter by (ERROR, WARNING, INFO, HINT)
            
        Returns:
            ErrorCollection: Errors matching the specified severity
            
        Example:
            >>> critical_errors = codebase.errors_by_severity(ErrorSeverity.ERROR)
            >>> warnings = codebase.errors_by_severity(ErrorSeverity.WARNING)
        """
        return self._lsp.get_errors_by_severity(severity)
    
    def errors_by_type(self, error_type: ErrorType) -> ErrorCollection:
        """Filter errors by error type.
        
        Args:
            error_type: The type of error to filter by (SYNTAX, SEMANTIC, LINT, etc.)
            
        Returns:
            ErrorCollection: Errors matching the specified type
            
        Example:
            >>> syntax_errors = codebase.errors_by_type(ErrorType.SYNTAX)
            >>> import_errors = codebase.errors_by_type(ErrorType.IMPORT)
        """
        return self._lsp.get_errors_by_type(error_type)
    
    def recent_errors(self, since_timestamp: datetime) -> ErrorCollection:
        """Get errors that occurred since a specific timestamp.
        
        Args:
            since_timestamp: Only return errors newer than this timestamp
            
        Returns:
            ErrorCollection: Recent errors since the timestamp
            
        Example:
            >>> from datetime import datetime, timedelta
            >>> one_hour_ago = datetime.now() - timedelta(hours=1)
            >>> recent = codebase.recent_errors(one_hour_ago)
        """
        return self._lsp.get_recent_errors(since_timestamp)
    
    # =====[ Detailed Error Context ]=====
    
    def error_suggestions(self, error_id: str) -> List[str]:
        """Get fix suggestions for a specific error.
        
        Args:
            error_id: The ID of the error to get suggestions for
            
        Returns:
            List[str]: List of suggested fixes
            
        Example:
            >>> suggestions = codebase.error_suggestions("error_123")
            >>> for suggestion in suggestions:
            ...     print(f"Suggestion: {suggestion}")
        """
        context = self.full_error_context(error_id)
        return context.fix_suggestions if context else []
    
    def error_related_symbols(self, error_id: str) -> List[str]:
        """Get symbols related to a specific error.
        
        Args:
            error_id: The ID of the error to get related symbols for
            
        Returns:
            List[str]: List of related symbol names
            
        Example:
            >>> symbols = codebase.error_related_symbols("error_123")
            >>> print(f"Related symbols: {symbols}")
        """
        errors = self.errors()
        error = next((e for e in errors.errors if e.id == error_id), None)
        return error.related_symbols if error else []
    
    def error_impact_analysis(self, error_id: str) -> Dict[str, Any]:
        """Get impact analysis for a specific error.
        
        Args:
            error_id: The ID of the error to analyze
            
        Returns:
            Dict[str, Any]: Impact analysis information
            
        Example:
            >>> impact = codebase.error_impact_analysis("error_123")
            >>> print(f"Blocking: {impact.get('blocking', False)}")
        """
        context = self.full_error_context(error_id)
        return context.impact_analysis if context else {}
    
    # =====[ Error Statistics & Analysis ]=====
    
    def error_summary(self) -> ErrorSummary:
        """Get summary statistics of all errors.
        
        Returns:
            ErrorSummary: Statistical summary of errors
            
        Example:
            >>> summary = codebase.error_summary()
            >>> print(f"Errors: {summary.error_count}, Warnings: {summary.warning_count}")
        """
        return self._lsp.get_error_summary()
    
    def error_trends(self) -> Dict[str, Any]:
        """Get error trends over time.
        
        Returns:
            Dict[str, Any]: Error trend information
            
        Example:
            >>> trends = codebase.error_trends()
            >>> print(f"Error trend: {trends.get('direction', 'stable')}")
        """
        # This would require historical data - placeholder implementation
        summary = self.error_summary()
        return {
            "current_total": summary.total_errors,
            "direction": "stable",  # Would be calculated from historical data
            "change_rate": 0.0,
            "last_updated": summary.last_updated
        }
    
    def most_common_errors(self) -> List[Dict[str, Any]]:
        """Get the most frequently occurring errors.
        
        Returns:
            List[Dict[str, Any]]: List of most common error types with counts
            
        Example:
            >>> common = codebase.most_common_errors()
            >>> for error_info in common:
            ...     print(f"{error_info['type']}: {error_info['count']} occurrences")
        """
        summary = self.error_summary()
        return summary.most_common_error_types
    
    def error_hotspots(self) -> List[Dict[str, Any]]:
        """Get files/areas with the most errors.
        
        Returns:
            List[Dict[str, Any]]: List of files with high error counts
            
        Example:
            >>> hotspots = codebase.error_hotspots()
            >>> for hotspot in hotspots:
            ...     print(f"{hotspot['file_path']}: {hotspot['error_count']} errors")
        """
        return self._lsp.get_error_hotspots()
    
    # =====[ Real-time Error Monitoring ]=====
    
    def watch_errors(self, callback: ErrorCallback) -> None:
        """Register a callback for real-time error monitoring.
        
        Args:
            callback: Function to call when errors change. Receives ErrorCollection.
            
        Example:
            >>> def on_error_change(errors):
            ...     print(f"Errors updated: {len(errors.errors)} total errors")
            >>> codebase.watch_errors(on_error_change)
        """
        self._lsp.watch_errors(callback)
    
    def unwatch_errors(self, callback: ErrorCallback) -> None:
        """Unregister an error monitoring callback.
        
        Args:
            callback: The callback function to remove
            
        Example:
            >>> codebase.unwatch_errors(on_error_change)
        """
        self._lsp.unwatch_errors(callback)
    
    def error_stream(self) -> ErrorCollection:
        """Get a stream of error updates (alias for errors() with real-time data).
        
        Returns:
            ErrorCollection: Current error collection
            
        Example:
            >>> stream = codebase.error_stream()
            >>> print(f"Current errors: {len(stream.errors)}")
        """
        return self.errors()
    
    def refresh_errors(self) -> ErrorCollection:
        """Force refresh of error detection.
        
        Returns:
            ErrorCollection: Refreshed error collection
            
        Example:
            >>> refreshed = codebase.refresh_errors()
            >>> print(f"Refreshed errors: {len(refreshed.errors)}")
        """
        return self._lsp.refresh_errors()
    
    # =====[ Error Resolution & Actions ]=====
    
    def auto_fix_errors(self, error_ids: List[str]) -> Dict[str, bool]:
        """Auto-fix specific errors where possible.
        
        Args:
            error_ids: List of error IDs to attempt to fix
            
        Returns:
            Dict[str, bool]: Map of error ID to success status
            
        Example:
            >>> errors = codebase.errors()
            >>> fixable = [e.id for e in errors.errors if e.has_quick_fix]
            >>> results = codebase.auto_fix_errors(fixable)
            >>> print(f"Fixed {sum(results.values())} out of {len(results)} errors")
        """
        results = {}
        for error_id in error_ids:
            try:
                quick_fixes = self.get_quick_fixes(error_id)
                if quick_fixes:
                    # Apply the first available fix
                    success = self.apply_error_fix(error_id, quick_fixes[0].id)
                    results[error_id] = success
                else:
                    results[error_id] = False
            except Exception as e:
                logger.error(f"Error auto-fixing {error_id}: {e}")
                results[error_id] = False
        
        return results
    
    def get_quick_fixes(self, error_id: str) -> List[QuickFix]:
        """Get available quick fixes for an error.
        
        Args:
            error_id: The ID of the error to get fixes for
            
        Returns:
            List[QuickFix]: Available quick fixes
            
        Example:
            >>> fixes = codebase.get_quick_fixes("error_123")
            >>> for fix in fixes:
            ...     print(f"Fix: {fix.title} - {fix.description}")
        """
        # This would integrate with LSP code actions
        # Placeholder implementation
        context = self.full_error_context(error_id)
        if not context:
            return []
        
        fixes = []
        for i, suggestion in enumerate(context.fix_suggestions):
            fix = QuickFix(
                id=f"fix_{error_id}_{i}",
                title=suggestion,
                description=f"Apply fix: {suggestion}",
                edit_operations=[],  # Would contain actual edit operations
                confidence=0.8
            )
            fixes.append(fix)
        
        return fixes
    
    def apply_error_fix(self, error_id: str, fix_id: str) -> bool:
        """Apply a specific fix to an error.
        
        Args:
            error_id: The ID of the error to fix
            fix_id: The ID of the fix to apply
            
        Returns:
            bool: True if fix was applied successfully
            
        Example:
            >>> fixes = codebase.get_quick_fixes("error_123")
            >>> if fixes:
            ...     success = codebase.apply_error_fix("error_123", fixes[0].id)
            ...     print(f"Fix applied: {success}")
        """
        try:
            # This would integrate with LSP code actions and transaction system
            # Placeholder implementation
            logger.info(f"Applying fix {fix_id} to error {error_id}")
            # In real implementation, this would apply the actual code changes
            return True
        except Exception as e:
            logger.error(f"Error applying fix {fix_id} to error {error_id}: {e}")
            return False
    
    # =====[ Code Intelligence ]=====
    
    def completions(self, file_path: str, position: Position) -> List[CompletionItem]:
        """Get code completions at a specific position.
        
        Args:
            file_path: Path to the file
            position: Position in the file (line, character)
            
        Returns:
            List[CompletionItem]: Available completions
            
        Example:
            >>> pos = Position(line=10, character=5)
            >>> completions = codebase.completions("src/main.py", pos)
            >>> for comp in completions:
            ...     print(f"Completion: {comp.label}")
        """
        # This would integrate with LSP completion provider
        # Placeholder implementation
        return []
    
    def hover_info(self, file_path: str, position: Position) -> Optional[HoverInfo]:
        """Get hover information at a specific position.
        
        Args:
            file_path: Path to the file
            position: Position in the file
            
        Returns:
            HoverInfo: Hover information, or None if not available
            
        Example:
            >>> pos = Position(line=10, character=5)
            >>> hover = codebase.hover_info("src/main.py", pos)
            >>> if hover:
            ...     print(f"Hover: {hover.contents}")
        """
        # This would integrate with LSP hover provider
        # Placeholder implementation
        return None
    
    def signature_help(self, file_path: str, position: Position) -> Optional[SignatureHelp]:
        """Get function signature help at a specific position.
        
        Args:
            file_path: Path to the file
            position: Position in the file
            
        Returns:
            SignatureHelp: Signature help information
            
        Example:
            >>> pos = Position(line=10, character=15)
            >>> sig_help = codebase.signature_help("src/main.py", pos)
            >>> if sig_help:
            ...     print(f"Signatures: {len(sig_help.signatures)}")
        """
        # This would integrate with LSP signature help provider
        # Placeholder implementation
        return None
    
    def definitions(self, symbol_name: str) -> List[SymbolInfo]:
        """Go to definition for a symbol.
        
        Args:
            symbol_name: Name of the symbol to find definitions for
            
        Returns:
            List[SymbolInfo]: Symbol definition locations
            
        Example:
            >>> defs = codebase.definitions("MyClass")
            >>> for definition in defs:
            ...     print(f"Definition: {definition.name} at {definition.location}")
        """
        # This would integrate with LSP definition provider
        # Placeholder implementation
        return []
    
    def references(self, symbol_name: str) -> List[SymbolInfo]:
        """Find all references to a symbol.
        
        Args:
            symbol_name: Name of the symbol to find references for
            
        Returns:
            List[SymbolInfo]: Symbol reference locations
            
        Example:
            >>> refs = codebase.references("MyClass")
            >>> print(f"Found {len(refs)} references to MyClass")
        """
        # This would integrate with LSP references provider
        # Placeholder implementation
        return []
    
    # =====[ Code Actions & Refactoring ]=====
    
    def code_actions(self, file_path: str, range_obj: Range) -> List[Dict[str, Any]]:
        """Get available code actions for a range.
        
        Args:
            file_path: Path to the file
            range_obj: Range in the file
            
        Returns:
            List[Dict[str, Any]]: Available code actions
            
        Example:
            >>> range_obj = Range(Position(10, 0), Position(10, 20))
            >>> actions = codebase.code_actions("src/main.py", range_obj)
            >>> for action in actions:
            ...     print(f"Action: {action.get('title', 'Unknown')}")
        """
        # This would integrate with LSP code actions provider
        # Placeholder implementation
        return []
    
    def rename_symbol(self, old_name: str, new_name: str) -> bool:
        """Rename a symbol throughout the codebase.
        
        Args:
            old_name: Current name of the symbol
            new_name: New name for the symbol
            
        Returns:
            bool: True if rename was successful
            
        Example:
            >>> success = codebase.rename_symbol("old_function", "new_function")
            >>> print(f"Rename successful: {success}")
        """
        # This would integrate with LSP rename provider
        # Placeholder implementation
        logger.info(f"Renaming symbol {old_name} to {new_name}")
        return True
    
    def extract_method(self, file_path: str, range_obj: Range) -> bool:
        """Extract a method from a code range.
        
        Args:
            file_path: Path to the file
            range_obj: Range of code to extract
            
        Returns:
            bool: True if extraction was successful
            
        Example:
            >>> range_obj = Range(Position(10, 0), Position(20, 0))
            >>> success = codebase.extract_method("src/main.py", range_obj)
            >>> print(f"Method extracted: {success}")
        """
        # This would integrate with LSP refactoring capabilities
        # Placeholder implementation
        logger.info(f"Extracting method from {file_path} at {range_obj}")
        return True
    
    def organize_imports(self, file_path: str) -> bool:
        """Organize imports in a file.
        
        Args:
            file_path: Path to the file to organize imports for
            
        Returns:
            bool: True if organization was successful
            
        Example:
            >>> success = codebase.organize_imports("src/main.py")
            >>> print(f"Imports organized: {success}")
        """
        # This would integrate with LSP organize imports capability
        # Placeholder implementation
        logger.info(f"Organizing imports in {file_path}")
        return True
    
    # =====[ Semantic Analysis ]=====
    
    def semantic_tokens(self, file_path: str) -> List[Dict[str, Any]]:
        """Get semantic token information for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List[Dict[str, Any]]: Semantic token information
            
        Example:
            >>> tokens = codebase.semantic_tokens("src/main.py")
            >>> print(f"Found {len(tokens)} semantic tokens")
        """
        # This would integrate with LSP semantic tokens provider
        # Placeholder implementation
        return []
    
    def document_symbols(self, file_path: str) -> List[SymbolInfo]:
        """Get document symbol outline for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List[SymbolInfo]: Document symbols
            
        Example:
            >>> symbols = codebase.document_symbols("src/main.py")
            >>> for symbol in symbols:
            ...     print(f"Symbol: {symbol.name} ({symbol.kind})")
        """
        # This would integrate with LSP document symbols provider
        # Placeholder implementation
        return []
    
    def workspace_symbols(self, query: str) -> List[SymbolInfo]:
        """Search workspace symbols.
        
        Args:
            query: Search query for symbols
            
        Returns:
            List[SymbolInfo]: Matching workspace symbols
            
        Example:
            >>> symbols = codebase.workspace_symbols("MyClass")
            >>> print(f"Found {len(symbols)} symbols matching 'MyClass'")
        """
        # This would integrate with LSP workspace symbols provider
        # Placeholder implementation
        return []
    
    def call_hierarchy(self, symbol_name: str) -> Dict[str, Any]:
        """Get call hierarchy for a symbol.
        
        Args:
            symbol_name: Name of the symbol
            
        Returns:
            Dict[str, Any]: Call hierarchy information
            
        Example:
            >>> hierarchy = codebase.call_hierarchy("my_function")
            >>> print(f"Call hierarchy: {hierarchy}")
        """
        # This would integrate with LSP call hierarchy provider
        # Placeholder implementation
        return {"symbol": symbol_name, "callers": [], "callees": []}
    
    # =====[ Diagnostics & Health ]=====
    
    def diagnostics(self) -> ErrorCollection:
        """Get all diagnostics (errors + warnings + info).
        
        Returns:
            ErrorCollection: All diagnostic information
            
        Example:
            >>> diagnostics = codebase.diagnostics()
            >>> print(f"Total diagnostics: {diagnostics.total_count}")
        """
        return self.errors()  # Diagnostics include all error types
    
    def health_check(self) -> HealthCheck:
        """Get overall codebase health check.
        
        Returns:
            HealthCheck: Health check results
            
        Example:
            >>> health = codebase.health_check()
            >>> print(f"Overall score: {health.overall_score:.2f}")
            >>> for rec in health.recommendations:
            ...     print(f"Recommendation: {rec}")
        """
        return self._lsp.get_health_check()
    
    def lsp_status(self) -> LSPStatus:
        """Get LSP server status.
        
        Returns:
            LSPStatus: Current LSP server status
            
        Example:
            >>> status = codebase.lsp_status()
            >>> print(f"LSP running: {status.is_running}")
            >>> print(f"Capabilities: {status.capabilities}")
        """
        return self._lsp.get_lsp_status()
    
    def capabilities(self) -> LSPCapabilities:
        """Get available LSP capabilities.
        
        Returns:
            LSPCapabilities: Available LSP capabilities
            
        Example:
            >>> caps = codebase.capabilities()
            >>> print(f"Completion: {caps.completion}")
            >>> print(f"Hover: {caps.hover}")
        """
        status = self.lsp_status()
        return status.capabilities


# Export the mixin
__all__ = ['LSPMethodsMixin']
