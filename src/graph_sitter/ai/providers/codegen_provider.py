"""
Enhanced Codegen SDK provider implementation with robust error handling.
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional

from .base import AIProvider, AIResponse

logger = logging.getLogger(__name__)


class CodegenProvider(AIProvider):
    """Enhanced Codegen SDK provider with robust error handling and monitoring."""
    
    provider_name = "codegen"
    
    def __init__(
        self, 
        org_id: Optional[str] = None,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Codegen provider.
        
        Args:
            org_id: Codegen organization ID (defaults to CODEGEN_ORG_ID env var)
            token: Codegen API token (defaults to CODEGEN_TOKEN env var)
            base_url: API base URL (defaults to CODEGEN_BASE_URL env var)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        self.org_id = org_id or os.getenv("CODEGEN_ORG_ID")
        self.token = token or os.getenv("CODEGEN_TOKEN")
        self.base_url = base_url or os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com")
        self.timeout = kwargs.get("timeout", 300)
        self.max_retries = kwargs.get("max_retries", 3)
        
        self._agent = None
        if self.org_id and self.token:
            try:
                # Import here to avoid circular imports
                from codegen import Agent
                self._agent = Agent(
                    org_id=self.org_id,
                    token=self.token,
                    base_url=self.base_url,
                    timeout=self.timeout,
                    max_retries=self.max_retries
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Codegen agent: {e}")
    
    def _check_availability(self) -> bool:
        """Check if Codegen SDK is available and properly configured."""
        if not self.org_id or not self.token:
            logger.debug("Codegen credentials not found")
            return False
        
        if not self._agent:
            logger.debug("Codegen agent not initialized")
            return False
        
        try:
            # Test credentials by attempting to list repositories
            self._agent.get_repositories()
            return True
        except Exception as e:
            logger.debug(f"Codegen availability check failed: {e}")
            return False
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        priority: str = "normal",
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate response using Codegen SDK.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (combined with prompt)
            model: Model preference (Codegen uses agents, not specific models)
            temperature: Sampling temperature (informational)
            max_tokens: Maximum tokens (informational)
            priority: Task priority ("low", "normal", "high")
            repository: Target repository
            branch: Target branch
            tags: Task tags for organization
            **kwargs: Additional Codegen parameters
            
        Returns:
            AIResponse object
        """
        if not self.is_available:
            raise RuntimeError("Codegen provider is not available")
        
        start_time = time.time()
        
        try:
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Prepare context for the task
            context = {}
            if tags:
                context["tags"] = tags
            if temperature != 0.0:
                context["temperature"] = temperature
            if max_tokens:
                context["max_tokens"] = max_tokens
            
            # Create and run task
            task = self._agent.run(
                prompt=full_prompt,
                context=context if context else None,
                repository=repository,
                branch=branch,
                priority=priority,
                **kwargs
            )
            
            # Wait for completion with timeout
            task.wait_for_completion(timeout=self.timeout)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record statistics
            self._record_request(response_time, error=False)
            
            # Get task result
            content = task.result or "Task completed successfully"
            
            # Prepare metadata
            metadata = {
                "task_id": task.task_id,
                "status": task.status,
                "priority": priority,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            
            if repository:
                metadata["repository"] = repository
            if branch:
                metadata["branch"] = branch
            if tags:
                metadata["tags"] = tags
            
            return AIResponse(
                content=content,
                provider_name=self.provider_name,
                model=model or "codegen-agent",
                usage=None,  # Codegen doesn't provide token usage
                response_time=response_time,
                request_id=task.task_id,
                metadata=metadata
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self._record_request(response_time, error=True)
            
            logger.error(f"Codegen request failed: {e}")
            raise RuntimeError(f"Codegen request failed: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Codegen models/agents."""
        return ["codegen-agent", "codegen-swe", "codegen-research"]
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics specific to Codegen."""
        base_stats = self.get_stats()
        
        enhanced_stats = {
            **base_stats,
            "provider_type": "codegen",
            "org_id": self.org_id,
            "credentials_configured": bool(self.org_id and self.token),
            "agent_initialized": bool(self._agent),
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
        
        # Add task-specific stats if agent is available
        if self._agent:
            try:
                usage = self._agent.get_usage()
                enhanced_stats.update({
                    "task_count": usage.get("total_tasks", 0),
                    "completed_tasks": usage.get("completed_tasks", 0),
                    "failed_tasks": usage.get("failed_tasks", 0)
                })
            except Exception as e:
                logger.debug(f"Failed to get Codegen usage stats: {e}")
        
        return enhanced_stats
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get available repositories for the organization."""
        if not self.is_available:
            return []
        
        try:
            return self._agent.get_repositories()
        except Exception as e:
            logger.warning(f"Failed to get repositories: {e}")
            return []
    
    def create_task(
        self,
        prompt: str,
        priority: str = "normal",
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        **kwargs
    ):
        """
        Create a task without waiting for completion.
        
        Returns the Task object for manual monitoring.
        """
        if not self.is_available:
            raise RuntimeError("Codegen provider is not available")
        
        return self._agent.run(
            prompt=prompt,
            priority=priority,
            repository=repository,
            branch=branch,
            **kwargs
        )

