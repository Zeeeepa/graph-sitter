"""
Tasks and Workflows Models

Task lifecycle management and workflow orchestration models
for the comprehensive CI/CD system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, Session

from ..base import DatabaseModel, AuditedModel, DescriptionMixin, StatusMixin


# Define enums
TASK_TYPE_ENUM = ENUM(
    'epic', 'feature', 'story', 'task', 'bug', 'research', 
    'documentation', 'testing', 'deployment', 'maintenance',
    name='task_type',
    create_type=True
)

TASK_STATUS_ENUM = ENUM(
    'backlog', 'todo', 'in_progress', 'in_review', 
    'testing', 'done', 'cancelled', 'blocked',
    name='task_status',
    create_type=True
)

PRIORITY_LEVEL_ENUM = ENUM(
    'low', 'normal', 'high', 'urgent', 'critical',
    name='priority_level',
    create_type=False  # Already created in extensions.sql
)


class TaskDefinition(AuditedModel, DescriptionMixin):
    """
    Reusable task template definitions.
    
    Defines reusable task templates with configuration, resource requirements,
    and execution parameters for workflow orchestration.
    """
    __tablename__ = 'task_definitions'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Task template information
    task_type = Column(TASK_TYPE_ENUM, nullable=False, default='task')
    category = Column(String(100), nullable=False, default='general')
    
    # Configuration and parameters
    configuration = Column('configuration', DatabaseModel.metadata.type, nullable=False, default=dict)
    default_parameters = Column('default_parameters', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Resource requirements
    estimated_duration_minutes = Column(Integer, nullable=True)
    required_resources = Column('required_resources', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Execution settings
    timeout_minutes = Column(Integer, nullable=False, default=60)
    retry_count = Column(Integer, nullable=False, default=3)
    retry_delay_seconds = Column(Integer, nullable=False, default=60)
    
    # Template metadata
    version = Column(String(20), nullable=False, default='1.0.0')
    is_active = Column(Boolean, nullable=False, default=True)
    usage_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    organization = relationship("Organization")
    tasks = relationship("Task", back_populates="task_definition")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', 'version', name='uq_task_def_org_name_version'),
        Index('idx_task_definitions_org', 'organization_id'),
        Index('idx_task_definitions_type', 'task_type'),
        Index('idx_task_definitions_category', 'category'),
        Index('idx_task_definitions_active', 'is_active'),
        Index('idx_task_definitions_usage', 'usage_count'),
    )
    
    def __init__(self, organization_id: str, name: str, task_type: str, **kwargs):
        """Initialize task definition with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            task_type=task_type,
            **kwargs
        )
    
    def create_task_instance(self, session: Session, **override_params) -> 'Task':
        """Create a task instance from this definition."""
        # Merge default parameters with overrides
        parameters = self.default_parameters.copy()
        parameters.update(override_params.get('parameters', {}))
        
        task = Task(
            organization_id=self.organization_id,
            task_definition=self,
            title=override_params.get('title', self.name),
            description=override_params.get('description', self.description),
            task_type=self.task_type,
            configuration=self.configuration.copy(),
            parameters=parameters,
            estimated_duration_minutes=override_params.get('estimated_duration_minutes', self.estimated_duration_minutes),
            timeout_minutes=override_params.get('timeout_minutes', self.timeout_minutes),
            retry_count=override_params.get('retry_count', self.retry_count),
            **{k: v for k, v in override_params.items() if k not in ['parameters', 'title', 'description', 'estimated_duration_minutes', 'timeout_minutes', 'retry_count']}
        )
        
        # Increment usage count
        self.usage_count += 1
        
        session.add(task)
        session.add(self)
        return task
    
    def get_definition_stats(self) -> Dict[str, Any]:
        """Get task definition statistics."""
        return {
            'id': str(self.id),
            'name': self.name,
            'task_type': self.task_type,
            'category': self.category,
            'version': self.version,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'timeout_minutes': self.timeout_minutes,
            'retry_count': self.retry_count,
            'total_tasks': len(self.tasks) if hasattr(self, 'tasks') else 0,
        }


