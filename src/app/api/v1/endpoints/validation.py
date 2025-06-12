"""
Validation workflow endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.base import get_db
from ....db.models import User, Repository, ValidationWorkflow, Sandbox
from ....auth.github import get_current_user
from ....validation.workflow import ValidationWorkflowManager
from ....sandbox.manager import SandboxManager

router = APIRouter()

@router.get("/repositories/{repo_id}/workflows", response_model=List[dict])
async def list_workflows(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List validation workflows for a repository."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workflow_manager = ValidationWorkflowManager(db)
    workflows = await workflow_manager.list_workflows(repo_id)
    
    return [
        {
            "id": workflow.id,
            "name": workflow.name,
            "is_active": workflow.is_active,
            "setup_commands": workflow.setup_commands,
            "rules": workflow.rules,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
        for workflow in workflows
    ]

@router.post("/repositories/{repo_id}/workflows")
async def create_workflow(
    repo_id: int,
    name: str,
    setup_commands: str,
    rules: dict = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new validation workflow."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workflow_manager = ValidationWorkflowManager(db)
    workflow = await workflow_manager.create_workflow(
        repository_id=repo_id,
        name=name,
        setup_commands=setup_commands,
        rules=rules,
    )
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "is_active": workflow.is_active,
        "setup_commands": workflow.setup_commands,
        "rules": workflow.rules,
    }

@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: int,
    name: Optional[str] = None,
    setup_commands: Optional[str] = None,
    rules: Optional[dict] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a validation workflow."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workflow_manager = ValidationWorkflowManager(db)
    workflow = await workflow_manager.update_workflow(
        workflow_id=workflow_id,
        name=name,
        setup_commands=setup_commands,
        rules=rules,
        is_active=is_active,
    )
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "is_active": workflow.is_active,
        "setup_commands": workflow.setup_commands,
        "rules": workflow.rules,
    }

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a validation workflow."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workflow_manager = ValidationWorkflowManager(db)
    success = await workflow_manager.delete_workflow(workflow_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"status": "success"}

@router.post("/workflows/{workflow_id}/run")
async def run_workflow(
    workflow_id: int,
    environment_vars: dict = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a validation workflow."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workflow_manager = ValidationWorkflowManager(db)
    sandbox = await workflow_manager.run_workflow(
        workflow_id=workflow_id,
        environment_vars=environment_vars,
    )
    
    return {
        "sandbox_id": sandbox.id,
        "status": sandbox.status,
        "results": sandbox.results,
    }

@router.get("/workflows/{workflow_id}/history", response_model=List[dict])
async def get_workflow_history(
    workflow_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workflow execution history."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workflow_manager = ValidationWorkflowManager(db)
    sandboxes = await workflow_manager.get_workflow_history(
        workflow_id=workflow_id,
        limit=limit,
    )
    
    return [
        {
            "id": sandbox.id,
            "name": sandbox.name,
            "status": sandbox.status,
            "results": sandbox.results,
            "created_at": sandbox.created_at,
            "updated_at": sandbox.updated_at,
        }
        for sandbox in sandboxes
    ]

