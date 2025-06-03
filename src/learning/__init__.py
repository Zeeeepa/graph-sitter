"""
Learning Module for Continuous Learning System & Pattern Recognition

This module implements the comprehensive continuous learning system that analyzes
historical patterns, optimizes workflows, and continuously improves the CICD system
based on data-driven insights and machine learning techniques.
"""

from .continuous_learning_engine import ContinuousLearningEngine
from .pattern_recognition import PatternRecognitionEngine
from .workflow_optimizer import WorkflowOptimizer
from .knowledge_manager import KnowledgeManager

__all__ = [
    'ContinuousLearningEngine',
    'PatternRecognitionEngine', 
    'WorkflowOptimizer',
    'KnowledgeManager'
]
