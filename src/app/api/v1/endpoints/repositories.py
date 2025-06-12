"""
Repository management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.base import get_db
from ....db.models import User, Repository
from ....auth.github import get_current_user
from ....repositories.manager import RepositoryManager

router = APIRouter()

@router.get("/repositories", response_model=List[dict])
async def list_repositories(
    include_private: bool = True,
    only_pinned: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List repositories for current user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    repo_manager = RepositoryManager(db, current_user.github_token)
    repos = await repo_manager.list_repositories(
        current_user.id,
        include_private=include_private,
        only_pinned=only_pinned,
    )
    
    return [
        {
            "id": repo.id,
            "github_id": repo.github_id,
            "name": repo.name,
            "full_name": repo.full_name,
            "is_private": repo.is_private,
            "is_pinned": repo.is_pinned,
        }
        for repo in repos
    ]

@router.post("/repositories/sync")
async def sync_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync repositories from GitHub."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    repo_manager = RepositoryManager(db, current_user.github_token)
    await repo_manager.sync_repositories(current_user)
    
    return {"status": "success"}

@router.post("/repositories/{repo_id}/pin")
async def pin_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pin a repository."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    repo_manager = RepositoryManager(db, current_user.github_token)
    repo = await repo_manager.pin_repository(repo_id)
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {"status": "success"}

@router.post("/repositories/{repo_id}/unpin")
async def unpin_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unpin a repository."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    repo_manager = RepositoryManager(db, current_user.github_token)
    repo = await repo_manager.unpin_repository(repo_id)
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {"status": "success"}

