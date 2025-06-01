"""
Pipeline Engine for Graph-Sitter CI/CD

Provides comprehensive pipeline execution with:
- Multi-step pipeline definitions
- Conditional execution and branching
- Integration with task management
- Artifact management
- Performance monitoring
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

from .task_management import Task, TaskManager, TaskStatus

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Pipeline step types"""
    COMMAND = "command"
    CODEGEN_TASK = "codegen_task"
    WEBHOOK = "webhook"
    CONDITION = "condition"
    PARALLEL = "parallel"
    SCRIPT = "script"


@dataclass
class PipelineStep:
    """Individual pipeline step definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    step_order: int = 0
    step_type: StepType = StepType.COMMAND
    configuration: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 3600
    retry_count: int = 0
    is_critical: bool = True
    condition: Optional[str] = None  # Condition for conditional execution
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if step should execute based on condition"""
        if not self.condition:
            return True
        
        try:
            # Simple condition evaluation (can be extended)
            return eval(self.condition, {"__builtins__": {}}, context)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{self.condition}': {e}")
            return True


@dataclass
class StepExecution:
    """Pipeline step execution tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_execution_id: str = ""
    pipeline_step_id: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Results
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    artifacts: Dict[str, Any] = field(default_factory=dict)
    
    def start_execution(self) -> None:
        """Mark step execution as started"""
        self.status = PipelineStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(self, exit_code: int = 0, stdout: str = "", stderr: str = "", artifacts: Dict[str, Any] = None) -> None:
        """Mark step execution as completed"""
        self.status = PipelineStatus.SUCCESS if exit_code == 0 else PipelineStatus.FAILURE
        self.completed_at = datetime.now(timezone.utc)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        if artifacts:
            self.artifacts.update(artifacts)


@dataclass
class Pipeline:
    """Pipeline definition with steps and configuration"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    name: str = ""
    description: str = ""
    pipeline_type: str = "build"  # build, test, deploy, analysis, security
    trigger_events: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    steps: List[PipelineStep] = field(default_factory=list)
    is_active: bool = True
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline"""
        if not step.step_order:
            step.step_order = len(self.steps) + 1
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.step_order)
    
    def get_step(self, step_id: str) -> Optional[PipelineStep]:
        """Get a step by ID"""
        return next((s for s in self.steps if s.id == step_id), None)
    
    def remove_step(self, step_id: str) -> bool:
        """Remove a step from the pipeline"""
        step = self.get_step(step_id)
        if step:
            self.steps.remove(step)
            return True
        return False


@dataclass
class PipelineExecution:
    """Pipeline execution tracking and results"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str = ""
    task_id: Optional[str] = None
    trigger_event: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    status: PipelineStatus = PipelineStatus.PENDING
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Results
    logs: str = ""
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    step_executions: List[StepExecution] = field(default_factory=list)
    
    # Context for step execution
    context: Dict[str, Any] = field(default_factory=dict)
    
    def start_execution(self) -> None:
        """Mark pipeline execution as started"""
        self.status = PipelineStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(self, success: bool = True) -> None:
        """Mark pipeline execution as completed"""
        self.status = PipelineStatus.SUCCESS if success else PipelineStatus.FAILURE
        self.completed_at = datetime.now(timezone.utc)
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
    
    def add_step_execution(self, step_execution: StepExecution) -> None:
        """Add a step execution to the pipeline execution"""
        step_execution.pipeline_execution_id = self.id
        self.step_executions.append(step_execution)


