"""
Enhanced OpenAI provider implementation with robust error handling and monitoring.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import AuthenticationError as OpenAIAuthError
from openai import RateLimitError as OpenAIRateLimitError
from openai import APITimeoutError as OpenAITimeoutError

from .base import (
    AIProvider, 
    AIResponse,
    ProviderUnavailableError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """Enhanced OpenAI provider implementation with comprehensive error handling."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize enhanced OpenAI provider.
        
        Args:
            api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY env var)
            base_url: Custom base URL for OpenAI API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
        self._last_validation_time = None
        self._validation_cache_duration = 300  # 5 minutes
        
        # Enhanced monitoring
        self._token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self._model_usage = {}
        
        if self.api_key:
            try:
                self._initialize_client()
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def _initialize_client(self):
        """Initialize the OpenAI client with enhanced configuration."""
        try:
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout,
                "max_retries": self.max_retries
            }
            
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            self._client = OpenAI(**client_kwargs)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise ProviderUnavailableError(f"Failed to initialize OpenAI client: {e}")
    
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
        """Get the OpenAI client with lazy initialization."""
        if not self._client:
            if not self.api_key:
                raise ProviderUnavailableError("OpenAI API key not provided")
            self._initialize_client()
        return self._client
    
    def validate_credentials(self) -> bool:
        """
        Validate the provider credentials with caching.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        if not self.is_available:
            return False
        
        # Check cache
        current_time = time.time()
        if (self._last_validation_time and 
            current_time - self._last_validation_time < self._validation_cache_duration):
            return True
        
        try:
            # Try a simple API call to validate credentials
            self.client.models.list()
            self._last_validation_time = current_time
            self.logger.info("OpenAI credentials validated successfully")
            return True
        except OpenAIAuthError:
            self.logger.error("OpenAI credential validation failed: Authentication error")
            return False
        except Exception as e:
            self.logger.warning(f"OpenAI credential validation failed: {e}")
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
        """Generate a response using enhanced OpenAI API."""
        
        if not self.is_available:
            raise ProviderUnavailableError("OpenAI provider is not available")
        
        start_time = time.time()
        request_id = f"openai_{int(start_time * 1000)}"
        
        # Use default model if not specified
        if not model:
            model = "gpt-4o"
        
        try:
            self._record_request()
            
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
            
            self.logger.info(f"[{request_id}] Making OpenAI API call with model {model}")
            
            # Make the API call with enhanced error handling
            try:
                response = self.client.chat.completions.create(**request_params)
            except OpenAIAuthError as e:
                self._record_request(success=False)
                raise ProviderAuthenticationError(f"OpenAI authentication failed: {e}")
            except OpenAIRateLimitError as e:
                self._record_request(success=False)
                self._handle_rate_limit()
                raise ProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
            except OpenAITimeoutError as e:
                self._record_request(success=False)
                raise ProviderTimeoutError(f"OpenAI request timed out: {e}")
            except Exception as e:
                self._record_request(success=False)
                raise ProviderUnavailableError(f"OpenAI API error: {e}")
            
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
                raise ProviderUnavailableError("No content in OpenAI response")
            
            # Prepare usage information
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                # Update tracking
                self._token_usage["prompt_tokens"] += usage["prompt_tokens"]
                self._token_usage["completion_tokens"] += usage["completion_tokens"]
                self._token_usage["total_tokens"] += usage["total_tokens"]
                
                if model not in self._model_usage:
                    self._model_usage[model] = {"requests": 0, "tokens": 0}
                self._model_usage[model]["requests"] += 1
                self._model_usage[model]["tokens"] += usage["total_tokens"]
            
            response_time = time.time() - start_time
            
            self.logger.info(f"[{request_id}] OpenAI response completed in {response_time:.2f}s")
            
            return AIResponse(
                content=content,
                provider_name=self.provider_name,
                model=model,
                usage=usage,
                metadata={
                    "request_id": request_id,
                    "finish_reason": choice.finish_reason,
                    "response_id": response.id,
                    "model": response.model,
                    "created": response.created,
                    "system_fingerprint": getattr(response, 'system_fingerprint', None)
                },
                raw_response=response,
                response_time=response_time,
                request_id=request_id
            )
            
        except Exception as e:
            if not isinstance(e, (ProviderAuthenticationError, ProviderRateLimitError, 
                                ProviderTimeoutError, ProviderUnavailableError)):
                self._record_request(success=False)
                self.logger.error(f"[{request_id}] Unexpected error in OpenAI provider: {e}")
                raise ProviderUnavailableError(f"Unexpected OpenAI error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def get_default_model(self) -> str:
        """Get the default model for OpenAI."""
        return "gpt-4o"
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced provider statistics."""
        base_stats = self.get_stats()
        
        return {
            **base_stats,
            "token_usage": self._token_usage.copy(),
            "model_usage": self._model_usage.copy(),
            "average_tokens_per_request": (
                self._token_usage["total_tokens"] / max(self._request_count, 1)
            ),
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "last_validation_time": self._last_validation_time
        }
    
    def get_models_from_api(self) -> List[Dict[str, Any]]:
        """Get available models from OpenAI API."""
        if not self.is_available:
            return []
        
        try:
            models = self.client.models.list()
            return [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in models.data
                if "gpt" in model.id  # Filter to GPT models
            ]
        except Exception as e:
            self.logger.warning(f"Failed to get OpenAI models: {e}")
            return []
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str = "gpt-4o") -> float:
        """
        Estimate cost for a request based on token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Pricing as of 2024 (approximate, check OpenAI pricing for current rates)
        pricing = {
            "gpt-4o": {"prompt": 0.005, "completion": 0.015},  # per 1K tokens
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
        }
        
        if model not in pricing:
            model = "gpt-4o"  # Default fallback
        
        prompt_cost = (prompt_tokens / 1000) * pricing[model]["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing[model]["completion"]
        
        return prompt_cost + completion_cost

