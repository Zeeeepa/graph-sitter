"""AI Client Factory for unified client creation and provider management."""

import logging
import time
from typing import Any, Protocol, runtime_checkable, Optional, Dict
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)

# Optional imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

try:
    from codegen import Agent
    CODEGEN_AVAILABLE = True
except ImportError:
    CODEGEN_AVAILABLE = False
    Agent = None

# Global client cache with thread safety
_client_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()

@runtime_checkable
class AIClient(Protocol):
    """Protocol for AI clients to ensure compatibility."""
    
    def chat_completions_create(self, **kwargs) -> Any:
        """Create a chat completion."""
        ...

class CircuitBreaker:
    """Circuit breaker pattern for AI service calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise RuntimeError("Circuit breaker is OPEN - service unavailable")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker opened due to {self.failure_count} failures")
                
                raise

class RateLimiter:
    """Simple rate limiter for AI API calls."""
    
    def __init__(self, max_calls: int = 60, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """Acquire a rate limit slot."""
        with self._lock:
            now = time.time()
            # Remove old calls outside the time window
            self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
            
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            return False
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        while not self.acquire():
            time.sleep(1)

class CodegenAIClient:
    """Wrapper for Codegen SDK to match OpenAI interface."""
    
    def __init__(self, org_id: str, token: str):
        if not CODEGEN_AVAILABLE:
            raise ImportError("Codegen SDK not available. Install with: pip install codegen")
        
        self.agent = Agent(org_id=org_id, token=token)
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(max_calls=30, time_window=60)  # Conservative rate limit

    @property
    def chat(self):
        """Provide chat interface similar to OpenAI."""
        return self
    
    @property
    def completions(self):
        """Provide completions interface similar to OpenAI."""
        return self
    
    def create(self, **kwargs) -> Any:
        """Create a completion using Codegen SDK with circuit breaker and rate limiting."""
        self.rate_limiter.wait_if_needed()
        
        def _create_completion():
            # Extract relevant parameters
            messages = kwargs.get("messages", [])
            model = kwargs.get("model", "gpt-4o")
            
            # Convert messages to a single prompt
            prompt_parts = []
            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")
                if role == "system":
                    prompt_parts.append(f"System: {content}")
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            
            prompt = "\n\n".join(prompt_parts)
            
            # Run the agent task
            task = self.agent.run(prompt=prompt)
            
            # Wait for completion with timeout
            max_wait_time = kwargs.get("timeout", 300)  # 5 minute default timeout
            start_time = time.time()
            
            while task.status not in ["completed", "failed", "cancelled"]:
                if time.time() - start_time > max_wait_time:
                    raise TimeoutError(f"Codegen task timed out after {max_wait_time} seconds")
                task.refresh()
                time.sleep(2)  # Poll every 2 seconds
            
            if task.status == "completed":
                return self._create_mock_response(task.result or "")
            else:
                raise RuntimeError(f"Codegen task failed with status: {task.status}")
        
        return self.circuit_breaker.call(_create_completion)

    def _create_mock_response(self, content: str) -> Any:
        """Create a mock response object that matches OpenAI's structure."""
        class MockChoice:
            def __init__(self, content: str):
                self.finish_reason = "tool_calls"
                self.message = MockMessage(content)
        
        class MockMessage:
            def __init__(self, content: str):
                self.tool_calls = [MockToolCall(content)]
        
        class MockToolCall:
            def __init__(self, content: str):
                self.function = MockFunction(content)
        
        class MockFunction:
            def __init__(self, content: str):
                import json
                self.arguments = json.dumps({"answer": content})
        
        class MockResponse:
            def __init__(self, content: str):
                self.choices = [MockChoice(content)]
        
        return MockResponse(content)


