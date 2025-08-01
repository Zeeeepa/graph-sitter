"""
Graph-Sitter Codebase Module

This module provides the main Codebase class with full Serena integration.
When importing from this module, all Serena code quality context and intelligence
features are automatically available.
"""

# Import the main Codebase class first
from graph_sitter.core.codebase import Codebase

# Then ensure Serena integration is loaded
try:
    from graph_sitter.extensions.serena.auto_init import ensure_serena_initialized
    _initialized = ensure_serena_initialized(Codebase)
    if _initialized:
        # Import Serena components for convenience
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
        
        # Make all Serena components available
        __all__ = [
            'Codebase',
            'SerenaCore',
            'SerenaConfig', 
            'SerenaCapability',
            'RefactoringType',
            'RefactoringResult',
            'CodeGenerationResult',
            'SemanticSearchResult',
            'SymbolInfo'
        ]
        
        # Verify comprehensive LSP methods are available on Codebase
        _comprehensive_lsp_methods = [
            # Core Error Retrieval Commands
            'errors', 'errors_by_file', 'errors_by_severity', 'errors_by_type', 'recent_errors',
            # Detailed Error Context
            'full_error_context', 'error_suggestions', 'error_related_symbols', 'error_impact_analysis',
            # Error Statistics & Analysis
            'error_summary', 'error_trends', 'most_common_errors', 'error_hotspots',
            # Real-time Error Monitoring
            'watch_errors', 'error_stream', 'refresh_errors',
            # Error Resolution & Actions
            'auto_fix_errors', 'get_quick_fixes', 'apply_error_fix',
            # Full Serena LSP Feature Retrieval
            'completions', 'hover_info', 'signature_help', 'definitions', 'references',
            # Code Actions & Refactoring
            'code_actions', 'rename_symbol', 'extract_method', 'organize_imports',
            # Semantic Analysis
            'semantic_tokens', 'document_symbols', 'workspace_symbols', 'call_hierarchy',
            # Diagnostics & Health
            'diagnostics', 'health_check', 'lsp_status', 'capabilities'
        ]
        
        # Legacy Serena methods for backward compatibility
        _legacy_serena_methods = [
            'get_serena_status', 'shutdown_serena', 'get_completions',
            'get_hover_info', 'get_signature_help', 'extract_variable', 'get_code_actions',
            'apply_code_action', 'generate_boilerplate',
            'generate_tests', 'generate_documentation', 'semantic_search',
            'find_code_patterns', 'find_similar_code', 'get_symbol_context',
            'analyze_symbol_impact', 'enable_realtime_analysis', 
            'disable_realtime_analysis'
        ]
        
    else:
        __all__ = ['Codebase']
        
except ImportError as e:
    # Serena not available
    __all__ = ['Codebase']

# Log available methods for debugging
try:
    if _initialized:
        from graph_sitter.shared.logging.get_logger import get_logger
        logger = get_logger(__name__)
        
        # Check comprehensive LSP methods availability
        available_lsp_methods = [method for method in _comprehensive_lsp_methods if hasattr(Codebase, method)]
        logger.debug(f"Comprehensive LSP API loaded: {len(available_lsp_methods)}/{len(_comprehensive_lsp_methods)} methods available")
        
        # Check legacy Serena methods availability
        available_legacy_methods = [method for method in _legacy_serena_methods if hasattr(Codebase, method)]
        logger.debug(f"Legacy Serena methods: {len(available_legacy_methods)}/{len(_legacy_serena_methods)} methods available")
        
        if len(available_lsp_methods) == len(_comprehensive_lsp_methods):
            logger.info("✅ Full Comprehensive LSP Error Retrieval API available via Codebase import")
            logger.info("🎯 All Serena LSP features easily retrievable directly from codebase object")
        else:
            missing_lsp = set(_comprehensive_lsp_methods) - set(available_lsp_methods)
            logger.warning(f"⚠️  Some LSP methods not available: {missing_lsp}")
        
        if len(available_legacy_methods) > 0:
            logger.info(f"✅ {len(available_legacy_methods)} legacy Serena methods available for backward compatibility")
except:
    # Ignore logging errors
    pass
