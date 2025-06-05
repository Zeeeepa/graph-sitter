"""
Graph-sitter visualization adapters.

This package provides comprehensive visualization capabilities for codebase analysis,
including function call relationships, dependency tracking, blast radius analysis,
and class method relationships.
"""

from .config import (
    VisualizationConfig,
    VisualizationType,
    OutputFormat,
    CallTraceConfig,
    DependencyTraceConfig,
    BlastRadiusConfig,
    MethodRelationshipsConfig,
    create_config,
    get_default_config,
    DEFAULT_COLOR_PALETTE
)

from .base import (
    BaseVisualizationAdapter,
    VisualizationResult,
    FunctionCallMixin,
    DependencyMixin,
    UsageMixin
)

from .call_trace import CallTraceVisualizer
from .dependency_trace import DependencyTraceVisualizer
from .blast_radius import BlastRadiusVisualizer
from .method_relationships import MethodRelationshipsVisualizer
from .manager import UnifiedVisualizationManager

# Convenience functions for backward compatibility
def create_react_visualizations(*args, **kwargs):
    """Create React-compatible visualizations."""
    manager = UnifiedVisualizationManager()
    return manager.create_react_visualizations(*args, **kwargs)

def generate_function_blast_radius(codebase, target_function, **kwargs):
    """Generate blast radius visualization for a function."""
    visualizer = BlastRadiusVisualizer(create_config(VisualizationType.BLAST_RADIUS, **kwargs))
    return visualizer.visualize(codebase, target_function)

def generate_issue_dashboard(*args, **kwargs):
    """Generate issue dashboard visualization."""
    manager = UnifiedVisualizationManager()
    return manager.generate_issue_dashboard(*args, **kwargs)

def generate_complexity_heatmap(*args, **kwargs):
    """Generate complexity heatmap visualization."""
    manager = UnifiedVisualizationManager()
    return manager.generate_complexity_heatmap(*args, **kwargs)

def generate_call_graph_visualization(codebase, target_function, **kwargs):
    """Generate call graph visualization."""
    visualizer = CallTraceVisualizer(create_config(VisualizationType.CALL_TRACE, **kwargs))
    return visualizer.visualize(codebase, target_function)

def generate_dependency_graph_visualization(codebase, target_symbol, **kwargs):
    """Generate dependency graph visualization."""
    visualizer = DependencyTraceVisualizer(create_config(VisualizationType.DEPENDENCY_TRACE, **kwargs))
    return visualizer.visualize(codebase, target_symbol)

def generate_class_methods_visualization(codebase, target_class, **kwargs):
    """Generate class methods visualization."""
    visualizer = MethodRelationshipsVisualizer(create_config(VisualizationType.METHOD_RELATIONSHIPS, **kwargs))
    return visualizer.visualize(codebase, target_class)

def generate_metrics_dashboard(*args, **kwargs):
    """Generate metrics dashboard visualization."""
    manager = UnifiedVisualizationManager()
    return manager.generate_metrics_dashboard(*args, **kwargs)

def generate_issues_visualization(*args, **kwargs):
    """Generate issues visualization."""
    manager = UnifiedVisualizationManager()
    return manager.generate_issues_visualization(*args, **kwargs)

# React visualization components
class ReactVisualizationGenerator:
    """Generator for React-compatible visualizations."""
    
    def __init__(self):
        self.manager = UnifiedVisualizationManager()
    
    def create_react_visualizations(self, *args, **kwargs):
        return self.manager.create_react_visualizations(*args, **kwargs)

# Codebase visualizations
class CodebaseVisualizer:
    """Main visualizer for comprehensive codebase analysis."""
    
    def __init__(self):
        self.manager = UnifiedVisualizationManager()
    
    def create_comprehensive_visualization(self, *args, **kwargs):
        return self.manager.create_comprehensive_visualization(*args, **kwargs)
    
    def create_interactive_html_report(self, *args, **kwargs):
        return self.manager.create_interactive_html_report(*args, **kwargs)
    
    def generate_visualization_data(self, *args, **kwargs):
        return self.manager.generate_visualization_data(*args, **kwargs)
    
    def create_visualization_components(self, *args, **kwargs):
        return self.manager.create_visualization_components(*args, **kwargs)

__all__ = [
    # Configuration
    'VisualizationConfig',
    'VisualizationType', 
    'OutputFormat',
    'CallTraceConfig',
    'DependencyTraceConfig',
    'BlastRadiusConfig',
    'MethodRelationshipsConfig',
    'create_config',
    'get_default_config',
    'DEFAULT_COLOR_PALETTE',
    
    # Base classes
    'BaseVisualizationAdapter',
    'VisualizationResult',
    'FunctionCallMixin',
    'DependencyMixin',
    'UsageMixin',
    
    # Specific visualizers
    'CallTraceVisualizer',
    'DependencyTraceVisualizer', 
    'BlastRadiusVisualizer',
    'MethodRelationshipsVisualizer',
    'UnifiedVisualizationManager',
    
    # Convenience functions
    'create_react_visualizations',
    'generate_function_blast_radius',
    'generate_issue_dashboard',
    'generate_complexity_heatmap',
    'generate_call_graph_visualization',
    'generate_dependency_graph_visualization',
    'generate_class_methods_visualization',
    'generate_metrics_dashboard',
    'generate_issues_visualization',
    
    # React and codebase visualizers
    'ReactVisualizationGenerator',
    'CodebaseVisualizer',
]

