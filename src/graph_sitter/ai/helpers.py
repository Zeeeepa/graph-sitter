"""Abstract AI Helper base class and concrete implementations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

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


class AbstractAIHelper(ABC):
    """Abstract base class for AI helper implementations.
    
    This class defines the interface that all AI helpers must implement,
    providing a consistent API for different AI providers and operations.
    """
    
    @abstractmethod
    def embeddings_with_backoff(self, **kwargs) -> Any:
        """Get embeddings with exponential backoff retry logic.
        
        Args:
            **kwargs: Provider-specific parameters for embedding generation
            
        Returns:
            Embedding response from the AI provider
        """
        pass
    
    @abstractmethod
    def get_embeddings(self, content_strs: List[str]) -> List[List[float]]:
        """Get embeddings for a list of content strings.
        
        Args:
            content_strs: List of strings to generate embeddings for
            
        Returns:
            List of embedding vectors (one per input string)
        """
        pass
    
    @abstractmethod
    def get_embedding(self, content_str: str) -> List[float]:
        """Get embedding for a single content string.
        
        Args:
            content_str: String to generate embedding for
            
        Returns:
            Embedding vector for the input string
        """
        pass
    
    @abstractmethod
    def llm_query_with_retry(self, **kwargs) -> Any:
        """Query LLM with retry logic.
        
        Args:
            **kwargs: Provider-specific parameters for LLM query
            
        Returns:
            LLM response
        """
        pass
    
    @abstractmethod
    def llm_query_no_retry(
        self, 
        messages: List[Dict[str, str]] = None, 
        model: str = "gpt-4-32k", 
        max_tokens: int = 3000
    ) -> Any:
        """Query LLM without retry logic.
        
        Args:
            messages: List of message dictionaries for the conversation
            model: Model name to use for the query
            max_tokens: Maximum tokens in the response
            
        Returns:
            LLM response
        """
        pass
    
    @abstractmethod
    def llm_query_functions_with_retry(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]], 
        max_tokens: int
    ) -> Any:
        """Query LLM with function calling and retry logic.
        
        Args:
            model: Model name to use
            messages: Conversation messages
            functions: Function definitions for function calling
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response with function calls
        """
        pass
    
    @abstractmethod
    def llm_query_functions(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]], 
        max_tokens: Optional[int] = None
    ) -> Any:
        """Query LLM with function calling without retry logic.
        
        Args:
            model: Model name to use
            messages: Conversation messages
            functions: Function definitions for function calling
            max_tokens: Maximum tokens in response (optional)
            
        Returns:
            LLM response with function calls
        """
        pass
    
    @staticmethod
    @abstractmethod
    def llm_response_to_json(response: Any) -> str:
        """Convert LLM response to JSON string.
        
        Args:
            response: LLM response object
            
        Returns:
            JSON string representation of the response
        """
        pass


class OpenAIHelper(AbstractAIHelper):
    """OpenAI implementation of AbstractAIHelper."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize OpenAI helper.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for API calls
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def embeddings_with_backoff(self, **kwargs) -> Any:
        """Get embeddings with exponential backoff."""
        import time
        import random
        
        max_retries = kwargs.pop('max_retries', 3)
        base_delay = kwargs.pop('base_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                return self.client.embeddings.create(**kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Embedding request failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
    
    def get_embeddings(self, content_strs: List[str]) -> List[List[float]]:
        """Get embeddings for multiple strings."""
        try:
            response = self.embeddings_with_backoff(
                input=content_strs,
                model="text-embedding-3-small"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            raise
    
    def get_embedding(self, content_str: str) -> List[float]:
        """Get embedding for a single string."""
        embeddings = self.get_embeddings([content_str])
        return embeddings[0] if embeddings else []
    
    def llm_query_with_retry(self, **kwargs) -> Any:
        """Query LLM with retry logic."""
        import time
        import random
        
        max_retries = kwargs.pop('max_retries', 3)
        base_delay = kwargs.pop('base_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"LLM query failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
    
    def llm_query_no_retry(
        self, 
        messages: List[Dict[str, str]] = None, 
        model: str = "gpt-4-32k", 
        max_tokens: int = 3000
    ) -> Any:
        """Query LLM without retry logic."""
        if messages is None:
            messages = []
        
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
    
    def llm_query_functions_with_retry(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]], 
        max_tokens: int
    ) -> Any:
        """Query LLM with function calling and retry logic."""
        return self.llm_query_with_retry(
            model=model,
            messages=messages,
            tools=[{"type": "function", "function": func} for func in functions],
            max_tokens=max_tokens
        )
    
    def llm_query_functions(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]], 
        max_tokens: Optional[int] = None
    ) -> Any:
        """Query LLM with function calling without retry logic."""
        kwargs = {
            "model": model,
            "messages": messages,
            "tools": [{"type": "function", "function": func} for func in functions]
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        
        return self.client.chat.completions.create(**kwargs)
    
    @staticmethod
    def llm_response_to_json(response: Any) -> str:
        """Convert OpenAI response to JSON string."""
        import json
        
        try:
            # Extract the response content
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    message = choice.message
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        # Function calling response
                        tool_call = message.tool_calls[0]
                        return tool_call.function.arguments
                    elif hasattr(message, 'content'):
                        # Regular text response
                        return json.dumps({"content": message.content})
            
            # Fallback: convert entire response to JSON
            return json.dumps(str(response))
        except Exception as e:
            logger.error(f"Failed to convert response to JSON: {e}")
            return json.dumps({"error": str(e)})


class CodegenHelper(AbstractAIHelper):
    """Codegen SDK implementation of AbstractAIHelper."""
    
    def __init__(self, org_id: str, token: str):
        """Initialize Codegen helper.
        
        Args:
            org_id: Codegen organization ID
            token: Codegen API token
        """
        if not CODEGEN_AVAILABLE:
            raise ImportError("Codegen SDK not available. Install with: pip install codegen")
        
        self.agent = Agent(org_id=org_id, token=token)

    def embeddings_with_backoff(self, **kwargs) -> Any:
        """Codegen doesn't support embeddings directly."""
        raise NotImplementedError("Codegen SDK doesn't support embeddings directly")
    
    def get_embeddings(self, content_strs: List[str]) -> List[List[float]]:
        """Codegen doesn't support embeddings directly."""
        raise NotImplementedError("Codegen SDK doesn't support embeddings directly")
    
    def get_embedding(self, content_str: str) -> List[float]:
        """Codegen doesn't support embeddings directly."""
        raise NotImplementedError("Codegen SDK doesn't support embeddings directly")
    
    def llm_query_with_retry(self, **kwargs) -> Any:
        """Query using Codegen agent with retry logic."""
        import time
        import random
        
        max_retries = kwargs.pop('max_retries', 3)
        base_delay = kwargs.pop('base_delay', 1.0)
        
        # Convert messages to prompt
        messages = kwargs.get('messages', [])
        prompt = self._messages_to_prompt(messages)
        
        for attempt in range(max_retries):
            try:
                task = self.agent.run(prompt=prompt)
                
                # Wait for completion
                while task.status not in ["completed", "failed", "cancelled"]:
                    task.refresh()
                    time.sleep(1)
                
                if task.status == "completed":
                    return self._create_mock_response(task.result or "")
                else:
                    raise RuntimeError(f"Codegen task failed with status: {task.status}")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Codegen query failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
    
    def llm_query_no_retry(
        self, 
        messages: List[Dict[str, str]] = None, 
        model: str = "gpt-4-32k", 
        max_tokens: int = 3000
    ) -> Any:
        """Query using Codegen agent without retry logic."""
        if messages is None:
            messages = []
        
        prompt = self._messages_to_prompt(messages)
        task = self.agent.run(prompt=prompt)
        
        # Wait for completion
        while task.status not in ["completed", "failed", "cancelled"]:
            task.refresh()
        
        if task.status == "completed":
            return self._create_mock_response(task.result or "")
        else:
            raise RuntimeError(f"Codegen task failed with status: {task.status}")
    
    def llm_query_functions_with_retry(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]], 
        max_tokens: int
    ) -> Any:
        """Query with function calling using Codegen agent."""
        # Add function definitions to the prompt
        prompt = self._messages_to_prompt(messages)
        prompt += "\n\nAvailable functions:\n"
        for func in functions:
            prompt += f"- {func.get('name', 'unknown')}: {func.get('description', 'No description')}\n"
        
        return self.llm_query_with_retry(messages=[{"role": "user", "content": prompt}])
    
    def llm_query_functions(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        functions: List[Dict[str, Any]], 
        max_tokens: Optional[int] = None
    ) -> Any:
        """Query with function calling without retry logic."""
        # Add function definitions to the prompt
        prompt = self._messages_to_prompt(messages)
        prompt += "\n\nAvailable functions:\n"
        for func in functions:
            prompt += f"- {func.get('name', 'unknown')}: {func.get('description', 'No description')}\n"
        
        return self.llm_query_no_retry(messages=[{"role": "user", "content": prompt}])
    
    @staticmethod
    def llm_response_to_json(response: Any) -> str:
        """Convert Codegen response to JSON string."""
        import json
        
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls'):
                    tool_call = choice.message.tool_calls[0]
                    return tool_call.function.arguments
            
            return json.dumps({"content": str(response)})
        except Exception as e:
            logger.error(f"Failed to convert Codegen response to JSON: {e}")
            return json.dumps({"error": str(e)})
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string."""
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
        
        return "\n\n".join(prompt_parts)
    
    def _create_mock_response(self, content: str) -> Any:
        """Create a mock response object that matches OpenAI's structure."""
        import json
        
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
                self.arguments = json.dumps({"answer": content})
        
        class MockResponse:
            def __init__(self, content: str):
                self.choices = [MockChoice(content)]
        
        return MockResponse(content)


