"""Comprehensive codebase visualization and interactive reporting."""

import json
import logging
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

from ..analysis.function_context import get_enhanced_function_context, FunctionContext
from ..analysis.enhanced_analysis import EnhancedCodebaseAnalyzer, AnalysisReport

logger = logging.getLogger(__name__)


@dataclass
class VisualizationData:
    """Data structure for codebase visualization."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    clusters: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class InteractiveReport:
    """Interactive report with multiple visualization types."""
    summary: Dict[str, Any]
    function_analysis: List[FunctionContext]
    dependency_graph: VisualizationData
    call_graph: VisualizationData
    complexity_heatmap: Dict[str, Any]
    issue_dashboard: Dict[str, Any]
    recommendations: List[str]
    export_data: Dict[str, Any]


class CodebaseVisualizer:
    """Comprehensive codebase visualization and reporting system."""
    
    def __init__(self, codebase: Codebase, output_dir: str = "codebase_analysis"):
        self.codebase = codebase
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize analyzers
        self.enhanced_analyzer = EnhancedCodebaseAnalyzer(codebase)
        
        # Visualization data
        self.function_contexts: Dict[str, FunctionContext] = {}
        self.analysis_report: Optional[AnalysisReport] = None
    
    def generate_comprehensive_report(self) -> InteractiveReport:
        """Generate comprehensive interactive report."""
        logger.info("Generating comprehensive codebase visualization report")
        
        # Run full analysis
        self.analysis_report = self.enhanced_analyzer.run_full_analysis()
        
        # Analyze function contexts
        self._analyze_function_contexts()
        
        # Generate visualizations
        dependency_graph = self._create_dependency_visualization()
        call_graph = self._create_call_graph_visualization()
        complexity_heatmap = self._create_complexity_heatmap()
        issue_dashboard = self._create_issue_dashboard()
        
        # Generate summary
        summary = self._create_summary()
        
        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations()
        
        # Create export data
        export_data = self._create_export_data()
        
        report = InteractiveReport(
            summary=summary,
            function_analysis=list(self.function_contexts.values()),
            dependency_graph=dependency_graph,
            call_graph=call_graph,
            complexity_heatmap=complexity_heatmap,
            issue_dashboard=issue_dashboard,
            recommendations=recommendations,
            export_data=export_data
        )
        
        # Save report
        self._save_interactive_report(report)
        
        return report
    
    def _analyze_function_contexts(self):
        """Analyze all functions for enhanced context."""
        logger.info("Analyzing function contexts...")
        
        for function in self.codebase.functions:
            try:
                context = get_enhanced_function_context(function)
                self.function_contexts[function.name] = context
            except Exception as e:
                logger.warning(f"Error analyzing function {function.name}: {e}")
    
    def _create_dependency_visualization(self) -> VisualizationData:
        """Create dependency graph visualization data."""
        nodes = []
        edges = []
        clusters = []
        
        # Create nodes for each function
        for func_name, context in self.function_contexts.items():
            node = {
                "id": func_name,
                "label": func_name,
                "type": "function",
                "filepath": context.filepath,
                "complexity": context.complexity_metrics.get("complexity_estimate", 0),
                "usage_count": context.complexity_metrics.get("usage_count", 0),
                "risk_level": context.risk_level,
                "impact_score": context.impact_score,
                "issues_count": len(context.issues),
                "size": min(max(context.complexity_metrics.get("line_count", 10), 10), 100)
            }
            nodes.append(node)
        
        # Create edges for dependencies
        for func_name, context in self.function_contexts.items():
            for dep in context.dependencies:
                if dep.get("name") in self.function_contexts:
                    edge = {
                        "source": func_name,
                        "target": dep["name"],
                        "type": "dependency",
                        "weight": 1
                    }
                    edges.append(edge)
        
        # Create clusters by file
        file_clusters = defaultdict(list)
        for func_name, context in self.function_contexts.items():
            if context.filepath:
                file_clusters[context.filepath].append(func_name)
        
        for filepath, functions in file_clusters.items():
            if len(functions) > 1:
                cluster = {
                    "id": filepath,
                    "label": Path(filepath).name,
                    "nodes": functions,
                    "type": "file"
                }
                clusters.append(cluster)
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            clusters=clusters,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "total_clusters": len(clusters),
                "graph_type": "dependency"
            }
        )
    
    def _create_call_graph_visualization(self) -> VisualizationData:
        """Create call graph visualization data."""
        nodes = []
        edges = []
        
        # Create nodes for functions with call information
        for func_name, context in self.function_contexts.items():
            node = {
                "id": func_name,
                "label": func_name,
                "type": "function",
                "call_sites_count": len(context.call_sites),
                "complexity": context.complexity_metrics.get("complexity_estimate", 0),
                "risk_level": context.risk_level
            }
            nodes.append(node)
        
        # Create edges for function calls
        for func_name, context in self.function_contexts.items():
            for call_site in context.call_sites:
                # Extract caller information if available
                caller = call_site.get("caller")
                if caller and caller in self.function_contexts:
                    edge = {
                        "source": caller,
                        "target": func_name,
                        "type": "call",
                        "weight": 1
                    }
                    edges.append(edge)
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            clusters=[],
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "graph_type": "call_graph"
            }
        )
    
    def _create_complexity_heatmap(self) -> Dict[str, Any]:
        """Create complexity heatmap data."""
        heatmap_data = []
        
        # Group functions by file
        file_functions = defaultdict(list)
        for func_name, context in self.function_contexts.items():
            if context.filepath:
                file_functions[context.filepath].append(context)
        
        for filepath, functions in file_functions.items():
            for func_context in functions:
                heatmap_data.append({
                    "file": Path(filepath).name,
                    "function": func_context.name,
                    "complexity": func_context.complexity_metrics.get("complexity_estimate", 0),
                    "line_count": func_context.complexity_metrics.get("line_count", 0),
                    "usage_count": func_context.complexity_metrics.get("usage_count", 0),
                    "risk_level": func_context.risk_level,
                    "impact_score": func_context.impact_score
                })
        
        return {
            "data": heatmap_data,
            "metrics": {
                "avg_complexity": sum(d["complexity"] for d in heatmap_data) / len(heatmap_data) if heatmap_data else 0,
                "max_complexity": max((d["complexity"] for d in heatmap_data), default=0),
                "high_complexity_functions": len([d for d in heatmap_data if d["complexity"] > 10])
            }
        }
    
    def _create_issue_dashboard(self) -> Dict[str, Any]:
        """Create issue dashboard data."""
        all_issues = []
        issue_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for func_name, context in self.function_contexts.items():
            for issue in context.issues:
                issue_data = {
                    "function": func_name,
                    "filepath": context.filepath,
                    "type": issue["type"],
                    "severity": issue["severity"],
                    "message": issue["message"],
                    "recommendation": issue.get("recommendation", "")
                }
                all_issues.append(issue_data)
                issue_counts[issue["type"]] += 1
                severity_counts[issue["severity"]] += 1
        
        return {
            "issues": all_issues,
            "summary": {
                "total_issues": len(all_issues),
                "issue_types": dict(issue_counts),
                "severity_distribution": dict(severity_counts),
                "functions_with_issues": len([c for c in self.function_contexts.values() if c.issues])
            }
        }
    
    def _create_summary(self) -> Dict[str, Any]:
        """Create analysis summary."""
        total_functions = len(self.function_contexts)
        total_issues = sum(len(c.issues) for c in self.function_contexts.values())
        
        risk_distribution = defaultdict(int)
        for context in self.function_contexts.values():
            risk_distribution[context.risk_level] += 1
        
        return {
            "codebase_stats": {
                "total_files": len(self.codebase.files),
                "total_functions": total_functions,
                "total_classes": len(self.codebase.classes),
                "total_imports": len(self.codebase.imports)
            },
            "analysis_stats": {
                "functions_analyzed": total_functions,
                "total_issues": total_issues,
                "avg_issues_per_function": total_issues / total_functions if total_functions else 0,
                "risk_distribution": dict(risk_distribution)
            },
            "quality_metrics": {
                "avg_complexity": sum(c.complexity_metrics.get("complexity_estimate", 0) for c in self.function_contexts.values()) / total_functions if total_functions else 0,
                "avg_impact_score": sum(c.impact_score for c in self.function_contexts.values()) / total_functions if total_functions else 0,
                "health_score": self.analysis_report.health_score if self.analysis_report else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_comprehensive_recommendations(self) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = set()
        
        # Collect all function recommendations
        for context in self.function_contexts.values():
            recommendations.update(context.recommendations)
        
        # Add system-level recommendations
        high_complexity_count = len([c for c in self.function_contexts.values() 
                                   if c.complexity_metrics.get("complexity_estimate", 0) > 10])
        
        if high_complexity_count > 5:
            recommendations.add("Consider implementing a complexity monitoring system")
        
        unused_functions = len([c for c in self.function_contexts.values() 
                              if c.complexity_metrics.get("usage_count", 0) == 0])
        
        if unused_functions > 3:
            recommendations.add("Review and remove unused functions to reduce codebase size")
        
        return list(recommendations)
    
    def _create_export_data(self) -> Dict[str, Any]:
        """Create data for export."""
        return {
            "function_contexts": [asdict(context) for context in self.function_contexts.values()],
            "analysis_report": asdict(self.analysis_report) if self.analysis_report else {},
            "export_timestamp": datetime.now().isoformat(),
            "codebase_info": {
                "total_files": len(self.codebase.files),
                "total_functions": len(self.codebase.functions),
                "total_classes": len(self.codebase.classes)
            }
        }
    
    def _save_interactive_report(self, report: InteractiveReport):
        """Save interactive report to files."""
        # Save JSON data
        json_file = self.output_dir / "analysis_report.json"
        with open(json_file, "w") as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        # Generate HTML report
        html_file = self.output_dir / "interactive_report.html"
        self._generate_html_report(report, html_file)
        
        # Save individual components
        self._save_component_files(report)
        
        logger.info(f"Interactive report saved to {self.output_dir}")
    
    def _generate_html_report(self, report: InteractiveReport, output_file: Path):
        """Generate interactive HTML report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .dashboard {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .panel {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .metric {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .risk-high {{ color: #e74c3c; }}
        .risk-medium {{ color: #f39c12; }}
        .risk-low {{ color: #f1c40f; }}
        .risk-minimal {{ color: #27ae60; }}
        .issue-error {{ background-color: #ffebee; }}
        .issue-warning {{ background-color: #fff3e0; }}
        .issue-info {{ background-color: #e3f2fd; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart {{ height: 400px; }}
    </style>
</head>
<body>
    <h1>🔍 Codebase Analysis Report</h1>
    
    <div class="dashboard">
        <div class="panel">
            <h2>📊 Summary</h2>
            <div class="metric">{report.summary['codebase_stats']['total_functions']}</div>
            <p>Total Functions</p>
            <div class="metric">{report.summary['analysis_stats']['total_issues']}</div>
            <p>Total Issues</p>
            <div class="metric">{report.summary['quality_metrics']['health_score']:.1f}</div>
            <p>Health Score</p>
        </div>
        
        <div class="panel">
            <h2>⚠️ Risk Distribution</h2>
            <div id="risk-chart" class="chart"></div>
        </div>
        
        <div class="panel">
            <h2>🔥 Complexity Heatmap</h2>
            <div id="complexity-chart" class="chart"></div>
        </div>
        
        <div class="panel">
            <h2>🐛 Issues Dashboard</h2>
            <div id="issues-chart" class="chart"></div>
        </div>
    </div>
    
    <div class="panel">
        <h2>🎯 Function Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th>Function</th>
                    <th>File</th>
                    <th>Complexity</th>
                    <th>Risk Level</th>
                    <th>Issues</th>
                    <th>Impact Score</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f'''
                <tr>
                    <td>{func.name}</td>
                    <td>{Path(func.filepath).name if func.filepath else 'N/A'}</td>
                    <td>{func.complexity_metrics.get('complexity_estimate', 0)}</td>
                    <td class="risk-{func.risk_level}">{func.risk_level}</td>
                    <td>{len(func.issues)}</td>
                    <td>{func.impact_score:.2f}</td>
                </tr>
                ''' for func in report.function_analysis[:20])}
            </tbody>
        </table>
    </div>
    
    <div class="panel">
        <h2>💡 Recommendations</h2>
        <ul>
            {''.join(f'<li>{rec}</li>' for rec in report.recommendations[:10])}
        </ul>
    </div>
    
    <script>
        // Risk distribution chart
        const riskData = {json.dumps(report.summary['analysis_stats']['risk_distribution'])};
        const riskChart = {{
            data: [{{
                values: Object.values(riskData),
                labels: Object.keys(riskData),
                type: 'pie',
                marker: {{
                    colors: ['#e74c3c', '#f39c12', '#f1c40f', '#27ae60']
                }}
            }}],
            layout: {{
                title: 'Risk Level Distribution',
                height: 350
            }}
        }};
        Plotly.newPlot('risk-chart', riskChart.data, riskChart.layout);
        
        // Complexity heatmap
        const complexityData = {json.dumps([f for f in report.complexity_heatmap['data'][:20]])};
        const complexityChart = {{
            data: [{{
                x: complexityData.map(d => d.function),
                y: complexityData.map(d => d.complexity),
                type: 'bar',
                marker: {{
                    color: complexityData.map(d => d.complexity),
                    colorscale: 'Viridis'
                }}
            }}],
            layout: {{
                title: 'Function Complexity',
                xaxis: {{ title: 'Functions' }},
                yaxis: {{ title: 'Complexity' }},
                height: 350
            }}
        }};
        Plotly.newPlot('complexity-chart', complexityChart.data, complexityChart.layout);
        
        // Issues chart
        const issuesData = {json.dumps(report.issue_dashboard['summary']['issue_types'])};
        const issuesChart = {{
            data: [{{
                x: Object.keys(issuesData),
                y: Object.values(issuesData),
                type: 'bar',
                marker: {{ color: '#3498db' }}
            }}],
            layout: {{
                title: 'Issues by Type',
                xaxis: {{ title: 'Issue Type' }},
                yaxis: {{ title: 'Count' }},
                height: 350
            }}
        }};
        Plotly.newPlot('issues-chart', issuesChart.data, issuesChart.layout);
    </script>
</body>
</html>
        """
        
        with open(output_file, "w") as f:
            f.write(html_content)
    
    def _save_component_files(self, report: InteractiveReport):
        """Save individual component files."""
        # Save dependency graph
        with open(self.output_dir / "dependency_graph.json", "w") as f:
            json.dump(asdict(report.dependency_graph), f, indent=2)
        
        # Save call graph
        with open(self.output_dir / "call_graph.json", "w") as f:
            json.dump(asdict(report.call_graph), f, indent=2)
        
        # Save function contexts
        with open(self.output_dir / "function_contexts.json", "w") as f:
            json.dump([asdict(fc) for fc in report.function_analysis], f, indent=2, default=str)
        
        # Save issues
        with open(self.output_dir / "issues.json", "w") as f:
            json.dump(report.issue_dashboard, f, indent=2)


def create_comprehensive_visualization(codebase: Codebase, output_dir: str = "codebase_analysis") -> InteractiveReport:
    """
    Create comprehensive codebase visualization and analysis.
    
    Args:
        codebase: Codebase to analyze
        output_dir: Output directory for reports
        
    Returns:
        Interactive report with comprehensive analysis
    """
    visualizer = CodebaseVisualizer(codebase, output_dir)
    return visualizer.generate_comprehensive_report()


def analyze_function_with_context(codebase: Codebase, function_name: str) -> Optional[FunctionContext]:
    """
    Analyze a specific function with full context.
    
    Args:
        codebase: Codebase containing the function
        function_name: Name of function to analyze
        
    Returns:
        Enhanced function context or None if not found
    """
    function = None
    for func in codebase.functions:
        if func.name == function_name:
            function = func
            break
    
    if not function:
        logger.warning(f"Function '{function_name}' not found in codebase")
        return None
    
    return get_enhanced_function_context(function)


if __name__ == "__main__":
    print("Codebase Visualization System")
    print("=" * 50)
    print("This module provides comprehensive codebase visualization")
    print("and interactive reporting capabilities.")
    print("\nKey features:")
    print("- Interactive HTML reports")
    print("- Dependency and call graph visualization")
    print("- Complexity heatmaps")
    print("- Issue dashboards")
    print("- Function context analysis")
    print("- Export capabilities")
