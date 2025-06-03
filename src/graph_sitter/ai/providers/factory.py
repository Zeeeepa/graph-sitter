"""
Enhanced factory for creating AI providers with intelligent selection and comprehensive monitoring.
"""

import logging
import os
from typing import Dict, List, Optional, Type, Any

from .base import AIProvider, ProviderUnavailableError
from .openai_provider import OpenAIProvider
from .codegen_provider import CodegenProvider

logger = logging.getLogger(__name__)


def get_available_providers() -> Dict[str, Type[AIProvider]]:
    """Get all available AI provider classes."""
    return {
        "openai": OpenAIProvider,
        "codegen": CodegenProvider
    }


def detect_available_credentials() -> Dict[str, Dict[str, Any]]:
    """
    Detect which AI providers have credentials available with detailed information.
    
    Returns:
        Dict mapping provider names to credential information
    """
    credentials = {}
    
    # Check OpenAI credentials
    openai_key = os.getenv("OPENAI_API_KEY")
    credentials["openai"] = {
        "available": bool(openai_key),
        "key_length": len(openai_key) if openai_key else 0,
        "key_prefix": openai_key[:8] + "..." if openai_key and len(openai_key) > 8 else None,
        "env_vars": ["OPENAI_API_KEY"]
    }
    
    # Check Codegen credentials
    codegen_org_id = os.getenv("CODEGEN_ORG_ID")
    codegen_token = os.getenv("CODEGEN_TOKEN")
    credentials["codegen"] = {
        "available": bool(codegen_org_id and codegen_token),
        "org_id": codegen_org_id,
        "token_length": len(codegen_token) if codegen_token else 0,
        "token_prefix": codegen_token[:8] + "..." if codegen_token and len(codegen_token) > 8 else None,
        "env_vars": ["CODEGEN_ORG_ID", "CODEGEN_TOKEN"]
    }
    
    return credentials


def validate_provider_credentials(provider_name: str) -> Dict[str, Any]:
    """
    Validate credentials for a specific provider.
    
    Args:
        provider_name: Name of the provider to validate
        
    Returns:
        Dict with validation results
    """
    available_providers = get_available_providers()
    
    if provider_name not in available_providers:
        return {
            "valid": False,
            "error": f"Unknown provider: {provider_name}",
            "provider_name": provider_name
        }
    
    try:
        provider_class = available_providers[provider_name]
        provider = provider_class()
        
        if not provider.is_available:
            return {
                "valid": False,
                "error": f"{provider_name} provider is not available (missing credentials)",
                "provider_name": provider_name
            }
        
        is_valid = provider.validate_credentials()
        
        return {
            "valid": is_valid,
            "error": None if is_valid else f"{provider_name} credential validation failed",
            "provider_name": provider_name,
            "stats": provider.get_stats() if hasattr(provider, 'get_stats') else {}
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to validate {provider_name}: {str(e)}",
            "provider_name": provider_name
        }


def create_ai_provider(
    provider_name: Optional[str] = None,
    prefer_codegen: bool = True,
    fallback_enabled: bool = True,
    validate_on_creation: bool = True,
    **kwargs
) -> AIProvider:
    """
    Create an AI provider with enhanced intelligent selection and validation.
    
    Args:
        provider_name: Specific provider to use ("openai" or "codegen")
        prefer_codegen: Whether to prefer Codegen SDK over OpenAI when both are available
        fallback_enabled: Whether to fall back to other providers if the preferred one fails
        validate_on_creation: Whether to validate credentials during creation
        **kwargs: Additional configuration for the provider
        
    Returns:
        Configured AI provider instance
        
    Raises:
        ProviderUnavailableError: If no providers are available or specified provider is invalid
    """
    available_providers = get_available_providers()
    available_credentials = detect_available_credentials()
    
    logger.info(f"Creating AI provider (prefer_codegen={prefer_codegen}, fallback={fallback_enabled})")
    
    # If specific provider is requested
    if provider_name:
        if provider_name not in available_providers:
            raise ProviderUnavailableError(
                f"Unknown provider: {provider_name}. Available: {list(available_providers.keys())}"
            )
        
        if not available_credentials.get(provider_name, {}).get("available", False):
            error_msg = f"Credentials not available for {provider_name} provider. "
            env_vars = available_credentials.get(provider_name, {}).get("env_vars", [])
            if env_vars:
                error_msg += f"Please set: {', '.join(env_vars)}"
            raise ProviderUnavailableError(error_msg)
        
        provider_class = available_providers[provider_name]
        
        try:
            provider = provider_class(**kwargs)
            
            if not provider.is_available:
                raise ProviderUnavailableError(f"{provider_name} provider is not properly configured")
            
            if validate_on_creation and not provider.validate_credentials():
                if fallback_enabled:
                    logger.warning(f"{provider_name} validation failed, trying fallback")
                    return _create_fallback_provider(provider_name, available_providers, 
                                                   available_credentials, validate_on_creation, **kwargs)
                else:
                    raise ProviderUnavailableError(f"{provider_name} credential validation failed")
            
            logger.info(f"Successfully created {provider_name} AI provider")
            return provider
            
        except Exception as e:
            if fallback_enabled:
                logger.warning(f"Failed to create {provider_name} provider: {e}, trying fallback")
                return _create_fallback_provider(provider_name, available_providers, 
                                               available_credentials, validate_on_creation, **kwargs)
            else:
                raise ProviderUnavailableError(f"Failed to create {provider_name} provider: {e}")
    
    # Auto-select provider based on availability and preference
    provider_priority = ["codegen", "openai"] if prefer_codegen else ["openai", "codegen"]
    
    for provider_name in provider_priority:
        if available_credentials.get(provider_name, {}).get("available", False):
            try:
                provider_class = available_providers[provider_name]
                provider = provider_class(**kwargs)
                
                if provider.is_available:
                    if not validate_on_creation or provider.validate_credentials():
                        logger.info(f"Auto-selected {provider_name} AI provider")
                        return provider
                    else:
                        logger.warning(f"{provider_name} provider failed validation, trying next option")
                else:
                    logger.warning(f"{provider_name} provider not available, trying next option")
                    
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_name} provider: {e}")
                continue
    
    # If no providers are available, provide helpful error message
    available_creds = [
        name for name, info in available_credentials.items() 
        if info.get("available", False)
    ]
    
    if not available_creds:
        raise ProviderUnavailableError(
            "No AI providers are available. Please set one of the following:\n"
            "- OpenAI: Set OPENAI_API_KEY environment variable\n"
            "- Codegen: Set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables\n"
            "Get your Codegen API token from: https://codegen.sh/token"
        )
    else:
        raise ProviderUnavailableError(
            f"AI providers with credentials ({available_creds}) failed to initialize. "
            "Please check your credentials and network connection."
        )


