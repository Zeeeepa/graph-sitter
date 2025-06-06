"""
📊 ADVANCED VISUALIZATION MODULE 📊

Comprehensive visualization capabilities for codebase analysis including:
- Interactive HTML reports with D3.js integration
- Dependency graphs and network visualizations
- Code structure diagrams and flowcharts
- Performance metrics dashboards
- Quality assessment visualizations
- Export capabilities for multiple formats
"""

from .interactive_reports import (
    InteractiveReportGenerator,
    create_interactive_report,
    generate_html_report
)

from .dependency_graphs import (
    DependencyGraphGenerator,
    create_dependency_graph,
    visualize_call_graph,
    visualize_import_graph
)

from .dashboards import (
    MetricsDashboard,
    QualityDashboard,
    PerformanceDashboard,
    create_comprehensive_dashboard
)

from .exporters import (
    ReportExporter,
    export_to_html,
    export_to_pdf,
    export_to_json,
    export_to_svg
)

__all__ = [
    # Interactive reports
    'InteractiveReportGenerator',
    'create_interactive_report',
    'generate_html_report',
    
    # Dependency graphs
    'DependencyGraphGenerator',
    'create_dependency_graph',
    'visualize_call_graph',
    'visualize_import_graph',
    
    # Dashboards
    'MetricsDashboard',
    'QualityDashboard',
    'PerformanceDashboard',
    'create_comprehensive_dashboard',
    
    # Exporters
    'ReportExporter',
    'export_to_html',
    'export_to_pdf',
    'export_to_json',
    'export_to_svg'
]

