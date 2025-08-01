"""
Graph-Sitter Enhanced Codebase Module

This module provides the main Codebase class with full LSP and Serena integration.
When importing from this module, all LSP error retrieval and code intelligence
features are automatically available directly on the codebase object.
"""

# Import the main Codebase class and LSP methods
from graph_sitter.core.codebase import Codebase as BaseCodebase
from graph_sitter.core.lsp_methods import LSPMethodsMixin
from graph_sitter.core.lsp_types import (
    ErrorInfo, ErrorCollection, ErrorSummary, ErrorContext, QuickFix,
    CompletionItem, HoverInfo, SignatureHelp, SymbolInfo, LSPCapabilities,
    LSPStatus, HealthCheck, ErrorSeverity, ErrorType, Position, Range
)

# Create enhanced Codebase class with LSP methods
class Codebase(LSPMethodsMixin, BaseCodebase):
    """
    Enhanced Codebase class with full LSP error retrieval and code intelligence.
    
    This class provides all the standard Codebase functionality plus:
    - Complete LSP error retrieval API
    - Real-time error monitoring
    - Code intelligence features (completions, hover, definitions, etc.)
    - Code actions and refactoring capabilities
    - Semantic analysis and symbol navigation
    - Health monitoring and diagnostics
    
    Example:
        >>> from graph_sitter.enhanced import Codebase
        >>> codebase = Codebase("./my-project")
        >>> 
        >>> # Get all errors
        >>> errors = codebase.errors()
        >>> print(f"Found {len(errors.errors)} errors")
        >>> 
        >>> # Get error context
        >>> if errors.errors:
        ...     context = codebase.full_error_context(errors.errors[0].id)
        ...     print(f"Error: {context.error.message}")
        >>> 
        >>> # Monitor errors in real-time
        >>> def on_error_change(error_collection):
        ...     print(f"Errors updated: {len(error_collection.errors)}")
        >>> codebase.watch_errors(on_error_change)
        >>> 
        >>> # Get health check
        >>> health = codebase.health_check()
        >>> print(f"Codebase health score: {health.overall_score:.2f}")
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced codebase with LSP integration."""
        super().__init__(*args, **kwargs)
        
        # Log successful initialization
        from graph_sitter.shared.logging.get_logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Enhanced Codebase initialized with LSP integration for {self.repo_path}")

# Try to load Serena integration for backward compatibility
try:
    from graph_sitter.extensions.serena.auto_init import ensure_serena_initialized
    _serena_initialized = ensure_serena_initialized(Codebase)
    if _serena_initialized:
        # Import Serena components for convenience
        from graph_sitter.extensions.serena import (
            SerenaCore, 
            SerenaConfig, 
            SerenaCapability,
            RefactoringType,
            RefactoringResult,
            CodeGenerationResult,
            SemanticSearchResult
        )
        
        # Add Serena components to exports
        _serena_exports = [
            'SerenaCore', 'SerenaConfig', 'SerenaCapability',
            'RefactoringType', 'RefactoringResult', 'CodeGenerationResult',
            'SemanticSearchResult'
        ]
    else:
        _serena_exports = []
        
except ImportError as e:
    # Serena not available, but LSP functionality still works
    from graph_sitter.shared.logging.get_logger import get_logger
    logger = get_logger(__name__)
    logger.info("Serena integration not available, using LSP-only mode")
    _serena_exports = []

# Make all components available
__all__ = [
    # Core enhanced codebase
    'Codebase',
    
    # LSP types for direct use
    'ErrorInfo', 'ErrorCollection', 'ErrorSummary', 'ErrorContext', 'QuickFix',
    'CompletionItem', 'HoverInfo', 'SignatureHelp', 'SymbolInfo', 
    'LSPCapabilities', 'LSPStatus', 'HealthCheck', 
    'ErrorSeverity', 'ErrorType', 'Position', 'Range'
] + _serena_exports

# Verify LSP methods are available on Codebase
_lsp_methods = [
    # Core error retrieval
    'errors', 'full_error_context', 'errors_by_file', 'errors_by_severity',
    'errors_by_type', 'recent_errors',
    
    # Error context and analysis
    'error_suggestions', 'error_related_symbols', 'error_impact_analysis',
    'error_summary', 'error_trends', 'most_common_errors', 'error_hotspots',
    
    # Real-time monitoring
    'watch_errors', 'unwatch_errors', 'error_stream', 'refresh_errors',
    
    # Error resolution
    'auto_fix_errors', 'get_quick_fixes', 'apply_error_fix',
    
    # Code intelligence
    'completions', 'hover_info', 'signature_help', 'definitions', 'references',
    
    # Code actions and refactoring
    'code_actions', 'rename_symbol', 'extract_method', 'organize_imports',
    
    # Semantic analysis
    'semantic_tokens', 'document_symbols', 'workspace_symbols', 'call_hierarchy',
    
    # Health and diagnostics
    'diagnostics', 'health_check', 'lsp_status', 'capabilities'
]

# Verify all methods are available (for development/debugging)
def _verify_lsp_methods():
    """Verify that all LSP methods are available on the Codebase class."""
    missing_methods = []
    for method_name in _lsp_methods:
        if not hasattr(Codebase, method_name):
            missing_methods.append(method_name)
    
    if missing_methods:
        from graph_sitter.shared.logging.get_logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Missing LSP methods on Codebase: {missing_methods}")
    
    return len(missing_methods) == 0

# Verify methods are available
_all_methods_available = _verify_lsp_methods()
