"""
API router configuration.
"""

from fastapi import APIRouter

from .endpoints import auth, repositories, validation

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(repositories.router, prefix="/repos", tags=["repositories"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])

