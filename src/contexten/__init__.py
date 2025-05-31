"""
Contexten - Agentic orchestrator with enhanced integrations
Enhanced implementation from contexten/extensions with comprehensive
Linear, GitHub, and Slack integrations for the graph-sitter system.
"""

from .core import ContextenOrchestrator
from .extensions import LinearExtension, GitHubExtension, SlackExtension
from .client import ContextenClient

__version__ = "1.0.0"
__all__ = [
    "ContextenOrchestrator",
    "LinearExtension", 
    "GitHubExtension",
    "SlackExtension",
    "ContextenClient"
]

