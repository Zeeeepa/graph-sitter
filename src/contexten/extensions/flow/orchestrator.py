"""
Unified Flow Orchestrator

Provides a unified interface across all flow frameworks with enhanced capabilities
for flow creation, execution, and monitoring.
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
import logging
from datetime import datetime
from enum import Enum

from .flow_manager import FlowManager
from .strands import StrandAgent, StrandWorkflow

logger = logging.getLogger(__name__)


class FlowStatus(Enum):
    """Flow execution status enumeration."""
    CREATED = "created"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    PAUSED = "paused"


class FlowPriority(Enum):
    """Flow execution priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class FlowOrchestrator:
    """
    Unified orchestrator for managing flows across multiple frameworks.
    
    Provides enhanced capabilities for:
    - Flow lifecycle management
    - Priority-based execution
    - Resource allocation
    - Error handling and recovery
    - Real-time monitoring
    """
    
    def __init__(
        self,
        agents: Optional[List[StrandAgent]] = None,
        max_concurrent_flows: int = 10,
        enable_monitoring: bool = True,
        **kwargs
    ):
        """
        Initialize the flow orchestrator.
        
        Args:
            agents: List of available strand agents
            max_concurrent_flows: Maximum number of concurrent flows
            enable_monitoring: Whether to enable flow monitoring
            **kwargs: Additional configuration
        """
        self.agents = agents or []
        self.max_concurrent_flows = max_concurrent_flows
        self.enable_monitoring = enable_monitoring
        
        # Initialize flow manager
        self.flow_manager = FlowManager(
            agents=self.agents,
            **kwargs
        )
        
        # Execution queues by priority
        self.execution_queues = {
            priority: asyncio.Queue() for priority in FlowPriority
        }
        
        # Resource tracking
        self.resource_usage = {
            "active_flows": 0,
            "total_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0
        }
        
        # Execution semaphore
        self.execution_semaphore = asyncio.Semaphore(max_concurrent_flows)
        
        # Background tasks
        self._executor_task = None
        self._monitor_task = None
        
    async def start(self):
        """Start the orchestrator background tasks."""
        if not self._executor_task:
            self._executor_task = asyncio.create_task(self._flow_executor())
            
        if self.enable_monitoring and not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._flow_monitor())
            
        logger.info("Flow orchestrator started")
        
    async def stop(self):
        """Stop the orchestrator and cleanup resources."""
        if self._executor_task:
            self._executor_task.cancel()
            try:
                await self._executor_task
            except asyncio.CancelledError:
                pass
                
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Flow orchestrator stopped")
        
    async def submit_flow(
        self,
        name: str,
        workflow_def: Dict[str, Any],
        priority: FlowPriority = FlowPriority.NORMAL,
        framework: str = "auto",
        execution_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a flow for execution.
        
        Args:
            name: Flow name
            workflow_def: Workflow definition
            priority: Execution priority
            framework: Framework preference
            execution_params: Optional execution parameters
            
        Returns:
            Dict containing submission result
        """
        try:
            # Create flow
            creation_result = await self.flow_manager.create_flow(
                name=name,
                workflow_def=workflow_def,
                framework=framework
            )
            
            if creation_result["status"] != "success":
                return creation_result
                
            flow_id = creation_result["flow_id"]
            
            # Create execution request
            execution_request = {
                "flow_id": flow_id,
                "execution_params": execution_params or {},
                "priority": priority,
                "submitted_at": datetime.now(),
                "attempts": 0
            }
            
            # Queue for execution
            await self.execution_queues[priority].put(execution_request)
            
            logger.info(f"Flow {flow_id} submitted with priority {priority.name}")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "priority": priority.name,
                "message": f"Flow {name} submitted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to submit flow {name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to submit flow {name}"
            }
            
    async def execute_flow_sync(
        self,
        name: str,
        workflow_def: Dict[str, Any],
        framework: str = "auto",
        execution_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a flow synchronously (wait for completion).
        
        Args:
            name: Flow name
            workflow_def: Workflow definition
            framework: Framework preference
            execution_params: Optional execution parameters
            timeout: Optional execution timeout
            
        Returns:
            Dict containing execution result
        """
        try:
            # Create flow
            creation_result = await self.flow_manager.create_flow(
                name=name,
                workflow_def=workflow_def,
                framework=framework
            )
            
            if creation_result["status"] != "success":
                return creation_result
                
            flow_id = creation_result["flow_id"]
            
            # Execute directly with semaphore
            async with self.execution_semaphore:
                execution_result = await asyncio.wait_for(
                    self.flow_manager.execute_flow(
                        flow_id=flow_id,
                        execution_params=execution_params
                    ),
                    timeout=timeout
                )
                
            # Update resource tracking
            self.resource_usage["total_executions"] += 1
            if execution_result["status"] != "success":
                self.resource_usage["failed_executions"] += 1
                
            return execution_result
            
        except asyncio.TimeoutError:
            logger.error(f"Flow {name} execution timed out")
            return {
                "status": "failed",
                "error": "Execution timeout",
                "message": f"Flow {name} execution timed out"
            }
        except Exception as e:
            logger.error(f"Failed to execute flow {name}: {e}")
            self.resource_usage["failed_executions"] += 1
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to execute flow {name}"
            }
            
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status and metrics."""
        queue_sizes = {
            priority.name: self.execution_queues[priority].qsize()
            for priority in FlowPriority
        }
        
        return {
            "status": "running" if self._executor_task and not self._executor_task.done() else "stopped",
            "resource_usage": self.resource_usage.copy(),
            "queue_sizes": queue_sizes,
            "max_concurrent_flows": self.max_concurrent_flows,
            "available_agents": len(self.agents),
            "monitoring_enabled": self.enable_monitoring
        }
        
    async def _flow_executor(self):
        """Background task for executing queued flows."""
        logger.info("Flow executor started")
        
        while True:
            try:
                # Check queues in priority order
                execution_request = None
                selected_priority = None
                
                for priority in [FlowPriority.CRITICAL, FlowPriority.HIGH, 
                               FlowPriority.NORMAL, FlowPriority.LOW]:
                    try:
                        execution_request = self.execution_queues[priority].get_nowait()
                        selected_priority = priority
                        break
                    except asyncio.QueueEmpty:
                        continue
                        
                if not execution_request:
                    # No requests available, wait a bit
                    await asyncio.sleep(0.1)
                    continue
                    
                # Execute flow with semaphore
                async with self.execution_semaphore:
                    await self._execute_queued_flow(execution_request, selected_priority)
                    
            except asyncio.CancelledError:
                logger.info("Flow executor cancelled")
                break
            except Exception as e:
                logger.error(f"Flow executor error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
                
    async def _execute_queued_flow(
        self,
        execution_request: Dict[str, Any],
        priority: FlowPriority
    ):
        """Execute a queued flow request."""
        flow_id = execution_request["flow_id"]
        execution_params = execution_request["execution_params"]
        
        try:
            self.resource_usage["active_flows"] += 1
            start_time = datetime.now()
            
            # Execute flow
            result = await self.flow_manager.execute_flow(
                flow_id=flow_id,
                execution_params=execution_params
            )
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_metrics(execution_time, result["status"] == "success")
            
            logger.info(f"Flow {flow_id} executed with priority {priority.name}, "
                       f"status: {result['status']}, duration: {execution_time:.2f}s")
                       
        except Exception as e:
            logger.error(f"Failed to execute queued flow {flow_id}: {e}")
            self._update_execution_metrics(0, False)
        finally:
            self.resource_usage["active_flows"] -= 1
            
    async def _flow_monitor(self):
        """Background task for monitoring flow health and metrics."""
        logger.info("Flow monitor started")
        
        while True:
            try:
                # Monitor resource usage
                if self.resource_usage["active_flows"] > self.max_concurrent_flows * 0.8:
                    logger.warning("High flow concurrency detected")
                    
                # Monitor failure rate
                total = self.resource_usage["total_executions"]
                failed = self.resource_usage["failed_executions"]
                if total > 10 and failed / total > 0.2:
                    logger.warning(f"High failure rate: {failed}/{total} ({failed/total*100:.1f}%)")
                    
                # Sleep for monitoring interval
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                logger.info("Flow monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Flow monitor error: {e}")
                await asyncio.sleep(5)
                
    def _update_execution_metrics(self, execution_time: float, success: bool):
        """Update execution metrics."""
        self.resource_usage["total_executions"] += 1
        
        if not success:
            self.resource_usage["failed_executions"] += 1
            
        # Update average execution time
        total = self.resource_usage["total_executions"]
        current_avg = self.resource_usage["average_execution_time"]
        self.resource_usage["average_execution_time"] = (
            (current_avg * (total - 1) + execution_time) / total
        )

