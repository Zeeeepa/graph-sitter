"""
Workflow builder for creating complex workflows
"""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from ..models.workflow import (
    Workflow, WorkflowStep, StepType, WorkflowCondition, 
    ConditionOperator, WorkflowStatus
)


class WorkflowBuilder:
    """
    Builder for creating complex workflows with fluent API
    """
    
    def __init__(self, name: str, created_by: str):
        self.workflow = Workflow(
            name=name,
            created_by=created_by,
            steps=[]
        )
        self._current_step_id = 0
    
    def description(self, description: str) -> "WorkflowBuilder":
        """Set workflow description"""
        self.workflow.description = description
        return self
    
    def version(self, version: str) -> "WorkflowBuilder":
        """Set workflow version"""
        self.workflow.version = version
        return self
    
    def max_parallel_tasks(self, max_tasks: int) -> "WorkflowBuilder":
        """Set maximum parallel tasks"""
        self.workflow.max_parallel_tasks = max_tasks
        return self
    
    def timeout_seconds(self, timeout: int) -> "WorkflowBuilder":
        """Set workflow timeout"""
        self.workflow.timeout_seconds = timeout
        return self
    
    def context(self, context: Dict[str, Any]) -> "WorkflowBuilder":
        """Set workflow context"""
        self.workflow.context.update(context)
        return self
    
    def variables(self, variables: Dict[str, Any]) -> "WorkflowBuilder":
        """Set workflow variables"""
        self.workflow.variables.update(variables)
        return self
    
    def metadata(self, metadata: Dict[str, Any]) -> "WorkflowBuilder":
        """Set workflow metadata"""
        self.workflow.metadata.update(metadata)
        return self
    
    def tags(self, tags: Set[str]) -> "WorkflowBuilder":
        """Set workflow tags"""
        self.workflow.tags.update(tags)
        return self
    
    def add_task_step(self, 
                     name: str,
                     task_template: Dict[str, Any],
                     depends_on: Set[str] = None,
                     description: Optional[str] = None) -> "WorkflowBuilder":
        """Add a task execution step"""
        step_id = self._generate_step_id()
        
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.TASK,
            task_template=task_template,
            depends_on=depends_on or set()
        )
        
        self.workflow.steps.append(step)
        return self
    
    def add_parallel_step(self,
                         name: str,
                         sub_steps: List[WorkflowStep],
                         depends_on: Set[str] = None,
                         description: Optional[str] = None) -> "WorkflowBuilder":
        """Add a parallel execution step"""
        step_id = self._generate_step_id()
        
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.PARALLEL,
            sub_steps=sub_steps,
            depends_on=depends_on or set()
        )
        
        self.workflow.steps.append(step)
        return self
    
    def add_sequential_step(self,
                           name: str,
                           sub_steps: List[WorkflowStep],
                           depends_on: Set[str] = None,
                           description: Optional[str] = None) -> "WorkflowBuilder":
        """Add a sequential execution step"""
        step_id = self._generate_step_id()
        
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.SEQUENTIAL,
            sub_steps=sub_steps,
            depends_on=depends_on or set()
        )
        
        self.workflow.steps.append(step)
        return self
    
    def add_conditional_step(self,
                            name: str,
                            condition: WorkflowCondition,
                            true_steps: List[WorkflowStep],
                            false_steps: List[WorkflowStep] = None,
                            depends_on: Set[str] = None,
                            description: Optional[str] = None) -> "WorkflowBuilder":
        """Add a conditional execution step"""
        step_id = self._generate_step_id()
        
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.CONDITIONAL,
            condition=condition,
            true_steps=true_steps,
            false_steps=false_steps or [],
            depends_on=depends_on or set()
        )
        
        self.workflow.steps.append(step)
        return self
    
    def add_loop_step(self,
                     name: str,
                     loop_condition: WorkflowCondition,
                     loop_steps: List[WorkflowStep],
                     max_iterations: int = 100,
                     depends_on: Set[str] = None,
                     description: Optional[str] = None) -> "WorkflowBuilder":
        """Add a loop execution step"""
        step_id = self._generate_step_id()
        
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.LOOP,
            loop_condition=loop_condition,
            loop_steps=loop_steps,
            max_iterations=max_iterations,
            depends_on=depends_on or set()
        )
        
        self.workflow.steps.append(step)
        return self
    
    def add_wait_step(self,
                     name: str,
                     wait_seconds: Optional[int] = None,
                     wait_condition: Optional[WorkflowCondition] = None,
                     depends_on: Set[str] = None,
                     description: Optional[str] = None) -> "WorkflowBuilder":
        """Add a wait step"""
        if not wait_seconds and not wait_condition:
            raise ValueError("Either wait_seconds or wait_condition must be specified")
        
        step_id = self._generate_step_id()
        
        step = WorkflowStep(
            id=step_id,
            name=name,
            description=description,
            step_type=StepType.WAIT,
            wait_seconds=wait_seconds,
            wait_condition=wait_condition,
            depends_on=depends_on or set()
        )
        
        self.workflow.steps.append(step)
        return self
    
    def build(self) -> Workflow:
        """Build and return the workflow"""
        return self.workflow
    
    def _generate_step_id(self) -> str:
        """Generate unique step ID"""
        self._current_step_id += 1
        return f"step_{self._current_step_id}"
    
    # Static helper methods for creating common workflow patterns
    
    @staticmethod
    def create_ci_cd_workflow(name: str, created_by: str, repository_url: str) -> Workflow:
        """Create a CI/CD workflow"""
        builder = WorkflowBuilder(name, created_by)
        
        # Build step
        builder.add_task_step(
            "build",
            {
                "name": "Build Application",
                "task_type": "code_generation",
                "metadata": {"repository_url": repository_url, "action": "build"}
            }
        )
        
        # Test step (depends on build)
        builder.add_task_step(
            "test",
            {
                "name": "Run Tests",
                "task_type": "testing",
                "metadata": {"repository_url": repository_url, "test_type": "unit"}
            },
            depends_on={"build"}
        )
        
        # Deploy step (conditional on test success)
        builder.add_conditional_step(
            "deploy_check",
            WorkflowCondition(
                field="test_status",
                operator=ConditionOperator.EQUALS,
                value="passed",
                source="result"
            ),
            true_steps=[
                WorkflowStep(
                    id="deploy",
                    name="Deploy to Production",
                    step_type=StepType.TASK,
                    task_template={
                        "name": "Deploy Application",
                        "task_type": "deployment",
                        "metadata": {"repository_url": repository_url, "environment": "production"}
                    }
                )
            ],
            depends_on={"test"}
        )
        
        return builder.build()
    
    @staticmethod
    def create_data_processing_workflow(name: str, created_by: str, data_sources: List[str]) -> Workflow:
        """Create a data processing workflow"""
        builder = WorkflowBuilder(name, created_by)
        
        # Parallel data extraction
        extraction_steps = []
        for i, source in enumerate(data_sources):
            extraction_steps.append(
                WorkflowStep(
                    id=f"extract_{i}",
                    name=f"Extract from {source}",
                    step_type=StepType.TASK,
                    task_template={
                        "name": f"Extract Data from {source}",
                        "task_type": "custom",
                        "metadata": {"data_source": source, "action": "extract"}
                    }
                )
            )
        
        builder.add_parallel_step(
            "data_extraction",
            extraction_steps,
            description="Extract data from all sources in parallel"
        )
        
        # Data transformation
        builder.add_task_step(
            "transform",
            {
                "name": "Transform Data",
                "task_type": "custom",
                "metadata": {"action": "transform", "sources": data_sources}
            },
            depends_on={"data_extraction"}
        )
        
        # Data loading
        builder.add_task_step(
            "load",
            {
                "name": "Load Data",
                "task_type": "custom",
                "metadata": {"action": "load", "destination": "data_warehouse"}
            },
            depends_on={"transform"}
        )
        
        return builder.build()
    
    @staticmethod
    def create_code_review_workflow(name: str, created_by: str, pull_request_url: str) -> Workflow:
        """Create a code review workflow"""
        builder = WorkflowBuilder(name, created_by)
        
        # Automated checks in parallel
        check_steps = [
            WorkflowStep(
                id="lint_check",
                name="Lint Check",
                step_type=StepType.TASK,
                task_template={
                    "name": "Run Linting",
                    "task_type": "code_analysis",
                    "metadata": {"pr_url": pull_request_url, "check_type": "lint"}
                }
            ),
            WorkflowStep(
                id="security_check",
                name="Security Check",
                step_type=StepType.TASK,
                task_template={
                    "name": "Security Analysis",
                    "task_type": "code_analysis",
                    "metadata": {"pr_url": pull_request_url, "check_type": "security"}
                }
            ),
            WorkflowStep(
                id="test_check",
                name="Test Check",
                step_type=StepType.TASK,
                task_template={
                    "name": "Run Tests",
                    "task_type": "testing",
                    "metadata": {"pr_url": pull_request_url, "test_type": "all"}
                }
            )
        ]
        
        builder.add_parallel_step(
            "automated_checks",
            check_steps,
            description="Run automated checks in parallel"
        )
        
        # Human review (conditional on automated checks passing)
        builder.add_conditional_step(
            "review_gate",
            WorkflowCondition(
                field="all_checks_passed",
                operator=ConditionOperator.EQUALS,
                value=True,
                source="result"
            ),
            true_steps=[
                WorkflowStep(
                    id="human_review",
                    name="Human Code Review",
                    step_type=StepType.TASK,
                    task_template={
                        "name": "Manual Code Review",
                        "task_type": "code_review",
                        "metadata": {"pr_url": pull_request_url, "review_type": "human"}
                    }
                )
            ],
            false_steps=[
                WorkflowStep(
                    id="fix_issues",
                    name="Fix Issues",
                    step_type=StepType.TASK,
                    task_template={
                        "name": "Fix Automated Check Issues",
                        "task_type": "code_generation",
                        "metadata": {"pr_url": pull_request_url, "action": "fix_issues"}
                    }
                )
            ],
            depends_on={"automated_checks"}
        )
        
        return builder.build()
    
    @staticmethod
    def create_monitoring_workflow(name: str, created_by: str, services: List[str]) -> Workflow:
        """Create a monitoring workflow"""
        builder = WorkflowBuilder(name, created_by)
        
        # Health checks loop
        health_check_steps = []
        for service in services:
            health_check_steps.append(
                WorkflowStep(
                    id=f"health_check_{service}",
                    name=f"Health Check - {service}",
                    step_type=StepType.TASK,
                    task_template={
                        "name": f"Check {service} Health",
                        "task_type": "monitoring",
                        "metadata": {"service": service, "check_type": "health"}
                    }
                )
            )
        
        builder.add_loop_step(
            "monitoring_loop",
            WorkflowCondition(
                field="monitoring_active",
                operator=ConditionOperator.EQUALS,
                value=True,
                source="variables"
            ),
            [
                WorkflowStep(
                    id="parallel_health_checks",
                    name="Parallel Health Checks",
                    step_type=StepType.PARALLEL,
                    sub_steps=health_check_steps
                ),
                WorkflowStep(
                    id="wait_interval",
                    name="Wait for Next Check",
                    step_type=StepType.WAIT,
                    wait_seconds=300  # 5 minutes
                )
            ],
            max_iterations=1000  # Run for a long time
        )
        
        return builder.build()

