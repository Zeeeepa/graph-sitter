"""AutoGenLib integration with Codegen SDK and Graph-sitter context.

This module provides dynamic code generation capabilities by integrating:
- AutoGenLib's import interception mechanism
- Codegen SDK for AI-powered code generation
- Graph-sitter's codebase context analysis
- Fallback to Claude API when needed
"""

from .core import AutoGenLibIntegration, init_autogenlib
from .generator import CodeGenerator, CodegenSDKProvider, ClaudeProvider
from .context import GraphSitterContextProvider

__all__ = [
    "AutoGenLibIntegration",
    "init_autogenlib", 
    "CodeGenerator",
    "CodegenSDKProvider",
    "ClaudeProvider",
    "GraphSitterContextProvider"
]

