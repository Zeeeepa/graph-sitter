"""
Platform Integrations

Integration clients for GitHub, Linear, Slack and other platforms.
"""

from .github_client import GitHubIntegration
from .linear_client import LinearIntegration
from .slack_client import SlackIntegration
from .base import BasePlatformIntegration

__all__ = [
    "GitHubIntegration",
    "LinearIntegration",
    "SlackIntegration", 
    "BasePlatformIntegration",
]

