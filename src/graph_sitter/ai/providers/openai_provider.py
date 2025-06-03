"""
Enhanced OpenAI provider implementation with robust error handling.
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

from .base import AIProvider, AIResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """Enhanced OpenAI provider with robust error handling and monitoring."""
    
    provider_name = "openai"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = kwargs.get("timeout", 30)
        self.max_retries = kwargs.get("max_retries", 3)
        
        self._client = None
        if self.api_key:
            try:
                self._client = OpenAI(
                    api_key=self.api_key,
                    timeout=self.timeout,
                    max_retries=self.max_retries
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def _check_availability(self) -> bool:
        """Check if OpenAI is available and properly configured."""
        if not self.api_key:
            logger.debug("OpenAI API key not found")
            return False
        
        if not self._client:
            logger.debug("OpenAI client not initialized")
            return False
        
        try:
            # Simple test to verify credentials
            self._client.models.list()
            return True
        except Exception as e:
            logger.debug(f"OpenAI availability check failed: {e}")
            return False
    
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
        Generate response using OpenAI.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (defaults to gpt-4o)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters
            
        Returns:
            AIResponse object
        """
        if not self.is_available:
            raise RuntimeError("OpenAI provider is not available")
        
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Set default model
            if not model:
                model = "gpt-4o"
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # Make request
            response: ChatCompletion = self._client.chat.completions.create(**request_params)
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record statistics
            self._record_request(response_time, error=False)
            
            # Prepare usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return AIResponse(
                content=content,
                provider_name=self.provider_name,
                model=model,
                usage=usage,
                response_time=response_time,
                request_id=response.id,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "created": response.created
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self._record_request(response_time, error=True)
            
            logger.error(f"OpenAI request failed: {e}")
            raise RuntimeError(f"OpenAI request failed: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        if not self.is_available:
            return []
        
        try:
            models = self._client.models.list()
            return [model.id for model in models.data if "gpt" in model.id]
        except Exception as e:
            logger.warning(f"Failed to get OpenAI models: {e}")
            return ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]  # Fallback list
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics specific to OpenAI."""
        base_stats = self.get_stats()
        
        enhanced_stats = {
            **base_stats,
            "provider_type": "openai",
            "api_key_configured": bool(self.api_key),
            "client_initialized": bool(self._client),
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
        
        return enhanced_stats

