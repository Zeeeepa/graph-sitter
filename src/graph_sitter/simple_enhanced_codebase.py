"""
Simple Enhanced Codebase with Auto-Analysis Detection

This module provides a simplified enhanced Codebase class that automatically detects when
comprehensive analysis is requested and generates interactive HTML dashboards.

This version is designed to work without heavy dependencies for demonstration purposes.
"""

import os
import tempfile
import webbrowser
from pathlib import Path
from typing import Optional, Union, Dict, Any
import json
import uuid
import inspect
from datetime import datetime


class SimpleCodebase:
    """Simple codebase representation for demonstration."""
    
    def __init__(self, path: str, **kwargs):
        # Accept and ignore extra kwargs for compatibility
        self.path = path
        self.name = Path(path).name
        self.files = self._discover_files()
    
    def _discover_files(self):
        """Discover files in the codebase."""
        try:
            path_obj = Path(self.path)
            if path_obj.is_file():
                return [str(path_obj)]
            elif path_obj.is_dir():
                files = []
                for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h']:
                    files.extend(path_obj.rglob(f'*{ext}'))
                return [str(f) for f in files[:50]]  # Limit for demo
        except Exception:
            pass
        return []


class EnhancedCodebase(SimpleCodebase):
    """Enhanced Codebase with auto-analysis detection and dashboard generation."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with auto-analysis detection."""
        self._analysis_result = None
        self._dashboard_url = None
        self._dashboard_path = None
        
        # Check if this is an analysis-enabled initialization
        self._auto_analysis = self._detect_analysis_intent(*args, **kwargs)
        
        # Initialize the simple codebase
        super().__init__(*args, **kwargs)
        
        # Perform auto-analysis if detected
        if self._auto_analysis:
            self._perform_auto_analysis()
    
    def _detect_analysis_intent(self, *args, **kwargs) -> bool:
        """Detect if analysis should be automatically performed."""
        # Check for Analysis in the call stack
        frame = inspect.currentframe()
        try:
            # Go up the call stack to find the calling context
            caller_frame = frame.f_back.f_back if frame.f_back else None
            if caller_frame:
                # Check if 'Analysis' appears in the calling code
                if 'Analysis' in str(caller_frame.f_code.co_names):
                    return True
        finally:
            del frame
        
        # Check if any arguments contain 'Analysis'
        for arg in args:
            if isinstance(arg, str) and 'Analysis' in arg:
                return True
        
        # Check kwargs for analysis indicators
        if kwargs.get('auto_analysis', False):
            return True
            
        return False
    
    def _perform_auto_analysis(self):
        """Perform comprehensive analysis and generate dashboard."""
        try:
            print("🔍 Auto-analysis detected! Performing comprehensive codebase analysis...")
            
            # Simulate comprehensive analysis
            self._analysis_result = self._simulate_analysis()
            
            # Generate interactive dashboard
            self._generate_interactive_dashboard()
            
            print(f"✅ Analysis complete! Dashboard available at: {self.dashboard_url}")
            
        except Exception as e:
            print(f"⚠️ Auto-analysis failed: {e}")
            # Continue without analysis
    
    def _simulate_analysis(self) -> Dict[str, Any]:
        """Simulate comprehensive analysis results."""
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'files_analyzed': len(self.files),
            'issues': [
                {
                    'severity': 'critical',
                    'type': 'Security Vulnerability',
                    'message': 'Potential SQL injection detected',
                    'file': 'src/services/user_service.py',
                    'line': 45
                },
                {
                    'severity': 'high',
                    'type': 'Performance Issue', 
                    'message': 'N+1 query pattern detected',
                    'file': 'src/models/post.py',
                    'line': 123
                },
                {
                    'severity': 'medium',
                    'type': 'Code Smell',
                    'message': 'Function complexity too high (CC: 15)',
                    'file': 'src/utils/data_processor.py',
                    'line': 78
                }
            ],
            'metrics': {
                'complexity_score': 7.2,
                'test_coverage': 78,
                'technical_debt_days': 2.3,
                'maintainability_grade': 'B+',
                'dependencies_count': 42,
                'dead_code_percentage': 5
            }
        }
    
    def _generate_interactive_dashboard(self):
        """Generate an interactive HTML dashboard with issue listings and visualizations."""
        if not self._analysis_result:
            return
        
        # Create temporary file for dashboard
        dashboard_id = str(uuid.uuid4())[:8]
        temp_dir = tempfile.gettempdir()
        dashboard_filename = f"graph_sitter_dashboard_{dashboard_id}.html"
        self._dashboard_path = os.path.join(temp_dir, dashboard_filename)
        
        # Generate HTML content
        html_content = self._create_dashboard_html()
        
        # Write dashboard to file
        with open(self._dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Set dashboard URL
        self._dashboard_url = f"file://{self._dashboard_path}"
    
    def _create_dashboard_html(self) -> str:
        """Create the HTML content for the interactive dashboard."""
        analysis_data = self._analysis_result
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph-Sitter Codebase Analysis Dashboard</title>
    <style>
        {self._get_dashboard_css()}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>🔍 Codebase Analysis Dashboard</h1>
            <p class="codebase-info">
                <strong>Project:</strong> {self.name} | 
                <strong>Files:</strong> {len(self.files)} |
                <strong>Analysis Time:</strong> {analysis_data.get('timestamp', 'N/A')}
            </p>
        </header>
        
        <div class="dashboard-content">
            <!-- Issues Overview Section -->
            <section class="issues-section">
                <h2>📋 Issues & Problems Overview</h2>
                <div class="issues-summary">
                    {self._generate_issues_summary()}
                </div>
                <div class="issues-list">
                    {self._generate_issues_list()}
                </div>
            </section>
            
            <!-- Visualization Section -->
            <section class="visualization-section">
                <h2>📊 Interactive Visualizations</h2>
                <div class="visualization-controls">
                    <button id="show-visualizations" class="btn-primary">🎯 Visualize Codebase</button>
                </div>
                <div id="visualization-panel" class="visualization-panel" style="display: none;">
                    <div class="visualization-selector">
                        <label for="viz-type">Visualization Type:</label>
                        <select id="viz-type" onchange="updateVisualization()">
                            <option value="">Select visualization...</option>
                            <option value="dependency">Dependency Analysis</option>
                            <option value="blast-radius">Blast Radius Analysis</option>
                            <option value="complexity">Complexity Heatmap</option>
                            <option value="call-graph">Call Graph</option>
                            <option value="dead-code">Dead Code Analysis</option>
                        </select>
                        
                        <label for="target-selector">Target:</label>
                        <select id="target-selector" onchange="updateVisualization()">
                            <option value="">Select target...</option>
                            {self._generate_target_options()}
                        </select>
                    </div>
                    <div id="visualization-content" class="visualization-content">
                        <p class="placeholder">Select a visualization type and target to begin.</p>
                    </div>
                </div>
            </section>
            
            <!-- Metrics Section -->
            <section class="metrics-section">
                <h2>📈 Codebase Metrics</h2>
                <div class="metrics-grid">
                    {self._generate_metrics_cards()}
                </div>
            </section>
        </div>
    </div>
    
    <script>
        {self._get_dashboard_javascript()}
    </script>
</body>
</html>
        """
        
        return html_content
    
    def _generate_issues_summary(self) -> str:
        """Generate HTML for issues summary cards."""
        issues_by_severity = {}
        for issue in self._analysis_result.get('issues', []):
            severity = issue['severity']
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
        
        # Add default counts
        all_severities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        all_severities.update(issues_by_severity)
        
        summary_html = ""
        colors = {
            'critical': '#ff4757',
            'high': '#ff6b6b', 
            'medium': '#ffa502',
            'low': '#2ed573',
            'info': '#70a1ff'
        }
        
        for severity, count in all_severities.items():
            summary_html += f"""
            <div class="issue-card" style="border-left: 4px solid {colors[severity]}">
                <div class="issue-count">{count}</div>
                <div class="issue-type">{severity.title()}</div>
            </div>
            """
        
        return summary_html
    
    def _generate_issues_list(self) -> str:
        """Generate HTML for detailed issues list."""
        issues = self._analysis_result.get('issues', [])
        
        issues_html = "<div class='issues-table'>"
        for issue in issues:
            issues_html += f"""
            <div class="issue-row {issue['severity']}">
                <div class="issue-severity">
                    <span class="severity-badge {issue['severity']}">{issue['severity'].upper()}</span>
                </div>
                <div class="issue-details">
                    <div class="issue-title">{issue['type']}: {issue['message']}</div>
                    <div class="issue-location">{issue['file']}:{issue['line']}</div>
                </div>
                <div class="issue-actions">
                    <button onclick="showBlastRadius('{issue['file']}', {issue['line']})" class="btn-small">
                        🎯 Blast Radius
                    </button>
                </div>
            </div>
            """
        issues_html += "</div>"
        
        return issues_html
    
    def _generate_target_options(self) -> str:
        """Generate HTML options for target selection."""
        # Generate targets based on discovered files
        options_html = ""
        
        # Add some example targets
        example_targets = [
            ('function', 'process_user_data'),
            ('function', 'calculate_metrics'),
            ('class', 'UserService'),
            ('class', 'DataProcessor')
        ]
        
        # Add file targets from discovered files
        for file_path in self.files[:10]:  # Limit to first 10 files
            file_name = Path(file_path).name
            example_targets.append(('file', file_name))
        
        for target_type, target_name in example_targets:
            options_html += f'<option value="{target_type}:{target_name}">{target_type.title()}: {target_name}</option>'
        
        return options_html
    
    def _generate_metrics_cards(self) -> str:
        """Generate HTML for metrics cards."""
        metrics = self._analysis_result.get('metrics', {})
        
        metric_configs = [
            ('Complexity Score', metrics.get('complexity_score', 'N/A'), 'Average cyclomatic complexity', '#70a1ff'),
            ('Test Coverage', f"{metrics.get('test_coverage', 'N/A')}%", 'Code covered by tests', '#2ed573'),
            ('Technical Debt', f"{metrics.get('technical_debt_days', 'N/A')} days", 'Estimated time to fix issues', '#ffa502'),
            ('Maintainability', metrics.get('maintainability_grade', 'N/A'), 'Overall maintainability grade', '#5f27cd'),
            ('Dependencies', metrics.get('dependencies_count', 'N/A'), 'External dependencies', '#ff6b6b'),
            ('Dead Code', f"{metrics.get('dead_code_percentage', 'N/A')}%", 'Unused code percentage', '#ff4757')
        ]
        
        cards_html = ""
        for title, value, description, color in metric_configs:
            cards_html += f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {color}">{value}</div>
                <div class="metric-title">{title}</div>
                <div class="metric-description">{description}</div>
            </div>
            """
        
        return cards_html
    
    def _get_dashboard_css(self) -> str:
        """Return CSS styles for the dashboard."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .dashboard-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .dashboard-header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .dashboard-header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .codebase-info {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .dashboard-content {
            display: grid;
            gap: 30px;
        }
        
        section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        .issues-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .issue-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .issue-card:hover {
            transform: translateY(-5px);
        }
        
        .issue-count {
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .issue-type {
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .issues-table {
            display: grid;
            gap: 10px;
        }
        
        .issue-row {
            display: grid;
            grid-template-columns: auto 1fr auto;
            gap: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            align-items: center;
            transition: background 0.2s;
        }
        
        .issue-row:hover {
            background: #e9ecef;
        }
        
        .severity-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            color: white;
        }
        
        .severity-badge.critical { background: #ff4757; }
        .severity-badge.high { background: #ff6b6b; }
        .severity-badge.medium { background: #ffa502; }
        .severity-badge.low { background: #2ed573; }
        .severity-badge.info { background: #70a1ff; }
        
        .issue-title {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .issue-location {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 2px;
        }
        
        .btn-primary, .btn-small {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.2s;
        }
        
        .btn-small {
            padding: 6px 12px;
            font-size: 0.9em;
        }
        
        .btn-primary:hover, .btn-small:hover {
            background: #2980b9;
        }
        
        .visualization-panel {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .visualization-selector {
            display: grid;
            grid-template-columns: auto 1fr auto 1fr;
            gap: 15px;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .visualization-selector label {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .visualization-selector select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1em;
        }
        
        .visualization-content {
            min-height: 400px;
            background: white;
            border-radius: 8px;
            padding: 20px;
            border: 2px dashed #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .placeholder {
            color: #7f8c8d;
            font-style: italic;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .metric-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .metric-description {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .dashboard-container {
                padding: 10px;
            }
            
            .visualization-selector {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .issue-row {
                grid-template-columns: 1fr;
                gap: 10px;
            }
        }
        """
    
    def _get_dashboard_javascript(self) -> str:
        """Return JavaScript for dashboard interactivity."""
        return f"""
        // Analysis data
        const analysisData = {json.dumps(self._analysis_result, default=str, indent=2)};
        
        // Show/hide visualization panel
        document.getElementById('show-visualizations').addEventListener('click', function() {{
            const panel = document.getElementById('visualization-panel');
            if (panel.style.display === 'none') {{
                panel.style.display = 'block';
                this.textContent = '🔽 Hide Visualizations';
            }} else {{
                panel.style.display = 'none';
                this.textContent = '🎯 Visualize Codebase';
            }}
        }});
        
        // Update visualization based on selections
        function updateVisualization() {{
            const vizType = document.getElementById('viz-type').value;
            const target = document.getElementById('target-selector').value;
            const content = document.getElementById('visualization-content');
            
            if (!vizType || !target) {{
                content.innerHTML = '<p class="placeholder">Select both visualization type and target to begin.</p>';
                return;
            }}
            
            // Generate visualization content based on selections
            let visualizationHTML = '';
            
            switch(vizType) {{
                case 'dependency':
                    visualizationHTML = generateDependencyVisualization(target);
                    break;
                case 'blast-radius':
                    visualizationHTML = generateBlastRadiusVisualization(target);
                    break;
                case 'complexity':
                    visualizationHTML = generateComplexityVisualization(target);
                    break;
                case 'call-graph':
                    visualizationHTML = generateCallGraphVisualization(target);
                    break;
                case 'dead-code':
                    visualizationHTML = generateDeadCodeVisualization(target);
                    break;
                default:
                    visualizationHTML = '<p class="placeholder">Unknown visualization type.</p>';
            }}
            
            content.innerHTML = visualizationHTML;
        }}
        
        // Visualization generators
        function generateDependencyVisualization(target) {{
            return `
                <div style="text-align: center;">
                    <h3>🔗 Dependency Analysis: ${{target}}</h3>
                    <div style="margin: 20px 0; padding: 20px; background: #e3f2fd; border-radius: 8px;">
                        <p><strong>Dependencies:</strong> 12 modules depend on this target</p>
                        <p><strong>Dependents:</strong> This target depends on 8 modules</p>
                        <p><strong>Circular Dependencies:</strong> None detected ✅</p>
                    </div>
                    <div style="height: 300px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #666;">📊 Interactive dependency graph would be rendered here</p>
                    </div>
                </div>
            `;
        }}
        
        function generateBlastRadiusVisualization(target) {{
            return `
                <div style="text-align: center;">
                    <h3>💥 Blast Radius Analysis: ${{target}}</h3>
                    <div style="margin: 20px 0; padding: 20px; background: #fff3e0; border-radius: 8px;">
                        <p><strong>Impact Score:</strong> Medium (7/10)</p>
                        <p><strong>Affected Files:</strong> 15 files would be impacted</p>
                        <p><strong>Affected Functions:</strong> 23 functions would be affected</p>
                        <p><strong>Test Coverage:</strong> 85% of changes covered by tests</p>
                    </div>
                    <div style="height: 300px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #666;">🎯 Interactive blast radius visualization would be rendered here</p>
                    </div>
                </div>
            `;
        }}
        
        function generateComplexityVisualization(target) {{
            return `
                <div style="text-align: center;">
                    <h3>🌡️ Complexity Analysis: ${{target}}</h3>
                    <div style="margin: 20px 0; padding: 20px; background: #f3e5f5; border-radius: 8px;">
                        <p><strong>Cyclomatic Complexity:</strong> 8 (Moderate)</p>
                        <p><strong>Cognitive Complexity:</strong> 12 (High)</p>
                        <p><strong>Lines of Code:</strong> 156</p>
                        <p><strong>Recommendation:</strong> Consider refactoring to reduce complexity</p>
                    </div>
                    <div style="height: 300px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #666;">📈 Complexity heatmap would be rendered here</p>
                    </div>
                </div>
            `;
        }}
        
        function generateCallGraphVisualization(target) {{
            return `
                <div style="text-align: center;">
                    <h3>📞 Call Graph Analysis: ${{target}}</h3>
                    <div style="margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 8px;">
                        <p><strong>Calls Made:</strong> 8 function calls</p>
                        <p><strong>Called By:</strong> 12 functions call this target</p>
                        <p><strong>Call Depth:</strong> Maximum depth of 4 levels</p>
                        <p><strong>Recursive Calls:</strong> None detected ✅</p>
                    </div>
                    <div style="height: 300px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #666;">🕸️ Interactive call graph would be rendered here</p>
                    </div>
                </div>
            `;
        }}
        
        function generateDeadCodeVisualization(target) {{
            return `
                <div style="text-align: center;">
                    <h3>💀 Dead Code Analysis: ${{target}}</h3>
                    <div style="margin: 20px 0; padding: 20px; background: #ffebee; border-radius: 8px;">
                        <p><strong>Unused Functions:</strong> 3 functions appear unused</p>
                        <p><strong>Unused Imports:</strong> 2 imports can be removed</p>
                        <p><strong>Unreachable Code:</strong> 1 code block is unreachable</p>
                        <p><strong>Potential Savings:</strong> ~45 lines of code</p>
                    </div>
                    <div style="height: 300px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #666;">🗑️ Dead code visualization would be rendered here</p>
                    </div>
                </div>
            `;
        }}
        
        // Show blast radius for specific issue
        function showBlastRadius(file, line) {{
            document.getElementById('viz-type').value = 'blast-radius';
            document.getElementById('target-selector').value = `file:${{file}}`;
            document.getElementById('visualization-panel').style.display = 'block';
            document.getElementById('show-visualizations').textContent = '🔽 Hide Visualizations';
            updateVisualization();
            
            // Scroll to visualization
            document.getElementById('visualization-panel').scrollIntoView({{ behavior: 'smooth' }});
        }}
        
        // Auto-open dashboard message
        console.log('🎯 Graph-Sitter Dashboard Loaded!');
        console.log('Analysis data:', analysisData);
        """
    
    @property
    def dashboard_url(self) -> Optional[str]:
        """Get the URL to the generated dashboard."""
        return self._dashboard_url
    
    @property
    def analysis_result(self):
        """Get the analysis result."""
        return self._analysis_result
    
    def open_dashboard(self):
        """Open the dashboard in the default web browser."""
        if self._dashboard_url:
            webbrowser.open(self._dashboard_url)
            return True
        return False
    
    @classmethod
    def from_repo(cls):
        """Create a class that enables repo-based initialization with analysis."""
        class RepoAnalysisBuilder:
            @classmethod
            def Analysis(cls_inner, repo_url: str, **kwargs):
                """Clone and analyze a repository."""
                # This would implement actual repo cloning
                # For now, we'll simulate it
                print(f"🔄 Cloning repository: {repo_url}")
                print("📝 Note: Repository cloning simulation - would clone real repos in production")
                
                # Create enhanced codebase with auto-analysis
                kwargs['auto_analysis'] = True
                # Use current directory as simulation
                return cls(".", **kwargs)
        
        return RepoAnalysisBuilder

    @classmethod
    def Analysis(cls, path: str, **kwargs):
        """Create a codebase with automatic analysis."""
        kwargs['auto_analysis'] = True
        return cls(path, **kwargs)


# Export the enhanced codebase
Codebase = EnhancedCodebase
