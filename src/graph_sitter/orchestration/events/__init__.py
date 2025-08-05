"""
Event Correlation System

Cross-platform event correlation and analysis for workflow orchestration.
"""

from .correlator import EventCorrelator
from .models import Event, EventCorrelation, CorrelationRule
from .analyzer import EventAnalyzer

__all__ = [
    "EventCorrelator",
    "Event",
    "EventCorrelation", 
    "CorrelationRule",
    "EventAnalyzer",
]

