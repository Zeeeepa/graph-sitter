"""
Abstract base class for AI providers with enhanced error handling and monitoring.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Standardized response from AI providers with comprehensive metadata."""
    content: str
    provider_name: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    raw_response: Optional[Any] = None
    response_time: Optional[float] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        """Ensure metadata is always a dict."""
        if self.metadata is None:
            self.metadata = {}


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class ProviderUnavailableError(AIProviderError):
    """Raised when a provider is not available or misconfigured."""
    pass


class ProviderAuthenticationError(AIProviderError):
    """Raised when provider authentication fails."""
    pass


class ProviderRateLimitError(AIProviderError):
    """Raised when provider rate limits are exceeded."""
    pass


class ProviderTimeoutError(AIProviderError):
    """Raised when provider requests timeout."""
    pass


class AIProvider(ABC):
    """
    Abstract base class for AI providers with enhanced robustness features.
    
    This class provides a unified interface for different AI providers while
    including comprehensive error handling, retry mechanisms, and monitoring.
    """
    
    def __init__(self, **kwargs):
        """Initialize the AI provider with configuration."""
        self.config = kwargs
        self._request_count = 0
        self._error_count = 0
        self._last_request_time = None
        self._rate_limit_reset_time = None
        
        # Configure logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the AI provider."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured."""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate the provider credentials.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate a response from the AI provider.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: Model to use (provider-specific)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            tools: Available tools/functions
            tool_choice: Tool choice strategy
            **kwargs: Additional provider-specific parameters
            
        Returns:
            AIResponse object with the generated content
            
        Raises:
            ProviderUnavailableError: If provider is not available
            ProviderAuthenticationError: If authentication fails
            ProviderRateLimitError: If rate limits are exceeded
            ProviderTimeoutError: If request times out
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass
    
    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        models = self.get_available_models()
        return models[0] if models else "default"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider usage statistics."""
        return {
            "provider_name": self.provider_name,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "last_request_time": self._last_request_time,
            "is_available": self.is_available
        }
    
    def _record_request(self, success: bool = True):
        """Record request statistics."""
        self._request_count += 1
        self._last_request_time = time.time()
        if not success:
            self._error_count += 1
    
    def _handle_rate_limit(self, retry_after: Optional[int] = None):
        """Handle rate limiting with exponential backoff."""
        if retry_after:
            self._rate_limit_reset_time = time.time() + retry_after
            self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
            time.sleep(retry_after)
        else:
            # Default exponential backoff
            wait_time = min(2 ** (self._error_count % 5), 60)  # Cap at 60 seconds
            self.logger.warning(f"Rate limited, waiting {wait_time} seconds")
            time.sleep(wait_time)
    
    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited."""
        if self._rate_limit_reset_time:
            return time.time() < self._rate_limit_reset_time
        return False
    
    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.provider_name}Provider"
    
    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return f"{self.provider_name}Provider(available={self.is_available}, requests={self._request_count})"

