"""Core Codegen SDK client implementation."""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional

from codegen.agents.agent import Agent

from .config import AutogenConfig, get_config
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    TaskError,
    TimeoutError,
)
from .models import TaskRequest, TaskResponse, TaskStatus
from .retry import RetryHandler
from .tracking import UsageTracker

logger = logging.getLogger(__name__)


class AutogenClient:
    """Main client for interacting with Codegen SDK."""
    
    def __init__(self, config: Optional[AutogenConfig] = None):
        """Initialize the Codegen client.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config or get_config()
        self._agent: Optional[Agent] = None
        self._retry_handler = RetryHandler(self.config)
        self._usage_tracker = UsageTracker(self.config)
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"AutogenClient initialized for org_id: {self.config.org_id}")
    
    def _validate_config(self) -> None:
        """Validate the configuration."""
        if not self.config.org_id:
            raise ConfigurationError("org_id is required")
        
        if not self.config.token:
            raise ConfigurationError("token is required")
    
    @property
    def agent(self) -> Agent:
        """Get or create the Codegen agent instance."""
        if self._agent is None:
            try:
                self._agent = Agent(
                    org_id=self.config.org_id,
                    token=self.config.token,
                    base_url=self.config.api_base_url,
                )
                logger.info("Codegen agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Codegen agent: {e}")
                raise AuthenticationError(f"Failed to authenticate with Codegen: {e}")
        
        return self._agent
    
    def run_task(self, request: TaskRequest) -> TaskResponse:
        """Run a task synchronously.
        
        Args:
            request: Task request containing prompt and configuration.
            
        Returns:
            TaskResponse with task details and result.
            
        Raises:
            TaskError: If task execution fails.
            TimeoutError: If task exceeds timeout.
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting task {task_id}: {request.prompt[:100]}...")
        
        try:
            # Track usage
            self._usage_tracker.track_request()
            
            # Execute task with retry logic
            def _execute_task():
                return self.agent.run(prompt=request.prompt)
            
            codegen_task = self._retry_handler.execute_with_retry(_execute_task)
            
            # Monitor task completion
            timeout = request.timeout or self.config.task_timeout
            elapsed = 0
            
            while codegen_task.status not in ["completed", "failed"] and elapsed < timeout:
                time.sleep(1)
                codegen_task.refresh()
                elapsed = time.time() - start_time
            
            if elapsed >= timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
            
            # Create response
            status = TaskStatus.COMPLETED if codegen_task.status == "completed" else TaskStatus.FAILED
            
            response = TaskResponse(
                task_id=task_id,
                status=status,
                result=codegen_task.result if status == TaskStatus.COMPLETED else None,
                error=getattr(codegen_task, 'error', None) if status == TaskStatus.FAILED else None,
                created_at=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
                updated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={
                    "elapsed_time": time.time() - start_time,
                    "codegen_task_id": getattr(codegen_task, 'id', None),
                }
            )
            
            # Track successful completion
            if status == TaskStatus.COMPLETED:
                self._usage_tracker.track_success()
                logger.info(f"Task {task_id} completed successfully in {response.metadata['elapsed_time']:.2f}s")
            else:
                self._usage_tracker.track_failure()
                logger.error(f"Task {task_id} failed: {response.error}")
            
            return response
            
        except Exception as e:
            self._usage_tracker.track_failure()
            logger.error(f"Task {task_id} failed with exception: {e}")
            
            return TaskResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                created_at=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
                updated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={
                    "elapsed_time": time.time() - start_time,
                    "exception_type": type(e).__name__,
                }
            )
    
    async def run_task_async(self, request: TaskRequest) -> TaskResponse:
        """Run a task asynchronously.
        
        Args:
            request: Task request containing prompt and configuration.
            
        Returns:
            TaskResponse with task details and result.
        """
        # Run the synchronous task in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run_task, request)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics.
        
        Returns:
            Dictionary containing usage statistics.
        """
        return self._usage_tracker.get_stats()
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self._usage_tracker.reset()
        logger.info("Usage statistics reset")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the client.
        
        Returns:
            Dictionary containing health status information.
        """
        try:
            # Try to initialize agent
            _ = self.agent
            
            return {
                "status": "healthy",
                "org_id": self.config.org_id,
                "api_base_url": self.config.api_base_url,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "usage_stats": self.get_usage_stats(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

