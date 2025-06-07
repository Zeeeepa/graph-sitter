"""
Codegen Package Overlay System

This package provides overlay functionality for enhancing pip-installed codegen packages
with contexten integration while preserving the original API.

Usage:
    python extensions/codegen/apply_overlay.py

This will enhance the existing codegen package with:
- Contexten ecosystem integration
- Enhanced monitoring and metrics
- Event handling and callbacks
- Health checks and debugging tools

The original API remains unchanged:
    from codegen.agents.agent import Agent
    agent = Agent(org_id="11", token="your_token")
"""

__version__ = "1.0.0"
__author__ = "Contexten Team"

# This module provides overlay functionality for the codegen package
# It does not replace the codegen package, but enhances it

