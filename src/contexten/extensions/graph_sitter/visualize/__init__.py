"""
Graph-Sitter Visualization Module

Consolidated visualization features for Tree-sitter analysis results.
Provides interactive charts, graphs, and reports for codebase insights.
"""

import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile


class Visualize:
    """
    Unified Visualization Interface
    
    Consolidates all visualization features for Tree-sitter analysis results
    into interactive charts, dependency graphs, and comprehensive reports.
    """
    
    def __init__(self, codebase: Optional[Codebase] = None):
        """
        Initialize the Visualization system.
        
        Args:
            codebase: Optional codebase to visualize. Can be set later.
        """
        self.codebase = codebase
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd',
            'light': '#8c564b',
            'dark': '#e377c2'
        }
    
    def set_codebase(self, codebase: Codebase) -> None:
        """
        Set the codebase for visualization.
        
        Args:
            codebase: The codebase to visualize
        """
        self.codebase = codebase
    
    def create_codebase_overview(self, analysis_results: Dict[str, Any]) -> go.Figure:
        """
        Create an overview dashboard of codebase metrics.
        
        Args:
            analysis_results: Results from comprehensive analysis
            
        Returns:
            go.Figure: Interactive dashboard figure
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Codebase Structure', 'Complexity Distribution', 
                          'Security Issues', 'Dead Code Analysis'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )
        
        # Codebase structure pie chart
        metrics = analysis_results['metrics']
        structure_labels = ['Functions', 'Classes', 'Global Vars', 'Interfaces']
        structure_values = [
            metrics['functions_count'],
            metrics['classes_count'], 
            metrics['global_vars_count'],
            metrics['interfaces_count']
        ]
        
        fig.add_trace(
            go.Pie(
                labels=structure_labels,
                values=structure_values,
                name="Structure",
                marker_colors=[self.color_scheme['primary'], self.color_scheme['secondary'],
                             self.color_scheme['success'], self.color_scheme['info']]
            ),
            row=1, col=1
        )
        
        # Complexity distribution bar chart
        complexity = analysis_results['complexity']['summary']
        complexity_labels = ['Complex Functions', 'Large Functions', 'Complex Classes']
        complexity_values = [
            complexity['total_complex_functions'],
            complexity['total_large_functions'],
            complexity['total_complex_classes']
        ]
        
        fig.add_trace(
            go.Bar(
                x=complexity_labels,
                y=complexity_values,
                name="Complexity",
                marker_color=self.color_scheme['warning']
            ),
            row=1, col=2
        )
        
        # Security issues bar chart
        security = analysis_results['security']['summary']
        security_labels = ['Dangerous Imports', 'Security Issues', 'High Risk Items']
        security_values = [
            security['total_dangerous_imports'],
            security['total_security_issues'],
            security['high_risk_items']
        ]
        
        fig.add_trace(
            go.Bar(
                x=security_labels,
                y=security_values,
                name="Security",
                marker_color=self.color_scheme['warning']
            ),
            row=2, col=1
        )
        
        # Dead code pie chart
        dead_code = analysis_results['dead_code']['summary']
        dead_labels = ['Dead Functions', 'Dead Classes', 'Dead Variables']
        dead_values = [
            dead_code['total_dead_functions'],
            dead_code['total_dead_classes'],
            dead_code['total_dead_variables']
        ]
        
        if sum(dead_values) > 0:
            fig.add_trace(
                go.Pie(
                    labels=dead_labels,
                    values=dead_values,
                    name="Dead Code",
                    marker_colors=[self.color_scheme['light'], self.color_scheme['dark'],
                                 self.color_scheme['info']]
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="Codebase Analysis Overview",
            title_x=0.5,
            height=800,
            showlegend=True
        )
        
        return fig
    
    def create_dependency_graph(self, codebase: Optional[Any] = None) -> str:
        """Create a dependency graph visualization"""
        if codebase is None:
            codebase = self.codebase
            
        if codebase is None:
            return "No codebase available for visualization"
            
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            from io import BytesIO
            import base64
            
            G: nx.DiGraph = nx.DiGraph()
            
            # Add basic nodes from codebase files
            if hasattr(codebase, 'files'):
                for file in list(codebase.files)[:20]:  # Limit to 20 files
                    G.add_node(file.name)
                    
                    # Add edges for imports
                    if hasattr(file, 'imports'):
                        for imp in file.imports:
                            if hasattr(imp, 'module_name'):
                                G.add_edge(file.name, imp.module_name)
            
            # Calculate layout
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Extract node and edge information
            node_x = [pos[node][0] for node in G.nodes()]
            node_y = [pos[node][1] for node in G.nodes()]
            node_text = list(G.nodes())
            
            edge_x = []
            edge_y = []
            edge_weights = []
            
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_weights.append(G[edge[0]][edge[1]].get('weight', 1))
            
            # Create edge trace
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color=self.color_scheme['light']),
                hoverinfo='none',
                mode='lines'
            )
            
            # Create node trace
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="middle center",
                marker=dict(
                    size=20,
                    color=self.color_scheme['primary'],
                    line=dict(width=2, color='white')
                )
            )
            
            # Create figure
            fig = go.Figure(data=[edge_trace, node_trace],
                           layout=go.Layout(
                               title='Module Dependency Graph',
                               titlefont_size=16,
                               showlegend=False,
                               hovermode='closest',
                               margin=dict(b=20,l=5,r=5,t=40),
                               annotations=[ dict(
                                   text="Dependency relationships between modules",
                                   showarrow=False,
                                   xref="paper", yref="paper",
                                   x=0.005, y=-0.002,
                                   xanchor="left", yanchor="bottom",
                                   font=dict(color="#888", size=12)
                               )],
                               xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                               yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                           ))
            
            # Export as PNG (requires kaleido)
            try:
                png_file = BytesIO()
                plt.figure(figsize=(10, 10))
                nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1000, font_size=10)
                plt.savefig(png_file, format='png')
                png_file.seek(0)
                png_base64 = base64.b64encode(png_file.read()).decode('utf-8')
                return f"data:image/png;base64,{png_base64}"
            except Exception as e:
                print(f"���️ Could not export PNG: {e}")
                return "No PNG export available"
        
        except Exception as e:
            print(f"���️ Error creating dependency graph: {e}")
            return "Error creating dependency graph"
    
    def create_complexity_heatmap(self, analysis_results: Dict[str, Any]) -> go.Figure:
        """
        Create a complexity heatmap for functions and classes.
        
        Args:
            analysis_results: Results from complexity analysis
            
        Returns:
            go.Figure: Interactive complexity heatmap
        """
        # Prepare data for heatmap
        complex_functions = analysis_results['complexity']['complex_functions'][:20]  # Top 20
        
        if not complex_functions:
            # Create empty heatmap
            fig = go.Figure(data=go.Heatmap(
                z=[[0]],
                x=['No Data'],
                y=['No Data'],
                colorscale='Reds'
            ))
            fig.update_layout(title="No Complex Functions Found")
            return fig
        
        # Create matrix data
        function_names = [f['name'][:20] for f in complex_functions]  # Truncate names
        complexity_scores = [f['complexity_score'] for f in complex_functions]
        lines_of_code = [f['lines_of_code'] for f in complex_functions]
        
        # Create 2D matrix for heatmap
        z_data = []
        for i, func in enumerate(complex_functions):
            z_data.append([func['complexity_score'], func['lines_of_code']])
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=['Complexity Score', 'Lines of Code'],
            y=function_names,
            colorscale='Reds',
            hoverongaps=False,
            hovertemplate='Function: %{y}<br>Metric: %{x}<br>Value: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Function Complexity Heatmap',
            xaxis_title='Metrics',
            yaxis_title='Functions',
            height=max(400, len(function_names) * 25)
        )
        
        return fig
    
    def generate_html_report(self, analysis_results: Dict[str, Any], 
                           output_path: str = "codebase_analysis_report.html") -> str:
        """
        Generate a comprehensive HTML report with all visualizations.
        
        Args:
            analysis_results: Results from comprehensive analysis
            output_path: Path to save the HTML report
            
        Returns:
            str: Path to the generated HTML report
        """
        # Create all visualizations
        overview_fig = self.create_codebase_overview(analysis_results)
        dependency_fig = self.create_dependency_graph(analysis_results)
        complexity_fig = self.create_complexity_heatmap(analysis_results)
        
        # Generate HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Codebase Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .chart-container {{
            margin: 20px 0;
        }}
        .summary-box {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 10px;
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            min-width: 120px;
            text-align: center;
        }}
        .warning {{
            background-color: #e74c3c;
        }}
        .success {{
            background-color: #27ae60;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Comprehensive Codebase Analysis Report</h1>
        <p>Generated: {analysis_results['metadata']['analysis_timestamp']}</p>
        <p>Analysis Duration: {analysis_results['metadata']['analysis_duration']:.2f} seconds</p>
    </div>
    
    <div class="section">
        <h2>📊 Executive Summary</h2>
        <div class="summary-box">
            <div class="metric">Files: {analysis_results['metrics']['files_count']}</div>
            <div class="metric">Functions: {analysis_results['metrics']['functions_count']}</div>
            <div class="metric">Classes: {analysis_results['metrics']['classes_count']}</div>
            <div class="metric">Symbols: {analysis_results['metrics']['symbols_count']}</div>
        </div>
        <div class="summary-box">
            <div class="metric warning">Dead Code: {analysis_results['dead_code']['summary']['total_dead_items']}</div>
            <div class="metric warning">Security Issues: {analysis_results['security']['summary']['total_security_issues']}</div>
            <div class="metric warning">Complex Functions: {analysis_results['complexity']['summary']['total_complex_functions']}</div>
            <div class="metric success">Hotspots: {len(analysis_results['hotspots'])}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Codebase Overview</h2>
        <div class="chart-container" id="overview-chart"></div>
    </div>
    
    <div class="section">
        <h2>🔗 Dependency Analysis</h2>
        <div class="chart-container" id="dependency-chart"></div>
    </div>
    
    <div class="section">
        <h2>🌡️ Complexity Analysis</h2>
        <div class="chart-container" id="complexity-chart"></div>
    </div>
    
    <div class="section">
        <h2>💡 Recommendations</h2>
        <ul>
        """
        
        for rec in analysis_results['recommendations']:
            html_content += f"<li>{rec}</li>"
        
        html_content += f"""
        </ul>
    </div>
    
    <script>
        // Plot all charts
        Plotly.newPlot('overview-chart', {overview_fig.to_json()});
        Plotly.newPlot('dependency-chart', {dependency_fig.to_json()});
        Plotly.newPlot('complexity-chart', {complexity_fig.to_json()});
    </script>
</body>
</html>
        """
        
        # Save HTML file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML report generated: {output_path}")
        return str(output_file.absolute())
    
    def export_charts(self, analysis_results: Dict[str, Any], 
                     output_dir: str = "charts") -> List[str]:
        """
        Export all charts as individual files.
        
        Args:
            analysis_results: Results from comprehensive analysis
            output_dir: Directory to save chart files
            
        Returns:
            List[str]: Paths to exported chart files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        # Create and export all charts
        charts = {
            'overview': self.create_codebase_overview(analysis_results),
            'dependencies': self.create_dependency_graph(analysis_results),
            'complexity': self.create_complexity_heatmap(analysis_results)
        }
        
        for name, fig in charts.items():
            # Export as HTML
            html_file = output_path / f"{name}.html"
            fig.write_html(str(html_file))
            exported_files.append(str(html_file))
            
            # Export as PNG (requires kaleido)
            try:
                png_file = output_path / f"{name}.png"
                fig.write_image(str(png_file), width=1200, height=800)
                exported_files.append(str(png_file))
            except Exception as e:
                print(f"���️ Could not export PNG for {name}: {e}")
        
        print(f"📊 Charts exported to: {output_dir}")
        return exported_files


# Export main class
__all__ = ['Visualize']
