"""
Contexten Unified Client Interface

This module provides a unified client interface for interacting with
the Contexten CI/CD system, abstracting the complexity of the underlying
orchestrator and providing a simple API for external consumers.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

from .core import ContextenOrchestrator, SystemConfig, SystemStatus
from ..codegen.autogenlib import TaskConfig, WorkflowDefinition, BatchConfig

logger = logging.getLogger(__name__)


class ClientMode(Enum):
    """Client operation modes."""
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"


@dataclass
class ClientConfig:
    """Configuration for the Contexten client."""
    # System configuration
    system_config: SystemConfig
    
    # Client settings
    mode: ClientMode = ClientMode.ASYNC
    timeout_seconds: int = 300
    retry_attempts: int = 3
    auto_start_orchestrator: bool = True
    
    # Response formatting
    include_metadata: bool = True
    include_metrics: bool = False
    response_format: str = "json"  # json, yaml, xml


@dataclass
class AnalysisRequest:
    """Request for codebase analysis."""
    repository_url: str
    analysis_type: str = "comprehensive"
    branch: Optional[str] = None
    include_dependencies: bool = True
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowRequest:
    """Request for workflow execution."""
    workflow_definition: WorkflowDefinition
    priority: int = 5
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BatchRequest:
    """Request for batch processing."""
    tasks: List[Dict[str, Any]]
    batch_config: Optional[BatchConfig] = None
    callback_url: Optional[str] = None


class ContextenClient:
    """
    Unified client interface for the Contexten CI/CD system.
    
    This client provides a simple, high-level API for interacting with
    the Contexten orchestrator, handling common operations like:
    - Codebase analysis
    - Workflow execution
    - Batch processing
    - System monitoring
    - Integration management
    """
    
    def __init__(self, config: ClientConfig):
        """
        Initialize the Contexten client.
        
        Args:
            config: Client configuration
        """
        self.config = config
        self.orchestrator: Optional[ContextenOrchestrator] = None
        self._is_started = False
        
        logger.info(f"ContextenClient initialized in {config.mode.value} mode")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the client and orchestrator."""
        if self._is_started:
            return
        
        logger.info("Starting Contexten client...")
        
        if self.config.auto_start_orchestrator:
            self.orchestrator = ContextenOrchestrator(self.config.system_config)
            await self.orchestrator.start()
        
        self._is_started = True
        logger.info("Contexten client started")
    
    async def stop(self):
        """Stop the client and orchestrator."""
        if not self._is_started:
            return
        
        logger.info("Stopping Contexten client...")
        
        if self.orchestrator:
            await self.orchestrator.stop()
        
        self._is_started = False
        logger.info("Contexten client stopped")
    
    async def analyze_codebase(self, request: AnalysisRequest) -> Dict[str, Any]:
        """
        Analyze a codebase.
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Analysis results
        """
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not started")
        
        logger.info(f"Analyzing codebase: {request.repository_url}")
        
        try:
            result = await self.orchestrator.execute_codebase_analysis(
                repository_url=request.repository_url,
                analysis_type=request.analysis_type
            )
            
            if self.config.include_metadata:
                result["request"] = asdict(request)
                result["client_metadata"] = {
                    "client_mode": self.config.mode.value,
                    "processed_at": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Codebase analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "repository_url": request.repository_url,
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_workflow(self, request: WorkflowRequest) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            request: Workflow execution request
            
        Returns:
            Workflow execution results
        """
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not started")
        
        logger.info(f"Executing workflow: {request.workflow_definition.name}")
        
        try:
            task_ids = await self.orchestrator.create_workflow(request.workflow_definition)
            
            result = {
                "status": "started",
                "workflow_id": request.workflow_definition.id,
                "task_ids": task_ids,
                "started_at": datetime.now().isoformat()
            }
            
            if self.config.include_metadata:
                result["request"] = asdict(request)
                result["client_metadata"] = {
                    "client_mode": self.config.mode.value,
                    "processed_at": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "workflow_id": request.workflow_definition.id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_batch(self, request: BatchRequest) -> Dict[str, Any]:
        """
        Process a batch of tasks.
        
        Args:
            request: Batch processing request
            
        Returns:
            Batch processing results
        """
        if not self.orchestrator or not self.orchestrator.batch_processor:
            raise RuntimeError("Batch processor not available")
        
        logger.info(f"Processing batch with {len(request.tasks)} tasks")
        
        try:
            # Convert task dictionaries to (task_id, TaskConfig) tuples
            tasks = []
            for i, task_dict in enumerate(request.tasks):
                task_id = task_dict.get("id", f"batch_task_{i}")
                task_config = TaskConfig(
                    prompt=task_dict["prompt"],
                    context=task_dict.get("context", {}),
                    priority=task_dict.get("priority", 5),
                    timeout=task_dict.get("timeout", 300),
                    metadata=task_dict.get("metadata", {})
                )
                tasks.append((task_id, task_config))
            
            # Execute batch
            batch_result = await self.orchestrator.batch_processor.process_batch(
                tasks=tasks,
                config=request.batch_config
            )
            
            result = {
                "status": batch_result.status.value,
                "batch_id": batch_result.batch_id,
                "total_tasks": batch_result.total_tasks,
                "completed_tasks": batch_result.completed_tasks,
                "failed_tasks": batch_result.failed_tasks,
                "duration_seconds": batch_result.duration_seconds,
                "started_at": batch_result.started_at.isoformat(),
                "completed_at": batch_result.completed_at.isoformat() if batch_result.completed_at else None
            }
            
            if self.config.include_metadata:
                result["request"] = asdict(request)
                result["task_results"] = {
                    task_id: asdict(task_result) 
                    for task_id, task_result in batch_result.task_results.items()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and health information.
        
        Returns:
            System status information
        """
        if not self.orchestrator:
            return {
                "status": "not_started",
                "orchestrator_available": False,
                "timestamp": datetime.now().isoformat()
            }
        
        status = self.orchestrator.get_system_status()
        
        if self.config.include_metrics:
            # Add additional metrics if requested
            if self.orchestrator.batch_processor:
                status["batch_metrics"] = self.orchestrator.batch_processor.get_performance_metrics()
            
            if self.orchestrator.task_manager:
                status["task_metrics"] = self.orchestrator.task_manager.get_status_summary()
        
        return status
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List active workflows.
        
        Returns:
            List of workflow information
        """
        if not self.orchestrator:
            return []
        
        workflows = []
        for workflow_id, workflow_info in self.orchestrator.active_workflows.items():
            workflow_data = {
                "id": workflow_id,
                "name": workflow_info["definition"].name,
                "description": workflow_info["definition"].description,
                "status": workflow_info["status"],
                "task_count": len(workflow_info["task_ids"]),
                "created_at": workflow_info["created_at"].isoformat()
            }
            
            if "completed_at" in workflow_info:
                workflow_data["completed_at"] = workflow_info["completed_at"].isoformat()
            
            workflows.append(workflow_data)
        
        return workflows
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        if not self.orchestrator:
            return None
        
        workflow_info = self.orchestrator.active_workflows.get(workflow_id)
        if not workflow_info:
            return None
        
        # Get task statuses
        task_statuses = {}
        if self.orchestrator.task_manager:
            for task_id in workflow_info["task_ids"]:
                task = self.orchestrator.task_manager.get_task(task_id)
                if task:
                    task_statuses[task_id] = {
                        "status": task.status.value,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None
                    }
        
        return {
            "id": workflow_id,
            "name": workflow_info["definition"].name,
            "description": workflow_info["definition"].description,
            "status": workflow_info["status"],
            "created_at": workflow_info["created_at"].isoformat(),
            "task_statuses": task_statuses,
            "total_tasks": len(workflow_info["task_ids"]),
            "completed_tasks": len([t for t in task_statuses.values() if t["status"] == "completed"])
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            True if cancelled successfully
        """
        if not self.orchestrator or not self.orchestrator.task_manager:
            return False
        
        cancelled_count = self.orchestrator.task_manager.cancel_workflow(workflow_id)
        
        if workflow_id in self.orchestrator.active_workflows:
            self.orchestrator.active_workflows[workflow_id]["status"] = "cancelled"
        
        logger.info(f"Cancelled workflow {workflow_id} ({cancelled_count} tasks)")
        return cancelled_count > 0
    
    def create_analysis_request(self, 
                              repository_url: str,
                              analysis_type: str = "comprehensive",
                              **kwargs) -> AnalysisRequest:
        """
        Create an analysis request.
        
        Args:
            repository_url: URL of repository to analyze
            analysis_type: Type of analysis to perform
            **kwargs: Additional request parameters
            
        Returns:
            AnalysisRequest instance
        """
        return AnalysisRequest(
            repository_url=repository_url,
            analysis_type=analysis_type,
            **kwargs
        )
    
    def create_workflow_request(self,
                              workflow_definition: WorkflowDefinition,
                              **kwargs) -> WorkflowRequest:
        """
        Create a workflow request.
        
        Args:
            workflow_definition: Workflow definition
            **kwargs: Additional request parameters
            
        Returns:
            WorkflowRequest instance
        """
        return WorkflowRequest(
            workflow_definition=workflow_definition,
            **kwargs
        )
    
    def create_batch_request(self,
                           tasks: List[Dict[str, Any]],
                           **kwargs) -> BatchRequest:
        """
        Create a batch request.
        
        Args:
            tasks: List of task definitions
            **kwargs: Additional request parameters
            
        Returns:
            BatchRequest instance
        """
        return BatchRequest(
            tasks=tasks,
            **kwargs
        )


# Convenience functions for common operations
async def analyze_repository(repository_url: str,
                           analysis_type: str = "comprehensive",
                           config: Optional[ClientConfig] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze a single repository.
    
    Args:
        repository_url: URL of repository to analyze
        analysis_type: Type of analysis to perform
        config: Optional client configuration
        
    Returns:
        Analysis results
    """
    if not config:
        # Create default configuration
        system_config = SystemConfig(
            codegen_org_id=os.getenv("CODEGEN_ORG_ID", ""),
            codegen_token=os.getenv("CODEGEN_TOKEN", "")
        )
        config = ClientConfig(system_config=system_config)
    
    async with ContextenClient(config) as client:
        request = client.create_analysis_request(repository_url, analysis_type)
        return await client.analyze_codebase(request)


async def execute_simple_workflow(workflow_definition: WorkflowDefinition,
                                 config: Optional[ClientConfig] = None) -> Dict[str, Any]:
    """
    Convenience function to execute a simple workflow.
    
    Args:
        workflow_definition: Workflow to execute
        config: Optional client configuration
        
    Returns:
        Workflow execution results
    """
    if not config:
        # Create default configuration
        system_config = SystemConfig(
            codegen_org_id=os.getenv("CODEGEN_ORG_ID", ""),
            codegen_token=os.getenv("CODEGEN_TOKEN", "")
        )
        config = ClientConfig(system_config=system_config)
    
    async with ContextenClient(config) as client:
        request = client.create_workflow_request(workflow_definition)
        return await client.execute_workflow(request)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the Contexten client."""
        import os
        
        # Create configuration
        system_config = SystemConfig(
            codegen_org_id=os.getenv("CODEGEN_ORG_ID", "example-org"),
            codegen_token=os.getenv("CODEGEN_TOKEN", "example-token"),
            max_concurrent_tasks=3
        )
        
        client_config = ClientConfig(
            system_config=system_config,
            mode=ClientMode.ASYNC,
            include_metadata=True
        )
        
        # Use client
        async with ContextenClient(client_config) as client:
            # Analyze a repository
            analysis_request = client.create_analysis_request(
                repository_url="https://github.com/example/repo",
                analysis_type="comprehensive"
            )
            
            result = await client.analyze_codebase(analysis_request)
            print(f"Analysis result: {result}")
            
            # Get system status
            status = await client.get_system_status()
            print(f"System status: {status}")
    
    asyncio.run(example_usage())

