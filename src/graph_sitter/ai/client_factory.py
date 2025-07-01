"""AI Client Factory for unified client creation and provider management."""

import logging
from typing import Any, Protocol, runtime_checkable

from openai import OpenAI

logger = logging.getLogger(__name__)


@runtime_checkable
class AIClient(Protocol):
    """Protocol for AI clients to ensure compatibility."""
    
    def chat_completions_create(self, **kwargs) -> Any:
        """Create a chat completion."""
        ...


class CodegenAIClient:
    """Wrapper for Codegen SDK to match OpenAI interface."""
    
    def __init__(self, org_id: str, token: str):
        try:
            from codegen import Agent
            self.agent = Agent(org_id=org_id, token=token)
        except ImportError as e:
            raise ImportError("Codegen SDK not available. Install with: pip install codegen") from e
    
    @property
    def chat(self):
        """Provide chat interface similar to OpenAI."""
        return self
    
    @property
    def completions(self):
        """Provide completions interface similar to OpenAI."""
        return self
    
    def create(self, **kwargs) -> Any:
        """Create a completion using Codegen SDK."""
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
        
        # Wait for completion and get result
        while task.status not in ["completed", "failed", "cancelled"]:
            task.refresh()
        
        if task.status == "completed":
            # Create a response object that matches OpenAI's structure
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
            
            return MockResponse(task.result or "")
        else:
            raise RuntimeError(f"Codegen task failed with status: {task.status}")


class AIClientFactory:
    """Factory for creating AI clients with automatic provider selection."""
    
    @staticmethod
    def create_client(
        openai_api_key: str | None = None,
        codegen_org_id: str | None = None,
        codegen_token: str | None = None,
        prefer_codegen: bool = True
    ) -> tuple[Any, str]:
        """Create an AI client with intelligent provider selection.
        
        Args:
            openai_api_key: OpenAI API key
            codegen_org_id: Codegen organization ID
            codegen_token: Codegen token
            prefer_codegen: Whether to prefer Codegen over OpenAI when both are available
            
        Returns:
            Tuple of (client, provider_name)
            
        Raises:
            ValueError: If no valid credentials are provided
        """
        # Check Codegen credentials
        has_codegen = bool(codegen_org_id and codegen_token)
        has_openai = bool(openai_api_key)
        
        if not has_codegen and not has_openai:
            raise ValueError(
                "No AI credentials provided. Please set either:\n"
                "- Codegen credentials: codegen_org_id and codegen_token\n"
                "- OpenAI credentials: openai_api_key"
            )
        
        # Determine which provider to use
        if prefer_codegen and has_codegen:
            try:
                logger.info("Creating Codegen AI client...")
                client = CodegenAIClient(org_id=codegen_org_id, token=codegen_token)
                return client, "codegen"
            except ImportError:
                logger.warning("Codegen SDK not available, falling back to OpenAI")
                if has_openai:
                    logger.info("Creating OpenAI client...")
                    client = OpenAI(api_key=openai_api_key)
                    return client, "openai"
                else:
                    raise ValueError("Codegen SDK not available and no OpenAI key provided")
        elif has_openai:
            logger.info("Creating OpenAI client...")
            client = OpenAI(api_key=openai_api_key)
            return client, "openai"
        elif has_codegen:
            try:
                logger.info("Creating Codegen AI client...")
                client = CodegenAIClient(org_id=codegen_org_id, token=codegen_token)
                return client, "codegen"
            except ImportError:
                raise ValueError("Codegen SDK not available and no OpenAI key provided")
        else:
            raise ValueError("No valid AI credentials provided")
    
    @staticmethod
    def get_openai_client(key: str) -> OpenAI:
        """Legacy method for backward compatibility."""
        return OpenAI(api_key=key)

