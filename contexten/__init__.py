"""
Contexten - Enhanced Orchestrator with SDK-Python and Strands-Agents Integration

This module provides a fully featured orchestrator that integrates:
- SDK-Python for model-driven agent building
- Strands-Agents tools for enhanced capabilities
- Advanced memory management
- System-level event evaluation
- Autonomous CI/CD capabilities
"""

from .orchestrator import EnhancedOrchestrator
from .memory import MemoryManager
from .events import EventEvaluator
from .cicd import AutonomousCICD

__version__ = "1.0.0"
__all__ = [
    "EnhancedOrchestrator",
    "MemoryManager", 
    "EventEvaluator",
    "AutonomousCICD"
]

