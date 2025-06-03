"""
Enhanced AI Provider System with Factory Patterns

This module provides a unified abstraction layer for multiple AI providers
with intelligent selection, robust error handling, and comprehensive monitoring.
"""

from .base import AIProvider, AIResponse
from .openai_provider import OpenAIProvider
from .codegen_provider import CodegenProvider
from .factory import (
    create_ai_provider,
    get_provider_status,
    get_provider_comparison,
    detect_available_credentials,
    get_best_provider,
    list_available_providers,
    ProviderUnavailableError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError
)

__all__ = [
    # Core classes
    "AIProvider",
    "AIResponse",
    "OpenAIProvider", 
    "CodegenProvider",
    
    # Factory functions
    "create_ai_provider",
    "get_provider_status",
    "get_provider_comparison",
    "detect_available_credentials",
    "get_best_provider",
    "list_available_providers",
    
    # Exceptions
    "ProviderUnavailableError",
    "ProviderAuthenticationError", 
    "ProviderRateLimitError",
    "ProviderTimeoutError"
]

