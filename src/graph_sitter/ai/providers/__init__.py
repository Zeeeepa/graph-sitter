"""
AI Provider System for Graph-Sitter

This module provides a unified abstraction layer for different AI providers,
enabling seamless integration of OpenAI, Codegen SDK, and future providers.
"""

from .base import AIProvider, AIResponse
from .factory import (
    create_ai_provider, 
    get_provider_status, 
    detect_available_credentials,
    get_provider_comparison,
    get_recommended_provider,
    validate_provider_credentials
)
from .openai_provider import OpenAIProvider
from .codegen_provider import CodegenProvider

__all__ = [
    "AIProvider",
    "AIResponse", 
    "create_ai_provider",
    "get_provider_status",
    "detect_available_credentials",
    "get_provider_comparison",
    "get_recommended_provider",
    "validate_provider_credentials",
    "OpenAIProvider",
    "CodegenProvider"
]

