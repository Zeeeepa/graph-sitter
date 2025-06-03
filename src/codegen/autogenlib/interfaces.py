"""Interfaces for contexten orchestrator integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .client import AutogenClient
from .config import AutogenConfig, get_config
from .context import ContextEnhancer
from .models import TaskRequest, TaskResponse, TaskStatus
from .async_processor import AsyncTaskProcessor

logger = logging.getLogger(__name__)


class OrchestratorInterface:
    """Main interface for contexten orchestrator to interact with autogenlib."""
    
    def __init__(self, config: Optional[AutogenConfig] = None):
        """Initialize the orchestrator interface.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config or get_config()
        self.client = AutogenClient(self.config)
        self.context_enhancer = ContextEnhancer(self.config)
        self.async_processor = AsyncTaskProcessor(self.config, self.client, self.context_enhancer)
        
        logger.info("OrchestratorInterface initialized")
    
    async def submit_task(self, prompt: str, **kwargs) -> TaskResponse:
        """Submit a task for execution.
        
        Args:
            prompt: Task prompt for the Codegen agent.
            **kwargs: Additional task parameters.
            
        Returns:
            TaskResponse with task details.
        """
        # Create task request
        request = TaskRequest(
            prompt=prompt,
            context=kwargs.get('context'),
            codebase_path=kwargs.get('codebase_path'),
            enhance_context=kwargs.get('enhance_context', True),
            timeout=kwargs.get('timeout'),
            priority=kwargs.get('priority', 1),
        )
        
        # Enhance prompt with context if enabled
        if request.enhance_context and request.codebase_path:
            try:
                enhanced_prompt = self.context_enhancer.enhance_prompt(request)
                request.prompt = enhanced_prompt
                logger.info("Prompt enhanced with codebase context")
            except Exception as e:
                logger.warning(f"Failed to enhance prompt: {e}")
        
        # Submit to async processor if enabled, otherwise run synchronously
        if self.config.enable_async_processing:
            return await self.async_processor.submit_task(request)
        else:
            return await self.client.run_task_async(request)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResponse]:
        """Get the status of a task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            TaskResponse if task exists, None otherwise.
        """
        if self.config.enable_async_processing:
            return await self.async_processor.get_task_status(task_id)
        else:
            # For synchronous processing, tasks are completed immediately
            logger.warning(f"Task status requested for {task_id}, but async processing is disabled")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            True if task was cancelled, False otherwise.
        """
        if self.config.enable_async_processing:
            return await self.async_processor.cancel_task(task_id)
        else:
            logger.warning(f"Task cancellation requested for {task_id}, but async processing is disabled")
            return False
    
    async def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskResponse]:
        """List tasks, optionally filtered by status.
        
        Args:
            status: Optional status filter.
            
        Returns:
            List of TaskResponse objects.
        """
        if self.config.enable_async_processing:
            return await self.async_processor.list_tasks(status)
        else:
            return []
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics.
        
        Returns:
            Dictionary containing usage statistics.
        """
        stats = self.client.get_usage_stats()
        
        if self.config.enable_async_processing:
            async_stats = await self.async_processor.get_stats()
            stats.update(async_stats)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check.
        
        Returns:
            Dictionary containing health status.
        """
        health = self.client.health_check()
        
        if self.config.enable_async_processing:
            async_health = await self.async_processor.health_check()
            health["async_processor"] = async_health
        
        return health
    
    async def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.client.reset_usage_stats()
        
        if self.config.enable_async_processing:
            await self.async_processor.reset_stats()
    
    def clear_context_cache(self) -> None:
        """Clear the context enhancement cache."""
        self.context_enhancer.clear_cache()
        logger.info("Context cache cleared")
    
    async def shutdown(self) -> None:
        """Shutdown the interface and cleanup resources."""
        if self.config.enable_async_processing:
            await self.async_processor.shutdown()
        
        logger.info("OrchestratorInterface shutdown complete")


class SimpleInterface:
    """Simplified interface for basic usage without async processing."""
    
    def __init__(self, config: Optional[AutogenConfig] = None):
        """Initialize the simple interface.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config or get_config()
        self.client = AutogenClient(self.config)
        self.context_enhancer = ContextEnhancer(self.config)
    
    def run_task(self, prompt: str, codebase_path: Optional[str] = None, **kwargs) -> TaskResponse:
        """Run a task synchronously.
        
        Args:
            prompt: Task prompt for the Codegen agent.
            codebase_path: Optional path to codebase for context enhancement.
            **kwargs: Additional task parameters.
            
        Returns:
            TaskResponse with task result.
        """
        # Create task request
        request = TaskRequest(
            prompt=prompt,
            codebase_path=codebase_path,
            enhance_context=kwargs.get('enhance_context', True),
            timeout=kwargs.get('timeout'),
            priority=kwargs.get('priority', 1),
        )
        
        # Enhance prompt with context if enabled
        if request.enhance_context and request.codebase_path:
            try:
                enhanced_prompt = self.context_enhancer.enhance_prompt(request)
                request.prompt = enhanced_prompt
            except Exception as e:
                logger.warning(f"Failed to enhance prompt: {e}")
        
        return self.client.run_task(request)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self.client.get_usage_stats()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check."""
        return self.client.health_check()

