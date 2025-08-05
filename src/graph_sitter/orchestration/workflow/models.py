"""
Workflow Data Models

Core data models for workflow definition and execution.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from uuid import uuid4


class WorkflowStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status of individual workflow steps"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class TriggerType(Enum):
    """Types of workflow triggers"""
    MANUAL = "manual"
    EVENT = "event"
    SCHEDULE = "schedule"
    DEPENDENCY = "dependency"


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    id: str
    name: str
    action: str  # Action to execute (e.g., 'github.create_pr', 'linear.update_issue')
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Step IDs this step depends on
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[timedelta] = None
    condition: Optional[str] = None  # Conditional execution expression
    on_failure: Optional[str] = None  # Action on failure ('skip', 'retry', 'fail')
    
    # Runtime state
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None


@dataclass
class WorkflowExecution:
    """Runtime execution instance of a workflow"""
    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution state
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    # Metadata
    triggered_by: Optional[str] = None
    trigger_event: Optional[Dict[str, Any]] = None


@dataclass
class Workflow:
    """Workflow definition"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Trigger configuration
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution settings
    max_concurrent_executions: int = 1
    timeout: Optional[timedelta] = None
    retry_failed_steps: bool = True
    
    # Scheduling
    schedule: Optional[str] = None  # Cron expression
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Other workflow IDs
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def add_step(self, step: WorkflowStep) -> 'Workflow':
        """Add a step to the workflow"""
        self.steps.append(step)
        self.updated_at = datetime.now()
        return self
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_ready_steps(self, completed_steps: List[str]) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)"""
        ready_steps = []
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep_id in completed_steps for dep_id in step.dependencies):
                    ready_steps.append(step)
        return ready_steps
    
    def validate(self) -> List[str]:
        """Validate workflow definition and return any errors"""
        errors = []
        
        # Check for duplicate step IDs
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Duplicate step IDs found")
        
        # Check for circular dependencies
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected")
        
        # Check for invalid dependencies
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    errors.append(f"Step {step.id} depends on non-existent step {dep_id}")
        
        return errors
    
    def _has_circular_dependencies(self) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False
                
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = self.get_step(step_id)
            if step:
                for dep_id in step.dependencies:
                    if has_cycle(dep_id):
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        for step in self.steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    return True
        
        return False


@dataclass
class WorkflowTemplate:
    """Template for creating workflows"""
    id: str
    name: str
    description: str
    template_steps: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def create_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Workflow:
        """Create a workflow instance from this template"""
        workflow = Workflow(
            id=workflow_id,
            name=self.name,
            description=self.description,
            tags=self.tags.copy()
        )
        
        # Create steps from template
        for step_template in self.template_steps:
            step = WorkflowStep(
                id=step_template['id'],
                name=step_template['name'],
                action=step_template['action'],
                parameters={**step_template.get('parameters', {}), **parameters},
                dependencies=step_template.get('dependencies', []),
                max_retries=step_template.get('max_retries', 3),
                timeout=step_template.get('timeout'),
                condition=step_template.get('condition'),
                on_failure=step_template.get('on_failure')
            )
            workflow.add_step(step)
        
        return workflow


# Common workflow patterns
COMMON_WORKFLOWS = {
    'github_pr_review': WorkflowTemplate(
        id='github_pr_review',
        name='GitHub PR Review Workflow',
        description='Automated PR review and feedback workflow',
        template_steps=[
            {
                'id': 'fetch_pr',
                'name': 'Fetch PR Details',
                'action': 'github.get_pr',
                'parameters': {'pr_number': '${pr_number}'}
            },
            {
                'id': 'analyze_code',
                'name': 'Analyze Code Changes',
                'action': 'codegen.analyze_changes',
                'dependencies': ['fetch_pr'],
                'parameters': {'pr_data': '${fetch_pr.result}'}
            },
            {
                'id': 'post_review',
                'name': 'Post Review Comments',
                'action': 'github.create_review',
                'dependencies': ['analyze_code'],
                'parameters': {
                    'pr_number': '${pr_number}',
                    'review_data': '${analyze_code.result}'
                }
            }
        ]
    ),
    
    'linear_issue_sync': WorkflowTemplate(
        id='linear_issue_sync',
        name='Linear Issue Sync Workflow',
        description='Sync GitHub issues with Linear tickets',
        template_steps=[
            {
                'id': 'fetch_github_issue',
                'name': 'Fetch GitHub Issue',
                'action': 'github.get_issue',
                'parameters': {'issue_number': '${issue_number}'}
            },
            {
                'id': 'create_linear_issue',
                'name': 'Create Linear Issue',
                'action': 'linear.create_issue',
                'dependencies': ['fetch_github_issue'],
                'parameters': {
                    'title': '${fetch_github_issue.result.title}',
                    'description': '${fetch_github_issue.result.body}'
                }
            },
            {
                'id': 'link_issues',
                'name': 'Link Issues',
                'action': 'github.add_comment',
                'dependencies': ['create_linear_issue'],
                'parameters': {
                    'issue_number': '${issue_number}',
                    'comment': 'Linked to Linear: ${create_linear_issue.result.url}'
                }
            }
        ]
    )
}

