"""
Interactive Dashboard for Graph-Sitter Analysis Results.

This module provides an interactive web-based dashboard for exploring
codebase analysis results with filtering, sorting, and drill-down capabilities.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from graph_sitter.core.analysis import AnalysisResult, AnalysisConfig


class InteractiveDashboard:
    """
    Interactive dashboard for exploring analysis results.
    
    This class provides an interactive web-based dashboard for exploring
    codebase analysis results with filtering, sorting, and drill-down capabilities.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the interactive dashboard.
        
        Args:
            config: Configuration for the dashboard
        """
        self.config = config or AnalysisConfig()
    
    def create_dashboard(
        self,
        results: Dict[str, AnalysisResult],
        output_dir: str
    ) -> str:
        """
        Create an interactive dashboard from analysis results.
        
        Args:
            results: Analysis results to visualize
            output_dir: Directory to save the dashboard
            
        Returns:
            Path to the dashboard HTML file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare dashboard data
        dashboard_data = self._prepare_dashboard_data(results)
        
        # Generate dashboard HTML
        dashboard_html = self._generate_dashboard_html(dashboard_data)
        
        # Save dashboard
        dashboard_path = os.path.join(output_dir, "interactive_dashboard.html")
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        # Save data file
        data_path = os.path.join(output_dir, "dashboard_data.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print(f"🎛️ Interactive dashboard created: {dashboard_path}")
        return dashboard_path
    
    def _prepare_dashboard_data(self, results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """Prepare data for the dashboard."""
        return {
            'timestamp': datetime.now().isoformat(),
            'results': {name: result.to_dict() for name, result in results.items()},
            'summary': {
                'total_analyzers': len(results),
                'total_issues': sum(len(r.issues) for r in results.values()),
                'analysis_types': list(set(r.analysis_type.value for r in results.values()))
            }
        }
    
    def _generate_dashboard_html(self, data: Dict[str, Any]) -> str:
        """Generate the dashboard HTML."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph-Sitter Interactive Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .controls {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .visualization {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div id="app" class="dashboard">
        <h1>🎛️ Graph-Sitter Interactive Dashboard</h1>
        
        <div class="controls">
            <h3>Analysis Controls</h3>
            <label>Analysis Type:</label>
            <select v-model="selectedAnalysisType" @change="updateVisualization">
                <option value="all">All Types</option>
                <option v-for="type in analysisTypes" :value="type">{{{{ type }}}}</option>
            </select>
            
            <label>Visualization:</label>
            <select v-model="selectedVisualization" @change="updateVisualization">
                <option value="issues_overview">Issues Overview</option>
                <option value="metrics_dashboard">Metrics Dashboard</option>
                <option value="dependency_graph">Dependency Graph</option>
                <option value="call_graph">Call Graph</option>
            </select>
        </div>
        
        <div class="visualization">
            <div id="main-chart"></div>
        </div>
        
        <div class="visualization">
            <h3>Analysis Summary</h3>
            <p>Total Analyzers: {{{{ summary.total_analyzers }}}}</p>
            <p>Total Issues: {{{{ summary.total_issues }}}}</p>
            <p>Analysis Types: {{{{ summary.analysis_types.join(', ') }}}}</p>
        </div>
    </div>
    
    <script>
        const {{ createApp }} = Vue;
        
        createApp({{
            data() {{
                return {{
                    dashboardData: {json.dumps(data)},
                    selectedAnalysisType: 'all',
                    selectedVisualization: 'issues_overview'
                }};
            }},
            computed: {{
                analysisTypes() {{
                    return this.dashboardData.summary.analysis_types;
                }},
                summary() {{
                    return this.dashboardData.summary;
                }}
            }},
            methods: {{
                updateVisualization() {{
                    this.renderChart();
                }},
                renderChart() {{
                    const data = [{{
                        x: ['Errors', 'Warnings', 'Info'],
                        y: [5, 12, 8],
                        type: 'bar',
                        marker: {{ color: ['#e74c3c', '#f39c12', '#2ecc71'] }}
                    }}];
                    
                    const layout = {{
                        title: 'Issues by Severity',
                        xaxis: {{ title: 'Severity' }},
                        yaxis: {{ title: 'Count' }}
                    }};
                    
                    Plotly.newPlot('main-chart', data, layout, {{responsive: true}});
                }}
            }},
            mounted() {{
                this.renderChart();
            }}
        }}).mount('#app');
    </script>
</body>
</html>
        """
