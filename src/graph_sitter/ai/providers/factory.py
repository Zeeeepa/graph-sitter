"""
Enhanced AI Provider Factory with intelligent selection and comprehensive monitoring.

This module provides factory functions for creating AI providers with automatic
selection, fallback mechanisms, and detailed status monitoring.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Type, Union

from .base import AIProvider
from .openai_provider import OpenAIProvider
from .codegen_provider import CodegenProvider

logger = logging.getLogger(__name__)


# Custom exceptions for provider management
class ProviderError(Exception):
    """Base exception for provider-related errors."""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is not available or misconfigured."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ProviderTimeoutError(ProviderError):
    """Raised when provider requests timeout."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None):
        super().__init__(message)
        self.timeout_duration = timeout_duration


# Provider registry
PROVIDER_CLASSES: Dict[str, Type[AIProvider]] = {
    "openai": OpenAIProvider,
    "codegen": CodegenProvider
}


def detect_available_credentials() -> Dict[str, Dict[str, Any]]:
    """
    Detect available credentials for all providers.
    
    Returns:
        Dictionary mapping provider names to credential information
    """
    credentials = {}
    
    # Check OpenAI credentials
    openai_key = os.getenv("OPENAI_API_KEY")
    credentials["openai"] = {
        "available": bool(openai_key),
        "api_key_configured": bool(openai_key),
        "details": "API key found" if openai_key else "API key not found"
    }
    
    # Check Codegen credentials
    codegen_org_id = os.getenv("CODEGEN_ORG_ID")
    codegen_token = os.getenv("CODEGEN_TOKEN")
    codegen_base_url = os.getenv("CODEGEN_BASE_URL")
    
    credentials["codegen"] = {
        "available": bool(codegen_org_id and codegen_token),
        "org_id_configured": bool(codegen_org_id),
        "token_configured": bool(codegen_token),
        "base_url_configured": bool(codegen_base_url),
        "base_url": codegen_base_url or "https://api.codegen.com",
        "details": "Fully configured" if (codegen_org_id and codegen_token) else "Missing credentials"
    }
    
    return credentials


