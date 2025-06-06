"""
Graph-sitter Analysis Module

This module provides comprehensive codebase analysis capabilities including:
- Core analysis engine with graph-sitter integration
- Code quality and complexity metrics
- Tree-sitter visualization and query patterns
- Pattern detection and dead code analysis
- AI-powered insights and training data generation

Based on features from README2.md and graph-sitter.com advanced settings.
"""

from .core.engine import AnalysisEngine
from .core.config import AnalysisConfig
from .metrics.quality import QualityMetrics
from .metrics.complexity import ComplexityAnalyzer
from .visualization.tree_sitter import TreeSitterVisualizer
from .detection.patterns import PatternDetector
from .detection.import_loops import ImportLoopDetector
from .detection.dead_code import DeadCodeDetector
from .ai.insights import AIInsights
from .ai.training_data import TrainingDataGenerator
from .integration.graph_sitter_config import GraphSitterConfigManager

__all__ = [
    'AnalysisEngine',
    'AnalysisConfig', 
    'QualityMetrics',
    'ComplexityAnalyzer',
    'TreeSitterVisualizer',
    'PatternDetector',
    'ImportLoopDetector',
    'DeadCodeDetector',
    'AIInsights',
    'TrainingDataGenerator',
    'GraphSitterConfigManager'
]

__version__ = "1.0.0"

