"""Integration with existing CodegenApp in contexten."""

import logging
from typing import Any, Dict, Optional

from .interfaces import OrchestratorInterface, SimpleInterface
from .config import AutogenConfig

logger = logging.getLogger(__name__)


class CodegenAppIntegration:
    """Integration layer for existing CodegenApp."""
    
    def __init__(self, config: Optional[AutogenConfig] = None):
        """Initialize the integration.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config
        self.orchestrator = OrchestratorInterface(config)
        self.simple = SimpleInterface(config)
        
        logger.info("CodegenAppIntegration initialized")
    
    async def handle_agent_request(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an agent request from the existing CodegenApp.
        
        Args:
            prompt: The prompt for the Codegen agent.
            context: Optional context information.
            
        Returns:
            Dictionary containing the response.
        """
        try:
            # Extract codebase path from context if available
            codebase_path = None
            if context and "codebase" in context:
                codebase_path = context["codebase"].get("path")
            
            # Submit task
            response = await self.orchestrator.submit_task(
                prompt=prompt,
                codebase_path=codebase_path,
                context=context,
            )
            
            return {
                "success": True,
                "task_id": response.task_id,
                "status": response.status.value,
                "result": response.result,
                "error": response.error,
                "metadata": response.metadata,
            }
        
        except Exception as e:
            logger.error(f"Failed to handle agent request: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            Dictionary containing task status.
        """
        try:
            response = await self.orchestrator.get_task_status(task_id)
            
            if response:
                return {
                    "success": True,
                    "task_id": response.task_id,
                    "status": response.status.value,
                    "result": response.result,
                    "error": response.error,
                    "created_at": response.created_at,
                    "updated_at": response.updated_at,
                    "metadata": response.metadata,
                }
            else:
                return {
                    "success": False,
                    "error": "Task not found",
                }
        
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a task.
        
        Args:
            task_id: Task identifier.
            
        Returns:
            Dictionary containing cancellation result.
        """
        try:
            cancelled = await self.orchestrator.cancel_task(task_id)
            
            return {
                "success": True,
                "cancelled": cancelled,
            }
        
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def handle_sync_request(self, prompt: str, codebase_path: Optional[str] = None) -> Dict[str, Any]:
        """Handle a synchronous request (for compatibility with existing sync code).
        
        Args:
            prompt: The prompt for the Codegen agent.
            codebase_path: Optional path to codebase.
            
        Returns:
            Dictionary containing the response.
        """
        try:
            response = self.simple.run_task(prompt, codebase_path)
            
            return {
                "success": True,
                "task_id": response.task_id,
                "status": response.status.value,
                "result": response.result,
                "error": response.error,
                "metadata": response.metadata,
            }
        
        except Exception as e:
            logger.error(f"Failed to handle sync request: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the integration.
        
        Returns:
            Dictionary containing health information.
        """
        try:
            health = await self.orchestrator.health_check()
            usage_stats = await self.orchestrator.get_usage_stats()
            
            return {
                "success": True,
                "health": health,
                "usage_stats": usage_stats,
            }
        
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def shutdown(self) -> None:
        """Shutdown the integration."""
        await self.orchestrator.shutdown()
        logger.info("CodegenAppIntegration shutdown complete")


def create_autogenlib_integration(config: Optional[AutogenConfig] = None) -> CodegenAppIntegration:
    """Factory function to create an autogenlib integration.
    
    Args:
        config: Optional configuration object.
        
    Returns:
        CodegenAppIntegration instance.
    """
    return CodegenAppIntegration(config)

