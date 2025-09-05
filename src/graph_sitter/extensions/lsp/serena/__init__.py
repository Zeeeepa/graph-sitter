"""
Enhanced Serena Extension for Graph-Sitter

This extension provides comprehensive code intelligence with advanced LSP integration,
including error analysis, refactoring, symbol intelligence, code actions, and real-time analysis.

Main Features:
- Advanced LSP integration with multiple server support
- Comprehensive refactoring operations (rename, extract, inline, move)
- Symbol intelligence with relationship tracking and impact analysis
- Code actions and quick fixes with LSP protocol compliance
- Real-time file monitoring and incremental analysis
- Comprehensive error detection and context analysis
- Function call chain mapping (callers and callees)
- Parameter usage analysis (unused, wrong types)
- Dependency tracking and analysis
- Symbol relationship mapping
- Real-time error context with fix suggestions

Usage:
    from graph_sitter.extensions.serena import (
        SerenaCore,
        SerenaLSPIntegration,
        create_serena_lsp_integration,
        SerenaConfig,
        SerenaCapability
    )
    
    # Create enhanced LSP integration
    integration = await create_serena_lsp_integration(
        codebase_path="/path/to/codebase"
    )
    
    # Get comprehensive diagnostics
    diagnostics = await integration.get_all_diagnostics()
    
    # Perform refactoring
    result = await integration.perform_refactoring(
        'rename',
        file_path='example.py',
        line=10,
        character=5,
        new_name='new_function_name'
    )
    
    # Get enhanced completions
    completions = await integration.get_completions_enhanced(
        'example.py', 15, 10
    )
    
    # Get symbol information
    symbol_info = await integration.get_symbol_info_enhanced('MyClass')
"""

# Core components
from .core import SerenaCore, get_or_create_core, create_core
from .types import (
    SerenaConfig, 
    SerenaCapability, 
    RefactoringType, 
    RefactoringResult, 
    RefactoringChange,
    RefactoringConflict,
    SymbolInfo,
    CodeAction,
    CodeGenerationResult, 
    SemanticSearchResult,
    HoverInfo,
    CompletionItem,
    AnalysisContext
)

# Error analysis system (NEW - Main focus)
from .error_analysis import (
    ComprehensiveErrorAnalyzer,
    ErrorContext,
    ParameterIssue,
    FunctionCallInfo,
    analyze_codebase_errors,
    get_instant_error_context,
    get_all_codebase_errors_with_context
)

# Main API interface (NEW - Easy access)
from .api import (
    SerenaAPI,
    create_serena_api,
    get_codebase_error_analysis,
    analyze_file_errors,
    find_function_relationships
)

# Advanced components
try:
    from .knowledge_integration import (
        AdvancedKnowledgeIntegration,
        KnowledgeContext,
        KnowledgeGraph,
        AdvancedErrorContext
    )
except ImportError:
    # Fallback if advanced components are not available
    pass

try:
    from .advanced_context import (
        AdvancedContextEngine,
        ContextualError,
        ContextualInsight
    )
except ImportError:
    pass

try:
    from .advanced_error_viewer import (
        AdvancedErrorViewer,
        ErrorViewConfig,
        ErrorCluster,
        ErrorVisualization
    )
except ImportError:
    pass

# MCP and semantic tools
from .mcp_bridge import SerenaMCPBridge, MCPToolResult
from .semantic_tools import SemanticTools

# LSP Integration (NEW - Real-time server communication)
try:
    from .lsp_integration import (
        SerenaLSPIntegration,
        create_serena_lsp_integration,
        get_comprehensive_code_errors,
        analyze_file_errors as lsp_analyze_file_errors
    )
    
    from .lsp import (
        SerenaLSPClient,
        SerenaServerManager,
        ServerConfig,
        ErrorRetriever,
        ComprehensiveErrorList,
        CodeError,
        RealTimeDiagnostics,
        DiagnosticFilter,
        DiagnosticStats,
        ConnectionType
    )
    
    LSP_AVAILABLE = True
except ImportError:
    # LSP integration not available
    LSP_AVAILABLE = False

# Advanced Serena components (NEW - Enhanced capabilities)
try:
    from .refactoring import RefactoringEngine
    from .refactoring.refactoring_engine import RefactoringConfig
    from .refactoring.rename_refactor import RenameRefactor
    from .refactoring.extract_refactor import ExtractRefactor
    from .refactoring.inline_refactor import InlineRefactor
    from .refactoring.move_refactor import MoveRefactor
    REFACTORING_AVAILABLE = True
