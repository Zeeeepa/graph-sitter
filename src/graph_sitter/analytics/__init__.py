"""
Analytics Module

This module provides comprehensive code analysis capabilities including:
- Multi-language code analysis (Python, TypeScript, JavaScript, Java, C++, Rust, Go)
- Quality scoring and metrics calculation
- Security vulnerability detection
- Performance analysis and optimization recommendations
- Dead code detection and dependency analysis
- Configurable analysis pipelines
"""

from .core.analysis_config import (
    # Configuration classes
    AnalysisConfig,
    QualityThresholds,
    AnalyzerConfig,
    PerformanceConfig,
    OutputConfig,
    
    # Enums
    AnalysisLanguage,
    AnalyzerType,
    ExportFormat,
    
    # Templates
    ConfigTemplates
)

__all__ = [
    # Configuration classes
    'AnalysisConfig',
    'QualityThresholds',
    'AnalyzerConfig', 
    'PerformanceConfig',
    'OutputConfig',
    
    # Enums
    'AnalysisLanguage',
    'AnalyzerType',
    'ExportFormat',
    
    # Templates
    'ConfigTemplates'
]

__version__ = '1.0.0'