def _create_fallback_provider(
    failed_provider: str,
    available_providers: Dict[str, Type[AIProvider]],
    available_credentials: Dict[str, Dict[str, Any]],
    validate_on_creation: bool,
    **kwargs
) -> AIProvider:
    """Create a fallback provider when the primary provider fails."""
    
    # Try other available providers
    for provider_name, provider_class in available_providers.items():
        if provider_name == failed_provider:
            continue
            
        if available_credentials.get(provider_name, {}).get("available", False):
            try:
                provider = provider_class(**kwargs)
                
                if provider.is_available:
                    if not validate_on_creation or provider.validate_credentials():
                        logger.info(f"Fallback to {provider_name} AI provider successful")
                        return provider
                    else:
                        logger.warning(f"Fallback {provider_name} provider failed validation")
                        
            except Exception as e:
                logger.warning(f"Fallback {provider_name} provider failed: {e}")
                continue
    
    raise ProviderUnavailableError("All available providers failed to initialize")


def get_provider_status() -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive status of all AI providers.
    
    Returns:
        Dict mapping provider names to detailed status information
    """
    status = {}
    available_providers = get_available_providers()
    available_credentials = detect_available_credentials()
    
    for name, provider_class in available_providers.items():
        cred_info = available_credentials.get(name, {})
        has_credentials = cred_info.get("available", False)
        
        provider_status = {
            "has_credentials": has_credentials,
            "credential_info": cred_info,
            "is_available": False,
            "validation_result": None,
            "error": None,
            "stats": None
        }
        
        if has_credentials:
            try:
                provider = provider_class()
                provider_status["is_available"] = provider.is_available
                
                if provider.is_available:
                    validation_result = validate_provider_credentials(name)
                    provider_status["validation_result"] = validation_result
                    
                    if validation_result.get("valid", False):
                        provider_status["stats"] = provider.get_stats()
                    else:
                        provider_status["error"] = validation_result.get("error")
                else:
                    provider_status["error"] = f"{name} provider not properly configured"
                    
            except Exception as e:
                provider_status["error"] = f"Failed to initialize {name}: {str(e)}"
                logger.debug(f"Provider {name} initialization failed: {e}")
        
        status[name] = provider_status
    
    return status


def get_recommended_provider() -> Optional[str]:
    """
    Get the recommended provider based on current availability and performance.
    
    Returns:
        Name of the recommended provider or None if none available
    """
    status = get_provider_status()
    
    # Prefer providers that are available and validated
    for provider_name in ["codegen", "openai"]:  # Prefer Codegen
        provider_status = status.get(provider_name, {})
        if (provider_status.get("has_credentials", False) and 
            provider_status.get("is_available", False) and
            provider_status.get("validation_result", {}).get("valid", False)):
            return provider_name
    
    return None


def get_provider_comparison() -> Dict[str, Any]:
    """
    Get a comparison of available providers with their capabilities and status.
    
    Returns:
        Dict with provider comparison information
    """
    status = get_provider_status()
    
    comparison = {
        "providers": {},
        "summary": {
            "total_providers": len(status),
            "available_providers": 0,
            "validated_providers": 0,
            "recommended_provider": get_recommended_provider()
        }
    }
    
    for name, provider_status in status.items():
        is_available = provider_status.get("is_available", False)
        is_validated = provider_status.get("validation_result", {}).get("valid", False)
        
        if is_available:
            comparison["summary"]["available_providers"] += 1
        if is_validated:
            comparison["summary"]["validated_providers"] += 1
        
        # Get provider capabilities
        try:
            provider_class = get_available_providers()[name]
            temp_provider = provider_class()
            capabilities = {
                "models": temp_provider.get_available_models(),
                "default_model": temp_provider.get_default_model()
            }
        except Exception:
            capabilities = {"models": [], "default_model": None}
        
        comparison["providers"][name] = {
            **provider_status,
            "capabilities": capabilities
        }
    
    return comparison
