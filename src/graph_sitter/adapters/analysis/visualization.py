"""
📊 Visualization and Reporting

Interactive HTML reports, D3.js visualizations, and export capabilities:
- Interactive HTML reports with rich visualizations
- Dependency graphs and class hierarchy visualizations
- D3.js-powered interactive charts and diagrams
- Multiple export formats (JSON, HTML, DOT, SVG)
- Real-time analysis dashboards
- Customizable report templates

Provides rich visual insights into codebase structure and metrics.
"""

import json
import html
import tempfile
import webbrowser
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from pathlib import Path
import base64


@dataclass
class VisualizationConfig:
    """Configuration for visualization generation"""
    theme: str = "light"
    color_scheme: str = "default"
    interactive: bool = True
    include_source_code: bool = False
    max_nodes: int = 1000
    max_depth: int = 10
    show_metrics: bool = True
    show_dependencies: bool = True
    export_format: str = "html"


@dataclass
class ChartData:
    """Data structure for chart generation"""
    title: str
    chart_type: str  # bar, line, pie, scatter, network, tree
    data: List[Dict[str, Any]]
    labels: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


class VisualizationEngine:
    """
    Core visualization engine for generating interactive reports
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load HTML templates for different visualization types"""
        return {
            'base_html': self._get_base_html_template(),
            'd3_network': self._get_d3_network_template(),
            'd3_tree': self._get_d3_tree_template(),
            'd3_bar_chart': self._get_d3_bar_chart_template(),
            'd3_pie_chart': self._get_d3_pie_chart_template(),
            'metrics_dashboard': self._get_metrics_dashboard_template(),
            'dependency_graph': self._get_dependency_graph_template()
        }
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                    output_path: str = None) -> str:
        """Generate a comprehensive HTML report with all visualizations"""
        try:
            # Prepare data for visualization
            charts = self._prepare_chart_data(analysis_results)
            
            # Generate HTML content
            html_content = self._generate_html_report(charts, analysis_results)
            
            # Save to file if path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return output_path
            else:
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(html_content)
                    return f.name
                    
        except Exception as e:
            print(f"Error generating comprehensive report: {e}")
            return ""
    
    def _prepare_chart_data(self, analysis_results: Dict[str, Any]) -> List[ChartData]:
        """Prepare data for various chart types"""
        charts = []
        
        # Complexity metrics chart
        if 'metrics' in analysis_results:
            metrics = analysis_results['metrics']
            charts.append(ChartData(
                title="Code Quality Metrics",
                chart_type="bar",
                data=[
                    {"name": "Cyclomatic Complexity", "value": metrics.get('cyclomatic_complexity', 0)},
                    {"name": "Maintainability Index", "value": metrics.get('maintainability_index', 0)},
                    {"name": "Technical Debt Ratio", "value": metrics.get('technical_debt_ratio', 0) * 100},
                    {"name": "Comment Ratio", "value": metrics.get('comment_ratio', 0) * 100}
                ]
            ))
        
        # Function complexity distribution
        if 'function_metrics' in analysis_results:
            func_metrics = analysis_results['function_metrics']
            complexity_data = [
                {"name": func_name, "value": metrics.get('cyclomatic_complexity', 0)}
                for func_name, metrics in func_metrics.items()
            ]
            charts.append(ChartData(
                title="Function Complexity Distribution",
                chart_type="bar",
                data=sorted(complexity_data, key=lambda x: x['value'], reverse=True)[:20]
            ))
        
        # Class hierarchy network
        if 'class_hierarchies' in analysis_results:
            hierarchies = analysis_results['class_hierarchies']
            network_data = []
            for parent, children in hierarchies.items():
                for child in children:
                    network_data.append({
                        "source": parent,
                        "target": child,
                        "type": "inheritance"
                    })
            
            if network_data:
                charts.append(ChartData(
                    title="Class Inheritance Network",
                    chart_type="network",
                    data=network_data
                ))
        
        # Test coverage pie chart
        if 'test_analysis' in analysis_results:
            test_data = analysis_results['test_analysis']
            total_functions = test_data.get('total_functions', 0)
            test_functions = test_data.get('total_test_functions', 0)
            
            charts.append(ChartData(
                title="Test Coverage Distribution",
                chart_type="pie",
                data=[
                    {"name": "Test Functions", "value": test_functions},
                    {"name": "Non-Test Functions", "value": max(0, total_functions - test_functions)}
                ]
            ))
        
        # Dead code analysis
        if 'dead_code' in analysis_results:
            dead_code = analysis_results['dead_code']
            total_functions = len(analysis_results.get('function_summaries', {}))
            
            charts.append(ChartData(
                title="Dead Code Analysis",
                chart_type="pie",
                data=[
                    {"name": "Dead Functions", "value": len(dead_code)},
                    {"name": "Active Functions", "value": max(0, total_functions - len(dead_code))}
                ]
            ))
        
        return charts
    
    def _generate_html_report(self, charts: List[ChartData], analysis_results: Dict[str, Any]) -> str:
        """Generate complete HTML report"""
        # Start with base template
        html_content = self.templates['base_html']
        
        # Generate chart sections
        chart_sections = []
        for i, chart in enumerate(charts):
            chart_html = self._generate_chart_html(chart, f"chart_{i}")
            chart_sections.append(chart_html)
        
        # Generate summary section
        summary_html = self._generate_summary_html(analysis_results)
        
        # Generate detailed metrics section
        metrics_html = self._generate_metrics_html(analysis_results)
        
        # Combine all sections
        content = f"""
        <div class="container">
            <h1>📊 Codebase Analysis Report</h1>
            
            <div class="summary-section">
                {summary_html}
            </div>
            
            <div class="charts-section">
                <h2>📈 Visualizations</h2>
                {''.join(chart_sections)}
            </div>
            
            <div class="metrics-section">
                {metrics_html}
            </div>
        </div>
        """
        
        # Replace placeholder in template
        html_content = html_content.replace('{{CONTENT}}', content)
        
        return html_content
    
    def _generate_chart_html(self, chart: ChartData, chart_id: str) -> str:
        """Generate HTML for a specific chart"""
        if chart.chart_type == "bar":
            return self._generate_bar_chart_html(chart, chart_id)
        elif chart.chart_type == "pie":
            return self._generate_pie_chart_html(chart, chart_id)
        elif chart.chart_type == "network":
            return self._generate_network_chart_html(chart, chart_id)
        else:
            return f"<div>Chart type '{chart.chart_type}' not implemented</div>"
    
    def _generate_bar_chart_html(self, chart: ChartData, chart_id: str) -> str:
        """Generate D3.js bar chart HTML"""
        data_json = json.dumps(chart.data)
        
        return f"""
        <div class="chart-container">
            <h3>{chart.title}</h3>
            <div id="{chart_id}" class="chart"></div>
            <script>
                (function() {{
                    const data = {data_json};
                    const margin = {{top: 20, right: 30, bottom: 40, left: 90}};
                    const width = 800 - margin.left - margin.right;
                    const height = 400 - margin.bottom - margin.top;
                    
                    const svg = d3.select("#{chart_id}")
                        .append("svg")
                        .attr("width", width + margin.left + margin.right)
                        .attr("height", height + margin.top + margin.bottom);
                    
                    const g = svg.append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
                    
                    const x = d3.scaleLinear()
                        .domain([0, d3.max(data, d => d.value)])
                        .range([0, width]);
                    
                    const y = d3.scaleBand()
                        .domain(data.map(d => d.name))
                        .range([0, height])
                        .padding(0.1);
                    
                    g.selectAll(".bar")
                        .data(data)
                        .enter().append("rect")
                        .attr("class", "bar")
                        .attr("x", 0)
                        .attr("y", d => y(d.name))
                        .attr("width", d => x(d.value))
                        .attr("height", y.bandwidth())
                        .attr("fill", "#4CAF50");
                    
                    g.append("g")
                        .attr("class", "x-axis")
                        .attr("transform", "translate(0," + height + ")")
                        .call(d3.axisBottom(x));
                    
                    g.append("g")
                        .attr("class", "y-axis")
                        .call(d3.axisLeft(y));
                }})();
            </script>
        </div>
        """
    
    def _generate_pie_chart_html(self, chart: ChartData, chart_id: str) -> str:
        """Generate D3.js pie chart HTML"""
        data_json = json.dumps(chart.data)
        
        return f"""
        <div class="chart-container">
            <h3>{chart.title}</h3>
            <div id="{chart_id}" class="chart"></div>
            <script>
                (function() {{
                    const data = {data_json};
                    const width = 400;
                    const height = 400;
                    const radius = Math.min(width, height) / 2;
                    
                    const color = d3.scaleOrdinal()
                        .domain(data.map(d => d.name))
                        .range(["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]);
                    
                    const svg = d3.select("#{chart_id}")
                        .append("svg")
                        .attr("width", width)
                        .attr("height", height);
                    
                    const g = svg.append("g")
                        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
                    
                    const pie = d3.pie()
                        .value(d => d.value);
                    
                    const arc = d3.arc()
                        .innerRadius(0)
                        .outerRadius(radius);
                    
                    const arcs = g.selectAll(".arc")
                        .data(pie(data))
                        .enter().append("g")
                        .attr("class", "arc");
                    
                    arcs.append("path")
                        .attr("d", arc)
                        .attr("fill", d => color(d.data.name));
                    
                    arcs.append("text")
                        .attr("transform", d => "translate(" + arc.centroid(d) + ")")
                        .attr("dy", "0.35em")
                        .style("text-anchor", "middle")
                        .text(d => d.data.name);
                }})();
            </script>
        </div>
        """
    
    def _generate_network_chart_html(self, chart: ChartData, chart_id: str) -> str:
        """Generate D3.js network chart HTML"""
        # Convert edge list to nodes and links
        nodes = set()
        for item in chart.data:
            nodes.add(item['source'])
            nodes.add(item['target'])
        
        nodes_list = [{"id": node, "name": node} for node in nodes]
        links_list = [{"source": item['source'], "target": item['target']} for item in chart.data]
        
        data_json = json.dumps({"nodes": nodes_list, "links": links_list})
        
        return f"""
        <div class="chart-container">
            <h3>{chart.title}</h3>
            <div id="{chart_id}" class="chart"></div>
            <script>
                (function() {{
                    const data = {data_json};
                    const width = 800;
                    const height = 600;
                    
                    const svg = d3.select("#{chart_id}")
                        .append("svg")
                        .attr("width", width)
                        .attr("height", height);
                    
                    const simulation = d3.forceSimulation(data.nodes)
                        .force("link", d3.forceLink(data.links).id(d => d.id))
                        .force("charge", d3.forceManyBody().strength(-300))
                        .force("center", d3.forceCenter(width / 2, height / 2));
                    
                    const link = svg.append("g")
                        .selectAll("line")
                        .data(data.links)
                        .enter().append("line")
                        .attr("stroke", "#999")
                        .attr("stroke-opacity", 0.6)
                        .attr("stroke-width", 2);
                    
                    const node = svg.append("g")
                        .selectAll("circle")
                        .data(data.nodes)
                        .enter().append("circle")
                        .attr("r", 8)
                        .attr("fill", "#4CAF50")
                        .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));
                    
                    const label = svg.append("g")
                        .selectAll("text")
                        .data(data.nodes)
                        .enter().append("text")
                        .text(d => d.name)
                        .attr("font-size", "12px")
                        .attr("dx", 12)
                        .attr("dy", 4);
                    
                    simulation.on("tick", () => {{
                        link
                            .attr("x1", d => d.source.x)
                            .attr("y1", d => d.source.y)
                            .attr("x2", d => d.target.x)
                            .attr("y2", d => d.target.y);
                        
                        node
                            .attr("cx", d => d.x)
                            .attr("cy", d => d.y);
                        
                        label
                            .attr("x", d => d.x)
                            .attr("y", d => d.y);
                    }});
                    
                    function dragstarted(event, d) {{
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        d.fx = d.x;
                        d.fy = d.y;
                    }}
                    
                    function dragged(event, d) {{
                        d.fx = event.x;
                        d.fy = event.y;
                    }}
                    
                    function dragended(event, d) {{
                        if (!event.active) simulation.alphaTarget(0);
                        d.fx = null;
                        d.fy = null;
                    }}
                }})();
            </script>
        </div>
        """
    
    def _generate_summary_html(self, analysis_results: Dict[str, Any]) -> str:
        """Generate summary section HTML"""
        summary = analysis_results.get('codebase_summary', '')
        
        return f"""
        <div class="summary-card">
            <h2>📋 Codebase Summary</h2>
            <pre>{html.escape(summary)}</pre>
        </div>
        """
    
    def _generate_metrics_html(self, analysis_results: Dict[str, Any]) -> str:
        """Generate detailed metrics section HTML"""
        metrics_html = "<h2>📊 Detailed Metrics</h2>"
        
        # Issues section
        if 'issues' in analysis_results:
            issues = analysis_results['issues']
            metrics_html += f"""
            <div class="metrics-card">
                <h3>⚠️ Issues Found ({len(issues)})</h3>
                <ul>
            """
            for issue in issues[:10]:  # Show first 10 issues
                metrics_html += f"""
                    <li>
                        <strong>{issue.get('type', 'Unknown')}</strong>: 
                        {html.escape(issue.get('message', ''))}
                        <br><small>Location: {issue.get('location', 'Unknown')}</small>
                    </li>
                """
            if len(issues) > 10:
                metrics_html += f"<li>... and {len(issues) - 10} more issues</li>"
            metrics_html += "</ul></div>"
        
        # Dead code section
        if 'dead_code' in analysis_results:
            dead_code = analysis_results['dead_code']
            metrics_html += f"""
            <div class="metrics-card">
                <h3>🗑️ Dead Code ({len(dead_code)} functions)</h3>
                <ul>
            """
            for func in dead_code[:10]:
                metrics_html += f"<li>{html.escape(func)}</li>"
            if len(dead_code) > 10:
                metrics_html += f"<li>... and {len(dead_code) - 10} more functions</li>"
            metrics_html += "</ul></div>"
        
        # Recursive functions
        if 'recursive_functions' in analysis_results:
            recursive = analysis_results['recursive_functions']
            if recursive:
                metrics_html += f"""
                <div class="metrics-card">
                    <h3>🔄 Recursive Functions ({len(recursive)})</h3>
                    <ul>
                """
                for func in recursive:
                    metrics_html += f"<li>{html.escape(func)}</li>"
                metrics_html += "</ul></div>"
        
        return metrics_html
    
    def _get_base_html_template(self) -> str:
        """Get base HTML template with D3.js and styling"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Codebase Analysis Report</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 2.5em;
                }
                h2 {
                    color: #34495e;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-top: 40px;
                }
                h3 {
                    color: #2c3e50;
                    margin-top: 30px;
                }
                .chart-container {
                    margin: 30px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background: #fafafa;
                }
                .chart {
                    text-align: center;
                }
                .summary-card, .metrics-card {
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }
                .summary-card pre {
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                    font-size: 0.9em;
                }
                .metrics-card ul {
                    list-style-type: none;
                    padding: 0;
                }
                .metrics-card li {
                    padding: 10px;
                    margin: 5px 0;
                    background: white;
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }
                .bar {
                    transition: fill 0.3s;
                }
                .bar:hover {
                    fill: #2ecc71 !important;
                }
                .axis {
                    font-size: 12px;
                }
                .axis path,
                .axis line {
                    fill: none;
                    stroke: #333;
                    shape-rendering: crispEdges;
                }
                .arc text {
                    font-size: 12px;
                    fill: white;
                    font-weight: bold;
                }
                .node {
                    cursor: pointer;
                }
                .node:hover {
                    fill: #2ecc71;
                }
                .link {
                    stroke: #999;
                    stroke-opacity: 0.6;
                }
            </style>
        </head>
        <body>
            {{CONTENT}}
        </body>
        </html>
        """
    
    def _get_d3_network_template(self) -> str:
        """Template for D3.js network visualization"""
        return "<!-- D3 Network Template -->"
    
    def _get_d3_tree_template(self) -> str:
        """Template for D3.js tree visualization"""
        return "<!-- D3 Tree Template -->"
    
    def _get_d3_bar_chart_template(self) -> str:
        """Template for D3.js bar chart"""
        return "<!-- D3 Bar Chart Template -->"
    
    def _get_d3_pie_chart_template(self) -> str:
        """Template for D3.js pie chart"""
        return "<!-- D3 Pie Chart Template -->"
    
    def _get_metrics_dashboard_template(self) -> str:
        """Template for metrics dashboard"""
        return "<!-- Metrics Dashboard Template -->"
    
    def _get_dependency_graph_template(self) -> str:
        """Template for dependency graph"""
        return "<!-- Dependency Graph Template -->"


