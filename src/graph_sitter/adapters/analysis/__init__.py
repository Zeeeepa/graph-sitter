"""
Comprehensive Analysis Framework

A unified, modular analysis system that consolidates all codebase analysis functionality.
Provides advanced metrics, pattern detection, visualization, and AI-powered insights.
"""

from .core.engine import AnalysisEngine, analyze_codebase
from .core.config import AnalysisConfig, AnalysisResult, AnalysisPresets

# Import main analysis components
from .metrics.quality import QualityAnalyzer
from .metrics.complexity import ComplexityAnalyzer
from .detection.patterns import PatternDetector
from .detection.dead_code import DeadCodeDetector
from .detection.import_loops import ImportLoopDetector
from .visualization.tree_sitter import TreeSitterVisualizer
from .ai.insights import AIInsightGenerator
from .ai.training_data import TrainingDataGenerator

__version__ = "1.0.0"
__author__ = "Graph-sitter Analysis Framework"

# Main API functions
__all__ = [
    # Core analysis
    'analyze_codebase',
    'AnalysisEngine',
    'AnalysisConfig',
    'AnalysisResult',
    'AnalysisPresets',
    
    # Analysis components
    'QualityAnalyzer',
    'ComplexityAnalyzer',
    'PatternDetector',
    'DeadCodeDetector',
    'ImportLoopDetector',
    'TreeSitterVisualizer',
    'AIInsightGenerator',
    'TrainingDataGenerator',
    
    # Convenience functions
    'get_codebase_summary',
    'find_dead_code',
    'detect_patterns',
    'generate_training_data',
    'create_visualization'
]


def get_codebase_summary(codebase_path: str, **kwargs) -> dict:
    """
    Get a quick summary of codebase metrics.
    
    Args:
        codebase_path: Path to the codebase
        **kwargs: Additional analysis options
        
    Returns:
        Dictionary containing summary metrics
    """
    config = AnalysisConfig()
    config.enable_ai_analysis = False  # Disable for quick summary
    config.generate_visualizations = False
    
    result = analyze_codebase(codebase_path, config, **kwargs)
    return result.get_summary_stats()


def find_dead_code(codebase_path: str, **kwargs) -> list:
    """
    Find dead code in the codebase.
    
    Args:
        codebase_path: Path to the codebase
        **kwargs: Additional analysis options
        
    Returns:
        List of dead code items
    """
    config = AnalysisConfig()
    config.enable_dead_code_detection = True
    config.enable_quality_metrics = False
    config.enable_complexity_analysis = False
    config.enable_pattern_detection = False
    config.enable_ai_analysis = False
    config.generate_visualizations = False
    
    result = analyze_codebase(codebase_path, config, **kwargs)
    return result.dead_code


def detect_patterns(codebase_path: str, **kwargs) -> list:
    """
    Detect code patterns and anti-patterns.
    
    Args:
        codebase_path: Path to the codebase
        **kwargs: Additional analysis options
        
    Returns:
        List of detected patterns
    """
    config = AnalysisConfig()
    config.enable_pattern_detection = True
    config.enable_quality_metrics = False
    config.enable_complexity_analysis = False
    config.enable_dead_code_detection = False
    config.enable_ai_analysis = False
    config.generate_visualizations = False
    
    result = analyze_codebase(codebase_path, config, **kwargs)
    return result.patterns


def generate_training_data(codebase_path: str, data_types: list = None, **kwargs) -> dict:
    """
    Generate machine learning training data from codebase.
    
    Args:
        codebase_path: Path to the codebase
        data_types: Types of training data to generate
        **kwargs: Additional analysis options
        
    Returns:
        Dictionary containing training datasets
    """
    # This would require access to the actual codebase object
    # For now, return a placeholder
    return {
        'note': 'Training data generation requires direct codebase access',
        'suggested_approach': 'Use the CLI tool or AnalysisEngine directly'
    }


