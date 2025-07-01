"""
Contexten Learning Module

This module provides continuous learning capabilities including pattern recognition,
performance tracking, and adaptive system optimization.
"""

from .pattern_recognition import (
    PatternRecognitionEngine,
    Pattern,
    PatternType,
    DataPoint
)
from .performance_tracker import (
    PerformanceTracker,
    MetricPoint,
    MetricType,
    PerformanceAlert,
    PerformanceTrend
)
from .adaptation_engine import (
    AdaptationEngine,
    Adaptation,
    AdaptationType,
    AdaptationRule
)

__version__ = "1.0.0"
__all__ = [
    # Pattern Recognition
    "PatternRecognitionEngine",
    "Pattern",
    "PatternType", 
    "DataPoint",
    
    # Performance Tracking
    "PerformanceTracker",
    "MetricPoint",
    "MetricType",
    "PerformanceAlert",
    "PerformanceTrend",
    
    # Adaptation Engine
    "AdaptationEngine",
    "Adaptation",
    "AdaptationType",
    "AdaptationRule"
]

