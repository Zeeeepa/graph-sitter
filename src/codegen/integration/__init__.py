"""
OpenEvolve Integration & Evaluation System

This module provides integration between the OpenEvolve framework and the graph-sitter
codebase for comprehensive effectiveness analysis and performance evaluation.

Components:
- openevolve: Integration layer for OpenEvolve agents
- database: Database overlay system for evaluation tracking
- evaluation: Effectiveness evaluation engine
- analysis: Performance analysis tools
"""

from .openevolve.integration_layer import OpenEvolveIntegrator
from .database.overlay import DatabaseOverlay
from .evaluation.engine import EffectivenessEvaluator
from .analysis.performance import PerformanceAnalyzer

__all__ = [
    "OpenEvolveIntegrator",
    "DatabaseOverlay", 
    "EffectivenessEvaluator",
    "PerformanceAnalyzer"
]

__version__ = "1.0.0"

