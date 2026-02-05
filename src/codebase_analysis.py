"""
Graph-Sitter Codebase Analysis - Main Orchestrator
===================================================

This module consolidates and orchestrates codebase analysis functionality from:
- graph_sitter_backend.py
- graph_sitter_analysis.py  
- analysisbig.py
- analysis.py

It provides a unified public API for comprehensive codebase analysis.
"""

# Standard library imports
from typing import Dict, List, Any, Union

# Core imports from consolidated modules
# NOTE: Don't import autogenlib_adapter here - causes circular dependency
# autogenlib_adapter imports from graph_sitter_analysis which may import from here
from lsp_adapter import *
from graph_sitter_tools_adapter import *

# Core graph-sitter SDK imports
from graph_sitter import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol

# Standard library
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================================
# CODEBASE SUMMARY FUNCTIONS
# ============================================================================

def get_codebase_summary(codebase: Codebase) -> str:
    """
    Generate a comprehensive summary of the entire codebase.
    
    Args:
        codebase: The Codebase object to analyze
        
    Returns:
        String containing formatted codebase summary
    """
    files = list(codebase.files)
    imports = list(codebase.imports)
    external_modules = list(codebase.external_modules)
    symbols = list(codebase.symbols)
    classes = list(codebase.classes)
    functions = list(codebase.functions)
    global_vars = list(codebase.global_vars)
    
    # Calculate edges
    symbol_edges = sum(len(list(s.usages)) for s in symbols if hasattr(s, 'usages'))
    import_edges = len(imports)
    
    summary = f"""Contains {len(symbols)} nodes
- {len(files)} files
- {len(imports)} imports
- {len(external_modules)} external_modules
- {len(symbols)} symbols
\t- {len(classes)} classes
\t- {len(functions)} functions
\t- {len(global_vars)} global_vars
\t- 0 interfaces

Contains {symbol_edges + import_edges} edges
- {symbol_edges} symbol -> used symbol
- {import_edges} import -> used symbol
- 0 export -> exported symbol
    """
    return summary


def get_file_summary(file) -> str:
    """
    Generate summary for a single file.
    
    Args:
        file: SourceFile object to summarize
        
    Returns:
        String containing formatted file summary
    """
    interfaces_count = len(file.interfaces) if hasattr(file, 'interfaces') else 0
    
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(list(file.imports))} imports
- {len(list(file.symbols))} symbol references
\t- {len(list(file.classes))} classes
\t- {len(list(file.functions))} functions
\t- {len(list(file.global_vars))} global variables
\t- {interfaces_count} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(list(file.imports))} importers
"""


def get_class_summary(cls) -> str:
    """
    Generate summary for a single class.
    
    Args:
        cls: Class object to summarize
        
    Returns:
        String containing formatted class summary
    """
    usages = list(cls.usages) if hasattr(cls, 'usages') else []
    
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_classes if hasattr(cls, 'parent_classes') else []}
- {len(list(cls.methods)) if hasattr(cls, 'methods') else 0} methods
- {len(list(cls.attributes)) if hasattr(cls, 'attributes') else 0} attributes
- 0 decorators
- 0 dependencies

==== [ `{cls.name}` (PyClass) Usage Summary ] ====
- {len(usages)} usages
"""


def get_function_summary(func) -> str:
    """
    Generate summary for a single function.
    
    Args:
        func: Function object to summarize
        
    Returns:
        String containing formatted function summary
    """
    usages = list(func.usages) if hasattr(func, 'usages') else []
    
    return f"""==== [ `{func.name}` (Function) Summary ] ====
- {len(list(func.parameters)) if hasattr(func, 'parameters') else 0} parameters
- {len(usages)} usages
- File: {func.file.path if hasattr(func, 'file') else 'unknown'}
"""


def get_symbol_summary(symbol) -> str:
    """
    Generate summary for a generic symbol.
    
    Args:
        symbol: Symbol object to summarize
        
    Returns:
        String containing formatted symbol summary
    """
    usages = list(symbol.usages) if hasattr(symbol, 'usages') else []
    
    return f"""==== [ `{symbol.name}` (Symbol) Summary ] ====
- Type: {type(symbol).__name__}
- {len(usages)} usages
- File: {symbol.file.path if hasattr(symbol, 'file') else 'unknown'}
"""


# ============================================================================
# DEAD CODE DETECTION
# ============================================================================

def find_dead_code(codebase: Codebase) -> Dict[str, List]:
    """
    Find potentially dead code (unused functions and classes).
    
    Args:
        codebase: The Codebase object to analyze
        
    Returns:
        Dictionary with 'functions' and 'classes' keys containing dead code lists
    """
    dead_functions = []
    dead_classes = []
    
    for func in codebase.functions:
        try:
            if hasattr(func, 'usages') and len(list(func.usages)) == 0:
                dead_functions.append({
                    'name': func.name,
                    'file': str(func.file.path),
                    'line': func.start_line if hasattr(func, 'start_line') else 0
                })
        except:
            pass
    
    for cls in codebase.classes:
        try:
            if hasattr(cls, 'usages') and len(list(cls.usages)) == 0:
                dead_classes.append({
                    'name': cls.name,
                    'file': str(cls.file.path),
                    'line': cls.start_line if hasattr(cls, 'start_line') else 0
                })
        except:
            pass
    
    return {
        'functions': dead_functions,
        'classes': dead_classes
    }


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

def analyze_codebase(path: Union[str, Codebase], language: str = "python") -> Dict[str, Any]:
    """
    Perform comprehensive analysis of a codebase.
    
    Args:
        path: Path to the codebase or Codebase object
        language: Programming language (default: "python")
        
    Returns:
        Dictionary containing complete analysis results
    """
    if isinstance(path, Codebase):
        codebase = path
    else:
        codebase = Codebase(path, language=language)
    
    results = {
        'summary': get_codebase_summary(codebase),
        'files_count': len(list(codebase.files)),
        'functions_count': len(list(codebase.functions)),
        'classes_count': len(list(codebase.classes)),
        'symbols_count': len(list(codebase.symbols)),
        'dead_code': find_dead_code(codebase)
    }
    
    return results


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Summary functions
    'get_codebase_summary',
    'get_file_summary',
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    # Analysis functions
    'analyze_codebase',
    'find_dead_code',
    # Core types (re-exported)
    'Codebase',
    'Symbol',
    'Import',
    'ExternalModule',
]

print("codebase_analysis loaded - main orchestrator with consolidated functionality")
