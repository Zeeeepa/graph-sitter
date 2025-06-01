"""
Continuous Learning and Analytics System

This module provides intelligent pattern recognition, real-time analytics,
and continuous learning capabilities for codebase analysis.
"""

from .pattern_engine import PatternEngine
from .knowledge_graph import KnowledgeGraph
from .analytics_processor import AnalyticsProcessor
from .learning_pipeline import ContinuousLearningPipeline

__version__ = "0.1.0"
__all__ = [
    "PatternEngine",
    "KnowledgeGraph", 
    "AnalyticsProcessor",
    "ContinuousLearningPipeline"
]

