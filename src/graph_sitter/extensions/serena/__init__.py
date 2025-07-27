"""
Serena Extension for Graph-Sitter

This extension provides comprehensive error analysis, code intelligence, semantic search, 
and real-time analysis capabilities through integration with existing graph-sitter and 
Serena components.

Main Features:
- Comprehensive error detection and context analysis
- Function call chain mapping (callers and callees)
- Parameter usage analysis (unused, wrong types)
- Dependency tracking and analysis
- Symbol relationship mapping
- Real-time error context with fix suggestions

Usage:
    from graph_sitter.extensions.serena import (
        SerenaAPI,
        ComprehensiveErrorAnalyzer,
        ErrorContext,
        get_codebase_error_analysis,
        analyze_file_errors,
        find_function_relationships
    )
    
    # Create API instance
    api = SerenaAPI(codebase)
    
    # Get all errors with context
    errors_with_context = api.get_all_errors_with_context()
    
    # Get error context for specific location
    context = api.get_error_context(file_path, line_number)
    
    # Find unused parameters
    unused_params = api.get_unused_parameters()
    
    # Get function relationships
    relationships = find_function_relationships(codebase, "function_name")
"""

# Core components
from .core import SerenaCore
from .serena_types import SerenaConfig, SerenaCapability, RefactoringType, RefactoringResult, CodeGenerationResult, SemanticSearchResult, SymbolInfo

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

# Existing components (maintained for compatibility)
from .intelligence import CodeIntelligence
from .refactoring import RefactoringEngine
from .actions import CodeActions
from .generation import CodeGenerator
from .search import SemanticSearch
from .realtime import RealtimeAnalyzer
from .symbols import SymbolIntelligence

__all__ = [
    # Core components
    'SerenaCore',
    'SerenaConfig',
    'SerenaCapability',
    'RefactoringType',
    'RefactoringResult',
    'CodeGenerationResult',
    'SemanticSearchResult',
    'SymbolInfo',
    
    # Error analysis system (NEW - Main focus)
    'ComprehensiveErrorAnalyzer',
    'ErrorContext',
    'ParameterIssue',
    'FunctionCallInfo',
    'analyze_codebase_errors',
    'get_instant_error_context',
    'get_all_codebase_errors_with_context',
    
    # Main API interface (NEW - Easy access)
    'SerenaAPI',
    'create_serena_api',
    'get_codebase_error_analysis',
    'analyze_file_errors',
    'find_function_relationships',
    
    # Advanced API (NEW - Comprehensive integration)
    'SerenaAdvancedAPI',
    'create_advanced_serena_api',
    'quick_error_analysis',
    'quick_knowledge_extraction',
    
    # Advanced components
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
    
    # MCP and semantic tools
    'SerenaMCPBridge',
    'MCPToolResult',
    'SemanticTools',
    
    # LSP Integration (NEW - Real-time server communication)
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
    
    # Existing components (maintained for compatibility)
    'CodeIntelligence', 
    'RefactoringEngine',
    'CodeActions',
    'CodeGenerator',
    'SemanticSearch',
    'RealtimeAnalyzer',
    'SymbolIntelligence'
]

__version__ = "2.0.0"
