"""
Sandbox environment management.
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from grainchain import Sandbox as GrainchainSandbox

from ..db.models import Sandbox, Repository
from ..core.config import settings

class SandboxManager:
    """Sandbox environment manager."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._active_sandboxes: Dict[int, GrainchainSandbox] = {}

    async def create_sandbox(
        self,
        repository_id: int,
        validation_workflow_id: int,
        environment_vars: Dict[str, str] = None,
    ) -> Sandbox:
        """Create a new sandbox environment."""
        # Create sandbox record
        sandbox = Sandbox(
            repository_id=repository_id,
            validation_workflow_id=validation_workflow_id,
            name=f"sandbox-{uuid.uuid4().hex[:8]}",
            status="initializing",
            environment_vars=environment_vars or {},
        )
        
        self.db.add(sandbox)
        await self.db.commit()
        await self.db.refresh(sandbox)

        try:
            # Initialize Grainchain sandbox
            grainchain_sandbox = await GrainchainSandbox().create()
            self._active_sandboxes[sandbox.id] = grainchain_sandbox

            # Update status
            sandbox.status = "active"
            await self.db.commit()
            await self.db.refresh(sandbox)

            return sandbox

        except Exception as e:
            # Update status on failure
            sandbox.status = "failed"
            sandbox.results = {"error": str(e)}
            await self.db.commit()
            await self.db.refresh(sandbox)
            raise

    async def get_sandbox(self, sandbox_id: int) -> Optional[Sandbox]:
        """Get sandbox by ID."""
        query = select(Sandbox).where(Sandbox.id == sandbox_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_sandboxes(
        self,
        repository_id: Optional[int] = None,
        validation_workflow_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Sandbox]:
        """List sandboxes with optional filters."""
        query = select(Sandbox)
        
        if repository_id:
            query = query.where(Sandbox.repository_id == repository_id)
        if validation_workflow_id:
            query = query.where(Sandbox.validation_workflow_id == validation_workflow_id)
        if status:
            query = query.where(Sandbox.status == status)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def run_command(self, sandbox_id: int, command: str) -> Dict[str, Any]:
        """Run a command in a sandbox."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError("Sandbox not found")

        grainchain_sandbox = self._active_sandboxes.get(sandbox_id)
        if not grainchain_sandbox:
            raise ValueError("Sandbox not active")

        try:
            # Run command
            result = await grainchain_sandbox.execute(command)
            
            # Update sandbox results
            current_results = sandbox.results or {}
            current_results[command] = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "timestamp": datetime.utcnow().isoformat(),
            }
            sandbox.results = current_results
            await self.db.commit()
            await self.db.refresh(sandbox)

            return current_results[command]

        except Exception as e:
            # Update sandbox status on failure
            sandbox.status = "failed"
            sandbox.results = {"error": str(e)}
            await self.db.commit()
            await self.db.refresh(sandbox)
            raise

    async def cleanup_sandbox(self, sandbox_id: int) -> bool:
        """Clean up a sandbox environment."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return False

        # Cleanup Grainchain sandbox
        grainchain_sandbox = self._active_sandboxes.pop(sandbox_id, None)
        if grainchain_sandbox:
            await grainchain_sandbox.cleanup()

        # Update status
        sandbox.status = "cleaned"
        await self.db.commit()
        await self.db.refresh(sandbox)

        return True

    async def cleanup_old_sandboxes(self) -> int:
        """Clean up sandboxes older than MAX_SANDBOX_AGE_DAYS."""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.MAX_SANDBOX_AGE_DAYS)
        
        # Find old sandboxes
        query = select(Sandbox).where(Sandbox.created_at < cutoff_date)
        result = await self.db.execute(query)
        old_sandboxes = result.scalars().all()

        # Clean up each sandbox
        cleaned_count = 0
        for sandbox in old_sandboxes:
            if await self.cleanup_sandbox(sandbox.id):
                cleaned_count += 1

        return cleaned_count