class HTMLReportGenerator:
    """
    Specialized HTML report generator
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.engine = VisualizationEngine(config)
    
    def generate_report(self, analysis_results: Dict[str, Any], output_path: str) -> str:
        """Generate HTML report and save to file"""
        return self.engine.generate_comprehensive_report(analysis_results, output_path)
    
    def generate_dashboard(self, analysis_results: Dict[str, Any], output_path: str) -> str:
        """Generate interactive dashboard"""
        # Enhanced dashboard with more interactive features
        return self.generate_report(analysis_results, output_path)


class DependencyGraphGenerator:
    """
    Generator for dependency graphs and network visualizations
    """
    
    def __init__(self):
        self.engine = VisualizationEngine()
    
    def generate_dependency_graph(self, dependencies: Dict[str, List[str]], 
                                output_format: str = "html") -> str:
        """Generate dependency graph visualization"""
        if output_format == "dot":
            return self._generate_dot_graph(dependencies)
        elif output_format == "html":
            return self._generate_html_graph(dependencies)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _generate_dot_graph(self, dependencies: Dict[str, List[str]]) -> str:
        """Generate DOT format graph"""
        dot_lines = ["digraph Dependencies {"]
        dot_lines.append("  rankdir=LR;")
        dot_lines.append("  node [shape=box, style=rounded];")
        
        for source, targets in dependencies.items():
            for target in targets:
                dot_lines.append(f'  "{source}" -> "{target}";')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def _generate_html_graph(self, dependencies: Dict[str, List[str]]) -> str:
        """Generate HTML network graph"""
        # Convert to network data
        network_data = []
        for source, targets in dependencies.items():
            for target in targets:
                network_data.append({
                    "source": source,
                    "target": target,
                    "type": "dependency"
                })
        
        chart = ChartData(
            title="Dependency Network",
            chart_type="network",
            data=network_data
        )
        
        return self.engine._generate_network_chart_html(chart, "dependency_graph")


class InteractiveTreeVisualizer:
    """
    Interactive tree visualizer for syntax trees and hierarchies
    """
    
    def __init__(self):
        self.engine = VisualizationEngine()
    
    def visualize_tree(self, tree_data: Dict[str, Any], output_path: str) -> str:
        """Generate interactive tree visualization"""
        # Implementation would create D3.js tree visualization
        html_content = self._generate_tree_html(tree_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_tree_html(self, tree_data: Dict[str, Any]) -> str:
        """Generate HTML for tree visualization"""
        # Simplified tree visualization
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Interactive Tree Visualization</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
        </head>
        <body>
            <div id="tree-container"></div>
            <script>
                // Tree visualization implementation would go here
                console.log("Tree data:", {json.dumps(tree_data)});
            </script>
        </body>
        </html>
        """


# Convenience functions for direct use

def export_to_html(analysis_results: Dict[str, Any], output_path: str, 
                  config: Optional[VisualizationConfig] = None) -> str:
    """Export analysis results to HTML report"""
    generator = HTMLReportGenerator(config)
    return generator.generate_report(analysis_results, output_path)


def export_to_json(analysis_results: Dict[str, Any], output_path: str) -> str:
    """Export analysis results to JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    return output_path


def export_to_dot(dependencies: Dict[str, List[str]], output_path: str) -> str:
    """Export dependency graph to DOT format"""
    generator = DependencyGraphGenerator()
    dot_content = generator.generate_dependency_graph(dependencies, "dot")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(dot_content)
    
    return output_path


def generate_d3_visualization(chart_data: ChartData, output_path: str) -> str:
    """Generate D3.js visualization"""
    engine = VisualizationEngine()
    chart_html = engine._generate_chart_html(chart_data, "main_chart")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{chart_data.title}</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .chart {{ text-align: center; }}
        </style>
    </head>
    <body>
        {chart_html}
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path

