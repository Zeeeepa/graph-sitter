"""
Planning Engine

Integrates with Codegen SDK for automated plan generation.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardPlan, DashboardTask, PlanStatus, TaskStatus

logger = get_logger(__name__)


class PlanningEngine:
    """Handles plan generation using Codegen SDK"""
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.plans: Dict[str, DashboardPlan] = {}
        
    async def initialize(self):
        """Initialize the planning engine"""
        logger.info("Initializing PlanningEngine...")
        
    async def generate_plan(self, project_id: str, requirements: str) -> DashboardPlan:
        """Generate a plan using Codegen SDK"""
        # For testing, create a mock plan
        plan_id = f"plan-{project_id}-{int(datetime.utcnow().timestamp())}"
        
        # Create mock tasks
        tasks = [
            DashboardTask(
                id=f"task-{plan_id}-1",
                plan_id=plan_id,
                title="Setup project structure",
                description="Initialize project with basic structure",
                estimated_hours=2.0
            ),
            DashboardTask(
                id=f"task-{plan_id}-2",
                plan_id=plan_id,
                title="Implement core functionality",
                description="Develop the main features based on requirements",
                estimated_hours=8.0,
                dependencies=[f"task-{plan_id}-1"]
            ),
            DashboardTask(
                id=f"task-{plan_id}-3",
                plan_id=plan_id,
                title="Add tests and documentation",
                description="Create comprehensive tests and documentation",
                estimated_hours=4.0,
                dependencies=[f"task-{plan_id}-2"]
            )
        ]
        
        plan = DashboardPlan(
            id=plan_id,
            project_id=project_id,
            title=f"Implementation Plan for {project_id}",
            description=f"Generated plan based on requirements: {requirements[:100]}...",
            tasks=tasks,
            status=PlanStatus.DRAFT,
            generated_by="codegen",
            codegen_prompt=requirements,
            total_tasks=len(tasks),
            estimated_total_hours=sum(task.estimated_hours for task in tasks)
        )
        
        self.plans[plan_id] = plan
        
        # Update project with plan reference
        await self.dashboard.project_manager.update_project(project_id, {"plan_id": plan_id})
        
        logger.info(f"Generated plan {plan_id} for project {project_id}")
        return plan
    
    async def get_plan(self, plan_id: str) -> Optional[DashboardPlan]:
        """Get specific plan by ID"""
        return self.plans.get(plan_id)
    
    async def update_plan_progress(self, plan_id: str):
        """Update plan progress based on task completion"""
        plan = self.plans.get(plan_id)
        if not plan:
            return
        
        completed_tasks = len([task for task in plan.tasks if task.status == TaskStatus.COMPLETED])
        plan.completed_tasks = completed_tasks
        plan.progress_percentage = (completed_tasks / plan.total_tasks * 100) if plan.total_tasks > 0 else 0
        
        if completed_tasks == plan.total_tasks:
            plan.status = PlanStatus.COMPLETED
        elif completed_tasks > 0:
            plan.status = PlanStatus.IN_PROGRESS
        
        plan.updated_at = datetime.utcnow()

