"""
HTML Dashboard Generator - Creates comprehensive HTML dashboards with visualizations
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from graph_sitter.adapters.analysis.enhanced_analysis import AnalysisReport

logger = logging.getLogger(__name__)


class HTMLDashboardGenerator:
    """
    Generates comprehensive HTML dashboards from analysis results.
    
    Creates interactive dashboards with:
    - Issue listing with filtering/sorting
    - Codebase overview metrics
    - Interactive visualizations
    - Drill-down capabilities
    """
    
    def __init__(self):
        """Initialize the dashboard generator."""
        self.template_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"
    
    def generate_dashboard(self, 
                          analysis_report: AnalysisReport,
                          output_dir: str,
                          open_browser: bool = False) -> str:
        """
        Generate complete HTML dashboard.
        
        Args:
            analysis_report: The analysis report to visualize
            output_dir: Directory to save dashboard files
            open_browser: Whether to open dashboard in browser
            
        Returns:
            Path to the main dashboard HTML file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate main dashboard HTML
        dashboard_html = self._generate_main_dashboard(analysis_report)
        dashboard_file = output_path / "dashboard.html"
        
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        # Generate supporting files
        self._generate_data_files(analysis_report, output_path)
        self._copy_static_files(output_path)
        
        logger.info(f"Dashboard generated at: {dashboard_file}")
        
        if open_browser:
            import webbrowser
            webbrowser.open(f"file://{dashboard_file.absolute()}")
        
        return str(dashboard_file.absolute())
    
    def _generate_main_dashboard(self, analysis_report: AnalysisReport) -> str:
        """Generate the main dashboard HTML."""
        
        # Calculate summary statistics
        issues_by_severity = {}
        issues_by_type = {}
        
        for issue in analysis_report.issues:
            severity = issue.get('severity', 'unknown')
            issue_type = issue.get('type', 'unknown')
            
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Dashboard - {analysis_report.codebase_id}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
        }}
        .metric-card {{
            border-left: 4px solid #667eea;
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
        }}
        .issue-severity-critical {{ border-left-color: #dc3545; }}
        .issue-severity-high {{ border-left-color: #fd7e14; }}
        .issue-severity-medium {{ border-left-color: #ffc107; }}
        .issue-severity-low {{ border-left-color: #28a745; }}
        .issue-item {{
            border-left: 3px solid #dee2e6;
            margin-bottom: 0.5rem;
            padding: 0.75rem;
            background: #f8f9fa;
            border-radius: 0.25rem;
        }}
        .issue-critical {{ border-left-color: #dc3545; }}
        .issue-high {{ border-left-color: #fd7e14; }}
        .issue-medium {{ border-left-color: #ffc107; }}
        .issue-low {{ border-left-color: #28a745; }}
        .visualization-container {{
            min-height: 400px;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .health-score {{
            font-size: 3rem;
            font-weight: bold;
        }}
        .health-excellent {{ color: #28a745; }}
        .health-good {{ color: #ffc107; }}
        .health-poor {{ color: #fd7e14; }}
        .health-critical {{ color: #dc3545; }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="dashboard-header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1><i class="fas fa-chart-line"></i> Codebase Analysis Dashboard</h1>
                    <p class="mb-0">Comprehensive analysis for: <strong>{analysis_report.codebase_id}</strong></p>
                    <small>Generated on: {analysis_report.timestamp}</small>
                </div>
                <div class="col-md-4 text-end">
                    <div class="health-score {self._get_health_class(analysis_report.health_score)}">
                        {analysis_report.health_score:.1f}/100
                    </div>
                    <small>Health Score</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="container mt-4">
        <!-- Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-primary">{analysis_report.summary.get('total_files', 0)}</h3>
                        <p class="mb-0">Files Analyzed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-success">{analysis_report.summary.get('total_functions', 0)}</h3>
                        <p class="mb-0">Functions</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h3 class="text-info">{analysis_report.summary.get('total_classes', 0)}</h3>
                        <p class="mb-0">Classes</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card issue-severity-{self._get_dominant_severity(issues_by_severity)}">
                    <div class="card-body text-center">
                        <h3 class="text-danger">{len(analysis_report.issues)}</h3>
                        <p class="mb-0">Issues Found</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Issues Overview -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-exclamation-triangle"></i> Issues by Severity</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="severityChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-tags"></i> Issues by Type</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="typeChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Issues List -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-list"></i> Detected Issues</h5>
                        <div>
                            <select id="severityFilter" class="form-select form-select-sm d-inline-block w-auto me-2">
                                <option value="">All Severities</option>
                                <option value="critical">Critical</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                            <select id="typeFilter" class="form-select form-select-sm d-inline-block w-auto">
                                <option value="">All Types</option>
                                <option value="error">Error</option>
                                <option value="warning">Warning</option>
                                <option value="security">Security</option>
                                <option value="performance">Performance</option>
                                <option value="maintainability">Maintainability</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="issuesList">
                            {self._generate_issues_html(analysis_report.issues)}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Visualizations Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-chart-bar"></i> Codebase Visualizations</h5>
                        <button id="loadVisualizationsBtn" class="btn btn-primary">
                            <i class="fas fa-eye"></i> Load Visualizations
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="visualizationsContainer" style="display: none;">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label for="vizType" class="form-label">Visualization Type:</label>
                                    <select id="vizType" class="form-select">
                                        <option value="dependency">Dependency Analysis</option>
                                        <option value="call_graph">Call Graph</option>
                                        <option value="blast_radius">Blast Radius</option>
                                        <option value="complexity_heatmap">Complexity Heatmap</option>
                                        <option value="class_relationships">Class Relationships</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label for="vizTarget" class="form-label">Target (optional):</label>
                                    <input type="text" id="vizTarget" class="form-control" placeholder="Function/Class name">
                                </div>
                            </div>
                            <div class="visualization-container">
                                <div id="visualizationPlot"></div>
                            </div>
                        </div>
                        <div id="visualizationsPlaceholder">
                            <p class="text-muted text-center py-4">
                                Click "Load Visualizations" to display interactive codebase visualizations
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-lightbulb"></i> Recommendations</h5>
                    </div>
                    <div class="card-body">
                        {self._generate_recommendations_html(analysis_report.recommendations)}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Load analysis data
        const analysisData = {json.dumps(analysis_report.__dict__, default=str, indent=2)};
        
        // Initialize charts
        document.addEventListener('DOMContentLoaded', function() {{
            initializeSeverityChart({json.dumps(issues_by_severity)});
            initializeTypeChart({json.dumps(issues_by_type)});
            initializeFilters();
            initializeVisualizations();
        }});
        
        function initializeSeverityChart(data) {{
            const ctx = document.getElementById('severityChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(data),
                    datasets: [{{
                        data: Object.values(data),
                        backgroundColor: [
                            '#dc3545', // critical
                            '#fd7e14', // high
                            '#ffc107', // medium
                            '#28a745', // low
                            '#6c757d'  // info
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}
        
        function initializeTypeChart(data) {{
            const ctx = document.getElementById('typeChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: Object.keys(data),
                    datasets: [{{
                        data: Object.values(data),
                        backgroundColor: '#667eea'
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        }}
        
        function initializeFilters() {{
            const severityFilter = document.getElementById('severityFilter');
            const typeFilter = document.getElementById('typeFilter');
            
            function filterIssues() {{
                const severity = severityFilter.value;
                const type = typeFilter.value;
                const issues = document.querySelectorAll('.issue-item');
                
                issues.forEach(issue => {{
                    const issueSeverity = issue.dataset.severity;
                    const issueType = issue.dataset.type;
                    
                    const showSeverity = !severity || issueSeverity === severity;
                    const showType = !type || issueType === type;
                    
                    issue.style.display = (showSeverity && showType) ? 'block' : 'none';
                }});
            }}
            
            severityFilter.addEventListener('change', filterIssues);
            typeFilter.addEventListener('change', filterIssues);
        }}
        
        function initializeVisualizations() {{
            const loadBtn = document.getElementById('loadVisualizationsBtn');
            const container = document.getElementById('visualizationsContainer');
            const placeholder = document.getElementById('visualizationsPlaceholder');
            const vizType = document.getElementById('vizType');
            const vizTarget = document.getElementById('vizTarget');
            
            loadBtn.addEventListener('click', function() {{
                container.style.display = 'block';
                placeholder.style.display = 'none';
                loadBtn.textContent = 'Visualizations Loaded';
                loadBtn.disabled = true;
                
                // Load initial visualization
                loadVisualization();
            }});
            
            vizType.addEventListener('change', loadVisualization);
            vizTarget.addEventListener('input', debounce(loadVisualization, 500));
            
            function loadVisualization() {{
                const type = vizType.value;
                const target = vizTarget.value;
                
                // This would normally make an API call to get visualization data
                // For now, we'll show a placeholder
                const plotDiv = document.getElementById('visualizationPlot');
                plotDiv.innerHTML = `
                    <div class="text-center py-4">
                        <i class="fas fa-chart-network fa-3x text-muted mb-3"></i>
                        <h5>${{type.replace('_', ' ').toUpperCase()}} Visualization</h5>
                        <p class="text-muted">Target: ${{target || 'All components'}}</p>
                        <small class="text-muted">Interactive visualization would be rendered here</small>
                    </div>
                `;
            }}
            
            function debounce(func, wait) {{
                let timeout;
                return function executedFunction(...args) {{
                    const later = () => {{
                        clearTimeout(timeout);
                        func(...args);
                    }};
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                }};
            }}
        }}
    </script>
</body>
</html>
        """
        
        return html_content
    
    def _generate_issues_html(self, issues: List[Dict[str, Any]]) -> str:
        """Generate HTML for issues list."""
        if not issues:
            return '<p class="text-muted">No issues detected. Great job!</p>'
        
        html_parts = []
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            issue_type = issue.get('type', 'unknown')
            
            html_parts.append(f"""
            <div class="issue-item issue-{severity}" data-severity="{severity}" data-type="{issue_type}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">{issue.get('title', 'Unknown Issue')}</h6>
                        <p class="mb-1 text-muted">{issue.get('description', '')}</p>
                        {f'<small class="text-muted">File: {issue.get("file_path", "Unknown")}</small>' if issue.get('file_path') else ''}
                        {f'<small class="text-muted"> | Line: {issue.get("line_number")}</small>' if issue.get('line_number') else ''}
                        {f'<div class="mt-2"><strong>Suggestion:</strong> {issue.get("suggestion", "")}</div>' if issue.get('suggestion') else ''}
                    </div>
                    <div class="text-end">
                        <span class="badge bg-{self._get_severity_color(severity)}">{severity.upper()}</span>
                        <br>
                        <small class="text-muted">{issue_type}</small>
                    </div>
                </div>
            </div>
            """)
        
        return ''.join(html_parts)
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations."""
        if not recommendations:
            return '<p class="text-muted">No specific recommendations at this time.</p>'
        
        html_parts = ['<ul class="list-group list-group-flush">']
        for rec in recommendations:
            html_parts.append(f'<li class="list-group-item"><i class="fas fa-arrow-right text-primary me-2"></i>{rec}</li>')
        html_parts.append('</ul>')
        
        return ''.join(html_parts)
    
    def _get_health_class(self, score: float) -> str:
        """Get CSS class for health score."""
        if score >= 80:
            return 'health-excellent'
        elif score >= 60:
            return 'health-good'
        elif score >= 40:
            return 'health-poor'
        else:
            return 'health-critical'
    
    def _get_dominant_severity(self, issues_by_severity: Dict[str, int]) -> str:
        """Get the most common severity level."""
        if not issues_by_severity:
            return 'low'
        
        return max(issues_by_severity.items(), key=lambda x: x[1])[0]
    
    def _get_severity_color(self, severity: str) -> str:
        """Get Bootstrap color class for severity."""
        color_map = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'success',
            'info': 'secondary'
        }
        return color_map.get(severity, 'secondary')
    
    def _generate_data_files(self, analysis_report: AnalysisReport, output_path: Path):
        """Generate supporting data files."""
        # Save analysis data as JSON for potential API access
        data_file = output_path / "analysis_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_report.__dict__, f, indent=2, default=str)
    
    def _copy_static_files(self, output_path: Path):
        """Copy static files (CSS, JS, images) to output directory."""
        # For now, we're using CDN resources, so no static files to copy
        # In a full implementation, you might want to copy local assets
        pass
    
    def generate_standalone_report(self, analysis_report: AnalysisReport) -> str:
        """Generate a standalone HTML report (simpler version)."""
        return self._generate_main_dashboard(analysis_report)

