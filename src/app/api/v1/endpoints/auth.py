"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.base import get_db
from ....auth.github import github_oauth, get_current_user
from ....db.models import User

router = APIRouter()

@router.get("/login/github")
async def github_login():
    """Get GitHub OAuth login URL."""
    return {
        "url": f"https://github.com/login/oauth/authorize?client_id={github_oauth.client_id}&redirect_uri={github_oauth.callback_url}"
    }

@router.get("/login/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle GitHub OAuth callback."""
    try:
        # Get access token
        access_token = await github_oauth.get_access_token(code)
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        # Get user info
        user_info = await github_oauth.get_user_info(access_token)
        
        # Get or create user
        user = await github_oauth.get_or_create_user(user_info, db)
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "email": current_user.email,
        "username": current_user.username,
    }

