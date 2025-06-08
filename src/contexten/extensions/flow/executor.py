"""
Enhanced Flow Executor

Provides advanced execution capabilities with support for:
- Multi-framework execution
- Error handling and recovery
- Resource management
- Execution context management
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
import asyncio
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .strands import StrandAgent, StrandWorkflow

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Context manager for flow execution."""
    
    def __init__(self, flow_id: str, execution_params: Dict[str, Any]):
        self.flow_id = flow_id
        self.execution_params = execution_params
        self.start_time = None
        self.end_time = None
        self.metrics = {}
        self.logs = []
        
    def log(self, level: str, message: str, **kwargs):
        """Add log entry to execution context."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "flow_id": self.flow_id,
            **kwargs
        }
        self.logs.append(log_entry)
        
        # Also log to standard logger
        getattr(logger, level.lower(), logger.info)(
            f"[{self.flow_id}] {message}"
        )
        
    def add_metric(self, key: str, value: Any):
        """Add metric to execution context."""
        self.metrics[key] = value
        
    @property
    def duration(self) -> Optional[timedelta]:
        """Get execution duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class FlowExecutor:
    """
    Enhanced flow executor with advanced capabilities.
    
    Features:
    - Multi-framework execution support
    - Automatic retry and recovery
    - Resource management and throttling
    - Detailed execution tracking
    - Error handling and reporting
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        execution_timeout: Optional[float] = None,
        enable_recovery: bool = True,
        **kwargs
    ):
        """
        Initialize the flow executor.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts (seconds)
            execution_timeout: Maximum execution time (seconds)
            enable_recovery: Whether to enable automatic recovery
            **kwargs: Additional configuration
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.execution_timeout = execution_timeout
        self.enable_recovery = enable_recovery
        
        # Execution tracking
        self.active_executions = {}
        self.execution_history = []
        
        # Recovery strategies
        self.recovery_strategies = {
            "timeout": self._handle_timeout_recovery,
            "agent_failure": self._handle_agent_failure_recovery,
            "resource_exhaustion": self._handle_resource_recovery,
            "network_error": self._handle_network_recovery
        }
        
    async def execute_workflow(
        self,
        workflow: StrandWorkflow,
        workflow_def: Dict[str, Any],
        agents: List[StrandAgent],
        execution_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with enhanced error handling and recovery.
        
        Args:
            workflow: Workflow to execute
            workflow_def: Workflow definition
            agents: Available agents
            execution_params: Optional execution parameters
            
        Returns:
            Dict containing execution results
        """
        flow_id = workflow_def.get("id", f"flow_{datetime.now().isoformat()}")
        context = ExecutionContext(flow_id, execution_params or {})
        
        try:
            context.start_time = datetime.now()
            context.log("info", f"Starting workflow execution: {workflow.name}")
            
            # Register active execution
            self.active_executions[flow_id] = context
            
            # Execute with retry logic
            result = await self._execute_with_retry(
                workflow=workflow,
                workflow_def=workflow_def,
                agents=agents,
                context=context
            )
            
            context.end_time = datetime.now()
            context.log("info", f"Workflow execution completed: {result.get('status')}")
            
            # Add execution metrics
            context.add_metric("execution_time", context.duration.total_seconds())
            context.add_metric("final_status", result.get("status"))
            context.add_metric("agent_count", len(agents))
            
            # Move to history
            self.execution_history.append(context)
            del self.active_executions[flow_id]
            
            return {
                **result,
                "execution_context": {
                    "flow_id": flow_id,
                    "duration": context.duration.total_seconds(),
                    "metrics": context.metrics,
                    "logs": context.logs[-10:]  # Last 10 log entries
                }
            }
            
        except Exception as e:
            context.end_time = datetime.now()
            context.log("error", f"Workflow execution failed: {str(e)}")
            
            # Move to history even on failure
            self.execution_history.append(context)
            if flow_id in self.active_executions:
                del self.active_executions[flow_id]
                
            return {
                "status": "failed",
                "error": str(e),
                "execution_context": {
                    "flow_id": flow_id,
                    "duration": context.duration.total_seconds() if context.duration else 0,
                    "metrics": context.metrics,
                    "logs": context.logs
                }
            }
            
    async def _execute_with_retry(
        self,
        workflow: StrandWorkflow,
        workflow_def: Dict[str, Any],
        agents: List[StrandAgent],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute workflow with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                context.log("info", f"Execution attempt {attempt + 1}/{self.max_retries + 1}")
                
                # Execute with timeout if specified
                if self.execution_timeout:
                    result = await asyncio.wait_for(
                        self._execute_workflow_core(workflow, workflow_def, agents, context),
                        timeout=self.execution_timeout
                    )
                else:
                    result = await self._execute_workflow_core(workflow, workflow_def, agents, context)
                    
                # Success - return result
                context.add_metric("successful_attempt", attempt + 1)
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                context.log("warning", f"Execution timeout on attempt {attempt + 1}")
                
                if self.enable_recovery and attempt < self.max_retries:
                    await self._apply_recovery_strategy("timeout", context)
                    
            except Exception as e:
                last_error = e
                context.log("warning", f"Execution failed on attempt {attempt + 1}: {str(e)}")
                
                if self.enable_recovery and attempt < self.max_retries:
                    # Determine recovery strategy based on error type
                    strategy = self._determine_recovery_strategy(e)
                    await self._apply_recovery_strategy(strategy, context)
                    
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                context.log("info", f"Waiting {delay}s before retry")
                await asyncio.sleep(delay)
                
        # All retries exhausted
        context.add_metric("failed_after_retries", self.max_retries + 1)
        raise last_error
        
    async def _execute_workflow_core(
        self,
        workflow: StrandWorkflow,
        workflow_def: Dict[str, Any],
        agents: List[StrandAgent],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Core workflow execution logic."""
        # Update workflow with available agents
        workflow.agents = agents
        
        # Execute workflow stages
        stages = workflow_def.get("stages", [])
        stage_results = []
        
        for i, stage in enumerate(stages):
            context.log("info", f"Executing stage {i + 1}/{len(stages)}: {stage.get('name', 'unnamed')}")
            
            stage_result = await self._execute_stage(
                stage=stage,
                agents=agents,
                context=context
            )
            
            stage_results.append(stage_result)
            
            # Check for stage failure
            if stage_result.get("status") == "failed":
                if not workflow_def.get("continue_on_failure", False):
                    context.log("error", f"Stage {i + 1} failed, stopping execution")
                    break
                else:
                    context.log("warning", f"Stage {i + 1} failed, continuing due to continue_on_failure")
                    
        # Determine overall status
        overall_status = "completed"
        if any(r.get("status") == "failed" for r in stage_results):
            overall_status = "failed" if not workflow_def.get("continue_on_failure", False) else "completed_with_errors"
            
        return {
            "status": overall_status,
            "stage_results": stage_results,
            "stages_executed": len(stage_results),
            "total_stages": len(stages)
        }
        
    async def _execute_stage(
        self,
        stage: Dict[str, Any],
        agents: List[StrandAgent],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a single workflow stage."""
        stage_name = stage.get("name", "unnamed")
        tasks = stage.get("tasks", [])
        
        context.log("debug", f"Stage '{stage_name}' has {len(tasks)} tasks")
        
        task_results = []
        
        # Execute tasks (could be parallel or sequential based on stage config)
        execution_mode = stage.get("execution_mode", "sequential")
        
        if execution_mode == "parallel":
            # Execute tasks in parallel
            task_coroutines = [
                self._execute_task(task, agents, context)
                for task in tasks
            ]
            task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            # Convert exceptions to error results
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    task_results[i] = {
                        "status": "failed",
                        "error": str(result),
                        "task_index": i
                    }
        else:
            # Execute tasks sequentially
            for i, task in enumerate(tasks):
                task_result = await self._execute_task(task, agents, context)
                task_results.append(task_result)
                
                # Stop on task failure if not configured to continue
                if task_result.get("status") == "failed" and not stage.get("continue_on_task_failure", False):
                    context.log("warning", f"Task {i + 1} failed, stopping stage execution")
                    break
                    
        # Determine stage status
        stage_status = "completed"
        if any(r.get("status") == "failed" for r in task_results):
            stage_status = "failed"
            
        return {
            "status": stage_status,
            "stage_name": stage_name,
            "task_results": task_results,
            "tasks_executed": len(task_results),
            "total_tasks": len(tasks)
        }
        
    async def _execute_task(
        self,
        task: Dict[str, Any],
        agents: List[StrandAgent],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a single task."""
        task_name = task.get("name", "unnamed")
        
        # Select appropriate agent
        agent = self._select_agent_for_task(task, agents)
        if not agent:
            return {
                "status": "failed",
                "error": "No suitable agent found",
                "task_name": task_name
            }
            
        context.log("debug", f"Executing task '{task_name}' with agent {type(agent).__name__}")
        
        try:
            # Execute task
            result = await agent.execute(task)
            
            context.log("debug", f"Task '{task_name}' completed with status: {result.get('status')}")
            
            return {
                "status": result.get("status", "completed"),
                "task_name": task_name,
                "agent_type": type(agent).__name__,
                "result": result
            }
            
        except Exception as e:
            context.log("error", f"Task '{task_name}' failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "task_name": task_name,
                "agent_type": type(agent).__name__
            }
            
    def _select_agent_for_task(
        self,
        task: Dict[str, Any],
        agents: List[StrandAgent]
    ) -> Optional[StrandAgent]:
        """Select the most suitable agent for a task."""
        required_tools = task.get("required_tools", [])
        preferred_agent_type = task.get("preferred_agent_type")
        
        # Filter agents by required tools
        suitable_agents = []
        for agent in agents:
            agent_tools = {tool.name for tool in agent.tools}
            if all(tool in agent_tools for tool in required_tools):
                suitable_agents.append(agent)
                
        if not suitable_agents:
            return None
            
        # Prefer specific agent type if specified
        if preferred_agent_type:
            for agent in suitable_agents:
                if type(agent).__name__ == preferred_agent_type:
                    return agent
                    
        # Return first suitable agent
        return suitable_agents[0]
        
    def _determine_recovery_strategy(self, error: Exception) -> str:
        """Determine appropriate recovery strategy based on error type."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return "timeout"
        elif "agent" in error_str or "tool" in error_str:
            return "agent_failure"
        elif "memory" in error_str or "resource" in error_str:
            return "resource_exhaustion"
        elif "network" in error_str or "connection" in error_str:
            return "network_error"
        else:
            return "timeout"  # Default strategy
            
    async def _apply_recovery_strategy(self, strategy: str, context: ExecutionContext):
        """Apply recovery strategy."""
        if strategy in self.recovery_strategies:
            context.log("info", f"Applying recovery strategy: {strategy}")
            await self.recovery_strategies[strategy](context)
        else:
            context.log("warning", f"Unknown recovery strategy: {strategy}")
            
    async def _handle_timeout_recovery(self, context: ExecutionContext):
        """Handle timeout recovery."""
        # Increase timeout for next attempt
        if hasattr(self, 'execution_timeout') and self.execution_timeout:
            self.execution_timeout *= 1.5
            context.log("info", f"Increased timeout to {self.execution_timeout}s")
            
    async def _handle_agent_failure_recovery(self, context: ExecutionContext):
        """Handle agent failure recovery."""
        # Could implement agent rotation or tool reinitialization
        context.log("info", "Applying agent failure recovery")
        await asyncio.sleep(0.5)  # Brief pause
        
    async def _handle_resource_recovery(self, context: ExecutionContext):
        """Handle resource exhaustion recovery."""
        # Force garbage collection and wait
        import gc
        gc.collect()
        context.log("info", "Applied resource recovery (garbage collection)")
        await asyncio.sleep(2.0)
        
    async def _handle_network_recovery(self, context: ExecutionContext):
        """Handle network error recovery."""
        # Wait longer for network issues
        context.log("info", "Applying network error recovery")
        await asyncio.sleep(5.0)
        
    def get_execution_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status for a flow."""
        if flow_id in self.active_executions:
            context = self.active_executions[flow_id]
            return {
                "flow_id": flow_id,
                "status": "executing",
                "start_time": context.start_time.isoformat(),
                "duration": (datetime.now() - context.start_time).total_seconds(),
                "metrics": context.metrics,
                "recent_logs": context.logs[-5:]  # Last 5 log entries
            }
        return None
        
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history."""
        return [
            {
                "flow_id": ctx.flow_id,
                "start_time": ctx.start_time.isoformat() if ctx.start_time else None,
                "end_time": ctx.end_time.isoformat() if ctx.end_time else None,
                "duration": ctx.duration.total_seconds() if ctx.duration else None,
                "metrics": ctx.metrics
            }
            for ctx in self.execution_history[-limit:]
        ]

