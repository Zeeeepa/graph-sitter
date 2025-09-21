"""Autogenlib - Direct import compatibility module.

This module re-exports autogenlib functionality to allow:
    from autogenlib import init, set_caching, set_exception_handler

"""

# Ensure serena path is set up first
from graph_sitter.extensions import *  # noqa: F403, F401

# Re-export autogenlib functionality
from graph_sitter.extensions.autogenlib import *  # noqa: F403, F401