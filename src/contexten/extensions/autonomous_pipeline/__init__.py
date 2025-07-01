"""
Autonomous Development Pipeline for Graph-Sitter Contexten
Provides end-to-end automation and intelligent task management.

This module integrates the autonomous development capabilities from OpenAlpha_Evolve
into the Graph-Sitter contexten framework, providing:

- Context Analysis Engine: Comprehensive codebase understanding
- Error Analysis and Classification: Intelligent error categorization
- Automated Debugging System: Self-healing capabilities
- Learning System: Continuous improvement through pattern recognition
- Autonomous Pipeline: End-to-end automation with intelligent task management
"""

from .pipeline_orchestrator import PipelineOrchestrator, PipelineStage, PipelineResult
from .context_analysis_engine import ContextAnalysisEngine, CodebaseSnapshot
from .error_classifier import ErrorClassifier, ErrorClassification
from .auto_debugger import AutoDebugger, DebugResult
from .learning_engine import LearningEngine, LearningPattern

__all__ = [
    'PipelineOrchestrator',
    'PipelineStage', 
    'PipelineResult',
    'ContextAnalysisEngine',
    'CodebaseSnapshot',
    'ErrorClassifier',
    'ErrorClassification',
    'AutoDebugger',
    'DebugResult',
    'LearningEngine',
    'LearningPattern'
]

__version__ = "1.0.0"

