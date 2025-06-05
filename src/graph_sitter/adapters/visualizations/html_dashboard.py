"""
HTML Dashboard Generator for Comprehensive Analysis Results.

This module generates interactive HTML dashboards that display analysis results,
issues, and provide entry points to the React visualization components.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from ..analysis.comprehensive_analysis import ComprehensiveAnalysisResult, IssueItem

logger = logging.getLogger(__name__)


class HTMLDashboardGenerator:
    """Generates HTML dashboards for analysis results."""
    
    def __init__(self, analysis_result: ComprehensiveAnalysisResult):
        """
        Initialize dashboard generator.
        
        Args:
            analysis_result: The comprehensive analysis result to display
        """
        self.analysis_result = analysis_result
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_dashboard(self, output_path: str = "analysis_dashboard.html") -> str:
        """
        Generate complete HTML dashboard.
        
        Args:
            output_path: Path where to save the HTML file
            
        Returns:
            Path to the generated HTML file
        """
        html_content = self._generate_html_content()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML dashboard generated: {output_file}")
        return str(output_file)
    
    def _generate_html_content(self) -> str:
        """Generate the complete HTML content."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Dashboard - {self.analysis_result.codebase_name}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="dashboard-container">
        {self._generate_header()}
        {self._generate_summary_section()}
        {self._generate_issues_section()}
        {self._generate_visualization_section()}
        {self._generate_details_section()}
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
    
    def _generate_header(self) -> str:
        """Generate the dashboard header."""
        return f"""
        <header class="dashboard-header">
            <div class="header-content">
                <h1>🔍 Codebase Analysis Dashboard</h1>
                <div class="codebase-info">
                    <h2>{self.analysis_result.codebase_name}</h2>
                    <div class="analysis-meta">
                        <span class="timestamp">📅 {self.analysis_result.analysis_summary.analysis_timestamp[:19]}</span>
                        <span class="duration">⏱️ {self.analysis_result.analysis_summary.analysis_duration:.2f}s</span>
                        <span class="health-score health-score-{self._get_health_score_class()}">
                            💚 Health Score: {self.analysis_result.analysis_summary.health_score:.1f}/100
                        </span>
                    </div>
                </div>
            </div>
        </header>"""
    
    def _generate_summary_section(self) -> str:
        """Generate the summary statistics section."""
        summary = self.analysis_result.analysis_summary
        return f"""
        <section class="summary-section">
            <h3>📊 Analysis Summary</h3>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-number">{summary.total_files}</div>
                    <div class="summary-label">Files Analyzed</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{summary.total_functions}</div>
                    <div class="summary-label">Functions</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{summary.total_classes}</div>
                    <div class="summary-label">Classes</div>
                </div>
                <div class="summary-card issues-card">
                    <div class="summary-number">{summary.total_issues}</div>
                    <div class="summary-label">Total Issues</div>
                </div>
            </div>
            
            <div class="issues-breakdown">
                <h4>Issues by Severity</h4>
                <div class="severity-grid">
                    <div class="severity-item critical">
                        <span class="severity-count">{summary.critical_issues}</span>
                        <span class="severity-label">Critical</span>
                    </div>
                    <div class="severity-item high">
                        <span class="severity-count">{summary.high_issues}</span>
                        <span class="severity-label">High</span>
                    </div>
                    <div class="severity-item medium">
                        <span class="severity-count">{summary.medium_issues}</span>
                        <span class="severity-label">Medium</span>
                    </div>
                    <div class="severity-item low">
                        <span class="severity-count">{summary.low_issues}</span>
                        <span class="severity-label">Low</span>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _generate_issues_section(self) -> str:
        """Generate the issues listing section."""
        return f"""
        <section class="issues-section">
            <div class="section-header">
                <h3>🚨 Issues & Findings</h3>
                <div class="filter-controls">
                    <select id="severityFilter" onchange="filterIssues()">
                        <option value="all">All Severities</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                    <select id="categoryFilter" onchange="filterIssues()">
                        <option value="all">All Categories</option>
                        <option value="error">Errors</option>
                        <option value="warning">Warnings</option>
                        <option value="suggestion">Suggestions</option>
                        <option value="security">Security</option>
                        <option value="performance">Performance</option>
                    </select>
                </div>
            </div>
            
            <div class="issues-list" id="issuesList">
                {self._generate_issues_list()}
            </div>
        </section>"""
    
    def _generate_issues_list(self) -> str:
        """Generate the list of issues."""
        if not self.analysis_result.issues:
            return '<div class="no-issues">🎉 No issues found! Your codebase looks great!</div>'
        
        issues_html = []
        for issue in self.analysis_result.issues:
            issues_html.append(self._generate_issue_item(issue))
        
        return '\\n'.join(issues_html)
    
    def _generate_issue_item(self, issue: IssueItem) -> str:
        """Generate HTML for a single issue item."""
        location_info = []
        if issue.file_path:
            location_info.append(f"📁 {issue.file_path}")
        if issue.line_number:
            location_info.append(f"📍 Line {issue.line_number}")
        if issue.function_name:
            location_info.append(f"🔧 {issue.function_name}()")
        if issue.class_name:
            location_info.append(f"🏗️ {issue.class_name}")
        
        location_str = " • ".join(location_info) if location_info else ""
        
        fix_suggestion = ""
        if issue.fix_suggestion:
            fix_suggestion = f'<div class="fix-suggestion">💡 <strong>Suggestion:</strong> {issue.fix_suggestion}</div>'
        
        return f"""
        <div class="issue-item" data-severity="{issue.severity}" data-category="{issue.category}">
            <div class="issue-header">
                <span class="severity-badge {issue.severity}">{issue.severity.upper()}</span>
                <span class="category-badge {issue.category}">{issue.category.upper()}</span>
                <h4 class="issue-title">{issue.title}</h4>
            </div>
            <div class="issue-description">{issue.description}</div>
            {f'<div class="issue-location">{location_str}</div>' if location_str else ''}
            {fix_suggestion}
        </div>"""
    
    def _generate_visualization_section(self) -> str:
        """Generate the visualization controls section."""
        return f"""
        <section class="visualization-section">
            <div class="section-header">
                <h3>📈 Interactive Visualizations</h3>
                <button class="visualize-btn" onclick="loadVisualizationDashboard()">
                    🚀 Launch Interactive Dashboard
                </button>
            </div>
            
            <div class="visualization-preview">
                <div class="viz-options">
                    <h4>Available Visualizations:</h4>
                    <div class="viz-grid">
                        <div class="viz-option" onclick="loadVisualization('dependency')">
                            <div class="viz-icon">🔗</div>
                            <div class="viz-title">Dependency Analysis</div>
                            <div class="viz-description">Explore module dependencies and relationships</div>
                        </div>
                        <div class="viz-option" onclick="loadVisualization('callgraph')">
                            <div class="viz-icon">📞</div>
                            <div class="viz-title">Call Graph</div>
                            <div class="viz-description">Visualize function call relationships</div>
                        </div>
                        <div class="viz-option" onclick="loadVisualization('complexity')">
                            <div class="viz-icon">🌡️</div>
                            <div class="viz-title">Complexity Heatmap</div>
                            <div class="viz-description">View code complexity across files</div>
                        </div>
                        <div class="viz-option" onclick="loadVisualization('blast-radius')">
                            <div class="viz-icon">💥</div>
                            <div class="viz-title">Blast Radius</div>
                            <div class="viz-description">Analyze impact of changes</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="visualizationContainer" class="visualization-container" style="display: none;">
                <div class="viz-controls">
                    <select id="vizType">
                        <option value="dependency">Dependency Analysis</option>
                        <option value="callgraph">Call Graph</option>
                        <option value="complexity">Complexity Heatmap</option>
                        <option value="blast-radius">Blast Radius</option>
                    </select>
                    <select id="vizTarget">
                        <option value="">Select Target...</option>
                        {self._generate_target_options()}
                    </select>
                    <button onclick="updateVisualization()">Update Visualization</button>
                </div>
                <div id="vizContent" class="viz-content">
                    <!-- Visualization content will be loaded here -->
                </div>
            </div>
        </section>"""
    
    def _generate_target_options(self) -> str:
        """Generate options for visualization targets."""
        options = []
        
        # Add function options
        if hasattr(self.analysis_result, 'function_contexts'):
            for context in self.analysis_result.function_contexts[:20]:  # Limit for performance
                options.append(f'<option value="function:{context.function_name}">Function: {context.function_name}</option>')
        
        # Add class options (if available)
        # This would need to be populated from the codebase analysis
        
        # Add file options for blast radius
        if hasattr(self.analysis_result.enhanced_analysis, 'file_analysis'):
            for file_path in list(getattr(self.analysis_result.enhanced_analysis, 'file_analysis', {}).keys())[:10]:
                options.append(f'<option value="file:{file_path}">File: {file_path}</option>')
        
        return '\\n'.join(options)
    
    def _generate_details_section(self) -> str:
        """Generate the detailed analysis section."""
        return f"""
        <section class="details-section">
            <h3>📋 Detailed Analysis</h3>
            <div class="details-tabs">
                <button class="tab-button active" onclick="showTab('metrics')">Metrics</button>
                <button class="tab-button" onclick="showTab('dependencies')">Dependencies</button>
                <button class="tab-button" onclick="showTab('functions')">Functions</button>
                <button class="tab-button" onclick="showTab('raw-data')">Raw Data</button>
            </div>
            
            <div id="metricsTab" class="tab-content active">
                {self._generate_metrics_content()}
            </div>
            
            <div id="dependenciesTab" class="tab-content">
                {self._generate_dependencies_content()}
            </div>
            
            <div id="functionsTab" class="tab-content">
                {self._generate_functions_content()}
            </div>
            
            <div id="raw-dataTab" class="tab-content">
                <pre class="raw-data">{json.dumps(self.analysis_result.to_dict(), indent=2, default=str)[:5000]}...</pre>
            </div>
        </section>"""
    
    def _generate_metrics_content(self) -> str:
        """Generate metrics content."""
        if not self.analysis_result.metrics:
            return "<p>No metrics data available.</p>"
        
        return f"""
        <div class="metrics-content">
            <h4>Codebase Metrics</h4>
            <div class="metrics-grid">
                <!-- Metrics will be populated from the analysis result -->
                <div class="metric-item">
                    <span class="metric-label">Average Complexity:</span>
                    <span class="metric-value">{getattr(self.analysis_result.metrics, 'average_complexity', 'N/A')}</span>
                </div>
                <!-- Add more metrics as needed -->
            </div>
        </div>"""
    
    def _generate_dependencies_content(self) -> str:
        """Generate dependencies content."""
        if not self.analysis_result.dependency_analysis:
            return "<p>No dependency data available.</p>"
        
        return """
        <div class="dependencies-content">
            <h4>Dependency Analysis</h4>
            <p>Dependency analysis results will be displayed here.</p>
        </div>"""
    
    def _generate_functions_content(self) -> str:
        """Generate functions content."""
        if not self.analysis_result.function_contexts:
            return "<p>No function context data available.</p>"
        
        functions_html = []
        for context in self.analysis_result.function_contexts[:10]:  # Show first 10
            functions_html.append(f"""
            <div class="function-item">
                <h5>{context.function_name}</h5>
                <p>Function analysis details would go here.</p>
            </div>""")
        
        return f"""
        <div class="functions-content">
            <h4>Function Analysis</h4>
            <div class="functions-list">
                {''.join(functions_html)}
            </div>
        </div>"""
    
    def _get_health_score_class(self) -> str:
        """Get CSS class for health score."""
        score = self.analysis_result.analysis_summary.health_score
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the dashboard."""
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
            background-color: #f5f7fa;
        }
        
        .dashboard-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header-content h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header-content h2 {
            font-size: 1.8em;
            margin-bottom: 15px;
            opacity: 0.9;
        }
        
        .analysis-meta {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .analysis-meta span {
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .health-score.excellent { background: rgba(76, 175, 80, 0.3) !important; }
        .health-score.good { background: rgba(255, 193, 7, 0.3) !important; }
        .health-score.fair { background: rgba(255, 152, 0, 0.3) !important; }
        .health-score.poor { background: rgba(244, 67, 54, 0.3) !important; }
        
        section {
            background: white;
            margin-bottom: 30px;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        section h3 {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #2c3e50;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            text-align: center;
            padding: 25px;
            border-radius: 8px;
            background: #f8f9fa;
            border: 2px solid #e9ecef;
        }
        
        .summary-card.issues-card {
            border-color: #ffc107;
            background: #fff3cd;
        }
        
        .summary-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .summary-label {
            font-size: 1.1em;
            color: #6c757d;
            margin-top: 5px;
        }
        
        .severity-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }
        
        .severity-item {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            color: white;
        }
        
        .severity-item.critical { background: #dc3545; }
        .severity-item.high { background: #fd7e14; }
        .severity-item.medium { background: #ffc107; color: #333; }
        .severity-item.low { background: #28a745; }
        
        .severity-count {
            display: block;
            font-size: 1.8em;
            font-weight: bold;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .filter-controls {
            display: flex;
            gap: 10px;
        }
        
        .filter-controls select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }
        
        .issues-list {
            max-height: 600px;
            overflow-y: auto;
        }
        
        .issue-item {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            background: white;
        }
        
        .issue-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .severity-badge, .category-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .severity-badge.critical { background: #dc3545; color: white; }
        .severity-badge.high { background: #fd7e14; color: white; }
        .severity-badge.medium { background: #ffc107; color: #333; }
        .severity-badge.low { background: #28a745; color: white; }
        
        .category-badge.error { background: #dc3545; color: white; }
        .category-badge.warning { background: #ffc107; color: #333; }
        .category-badge.suggestion { background: #17a2b8; color: white; }
        .category-badge.security { background: #6f42c1; color: white; }
        .category-badge.performance { background: #fd7e14; color: white; }
        
        .issue-title {
            flex: 1;
            font-size: 1.1em;
            color: #2c3e50;
        }
        
        .issue-description {
            color: #6c757d;
            margin-bottom: 10px;
        }
        
        .issue-location {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 10px;
        }
        
        .fix-suggestion {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 4px;
            padding: 10px;
            font-size: 0.9em;
        }
        
        .visualize-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .visualize-btn:hover {
            transform: translateY(-2px);
        }
        
        .viz-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .viz-option {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .viz-option:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .viz-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .viz-title {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .viz-description {
            font-size: 0.9em;
            color: #6c757d;
        }
        
        .details-tabs {
            display: flex;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 20px;
        }
        
        .tab-button {
            background: none;
            border: none;
            padding: 12px 24px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        
        .tab-button.active {
            border-bottom-color: #667eea;
            color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .raw-data {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.9em;
        }
        
        .no-issues {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            color: #28a745;
        }
        
        @media (max-width: 768px) {
            .dashboard-container {
                padding: 10px;
            }
            
            .analysis-meta {
                flex-direction: column;
                gap: 10px;
            }
            
            .section-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }
            
            .filter-controls {
                width: 100%;
            }
            
            .filter-controls select {
                flex: 1;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for dashboard interactivity."""
        return f"""
        // Dashboard JavaScript functionality
        
        function filterIssues() {{
            const severityFilter = document.getElementById('severityFilter').value;
            const categoryFilter = document.getElementById('categoryFilter').value;
            const issues = document.querySelectorAll('.issue-item');
            
            issues.forEach(issue => {{
                const severity = issue.dataset.severity;
                const category = issue.dataset.category;
                
                const severityMatch = severityFilter === 'all' || severity === severityFilter;
                const categoryMatch = categoryFilter === 'all' || category === categoryFilter;
                
                if (severityMatch && categoryMatch) {{
                    issue.style.display = 'block';
                }} else {{
                    issue.style.display = 'none';
                }}
            }});
        }}
        
        function showTab(tabName) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(button => {{
                button.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }}
        
        function loadVisualization(type) {{
            const container = document.getElementById('visualizationContainer');
            const vizType = document.getElementById('vizType');
            
            vizType.value = type;
            container.style.display = 'block';
            container.scrollIntoView({{ behavior: 'smooth' }});
            
            updateVisualization();
        }}
        
        function updateVisualization() {{
            const vizType = document.getElementById('vizType').value;
            const vizTarget = document.getElementById('vizTarget').value;
            const content = document.getElementById('vizContent');
            
            // This would normally load actual visualization content
            content.innerHTML = `
                <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 8px;">
                    <h4>Loading ${{vizType}} visualization...</h4>
                    <p>Target: ${{vizTarget || 'All'}}</p>
                    <p style="margin-top: 20px; color: #6c757d;">
                        Interactive React dashboard will be loaded here.
                    </p>
                </div>
            `;
        }}
        
        function loadVisualizationDashboard() {{
            // This would open the full React dashboard
            const url = '/dashboard/{quote(self.analysis_result.codebase_id)}';
            
            // For now, show a placeholder
            alert('Interactive React dashboard would open at: ' + url);
            
            // In a real implementation, this would:
            // window.open(url, '_blank');
        }}
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Analysis Dashboard loaded');
            console.log('Analysis data:', {json.dumps({"total_issues": len(self.analysis_result.issues), "health_score": self.analysis_result.analysis_summary.health_score})});
        }});
        """


def generate_html_dashboard(analysis_result: ComprehensiveAnalysisResult, 
                          output_path: str = "analysis_dashboard.html") -> str:
    """
    Convenience function to generate HTML dashboard.
    
    Args:
        analysis_result: The comprehensive analysis result
        output_path: Path where to save the HTML file
        
    Returns:
        Path to the generated HTML file
    """
    generator = HTMLDashboardGenerator(analysis_result)
    return generator.generate_dashboard(output_path)

