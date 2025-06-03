"""
Factory for creating AI providers with intelligent selection.
"""

import logging
import os
from typing import Dict, List, Optional, Type

from .base import AIProvider
from .openai_provider import OpenAIProvider
from .codegen_provider import CodegenProvider

logger = logging.getLogger(__name__)


def get_available_providers() -> Dict[str, Type[AIProvider]]:
    """Get all available AI provider classes."""
    return {
        "openai": OpenAIProvider,
        "codegen": CodegenProvider
    }


def detect_available_credentials() -> Dict[str, bool]:
    """Detect which AI providers have credentials available."""
    credentials = {}
    
    # Check OpenAI credentials
    credentials["openai"] = bool(os.getenv("OPENAI_API_KEY"))
    
    # Check Codegen credentials
    credentials["codegen"] = bool(
        os.getenv("CODEGEN_ORG_ID") and os.getenv("CODEGEN_TOKEN")
    )
    
    return credentials


def create_ai_provider(
    provider_name: Optional[str] = None,
    prefer_codegen: bool = True,
    **kwargs
) -> AIProvider:
    """
    Create an AI provider with intelligent selection.
    
    Args:
        provider_name: Specific provider to use ("openai" or "codegen")
        prefer_codegen: Whether to prefer Codegen SDK over OpenAI when both are available
        **kwargs: Additional configuration for the provider
        
    Returns:
        Configured AI provider instance
        
    Raises:
        ValueError: If no providers are available or specified provider is invalid
    """
    available_providers = get_available_providers()
    available_credentials = detect_available_credentials()
    
    # If specific provider is requested
    if provider_name:
        if provider_name not in available_providers:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(available_providers.keys())}")
        
        if not available_credentials.get(provider_name, False):
            raise ValueError(f"Credentials not available for {provider_name} provider")
        
        provider_class = available_providers[provider_name]
        provider = provider_class(**kwargs)
        
        if not provider.is_available:
            raise ValueError(f"{provider_name} provider is not properly configured")
        
        logger.info(f"Using {provider_name} AI provider")
        return provider
    
    # Auto-select provider based on availability and preference
    provider_priority = ["codegen", "openai"] if prefer_codegen else ["openai", "codegen"]
    
    for provider_name in provider_priority:
        if available_credentials.get(provider_name, False):
            try:
                provider_class = available_providers[provider_name]
                provider = provider_class(**kwargs)
                
                if provider.is_available and provider.validate_credentials():
                    logger.info(f"Auto-selected {provider_name} AI provider")
                    return provider
                else:
                    logger.warning(f"{provider_name} provider failed validation, trying next option")
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_name} provider: {e}")
                continue
    
    # If no providers are available, provide helpful error message
    available_creds = [name for name, available in available_credentials.items() if available]
    if not available_creds:
        raise ValueError(
            "No AI providers are available. Please set one of the following:\n"
            "- OpenAI: Set OPENAI_API_KEY environment variable\n"
            "- Codegen: Set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables\n"
            "Get your Codegen API token from: https://codegen.sh/token"
        )
    else:
        raise ValueError(
            f"AI providers with credentials ({available_creds}) failed to initialize. "
            "Please check your credentials and network connection."
        )


def get_provider_status() -> Dict[str, Dict[str, bool]]:
    """Get status of all AI providers."""
    status = {}
    available_providers = get_available_providers()
    available_credentials = detect_available_credentials()
    
    for name, provider_class in available_providers.items():
        has_credentials = available_credentials.get(name, False)
        is_working = False
        
        if has_credentials:
            try:
                provider = provider_class()
                is_working = provider.is_available and provider.validate_credentials()
            except Exception as e:
                logger.debug(f"Provider {name} validation failed: {e}")
        
        status[name] = {
            "has_credentials": has_credentials,
            "is_available": is_working
        }
    
    return status

