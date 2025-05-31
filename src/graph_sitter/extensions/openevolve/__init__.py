"""
OpenEvolve Integration Extension for Graph-sitter

This extension integrates OpenEvolve's evolutionary coding capabilities with Graph-sitter's
code analysis and manipulation framework, adding continuous learning mechanics and
comprehensive step context tracking.
"""

from .integration import OpenEvolveIntegration
from .learning_system import ContinuousLearningSystem
from .context_tracker import ContextTracker
from .database_manager import OpenEvolveDatabase
from .performance_monitor import PerformanceMonitor

__all__ = [
    "OpenEvolveIntegration",
    "ContinuousLearningSystem", 
    "ContextTracker",
    "OpenEvolveDatabase",
    "PerformanceMonitor"
]

__version__ = "1.0.0"

