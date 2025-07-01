"""
GitHub OAuth authentication handler.
"""

from typing import Optional, Dict, Any
import aiohttp
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.base import get_db
from ..db.models import User

class GitHubOAuth:
    """GitHub OAuth handler."""

    def __init__(self):
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        self.callback_url = settings.GITHUB_CALLBACK_URL

    async def get_access_token(self, code: str) -> str:
        """Exchange code for access token."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.callback_url,
                },
                headers={"Accept": "application/json"},
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to get access token")
                data = await response.json()
                return data.get("access_token")

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get GitHub user information."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to get user info")
                return await response.json()

    async def get_or_create_user(
        self, user_info: Dict[str, Any], db: AsyncSession
    ) -> User:
        """Get existing user or create new one."""
        # Check if user exists
        user = await db.query(User).filter(User.github_id == str(user_info["id"])).first()
        
        if not user:
            # Create new user
            user = User(
                github_id=str(user_info["id"]),
                email=user_info.get("email"),
                username=user_info["login"],
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user

github_oauth = GitHubOAuth()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_access_token),
) -> Optional[User]:
    """Get current authenticated user."""
    if not token:
        return None
        
    try:
        user_info = await github_oauth.get_user_info(token)
        return await github_oauth.get_or_create_user(user_info, db)
    except Exception:
        return None

