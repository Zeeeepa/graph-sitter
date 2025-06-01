"""Advanced Code Metrics and Analysis Engine

This module provides comprehensive code metrics and analysis capabilities including:
- Cyclomatic Complexity
- Halstead Volume
- Maintainability Index
- Lines of Code Metrics
- Depth of Inheritance
- Function Context Analysis
- Quality Analysis
- Test Analysis

The metrics engine integrates with the existing graph_sitter functionality
and provides database storage for historical tracking and trend analysis.
"""

from .core.metrics_engine import MetricsEngine
from .core.metrics_registry import MetricsRegistry
from .calculators.cyclomatic_complexity import CyclomaticComplexityCalculator
from .calculators.halstead_volume import HalsteadVolumeCalculator
from .calculators.maintainability_index import MaintainabilityIndexCalculator
from .calculators.lines_of_code import LinesOfCodeCalculator
from .calculators.depth_of_inheritance import DepthOfInheritanceCalculator
from .models.metrics_data import MetricsData, FunctionMetrics, ClassMetrics, FileMetrics
from .analysis.function_context import FunctionContextAnalyzer
from .analysis.quality_analyzer import QualityAnalyzer
from .analysis.test_analyzer import TestAnalyzer
from .storage.metrics_database import MetricsDatabase

__all__ = [
    "MetricsEngine",
    "MetricsRegistry", 
    "CyclomaticComplexityCalculator",
    "HalsteadVolumeCalculator",
    "MaintainabilityIndexCalculator",
    "LinesOfCodeCalculator",
    "DepthOfInheritanceCalculator",
    "MetricsData",
    "FunctionMetrics",
    "ClassMetrics", 
    "FileMetrics",
    "FunctionContextAnalyzer",
    "QualityAnalyzer",
    "TestAnalyzer",
    "MetricsDatabase",
]

