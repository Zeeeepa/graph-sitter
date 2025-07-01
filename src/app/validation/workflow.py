"""
Validation workflow management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db.models import ValidationWorkflow, Repository, Sandbox
from ..sandbox.manager import SandboxManager
from ..core.config import settings

class ValidationWorkflowManager:
    """Validation workflow manager."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sandbox_manager = SandboxManager()

    async def create_workflow(
        self,
        repository_id: int,
        name: str,
        setup_commands: str,
        rules: Dict[str, Any] = None,
    ) -> ValidationWorkflow:
        """Create a new validation workflow."""
        workflow = ValidationWorkflow(
            repository_id=repository_id,
            name=name,
            setup_commands=setup_commands,
            rules=rules or {},
            is_active=True,
        )
        
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[ValidationWorkflow]:
        """Get workflow by ID."""
        query = select(ValidationWorkflow).where(ValidationWorkflow.id == workflow_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_workflows(self, repository_id: int) -> List[ValidationWorkflow]:
        """List all workflows for a repository."""
        query = select(ValidationWorkflow).where(
            ValidationWorkflow.repository_id == repository_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_workflow(
        self,
        workflow_id: int,
        name: Optional[str] = None,
        setup_commands: Optional[str] = None,
        rules: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ValidationWorkflow]:
        """Update workflow settings."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        if name is not None:
            workflow.name = name
        if setup_commands is not None:
            workflow.setup_commands = setup_commands
        if rules is not None:
            workflow.rules = rules
        if is_active is not None:
            workflow.is_active = is_active

        workflow.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow

    async def delete_workflow(self, workflow_id: int) -> bool:
        """Delete a workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False

        await self.db.delete(workflow)
        await self.db.commit()
        return True

    async def run_workflow(
        self,
        workflow_id: int,
        environment_vars: Dict[str, str] = None,
    ) -> Sandbox:
        """Run a validation workflow in a sandbox."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        # Create sandbox
        sandbox = await self.sandbox_manager.create_sandbox(
            repository_id=workflow.repository_id,
            validation_workflow_id=workflow.id,
            environment_vars=environment_vars or {},
        )

        # Run setup commands
        commands = workflow.setup_commands.split("\n")
        for command in commands:
            command = command.strip()
            if command:
                await self.sandbox_manager.run_command(sandbox.id, command)

        # Update sandbox status
        sandbox.status = "completed"
        await self.db.commit()
        await self.db.refresh(sandbox)

        return sandbox

    async def get_workflow_history(
        self,
        workflow_id: int,
        limit: int = 10,
    ) -> List[Sandbox]:
        """Get workflow execution history."""
        query = (
            select(Sandbox)
            .where(Sandbox.validation_workflow_id == workflow_id)
            .order_by(Sandbox.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

