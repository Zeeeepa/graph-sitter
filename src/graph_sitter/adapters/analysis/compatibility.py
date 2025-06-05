"""
Backward compatibility functions for legacy codebase analysis.

This module maintains the original analysis functions to ensure
backward compatibility while the system transitions to the new
modular architecture.
"""

from typing import Optional

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_resolution import Import
from graph_sitter.enums import EdgeType, SymbolType

from .db_integrated_analysis import CodebaseDBAdapter


def get_codebase_summary(codebase: Codebase) -> str:
    """
    Legacy codebase summary function.
    
    Provides the original codebase summary format for backward compatibility.
    """
    node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
    edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
    """

    return f"{node_summary}\n{edge_summary}"


def get_file_summary(file: SourceFile) -> str:
    """
    Legacy file summary function.
    
    Provides the original file summary format for backward compatibility.
    """
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""


def get_class_summary(cls: Class) -> str:
    """
    Legacy class summary function.
    
    Provides the original class summary format for backward compatibility.
    """
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
    """
    Legacy function summary function.
    
    Provides the original function summary format for backward compatibility.
    """
    return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """


def get_symbol_summary(symbol: Symbol) -> str:
    """
    Legacy symbol summary function.
    
    Provides the original symbol summary format for backward compatibility.
    """
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

    return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
    """


def get_codebase_summary_enhanced(codebase: Codebase, 
                                 db_adapter: Optional[CodebaseDBAdapter] = None) -> str:
    """
    Enhanced version of get_codebase_summary with optional database integration.
    
    This function maintains backward compatibility while providing enhanced features
    when a database adapter is provided.
    
    Args:
        codebase: Codebase to analyze
        db_adapter: Optional database adapter for enhanced features
        
    Returns:
        Codebase summary string (enhanced if db_adapter provided)
    """
    # Always provide the original functionality
    original_summary = get_codebase_summary(codebase)
    
    # If database adapter is provided, enhance with additional information
    if db_adapter:
        try:
            enhanced_result = db_adapter.analyze_codebase_enhanced(codebase)
            return f"{original_summary}\n\nEnhanced Analysis:\n" \
                   f"Quality Score: {enhanced_result.quality_score}/100\n" \
                   f"Issues Found: {len(enhanced_result.issues)}\n" \
                   f"Recommendations: {len(enhanced_result.recommendations)}"
        except Exception as e:
            # Fallback to original functionality if enhancement fails
            print(f"Enhanced analysis failed, using original: {e}")
            return original_summary
    
    return original_summary

