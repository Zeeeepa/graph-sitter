"""
Minimal adapter for Contexten extensions integration with Graph_sitter.
Provides compatibility layer for the refactored contexten extensions structure.
"""

from typing import Optional, Dict, Any
import importlib
import sys
from pathlib import Path

class ContextenAdapter:
    """Adapter to bridge Graph_sitter with refactored Contexten extensions."""
    
    def __init__(self):
        self._cached_modules = {}
    
    def get_github_adapter(self):
        """Get Github extension adapter."""
        if 'github' not in self._cached_modules:
            try:
                from contexten.extensions.Github import github
                self._cached_modules['github'] = github
            except ImportError:
                return None
        return self._cached_modules['github']
    
    def get_linear_adapter(self):
        """Get Linear extension adapter."""
        if 'linear' not in self._cached_modules:
            try:
                from contexten.extensions.Linear import linear
                self._cached_modules['linear'] = linear
            except ImportError:
                return None
        return self._cached_modules['linear']
    
    def get_slack_adapter(self):
        """Get Slack extension adapter."""
        if 'slack' not in self._cached_modules:
            try:
                from contexten.extensions.Slack import slack
                self._cached_modules['slack'] = slack
            except ImportError:
                return None
        return self._cached_modules['slack']
    
    def get_mcp_adapter(self):
        """Get MCP adapter."""
        if 'mcp' not in self._cached_modules:
            try:
                from contexten import mcp
                self._cached_modules['mcp'] = mcp
            except ImportError:
                return None
        return self._cached_modules['mcp']
    
    def get_contexten_app(self):
        """Get Contexten app."""
        try:
            from contexten.extensions.Contexten.contexten_app import ContextenApp
            return ContextenApp
        except ImportError:
            return None

# Global adapter instance
contexten_adapter = ContextenAdapter()

