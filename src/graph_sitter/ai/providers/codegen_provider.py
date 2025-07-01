"""
Codegen SDK provider implementation.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from codegen import Agent
from codegen.exceptions import CodegenError

from .base import AIProvider, AIResponse

logger = logging.getLogger(__name__)


class CodegenProvider(AIProvider):
    """Codegen SDK provider implementation."""
    
    def __init__(self, org_id: Optional[str] = None, token: Optional[str] = None, **kwargs):
        """
        Initialize Codegen provider.
        
        Args:
            org_id: Codegen organization ID (if not provided, will use CODEGEN_ORG_ID env var)
            token: Codegen API token (if not provided, will use CODEGEN_TOKEN env var)
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        self.org_id = org_id or os.getenv("CODEGEN_ORG_ID")
        self.token = token or os.getenv("CODEGEN_TOKEN")
        self._agent = None
        
        if self.org_id and self.token:
            try:
                self._agent = Agent(org_id=self.org_id, token=self.token)
            except Exception as e:
                logger.warning(f"Failed to initialize Codegen agent: {e}")
    
    @property
    def provider_name(self) -> str:
        """Return the name of the AI provider."""
        return "Codegen"
    
    @property
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured."""
        return self.org_id is not None and self.token is not None and self._agent is not None
    
    @property
    def agent(self) -> Agent:
        """Get the Codegen agent."""
        if not self._agent:
            if not self.org_id or not self.token:
                raise ValueError("Codegen org_id and token not provided")
            self._agent = Agent(org_id=self.org_id, token=self.token)
        return self._agent
    
    def validate_credentials(self) -> bool:
        """Validate the provider credentials."""
        if not self.is_available:
            return False
        
        try:
            # Try to get usage statistics to validate credentials
            self.agent.get_usage()
            return True
        except Exception as e:
            logger.warning(f"Codegen credential validation failed: {e}")
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
        """Generate a response using Codegen SDK."""
        
        if not self.is_available:
            raise ValueError("Codegen provider is not available")
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        # Prepare context for the Codegen agent
        context = {}
        if tools:
            context["available_tools"] = tools
        if temperature != 0.0:
            context["temperature"] = temperature
        if max_tokens:
            context["max_tokens"] = max_tokens
        
        # Add any additional kwargs to context
        context.update(kwargs)
        
        try:
            # Run the Codegen agent task
            task = self.agent.run(
                prompt=full_prompt,
                context=context if context else None,
                priority="normal"
            )
            
            # Wait for completion (with a reasonable timeout)
            task.wait_for_completion(timeout=300, poll_interval=5)
            
            # Get the result
            result = task.result or ""
            
            return AIResponse(
                content=result,
                provider=self.provider_name,
                model=model or "codegen-agent",
                usage={
                    "task_id": task.task_id,
                    "status": task.status
                },
                metadata={
                    "task_id": task.task_id,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "artifacts": task.get_artifacts()
                },
                raw_response=task
            )
            
        except CodegenError as e:
            logger.error(f"Codegen API call failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Codegen provider: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available Codegen models."""
        return [
            "codegen-agent",
            "codegen-swe-agent",
            "codegen-code-agent",
            "codegen-chat-agent"
        ]
    
    def get_default_model(self) -> str:
        """Get the default model for Codegen."""
        return "codegen-agent"