except ImportError:
    REFACTORING_AVAILABLE = False

try:
    from .symbols import SymbolIntelligence
    SYMBOL_INTELLIGENCE_AVAILABLE = True
except ImportError:
    SYMBOL_INTELLIGENCE_AVAILABLE = False

try:
    from .actions import CodeActions
    CODE_ACTIONS_AVAILABLE = True
except ImportError:
    CODE_ACTIONS_AVAILABLE = False

try:
    from .realtime import RealtimeAnalyzer
    REALTIME_ANALYSIS_AVAILABLE = True
except ImportError:
    REALTIME_ANALYSIS_AVAILABLE = False

# Auto-initialization (NEW - Seamless integration)
try:
    from .auto_init import initialize_serena_integration, add_serena_to_codebase
    AUTO_INIT_AVAILABLE = True
except ImportError:
    AUTO_INIT_AVAILABLE = False

# Existing components (maintained for compatibility)
try:
    from .intelligence import CodeIntelligence
    from .generation import CodeGenerator
    from .search import SemanticSearch
except ImportError:
    # Legacy components may not be available
    pass

__all__ = [
    # Core components (NEW - Enhanced)
    'SerenaCore',
    'get_or_create_core',
    'create_core',
    'SerenaConfig',
    'SerenaCapability',
    'RefactoringType',
    'RefactoringResult',
    'RefactoringChange',
    'RefactoringConflict',
    'SymbolInfo',
    'CodeAction',
    'CodeGenerationResult',
    'SemanticSearchResult',
    'HoverInfo',
    'CompletionItem',
    'AnalysisContext',
    
    # Enhanced LSP Integration (NEW - Advanced capabilities)
    'SerenaLSPIntegration',
    'create_serena_lsp_integration', 
    'get_comprehensive_code_errors',
    'lsp_analyze_file_errors',
    'SerenaLSPClient',
    'SerenaServerManager',
    'ServerConfig',
    'ErrorRetriever',
    'ComprehensiveErrorList',
    'CodeError',
    'RealTimeDiagnostics',
    'DiagnosticFilter',
    'DiagnosticStats',
    'ConnectionType',
    'LSP_AVAILABLE',
    
    # Advanced Refactoring System (NEW)
    'RefactoringEngine',
    'RefactoringConfig',
    'RenameRefactor',
    'ExtractRefactor',
    'InlineRefactor',
    'MoveRefactor',
    'REFACTORING_AVAILABLE',
    
    # Symbol Intelligence (NEW)
    'SymbolIntelligence',
    'SYMBOL_INTELLIGENCE_AVAILABLE',
    
    # Code Actions (NEW)
    'CodeActions',
    'CODE_ACTIONS_AVAILABLE',
    
    # Real-time Analysis (NEW)
    'RealtimeAnalyzer',
    'REALTIME_ANALYSIS_AVAILABLE',
    
    # Auto-initialization (NEW)
    'initialize_serena_integration',
    'add_serena_to_codebase',
    'AUTO_INIT_AVAILABLE',
    
    # Error analysis system (Existing - Enhanced)
    'ComprehensiveErrorAnalyzer',
    'ErrorContext',
    'ParameterIssue',
    'FunctionCallInfo',
    'analyze_codebase_errors',
    'get_instant_error_context',
    'get_all_codebase_errors_with_context',
    
    # Main API interface (Existing - Enhanced)
    'SerenaAPI',
    'create_serena_api',
    'get_codebase_error_analysis',
    'analyze_file_errors',
    'find_function_relationships',
    
    # Advanced API (Existing)
    'SerenaAdvancedAPI',
    'create_advanced_serena_api',
    'quick_error_analysis',
    'quick_knowledge_extraction',
    
    # Advanced components (Existing)
    'AdvancedKnowledgeIntegration',
    'KnowledgeContext',
    'KnowledgeGraph',
    'AdvancedErrorContext',
    'AdvancedContextEngine',
    'ContextualError',
    'ContextualInsight',
    'AdvancedErrorViewer',
    'ErrorViewConfig',
    'ErrorCluster',
    'ErrorVisualization',
    
    # MCP and semantic tools (Existing)
    'SerenaMCPBridge',
    'MCPToolResult',
    'SemanticTools',
    
    # Legacy components (Maintained for compatibility)
    'CodeIntelligence', 
    'CodeGenerator',
    'SemanticSearch'
]

__version__ = "2.0.0"
