"""
Linear & GitHub Dashboard Implementation

A comprehensive dashboard for managing GitHub projects with Linear integration,
requirements management, webhook integration, and AI-powered chat interface.
"""

from .api.main import create_dashboard_app
from .models.project import Project, ProjectStatus
from .models.requirements import Requirements
from .services.github_service import GitHubService
from .services.linear_service import LinearService
from .services.webhook_service import WebhookService

__all__ = [
    "create_dashboard_app",
    "Project",
    "ProjectStatus", 
    "Requirements",
    "GitHubService",
    "LinearService",
    "WebhookService",
]