class AIClientFactory:
    """Factory for creating AI clients with automatic provider selection."""
    
    @staticmethod
    def create_client(
        openai_api_key: str | None = None,
        codegen_org_id: str | None = None,
        codegen_token: str | None = None,
        prefer_codegen: bool = True,
        use_cache: bool = True
    ) -> tuple[Any, str]:
        """Create an AI client with intelligent provider selection and caching.
        
        Args:
            openai_api_key: OpenAI API key
            codegen_org_id: Codegen organization ID
            codegen_token: Codegen token
            prefer_codegen: Whether to prefer Codegen over OpenAI when both are available
            use_cache: Whether to use client caching for performance
            
        Returns:
            Tuple of (client, provider_name)
            
        Raises:
            ValueError: If no valid credentials are provided
        """
        # Create cache key for client reuse
        cache_key = None
        if use_cache:
            cache_key = f"{prefer_codegen}:{openai_api_key or ''}:{codegen_org_id or ''}:{codegen_token or ''}"
            
            with _cache_lock:
                if cache_key in _client_cache:
                    cached_client, cached_provider = _client_cache[cache_key]
                    logger.debug(f"Using cached {cached_provider} client")
                    return cached_client, cached_provider
        
        # Check Codegen credentials
        has_codegen = bool(codegen_org_id and codegen_token)
        has_openai = bool(openai_api_key)
        
        if not has_codegen and not has_openai:
            raise ValueError(
                "No AI credentials provided. Please set either:\n"
                "- Codegen credentials: codegen_org_id and codegen_token\n"
                "- OpenAI credentials: openai_api_key"
            )
        
        client = None
        provider = None
        
        # Determine which provider to use
        if prefer_codegen and has_codegen:
            if not CODEGEN_AVAILABLE:
                logger.warning("Codegen SDK not available, falling back to OpenAI")
                if has_openai:
                    if not OPENAI_AVAILABLE:
                        raise ValueError("Neither Codegen SDK nor OpenAI package is available")
                    logger.info("Creating OpenAI client...")
                    client = OpenAI(api_key=openai_api_key)
                    provider = "openai"
                else:
                    raise ValueError("Codegen SDK not available and no OpenAI key provided")
            else:
                logger.info("Creating Codegen AI client...")
                client = CodegenAIClient(org_id=codegen_org_id, token=codegen_token)
                provider = "codegen"
        elif has_openai:
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI package not available. Install with: pip install openai")
            logger.info("Creating OpenAI client...")
            client = OpenAI(api_key=openai_api_key)
            provider = "openai"
        elif has_codegen:
            if not CODEGEN_AVAILABLE:
                raise ValueError("Codegen SDK not available. Install with: pip install codegen")
            logger.info("Creating Codegen AI client...")
            client = CodegenAIClient(org_id=codegen_org_id, token=codegen_token)
            provider = "codegen"
        else:
            raise ValueError("No valid AI credentials provided")
        
        # Cache the client if caching is enabled
        if use_cache and cache_key and client and provider:
            with _cache_lock:
                _client_cache[cache_key] = (client, provider)
                logger.debug(f"Cached {provider} client")
        
        return client, provider
    
    @staticmethod
    def get_openai_client(key: str) -> OpenAI:
        """Legacy method for backward compatibility."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        return OpenAI(api_key=key)
    
    @staticmethod
    def clear_cache() -> None:
        """Clear the client cache."""
        with _cache_lock:
            _client_cache.clear()
            logger.info("Client cache cleared")
    
    @staticmethod
    def get_cache_info() -> Dict[str, int]:
        """Get information about the current client cache."""
        with _cache_lock:
            return {
                "cached_clients": len(_client_cache),
                "cache_keys": list(_client_cache.keys())
            }


def _extract_response_content(response: Any) -> str:
    """Extract content from AI response regardless of provider."""
    try:
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message'):
                message = choice.message
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Function calling response
                    tool_call = message.tool_calls[0]
                    if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments'):
                        import json
                        try:
                            args = json.loads(tool_call.function.arguments)
                            return args.get('answer', str(args))
                        except json.JSONDecodeError:
                            return tool_call.function.arguments
                elif hasattr(message, 'content') and message.content:
                    # Regular text response
                    return message.content
        
        # Fallback: convert to string
        return str(response)
    except Exception as e:
        logger.error(f"Failed to extract response content: {e}")
        return f"Error extracting response: {e}"


# Performance monitoring utilities
class AIMetrics:
    """Simple metrics collection for AI operations."""
    
    def __init__(self):
        self.call_count = 0
        self.total_time = 0.0
        self.error_count = 0
        self.last_call_time = None
        self._lock = threading.Lock()
    
    def record_call(self, duration: float, success: bool = True):
        """Record an AI call with timing and success status."""
        with self._lock:
            self.call_count += 1
            self.total_time += duration
            self.last_call_time = time.time()
            if not success:
                self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics."""
        with self._lock:
            avg_time = self.total_time / self.call_count if self.call_count > 0 else 0
            error_rate = self.error_count / self.call_count if self.call_count > 0 else 0
            
            return {
                "total_calls": self.call_count,
                "total_time": self.total_time,
                "average_time": avg_time,
                "error_count": self.error_count,
                "error_rate": error_rate,
                "last_call_time": self.last_call_time
            }
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self.call_count = 0
            self.total_time = 0.0
            self.error_count = 0
            self.last_call_time = None


# Global metrics instance
ai_metrics = AIMetrics()


def get_ai_metrics() -> Dict[str, Any]:
    """Get current AI metrics."""
    return ai_metrics.get_stats()


def reset_ai_metrics() -> None:
    """Reset AI metrics."""
    ai_metrics.reset()
