"""
Analytics Dashboard for Graph-Sitter Analytics

Provides visualization and reporting capabilities for analysis results:
- Interactive charts and graphs
- Comprehensive reports
- Trend analysis
- Export capabilities
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..core.analysis_result import AnalysisReport, Finding, Severity, FindingType


class AnalyticsDashboard:
    """
    Creates interactive visualizations and reports for analytics results.
    
    Provides comprehensive dashboards with charts, metrics, and insights
    for all analysis types.
    """
    
    def __init__(self):
        self.color_scheme = {
            "critical": "#dc3545",
            "high": "#fd7e14", 
            "medium": "#ffc107",
            "low": "#28a745",
            "info": "#17a2b8"
        }
        
        self.finding_type_colors = {
            FindingType.COMPLEXITY: "#6f42c1",
            FindingType.PERFORMANCE: "#e83e8c",
            FindingType.SECURITY: "#dc3545",
            FindingType.DEAD_CODE: "#6c757d",
            FindingType.DEPENDENCY: "#20c997",
            FindingType.MAINTAINABILITY: "#fd7e14",
            FindingType.BUG_RISK: "#ffc107"
        }
    
    def create_comprehensive_dashboard(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create a comprehensive dashboard with all visualizations."""
        dashboard = {
            "overview": self._create_overview_section(report),
            "severity_analysis": self._create_severity_charts(report),
            "analyzer_breakdown": self._create_analyzer_breakdown(report),
            "file_analysis": self._create_file_analysis(report),
            "trends": self._create_trend_analysis(report),
            "recommendations": self._create_recommendations_section(report),
            "metrics": self._create_metrics_dashboard(report)
        }
        
        return dashboard
    
    def _create_overview_section(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create overview section with key metrics."""
        stats = report.get_summary_stats()
        
        # Key metrics cards
        metrics_cards = [
            {
                "title": "Overall Quality Score",
                "value": f"{report.overall_quality_score:.1f}/100",
                "color": self._get_score_color(report.overall_quality_score),
                "trend": "stable"  # Could be enhanced with historical data
            },
            {
                "title": "Total Issues",
                "value": str(report.total_findings),
                "color": self._get_severity_color_by_count(report.total_findings),
                "breakdown": {
                    "Critical": stats["critical_issues"],
                    "High": stats["high_issues"],
                    "Medium": stats["medium_issues"],
                    "Low": stats["low_issues"]
                }
            },
            {
                "title": "Files Analyzed",
                "value": str(stats["total_files"]),
                "color": self.color_scheme["info"]
            },
            {
                "title": "Lines Analyzed",
                "value": f"{stats['total_lines']:,}",
                "color": self.color_scheme["info"]
            }
        ]
        
        # Create overview chart
        overview_chart = self._create_overview_chart(report)
        
        return {
            "metrics_cards": metrics_cards,
            "overview_chart": overview_chart,
            "execution_summary": {
                "execution_time": f"{report.execution_time:.2f}s",
                "analyzers_run": len(stats["successful_analyzers"]),
                "failed_analyzers": stats["failed_analyzers"]
            }
        }
    
    def _create_severity_charts(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create severity-based analysis charts."""
        stats = report.get_summary_stats()
        
        # Severity distribution pie chart
        severity_data = {
            "Critical": stats["critical_issues"],
            "High": stats["high_issues"], 
            "Medium": stats["medium_issues"],
            "Low": stats["low_issues"]
        }
        
        severity_pie = go.Figure(data=[go.Pie(
            labels=list(severity_data.keys()),
            values=list(severity_data.values()),
            marker_colors=[self.color_scheme[k.lower()] for k in severity_data.keys()],
            hole=0.4
        )])
        
        severity_pie.update_layout(
            title="Issues by Severity",
            showlegend=True,
            height=400
        )
        
        # Severity by analyzer
        analyzer_severity = self._get_analyzer_severity_breakdown(report)
        
        severity_by_analyzer = go.Figure()
        
        for severity in ["Critical", "High", "Medium", "Low"]:
            severity_by_analyzer.add_trace(go.Bar(
                name=severity,
                x=list(analyzer_severity.keys()),
                y=[analyzer_severity[analyzer].get(severity, 0) for analyzer in analyzer_severity.keys()],
                marker_color=self.color_scheme[severity.lower()]
            ))
        
        severity_by_analyzer.update_layout(
            title="Issues by Analyzer and Severity",
            barmode='stack',
            xaxis_title="Analyzer",
            yaxis_title="Number of Issues",
            height=400
        )
        
        return {
            "severity_distribution": severity_pie.to_json(),
            "severity_by_analyzer": severity_by_analyzer.to_json()
        }
    
    def _create_analyzer_breakdown(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create analyzer-specific breakdown."""
        analyzer_data = {}
        
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed":
                analyzer_data[analyzer_name] = {
                    "total_findings": len(result.findings),
                    "quality_score": result.metrics.quality_score or 0,
                    "execution_time": result.metrics.execution_time,
                    "files_analyzed": result.metrics.files_analyzed,
                    "top_findings": [
                        {
                            "title": f.title,
                            "severity": f.severity.value,
                            "file": f.file_path
                        }
                        for f in sorted(result.findings, 
                                      key=lambda x: self._severity_weight(x.severity), 
                                      reverse=True)[:5]
                    ]
                }
        
        # Create analyzer performance chart
        analyzer_performance = go.Figure()
        
        analyzers = list(analyzer_data.keys())
        scores = [analyzer_data[a]["quality_score"] for a in analyzers]
        findings = [analyzer_data[a]["total_findings"] for a in analyzers]
        
        analyzer_performance.add_trace(go.Scatter(
            x=analyzers,
            y=scores,
            mode='markers+lines',
            name='Quality Score',
            yaxis='y',
            marker=dict(size=10, color=self.color_scheme["info"])
        ))
        
        analyzer_performance.add_trace(go.Bar(
            x=analyzers,
            y=findings,
            name='Total Findings',
            yaxis='y2',
            marker_color=self.color_scheme["medium"],
            opacity=0.7
        ))
        
        analyzer_performance.update_layout(
            title="Analyzer Performance Overview",
            xaxis_title="Analyzer",
            yaxis=dict(title="Quality Score", side="left"),
            yaxis2=dict(title="Number of Findings", side="right", overlaying="y"),
            height=400
        )
        
        return {
            "analyzer_data": analyzer_data,
            "performance_chart": analyzer_performance.to_json()
        }
    
    def _create_file_analysis(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create file-level analysis."""
        # Group findings by file
        file_findings = {}
        for result in report.analysis_results.values():
            for finding in result.findings:
                file_path = finding.file_path
                if file_path not in file_findings:
                    file_findings[file_path] = []
                file_findings[file_path].append(finding)
        
        # Calculate file risk scores
        file_risks = []
        for file_path, findings in file_findings.items():
            risk_score = sum(self._severity_weight(f.severity) for f in findings)
            file_risks.append({
                "file": Path(file_path).name,
                "full_path": file_path,
                "risk_score": risk_score,
                "finding_count": len(findings),
                "critical_count": len([f for f in findings if f.severity == Severity.CRITICAL]),
                "high_count": len([f for f in findings if f.severity == Severity.HIGH])
            })
        
        # Sort by risk score
        file_risks.sort(key=lambda x: x["risk_score"], reverse=True)
        
        # Create file risk chart (top 20 files)
        top_files = file_risks[:20]
        
        file_risk_chart = go.Figure(data=[go.Bar(
            x=[f["file"] for f in top_files],
            y=[f["risk_score"] for f in top_files],
            marker_color=[self._get_risk_color(f["risk_score"]) for f in top_files],
            text=[f"Issues: {f['finding_count']}" for f in top_files],
            textposition='auto'
        )])
        
        file_risk_chart.update_layout(
            title="Top 20 Files by Risk Score",
            xaxis_title="File",
            yaxis_title="Risk Score",
            height=400,
            xaxis_tickangle=-45
        )
        
        return {
            "file_risks": file_risks[:50],  # Top 50 files
            "risk_chart": file_risk_chart.to_json(),
            "total_files_with_issues": len(file_findings)
        }
    
    def _create_trend_analysis(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create trend analysis (placeholder for historical data)."""
        # This would be enhanced with historical data
        return {
            "message": "Trend analysis requires historical data",
            "current_snapshot": {
                "timestamp": report.timestamp,
                "quality_score": report.overall_quality_score,
                "total_findings": report.total_findings
            }
        }
    
    def _create_recommendations_section(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create recommendations section."""
        # Aggregate recommendations from all analyzers
        all_recommendations = report.recommendations.copy()
        
        for result in report.analysis_results.values():
            all_recommendations.extend(result.recommendations)
        
        # Prioritize recommendations
        prioritized_recommendations = self._prioritize_recommendations(all_recommendations, report)
        
        return {
            "top_recommendations": prioritized_recommendations[:10],
            "total_recommendations": len(all_recommendations),
            "quick_wins": self._identify_quick_wins(report),
            "long_term_improvements": self._identify_long_term_improvements(report)
        }
    
    def _create_metrics_dashboard(self, report: AnalysisReport) -> Dict[str, Any]:
        """Create detailed metrics dashboard."""
        metrics = {}
        
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed":
                analyzer_metrics = {}
                
                # Extract analyzer-specific metrics
                if analyzer_name == "complexity":
                    analyzer_metrics = result.metrics.complexity_metrics
                elif analyzer_name == "performance":
                    analyzer_metrics = result.metrics.performance_metrics
                elif analyzer_name == "security":
                    analyzer_metrics = result.metrics.security_metrics
                elif analyzer_name == "dead_code":
                    analyzer_metrics = result.metrics.dead_code_metrics
                elif analyzer_name == "dependency":
                    analyzer_metrics = result.metrics.dependency_metrics
                
                metrics[analyzer_name] = analyzer_metrics
        
        return metrics
    
    def _create_overview_chart(self, report: AnalysisReport) -> str:
        """Create overview radar chart."""
        # Get quality scores from each analyzer
        analyzer_scores = {}
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed" and result.metrics.quality_score is not None:
                analyzer_scores[analyzer_name] = result.metrics.quality_score
        
        if not analyzer_scores:
            return "{}"
        
        # Create radar chart
        categories = list(analyzer_scores.keys())
        values = list(analyzer_scores.values())
        
        radar_chart = go.Figure()
        
        radar_chart.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Quality Scores',
            line_color=self.color_scheme["info"]
        ))
        
        radar_chart.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Quality Scores by Analyzer",
            height=400
        )
        
        return radar_chart.to_json()
    
    def _get_analyzer_severity_breakdown(self, report: AnalysisReport) -> Dict[str, Dict[str, int]]:
        """Get severity breakdown by analyzer."""
        breakdown = {}
        
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed":
                breakdown[analyzer_name] = {
                    "Critical": result.metrics.critical_issues,
                    "High": result.metrics.high_issues,
                    "Medium": result.metrics.medium_issues,
                    "Low": result.metrics.low_issues
                }
        
        return breakdown
    
    def _severity_weight(self, severity: Severity) -> int:
        """Get numeric weight for severity."""
        weights = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        return weights.get(severity, 0)
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on quality score."""
        if score >= 80:
            return self.color_scheme["low"]
        elif score >= 60:
            return self.color_scheme["medium"]
        elif score >= 40:
            return self.color_scheme["high"]
        else:
            return self.color_scheme["critical"]
    
    def _get_severity_color_by_count(self, count: int) -> str:
        """Get color based on issue count."""
        if count == 0:
            return self.color_scheme["low"]
        elif count <= 5:
            return self.color_scheme["medium"]
        elif count <= 15:
            return self.color_scheme["high"]
        else:
            return self.color_scheme["critical"]
    
    def _get_risk_color(self, risk_score: int) -> str:
        """Get color based on risk score."""
        if risk_score <= 5:
            return self.color_scheme["low"]
        elif risk_score <= 10:
            return self.color_scheme["medium"]
        elif risk_score <= 20:
            return self.color_scheme["high"]
        else:
            return self.color_scheme["critical"]
    
    def _prioritize_recommendations(self, recommendations: List[str], report: AnalysisReport) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on impact and effort."""
        prioritized = []
        
        for i, rec in enumerate(recommendations):
            # Simple prioritization based on keywords
            priority = "medium"
            impact = "medium"
            effort = "medium"
            
            rec_lower = rec.lower()
            
            # High priority items
            if any(word in rec_lower for word in ["critical", "security", "vulnerability", "circular"]):
                priority = "high"
                impact = "high"
            
            # Low effort items
            if any(word in rec_lower for word in ["remove", "delete", "clean", "unused"]):
                effort = "low"
            
            # High effort items
            if any(word in rec_lower for word in ["refactor", "restructure", "redesign", "architecture"]):
                effort = "high"
            
            prioritized.append({
                "recommendation": rec,
                "priority": priority,
                "impact": impact,
                "effort": effort,
                "order": i
            })
        
        # Sort by priority, then impact, then effort
        priority_order = {"high": 3, "medium": 2, "low": 1}
        effort_order = {"low": 3, "medium": 2, "high": 1}  # Lower effort is better
        
        prioritized.sort(key=lambda x: (
            priority_order.get(x["priority"], 0),
            priority_order.get(x["impact"], 0),
            effort_order.get(x["effort"], 0)
        ), reverse=True)
        
        return prioritized
    
    def _identify_quick_wins(self, report: AnalysisReport) -> List[str]:
        """Identify quick win opportunities."""
        quick_wins = []
        
        # Look for dead code findings
        for result in report.analysis_results.values():
            if result.status == "completed":
                dead_code_count = len([f for f in result.findings if f.type == FindingType.DEAD_CODE])
                if dead_code_count > 0:
                    quick_wins.append(f"Remove {dead_code_count} dead code items for immediate cleanup")
        
        # Look for unused imports
        unused_imports = 0
        for result in report.analysis_results.values():
            for finding in result.findings:
                if "unused import" in finding.title.lower():
                    unused_imports += 1
        
        if unused_imports > 0:
            quick_wins.append(f"Clean up {unused_imports} unused imports")
        
        return quick_wins[:5]
    
    def _identify_long_term_improvements(self, report: AnalysisReport) -> List[str]:
        """Identify long-term improvement opportunities."""
        improvements = []
        
        # Look for architectural issues
        for result in report.analysis_results.values():
            if result.status == "completed":
                arch_issues = len([f for f in result.findings if "architecture" in f.description.lower()])
                if arch_issues > 0:
                    improvements.append(f"Address {arch_issues} architectural issues for better maintainability")
        
        # Look for high complexity
        for result in report.analysis_results.values():
            if result.status == "completed":
                complex_issues = len([f for f in result.findings if f.type == FindingType.COMPLEXITY and f.severity in [Severity.HIGH, Severity.CRITICAL]])
                if complex_issues > 0:
                    improvements.append(f"Refactor {complex_issues} highly complex functions")
        
        return improvements[:5]
    
    def export_dashboard(self, dashboard: Dict[str, Any], output_path: str, format: str = "html"):
        """Export dashboard to file."""
        if format.lower() == "html":
            self._export_html_dashboard(dashboard, output_path)
        elif format.lower() == "json":
            self._export_json_dashboard(dashboard, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_html_dashboard(self, dashboard: Dict[str, Any], output_path: str):
        """Export dashboard as HTML."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Graph-Sitter Analytics Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric-card {{ display: inline-block; margin: 10px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .chart-container {{ margin: 20px 0; }}
                h1, h2 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>Graph-Sitter Analytics Dashboard</h1>
            
            <h2>Overview</h2>
            <div id="overview-metrics">
                <!-- Metrics cards would be rendered here -->
            </div>
            
            <div class="chart-container">
                <div id="overview-chart"></div>
            </div>
            
            <h2>Severity Analysis</h2>
            <div class="chart-container">
                <div id="severity-chart"></div>
            </div>
            
            <script>
                // Render charts
                var dashboardData = {json.dumps(dashboard, indent=2)};
                
                // Render overview chart if available
                if (dashboardData.overview && dashboardData.overview.overview_chart) {{
                    Plotly.newPlot('overview-chart', JSON.parse(dashboardData.overview.overview_chart));
                }}
                
                // Render severity charts if available
                if (dashboardData.severity_analysis && dashboardData.severity_analysis.severity_distribution) {{
                    Plotly.newPlot('severity-chart', JSON.parse(dashboardData.severity_analysis.severity_distribution));
                }}
            </script>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _export_json_dashboard(self, dashboard: Dict[str, Any], output_path: str):
        """Export dashboard as JSON."""
        with open(output_path, 'w') as f:
            json.dump(dashboard, f, indent=2, default=str)

