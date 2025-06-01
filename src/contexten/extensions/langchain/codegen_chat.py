"""
LangChain wrapper for Codegen SDK

Provides a LangChain-compatible interface for the Codegen SDK,
allowing it to be used as a chat model in LangChain applications.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class ChatCodegen(BaseChatModel):
    """LangChain wrapper for Codegen SDK"""
    
    org_id: str = Field(description="Codegen organization ID")
    token: str = Field(description="Codegen API token")
    model_name: str = Field(default="codegen-agent", description="Model identifier for Codegen")
    temperature: float = Field(default=0.1, description="Temperature parameter", ge=0, le=1)
    max_tokens: Optional[int] = Field(default=4000, description="Maximum tokens to generate")
    timeout: int = Field(default=300, description="Request timeout in seconds")
    
    def __init__(self, org_id: str, token: str, **kwargs):
        """Initialize ChatCodegen with credentials"""
        super().__init__(org_id=org_id, token=token, **kwargs)
        self._agent = None
    
    @property
    def agent(self):
        """Lazy initialization of Codegen agent"""
        if self._agent is None:
            try:
                from codegen import Agent
                self._agent = Agent(org_id=self.org_id, token=self.token)
            except ImportError as e:
                raise ImportError(
                    "Codegen SDK not available. Install with: pip install codegen"
                ) from e
        return self._agent
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM class"""
        return "codegen_chat"
    
    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert LangChain messages to a single prompt for Codegen"""
        prompt_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            else:
                # Generic message
                prompt_parts.append(f"{message.__class__.__name__}: {message.content}")
        
        return "\n\n".join(prompt_parts)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion using Codegen SDK"""
        
        # Convert messages to prompt
        prompt = self._convert_messages_to_prompt(messages)
        
        # Add any additional context from kwargs
        if kwargs:
            context_info = []
            for key, value in kwargs.items():
                if key not in ['stop', 'run_manager']:
                    context_info.append(f"{key}: {value}")
            if context_info:
                prompt += f"\n\nAdditional Context:\n" + "\n".join(context_info)
        
        try:
            # Run the task synchronously using asyncio
            result = asyncio.run(self._async_generate(prompt))
            
            # Create ChatGeneration
            generation = ChatGeneration(
                message=AIMessage(content=result["content"]),
                generation_info={
                    "provider": "codegen_sdk",
                    "model": self.model_name,
                    "tokens_used": result.get("tokens_used", 0),
                    "generation_time": result.get("generation_time", 0),
                    "cost_estimate": result.get("cost_estimate", 0.0)
                }
            )
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            # If Codegen SDK fails, provide a helpful error message
            error_msg = f"Codegen SDK error: {str(e)}"
            if run_manager:
                run_manager.on_llm_error(e)
            
            # Return an error response instead of raising
            generation = ChatGeneration(
                message=AIMessage(content=f"Error: {error_msg}"),
                generation_info={"error": error_msg, "provider": "codegen_sdk"}
            )
            return ChatResult(generations=[generation])
    
    async def _async_generate(self, prompt: str) -> Dict[str, Any]:
        """Async generation using Codegen SDK"""
        start_time = time.time()
        
        try:
            # Create task with Codegen SDK
            task = self.agent.run(prompt=prompt)
            
            # Wait for completion
            result = await self._wait_for_completion(task)
            
            generation_time = time.time() - start_time
            
            return {
                "content": result.get("content", ""),
                "tokens_used": result.get("tokens_used", 0),
                "cost_estimate": result.get("cost_estimate", 0.0),
                "generation_time": generation_time,
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            raise Exception(f"Codegen SDK generation failed: {str(e)}")
    
    async def _wait_for_completion(self, task, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Wait for Codegen SDK task completion"""
        timeout = timeout or self.timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                task.refresh()
                
                if task.status == "completed":
                    return {
                        "content": task.result or "",
                        "metadata": getattr(task, "metadata", {}),
                        "tokens_used": getattr(task, "tokens_used", 0),
                        "cost_estimate": getattr(task, "cost_estimate", 0.0)
                    }
                elif task.status == "failed":
                    error_msg = getattr(task, "error", "Unknown error")
                    raise Exception(f"Task failed: {error_msg}")
                
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
    
    @classmethod
    def from_env(cls, **kwargs) -> "ChatCodegen":
        """Create ChatCodegen instance from environment variables"""
        org_id = os.getenv("CODEGEN_ORG_ID")
        token = os.getenv("CODEGEN_TOKEN")
        
        if not org_id:
            raise ValueError(
                "CODEGEN_ORG_ID not found in environment. "
                "Please set it in your .env file or environment variables."
            )
        
        if not token:
            raise ValueError(
                "CODEGEN_TOKEN not found in environment. "
                "Please set it in your .env file or environment variables."
            )
        
        return cls(org_id=org_id, token=token, **kwargs)
    
    def get_num_tokens(self, text: str) -> int:
        """Estimate number of tokens in text"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters for this model"""
        return {
            "model_name": self.model_name,
            "org_id": self.org_id[:8] + "..." if len(self.org_id) > 8 else self.org_id,  # Partial for privacy
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout
        }

