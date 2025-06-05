"""
Visualization - Using Graph-Sitter's Built-in Visualization

This implements visualization using graph-sitter's built-in visualize() method
and simple dashboard creation as mentioned on graph-sitter.com.
"""

import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import json

from graph_sitter.core.codebase import Codebase
from .simple_analysis import get_call_graph, get_inheritance_hierarchy


def visualize_call_graph(codebase_or_path, output_path: Optional[str] = None) -> str:
    """
    Visualize call graph using graph-sitter's built-in visualization.
    
    Based on the visualization example from graph-sitter.com:
    "codebase.visualize(graph='call_graph')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Use graph-sitter's built-in visualization
    if hasattr(codebase, 'visualize'):
        return codebase.visualize(graph='call_graph', output=output_path)
    else:
        # Fallback to simple HTML visualization
        call_graph = get_call_graph(codebase)
        return _create_simple_graph_html(call_graph, "Call Graph", output_path)


def visualize_inheritance(codebase_or_path, output_path: Optional[str] = None) -> str:
    """
    Visualize inheritance hierarchy using graph-sitter's built-in visualization.
    
    Based on the visualization example from graph-sitter.com:
    "codebase.visualize(graph='inheritance')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Use graph-sitter's built-in visualization
    if hasattr(codebase, 'visualize'):
        return codebase.visualize(graph='inheritance', output=output_path)
    else:
        # Fallback to simple HTML visualization
        hierarchy = get_inheritance_hierarchy(codebase)
        return _create_simple_graph_html(hierarchy, "Inheritance Hierarchy", output_path)


def visualize_dependencies(codebase_or_path, output_path: Optional[str] = None) -> str:
    """
    Visualize dependencies using graph-sitter's built-in visualization.
    
    Based on the visualization example from graph-sitter.com:
    "codebase.visualize(graph='dependencies')"
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Use graph-sitter's built-in visualization
    if hasattr(codebase, 'visualize'):
        return codebase.visualize(graph='dependencies', output=output_path)
    else:
        # Fallback to simple HTML visualization
        deps = {}
        for func in codebase.functions:
            if hasattr(func, 'dependencies'):
                deps[func.name] = [dep.name for dep in func.dependencies]
        return _create_simple_graph_html(deps, "Dependencies", output_path)


def create_interactive_dashboard(codebase_or_path, analysis_results: Dict[str, Any]) -> str:
    """
    Create interactive dashboard with visualization options.
    
    This provides the HTML dashboard requested by the user with:
    1. Issues/errors listing
    2. Optional "Visualize Codebase" button
    3. Dropdown for analysis types
    4. Target selection
    """
    if isinstance(codebase_or_path, str):
        codebase = Codebase(codebase_or_path)
    else:
        codebase = codebase_or_path
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        html_content = _generate_dashboard_html(codebase, analysis_results)
        f.write(html_content)
        dashboard_path = f.name
    
    return dashboard_path


def _generate_dashboard_html(codebase: Codebase, analysis_results: Dict[str, Any]) -> str:
    """Generate the HTML content for the interactive dashboard."""
    
    stats = analysis_results.get('stats', {})
    issues = analysis_results.get('issues', [])
    summary = analysis_results.get('summary', {})
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Graph-Sitter Analysis Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                  gap: 20px; margin: 30px 0; }}
        .stat-box {{ background: white; padding: 20px; border-radius: 8px; 
                     box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .section {{ background: white; margin: 20px 0; padding: 25px; 
                    border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .issues {{ margin: 20px 0; }}
        .issue {{ padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid; }}
        .issue.high {{ background: #fff5f5; border-color: #e53e3e; }}
        .issue.medium {{ background: #fffbeb; border-color: #dd6b20; }}
        .issue.low {{ background: #f0fff4; border-color: #38a169; }}
        .visualize-section {{ background: #f8f9fa; padding: 25px; border-radius: 8px; }}
        .controls {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .control-group {{ display: flex; flex-direction: column; gap: 5px; }}
        select {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; }}
        button {{ padding: 12px 24px; background: #667eea; color: white; 
                  border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }}
        button:hover {{ background: #5a67d8; }}
        .visualization {{ display: none; margin: 20px 0; padding: 25px; 
                          background: white; border-radius: 8px; border: 2px dashed #667eea; }}
        .graph-placeholder {{ background: #f7fafc; padding: 40px; text-align: center; 
                              border-radius: 8px; color: #4a5568; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Graph-Sitter Analysis Dashboard</h1>
            <p>Comprehensive codebase analysis using graph-sitter's built-in capabilities</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{stats.get('total_files', 0)}</div>
                <div class="stat-label">📁 Files</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats.get('total_functions', 0)}</div>
                <div class="stat-label">⚡ Functions</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{stats.get('total_classes', 0)}</div>
                <div class="stat-label">🏗️ Classes</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{summary.get('total_issues', 0)}</div>
                <div class="stat-label">🚨 Issues</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🚨 Issues & Analysis Results</h2>
            <div class="issues">
                {_generate_issues_html(issues)}
            </div>
        </div>
        
        <div class="section">
            <div class="visualize-section">
                <h2>📊 Interactive Codebase Visualization</h2>
                <p>Select analysis type and target to generate interactive visualizations:</p>
                
                <div class="controls">
                    <div class="control-group">
                        <label><strong>Analysis Type:</strong></label>
                        <select id="analysisType">
                            <option value="call_graph">Call Graph Analysis</option>
                            <option value="inheritance">Inheritance Hierarchy</option>
                            <option value="dependencies">Dependency Analysis</option>
                            <option value="blast_radius">Blast Radius Analysis</option>
                            <option value="dead_code">Dead Code Detection</option>
                        </select>
                    </div>
                    
                    <div class="control-group">
                        <label><strong>Target Element:</strong></label>
                        <select id="targetElement">
                            <option value="">All elements</option>
                            {_generate_target_options(codebase)}
                        </select>
                    </div>
                    
                    <button onclick="loadVisualization()">🎯 Generate Visualization</button>
                </div>
                
                <div id="visualization" class="visualization">
                    <h3>📈 Interactive Graph Visualization</h3>
                    <div class="graph-placeholder">
                        <h4>🎨 Graph Visualization Area</h4>
                        <p><strong>Analysis:</strong> <span id="selectedAnalysis"></span></p>
                        <p><strong>Target:</strong> <span id="selectedTarget"></span></p>
                        <p>Interactive graph would be rendered here using graph-sitter's built-in visualize() method</p>
                        <ul style="text-align: left; display: inline-block;">
                            <li>🔵 Nodes: Functions, Classes, Files</li>
                            <li>🔗 Edges: Dependencies, Calls, Inheritance</li>
                            <li>🖱️ Interactive: Click to explore, zoom, filter</li>
                            <li>🎯 Focused: Based on selected analysis type and target</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function loadVisualization() {{
            const analysisType = document.getElementById('analysisType').value;
            const target = document.getElementById('targetElement').value;
            
            document.getElementById('selectedAnalysis').textContent = 
                analysisType.replace('_', ' ').toUpperCase();
            document.getElementById('selectedTarget').textContent = target || 'All Elements';
            document.getElementById('visualization').style.display = 'block';
            
            // In real implementation, this would call:
            // codebase.visualize(graph=analysisType, target=target)
            console.log('Loading visualization:', analysisType, 'for target:', target);
        }}
    </script>
</body>
</html>
"""


