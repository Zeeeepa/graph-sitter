"""
GitHub Extension for Contexten

Provides comprehensive GitHub integration with webhook handling, 
repository management, and event processing.
"""

from .github import GitHub, GitHubEventHandler
from .github_types import GitHubWebhookPayload
from .types.base import GitHubInstallation
from .types.pull_request import PullRequest
from .types.push import Push
from .types.commit import Commit

__version__ = "1.0.0"
__all__ = [
    "GitHub",
    "GitHubEventHandler",
    "GitHubWebhookPayload",
    "GitHubInstallation",
    "PullRequest", 
    "Push",
    "Commit"
]

