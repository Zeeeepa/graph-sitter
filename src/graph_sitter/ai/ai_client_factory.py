"""
AI Client Factory and Abstraction Layer

Provides a unified interface for working with different AI providers
(OpenAI, Codegen SDK) with automatic fallback and configuration-based selection.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from graph_sitter.ai.client import get_openai_client
from graph_sitter.configs.models.secrets import SecretsConfig
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class AIResponse:
    """Standardized AI response format"""
    
    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        provider: str = "unknown",
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        generation_time: float = 0.0
    ):
        self.content = content
        self.metadata = metadata or {}
        self.provider = provider
        self.tokens_used = tokens_used
        self.cost_estimate = cost_estimate
        self.generation_time = generation_time


class AIClientInterface(ABC):
    """Abstract interface for AI clients"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate AI response for the given prompt"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI client is properly configured and available"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the AI provider"""
        pass


class OpenAIClient(AIClientInterface):
    """OpenAI client implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = get_openai_client(self.api_key)
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response using OpenAI API"""
        start_time = time.time()
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request parameters
            request_params = {
                "model": kwargs.get("model", "gpt-4"),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 4000),
            }
            
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = kwargs.get("tool_choice", "auto")
            
            # Make API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract content
            content = ""
            if response.choices[0].message.content:
                content = response.choices[0].message.content
            elif response.choices[0].message.tool_calls:
                # Handle tool calls
                tool_calls = response.choices[0].message.tool_calls
                for tool_call in tool_calls:
                    if tool_call.function.name == "set_answer":
                        import json
                        args = json.loads(tool_call.function.arguments)
                        content = args.get("answer", "")
                        break
            
            generation_time = time.time() - start_time
            
            return AIResponse(
                content=content,
                metadata={
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "tool_calls": response.choices[0].message.tool_calls
                },
                provider="openai",
                tokens_used=response.usage.total_tokens if response.usage else 0,
                cost_estimate=self._estimate_cost(response.usage.total_tokens if response.usage else 0),
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available"""
        return bool(self.api_key)
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _estimate_cost(self, tokens: int) -> float:
        """Rough cost estimation for GPT-4"""
        # Approximate cost per 1K tokens for GPT-4
        cost_per_1k = 0.03  # This is a rough estimate
        return (tokens / 1000) * cost_per_1k


class CodegenSDKClient(AIClientInterface):
    """Codegen SDK client implementation"""
    
    def __init__(self, org_id: str, token: str):
        self.org_id = org_id
        self.token = token
        self._agent = None
    
    @property
    def agent(self):
        if self._agent is None:
            try:
                from codegen import Agent
                self._agent = Agent(org_id=self.org_id, token=self.token)
            except ImportError:
                logger.error("Codegen SDK not available. Install with: pip install codegen")
                raise ImportError("Codegen SDK not installed")
        return self._agent
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response using Codegen SDK"""
        start_time = time.time()
        
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Run task via Codegen SDK
            task = self.agent.run(prompt=full_prompt)
            
            # Wait for completion
            result = await self._wait_for_completion(task, kwargs.get("timeout", 300))
            
            generation_time = time.time() - start_time
            
            return AIResponse(
                content=result.get("content", ""),
                metadata=result.get("metadata", {}),
                provider="codegen_sdk",
                tokens_used=result.get("tokens_used", 0),
                cost_estimate=result.get("cost_estimate", 0.0),
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"Codegen SDK error: {str(e)}")
            raise
    
    async def _wait_for_completion(self, task, timeout: int = 300) -> Dict[str, Any]:
        """Wait for Codegen SDK task completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                task.refresh()
                
                if task.status == "completed":
                    return {
                        "content": task.result,
                        "metadata": getattr(task, "metadata", {}),
                        "tokens_used": getattr(task, "tokens_used", 0),
                        "cost_estimate": getattr(task, "cost_estimate", 0.0)
                    }
                elif task.status == "failed":
                    raise Exception(f"Task failed: {getattr(task, 'error', 'Unknown error')}")
                
                await asyncio.sleep(2)  # Wait 2 seconds before checking again
                
            except Exception as e:
                if "completed" in str(e).lower():
                    # Task might be completed but with an error in status check
                    return {
                        "content": getattr(task, "result", ""),
                        "metadata": {},
                        "tokens_used": 0,
                        "cost_estimate": 0.0
                    }
                raise
        
        raise TimeoutError(f"Task timed out after {timeout} seconds")
    
    def is_available(self) -> bool:
        """Check if Codegen SDK client is available"""
        try:
            return bool(self.org_id and self.token and self.agent)
        except ImportError:
            return False
    
    @property
    def provider_name(self) -> str:
        return "codegen_sdk"


class AIClientFactory:
    """Factory for creating AI clients with automatic provider selection"""
    
    @staticmethod
    def create_client(secrets: SecretsConfig, preferred_provider: Optional[str] = None) -> AIClientInterface:
        """
        Create an AI client based on available credentials and preferences
        
        Args:
            secrets: SecretsConfig containing API credentials
            preferred_provider: Optional preferred provider ("openai" or "codegen_sdk")
            
        Returns:
            AIClientInterface: Configured AI client
            
        Raises:
            ValueError: If no valid credentials are available
        """
        
        # Check Codegen SDK availability
        codegen_available = bool(secrets.codegen_org_id and secrets.codegen_token)
        
        # Check OpenAI availability
        openai_available = bool(secrets.openai_api_key)
        
        # Determine which client to use
        if preferred_provider == "codegen_sdk" and codegen_available:
            logger.info("Using Codegen SDK client (preferred)")
            return CodegenSDKClient(secrets.codegen_org_id, secrets.codegen_token)
        elif preferred_provider == "openai" and openai_available:
            logger.info("Using OpenAI client (preferred)")
            return OpenAIClient(secrets.openai_api_key)
        elif codegen_available:
            logger.info("Using Codegen SDK client (auto-selected)")
            return CodegenSDKClient(secrets.codegen_org_id, secrets.codegen_token)
        elif openai_available:
            logger.info("Using OpenAI client (auto-selected)")
            return OpenAIClient(secrets.openai_api_key)
        else:
            raise ValueError(
                "No AI provider credentials available. Please set either:\n"
                "- Codegen SDK: codegen_org_id and codegen_token\n"
                "- OpenAI: openai_api_key"
            )
    
    @staticmethod
    def get_available_providers(secrets: SecretsConfig) -> List[str]:
        """Get list of available AI providers based on credentials"""
        providers = []
        
        if secrets.codegen_org_id and secrets.codegen_token:
            providers.append("codegen_sdk")
        
        if secrets.openai_api_key:
            providers.append("openai")
        
        return providers

