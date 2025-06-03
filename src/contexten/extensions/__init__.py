"""Contexten package - AI agent extensions and tools."""

# Import available extensions with error handling
try:
    from .github.github import GitHubClient
except ImportError:
    GitHubClient = None

try:
    from .linear.linear_client import LinearClient
except ImportError:
    LinearClient = None

try:
    from .prefect.client import PrefectClient
except ImportError:
    PrefectClient = None

__all__ = ["GitHubClient", "LinearClient", "PrefectClient"]

