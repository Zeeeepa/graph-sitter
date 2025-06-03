"""
Codegen SDK Integration Module

This module provides comprehensive integration between the Codegen SDK and the
graph-sitter contexten orchestrator, enabling enhanced code generation capabilities
with intelligent codebase context integration.

Key Components:
- CodegenSDKAdapter: Main interface for Codegen SDK integration
- Enhanced Autogenlib: Context-aware code generation
- Performance Infrastructure: Connection pooling, rate limiting, concurrency
- Context Enhancement: Intelligent codebase context selection
- Configuration Management: Secure org_id and token handling
"""

from .codegen_client import CodegenSDKAdapter, CodegenConfig
from .autogenlib.enhanced_autogenlib import EnhancedAutogenLib
from .config.auth_config import AuthConfig
from .performance.batch_processor import BatchProcessor

__all__ = [
    "CodegenSDKAdapter",
    "CodegenConfig", 
    "EnhancedAutogenLib",
    "AuthConfig",
    "BatchProcessor"
]

__version__ = "1.0.0"

