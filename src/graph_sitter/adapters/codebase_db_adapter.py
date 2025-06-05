"""
Codebase Database Adapter for Enhanced Analysis Integration

This adapter provides seamless integration between the existing 
graph_sitter/codebase/codebase_analysis.py functionality and the new 
comprehensive database schema.

This module now serves as a clean interface that coordinates functionality
from the refactored analysis modules while maintaining backward compatibility.
"""

# Backward compatibility imports - maintain existing interface
from .analysis.compatibility import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    get_codebase_summary_enhanced
)

# Enhanced functionality imports
from .analysis.db_integrated_analysis import (
    CodebaseDBAdapter,
    create_enhanced_analyzer
)

from .analysis.database_utils import (
    AnalysisResult,
    DatabaseMetrics,
    convert_rset_to_dicts,
    execute_query_with_rset_conversion
)

from .analysis.metrics import (
    EnhancedCodebaseMetrics,
    CodebaseMetrics
)

# Re-export for backward compatibility
__all__ = [
    # Legacy compatibility functions
    'get_codebase_summary',
    'get_file_summary', 
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    'get_codebase_summary_enhanced',
    
    # Enhanced functionality
    'CodebaseDBAdapter',
    'create_enhanced_analyzer',
    'AnalysisResult',
    'DatabaseMetrics',
    'EnhancedCodebaseMetrics',
    'CodebaseMetrics',
    
    # Database utilities
    'convert_rset_to_dicts',
    'execute_query_with_rset_conversion'
]

# Maintain backward compatibility aliases
_convert_rset_to_dicts = convert_rset_to_dicts
_execute_query_with_rset_conversion = execute_query_with_rset_conversion

