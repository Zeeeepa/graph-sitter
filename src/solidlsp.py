"""Solidlsp - Direct import compatibility module.

This module re-exports solidlsp functionality to allow:
    from solidlsp import SolidLanguageServer

"""

# Ensure serena path is set up first
from graph_sitter.extensions import *  # noqa: F403, F401

# Re-export solidlsp functionality (now available via serena path)
from solidlsp import *  # noqa: F403, F401