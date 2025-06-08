#!/usr/bin/env python3
"""
📊 DASHBOARDS MODULE 📊

Comprehensive dashboard components for codebase analysis visualization.
Provides real-time project state monitoring and code quality insights.

Features:
- MetricsDashboard: Code quality metrics and trends
- QualityDashboard: Code quality assessment and scoring
- PerformanceDashboard: Performance metrics and bottlenecks
- Comprehensive dashboard creation utilities
"""

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """Configuration for dashboard generation."""
    title: str = "Codebase Dashboard"
    theme: str = "default"  # default, dark, light, professional
    refresh_interval: int = 30  # seconds
    show_trends: bool = True
    show_alerts: bool = True
    real_time: bool = True
    export_enabled: bool = True

@dataclass
class MetricData:
    """Represents a metric with value, trend, and metadata."""
    name: str
    value: Union[int, float, str]
    unit: str = ""
    trend: Optional[float] = None  # percentage change
    status: str = "normal"  # normal, warning, critical
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

class MetricsDashboard:
    """
    Dashboard for displaying code quality metrics and trends.
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize the metrics dashboard."""
        self.config = config or DashboardConfig(title="Code Quality Metrics")
        self.metrics: List[MetricData] = []
        self.historical_data: Dict[str, List[MetricData]] = {}
    
    def add_metric(self, metric: MetricData) -> None:
        """Add a metric to the dashboard."""
        self.metrics.append(metric)
        
        # Store historical data
        if metric.name not in self.historical_data:
            self.historical_data[metric.name] = []
        self.historical_data[metric.name].append(metric)
    
    def add_code_quality_metrics(self, analysis_results: Dict[str, Any]) -> None:
        """Add standard code quality metrics from analysis results."""
        # Lines of code
        if 'total_lines' in analysis_results:
            self.add_metric(MetricData(
                name="Total Lines of Code",
                value=analysis_results['total_lines'],
                unit="lines",
                description="Total lines of code in the project"
            ))
        
        # Complexity metrics
        if 'complexity' in analysis_results:
            complexity = analysis_results['complexity']
            self.add_metric(MetricData(
                name="Cyclomatic Complexity",
                value=complexity.get('average', 0),
                unit="avg",
                status="warning" if complexity.get('average', 0) > 10 else "normal",
                description="Average cyclomatic complexity per function"
            ))
        
        # Test coverage
        if 'test_coverage' in analysis_results:
            coverage = analysis_results['test_coverage']
            self.add_metric(MetricData(
                name="Test Coverage",
                value=coverage,
                unit="%",
                status="critical" if coverage < 50 else "warning" if coverage < 80 else "normal",
                description="Percentage of code covered by tests"
            ))
        
        # Technical debt
        if 'technical_debt' in analysis_results:
            debt = analysis_results['technical_debt']
            self.add_metric(MetricData(
                name="Technical Debt",
                value=debt.get('hours', 0),
                unit="hours",
                status="critical" if debt.get('hours', 0) > 100 else "warning" if debt.get('hours', 0) > 50 else "normal",
                description="Estimated hours to fix technical debt"
            ))
    
    def generate_html(self) -> str:
        """Generate HTML for the metrics dashboard."""
        html = f"""
        <div class="metrics-dashboard" data-config='{json.dumps(self.config.__dict__)}'>
            <div class="dashboard-header">
                <h2><i class="fas fa-chart-line"></i> {self.config.title}</h2>
                <div class="dashboard-controls">
                    <button class="btn btn-sm btn-outline-primary" onclick="refreshDashboard()">
                        <i class="fas fa-sync"></i> Refresh
                    </button>
                    {('<button class="btn btn-sm btn-outline-secondary" onclick="exportDashboard()"><i class="fas fa-download"></i> Export</button>' if self.config.export_enabled else '')}
                </div>
            </div>
            
            <div class="metrics-grid">
        """
        
        for metric in self.metrics:
            status_class = f"metric-{metric.status}"
            trend_icon = ""
            if metric.trend is not None:
                if metric.trend > 0:
                    trend_icon = '<i class="fas fa-arrow-up text-success"></i>'
                elif metric.trend < 0:
                    trend_icon = '<i class="fas fa-arrow-down text-danger"></i>'
                else:
                    trend_icon = '<i class="fas fa-minus text-muted"></i>'
            
            html += f"""
                <div class="metric-card {status_class}">
                    <div class="metric-header">
                        <h4>{metric.name}</h4>
                        {trend_icon}
                    </div>
                    <div class="metric-value">
                        <span class="value">{metric.value}</span>
                        <span class="unit">{metric.unit}</span>
                    </div>
                    {f'<div class="metric-trend">Trend: {metric.trend:+.1f}%</div>' if metric.trend is not None else ''}
                    <div class="metric-description">{metric.description}</div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html

class QualityDashboard:
    """
    Dashboard for code quality assessment and scoring.
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize the quality dashboard."""
        self.config = config or DashboardConfig(title="Code Quality Assessment")
        self.quality_scores: Dict[str, float] = {}
        self.quality_issues: List[Dict[str, Any]] = []
        self.quality_trends: Dict[str, List[float]] = {}
    
    def add_quality_score(self, category: str, score: float, max_score: float = 100) -> None:
        """Add a quality score for a specific category."""
        normalized_score = (score / max_score) * 100
        self.quality_scores[category] = normalized_score
    
    def add_quality_issue(self, issue: Dict[str, Any]) -> None:
        """Add a quality issue to track."""
        required_fields = ['file', 'line', 'severity', 'message', 'rule']
        if all(field in issue for field in required_fields):
            self.quality_issues.append(issue)
        else:
            logger.warning(f"Quality issue missing required fields: {issue}")
    
    def calculate_overall_score(self) -> float:
        """Calculate overall quality score."""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores.values()) / len(self.quality_scores)
    
    def generate_html(self) -> str:
        """Generate HTML for the quality dashboard."""
        overall_score = self.calculate_overall_score()
        score_class = "score-excellent" if overall_score >= 90 else "score-good" if overall_score >= 70 else "score-poor"
        
        html = f"""
        <div class="quality-dashboard">
            <div class="dashboard-header">
                <h2><i class="fas fa-shield-alt"></i> {self.config.title}</h2>
            </div>
            
            <div class="overall-score {score_class}">
                <div class="score-circle">
                    <span class="score-value">{overall_score:.1f}</span>
                    <span class="score-label">Overall Score</span>
                </div>
            </div>
            
            <div class="quality-categories">
        """
        
        for category, score in self.quality_scores.items():
            score_class = "score-excellent" if score >= 90 else "score-good" if score >= 70 else "score-poor"
            html += f"""
                <div class="quality-category {score_class}">
                    <h4>{category.replace('_', ' ').title()}</h4>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score}%"></div>
                    </div>
                    <span class="score-text">{score:.1f}%</span>
                </div>
            """
        
        html += """
            </div>
            
            <div class="quality-issues">
                <h3>Recent Issues</h3>
                <div class="issues-list">
        """
        
        # Show top 10 most recent issues
        recent_issues = sorted(self.quality_issues, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        for issue in recent_issues:
            severity_class = f"severity-{issue['severity'].lower()}"
            html += f"""
                <div class="quality-issue {severity_class}">
                    <div class="issue-header">
                        <span class="issue-file">{issue['file']}</span>
                        <span class="issue-line">Line {issue['line']}</span>
                        <span class="issue-severity">{issue['severity']}</span>
                    </div>
                    <div class="issue-message">{issue['message']}</div>
                    <div class="issue-rule">{issue['rule']}</div>
                </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html