def create_visualization(codebase_path: str, output_path: str = None, **kwargs) -> str:
    """
    Create interactive visualization of the codebase.
    
    Args:
        codebase_path: Path to the codebase
        output_path: Path for output HTML file
        **kwargs: Additional analysis options
        
    Returns:
        Path to the generated visualization file
    """
    config = AnalysisConfig()
    config.generate_visualizations = True
    config.export_html = True
    
    result = analyze_codebase(codebase_path, config, **kwargs)
    
    if result.visualization_data:
        visualizer = TreeSitterVisualizer()
        
        if output_path is None:
            output_path = visualizer.create_temporary_visualization(result.visualization_data)
        else:
            visualizer.export_html(result.visualization_data, output_path)
        
        return output_path
    else:
        raise ValueError("No visualization data generated")


# Module-level configuration
def configure_logging(level: str = 'INFO'):
    """Configure logging for the analysis framework."""
    import logging
    
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_version() -> str:
    """Get the version of the analysis framework."""
    return __version__


def get_available_presets() -> list:
    """Get list of available analysis presets."""
    return ['basic', 'comprehensive', 'quality', 'performance', 'ai']


def create_custom_config(**kwargs) -> AnalysisConfig:
    """
    Create a custom analysis configuration.
    
    Args:
        **kwargs: Configuration options
        
    Returns:
        AnalysisConfig object
    """
    return AnalysisConfig(**kwargs)


# Framework information
FRAMEWORK_INFO = {
    'name': 'Graph-sitter Analysis Framework',
    'version': __version__,
    'description': 'Comprehensive codebase analysis with graph-sitter integration',
    'features': [
        'Quality metrics analysis',
        'Complexity analysis',
        'Pattern detection',
        'Dead code detection',
        'Import loop detection',
        'Interactive visualizations',
        'AI-powered insights',
        'Training data generation'
    ],
    'supported_languages': ['Python'],  # Extensible
    'requirements': {
        'optional': ['graph-sitter', 'openai'],
        'visualization': ['d3.js (included in HTML export)']
    }
}


def print_framework_info():
    """Print information about the analysis framework."""
    info = FRAMEWORK_INFO
    print(f"🚀 {info['name']} v{info['version']}")
    print(f"📝 {info['description']}")
    print("\n✨ Features:")
    for feature in info['features']:
        print(f"  • {feature}")
    print(f"\n🔧 Supported Languages: {', '.join(info['supported_languages'])}")
    print("\n📦 Requirements:")
    print(f"  Optional: {', '.join(info['requirements']['optional'])}")
    print(f"  Visualization: {', '.join(info['requirements']['visualization'])}")


# Quick start example
QUICK_START_EXAMPLE = '''
# Quick Start Example

from graph_sitter.adapters.analysis import analyze_codebase, AnalysisPresets

# Basic analysis
result = analyze_codebase("/path/to/code")
result.print_summary()

# Comprehensive analysis
config = AnalysisPresets.comprehensive()
result = analyze_codebase("/path/to/code", config)

# Quality-focused analysis
config = AnalysisPresets.quality_focused()
result = analyze_codebase("/path/to/code", config)

# Custom analysis
from graph_sitter.adapters.analysis import AnalysisConfig
config = AnalysisConfig(
    enable_ai_analysis=True,
    generate_visualizations=True,
    ai_api_key="your-api-key"
)
result = analyze_codebase("/path/to/code", config)

# Access specific results
print(f"Quality Score: {result.quality_metrics.get('maintainability_score', 0)}")
print(f"Dead Code Items: {len(result.dead_code)}")
print(f"Pattern Issues: {len(result.patterns)}")

# Export results
result.save_to_file("analysis_results.json")

# Generate visualization
from graph_sitter.adapters.analysis import create_visualization
viz_path = create_visualization("/path/to/code", "report.html")
print(f"Visualization saved to: {viz_path}")
'''


def print_quick_start():
    """Print quick start example."""
    print("🚀 Quick Start Example:")
    print(QUICK_START_EXAMPLE)

