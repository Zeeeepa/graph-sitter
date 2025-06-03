"""
Contexten Integrations Module

This module provides integration adapters and unified interfaces
for connecting all Contexten components and external systems.
"""

from .codebase_adapter import (
    CodebaseAdapter,
    AnalysisRequest,
    AnalysisResult,
    quick_analyze,
    analyze_specific_files
)
from .database_adapter import (
    DatabaseAdapter,
    DatabaseConfig,
    DatabaseConnectionError,
    DatabaseOperationError
)
from .unified_api import (
    UnifiedAPI,
    APIRequest,
    APIResponse,
    APIVersion
)

__version__ = "1.0.0"
__all__ = [
    # Codebase Integration
    "CodebaseAdapter",
    "AnalysisRequest",
    "AnalysisResult",
    "quick_analyze",
    "analyze_specific_files",
    
    # Database Integration
    "DatabaseAdapter",
    "DatabaseConfig",
    "DatabaseConnectionError",
    "DatabaseOperationError",
    
    # Unified API
    "UnifiedAPI",
    "APIRequest",
    "APIResponse",
    "APIVersion"
]

