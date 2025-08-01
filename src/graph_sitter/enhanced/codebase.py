"""
Graph-Sitter Enhanced Codebase Module

This module provides the main Codebase class with full Serena integration and
unified error handling capabilities. The core error methods are now directly
available on the Codebase class:

- codebase.errors(): Get all errors in the codebase
- codebase.full_error_context(error_id): Get comprehensive context for specific error
- codebase.resolve_errors(): Auto-fix all errors
- codebase.resolve_error(error_id): Auto-fix specific error

Features:
✅ Unified Interface: All methods available directly on Codebase class
⚡ Lazy Loading: LSP features initialized only when first accessed
🔄 Consistent Return Types: Standardized error/result objects
🛡️ Graceful Error Handling: Proper fallbacks when LSP unavailable
🚀 Performance: Efficient caching and batching of LSP requests
"""

# Import the main Codebase class with integrated error handling
from graph_sitter.core.codebase import Codebase

# Import Serena analysis components
try:
    from graph_sitter.analysis.serena_analysis import (
        SerenaAnalyzer,
        LSPDiagnostic,
        ErrorContext,
        SymbolOverview,
        CodebaseHealth
    )
    SERENA_AVAILABLE = True
except ImportError:
    SERENA_AVAILABLE = False

# Import legacy Serena components for backward compatibility
try:
    from graph_sitter.extensions.serena.auto_init import ensure_serena_initialized
    _legacy_initialized = ensure_serena_initialized(Codebase)
    
    if _legacy_initialized:
        # Import legacy Serena components for compatibility
        from graph_sitter.extensions.serena import (
            SerenaCore, 
            SerenaConfig, 
            SerenaCapability,
            RefactoringType,
            RefactoringResult,
            CodeGenerationResult,
            SemanticSearchResult,
            SymbolInfo
        )
        LEGACY_SERENA_AVAILABLE = True
    else:
        LEGACY_SERENA_AVAILABLE = False
        
except ImportError:
    LEGACY_SERENA_AVAILABLE = False

# Define what's available for import
if SERENA_AVAILABLE:
    __all__ = [
        'Codebase',
        'SerenaAnalyzer',
        'LSPDiagnostic',
        'ErrorContext',
        'SymbolOverview',
        'CodebaseHealth'
    ]
    
    if LEGACY_SERENA_AVAILABLE:
        __all__.extend([
            'SerenaCore',
            'SerenaConfig', 
            'SerenaCapability',
            'RefactoringType',
            'RefactoringResult',
            'CodeGenerationResult',
            'SemanticSearchResult',
            'SymbolInfo'
        ])
else:
    __all__ = ['Codebase']

# Log available capabilities
try:
    from graph_sitter.shared.logging.get_logger import get_logger
    logger = get_logger(__name__)
    
    # Check core error methods
    core_error_methods = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error']
    available_error_methods = [method for method in core_error_methods if hasattr(Codebase, method)]
    
    if len(available_error_methods) == len(core_error_methods):
        logger.info("✅ Core Serena error handling methods available on Codebase class")
        logger.info("🚀 Available: codebase.errors(), codebase.full_error_context(), codebase.resolve_errors(), codebase.resolve_error()")
    else:
        missing = set(core_error_methods) - set(available_error_methods)
        logger.warning(f"⚠️  Some core error methods not available: {missing}")
    
    # Check Serena analyzer availability
    if SERENA_AVAILABLE:
        logger.info("✅ Serena analyzer available for comprehensive codebase analysis")
    else:
        logger.warning("⚠️  Serena analyzer not available - install Serena dependencies")
    
    # Check legacy Serena compatibility
    if LEGACY_SERENA_AVAILABLE:
        legacy_methods = [
            'get_serena_status', 'shutdown_serena', 'get_completions',
            'get_hover_info', 'get_signature_help', 'rename_symbol',
            'extract_method', 'semantic_search', 'generate_boilerplate'
        ]
        available_legacy = [method for method in legacy_methods if hasattr(Codebase, method)]
        logger.info(f"✅ Legacy Serena compatibility: {len(available_legacy)}/{len(legacy_methods)} methods available")
    
except Exception:
    # Ignore logging errors
    pass
