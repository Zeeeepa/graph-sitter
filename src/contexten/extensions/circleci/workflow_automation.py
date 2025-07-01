"""
CircleCI Workflow Automation

Comprehensive workflow automation system that:
- Orchestrates failure detection and resolution
- Manages task lifecycle and progress tracking
- Coordinates with external services (GitHub, Codegen)
- Provides real-time status updates
- Handles retry logic and error recovery
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from .config import CircleCIIntegrationConfig
from .types import (
    CircleCIEvent, FailureAnalysis, GeneratedFix, FixGenerationStats,
    BuildStatus, FixConfidence
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskProgress:
    """Task progress information"""
    current_step: str
    total_steps: int
    completed_steps: int
    percentage: float
    estimated_remaining: Optional[timedelta] = None
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowTask:
    """Workflow task definition"""
    id: str
    type: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    
    # Task data
    event: CircleCIEvent
    failure_analysis: Optional[FailureAnalysis] = None
    generated_fix: Optional[GeneratedFix] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    # Progress tracking
    progress: Optional[TaskProgress] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get task duration"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return end_time - self.started_at
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if task is active"""
        return self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]


@dataclass
class WorkflowStats:
    """Workflow automation statistics"""
    tasks_created: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_cancelled: int = 0
    tasks_timeout: int = 0
    progress_updates_sent: int = 0
    status_syncs_performed: int = 0
    last_task_created: Optional[datetime] = None
    last_progress_update: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate"""
        total_finished = self.tasks_completed + self.tasks_failed + self.tasks_cancelled + self.tasks_timeout
        if total_finished == 0:
            return 0.0
        return (self.tasks_completed / total_finished) * 100


class WorkflowAutomation:
    """
    Comprehensive workflow automation system for CircleCI integration
    """
    
    def __init__(self, config: CircleCIIntegrationConfig):
        self.config = config
        self.stats = WorkflowStats()
        
        # Task management
        self.tasks: Dict[str, WorkflowTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Event handlers
        self.task_handlers: Dict[str, Callable[[WorkflowTask], Awaitable[Any]]] = {}
        self.progress_callbacks: List[Callable[[WorkflowTask], Awaitable[None]]] = []
        
        # Workflow state
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.worker_tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the workflow automation system"""
        if self.is_running:
            logger.warning("Workflow automation is already running")
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # Start worker tasks
        max_workers = self.config.workflow.max_concurrent_tasks
        for i in range(max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        # Start progress update task
        if self.config.workflow.send_progress_notifications:
            progress_task = asyncio.create_task(self._progress_update_loop())
            self.worker_tasks.append(progress_task)
        
        logger.info(f"Workflow automation started with {max_workers} workers")
    
    async def stop(self):
        """Stop the workflow automation system"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Cancel all active tasks
        for task_id, task in self.active_tasks.items():
            task.cancel()
            logger.info(f"Cancelled active task: {task_id}")
        
        # Wait for workers to finish
        for worker in self.worker_tasks:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
        
        self.worker_tasks.clear()
        self.active_tasks.clear()
        
        logger.info("Workflow automation stopped")
    
    def register_task_handler(self, task_type: str, handler: Callable[[WorkflowTask], Awaitable[Any]]):
        """Register a task handler"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def add_progress_callback(self, callback: Callable[[WorkflowTask], Awaitable[None]]):
        """Add progress update callback"""
        self.progress_callbacks.append(callback)
        logger.info("Added progress callback")
    
    async def create_failure_analysis_task(self, event: CircleCIEvent) -> WorkflowTask:
        """Create a failure analysis task"""
        task = WorkflowTask(
            id=str(uuid.uuid4()),
            type="failure_analysis",
            title=f"Analyze failure: {event.project_slug}",
            description=f"Analyze build failure for {event.project_slug} (commit: {event.commit_sha[:8] if event.commit_sha else 'unknown'})",
            priority=self._determine_priority(event),
            status=TaskStatus.PENDING,
            event=event,
            timeout_at=datetime.now() + timedelta(seconds=self.config.workflow.task_timeout)
        )
        
        self.tasks[task.id] = task
        
        # Queue for processing
        if self.config.workflow.auto_start_tasks:
            await self.start_task(task.id)
        
        # Update stats
        self.stats.tasks_created += 1
        self.stats.last_task_created = datetime.now()
        
        logger.info(f"Created failure analysis task: {task.id}")
        return task
    
    async def create_fix_generation_task(
        self, 
        failure_analysis: FailureAnalysis,
        parent_task_id: Optional[str] = None
    ) -> WorkflowTask:
        """Create a fix generation task"""
        
        # Create synthetic event from analysis
        event = CircleCIEvent(
            id=failure_analysis.build_id,
            type="workflow-completed",  # type: ignore
            timestamp=failure_analysis.analysis_timestamp,
            project_slug=failure_analysis.project_slug,
            organization=failure_analysis.project_slug.split('/')[0],
            status=BuildStatus.FAILED
        )
        
        task = WorkflowTask(
            id=str(uuid.uuid4()),
            type="fix_generation",
            title=f"Generate fix: {failure_analysis.failure_type.value}",
            description=f"Generate fix for {failure_analysis.failure_type.value} in {failure_analysis.project_slug}",
            priority=self._determine_fix_priority(failure_analysis),
            status=TaskStatus.PENDING,
            event=event,
            failure_analysis=failure_analysis,
            timeout_at=datetime.now() + timedelta(seconds=self.config.workflow.task_timeout),
            metadata={"parent_task_id": parent_task_id} if parent_task_id else {}
        )
        
        self.tasks[task.id] = task
        
        # Queue for processing
        if self.config.workflow.auto_start_tasks:
            await self.start_task(task.id)
        
        # Update stats
        self.stats.tasks_created += 1
        self.stats.last_task_created = datetime.now()
        
        logger.info(f"Created fix generation task: {task.id}")
        return task
    
    async def create_fix_application_task(
        self, 
        generated_fix: GeneratedFix,
        parent_task_id: Optional[str] = None
    ) -> WorkflowTask:
        """Create a fix application task"""
        
        # Create synthetic event from fix
        event = CircleCIEvent(
            id=generated_fix.failure_analysis_id,
            type="workflow-completed",  # type: ignore
            timestamp=generated_fix.timestamp,
            project_slug=generated_fix.failure_analysis_id.split('-')[0],  # Extract from ID
            organization="unknown",
            status=BuildStatus.FAILED
        )
        
        task = WorkflowTask(
            id=str(uuid.uuid4()),
            type="fix_application",
            title=f"Apply fix: {generated_fix.title}",
            description=f"Apply generated fix: {generated_fix.description}",
            priority=self._determine_application_priority(generated_fix),
            status=TaskStatus.PENDING,
            event=event,
            generated_fix=generated_fix,
            timeout_at=datetime.now() + timedelta(seconds=self.config.workflow.task_timeout),
            metadata={"parent_task_id": parent_task_id} if parent_task_id else {}
        )
        
        self.tasks[task.id] = task
        
        # Queue for processing
        if self.config.workflow.auto_start_tasks:
            await self.start_task(task.id)
        
        # Update stats
        self.stats.tasks_created += 1
        self.stats.last_task_created = datetime.now()
        
        logger.info(f"Created fix application task: {task.id}")
        return task
    
    async def start_task(self, task_id: str) -> bool:
        """Start a specific task"""
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not pending (status: {task.status})")
            return False
        
        try:
            # Queue the task
            await self.task_queue.put(task)
            logger.info(f"Queued task for execution: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start task {task_id}: {e}")
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        # Cancel if running
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
        
        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        # Update stats
        self.stats.tasks_cancelled += 1
        
        # Notify callbacks
        await self._notify_progress_callbacks(task)
        
        logger.info(f"Cancelled task: {task_id}")
        return True
    
    async def _worker_loop(self, worker_name: str):
        """Main worker loop"""
        logger.info(f"Started worker: {worker_name}")
        
        while self.is_running:
            try:
                # Wait for task or shutdown
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the task
                await self._process_task(task, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker stopped: {worker_name}")
    
    async def _process_task(self, task: WorkflowTask, worker_name: str):
        """Process a single task"""
        task_id = task.id
        
        try:
            # Check if task is still valid
            if task.status != TaskStatus.PENDING:
                logger.warning(f"Task {task_id} is no longer pending")
                return
            
            # Check timeout
            if task.timeout_at and datetime.now() > task.timeout_at:
                task.status = TaskStatus.TIMEOUT
                task.completed_at = datetime.now()
                task.error = "Task timed out before execution"
                self.stats.tasks_timeout += 1
                await self._notify_progress_callbacks(task)
                logger.warning(f"Task {task_id} timed out before execution")
                return
            
            # Start task
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"Worker {worker_name} starting task {task_id} ({task.type})")
            
            # Get handler
            handler = self.task_handlers.get(task.type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.type}")
            
            # Create async task for execution
            execution_task = asyncio.create_task(handler(task))
            self.active_tasks[task_id] = execution_task
            
            # Execute with timeout
            timeout_seconds = (task.timeout_at - datetime.now()).total_seconds() if task.timeout_at else None
            
            try:
                result = await asyncio.wait_for(execution_task, timeout=timeout_seconds)
                
                # Task completed successfully
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                
                self.stats.tasks_completed += 1
                
                logger.info(f"Task {task_id} completed successfully")
                
            except asyncio.TimeoutError:
                # Task timed out
                execution_task.cancel()
                task.status = TaskStatus.TIMEOUT
                task.completed_at = datetime.now()
                task.error = "Task execution timed out"
                
                self.stats.tasks_timeout += 1
                
                logger.warning(f"Task {task_id} timed out during execution")
                
            except asyncio.CancelledError:
                # Task was cancelled
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                task.error = "Task was cancelled"
                
                self.stats.tasks_cancelled += 1
                
                logger.info(f"Task {task_id} was cancelled")
                
            except Exception as e:
                # Task failed
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = str(e)
                
                self.stats.tasks_failed += 1
                
                logger.error(f"Task {task_id} failed: {e}")
            
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Notify callbacks
            await self._notify_progress_callbacks(task)
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            
            # Mark task as failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = f"Processing error: {e}"
            
            self.stats.tasks_failed += 1
            
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Notify callbacks
            await self._notify_progress_callbacks(task)
    
    async def _progress_update_loop(self):
        """Progress update loop"""
        logger.info("Started progress update loop")
        
        while self.is_running:
            try:
                # Send progress updates for active tasks
                for task in self.tasks.values():
                    if task.is_active and task.progress:
                        await self._notify_progress_callbacks(task)
                        self.stats.progress_updates_sent += 1
                
                self.stats.last_progress_update = datetime.now()
                
                # Wait for next update interval
                await asyncio.sleep(self.config.workflow.progress_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in progress update loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Progress update loop stopped")
    
    async def _notify_progress_callbacks(self, task: WorkflowTask):
        """Notify progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                await callback(task)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def _determine_priority(self, event: CircleCIEvent) -> TaskPriority:
        """Determine task priority based on event"""
        # High priority for main branch failures
        if event.branch in ["main", "master", "production"]:
            return TaskPriority.HIGH
        
        # Normal priority for develop/staging
        if event.branch in ["develop", "staging"]:
            return TaskPriority.NORMAL
        
        # Low priority for feature branches
        return TaskPriority.LOW
    
    def _determine_fix_priority(self, analysis: FailureAnalysis) -> TaskPriority:
        """Determine fix generation priority"""
        # High priority for high-confidence analyses
        if analysis.confidence >= 0.8:
            return TaskPriority.HIGH
        
        # Critical priority for infrastructure failures
        if analysis.failure_type in ["infrastructure_error", "configuration_error"]:
            return TaskPriority.CRITICAL
        
        return TaskPriority.NORMAL
    
    def _determine_application_priority(self, fix: GeneratedFix) -> TaskPriority:
        """Determine fix application priority"""
        # High priority for high-confidence fixes
        if fix.overall_confidence in [FixConfidence.HIGH]:
            return TaskPriority.HIGH
        
        # Normal priority for medium confidence
        if fix.overall_confidence in [FixConfidence.MEDIUM]:
            return TaskPriority.NORMAL
        
        return TaskPriority.LOW
    
    # Public API methods
    def get_task(self, task_id: str) -> Optional[WorkflowTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_active_tasks(self) -> List[WorkflowTask]:
        """Get all active tasks"""
        return [task for task in self.tasks.values() if task.is_active]
    
    def get_completed_tasks(self, limit: int = 10) -> List[WorkflowTask]:
        """Get recent completed tasks"""
        completed = [task for task in self.tasks.values() if task.is_completed]
        completed.sort(key=lambda t: t.completed_at or datetime.min, reverse=True)
        return completed[:limit]
    
    def get_workflow_stats(self) -> WorkflowStats:
        """Get workflow statistics"""
        return self.stats
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information"""
        return {
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "total_tasks": len(self.tasks),
            "is_running": self.is_running
        }
    
    async def update_task_progress(
        self, 
        task_id: str, 
        current_step: str, 
        completed_steps: int, 
        total_steps: int
    ):
        """Update task progress"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        task.progress = TaskProgress(
            current_step=current_step,
            total_steps=total_steps,
            completed_steps=completed_steps,
            percentage=percentage
        )
        
        # Notify callbacks if configured
        if self.config.workflow.send_progress_notifications:
            await self._notify_progress_callbacks(task)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "healthy": self.is_running,
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "workers_running": len(self.worker_tasks),
            "stats": self.stats.__dict__
        }

