"""
🔍 Comprehensive Code Analysis System

Consolidated analysis framework combining features from all PRs and existing tools:
- Core analysis engine with dependency tracking
- Advanced code quality metrics and complexity analysis
- Tree-sitter integration with query patterns
- Interactive visualization and reporting
- AI-powered code analysis and improvement
- Dead code detection and import loop analysis
- Legacy tool compatibility and migration support

This module consolidates functionality from:
- PRs #211, #212, #213, #214, #215
- analyze_codebase.py
- analyze_codebase_enhanced.py  
- enhanced_analyzer.py
- graph_sitter_enhancements.py
"""

from .core.engine import AnalysisEngine, CodebaseAnalyzer
from .core.config import AnalysisConfig, AnalysisResult, AnalysisPresets
from .metrics.quality import QualityMetrics, calculate_quality_metrics
from .metrics.complexity import ComplexityAnalyzer, calculate_complexity_metrics
from .visualization.reports import HTMLReportGenerator, InteractiveVisualizer
from .detection.patterns import PatternDetector, detect_code_patterns
from .detection.dead_code import DeadCodeDetector, find_dead_code
from .detection.import_loops import ImportLoopDetector, detect_import_loops
from .ai.insights import AIAnalyzer, generate_ai_insights
from .ai.training_data import TrainingDataGenerator, generate_training_data
from .integration.graph_sitter_config import GraphSitterConfigManager
from .legacy.compatibility import LegacyAnalyzerWrapper

# Main analysis function
def analyze_codebase(path: str, config: AnalysisConfig = None) -> AnalysisResult:
    """
    Comprehensive codebase analysis with all features.
    
    Args:
        path: Path to analyze (file or directory)
        config: Analysis configuration (uses default if None)
    
    Returns:
        AnalysisResult containing all analysis data
    """
    if config is None:
        config = AnalysisPresets.comprehensive()
    
    analyzer = CodebaseAnalyzer(config)
    return analyzer.analyze(path)

# Convenience functions
def quick_analysis(path: str) -> AnalysisResult:
    """Quick analysis with basic metrics"""
    config = AnalysisPresets.quick()
    return analyze_codebase(path, config)

def quality_analysis(path: str) -> AnalysisResult:
    """Quality-focused analysis"""
    config = AnalysisPresets.quality_focused()
    return analyze_codebase(path, config)

def comprehensive_analysis(path: str) -> AnalysisResult:
    """Comprehensive analysis with all features"""
    config = AnalysisPresets.comprehensive()
    return analyze_codebase(path, config)

__all__ = [
    # Main functions
    'analyze_codebase',
    'quick_analysis', 
    'quality_analysis',
    'comprehensive_analysis',
    
    # Core classes
    'AnalysisEngine',
    'CodebaseAnalyzer',
    'AnalysisConfig',
    'AnalysisResult',
    'AnalysisPresets',
    
    # Metrics
    'QualityMetrics',
    'ComplexityAnalyzer',
    'calculate_quality_metrics',
    'calculate_complexity_metrics',
    
    # Visualization
    'HTMLReportGenerator',
    'InteractiveVisualizer',
    
    # Detection
    'PatternDetector',
    'DeadCodeDetector', 
    'ImportLoopDetector',
    'detect_code_patterns',
    'find_dead_code',
    'detect_import_loops',
    
    # AI Integration
    'AIAnalyzer',
    'TrainingDataGenerator',
    'generate_ai_insights',
    'generate_training_data',
    
    # Integration
    'GraphSitterConfigManager',
    
    # Legacy Support
    'LegacyAnalyzerWrapper'
]

# Version information
__version__ = "2.0.0"
__author__ = "Graph-sitter Analysis Team"
__description__ = "Comprehensive codebase analysis and intelligence system"

