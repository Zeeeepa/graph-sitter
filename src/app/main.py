"""
Main FastAPI application module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1.api import api_router
from .core.events import create_start_app_handler, create_stop_app_handler

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add event handlers
    application.add_event_handler("startup", create_start_app_handler())
    application.add_event_handler("shutdown", create_stop_app_handler())

    # Include API router
    application.include_router(api_router, prefix="/api/v1")

    return application

app = create_application()