def get_provider_status() -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive status of all providers.
    
    Returns:
        Dictionary mapping provider names to status information
    """
    status = {}
    credentials = detect_available_credentials()
    
    for provider_name, provider_class in PROVIDER_CLASSES.items():
        try:
            # Create provider instance
            provider = provider_class()
            
            # Get basic status
            is_available = provider.is_available
            stats = provider.get_stats()
            
            status[provider_name] = {
                "is_available": is_available,
                "credentials": credentials.get(provider_name, {}),
                "stats": stats,
                "provider_class": provider_class.__name__,
                "error": None
            }
            
            # Add enhanced stats if available
            if hasattr(provider, 'get_enhanced_stats'):
                status[provider_name]["enhanced_stats"] = provider.get_enhanced_stats()
            
        except Exception as e:
            status[provider_name] = {
                "is_available": False,
                "credentials": credentials.get(provider_name, {}),
                "stats": {},
                "provider_class": provider_class.__name__,
                "error": str(e)
            }
    
    return status


def get_provider_comparison() -> Dict[str, Any]:
    """
    Get detailed comparison of all providers.
    
    Returns:
        Comprehensive comparison including recommendations
    """
    status = get_provider_status()
    
    available_providers = [
        name for name, info in status.items() 
        if info["is_available"]
    ]
    
    # Determine recommended provider
    recommended_provider = None
    if "codegen" in available_providers:
        recommended_provider = "codegen"  # Prefer Codegen SDK
    elif "openai" in available_providers:
        recommended_provider = "openai"
    
    comparison = {
        "providers": status,
        "available_providers": available_providers,
        "total_providers": len(PROVIDER_CLASSES),
        "summary": {
            "available_count": len(available_providers),
            "recommended_provider": recommended_provider,
            "fallback_available": len(available_providers) > 1
        }
    }
    
    return comparison


def create_ai_provider(
    provider_name: Optional[str] = None,
    prefer_codegen: bool = True,
    fallback_enabled: bool = True,
    validate_on_creation: bool = True,
    **kwargs
) -> AIProvider:
    """
    Create an AI provider with intelligent selection and fallback.
    
    Args:
        provider_name: Specific provider to use ("openai", "codegen")
        prefer_codegen: Whether to prefer Codegen SDK when auto-selecting
        fallback_enabled: Whether to try fallback providers if primary fails
        validate_on_creation: Whether to validate provider availability on creation
        **kwargs: Provider-specific configuration options
        
    Returns:
        Configured AIProvider instance
        
    Raises:
        ProviderUnavailableError: If no providers are available
    """
    logger.info(f"Creating AI provider (name={provider_name}, prefer_codegen={prefer_codegen})")
    
    # If specific provider requested, try to create it
    if provider_name:
        if provider_name not in PROVIDER_CLASSES:
            raise ProviderUnavailableError(f"Unknown provider: {provider_name}")
        
        provider_class = PROVIDER_CLASSES[provider_name]
        provider = provider_class(**kwargs)
        
        if validate_on_creation and not provider.is_available:
            if fallback_enabled:
                logger.warning(f"Requested provider {provider_name} not available, trying fallback")
                return create_ai_provider(
                    provider_name=None,
                    prefer_codegen=prefer_codegen,
                    fallback_enabled=False,  # Avoid infinite recursion
                    validate_on_creation=validate_on_creation,
                    **kwargs
                )
            else:
                raise ProviderUnavailableError(f"Provider {provider_name} is not available")
        
        logger.info(f"Created {provider_name} provider successfully")
        return provider
    
    # Auto-select provider based on preferences and availability
    provider_order = []
    if prefer_codegen:
        provider_order = ["codegen", "openai"]
    else:
        provider_order = ["openai", "codegen"]
    
    last_error = None
    for provider_name in provider_order:
        try:
            provider_class = PROVIDER_CLASSES[provider_name]
            provider = provider_class(**kwargs)
            
            if not validate_on_creation or provider.is_available:
                logger.info(f"Auto-selected {provider_name} provider")
                return provider
            else:
                logger.debug(f"Provider {provider_name} not available, trying next")
                
        except Exception as e:
            logger.debug(f"Failed to create {provider_name} provider: {e}")
            last_error = e
    
    # No providers available
    error_msg = "No AI providers are available"
    if last_error:
        error_msg += f". Last error: {last_error}"
    
    raise ProviderUnavailableError(error_msg)


def get_best_provider(
    task_type: Optional[str] = None,
    prefer_codegen: bool = True,
    **kwargs
) -> AIProvider:
    """
    Get the best provider for a specific task type.
    
    Args:
        task_type: Type of task ("code_generation", "analysis", "chat", etc.)
        prefer_codegen: Whether to prefer Codegen SDK
        **kwargs: Provider configuration options
        
    Returns:
        Best available provider for the task
    """
    # Task-specific provider preferences
    task_preferences = {
        "code_generation": ["codegen", "openai"],
        "code_analysis": ["codegen", "openai"],
        "code_review": ["codegen", "openai"],
        "documentation": ["openai", "codegen"],
        "chat": ["openai", "codegen"],
        "general": ["codegen", "openai"] if prefer_codegen else ["openai", "codegen"]
    }
    
    # Get provider order for task type
    provider_order = task_preferences.get(task_type, task_preferences["general"])
    
    # Try providers in order
    for provider_name in provider_order:
        try:
            provider = create_ai_provider(
                provider_name=provider_name,
                fallback_enabled=False,
                **kwargs
            )
            if provider.is_available:
                logger.info(f"Selected {provider_name} for task type: {task_type}")
                return provider
        except Exception as e:
            logger.debug(f"Provider {provider_name} not available for task {task_type}: {e}")
    
    # Fallback to any available provider
    logger.warning(f"No preferred providers available for task {task_type}, using fallback")
    return create_ai_provider(prefer_codegen=prefer_codegen, **kwargs)


def list_available_providers() -> List[str]:
    """Get list of available provider names."""
    return list(PROVIDER_CLASSES.keys())


def list_available_provider_names() -> List[str]:
    """Alias for list_available_providers for backward compatibility."""
    return list_available_providers()


def register_provider(name: str, provider_class: Type[AIProvider]):
    """
    Register a custom provider class.
    
    Args:
        name: Provider name
        provider_class: Provider class (must inherit from AIProvider)
    """
    if not issubclass(provider_class, AIProvider):
        raise ValueError("Provider class must inherit from AIProvider")
    
    PROVIDER_CLASSES[name] = provider_class
    logger.info(f"Registered custom provider: {name}")


def unregister_provider(name: str):
    """Unregister a provider."""
    if name in PROVIDER_CLASSES:
        del PROVIDER_CLASSES[name]
        logger.info(f"Unregistered provider: {name}")
    else:
        logger.warning(f"Provider {name} not found for unregistration")