def create_ai_helper(
    openai_api_key: Optional[str] = None,
    codegen_org_id: Optional[str] = None,
    codegen_token: Optional[str] = None,
    prefer_codegen: bool = True
) -> AbstractAIHelper:
    """Create an AI helper instance with intelligent provider selection.
    
    Args:
        openai_api_key: OpenAI API key
        codegen_org_id: Codegen organization ID
        codegen_token: Codegen API token
        prefer_codegen: Whether to prefer Codegen over OpenAI when both are available
        
    Returns:
        AbstractAIHelper instance
        
    Raises:
        ValueError: If no valid credentials are provided
    """
    has_codegen = bool(codegen_org_id and codegen_token)
    has_openai = bool(openai_api_key)
    
    if not has_codegen and not has_openai:
        raise ValueError(
            "No AI credentials provided. Please set either:\n"
            "- Codegen credentials: codegen_org_id and codegen_token\n"
            "- OpenAI credentials: openai_api_key"
        )
    
    if prefer_codegen and has_codegen:
        try:
            return CodegenHelper(org_id=codegen_org_id, token=codegen_token)
        except ImportError:
            logger.warning("Codegen SDK not available, falling back to OpenAI")
            if has_openai:
                return OpenAIHelper(api_key=openai_api_key)
            else:
                raise ValueError("Codegen SDK not available and no OpenAI key provided")
    elif has_openai:
        return OpenAIHelper(api_key=openai_api_key)
    elif has_codegen:
        try:
            return CodegenHelper(org_id=codegen_org_id, token=codegen_token)
        except ImportError:
            raise ValueError("Codegen SDK not available and no OpenAI key provided")
    else:
        raise ValueError("No valid AI credentials provided")
