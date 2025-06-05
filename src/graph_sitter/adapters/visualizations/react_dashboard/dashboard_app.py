"""
React Dashboard Application for Interactive Codebase Visualization.

This module provides a Flask/FastAPI server that serves the React dashboard
and provides API endpoints for interactive visualization components.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from ..analysis.comprehensive_analysis import ComprehensiveAnalysisResult

logger = logging.getLogger(__name__)


class ReactDashboardApp:
    """Flask application for serving the React dashboard."""
    
    def __init__(self, analysis_result: ComprehensiveAnalysisResult, port: int = 8000):
        """
        Initialize the React dashboard application.
        
        Args:
            analysis_result: The comprehensive analysis result to serve
            port: Port to run the server on
        """
        self.analysis_result = analysis_result
        self.port = port
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / "templates"),
                        static_folder=str(Path(__file__).parent / "static"))
        CORS(self.app)
        
        self._setup_routes()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard page."""
            return render_template('dashboard.html', 
                                 codebase_name=self.analysis_result.codebase_name,
                                 codebase_id=self.analysis_result.codebase_id)
        
        @self.app.route('/dashboard/<codebase_id>')
        def dashboard(codebase_id: str):
            """Serve the dashboard for a specific codebase."""
            return render_template('dashboard.html',
                                 codebase_name=self.analysis_result.codebase_name,
                                 codebase_id=codebase_id)
        
        @self.app.route('/api/analysis/<codebase_id>')
        def get_analysis_data(codebase_id: str):
            """Get analysis data for the dashboard."""
            if codebase_id != self.analysis_result.codebase_id:
                return jsonify({'error': 'Codebase not found'}), 404
            
            return jsonify(self.analysis_result.to_dict())
        
        @self.app.route('/api/visualization/<viz_type>')
        def get_visualization_data(viz_type: str):
            """Get data for specific visualization type."""
            target = request.args.get('target', '')
            
            if viz_type == 'dependency':
                return jsonify(self._get_dependency_visualization_data(target))
            elif viz_type == 'callgraph':
                return jsonify(self._get_callgraph_visualization_data(target))
            elif viz_type == 'complexity':
                return jsonify(self._get_complexity_visualization_data(target))
            elif viz_type == 'blast-radius':
                return jsonify(self._get_blast_radius_visualization_data(target))
            else:
                return jsonify({'error': 'Unknown visualization type'}), 400
        
        @self.app.route('/api/issues')
        def get_issues():
            """Get filtered issues."""
            severity = request.args.get('severity', 'all')
            category = request.args.get('category', 'all')
            
            issues = self.analysis_result.issues
            
            if severity != 'all':
                issues = [i for i in issues if i.severity == severity]
            
            if category != 'all':
                issues = [i for i in issues if i.category == category]
            
            return jsonify([issue.__dict__ for issue in issues])
        
        @self.app.route('/api/functions')
        def get_functions():
            """Get function analysis data."""
            return jsonify([context.__dict__ for context in self.analysis_result.function_contexts])
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get metrics data."""
            if self.analysis_result.metrics:
                return jsonify(self.analysis_result.metrics.__dict__)
            return jsonify({})
    
    def _get_dependency_visualization_data(self, target: str) -> Dict[str, Any]:
        """Get dependency visualization data."""
        # This would generate actual dependency graph data
        return {
            'type': 'dependency',
            'target': target,
            'nodes': [
                {'id': 'module1', 'label': 'Module 1', 'type': 'module'},
                {'id': 'module2', 'label': 'Module 2', 'type': 'module'},
                {'id': 'module3', 'label': 'Module 3', 'type': 'module'},
            ],
            'edges': [
                {'source': 'module1', 'target': 'module2', 'type': 'imports'},
                {'source': 'module2', 'target': 'module3', 'type': 'imports'},
            ],
            'layout': 'force-directed'
        }
    
    def _get_callgraph_visualization_data(self, target: str) -> Dict[str, Any]:
        """Get call graph visualization data."""
        return {
            'type': 'callgraph',
            'target': target,
            'nodes': [
                {'id': 'func1', 'label': 'Function 1', 'type': 'function'},
                {'id': 'func2', 'label': 'Function 2', 'type': 'function'},
                {'id': 'func3', 'label': 'Function 3', 'type': 'function'},
            ],
            'edges': [
                {'source': 'func1', 'target': 'func2', 'type': 'calls'},
                {'source': 'func2', 'target': 'func3', 'type': 'calls'},
            ],
            'layout': 'hierarchical'
        }
    
    def _get_complexity_visualization_data(self, target: str) -> Dict[str, Any]:
        """Get complexity heatmap visualization data."""
        return {
            'type': 'complexity',
            'target': target,
            'data': [
                {'file': 'file1.py', 'complexity': 5, 'color': 'green'},
                {'file': 'file2.py', 'complexity': 12, 'color': 'yellow'},
                {'file': 'file3.py', 'complexity': 25, 'color': 'red'},
            ],
            'layout': 'treemap'
        }
    
    def _get_blast_radius_visualization_data(self, target: str) -> Dict[str, Any]:
        """Get blast radius visualization data."""
        return {
            'type': 'blast-radius',
            'target': target,
            'center': target,
            'affected_files': [
                {'file': 'file1.py', 'impact': 'high', 'distance': 1},
                {'file': 'file2.py', 'impact': 'medium', 'distance': 2},
                {'file': 'file3.py', 'impact': 'low', 'distance': 3},
            ],
            'layout': 'radial'
        }
    
    def run(self, debug: bool = False):
        """Run the Flask application."""
        self.logger.info(f"Starting React dashboard server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)


def create_dashboard_app(analysis_result: ComprehensiveAnalysisResult, 
                        port: int = 8000) -> ReactDashboardApp:
    """
    Create and configure the React dashboard application.
    
    Args:
        analysis_result: The comprehensive analysis result to serve
        port: Port to run the server on
        
    Returns:
        Configured ReactDashboardApp instance
    """
    return ReactDashboardApp(analysis_result, port)

