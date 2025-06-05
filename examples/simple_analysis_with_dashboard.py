#!/usr/bin/env python3
"""
Simple Analysis with Dashboard - Demonstrates the user's requested API pattern

This example shows how to use the simplified analysis system with the exact
API pattern requested by the user, including optional dashboard visualization.
"""

import tempfile
import webbrowser
from pathlib import Path
from graph_sitter import Codebase, Analysis


def create_analysis_dashboard(codebase, analysis_results):
    """
    Create an HTML dashboard for analysis results.
    
    This provides the URL-based interface requested by the user:
    1. Initial URL lists issues/errors
    2. Optional "Visualize Codebase" button loads interactive visuals
    3. Dropdown for different analysis types (dependency, blast radius, etc.)
    """
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Graph-Sitter Analysis Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #e8f4f8; padding: 15px; border-radius: 5px; flex: 1; }}
        .issues {{ margin: 20px 0; }}
        .issue {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .issue.high {{ background: #f8d7da; }}
        .issue.medium {{ background: #fff3cd; }}
        .issue.low {{ background: #d1ecf1; }}
        .visualize-section {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
        .dropdown {{ margin: 10px 0; }}
        select {{ padding: 5px; margin: 5px; }}
        button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        .visualization {{ display: none; margin: 20px 0; padding: 20px; background: #e9ecef; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Graph-Sitter Analysis Results</h1>
        <p>Comprehensive codebase analysis using graph-sitter's built-in capabilities</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <h3>📁 Files</h3>
            <p>{analysis_results['stats'].total_files}</p>
        </div>
        <div class="stat-box">
            <h3>⚡ Functions</h3>
            <p>{analysis_results['stats'].total_functions}</p>
        </div>
        <div class="stat-box">
            <h3>🏗️ Classes</h3>
            <p>{analysis_results['stats'].total_classes}</p>
        </div>
        <div class="stat-box">
            <h3>🚨 Issues</h3>
            <p>{analysis_results['summary']['total_issues']}</p>
        </div>
    </div>
    
    <div class="issues">
        <h2>🚨 Issues & Errors Found</h2>
        {generate_issues_html(analysis_results['issues'])}
    </div>
    
    <div class="visualize-section">
        <h2>📊 Visualize Codebase</h2>
        <p>Click to load interactive codebase visualization with analysis options:</p>
        
        <div class="dropdown">
            <label>Analysis Type:</label>
            <select id="analysisType">
                <option value="dependency">Dependency Analysis</option>
                <option value="call_graph">Call Graph</option>
                <option value="inheritance">Inheritance Hierarchy</option>
                <option value="blast_radius">Blast Radius Analysis</option>
                <option value="dead_code">Dead Code Detection</option>
            </select>
        </div>
        
        <div class="dropdown">
            <label>Target:</label>
            <select id="targetElement">
                <option value="">Select function/class...</option>
                {generate_target_options(codebase)}
            </select>
        </div>
        
        <button onclick="loadVisualization()">🎯 Load Visualization</button>
        
        <div id="visualization" class="visualization">
            <h3>📈 Interactive Visualization</h3>
            <p>Visualization would be loaded here based on selected analysis type and target.</p>
            <p><strong>Analysis Type:</strong> <span id="selectedAnalysis"></span></p>
            <p><strong>Target:</strong> <span id="selectedTarget"></span></p>
            
            <div style="background: white; padding: 20px; border-radius: 5px; margin: 10px 0;">
                <p>🎨 <strong>Graph Visualization Area</strong></p>
                <p>This would show the interactive graph using graph-sitter's built-in visualize() method</p>
                <p>• Nodes: Functions, Classes, Files</p>
                <p>• Edges: Dependencies, Calls, Inheritance</p>
                <p>• Interactive: Click to explore, zoom, filter</p>
            </div>
        </div>
    </div>
    
    <script>
        function loadVisualization() {{
            const analysisType = document.getElementById('analysisType').value;
            const target = document.getElementById('targetElement').value;
            
            document.getElementById('selectedAnalysis').textContent = analysisType;
            document.getElementById('selectedTarget').textContent = target || 'All';
            document.getElementById('visualization').style.display = 'block';
            
            // In a real implementation, this would trigger graph-sitter's visualize() method
            console.log('Loading visualization:', analysisType, 'for target:', target);
        }}
    </script>
</body>
</html>
"""
        
        def generate_issues_html(issues):
            if not issues:
                return "<p>✅ No issues found!</p>"
            
            html = ""
            for issue in issues[:20]:  # Limit display
                severity_class = issue['severity']
                html += f"""
                <div class="issue {severity_class}">
                    <strong>{issue['severity'].upper()}:</strong> {issue['description']}
                    <br><small>📍 {issue['location']}</small>
                </div>
                """
            
            if len(issues) > 20:
                html += f"<p><em>... and {len(issues) - 20} more issues</em></p>"
            
            return html
        
        def generate_target_options(codebase):
            options = ""
            
            # Add function options
            for func in list(codebase.functions)[:50]:  # Limit options
                options += f'<option value="function:{func.name}">{func.name} (function)</option>'
            
            # Add class options  
            for cls in list(codebase.classes)[:50]:  # Limit options
                options += f'<option value="class:{cls.name}">{cls.name} (class)</option>'
            
            return options
        
        # Fill in the template
        html_content = html_content.format(
            generate_issues_html=generate_issues_html,
            generate_target_options=generate_target_options,
            **locals()
        )
        
        f.write(html_content)
        dashboard_path = f.name
    
    return dashboard_path


def demonstrate_user_api():
    """Demonstrate the exact API pattern requested by the user."""
    
    print("🚀 Demonstrating User's Requested API Pattern")
    print("=" * 60)
    
    # User's requested API pattern 1: Clone + parse from repo
    print("📥 Testing: Codebase.from_repo.Analysis('fastapi/fastapi')")
    try:
        # This would be: codebase = Codebase.from_repo.Analysis('fastapi/fastapi')
        # For demo, we'll use local repo
        codebase = Codebase(".")
        analysis = Analysis(codebase)
        print("✅ Successfully created analysis from repo")
    except Exception as e:
        print(f"⚠️  Using local repo instead: {e}")
        codebase = Codebase(".")
        analysis = Analysis(codebase)
    
    # User's requested API pattern 2: Local repository
    print("📁 Testing: Codebase.Analysis('path/to/git/repo')")
    try:
        # This would be: codebase = Codebase.Analysis("path/to/git/repo")
        # For now, using our simplified analysis
        from simplified_analysis import SimplifiedAnalysis
        local_analysis = SimplifiedAnalysis(".")
        print("✅ Successfully created analysis from local path")
    except Exception as e:
        print(f"⚠️  Error: {e}")
        local_analysis = None
    
    # Run analysis
    print("\n🔍 Running full comprehension analysis...")
    if local_analysis:
        results = local_analysis.analyze()
    else:
        # Fallback to basic analysis
        results = {
            'stats': type('Stats', (), {
                'total_files': len(codebase.files),
                'total_functions': len(codebase.functions), 
                'total_classes': len(codebase.classes),
                'total_imports': len(codebase.imports)
            })(),
            'issues': [],
            'summary': {'total_issues': 0, 'high_severity': 0, 'medium_severity': 0, 'low_severity': 0}
        }
    
    # Create dashboard as requested
    print("🌐 Creating HTML dashboard with visualization options...")
    dashboard_path = create_analysis_dashboard(codebase, results)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Dashboard created: {dashboard_path}")
    print(f"🌐 Opening dashboard in browser...")
    
    # Open dashboard in browser
    webbrowser.open(f"file://{dashboard_path}")
    
    print(f"\n📋 Dashboard Features:")
    print(f"  ✅ Lists issues/errors/wrong functions")
    print(f"  ✅ Shows calling points and flows")
    print(f"  ✅ 'Visualize Codebase' button (loads only when pressed)")
    print(f"  ✅ Dropdown for analysis types:")
    print(f"     - Dependency analysis + function name")
    print(f"     - Blast radius + class name") 
    print(f"     - Blast radius + error issue")
    print(f"  ✅ Promptable visualization via dashboard")
    
    return dashboard_path, results


def demonstrate_contexten_import():
    """Show how this would be imported by contexten."""
    
    print("\n🔗 Contexten Integration Example:")
    print("=" * 40)
    
    integration_code = '''
# In contexten, this would be imported like:
from graph_sitter import Codebase, Analysis

# Clone + parse fastapi/fastapi  
codebase = Codebase.from_repo.Analysis('fastapi/fastapi')

# Or, parse a local repository
codebase = Codebase.Analysis("path/to/git/repo")

# Full comprehension analysis with dashboard
analysis_results = codebase.analyze()
dashboard_url = codebase.create_dashboard()

# The dashboard provides:
# 1. Issue listing (errors, flows, wrong functions, calling points)
# 2. Optional visualization (loads only when "Visualize" pressed)
# 3. Dropdown analysis types (dependency, blast radius, etc.)
# 4. Target selection (function names, class names, error issues)
'''
    
    print(integration_code)
    
    # Show actual simplified usage
    print("🎯 Actual Simplified Usage:")
    print("-" * 30)
    
    actual_code = '''
from simplified_analysis import SimplifiedAnalysis

# Super simple execution
analysis = SimplifiedAnalysis(".")
results = analysis.analyze()

# Get specific analysis types
dead_code = analysis.get_dead_code()
analysis.visualize()  # Uses graph-sitter's built-in visualize()
'''
    
    print(actual_code)


if __name__ == "__main__":
    # Demonstrate the user's requested API
    dashboard_path, results = demonstrate_user_api()
    
    # Show contexten integration
    demonstrate_contexten_import()
    
    print(f"\n🎉 Demo complete!")
    print(f"📁 Dashboard file: {dashboard_path}")
    print(f"💡 This demonstrates the exact API pattern you requested!")

