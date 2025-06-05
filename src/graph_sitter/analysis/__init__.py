"""
Graph-sitter Analysis Module

Comprehensive codebase analysis with dashboard visualizations.
"""

from .orchestrator import AnalysisOrchestrator
from .issue_detector import IssueDetector
from .dashboard_generator import HTMLDashboardGenerator
from .visualization_interface import VisualizationInterface

# Import the codebase extension to add Analysis methods
from . import codebase_extension

__all__ = [
    "AnalysisOrchestrator",
    "IssueDetector", 
    "HTMLDashboardGenerator",
    "VisualizationInterface"
]