class Task(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Individual task execution instances.
    
    Represents individual task executions with comprehensive tracking,
    resource monitoring, and workflow integration.
    """
    __tablename__ = 'tasks'
    
    # Organization and relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    task_definition_id = Column(UUID(as_uuid=True), ForeignKey('task_definitions.id', ondelete='SET NULL'), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id', ondelete='SET NULL'), nullable=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflows.id', ondelete='SET NULL'), nullable=True)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True)
    
    # Task identification
    title = Column(String(500), nullable=False)
    task_type = Column(TASK_TYPE_ENUM, nullable=False, default='task')
    priority = Column(PRIORITY_LEVEL_ENUM, nullable=False, default='normal')
    
    # Assignment and ownership
    assignee_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # External references
    external_refs = Column('external_refs', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Task configuration and parameters
    configuration = Column('configuration', DatabaseModel.metadata.type, nullable=False, default=dict)
    parameters = Column('parameters', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Effort tracking
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    progress_percentage = Column(Integer, nullable=False, default=0)
    
    # Execution tracking
    scheduled_at = Column('scheduled_at', DatabaseModel.created_at.type, nullable=True)
    started_at = Column('started_at', DatabaseModel.created_at.type, nullable=True)
    completed_at = Column('completed_at', DatabaseModel.created_at.type, nullable=True)
    due_date = Column('due_date', DatabaseModel.created_at.type, nullable=True)
    
    # Execution settings
    timeout_minutes = Column(Integer, nullable=False, default=60)
    retry_count = Column(Integer, nullable=False, default=3)
    current_retry = Column(Integer, nullable=False, default=0)
    
    # Results and output
    results = Column('results', DatabaseModel.metadata.type, nullable=True)
    output_data = Column('output_data', DatabaseModel.metadata.type, nullable=True)
    error_details = Column('error_details', DatabaseModel.metadata.type, nullable=True)
    
    # Resource usage tracking
    cpu_usage_percent = Column(Numeric(5, 2), nullable=True)
    memory_usage_mb = Column(Integer, nullable=True)
    disk_usage_mb = Column(Integer, nullable=True)
    
    # Labels and tags
    labels = Column('labels', DatabaseModel.metadata.type, nullable=False, default=list)
    tags = Column('tags', DatabaseModel.metadata.type, nullable=False, default=list)
    
    # Relationships
    organization = relationship("Organization")
    task_definition = relationship("TaskDefinition", back_populates="tasks")
    project = relationship("Project")
    repository = relationship("Repository")
    workflow = relationship("Workflow", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    parent_task = relationship("Task", remote_side="Task.id", back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task", cascade="all, delete-orphan")
    dependencies_as_dependent = relationship("TaskDependency", foreign_keys="TaskDependency.dependent_task_id", back_populates="dependent_task")
    dependencies_as_dependency = relationship("TaskDependency", foreign_keys="TaskDependency.dependency_task_id", back_populates="dependency_task")
    
    # Constraints
    __table_args__ = (
        Index('idx_tasks_org', 'organization_id'),
        Index('idx_tasks_definition', 'task_definition_id'),
        Index('idx_tasks_project', 'project_id'),
        Index('idx_tasks_repository', 'repository_id'),
        Index('idx_tasks_workflow', 'workflow_id'),
        Index('idx_tasks_parent', 'parent_task_id'),
        Index('idx_tasks_assignee', 'assignee_id'),
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_priority', 'priority'),
        Index('idx_tasks_type', 'task_type'),
        Index('idx_tasks_scheduled', 'scheduled_at'),
        Index('idx_tasks_started', 'started_at'),
        Index('idx_tasks_completed', 'completed_at'),
        Index('idx_tasks_due_date', 'due_date'),
        Index('idx_tasks_progress', 'progress_percentage'),
        Index('idx_tasks_labels_gin', 'labels', postgresql_using='gin'),
        Index('idx_tasks_tags_gin', 'tags', postgresql_using='gin'),
    )
    
    def __init__(self, organization_id: str, title: str, **kwargs):
        """Initialize task with required fields."""
        super().__init__(
            organization_id=organization_id,
            title=title,
            **kwargs
        )
    
    @property
    def dependencies(self) -> List['Task']:
        """Get tasks that this task depends on."""
        return [dep.dependency_task for dep in self.dependencies_as_dependent]
    
    @property
    def dependents(self) -> List['Task']:
        """Get tasks that depend on this task."""
        return [dep.dependent_task for dep in self.dependencies_as_dependency]
    
    def start_task(self) -> None:
        """Start task execution."""
        self.status = 'in_progress'
        self.started_at = datetime.utcnow()
        self.progress_percentage = 0
    
    def complete_task(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Complete task execution."""
        self.status = 'done'
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.actual_duration_minutes = int(duration.total_seconds() / 60)
        
        if results:
            self.results = results
    
    def fail_task(self, error_details: Dict[str, Any]) -> None:
        """Mark task as failed."""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
        self.error_details = error_details
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.actual_duration_minutes = int(duration.total_seconds() / 60)
    
    def can_start(self) -> bool:
        """Check if task can be started (all dependencies completed)."""
        if self.status not in ['backlog', 'todo']:
            return False
        
        for dependency in self.dependencies:
            if dependency.status != 'done':
                return False
        
        return True
    
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date and self.status not in ['done', 'cancelled']
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get task summary information."""
        return {
            'id': str(self.id),
            'title': self.title,
            'task_type': self.task_type,
            'status': self.status,
            'priority': self.priority,
            'progress_percentage': self.progress_percentage,
            'assignee_id': str(self.assignee_id) if self.assignee_id else None,
            'assignee_name': self.assignee.name if self.assignee else None,
            'project_id': str(self.project_id) if self.project_id else None,
            'project_name': self.project.name if self.project else None,
            'workflow_id': str(self.workflow_id) if self.workflow_id else None,
            'parent_task_id': str(self.parent_task_id) if self.parent_task_id else None,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'actual_duration_minutes': self.actual_duration_minutes,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_overdue': self.is_overdue(),
            'can_start': self.can_start(),
            'subtask_count': len(self.subtasks),
            'dependency_count': len(self.dependencies),
            'dependent_count': len(self.dependents),
            'labels': self.labels,
            'tags': self.tags,
        }


class TaskDependency(DatabaseModel, AuditedModel):
    """
    Task dependency relationships.
    
    Manages dependencies between tasks for workflow orchestration
    and execution ordering.
    """
    __tablename__ = 'task_dependencies'
    
    # Organization relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Dependency relationship
    dependent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    dependency_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    
    # Dependency metadata
    dependency_type = Column(String(50), nullable=False, default='blocks')
    description = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    dependent_task = relationship("Task", foreign_keys=[dependent_task_id], back_populates="dependencies_as_dependent")
    dependency_task = relationship("Task", foreign_keys=[dependency_task_id], back_populates="dependencies_as_dependency")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('dependent_task_id', 'dependency_task_id', name='uq_task_dependency'),
        Index('idx_task_deps_org', 'organization_id'),
        Index('idx_task_deps_dependent', 'dependent_task_id'),
        Index('idx_task_deps_dependency', 'dependency_task_id'),
        Index('idx_task_deps_type', 'dependency_type'),
    )
    
    def __init__(self, organization_id: str, dependent_task_id: str, dependency_task_id: str, **kwargs):
        """Initialize task dependency with required fields."""
        super().__init__(
            organization_id=organization_id,
            dependent_task_id=dependent_task_id,
            dependency_task_id=dependency_task_id,
            **kwargs
        )


class Workflow(AuditedModel, DescriptionMixin, StatusMixin):
    """
    Workflow orchestration and management.
    
    Manages multi-task workflows with execution ordering,
    conditional logic, and parallel processing capabilities.
    """
    __tablename__ = 'workflows'
    
    # Organization and project relationships
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    
    # Workflow configuration
    workflow_type = Column(String(100), nullable=False, default='sequential')
    configuration = Column('configuration', DatabaseModel.metadata.type, nullable=False, default=dict)
    
    # Execution tracking
    started_at = Column('started_at', DatabaseModel.created_at.type, nullable=True)
    completed_at = Column('completed_at', DatabaseModel.created_at.type, nullable=True)
    
    # Workflow metadata
    version = Column(String(20), nullable=False, default='1.0.0')
    is_template = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    organization = relationship("Organization")
    project = relationship("Project")
    tasks = relationship("Task", back_populates="workflow")
    
    # Constraints
    __table_args__ = (
        Index('idx_workflows_org', 'organization_id'),
        Index('idx_workflows_project', 'project_id'),
        Index('idx_workflows_type', 'workflow_type'),
        Index('idx_workflows_status', 'status'),
        Index('idx_workflows_template', 'is_template'),
    )
    
    def __init__(self, organization_id: str, name: str, workflow_type: str = 'sequential', **kwargs):
        """Initialize workflow with required fields."""
        super().__init__(
            organization_id=organization_id,
            name=name,
            workflow_type=workflow_type,
            **kwargs
        )
    
    def start_workflow(self) -> None:
        """Start workflow execution."""
        self.status = 'in_progress'
        self.started_at = datetime.utcnow()
    
    def complete_workflow(self) -> None:
        """Complete workflow execution."""
        self.status = 'done'
        self.completed_at = datetime.utcnow()
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get workflow summary information."""
        task_statuses = {}
        for task in self.tasks:
            status = task.status
            task_statuses[status] = task_statuses.get(status, 0) + 1
        
        return {
            'id': str(self.id),
            'name': self.name,
            'workflow_type': self.workflow_type,
            'status': self.status,
            'version': self.version,
            'is_template': self.is_template,
            'project_id': str(self.project_id) if self.project_id else None,
            'project_name': self.project.name if self.project else None,
            'total_tasks': len(self.tasks),
            'task_statuses': task_statuses,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

