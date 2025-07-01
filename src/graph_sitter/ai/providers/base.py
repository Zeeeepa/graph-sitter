"""
Abstract base class for AI providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class AIResponse:
    """Standardized response from AI providers."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    raw_response: Optional[Any] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, **kwargs):
        """Initialize the AI provider with configuration."""
        self.config = kwargs
    
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
        """Validate the provider credentials."""
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
    
    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.provider_name}Provider"
    
    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return f"{self.provider_name}Provider(available={self.is_available})"

