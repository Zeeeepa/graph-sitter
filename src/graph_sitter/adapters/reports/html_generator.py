"""
HTML Report Generator for comprehensive codebase analysis.

This module provides functionality to generate detailed HTML reports with
interactive visualizations, issue listings, and analysis summaries.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict

from graph_sitter.core.analysis import AnalysisResult, AnalysisConfig


class HTMLReportGenerator:
    """
    Generates comprehensive HTML reports from analysis results.
    
    This class creates interactive HTML reports that include:
    - Executive summary of analysis results
    - Detailed issue listings with severity levels
    - Interactive charts and visualizations
    - Code metrics and recommendations
    - Navigation between different analysis types
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the HTML report generator.
        
        Args:
            config: Analysis configuration for report customization
        """
        self.config = config or AnalysisConfig()
        self.template_dir = Path(__file__).parent / "templates"
    
    def generate_report(
        self, 
        results: Dict[str, AnalysisResult], 
        output_dir: str,
        report_title: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive HTML report from analysis results.
        
        Args:
            results: Dictionary of analysis results by type
            output_dir: Directory to save the report
            report_title: Custom title for the report
            
        Returns:
            Path to the generated HTML report
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare report data
        report_data = self._prepare_report_data(results, report_title)
        
        # Generate main report HTML
        report_html = self._generate_main_report_html(report_data)
        
        # Save report
        report_path = os.path.join(output_dir, "analysis_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        # Generate supporting files
        self._generate_supporting_files(output_dir, report_data)
        
        return report_path
    
    def _prepare_report_data(
        self, 
        results: Dict[str, AnalysisResult], 
        report_title: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare data structure for report generation."""
        
        # Aggregate all issues
        all_issues = []
        for result in results.values():
            all_issues.extend(result.issues)
        
        # Categorize issues by severity
        issues_by_severity = {
            'error': [i for i in all_issues if i.get('severity') == 'error'],
            'warning': [i for i in all_issues if i.get('severity') == 'warning'],
            'info': [i for i in all_issues if i.get('severity') == 'info'],
        }
        
        # Aggregate metrics
        all_metrics = {}
        for analysis_type, result in results.items():
            for key, value in result.metrics.items():
                all_metrics[f"{analysis_type}_{key}"] = value
        
        # Aggregate recommendations
        all_recommendations = []
        for result in results.values():
            all_recommendations.extend(result.recommendations)
        
        return {
            'title': report_title or f"Graph-Sitter Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': len(all_issues),
                'error_count': len(issues_by_severity['error']),
                'warning_count': len(issues_by_severity['warning']),
                'info_count': len(issues_by_severity['info']),
                'analysis_types': list(results.keys()),
                'total_recommendations': len(all_recommendations)
            },
            'results': {name: asdict(result) for name, result in results.items()},
            'issues_by_severity': issues_by_severity,
            'all_metrics': all_metrics,
            'recommendations': all_recommendations,
            'analysis_details': results
        }
    
    def _generate_main_report_html(self, report_data: Dict[str, Any]) -> str:
        """Generate the main HTML report content."""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_data['title']}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{report_data['title']}</h1>
            <p class="timestamp">Generated on {datetime.fromisoformat(report_data['timestamp']).strftime('%B %d, %Y at %I:%M %p')}</p>
        </header>
        
        <nav class="report-nav">
            <ul>
                <li><a href="#summary" class="nav-link active">Summary</a></li>
                <li><a href="#issues" class="nav-link">Issues</a></li>
                <li><a href="#metrics" class="nav-link">Metrics</a></li>
                <li><a href="#recommendations" class="nav-link">Recommendations</a></li>
                <li><a href="#visualizations" class="nav-link">Visualizations</a></li>
            </ul>
        </nav>
        
        <main class="report-content">
            {self._generate_summary_section(report_data)}
            {self._generate_issues_section(report_data)}
            {self._generate_metrics_section(report_data)}
            {self._generate_recommendations_section(report_data)}
            {self._generate_visualizations_section(report_data)}
        </main>
        
        <footer class="report-footer">
            <p>Generated by Graph-Sitter Analysis Engine</p>
            <p><a href="#visualizations" onclick="loadVisualizationDashboard()">🎛️ Open Interactive Dashboard</a></p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        return html_content
    
    def _generate_summary_section(self, report_data: Dict[str, Any]) -> str:
        """Generate the summary section of the report."""
        summary = report_data['summary']
        
        return f"""
        <section id="summary" class="report-section">
            <h2>📊 Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Issues</h3>
                    <div class="metric-value">{summary['total_issues']}</div>
                </div>
                <div class="summary-card error">
                    <h3>Errors</h3>
                    <div class="metric-value">{summary['error_count']}</div>
                </div>
                <div class="summary-card warning">
                    <h3>Warnings</h3>
                    <div class="metric-value">{summary['warning_count']}</div>
                </div>
                <div class="summary-card info">
                    <h3>Info</h3>
                    <div class="metric-value">{summary['info_count']}</div>
                </div>
            </div>
            
            <div class="analysis-types">
                <h3>Analysis Types Performed</h3>
                <ul>
                    {' '.join([f'<li class="analysis-type">{analysis_type.replace("_", " ").title()}</li>' for analysis_type in summary['analysis_types']])}
                </ul>
            </div>
        </section>
        """
    
    def _generate_issues_section(self, report_data: Dict[str, Any]) -> str:
        """Generate the issues section of the report."""
        issues_by_severity = report_data['issues_by_severity']
        
        issues_html = """
        <section id="issues" class="report-section">
            <h2>🚨 Issues Found</h2>
            <div class="issues-container">
        """
        
        for severity, issues in issues_by_severity.items():
            if issues:
                issues_html += f"""
                <div class="issues-group {severity}">
                    <h3>{severity.title()} Issues ({len(issues)})</h3>
                    <div class="issues-list">
                """
                
                for issue in issues:
                    issues_html += f"""
                    <div class="issue-item {severity}">
                        <div class="issue-header">
                            <span class="issue-type">{issue.get('type', 'unknown').replace('_', ' ').title()}</span>
                            <span class="issue-severity {severity}">{severity.upper()}</span>
                        </div>
                        <div class="issue-description">{issue.get('description', 'No description available')}</div>
                        <div class="issue-location">
                            <strong>Location:</strong> {issue.get('file', 'unknown')} 
                            {f"(Line: {issue.get('location', 'unknown')})" if issue.get('location') != 'unknown' else ''}
                        </div>
                    </div>
                    """
                
                issues_html += """
                    </div>
                </div>
                """
        
        issues_html += """
            </div>
        </section>
        """
        
        return issues_html
    
    def _generate_metrics_section(self, report_data: Dict[str, Any]) -> str:
        """Generate the metrics section of the report."""
        metrics = report_data['all_metrics']
        
        metrics_html = """
        <section id="metrics" class="report-section">
            <h2>📈 Code Metrics</h2>
            <div class="metrics-grid">
        """
        
        for metric_name, metric_value in metrics.items():
            display_name = metric_name.replace('_', ' ').title()
            metrics_html += f"""
            <div class="metric-card">
                <h4>{display_name}</h4>
                <div class="metric-value">{metric_value}</div>
            </div>
            """
        
        metrics_html += """
            </div>
        </section>
        """
        
        return metrics_html
    
    def _generate_recommendations_section(self, report_data: Dict[str, Any]) -> str:
        """Generate the recommendations section of the report."""
        recommendations = report_data['recommendations']
        
        recommendations_html = """
        <section id="recommendations" class="report-section">
            <h2>💡 Recommendations</h2>
            <div class="recommendations-list">
        """
        
        for i, recommendation in enumerate(recommendations, 1):
            recommendations_html += f"""
            <div class="recommendation-item">
                <div class="recommendation-number">{i}</div>
                <div class="recommendation-text">{recommendation}</div>
            </div>
            """
        
        recommendations_html += """
            </div>
        </section>
        """
        
        return recommendations_html
    
    def _generate_visualizations_section(self, report_data: Dict[str, Any]) -> str:
        """Generate the visualizations section of the report."""
        return """
        <section id="visualizations" class="report-section">
            <h2>📊 Interactive Visualizations</h2>
            <div class="visualization-controls">
                <label for="analysis-type-select">Analysis Type:</label>
                <select id="analysis-type-select" onchange="updateVisualization()">
                    <option value="all">All Analysis Types</option>
                    <option value="call_graph">Call Graph</option>
                    <option value="dead_code">Dead Code</option>
                    <option value="dependencies">Dependencies</option>
                    <option value="metrics">Metrics</option>
                    <option value="function_context">Function Context</option>
                </select>
                
                <label for="visualization-type-select">Visualization Type:</label>
                <select id="visualization-type-select" onchange="updateVisualization()">
                    <option value="issues_by_severity">Issues by Severity</option>
                    <option value="metrics_overview">Metrics Overview</option>
                    <option value="analysis_timeline">Analysis Timeline</option>
                </select>
            </div>
            
            <div id="visualization-container">
                <div id="plotly-chart"></div>
            </div>
            
            <div class="dashboard-link">
                <button onclick="loadVisualizationDashboard()" class="dashboard-btn">
                    🎛️ Open Interactive Dashboard
                </button>
                <p>Click to open the full interactive dashboard with advanced visualization options.</p>
            </div>
        </section>
        """
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .report-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .timestamp {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .report-nav {
            background: #2c3e50;
            padding: 0;
        }
        
        .report-nav ul {
            list-style: none;
            display: flex;
            flex-wrap: wrap;
        }
        
        .report-nav li {
            flex: 1;
        }
        
        .nav-link {
            display: block;
            padding: 1rem;
            color: white;
            text-decoration: none;
            text-align: center;
            transition: background-color 0.3s;
        }
        
        .nav-link:hover, .nav-link.active {
            background-color: #34495e;
        }
        
        .report-content {
            padding: 2rem;
        }
        
        .report-section {
            margin-bottom: 3rem;
        }
        
        .report-section h2 {
            color: #2c3e50;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #ecf0f1;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .summary-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .summary-card.error {
            border-left-color: #e74c3c;
        }
        
        .summary-card.warning {
            border-left-color: #f39c12;
        }
        
        .summary-card.info {
            border-left-color: #2ecc71;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 0.5rem;
        }
        
        .analysis-types ul {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .analysis-type {
            background: #ecf0f1;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .issues-group {
            margin-bottom: 2rem;
        }
        
        .issues-group h3 {
            margin-bottom: 1rem;
            padding: 0.5rem;
            border-radius: 4px;
        }
        
        .issues-group.error h3 {
            background: #fadbd8;
            color: #c0392b;
        }
        
        .issues-group.warning h3 {
            background: #fdeaa7;
            color: #d68910;
        }
        
        .issues-group.info h3 {
            background: #d5f4e6;
            color: #27ae60;
        }
        
        .issue-item {
            background: white;
            border: 1px solid #ecf0f1;
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-left: 4px solid #bdc3c7;
        }
        
        .issue-item.error {
            border-left-color: #e74c3c;
        }
        
        .issue-item.warning {
            border-left-color: #f39c12;
        }
        
        .issue-item.info {
            border-left-color: #2ecc71;
        }
        
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .issue-type {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .issue-severity {
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }
        
        .issue-severity.error {
            background: #e74c3c;
        }
        
        .issue-severity.warning {
            background: #f39c12;
        }
        
        .issue-severity.info {
            background: #2ecc71;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #9b59b6;
        }
        
        .recommendations-list {
            space-y: 1rem;
        }
        
        .recommendation-item {
            display: flex;
            align-items: flex-start;
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        .recommendation-number {
            background: #3498db;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 1rem;
            flex-shrink: 0;
        }
        
        .visualization-controls {
            background: #ecf0f1;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .visualization-controls label {
            font-weight: bold;
        }
        
        .visualization-controls select {
            padding: 0.5rem;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
        }
        
        #visualization-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        
        .dashboard-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1.1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .dashboard-btn:hover {
            transform: translateY(-2px);
        }
        
        .dashboard-link {
            text-align: center;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .report-footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 2rem;
        }
        
        .report-footer a {
            color: #3498db;
            text-decoration: none;
        }
        
        @media (max-width: 768px) {
            .report-nav ul {
                flex-direction: column;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .visualization-controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactive features."""
        return """
        // Navigation functionality
        document.addEventListener('DOMContentLoaded', function() {
            const navLinks = document.querySelectorAll('.nav-link');
            const sections = document.querySelectorAll('.report-section');
            
            navLinks.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    // Update active nav link
                    navLinks.forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Show corresponding section
                    const targetId = this.getAttribute('href').substring(1);
                    sections.forEach(section => {
                        section.style.display = section.id === targetId ? 'block' : 'none';
                    });
                });
            });
            
            // Initialize with summary section
            sections.forEach(section => {
                section.style.display = section.id === 'summary' ? 'block' : 'none';
            });
            
            // Initialize visualization
            updateVisualization();
        });
        
        function updateVisualization() {
            const analysisType = document.getElementById('analysis-type-select').value;
            const visualizationType = document.getElementById('visualization-type-select').value;
            
            // Sample data for demonstration
            let data, layout;
            
            if (visualizationType === 'issues_by_severity') {
                data = [{
                    x: ['Error', 'Warning', 'Info'],
                    y: [5, 12, 8], // These would be populated from actual data
                    type: 'bar',
                    marker: {
                        color: ['#e74c3c', '#f39c12', '#2ecc71']
                    }
                }];
                layout = {
                    title: 'Issues by Severity',
                    xaxis: { title: 'Severity Level' },
                    yaxis: { title: 'Number of Issues' }
                };
            } else if (visualizationType === 'metrics_overview') {
                data = [{
                    labels: ['Functions', 'Classes', 'Lines of Code', 'Complexity'],
                    values: [45, 12, 2500, 150], // These would be populated from actual data
                    type: 'pie'
                }];
                layout = {
                    title: 'Code Metrics Overview'
                };
            } else {
                // Analysis timeline
                data = [{
                    x: ['Call Graph', 'Dead Code', 'Dependencies', 'Metrics', 'Function Context'],
                    y: [2.5, 1.8, 3.2, 1.2, 2.1], // Analysis execution times
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: '#3498db' }
                }];
                layout = {
                    title: 'Analysis Execution Timeline',
                    xaxis: { title: 'Analysis Type' },
                    yaxis: { title: 'Execution Time (seconds)' }
                };
            }
            
            Plotly.newPlot('plotly-chart', data, layout, {responsive: true});
        }
        
        function loadVisualizationDashboard() {
            // This would open the interactive dashboard
            alert('Interactive dashboard would open here. This feature connects to the dashboard module.');
        }
        """
    
    def _generate_supporting_files(self, output_dir: str, report_data: Dict[str, Any]) -> None:
        """Generate supporting files for the report."""
        
        # Generate JSON data file for external tools
        data_file = os.path.join(output_dir, "analysis_data.json")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate CSV file for issues
        issues_csv = os.path.join(output_dir, "issues.csv")
        with open(issues_csv, 'w', encoding='utf-8') as f:
            f.write("Type,Severity,Description,File,Location\\n")
            for severity, issues in report_data['issues_by_severity'].items():
                for issue in issues:
                    f.write(f"{issue.get('type', '')},{severity},{issue.get('description', '').replace(',', ';')},{issue.get('file', '')},{issue.get('location', '')}\\n")
        
        print(f"📄 Supporting files generated in {output_dir}")
        print(f"   - analysis_data.json: Raw analysis data")
        print(f"   - issues.csv: Issues in CSV format")

