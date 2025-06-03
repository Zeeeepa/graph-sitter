"""
OpenAI provider implementation.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .base import AIProvider, AIResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        
        if self.api_key:
            try:
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    @property
    def provider_name(self) -> str:
        """Return the name of the AI provider."""
        return "OpenAI"
    
    @property
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured."""
        return self.api_key is not None and self._client is not None
    
    @property
    def client(self) -> OpenAI:
        """Get the OpenAI client."""
        if not self._client:
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def validate_credentials(self) -> bool:
        """Validate the provider credentials."""
        if not self.is_available:
            return False
        
        try:
            # Try a simple API call to validate credentials
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI credential validation failed: {e}")
            return False
    
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
        """Generate a response using OpenAI."""
        
        if not self.is_available:
            raise ValueError("OpenAI provider is not available")
        
        # Use default model if not specified
        if not model:
            model = "gpt-4o"
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        if tools:
            request_params["tools"] = tools
            if tool_choice:
                request_params["tool_choice"] = tool_choice
        
        # Add any additional kwargs
        request_params.update(kwargs)
        
        try:
            # Make the API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract content from response
            choice = response.choices[0]
            content = ""
            
            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                # Handle tool calls
                tool_call = choice.message.tool_calls[0]
                try:
                    tool_response = json.loads(tool_call.function.arguments)
                    content = tool_response.get("answer", str(tool_response))
                except json.JSONDecodeError:
                    content = tool_call.function.arguments
            elif choice.message.content:
                content = choice.message.content
            else:
                raise ValueError("No content in OpenAI response")
            
            # Prepare usage information
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return AIResponse(
                content=content,
                provider=self.provider_name,
                model=model,
                usage=usage,
                metadata={
                    "finish_reason": choice.finish_reason,
                    "response_id": response.id
                },
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]

