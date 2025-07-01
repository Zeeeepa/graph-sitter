"""
Enhanced Codegen SDK provider implementation with robust error handling and monitoring.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from codegen import Agent
from codegen.cli.errors import CodegenError, AuthError as CodegenAuthError

from .base import (
    AIProvider, 
    AIResponse, 
    ProviderUnavailableError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError
)

logger = logging.getLogger(__name__)


class CodegenProvider(AIProvider):
    """Enhanced Codegen SDK provider implementation with comprehensive error handling."""
    
    def __init__(
        self, 
        org_id: Optional[str] = None, 
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 300,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize enhanced Codegen provider.
        
        Args:
            org_id: Codegen organization ID (if not provided, will use CODEGEN_ORG_ID env var)
            token: Codegen API token (if not provided, will use CODEGEN_TOKEN env var)
            base_url: Custom base URL for Codegen API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        self.org_id = org_id or os.getenv("CODEGEN_ORG_ID")
        self.token = token or os.getenv("CODEGEN_TOKEN")
        self.base_url = base_url or os.getenv("CODEGEN_BASE_URL", "https://codegen-sh-rest-api.modal.run")
        self.timeout = timeout
        self.max_retries = max_retries
        self._agent = None
        self._last_validation_time: Optional[float] = None
        self._validation_cache_duration = 300  # 5 minutes
        self._credentials_validated: Optional[bool] = None
        
        # Enhanced monitoring
        self._task_count = 0
        self._successful_tasks = 0
        self._failed_tasks = 0
        
        if self.org_id and self.token:
            try:
                self._initialize_agent()
            except Exception as e:
                self.logger.warning(f"Failed to initialize Codegen agent: {e}")
    
    def _initialize_agent(self):
        """Initialize the Codegen agent with enhanced configuration."""
        try:
            self._agent = Agent(
                org_id=self.org_id,
                token=self.token,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
                enable_logging=True
            )
            self.logger.info("Codegen agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Codegen agent: {e}")
            raise ProviderUnavailableError(f"Failed to initialize Codegen agent: {e}")
    
    @property
    def provider_name(self) -> str:
        """Return the name of the AI provider."""
        return "Codegen"
    
    @property
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured."""
        return (
            self.org_id is not None and 
            self.token is not None and 
            self._agent is not None
        )
    
    @property
    def agent(self) -> Agent:
        """Get the Codegen agent instance."""
        if not self._agent:
            if not self.org_id or not self.token:
                raise ProviderUnavailableError("Codegen org_id and token not provided")
            self._initialize_agent()
        
        if not self._agent:
            raise ProviderUnavailableError("Failed to initialize Codegen agent")
            
        return self._agent  # Return Agent instance instead of None
    
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
            # Try to get usage statistics to validate credentials
            self.agent.get_usage()
            self._last_validation_time = current_time
            self.logger.info("Codegen credentials validated successfully")
            return True
        except CodegenAuthError:
            self.logger.error("Codegen credential validation failed: Authentication error")
            return False
        except Exception as e:
            self.logger.warning(f"Codegen credential validation failed: {e}")
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
        priority: str = "normal",
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate a response using enhanced Codegen SDK."""
        
        if not self.is_available:
            raise ProviderUnavailableError("Codegen provider is not available")
        
        start_time = time.time()
        request_id = f"codegen_{int(start_time * 1000)}"
        
        try:
            self._record_request()
            
            # Prepare the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            # Prepare enhanced context for the Codegen agent
            context = {
                "request_id": request_id,
                "model_preference": model or "codegen-agent",
                "temperature": temperature,
                "provider": "enhanced-codegen-sdk"
            }
            
            if tools:
                context["available_tools"] = tools
                context["tool_choice"] = tool_choice
            if max_tokens:
                context["max_tokens"] = max_tokens
            if tags:
                context["tags"] = tags
            
            # Add any additional kwargs to context
            context.update(kwargs)
            
            self.logger.info(f"[{request_id}] Creating Codegen task: {prompt[:100]}...")
            
            # Run the Codegen agent task with enhanced options
            task = self.agent.run(
                prompt=full_prompt,
                context=context if context else None,
                priority=priority,
                repository=repository,
                branch=branch,
                tags=tags,
                timeout=self.timeout
            )
            
            self._task_count += 1
            
            # Wait for completion with progress monitoring
            def progress_callback(progress_info):
                if progress_info:
                    self.logger.debug(f"[{request_id}] Task progress: {progress_info}")
            
            try:
                task.wait_for_completion(
                    timeout=self.timeout, 
                    poll_interval=5,
                    progress_callback=progress_callback
                )
                
                self._successful_tasks += 1
                
            except Exception as task_error:
                self._failed_tasks += 1
                self._record_request(success=False)
                
                if "timeout" in str(task_error).lower():
                    raise ProviderTimeoutError(f"Codegen task timed out: {task_error}")
                elif "rate limit" in str(task_error).lower():
                    raise ProviderRateLimitError(f"Codegen rate limit exceeded: {task_error}")
                else:
                    raise ProviderUnavailableError(f"Codegen task failed: {task_error}")
            
            # Get the result and artifacts
            result = task.result or ""
            artifacts = task.get_artifacts()
            
            response_time = time.time() - start_time
            
            self.logger.info(f"[{request_id}] Codegen task completed in {response_time:.2f}s")
            
            return AIResponse(
                content=result,
                provider_name=self.provider_name,
                model=model or "codegen-agent",
                usage={
                    "task_id": task.task_id,
                    "status": task.status,
                    "duration": task.duration,
                    "artifacts_count": len(artifacts)
                },
                metadata={
                    "request_id": request_id,
                    "task_id": task.task_id,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "artifacts": artifacts,
                    "logs_count": len(task.get_logs()),
                    "priority": priority,
                    "repository": repository,
                    "branch": branch,
                    "tags": tags
                },
                raw_response=task,
                response_time=response_time,
                request_id=request_id
            )
            
        except CodegenError as e:
            self._record_request(success=False)
            self.logger.error(f"[{request_id}] Codegen API call failed: {e}")
            
            if isinstance(e, CodegenAuthError):
                raise ProviderAuthenticationError(f"Codegen authentication failed: {e}")
            elif "rate limit" in str(e).lower():
                raise ProviderRateLimitError(f"Codegen rate limit exceeded: {e}")
            elif "timeout" in str(e).lower():
                raise ProviderTimeoutError(f"Codegen request timed out: {e}")
            else:
                raise ProviderUnavailableError(f"Codegen API error: {e}")
        
        except Exception as e:
            self._record_request(success=False)
            self.logger.error(f"[{request_id}] Unexpected error in Codegen provider: {e}")
            raise ProviderUnavailableError(f"Unexpected Codegen error: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Codegen models."""
        return [
            "codegen-agent",
            "codegen-swe-agent",
            "codegen-code-agent", 
            "codegen-chat-agent",
            "codegen-review-agent",
            "codegen-debug-agent"
        ]
    
    def get_default_model(self) -> str:
        """Get the default model for Codegen."""
        return "codegen-agent"
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced provider statistics."""
        base_stats = self.get_stats()
        
        return {
            **base_stats,
            "task_count": self._task_count,
            "successful_tasks": self._successful_tasks,
            "failed_tasks": self._failed_tasks,
            "success_rate": self._successful_tasks / max(self._task_count, 1),
            "org_id": self.org_id,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "last_validation_time": self._last_validation_time
        }
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get usage information from Codegen API."""
        if not self.is_available:
            return {}
        
        try:
            return self.agent.get_usage()
        except Exception as e:
            self.logger.warning(f"Failed to get Codegen usage info: {e}")
            return {}
    
    def list_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks from Codegen API."""
        if not self.is_available:
            return []
        
        try:
            tasks = self.agent.list_tasks(limit=limit)
            return [
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "created_at": task.created_at,
                    "prompt": task.prompt[:100] if task.prompt else None
                }
                for task in tasks
            ]
        except Exception as e:
            self.logger.warning(f"Failed to get recent Codegen tasks: {e}")
            return []
