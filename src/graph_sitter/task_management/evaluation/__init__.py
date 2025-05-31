"""
Evaluation and Analytics System

Provides comprehensive evaluation capabilities for task effectiveness,
system performance, and optimization recommendations.
"""

from .evaluator import EvaluationSystem, EvaluationConfig, EvaluationResult
from .tracker import EffectivenessTracker, EffectivenessMetrics, TrackingConfig
from .analytics import AnalyticsEngine, AnalyticsReport, TrendAnalysis
from .metrics import EvaluationMetrics, MetricCalculator, MetricAggregator

__all__ = [
    "EvaluationSystem",
    "EvaluationConfig",
    "EvaluationResult", 
    "EffectivenessTracker",
    "EffectivenessMetrics",
    "TrackingConfig",
    "AnalyticsEngine",
    "AnalyticsReport",
    "TrendAnalysis",
    "EvaluationMetrics",
    "MetricCalculator",
    "MetricAggregator",
]

