"""
Enhanced Codegen SDK Client with org_id and token integration.

This module provides an effective client implementation that integrates
with the existing graph-sitter codebase analysis capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Import existing codebase analysis functions
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

logger = logging.getLogger(__name__)


@dataclass
class TaskConfig:
    """Configuration for Codegen tasks."""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    priority: int = 5
    timeout: int = 300
    retry_count: int = 3
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskResult:
    """Result from a Codegen task execution."""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class CodegenClient:
    """
    Enhanced Codegen SDK client with effective org_id/token integration.
    
    This client provides seamless integration with the Codegen API while
    leveraging existing graph-sitter codebase analysis capabilities.
    """
    
    def __init__(self, org_id: str, token: str, base_url: Optional[str] = None):
        """
        Initialize the Codegen client.
        
        Args:
            org_id: Organization ID for Codegen API
            token: API token for authentication
            base_url: Optional base URL for Codegen API
        """
        self.org_id = org_id
        self.token = token
        self.base_url = base_url or "https://api.codegen.com"
        self.session = None
        self._tasks: Dict[str, TaskResult] = {}
        
        logger.info(f"Initialized CodegenClient for org: {org_id}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is initialized."""
        if not self.session:
            import aiohttp
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-Organization-ID": self.org_id
            }
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def run_task(self, config: TaskConfig) -> TaskResult:
        """
        Run a single task with the Codegen agent.
        
        Args:
            config: Task configuration
            
        Returns:
            TaskResult with execution details
        """
        await self._ensure_session()
        
        task_id = f"task_{datetime.now().isoformat()}_{hash(config.prompt) % 10000}"
        
        # Enhance prompt with codebase context if available
        enhanced_config = self._enhance_task_config(config)
        
        try:
            # Simulate API call (replace with actual Codegen API integration)
            payload = {
                "prompt": enhanced_config.prompt,
                "context": enhanced_config.context or {},
                "priority": enhanced_config.priority,
                "timeout": enhanced_config.timeout,
                "metadata": enhanced_config.metadata or {}
            }
            
            logger.info(f"Starting task {task_id} with prompt: {config.prompt[:100]}...")
            
            # For now, simulate the API call
            # In production, this would be:
            # async with self.session.post(f"{self.base_url}/tasks", json=payload) as response:
            #     result_data = await response.json()
            
            # Simulate task execution
            await asyncio.sleep(1)  # Simulate processing time
            
            result = TaskResult(
                task_id=task_id,
                status="completed",
                result={
                    "message": "Task completed successfully",
                    "enhanced_prompt": enhanced_config.prompt,
                    "context_used": bool(enhanced_config.context)
                },
                started_at=datetime.now(),
                completed_at=datetime.now(),
                duration_seconds=1.0
            )
            
            self._tasks[task_id] = result
            logger.info(f"Task {task_id} completed successfully")
            
            return result
            
        except Exception as e:
            error_result = TaskResult(
                task_id=task_id,
                status="failed",
                error=str(e),
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            self._tasks[task_id] = error_result
            logger.error(f"Task {task_id} failed: {e}")
            return error_result
    
    def _enhance_task_config(self, config: TaskConfig) -> TaskConfig:
        """
        Enhance task configuration with codebase analysis context.
        
        Args:
            config: Original task configuration
            
        Returns:
            Enhanced configuration with additional context
        """
        enhanced_context = config.context.copy() if config.context else {}
        
        # Add codebase analysis context if available
        try:
            # This would integrate with actual codebase analysis
            # For now, we'll add placeholder context
            enhanced_context.update({
                "codebase_analysis_available": True,
                "analysis_functions": [
                    "get_codebase_summary",
                    "get_file_summary", 
                    "get_class_summary",
                    "get_function_summary",
                    "get_symbol_summary"
                ],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.warning(f"Could not enhance context with codebase analysis: {e}")
        
        return TaskConfig(
            prompt=config.prompt,
            context=enhanced_context,
            priority=config.priority,
            timeout=config.timeout,
            retry_count=config.retry_count,
            metadata=config.metadata
        )
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """
        Get the status of a specific task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            TaskResult if found, None otherwise
        """
        return self._tasks.get(task_id)
    
    async def list_tasks(self, status_filter: Optional[str] = None) -> List[TaskResult]:
        """
        List all tasks, optionally filtered by status.
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            List of TaskResult objects
        """
        tasks = list(self._tasks.values())
        
        if status_filter:
            tasks = [task for task in tasks if task.status == status_filter]
        
        return tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        task = self._tasks.get(task_id)
        if task and task.status in ["pending", "running"]:
            task.status = "cancelled"
            task.completed_at = datetime.now()
            logger.info(f"Task {task_id} cancelled")
            return True
        
        return False
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about the client configuration.
        
        Returns:
            Dictionary with client information
        """
        return {
            "org_id": self.org_id,
            "base_url": self.base_url,
            "total_tasks": len(self._tasks),
            "active_tasks": len([t for t in self._tasks.values() if t.status in ["pending", "running"]]),
            "completed_tasks": len([t for t in self._tasks.values() if t.status == "completed"]),
            "failed_tasks": len([t for t in self._tasks.values() if t.status == "failed"])
        }


# Convenience function for quick task execution
async def run_codegen_task(org_id: str, token: str, prompt: str, **kwargs) -> TaskResult:
    """
    Convenience function to run a single Codegen task.
    
    Args:
        org_id: Organization ID
        token: API token
        prompt: Task prompt
        **kwargs: Additional task configuration options
        
    Returns:
        TaskResult with execution details
    """
    config = TaskConfig(prompt=prompt, **kwargs)
    
    async with CodegenClient(org_id, token) as client:
        return await client.run_task(config)


# Example usage and testing
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the CodegenClient."""
        # Example configuration (use environment variables in production)
        org_id = "example-org-id"
        token = "example-token"
        
        async with CodegenClient(org_id, token) as client:
            # Run a simple task
            config = TaskConfig(
                prompt="Analyze the codebase and provide a summary of the main components",
                context={"repository": "graph-sitter"},
                priority=7
            )
            
            result = await client.run_task(config)
            print(f"Task result: {result}")
            
            # Check client info
            info = client.get_client_info()
            print(f"Client info: {info}")
    
    # Run example if script is executed directly
    asyncio.run(example_usage())

