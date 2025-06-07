"""
Enhanced Workflow Service
Provides advanced workflow management, monitoring, and orchestration capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowTask:
    """Individual task within a workflow."""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowExecution:
    """Workflow execution instance."""
    id: str
    project_id: str
    project_name: str
    workflow_type: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tasks: List[WorkflowTask] = field(default_factory=list)
    progress: float = 0.0
    total_steps: int = 0
    completed_steps: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_progress(self) -> float:
        """Calculate workflow progress based on completed tasks."""
        if not self.tasks:
            return 0.0
        
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        self.completed_steps = completed
        self.total_steps = len(self.tasks)
        self.progress = (completed / len(self.tasks)) * 100
        return self.progress

class WorkflowService:
    """Enhanced workflow service with monitoring and orchestration."""
    
    def __init__(self):
        self.executions: Dict[str, WorkflowExecution] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.workflow_templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize workflow templates for different project types."""
        return {
            "full_development": [
                {
                    "name": "Code Analysis",
                    "description": "Analyze codebase structure and dependencies",
                    "estimated_duration": 60,
                    "dependencies": []
                },
                {
                    "name": "Generate Plan",
                    "description": "Create detailed implementation plan",
                    "estimated_duration": 120,
                    "dependencies": ["Code Analysis"]
                },
                {
                    "name": "Create Linear Issues",
                    "description": "Generate Linear issues from plan",
                    "estimated_duration": 30,
                    "dependencies": ["Generate Plan"]
                },
                {
                    "name": "Execute Tasks",
                    "description": "Execute planned development tasks",
                    "estimated_duration": 1800,
                    "dependencies": ["Create Linear Issues"]
                },
                {
                    "name": "Quality Gates",
                    "description": "Run tests, linting, and security checks",
                    "estimated_duration": 300,
                    "dependencies": ["Execute Tasks"]
                },
                {
                    "name": "Create PR",
                    "description": "Create pull request with changes",
                    "estimated_duration": 60,
                    "dependencies": ["Quality Gates"]
                }
            ],
            "bug_fix": [
                {
                    "name": "Issue Analysis",
                    "description": "Analyze bug report and reproduce issue",
                    "estimated_duration": 180,
                    "dependencies": []
                },
                {
                    "name": "Generate Fix",
                    "description": "Implement bug fix",
                    "estimated_duration": 600,
                    "dependencies": ["Issue Analysis"]
                },
                {
                    "name": "Test Fix",
                    "description": "Test the implemented fix",
                    "estimated_duration": 300,
                    "dependencies": ["Generate Fix"]
                },
                {
                    "name": "Create PR",
                    "description": "Create pull request with fix",
                    "estimated_duration": 60,
                    "dependencies": ["Test Fix"]
                }
            ],
            "feature_enhancement": [
                {
                    "name": "Requirements Analysis",
                    "description": "Analyze feature requirements",
                    "estimated_duration": 120,
                    "dependencies": []
                },
                {
                    "name": "Design Implementation",
                    "description": "Design feature implementation",
                    "estimated_duration": 240,
                    "dependencies": ["Requirements Analysis"]
                },
                {
                    "name": "Implement Feature",
                    "description": "Implement the new feature",
                    "estimated_duration": 1200,
                    "dependencies": ["Design Implementation"]
                },
                {
                    "name": "Add Tests",
                    "description": "Add comprehensive tests",
                    "estimated_duration": 600,
                    "dependencies": ["Implement Feature"]
                },
                {
                    "name": "Documentation",
                    "description": "Update documentation",
                    "estimated_duration": 180,
                    "dependencies": ["Add Tests"]
                },
                {
                    "name": "Create PR",
                    "description": "Create pull request",
                    "estimated_duration": 60,
                    "dependencies": ["Documentation"]
                }
            ]
        }
    
    async def create_workflow(
        self,
        project_id: str,
        project_name: str,
        workflow_type: str = "full_development",
        custom_tasks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Create a new workflow execution."""
        execution_id = str(uuid.uuid4())
        
        # Use custom tasks or template
        task_templates = custom_tasks or self.workflow_templates.get(workflow_type, [])
        
        # Create workflow tasks
        tasks = []
        for i, template in enumerate(task_templates):
            task = WorkflowTask(
                id=f"task-{i+1}",
                name=template["name"],
                description=template["description"],
                dependencies=template.get("dependencies", []),
                metadata={
                    "estimated_duration": template.get("estimated_duration", 300),
                    "order": i
                }
            )
            tasks.append(task)
        
        # Create workflow execution
        execution = WorkflowExecution(
            id=execution_id,
            project_id=project_id,
            project_name=project_name,
            workflow_type=workflow_type,
            tasks=tasks,
            metadata={
                "created_at": datetime.now().isoformat(),
                "template_used": workflow_type
            }
        )
        
        self.executions[execution_id] = execution
        logger.info(f"Created workflow {execution_id} for project {project_name}")
        
        return execution_id
    
    async def start_workflow(self, execution_id: str) -> bool:
        """Start workflow execution."""
        if execution_id not in self.executions:
            logger.error(f"Workflow {execution_id} not found")
            return False
        
        execution = self.executions[execution_id]
        if execution.status != WorkflowStatus.PENDING:
            logger.warning(f"Workflow {execution_id} is not in pending state")
            return False
        
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.now()
        
        # Start workflow execution task
        task = asyncio.create_task(self._execute_workflow(execution))
        self.active_tasks[execution_id] = task
        
        logger.info(f"Started workflow {execution_id}")
        return True
    
    async def _execute_workflow(self, execution: WorkflowExecution):
        """Execute workflow tasks in dependency order."""
        try:
            # Build dependency graph
            task_map = {task.name: task for task in execution.tasks}
            completed_tasks = set()
            
            while len(completed_tasks) < len(execution.tasks):
                # Find tasks ready to execute
                ready_tasks = []
                for task in execution.tasks:
                    if (task.status == TaskStatus.PENDING and 
                        all(dep in completed_tasks for dep in task.dependencies)):
                        ready_tasks.append(task)
                
                if not ready_tasks:
                    # Check if we're stuck
                    pending_tasks = [t for t in execution.tasks if t.status == TaskStatus.PENDING]
                    if pending_tasks:
                        logger.error(f"Workflow {execution.id} stuck - circular dependencies or missing tasks")
                        execution.status = WorkflowStatus.FAILED
                        return
                    break
                
                # Execute ready tasks (could be parallel in future)
                for task in ready_tasks:
                    await self._execute_task(task, execution)
                    if task.status == TaskStatus.COMPLETED:
                        completed_tasks.add(task.name)
                    elif task.status == TaskStatus.FAILED:
                        logger.error(f"Task {task.name} failed, stopping workflow")
                        execution.status = WorkflowStatus.FAILED
                        return
                
                # Update progress
                execution.calculate_progress()
                
                # Small delay between task batches
                await asyncio.sleep(1)
            
            # Workflow completed successfully
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.calculate_progress()
            
            logger.info(f"Workflow {execution.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow {execution.id} failed with error: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
        
        finally:
            # Clean up active task
            if execution.id in self.active_tasks:
                del self.active_tasks[execution.id]
    
    async def _execute_task(self, task: WorkflowTask, execution: WorkflowExecution):
        """Execute a single workflow task."""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        try:
            # Simulate task execution based on type
            await self._simulate_task_execution(task, execution)
            
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.duration = (task.end_time - task.start_time).total_seconds()
            
            logger.info(f"Task {task.name} completed in {task.duration:.1f}s")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            task.duration = (task.end_time - task.start_time).total_seconds()
            
            logger.error(f"Task {task.name} failed: {e}")
    
    async def _simulate_task_execution(self, task: WorkflowTask, execution: WorkflowExecution):
        """Simulate task execution with realistic timing and logging."""
        estimated_duration = task.metadata.get("estimated_duration", 300)
        
        # Simulate work with progress updates
        steps = 5
        step_duration = min(estimated_duration / steps, 30)  # Max 30s per step
        
        for i in range(steps):
            await asyncio.sleep(step_duration)
            
            # Add progress log
            progress = ((i + 1) / steps) * 100
            log_message = f"Step {i+1}/{steps} completed ({progress:.0f}%)"
            task.logs.append(f"{datetime.now().isoformat()}: {log_message}")
            
            # Simulate occasional failures (5% chance)
            if i == steps - 1 and task.name != "Create PR":  # Don't fail final steps
                import random
                if random.random() < 0.05:
                    raise Exception(f"Simulated failure in {task.name}")
        
        # Add completion log
        task.logs.append(f"{datetime.now().isoformat()}: Task completed successfully")
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """Pause workflow execution."""
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.PAUSED
            
            # Cancel active task if exists
            if execution_id in self.active_tasks:
                self.active_tasks[execution_id].cancel()
                del self.active_tasks[execution_id]
            
            logger.info(f"Paused workflow {execution_id}")
            return True
        
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """Resume paused workflow."""
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        if execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            
            # Restart workflow execution
            task = asyncio.create_task(self._execute_workflow(execution))
            self.active_tasks[execution_id] = task
            
            logger.info(f"Resumed workflow {execution_id}")
            return True
        
        return False
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel workflow execution."""
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        execution.status = WorkflowStatus.CANCELLED
        execution.end_time = datetime.now()
        
        # Cancel active task if exists
        if execution_id in self.active_tasks:
            self.active_tasks[execution_id].cancel()
            del self.active_tasks[execution_id]
        
        logger.info(f"Cancelled workflow {execution_id}")
        return True
    
    def get_workflow(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        return self.executions.get(execution_id)
    
    def get_workflows_for_project(self, project_id: str) -> List[WorkflowExecution]:
        """Get all workflows for a project."""
        return [
            execution for execution in self.executions.values()
            if execution.project_id == project_id
        ]
    
    def get_active_workflows(self) -> List[WorkflowExecution]:
        """Get all active (running/paused) workflows."""
        return [
            execution for execution in self.executions.values()
            if execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]
        ]
    
    def get_recent_workflows(self, limit: int = 10) -> List[WorkflowExecution]:
        """Get recent workflows ordered by start time."""
        workflows = list(self.executions.values())
        workflows.sort(key=lambda w: w.start_time or datetime.min, reverse=True)
        return workflows[:limit]
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics."""
        total = len(self.executions)
        if total == 0:
            return {
                "total_workflows": 0,
                "success_rate": 0,
                "average_duration": 0,
                "active_workflows": 0
            }
        
        completed = sum(1 for w in self.executions.values() if w.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for w in self.executions.values() if w.status == WorkflowStatus.FAILED)
        active = sum(1 for w in self.executions.values() if w.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED])
        
        # Calculate average duration for completed workflows
        completed_workflows = [w for w in self.executions.values() if w.status == WorkflowStatus.COMPLETED and w.end_time and w.start_time]
        avg_duration = 0
        if completed_workflows:
            total_duration = sum((w.end_time - w.start_time).total_seconds() for w in completed_workflows)
            avg_duration = total_duration / len(completed_workflows)
        
        return {
            "total_workflows": total,
            "completed_workflows": completed,
            "failed_workflows": failed,
            "active_workflows": active,
            "success_rate": (completed / total) * 100 if total > 0 else 0,
            "average_duration": avg_duration,
            "workflow_types": list(self.workflow_templates.keys())
        }

# Global workflow service instance
workflow_service = WorkflowService()