def _generate_issues_html(issues) -> str:
    """Generate HTML for the issues list."""
    if not issues:
        return "<div class='issue low'>✅ <strong>No issues found!</strong> Your codebase looks great.</div>"
    
    html = ""
    for issue in issues[:20]:  # Limit display
        severity = issue.get('severity', 'low')
        html += f"""
        <div class="issue {severity}">
            <strong>{severity.upper()}:</strong> {issue.get('description', 'Unknown issue')}
            <br><small>📍 Category: {issue.get('category', 'general')}</small>
        </div>
        """
    
    if len(issues) > 20:
        html += f"<div class='issue low'><em>... and {len(issues) - 20} more issues</em></div>"
    
    return html


def _generate_target_options(codebase) -> str:
    """Generate HTML options for target selection."""
    options = ""
    
    # Add function options (limit to prevent overwhelming dropdown)
    functions = list(codebase.functions)[:50] if hasattr(codebase, 'functions') else []
    for func in functions:
        if hasattr(func, 'name'):
            options += f'<option value="function:{func.name}">{func.name} (function)</option>'
    
    # Add class options
    classes = list(codebase.classes)[:50] if hasattr(codebase, 'classes') else []
    for cls in classes:
        if hasattr(cls, 'name'):
            options += f'<option value="class:{cls.name}">{cls.name} (class)</option>'
    
    return options


def _create_simple_graph_html(graph_data: Dict[str, Any], title: str, output_path: Optional[str] = None) -> str:
    """Create a simple HTML visualization for graph data."""
    
    if output_path is None:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title} - Graph-Sitter Visualization</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .graph-container {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .node {{ background: #e3f2fd; padding: 10px; margin: 5px; border-radius: 4px; }}
        .edge {{ margin-left: 20px; color: #666; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="graph-container">
        <h3>Graph Structure:</h3>
        {_format_graph_data(graph_data)}
    </div>
    <p><em>This is a simple fallback visualization. In a full implementation, 
    this would use graph-sitter's built-in interactive visualization.</em></p>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    return output_path


def _format_graph_data(graph_data: Dict[str, Any]) -> str:
    """Format graph data as simple HTML."""
    html = ""
    for node, connections in graph_data.items():
        html += f'<div class="node"><strong>{node}</strong>'
        if connections:
            for connection in connections:
                html += f'<div class="edge">→ {connection}</div>'
        else:
            html += '<div class="edge">→ (no connections)</div>'
        html += '</div>'
    return html

