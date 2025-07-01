"""
Autonomous CI/CD System for Graph-Sitter with Codegen SDK Integration

This module provides intelligent CI/CD automation that can:
- Self-heal failing pipelines using Codegen SDK
- Auto-review PRs with contextual understanding
- Continuously optimize pipeline performance
- Predict and prevent failures before they occur
- Generate intelligent test cases and documentation
"""

from .autonomous_pipeline_manager import AutonomousPipelineManager
from .intelligent_pr_reviewer import IntelligentPRReviewer
from .self_healing_pipeline import SelfHealingPipeline
from .predictive_failure_detector import PredictiveFailureDetector
from .auto_test_generator import AutoTestGenerator

__all__ = [
    'AutonomousPipelineManager',
    'IntelligentPRReviewer', 
    'SelfHealingPipeline',
    'PredictiveFailureDetector',
    'AutoTestGenerator'
]

__version__ = "1.0.0"

