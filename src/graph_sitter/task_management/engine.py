"""
Comprehensive Task Management Engine with Database Integration & OpenEvolve Evaluation

This module implements a sophisticated task management system with expanded database categories,
OpenEvolve integration for step-by-step evaluation, and automated workflow management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

# Core imports for database integration
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

# OpenEvolve integration imports
try:
    from openevolve.evaluator import Evaluator
    from openevolve.database import Database as OpenEvolveDB
    from openevolve.controller import Controller
    OPENEVOLVE_AVAILABLE = True
except ImportError:
    OPENEVOLVE_AVAILABLE = False
    logging.warning("OpenEvolve not available. Some features will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

# Database Models

class Project(Base):
    """Top-level project organization and repository management"""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    repository_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Relationships
    tasks = relationship("Task", back_populates="project")
    analytics = relationship("Analytics", back_populates="project")
    events = relationship("Event", back_populates="project")

class Task(Base):
    """Complete task lifecycle management with flexible metadata"""
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=TaskPriority.MEDIUM.value)
    assigned_to = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    task_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    executions = relationship("TaskExecution", back_populates="task")
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.task_id")

class TaskExecution(Base):
    """Task execution tracking and results"""
    __tablename__ = 'task_executions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50))
    result = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Integer)  # in seconds
    
    # Relationships
    task = relationship("Task", back_populates="executions")

class TaskDependency(Base):
    """Task dependencies management"""
    __tablename__ = 'task_dependencies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'))
    depends_on_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    """Comprehensive codebase analysis and metrics storage"""
    __tablename__ = 'analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    analytics_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Relationships
    project = relationship("Project", back_populates="analytics")

class Prompt(Base):
    """Dynamic prompt generation and template management"""
    __tablename__ = 'prompts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    template = Column(Text, nullable=False)
    variables = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    prompt_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Relationships
    executions = relationship("PromptExecution", back_populates="prompt")

class PromptExecution(Base):
    """Prompt execution tracking and results"""
    __tablename__ = 'prompt_executions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey('prompts.id'))
    input_data = Column(JSON)
    output_data = Column(JSON)
    executed_at = Column(DateTime, default=datetime.utcnow)
    execution_time = Column(Integer)  # in milliseconds
    
    # Relationships
    prompt = relationship("Prompt", back_populates="executions")

class Event(Base):
    """Linear, Slack, GitHub, deployment, and system events"""
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    event_type = Column(String(100), nullable=False)  # linear, slack, github, deployment, system
    source = Column(String(255))
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="events")

@dataclass
class TaskManagerConfig:
    """Configuration for the Task Management Engine"""
    database_url: str = "postgresql://localhost/task_management"
    openevolve_enabled: bool = True
    max_concurrent_tasks: int = 10
    evaluation_interval: int = 300  # seconds
    auto_merge_threshold: float = 0.8  # success rate threshold for auto-merge

class TaskManagementEngine:
    """
    Comprehensive Task Management Engine with Database Integration & OpenEvolve Evaluation
    
    This engine provides:
    1. Complete task lifecycle management with flexible metadata
    2. Comprehensive codebase analysis and metrics storage
    3. Dynamic prompt generation and template management
    4. Event tracking for Linear, Slack, GitHub, deployment, and system events
    5. OpenEvolve integration for step-by-step effectiveness analysis
    6. Automated workflow management and validation
    """
    
    def __init__(self, config: TaskManagerConfig):
        self.config = config
        self.engine = create_engine(config.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize OpenEvolve components if available
        self.openevolve_evaluator = None
        self.openevolve_db = None
        self.openevolve_controller = None
        
        if OPENEVOLVE_AVAILABLE and config.openevolve_enabled:
            self._initialize_openevolve()
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info("Task Management Engine initialized successfully")
    
    def _initialize_openevolve(self):
        """Initialize OpenEvolve components for step-by-step evaluation"""
        try:
            self.openevolve_evaluator = Evaluator()
            self.openevolve_db = OpenEvolveDB()
            self.openevolve_controller = Controller()
            logger.info("OpenEvolve integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenEvolve: {e}")
            self.config.openevolve_enabled = False
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            return db
        finally:
            pass  # Session will be closed by caller
    
    # Project Management
    
    async def create_project(self, name: str, description: str = None, 
                           repository_url: str = None, metadata: Dict = None) -> Project:
        """Create a new project"""
        db = self.get_db()
        try:
            project = Project(
                name=name,
                description=description,
                repository_url=repository_url,
                project_metadata=metadata or {}
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            
            # Log project creation event
            await self.log_event(
                project_id=project.id,
                event_type="system",
                source="task_engine",
                event_data={"action": "project_created", "project_name": name}
            )
            
            logger.info(f"Project created: {name} ({project.id})")
            return project
        finally:
            db.close()
    
    async def get_project(self, project_id: Union[str, uuid.UUID]) -> Optional[Project]:
        """Get project by ID"""
        db = self.get_db()
        try:
            return db.query(Project).filter(Project.id == project_id).first()
        finally:
            db.close()
    
    # Task Management
    
    async def create_task(self, project_id: Union[str, uuid.UUID], title: str, 
                         description: str = None, priority: TaskPriority = TaskPriority.MEDIUM,
                         assigned_to: str = None, due_date: datetime = None,
                         metadata: Dict = None) -> Task:
        """Create a new task"""
        db = self.get_db()
        try:
            task = Task(
                project_id=project_id,
                title=title,
                description=description,
                priority=priority.value,
                assigned_to=assigned_to,
                due_date=due_date,
                task_metadata=metadata or {}
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # Log task creation event
            await self.log_event(
                project_id=project_id,
                event_type="system",
                source="task_engine",
                event_data={"action": "task_created", "task_id": str(task.id), "title": title}
            )
            
            logger.info(f"Task created: {title} ({task.id})")
            return task
        finally:
            db.close()
    
    async def update_task_status(self, task_id: Union[str, uuid.UUID], 
                               status: TaskStatus) -> Optional[Task]:
        """Update task status"""
        db = self.get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                old_status = task.status
                task.status = status.value
                task.updated_at = datetime.utcnow()
                
                if status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
                
                db.commit()
                db.refresh(task)
                
                # Log status change event
                await self.log_event(
                    project_id=task.project_id,
                    event_type="system",
                    source="task_engine",
                    event_data={
                        "action": "task_status_updated",
                        "task_id": str(task.id),
                        "old_status": old_status,
                        "new_status": status.value
                    }
                )
                
                # Trigger OpenEvolve evaluation if enabled
                if self.config.openevolve_enabled and status == TaskStatus.COMPLETED:
                    await self._evaluate_task_completion(task)
                
                logger.info(f"Task {task_id} status updated: {old_status} -> {status.value}")
                return task
            return None
        finally:
            db.close()
    
    async def execute_task(self, task_id: Union[str, uuid.UUID]) -> TaskExecution:
        """Execute a task and track the execution"""
        db = self.get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Create execution record
            execution = TaskExecution(
                task_id=task_id,
                status=TaskStatus.IN_PROGRESS.value
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Update task status
            await self.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            try:
                # Execute the actual task logic here
                # This is where you would integrate with your specific task execution logic
                result = await self._execute_task_logic(task)
                
                # Update execution with success
                execution.completed_at = datetime.utcnow()
                execution.status = TaskStatus.COMPLETED.value
                execution.result = result
                execution.execution_time = int((execution.completed_at - execution.started_at).total_seconds())
                
                # Update task status
                await self.update_task_status(task_id, TaskStatus.COMPLETED)
                
            except Exception as e:
                # Update execution with failure
                execution.completed_at = datetime.utcnow()
                execution.status = TaskStatus.FAILED.value
                execution.error_message = str(e)
                execution.execution_time = int((execution.completed_at - execution.started_at).total_seconds())
                
                # Update task status
                await self.update_task_status(task_id, TaskStatus.FAILED)
                
                logger.error(f"Task execution failed: {e}")
            
            db.commit()
            db.refresh(execution)
            return execution
            
        finally:
            db.close()
    
    async def _execute_task_logic(self, task: Task) -> Dict[str, Any]:
        """
        Execute the actual task logic. This should be overridden or extended
        based on your specific task requirements.
        """
        # Placeholder implementation
        await asyncio.sleep(1)  # Simulate work
        return {
            "status": "completed",
            "message": f"Task '{task.title}' executed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Analytics Management
    
    async def record_metric(self, project_id: Union[str, uuid.UUID], 
                          metric_name: str, metric_value: Any, metadata: Dict = None):
        """Record a metric for analytics"""
        db = self.get_db()
        try:
            analytics = Analytics(
                project_id=project_id,
                metric_name=metric_name,
                metric_value=metric_value,
                analytics_metadata=metadata or {}  # Updated to use analytics_metadata
            )
            db.add(analytics)
            db.commit()
            
            logger.info(f"Metric recorded: {metric_name} = {metric_value}")
        finally:
            db.close()
    
    async def get_metrics(self, project_id: Union[str, uuid.UUID], 
                         metric_name: str = None, 
                         start_date: datetime = None,
                         end_date: datetime = None) -> List[Analytics]:
        """Get metrics for a project"""
        db = self.get_db()
        try:
            query = db.query(Analytics).filter(Analytics.project_id == project_id)
            
            if metric_name:
                query = query.filter(Analytics.metric_name == metric_name)
            
            if start_date:
                query = query.filter(Analytics.timestamp >= start_date)
            
            if end_date:
                query = query.filter(Analytics.timestamp <= end_date)
            
            return query.order_by(Analytics.timestamp.desc()).all()
        finally:
            db.close()
    
    # Prompt Management
    
    async def create_prompt_template(self, name: str, template: str, 
                                   variables: List[str] = None, metadata: Dict = None) -> Prompt:
        """Create a new prompt template"""
        db = self.get_db()
        try:
            prompt = Prompt(
                name=name,
                template=template,
                variables=variables or [],
                prompt_metadata=metadata or {}  # Updated to use prompt_metadata
            )
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
            
            logger.info(f"Prompt template created: {name}")
            return prompt
        finally:
            db.close()
    
    async def execute_prompt(self, prompt_id: Union[str, uuid.UUID], 
                           input_data: Dict) -> PromptExecution:
        """Execute a prompt with given input data"""
        db = self.get_db()
        try:
            prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
            if not prompt:
                raise ValueError(f"Prompt {prompt_id} not found")
            
            start_time = datetime.utcnow()
            
            # Execute prompt logic (placeholder implementation)
            output_data = await self._execute_prompt_logic(prompt, input_data)
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)  # milliseconds
            
            # Record execution
            execution = PromptExecution(
                prompt_id=prompt_id,
                input_data=input_data,
                output_data=output_data,
                execution_time=execution_time
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            logger.info(f"Prompt executed: {prompt.name} in {execution_time}ms")
            return execution
        finally:
            db.close()
    
    async def _execute_prompt_logic(self, prompt: Prompt, input_data: Dict) -> Dict[str, Any]:
        """Execute prompt logic (placeholder implementation)"""
        # This would integrate with your LLM or prompt execution system
        return {
            "generated_text": f"Response for prompt '{prompt.name}' with input: {input_data}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Event Management
    
    async def log_event(self, project_id: Union[str, uuid.UUID], event_type: str, 
                       source: str, event_data: Dict):
        """Log an event"""
        db = self.get_db()
        try:
            event = Event(
                project_id=project_id,
                event_type=event_type,
                source=source,
                event_data=event_data
            )
            db.add(event)
            db.commit()
            
            logger.debug(f"Event logged: {event_type} from {source}")
        finally:
            db.close()
    
    async def get_events(self, project_id: Union[str, uuid.UUID] = None,
                        event_type: str = None, source: str = None,
                        start_date: datetime = None, end_date: datetime = None,
                        limit: int = 100) -> List[Event]:
        """Get events with optional filtering"""
        db = self.get_db()
        try:
            query = db.query(Event)
            
            if project_id:
                query = query.filter(Event.project_id == project_id)
            
            if event_type:
                query = query.filter(Event.event_type == event_type)
            
            if source:
                query = query.filter(Event.source == source)
            
            if start_date:
                query = query.filter(Event.timestamp >= start_date)
            
            if end_date:
                query = query.filter(Event.timestamp <= end_date)
            
            return query.order_by(Event.timestamp.desc()).limit(limit).all()
        finally:
            db.close()
    
    # OpenEvolve Integration
    
    async def _evaluate_task_completion(self, task: Task):
        """Evaluate task completion using OpenEvolve"""
        if not self.config.openevolve_enabled or not self.openevolve_evaluator:
            return
        
        try:
            # Prepare evaluation data
            evaluation_data = {
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "metadata": task.task_metadata,
                "completion_time": task.completed_at.isoformat() if task.completed_at else None
            }
            
            # Run OpenEvolve evaluation
            evaluation_result = await self._run_openevolve_evaluation(evaluation_data)
            
            # Store evaluation results
            await self.record_metric(
                project_id=task.project_id,
                metric_name="openevolve_evaluation",
                metric_value=evaluation_result,
                metadata={"task_id": str(task.id)}
            )
            
            logger.info(f"OpenEvolve evaluation completed for task {task.id}")
            
        except Exception as e:
            logger.error(f"OpenEvolve evaluation failed for task {task.id}: {e}")
    
    async def _run_openevolve_evaluation(self, evaluation_data: Dict) -> Dict[str, Any]:
        """Run OpenEvolve evaluation (placeholder implementation)"""
        # This would integrate with the actual OpenEvolve evaluation logic
        return {
            "effectiveness_score": 0.85,
            "improvement_suggestions": ["Consider adding more detailed documentation"],
            "evaluation_timestamp": datetime.utcnow().isoformat()
        }
    
    # Workflow Management
    
    async def monitor_sub_issues(self, project_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Monitor sub-issue progress"""
        db = self.get_db()
        try:
            tasks = db.query(Task).filter(Task.project_id == project_id).all()
            
            status_counts = {}
            for task in tasks:
                status = task.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            total_tasks = len(tasks)
            completed_tasks = status_counts.get(TaskStatus.COMPLETED.value, 0)
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            monitoring_result = {
                "project_id": str(project_id),
                "total_tasks": total_tasks,
                "status_breakdown": status_counts,
                "completion_rate": completion_rate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Record monitoring metric
            await self.record_metric(
                project_id=project_id,
                metric_name="sub_issue_monitoring",
                metric_value=monitoring_result
            )
            
            return monitoring_result
            
        finally:
            db.close()
    
    async def validate_implementation(self, task_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Validate implementation against requirements"""
        db = self.get_db()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Get task executions
            executions = db.query(TaskExecution).filter(TaskExecution.task_id == task_id).all()
            
            validation_result = {
                "task_id": str(task_id),
                "task_title": task.title,
                "execution_count": len(executions),
                "success_rate": 0,
                "validation_passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if executions:
                successful_executions = [e for e in executions if e.status == TaskStatus.COMPLETED.value]
                validation_result["success_rate"] = len(successful_executions) / len(executions)
                validation_result["validation_passed"] = validation_result["success_rate"] >= self.config.auto_merge_threshold
            
            # Record validation metric
            await self.record_metric(
                project_id=task.project_id,
                metric_name="implementation_validation",
                metric_value=validation_result,
                metadata={"task_id": str(task_id)}
            )
            
            return validation_result
            
        finally:
            db.close()
    
    async def auto_merge_successful_implementations(self, project_id: Union[str, uuid.UUID]) -> List[str]:
        """Automatically merge successful implementations to main branch"""
        merged_tasks = []
        
        db = self.get_db()
        try:
            # Get completed tasks
            completed_tasks = db.query(Task).filter(
                Task.project_id == project_id,
                Task.status == TaskStatus.COMPLETED.value
            ).all()
            
            for task in completed_tasks:
                validation_result = await self.validate_implementation(task.id)
                
                if validation_result["validation_passed"]:
                    # Simulate merge operation (placeholder)
                    merge_result = await self._perform_merge(task)
                    
                    if merge_result["success"]:
                        merged_tasks.append(str(task.id))
                        
                        # Log merge event
                        await self.log_event(
                            project_id=project_id,
                            event_type="system",
                            source="auto_merge",
                            event_data={
                                "action": "task_merged",
                                "task_id": str(task.id),
                                "merge_result": merge_result
                            }
                        )
            
            return merged_tasks
            
        finally:
            db.close()
    
    async def _perform_merge(self, task: Task) -> Dict[str, Any]:
        """Perform merge operation (placeholder implementation)"""
        # This would integrate with your Git/version control system
        return {
            "success": True,
            "merge_commit": "abc123def456",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Utility Methods
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        db = self.get_db()
        try:
            # Count various entities
            project_count = db.query(Project).count()
            task_count = db.query(Task).count()
            active_task_count = db.query(Task).filter(
                Task.status.in_([TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value])
            ).count()
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "statistics": {
                    "total_projects": project_count,
                    "total_tasks": task_count,
                    "active_tasks": active_task_count
                },
                "openevolve_enabled": self.config.openevolve_enabled,
                "database_connected": True
            }
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()

# Factory function for easy initialization
def create_task_management_engine(database_url: str = None, **kwargs) -> TaskManagementEngine:
    """Create and configure a TaskManagementEngine instance"""
    config = TaskManagerConfig(
        database_url=database_url or "postgresql://localhost/task_management",
        **kwargs
    )
    return TaskManagementEngine(config)

# Example usage and testing
async def main():
    """Example usage of the Task Management Engine"""
    # Initialize the engine
    engine = create_task_management_engine(
        database_url="sqlite:///task_management.db",  # Using SQLite for example
        openevolve_enabled=False  # Disable for example if not available
    )
    
    # Create a project
    project = await engine.create_project(
        name="Comprehensive Task Management System",
        description="Implementation of sophisticated task management with OpenEvolve integration",
        repository_url="https://github.com/example/task-management"
    )
    
    # Create tasks
    task1 = await engine.create_task(
        project_id=project.id,
        title="Implement Database Schema",
        description="Create comprehensive database schema for all 5 categories",
        priority=TaskPriority.HIGH
    )
    
    task2 = await engine.create_task(
        project_id=project.id,
        title="Integrate OpenEvolve Components",
        description="Integrate evaluator.py, database.py, and controller.py",
        priority=TaskPriority.HIGH
    )
    
    # Execute tasks
    execution1 = await engine.execute_task(task1.id)
    execution2 = await engine.execute_task(task2.id)
    
    # Monitor progress
    monitoring_result = await engine.monitor_sub_issues(project.id)
    print(f"Project monitoring: {monitoring_result}")
    
    # Get system health
    health = await engine.get_system_health()
    print(f"System health: {health}")

if __name__ == "__main__":
    asyncio.run(main())
