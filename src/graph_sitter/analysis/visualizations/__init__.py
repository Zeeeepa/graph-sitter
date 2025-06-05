"""
Visualization adapters for graph-sitter codebase analysis.

This module contains all visualization-related functionality including:
- React-based interactive visualizations
- HTML report generation
- Codebase visualization components
- Blast radius and dependency visualizations
"""

from .react_visualizations import (
    ReactVisualizationGenerator,
    create_react_visualizations,
    generate_function_blast_radius,
    generate_issue_dashboard,
    generate_complexity_heatmap,
    generate_call_graph_visualization,
    generate_dependency_graph_visualization,
    generate_class_methods_visualization,
    generate_metrics_dashboard,
    generate_issues_visualization
)

from .codebase_visualization import (
    CodebaseVisualizer,
    create_comprehensive_visualization,
    create_interactive_html_report,
    generate_visualization_data,
    create_visualization_components
)

__all__ = [
    # React visualizations
    'ReactVisualizationGenerator',
    'create_react_visualizations',
    'generate_function_blast_radius',
    'generate_issue_dashboard',
    'generate_complexity_heatmap',
    'generate_call_graph_visualization',
    'generate_dependency_graph_visualization',
    'generate_class_methods_visualization',
    'generate_metrics_dashboard',
    'generate_issues_visualization',
    
    # Codebase visualizations
    'CodebaseVisualizer',
    'create_comprehensive_visualization',
    'create_interactive_html_report',
    'generate_visualization_data',
    'create_visualization_components'
]

