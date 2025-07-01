"""
Enhanced AI client with multi-provider support and factory patterns.

This module provides a unified interface for AI interactions with automatic
provider selection, fallback mechanisms, and comprehensive error handling.
"""

import logging
from typing import Optional

from .providers import create_ai_provider, AIProvider, AIResponse

logger = logging.getLogger(__name__)


def get_ai_client(
    provider_name: Optional[str] = None,
    prefer_codegen: bool = True,
    **kwargs
) -> AIProvider:
    """
    Get an AI client with intelligent provider selection.
    
    Args:
        provider_name: Specific provider to use ("openai", "codegen")
        prefer_codegen: Whether to prefer Codegen SDK when auto-selecting
        **kwargs: Provider-specific configuration options
        
    Returns:
        Configured AIProvider instance
        
    Example:
        # Automatic selection (prefers Codegen SDK)
        client = get_ai_client()
        
        # Force specific provider
        openai_client = get_ai_client(provider_name="openai")
        codegen_client = get_ai_client(provider_name="codegen")
    """
    return create_ai_provider(
        provider_name=provider_name,
        prefer_codegen=prefer_codegen,
        **kwargs
    )


def get_openai_client(key: str):
    """
    Legacy function for backward compatibility.
    
    Args:
        key: OpenAI API key
        
    Returns:
        OpenAI provider instance
    """
    from .providers import OpenAIProvider
    return OpenAIProvider(api_key=key)


# Convenience functions for common operations
def generate_ai_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> AIResponse:
    """
    Generate an AI response with automatic provider selection.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        provider_name: Specific provider to use
        model: Model to use
        **kwargs: Additional parameters
        
    Returns:
        AIResponse object
    """
    client = get_ai_client(provider_name=provider_name)
    return client.generate_response(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        **kwargs
    )

