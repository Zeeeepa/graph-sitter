"""
Repository management and GitHub integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from github import Github
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db.models import Repository, User
from ..core.config import settings

class RepositoryManager:
    """Repository management."""

    def __init__(self, db: AsyncSession, github_token: str):
        self.db = db
        self.github = Github(github_token)

    async def sync_repositories(self, user: User) -> List[Repository]:
        """Sync repositories from GitHub."""
        # Get repositories from GitHub
        github_repos = list(self.github.get_user().get_repos())
        
        # Update local database
        synced_repos = []
        for github_repo in github_repos:
            repo = await self.get_repository_by_github_id(github_repo.id)
            
            if not repo:
                # Create new repository
                repo = Repository(
                    user_id=user.id,
                    github_id=github_repo.id,
                    name=github_repo.name,
                    full_name=github_repo.full_name,
                    is_private=github_repo.private,
                )
                self.db.add(repo)
            else:
                # Update existing repository
                repo.name = github_repo.name
                repo.full_name = github_repo.full_name
                repo.is_private = github_repo.private
                repo.updated_at = datetime.utcnow()
            
            synced_repos.append(repo)
        
        await self.db.commit()
        for repo in synced_repos:
            await self.db.refresh(repo)
        
        return synced_repos

    async def get_repository(self, repo_id: int) -> Optional[Repository]:
        """Get repository by ID."""
        query = select(Repository).where(Repository.id == repo_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_repository_by_github_id(self, github_id: int) -> Optional[Repository]:
        """Get repository by GitHub ID."""
        query = select(Repository).where(Repository.github_id == github_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_repositories(
        self,
        user_id: int,
        include_private: bool = True,
        only_pinned: bool = False,
    ) -> List[Repository]:
        """List repositories for a user."""
        query = select(Repository).where(Repository.user_id == user_id)
        
        if not include_private:
            query = query.where(Repository.is_private == False)
        if only_pinned:
            query = query.where(Repository.is_pinned == True)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def pin_repository(self, repo_id: int) -> Optional[Repository]:
        """Pin a repository."""
        repo = await self.get_repository(repo_id)
        if not repo:
            return None

        repo.is_pinned = True
        repo.updated_at = datetime.utcnow()
        
        # Set up webhook if not already configured
        if not repo.webhook_id:
            await self._setup_webhook(repo)
        
        await self.db.commit()
        await self.db.refresh(repo)
        
        return repo

    async def unpin_repository(self, repo_id: int) -> Optional[Repository]:
        """Unpin a repository."""
        repo = await self.get_repository(repo_id)
        if not repo:
            return None

        repo.is_pinned = False
        repo.updated_at = datetime.utcnow()
        
        # Remove webhook if exists
        if repo.webhook_id:
            await self._remove_webhook(repo)
        
        await self.db.commit()
        await self.db.refresh(repo)
        
        return repo

    async def _setup_webhook(self, repo: Repository) -> None:
        """Set up GitHub webhook for a repository."""
        github_repo = self.github.get_repo(repo.full_name)
        
        # Create webhook
        webhook = github_repo.create_hook(
            name="web",
            config={
                "url": f"{settings.API_V1_STR}/webhooks/github",
                "content_type": "json",
                "secret": settings.GITHUB_WEBHOOK_SECRET,
            },
            events=["pull_request"],
            active=True,
        )
        
        # Update repository
        repo.webhook_id = webhook.id
        repo.webhook_secret = settings.GITHUB_WEBHOOK_SECRET

    async def _remove_webhook(self, repo: Repository) -> None:
        """Remove GitHub webhook from a repository."""
        if not repo.webhook_id:
            return

        try:
            github_repo = self.github.get_repo(repo.full_name)
            webhook = github_repo.get_hook(repo.webhook_id)
            webhook.delete()
        except Exception:
            pass  # Ignore errors if webhook doesn't exist
        
        # Update repository
        repo.webhook_id = None
        repo.webhook_secret = None

