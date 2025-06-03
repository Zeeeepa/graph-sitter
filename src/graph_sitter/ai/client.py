"""
Enhanced AI client with support for multiple providers and intelligent selection.
"""

import logging
from typing import Optional

from openai import OpenAI

from .providers import AIProvider, create_ai_provider

logger = logging.getLogger(__name__)


def get_openai_client(key: str) -> OpenAI:
    """Legacy function for backward compatibility."""
    return OpenAI(api_key=key)


def get_ai_client(
    provider_name: Optional[str] = None,
    prefer_codegen: bool = True,
    fallback_enabled: bool = True,
    validate_on_creation: bool = True,
    **kwargs
) -> AIProvider:
    """
    Get an AI client with enhanced provider selection.
    
    Args:
        provider_name: Specific provider to use ("openai" or "codegen")
        prefer_codegen: Whether to prefer Codegen SDK over OpenAI
        fallback_enabled: Whether to fall back to other providers if preferred fails
        validate_on_creation: Whether to validate credentials during creation
        **kwargs: Additional configuration for the provider
        
    Returns:
        Configured AI provider instance
        
    Raises:
        ProviderUnavailableError: If no providers are available
    """
    logger.info(f"Getting AI client (provider={provider_name}, prefer_codegen={prefer_codegen})")
    
    return create_ai_provider(
        provider_name=provider_name,
        prefer_codegen=prefer_codegen,
        fallback_enabled=fallback_enabled,
        validate_on_creation=validate_on_creation,
        **kwargs
    )

