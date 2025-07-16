"""
Historical Pattern Analysis Engine with Machine Learning

This module provides intelligent pattern recognition, predictive analytics,
and automated optimization recommendations for the graph-sitter system.

Components:
- DataPipeline: Data extraction and preprocessing
- PatternDetectionEngine: Pattern recognition algorithms
- PredictiveAnalyticsService: Predictive models and analytics
- RecommendationEngine: Optimization recommendations
- ModelManager: ML model training and lifecycle management
"""

from .data_pipeline.pipeline import DataPipeline
from .pattern_detection.engine import PatternDetectionEngine
from .predictive_analytics.service import PredictiveAnalyticsService
from .recommendation_engine.engine import RecommendationEngine
from .model_management.manager import ModelManager

__all__ = [
    "DataPipeline",
    "PatternDetectionEngine", 
    "PredictiveAnalyticsService",
    "RecommendationEngine",
    "ModelManager",
]