class PipelineEngine:
    """
    Comprehensive pipeline execution engine with support for:
    - Multi-step pipeline execution
    - Conditional and parallel execution
    - Integration with task management
    - Artifact management and metrics collection
    """
    
    def __init__(self, organization_id: str, task_manager: Optional[TaskManager] = None, database_connection=None):
        self.organization_id = organization_id
        self.task_manager = task_manager
        self.db = database_connection
        self.pipelines: Dict[str, Pipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.step_executors: Dict[StepType, Callable] = {
            StepType.COMMAND: self._execute_command_step,
            StepType.CODEGEN_TASK: self._execute_codegen_task_step,
            StepType.WEBHOOK: self._execute_webhook_step,
            StepType.CONDITION: self._execute_condition_step,
            StepType.SCRIPT: self._execute_script_step,
        }
    
    async def create_pipeline(self, pipeline: Pipeline) -> str:
        """Create a new pipeline"""
        self.pipelines[pipeline.id] = pipeline
        
        # Store in database if available
        if self.db:
            await self._store_pipeline_in_db(pipeline)
        
        logger.info(f"Created pipeline {pipeline.id}: {pipeline.name}")
        return pipeline.id
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID"""
        return self.pipelines.get(pipeline_id)
    
    async def list_pipelines(self, project_id: Optional[str] = None, pipeline_type: Optional[str] = None) -> List[Pipeline]:
        """List pipelines with optional filters"""
        pipelines = list(self.pipelines.values())
        
        if project_id:
            pipelines = [p for p in pipelines if p.project_id == project_id]
        if pipeline_type:
            pipelines = [p for p in pipelines if p.pipeline_type == pipeline_type]
        
        return pipelines
    
    async def execute_pipeline(self, pipeline_id: str, trigger_event: Optional[str] = None, trigger_data: Dict[str, Any] = None, context: Dict[str, Any] = None) -> PipelineExecution:
        """Execute a pipeline with optional trigger and context"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        if not pipeline.is_active:
            raise ValueError(f"Pipeline {pipeline_id} is not active")
        
        # Create execution record
        execution = PipelineExecution(
            pipeline_id=pipeline_id,
            trigger_event=trigger_event,
            trigger_data=trigger_data or {},
            context=context or {}
        )
        self.executions[execution.id] = execution
        
        # Start execution
        execution.start_execution()
        logger.info(f"Starting pipeline execution {execution.id} for pipeline {pipeline_id}")
        
        try:
            # Execute pipeline steps
            success = await self._execute_pipeline_steps(pipeline, execution)
            execution.complete_execution(success)
            
            logger.info(f"Pipeline execution {execution.id} completed with status: {execution.status}")
            
        except Exception as e:
            execution.status = PipelineStatus.FAILURE
            execution.completed_at = datetime.now(timezone.utc)
            execution.logs += f"\nPipeline execution failed: {str(e)}"
            logger.error(f"Pipeline execution {execution.id} failed: {e}")
            
        finally:
            # Store execution in database
            if self.db:
                await self._store_execution_in_db(execution)
        
        return execution
    
    async def _execute_pipeline_steps(self, pipeline: Pipeline, execution: PipelineExecution) -> bool:
        """Execute all steps in a pipeline"""
        success = True
        
        for step in pipeline.steps:
            # Check if step should execute based on condition
            if not step.should_execute(execution.context):
                logger.info(f"Skipping step {step.name} due to condition")
                continue
            
            # Execute step with retries
            step_success = await self._execute_step_with_retries(step, execution)
            
            if not step_success and step.is_critical:
                success = False
                break
            elif not step_success:
                logger.warning(f"Non-critical step {step.name} failed, continuing pipeline")
        
        return success
    
    async def _execute_step_with_retries(self, step: PipelineStep, execution: PipelineExecution) -> bool:
        """Execute a step with retry logic"""
        for attempt in range(step.retry_count + 1):
            step_execution = StepExecution(
                pipeline_step_id=step.id
            )
            execution.add_step_execution(step_execution)
            
            try:
                step_execution.start_execution()
                logger.info(f"Executing step {step.name} (attempt {attempt + 1})")
                
                # Get step executor
                executor = self.step_executors.get(step.step_type)
                if not executor:
                    raise ValueError(f"No executor found for step type {step.step_type}")
                
                # Execute step with timeout
                result = await asyncio.wait_for(
                    executor(step, execution),
                    timeout=step.timeout_seconds
                )
                
                # Process result
                if isinstance(result, dict):
                    step_execution.complete_execution(
                        exit_code=result.get("exit_code", 0),
                        stdout=result.get("stdout", ""),
                        stderr=result.get("stderr", ""),
                        artifacts=result.get("artifacts", {})
                    )
                else:
                    step_execution.complete_execution()
                
                # Update execution context with step results
                execution.context[f"step_{step.name}_result"] = result
                
                if step_execution.status == PipelineStatus.SUCCESS:
                    return True
                
            except asyncio.TimeoutError:
                step_execution.complete_execution(exit_code=124, stderr="Step execution timed out")
                logger.error(f"Step {step.name} timed out after {step.timeout_seconds} seconds")
                
            except Exception as e:
                step_execution.complete_execution(exit_code=1, stderr=str(e))
                logger.error(f"Step {step.name} failed: {e}")
            
            # If this was the last attempt, return failure
            if attempt == step.retry_count:
                return False
            
            # Wait before retry
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    async def _execute_command_step(self, step: PipelineStep, execution: PipelineExecution) -> Dict[str, Any]:
        """Execute a command step"""
        command = step.configuration.get("command", "")
        if not command:
            raise ValueError("Command step requires 'command' in configuration")
        
        # Simulate command execution (in real implementation, use subprocess)
        await asyncio.sleep(0.1)
        
        return {
            "exit_code": 0,
            "stdout": f"Command '{command}' executed successfully",
            "stderr": "",
            "artifacts": {}
        }
    
    async def _execute_codegen_task_step(self, step: PipelineStep, execution: PipelineExecution) -> Dict[str, Any]:
        """Execute a Codegen SDK task step"""
        if not self.task_manager:
            raise ValueError("Task manager required for Codegen task steps")
        
        task_config = step.configuration.get("task", {})
        
        # Create and execute task
        task = Task(
            title=task_config.get("title", f"Pipeline step: {step.name}"),
            description=task_config.get("description", ""),
            organization_id=self.organization_id
        )
        
        task_id = await self.task_manager.create_task(task)
        task_execution = await self.task_manager.execute_task(task_id)
        
        return {
            "exit_code": 0 if task_execution.status == TaskStatus.COMPLETED else 1,
            "stdout": json.dumps(task_execution.result),
            "stderr": task_execution.error_message or "",
            "artifacts": {"task_execution_id": task_execution.id}
        }
    
    async def _execute_webhook_step(self, step: PipelineStep, execution: PipelineExecution) -> Dict[str, Any]:
        """Execute a webhook step"""
        url = step.configuration.get("url", "")
        method = step.configuration.get("method", "POST")
        payload = step.configuration.get("payload", {})
        
        if not url:
            raise ValueError("Webhook step requires 'url' in configuration")
        
        # Simulate webhook call (in real implementation, use aiohttp)
        await asyncio.sleep(0.1)
        
        return {
            "exit_code": 0,
            "stdout": f"Webhook {method} to {url} completed",
            "stderr": "",
            "artifacts": {"webhook_response": {"status": 200}}
        }
    
    async def _execute_condition_step(self, step: PipelineStep, execution: PipelineExecution) -> Dict[str, Any]:
        """Execute a condition step"""
        condition = step.configuration.get("condition", "")
        if not condition:
            raise ValueError("Condition step requires 'condition' in configuration")
        
        try:
            result = eval(condition, {"__builtins__": {}}, execution.context)
            execution.context[f"condition_{step.name}"] = result
            
            return {
                "exit_code": 0 if result else 1,
                "stdout": f"Condition '{condition}' evaluated to {result}",
                "stderr": "",
                "artifacts": {"condition_result": result}
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Failed to evaluate condition: {e}",
                "artifacts": {}
            }
    
    async def _execute_script_step(self, step: PipelineStep, execution: PipelineExecution) -> Dict[str, Any]:
        """Execute a script step"""
        script = step.configuration.get("script", "")
        language = step.configuration.get("language", "bash")
        
        if not script:
            raise ValueError("Script step requires 'script' in configuration")
        
        # Simulate script execution
        await asyncio.sleep(0.1)
        
        return {
            "exit_code": 0,
            "stdout": f"Script executed successfully ({language})",
            "stderr": "",
            "artifacts": {}
        }
    
    async def get_execution_metrics(self, execution_id: str) -> Dict[str, Any]:
        """Get metrics for a pipeline execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return {}
        
        total_steps = len(execution.step_executions)
        successful_steps = len([s for s in execution.step_executions if s.status == PipelineStatus.SUCCESS])
        failed_steps = len([s for s in execution.step_executions if s.status == PipelineStatus.FAILURE])
        
        return {
            "execution_id": execution_id,
            "pipeline_id": execution.pipeline_id,
            "status": execution.status.value,
            "duration_seconds": execution.duration_seconds,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    
    async def _store_pipeline_in_db(self, pipeline: Pipeline) -> None:
        """Store pipeline in database"""
        # Implementation would depend on database connection
        pass
    
    async def _store_execution_in_db(self, execution: PipelineExecution) -> None:
        """Store pipeline execution in database"""
        # Implementation would depend on database connection
        pass


# Utility functions for pipeline management
def create_pipeline_from_dict(data: Dict[str, Any]) -> Pipeline:
    """Create a Pipeline object from dictionary data"""
    pipeline = Pipeline()
    for key, value in data.items():
        if key == "steps" and isinstance(value, list):
            pipeline.steps = [create_step_from_dict(step_data) for step_data in value]
        elif hasattr(pipeline, key):
            setattr(pipeline, key, value)
    return pipeline


def create_step_from_dict(data: Dict[str, Any]) -> PipelineStep:
    """Create a PipelineStep object from dictionary data"""
    step = PipelineStep()
    for key, value in data.items():
        if key == "step_type" and isinstance(value, str):
            step.step_type = StepType(value)
        elif hasattr(step, key):
            setattr(step, key, value)
    return step