class PerformanceDashboard:
    """
    Dashboard for performance metrics and bottlenecks.
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize the performance dashboard."""
        self.config = config or DashboardConfig(title="Performance Metrics")
        self.performance_metrics: Dict[str, Any] = {}
        self.bottlenecks: List[Dict[str, Any]] = []
    
    def add_performance_metric(self, name: str, value: float, unit: str = "ms", threshold: Optional[float] = None) -> None:
        """Add a performance metric."""
        status = "normal"
        if threshold and value > threshold:
            status = "warning" if value > threshold * 1.5 else "critical"
        
        self.performance_metrics[name] = {
            'value': value,
            'unit': unit,
            'threshold': threshold,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
    
    def add_bottleneck(self, bottleneck: Dict[str, Any]) -> None:
        """Add a performance bottleneck."""
        required_fields = ['function', 'file', 'execution_time', 'calls']
        if all(field in bottleneck for field in required_fields):
            self.bottlenecks.append(bottleneck)
    
    def generate_html(self) -> str:
        """Generate HTML for the performance dashboard."""
        html = f"""
        <div class="performance-dashboard">
            <div class="dashboard-header">
                <h2><i class="fas fa-tachometer-alt"></i> {self.config.title}</h2>
            </div>
            
            <div class="performance-metrics">
        """
        
        for name, metric in self.performance_metrics.items():
            status_class = f"metric-{metric['status']}"
            html += f"""
                <div class="performance-metric {status_class}">
                    <h4>{name}</h4>
                    <div class="metric-value">
                        <span class="value">{metric['value']:.2f}</span>
                        <span class="unit">{metric['unit']}</span>
                    </div>
                    {f'<div class="threshold">Threshold: {metric["threshold"]:.2f} {metric["unit"]}</div>' if metric['threshold'] else ''}
                </div>
            """
        
        html += """
            </div>
            
            <div class="bottlenecks-section">
                <h3>Performance Bottlenecks</h3>
                <div class="bottlenecks-list">
        """
        
        # Sort bottlenecks by execution time
        sorted_bottlenecks = sorted(self.bottlenecks, key=lambda x: x['execution_time'], reverse=True)[:10]
        for bottleneck in sorted_bottlenecks:
            html += f"""
                <div class="bottleneck-item">
                    <div class="bottleneck-header">
                        <span class="function-name">{bottleneck['function']}</span>
                        <span class="execution-time">{bottleneck['execution_time']:.2f}ms</span>
                    </div>
                    <div class="bottleneck-details">
                        <span class="file-path">{bottleneck['file']}</span>
                        <span class="call-count">{bottleneck['calls']} calls</span>
                    </div>
                </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html

def create_comprehensive_dashboard(
    metrics_data: Optional[Dict[str, Any]] = None,
    quality_data: Optional[Dict[str, Any]] = None,
    performance_data: Optional[Dict[str, Any]] = None,
    config: Optional[DashboardConfig] = None
) -> str:
    """
    Create a comprehensive dashboard combining all dashboard types.
    
    Args:
        metrics_data: Data for metrics dashboard
        quality_data: Data for quality dashboard
        performance_data: Data for performance dashboard
        config: Dashboard configuration
    
    Returns:
        Complete HTML dashboard
    """
    config = config or DashboardConfig(title="Comprehensive Codebase Dashboard")
    
    # Create individual dashboards
    dashboards_html = []
    
    if metrics_data:
        metrics_dashboard = MetricsDashboard(config)
        metrics_dashboard.add_code_quality_metrics(metrics_data)
        dashboards_html.append(metrics_dashboard.generate_html())
    
    if quality_data:
        quality_dashboard = QualityDashboard(config)
        for category, score in quality_data.get('scores', {}).items():
            quality_dashboard.add_quality_score(category, score)
        for issue in quality_data.get('issues', []):
            quality_dashboard.add_quality_issue(issue)
        dashboards_html.append(quality_dashboard.generate_html())
    
    if performance_data:
        performance_dashboard = PerformanceDashboard(config)
        for name, metric in performance_data.get('metrics', {}).items():
            performance_dashboard.add_performance_metric(
                name, metric['value'], metric.get('unit', 'ms'), metric.get('threshold')
            )
        for bottleneck in performance_data.get('bottlenecks', []):
            performance_dashboard.add_bottleneck(bottleneck)
        dashboards_html.append(performance_dashboard.generate_html())
    
    # Combine all dashboards
    combined_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.title}</title>
        
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- Font Awesome -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        
        <style>
            .dashboard-container {{ padding: 20px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
            .metric-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-normal {{ border-left: 4px solid #28a745; }}
            .metric-warning {{ border-left: 4px solid #ffc107; }}
            .metric-critical {{ border-left: 4px solid #dc3545; }}
            .metric-value {{ font-size: 2em; font-weight: bold; }}
            .overall-score {{ text-align: center; margin: 20px 0; }}
            .score-circle {{ display: inline-block; width: 120px; height: 120px; border-radius: 50%; 
                           display: flex; flex-direction: column; justify-content: center; align-items: center; }}
            .score-excellent {{ background: #28a745; color: white; }}
            .score-good {{ background: #ffc107; color: white; }}
            .score-poor {{ background: #dc3545; color: white; }}
            .quality-categories {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .quality-category {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .score-bar {{ width: 100%; height: 10px; background: #e9ecef; border-radius: 5px; overflow: hidden; }}
            .score-fill {{ height: 100%; transition: width 0.3s ease; }}
            .score-excellent .score-fill {{ background: #28a745; }}
            .score-good .score-fill {{ background: #ffc107; }}
            .score-poor .score-fill {{ background: #dc3545; }}
            .quality-issues {{ margin-top: 30px; }}
            .issues-list {{ max-height: 400px; overflow-y: auto; }}
            .quality-issue {{ background: white; margin: 10px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .severity-critical {{ border-left: 4px solid #dc3545; }}
            .severity-warning {{ border-left: 4px solid #ffc107; }}
            .severity-info {{ border-left: 4px solid #17a2b8; }}
            .performance-metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .performance-metric {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .bottlenecks-list {{ max-height: 400px; overflow-y: auto; }}
            .bottleneck-item {{ background: white; margin: 10px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="container-fluid dashboard-container">
            <div class="row">
                <div class="col-12">
                    <h1 class="text-center mb-4">{config.title}</h1>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    {''.join(dashboards_html)}
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JS -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        
        <script>
            function refreshDashboard() {{
                location.reload();
            }}
            
            function exportDashboard() {{
                const content = document.documentElement.outerHTML;
                const blob = new Blob([content], {{ type: 'text/html' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'dashboard.html';
                a.click();
                URL.revokeObjectURL(url);
            }}
            
            // Auto-refresh if enabled
            {f'setInterval(refreshDashboard, {config.refresh_interval * 1000});' if config.real_time else ''}
        </script>
    </body>
    </html>
    """
    
    return combined_html

