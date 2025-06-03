"""
Enhanced AI client with support for multiple providers (OpenAI and Codegen SDK).
"""

import logging
from typing import Optional
from openai import OpenAI

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
        provider_name: Specific provider to use ("openai" or "codegen")
        prefer_codegen: Whether to prefer Codegen SDK over OpenAI when both are available
        **kwargs: Additional configuration for the provider
        
    Returns:
        Configured AI provider instance
    """
    return create_ai_provider(
        provider_name=provider_name,
        prefer_codegen=prefer_codegen,
        **kwargs
    )


def get_openai_client(key: str) -> OpenAI:
    """
    Legacy function for backward compatibility.
    
    Args:
        key: OpenAI API key
        
    Returns:
        OpenAI client instance
    """
    return OpenAI(api_key=key)

