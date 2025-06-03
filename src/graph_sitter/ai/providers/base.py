"""
Abstract base classes for AI providers with enhanced capabilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Standardized response format for all AI providers."""
    
    content: str
    provider_name: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.response_time is None:
            self.response_time = time.time()


class AIProvider(ABC):
    """
    Abstract base class for AI providers with enhanced capabilities.
    
    This class defines the interface that all AI providers must implement,
    including robust error handling, monitoring, and configuration management.
    """
    
    provider_name: str = "base"
    
    def __init__(self, **kwargs):
        """Initialize the provider with configuration."""
        self.config = kwargs
        self.stats = {
            "request_count": 0,
            "error_count": 0,
            "total_response_time": 0.0,
            "last_request_time": None
        }
        self._is_available = None
        self._last_availability_check = 0
        self._availability_cache_duration = 300  # 5 minutes
    
    @property
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.
        
        Uses caching to avoid repeated expensive checks.
        """
        current_time = time.time()
        if (self._is_available is None or 
            current_time - self._last_availability_check > self._availability_cache_duration):
            
            try:
                self._is_available = self._check_availability()
                self._last_availability_check = current_time
                logger.debug(f"{self.provider_name} availability: {self._is_available}")
            except Exception as e:
                logger.warning(f"Availability check failed for {self.provider_name}: {e}")
                self._is_available = False
        
        return self._is_available
    
    @abstractmethod
    def _check_availability(self) -> bool:
        """Check if the provider is available and properly configured."""
        pass
    
    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate a response using the AI provider.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: Model to use (provider-specific)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            AIResponse object with standardized format
        """
        pass
    
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        stats = self.stats.copy()
        if stats["request_count"] > 0:
            stats["average_response_time"] = stats["total_response_time"] / stats["request_count"]
            stats["error_rate"] = stats["error_count"] / stats["request_count"]
        else:
            stats["average_response_time"] = 0.0
            stats["error_rate"] = 0.0
        
        return stats
    
    def _record_request(self, response_time: float, error: bool = False):
        """Record request statistics."""
        self.stats["request_count"] += 1
        self.stats["total_response_time"] += response_time
        self.stats["last_request_time"] = time.time()
        
        if error:
            self.stats["error_count"] += 1
    
    def reset_stats(self):
        """Reset provider statistics."""
        self.stats = {
            "request_count": 0,
            "error_count": 0,
            "total_response_time": 0.0,
            "last_request_time": None
        }
    
    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(available={self.is_available})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return f"{self.__class__.__name__}(provider_name={self.provider_name}, available={self.is_available})"

