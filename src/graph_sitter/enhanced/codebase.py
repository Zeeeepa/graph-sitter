"""
Graph-Sitter Codebase Module

This module provides the main Codebase class with full Serena integration.
When importing from this module, all Serena code quality context and intelligence
features are automatically available.
"""

# Import the main Codebase class first
from graph_sitter.core.codebase import Codebase

# Then ensure Serena integration is loaded (now from LSP extension)
try:
    from graph_sitter.extensions.lsp.serena.auto_init import ensure_serena_initialized
    _initialized = ensure_serena_initialized(Codebase)
    if _initialized:
        # Import Serena components for convenience (now from LSP extension)
        from graph_sitter.extensions.lsp.serena import (
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
        
        # Verify Serena methods are available on Codebase
        _serena_methods = [
            'get_serena_status', 'shutdown_serena', 'get_completions',
            'get_hover_info', 'get_signature_help', 'rename_symbol',
            'extract_method', 'extract_variable', 'get_code_actions',
            'apply_code_action', 'organize_imports', 'generate_boilerplate',
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
        
        _serena_methods = [
            'get_serena_status', 'shutdown_serena', 'get_completions',
            'get_hover_info', 'get_signature_help', 'rename_symbol',
            'extract_method', 'extract_variable', 'get_code_actions',
            'apply_code_action', 'organize_imports', 'generate_boilerplate',
            'generate_tests', 'generate_documentation', 'semantic_search',
            'find_code_patterns', 'find_similar_code', 'get_symbol_context',
            'analyze_symbol_impact', 'enable_realtime_analysis', 
            'disable_realtime_analysis'
        ]
        
        available_methods = [method for method in _serena_methods if hasattr(Codebase, method)]
        logger.debug(f"Serena integration loaded: {len(available_methods)}/{len(_serena_methods)} methods available")
        
        if len(available_methods) == len(_serena_methods):
            logger.info("✅ Full Serena code quality context available via Codebase import")
        else:
            missing = set(_serena_methods) - set(available_methods)
            logger.warning(f"⚠️  Some Serena methods not available: {missing}")
except:
    # Ignore logging errors
    pass
