"""
Analysis Configuration Module

Provides configuration management for the analysis system.
"""

from .manager import ConfigManager
from .defaults import DEFAULT_CONFIG, DEFAULT_TOOL_CONFIGS

__all__ = ["ConfigManager", "DEFAULT_CONFIG", "DEFAULT_TOOL_CONFIGS"]