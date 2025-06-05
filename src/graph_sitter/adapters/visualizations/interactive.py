"""
Interactive visualization components for Graph-Sitter.

This module provides interactive visualization components that can be embedded
in dashboards and reports for exploring analysis results.
"""

from typing import Dict, List, Any, Optional
import json

from graph_sitter.core.analysis import AnalysisResult


class InteractiveChart:
    """Base class for interactive charts."""
    
    def __init__(self, chart_id: str, title: str):
        self.chart_id = chart_id
        self.title = title
    
    def render(self, data: Dict[str, Any]) -> str:
        """Render the chart as HTML/JavaScript."""
        raise NotImplementedError


class IssuesSeverityChart(InteractiveChart):
    """Interactive chart for issues by severity."""
    
    def __init__(self, chart_id: str = "issues-severity-chart"):
        super().__init__(chart_id, "Issues by Severity")
    
    def render(self, results: Dict[str, AnalysisResult]) -> str:
        """Render issues severity chart."""
        
        # Aggregate issues by severity
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        for result in results.values():
            for issue in result.issues:
                severity = issue.severity.value
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        chart_data = {
            'x': list(severity_counts.keys()),
            'y': list(severity_counts.values()),
            'type': 'bar',
            'marker': {
                'color': ['#e74c3c', '#f39c12', '#2ecc71']
            }
        }
        
        return f"""
        <div id="{self.chart_id}"></div>
        <script>
            Plotly.newPlot('{self.chart_id}', [{json.dumps(chart_data)}], {{
                title: '{self.title}',
                xaxis: {{ title: 'Severity Level' }},
                yaxis: {{ title: 'Number of Issues' }}
            }}, {{responsive: true}});
        </script>
        """


class MetricsOverviewChart(InteractiveChart):
    """Interactive chart for metrics overview."""
    
    def __init__(self, chart_id: str = "metrics-overview-chart"):
        super().__init__(chart_id, "Metrics Overview")
    
    def render(self, results: Dict[str, AnalysisResult]) -> str:
        """Render metrics overview chart."""
        
        # Aggregate metrics
        all_metrics = {}
        for analyzer_name, result in results.items():
            for metric in result.metrics:
                metric_name = f"{analyzer_name}_{metric.name}"
                all_metrics[metric_name] = metric.value
        
        # Create pie chart data
        chart_data = {
            'labels': list(all_metrics.keys())[:10],  # Top 10 metrics
            'values': list(all_metrics.values())[:10],
            'type': 'pie'
        }
        
        return f"""
        <div id="{self.chart_id}"></div>
        <script>
            Plotly.newPlot('{self.chart_id}', [{json.dumps(chart_data)}], {{
                title: '{self.title}'
            }}, {{responsive: true}});
        </script>
        """


class AnalysisTimelineChart(InteractiveChart):
    """Interactive chart for analysis execution timeline."""
    
    def __init__(self, chart_id: str = "analysis-timeline-chart"):
        super().__init__(chart_id, "Analysis Timeline")
    
    def render(self, results: Dict[str, AnalysisResult]) -> str:
        """Render analysis timeline chart."""
        
        # Extract execution times
        analyzer_names = []
        execution_times = []
        
        for analyzer_name, result in results.items():
            analyzer_names.append(analyzer_name)
            execution_times.append(result.execution_time or 0)
        
        chart_data = {
            'x': analyzer_names,
            'y': execution_times,
            'type': 'scatter',
            'mode': 'lines+markers',
            'marker': {'color': '#3498db'}
        }
        
        return f"""
        <div id="{self.chart_id}"></div>
        <script>
            Plotly.newPlot('{self.chart_id}', [{json.dumps(chart_data)}], {{
                title: '{self.title}',
                xaxis: {{ title: 'Analysis Type' }},
                yaxis: {{ title: 'Execution Time (seconds)' }}
            }}, {{responsive: true}});
        </script>
        """


class InteractiveVisualizationBuilder:
    """Builder for creating interactive visualizations."""
    
    def __init__(self):
        self.charts = []
    
    def add_issues_severity_chart(self, chart_id: str = None) -> 'InteractiveVisualizationBuilder':
        """Add issues severity chart."""
        chart = IssuesSeverityChart(chart_id or f"issues-severity-{len(self.charts)}")
        self.charts.append(chart)
        return self
    
    def add_metrics_overview_chart(self, chart_id: str = None) -> 'InteractiveVisualizationBuilder':
        """Add metrics overview chart."""
        chart = MetricsOverviewChart(chart_id or f"metrics-overview-{len(self.charts)}")
        self.charts.append(chart)
        return self
    
    def add_analysis_timeline_chart(self, chart_id: str = None) -> 'InteractiveVisualizationBuilder':
        """Add analysis timeline chart."""
        chart = AnalysisTimelineChart(chart_id or f"analysis-timeline-{len(self.charts)}")
        self.charts.append(chart)
        return self
    
    def render_all(self, results: Dict[str, AnalysisResult]) -> str:
        """Render all charts."""
        html_parts = []
        
        # Add Plotly.js if not already included
        html_parts.append('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>')
        
        # Render each chart
        for chart in self.charts:
            html_parts.append(chart.render(results))
        
        return '\n'.join(html_parts)
    
    def render_dashboard_section(self, results: Dict[str, AnalysisResult]) -> str:
        """Render as a dashboard section with controls."""
        
        chart_options = []
        for i, chart in enumerate(self.charts):
            chart_options.append(f'<option value="{i}">{chart.title}</option>')
        
        html = f"""
        <div class="interactive-visualization-section">
            <div class="visualization-controls">
                <label for="chart-selector">Select Visualization:</label>
                <select id="chart-selector" onchange="switchChart()">
                    {chr(10).join(chart_options)}
                </select>
            </div>
            
            <div class="chart-container">
        """
        
        # Add all charts (initially hidden except first)
        for i, chart in enumerate(self.charts):
            visibility = "block" if i == 0 else "none"
            html += f'<div id="chart-{i}" style="display: {visibility};">'
            html += chart.render(results)
            html += '</div>'
        
        html += """
            </div>
            
            <script>
                function switchChart() {
                    const selector = document.getElementById('chart-selector');
                    const selectedIndex = selector.value;
                    
                    // Hide all charts
                    for (let i = 0; i < """ + str(len(self.charts)) + """; i++) {
                        const chart = document.getElementById('chart-' + i);
                        if (chart) {
                            chart.style.display = 'none';
                        }
                    }
                    
                    // Show selected chart
                    const selectedChart = document.getElementById('chart-' + selectedIndex);
                    if (selectedChart) {
                        selectedChart.style.display = 'block';
                    }
                }
            </script>
        </div>
        """
        
        return html


def create_default_dashboard(results: Dict[str, AnalysisResult]) -> str:
    """Create a default interactive dashboard with common visualizations."""
    
    builder = InteractiveVisualizationBuilder()
    builder.add_issues_severity_chart()
    builder.add_metrics_overview_chart()
    builder.add_analysis_timeline_chart()
    
    return builder.render_dashboard_section(results)
