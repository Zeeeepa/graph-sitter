"""
Flask API Server for Enhanced Codebase Analytics
Provides REST endpoints for visualization dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
from pathlib import Path
from dataclasses import asdict
import traceback

from enhanced_analytics import EnhancedCodebaseAnalyzer, analyze_codebase_enhanced
from graph_sitter import Codebase

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
app.config['DEBUG'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables for caching
current_analysis = None
current_analyzer = None


@app.route('/')
def index():
    """Serve the main dashboard"""
    return send_from_directory('../frontend', 'visualization_dashboard.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """
    Analyze a repository and return comprehensive results
    
    Expected JSON payload:
    {
        "repo_path": "owner/repo" or "local/path",
        "language": "python" (optional),
        "commit": "commit_hash" (optional)
    }
    """
    global current_analysis, current_analyzer
    
    try:
        data = request.get_json()
        if not data or 'repo_path' not in data:
            return jsonify({'error': 'repo_path is required'}), 400
        
        repo_path = data['repo_path']
        language = data.get('language', 'python')
        commit = data.get('commit')
        
        print(f"🚀 Starting analysis of: {repo_path}")
        
        # Initialize codebase
        if repo_path.startswith(('http', 'git')) or '/' in repo_path:
            # Remote repository
            if commit:
                codebase = Codebase.from_repo(repo_path, commit=commit, language=language)
            else:
                codebase = Codebase.from_repo(repo_path, language=language)
        else:
            # Local path
            codebase = Codebase.from_path(repo_path, language=language)
        
        # Perform analysis
        analyzer = EnhancedCodebaseAnalyzer(codebase)
        results = analyzer.analyze_complete()
        
        # Cache results
        current_analysis = results
        current_analyzer = analyzer
        
        # Convert to JSON-serializable format
        response_data = {
            'status': 'success',
            'data': {
                'dependency_graph': results.dependency_graph,
                'call_graph': results.call_graph,
                'complexity_heatmap': results.complexity_heatmap,
                'error_blast_radius': results.error_blast_radius,
                'file_tree': asdict(results.file_tree),
                'metrics_summary': results.metrics_summary,
                'errors': [asdict(error) for error in analyzer.errors],
                'fixable_errors_count': len(analyzer.get_fixable_errors())
            }
        }
        
        print(f"✅ Analysis complete! Found {len(analyzer.errors)} issues")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Get list of detected errors"""
    global current_analyzer
    
    if not current_analyzer:
        return jsonify({'error': 'No analysis data available. Run analysis first.'}), 404
    
    try:
        errors = [asdict(error) for error in current_analyzer.errors]
        fixable_errors = [asdict(error) for error in current_analyzer.get_fixable_errors()]
        
        return jsonify({
            'status': 'success',
            'data': {
                'all_errors': errors,
                'fixable_errors': fixable_errors,
                'total_count': len(errors),
                'fixable_count': len(fixable_errors),
                'error_breakdown': current_analyzer.metrics.get('error_breakdown', {})
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/fix-errors', methods=['POST'])
def fix_errors():
    """Apply automatic fixes to detected errors"""
    global current_analyzer
    
    if not current_analyzer:
        return jsonify({'error': 'No analysis data available. Run analysis first.'}), 404
    
    try:
        data = request.get_json()
        error_types = data.get('error_types', []) if data else []
        
        if error_types:
            # Fix specific error types
            print(f"🔧 Fixing specific error types: {error_types}")
            # Filter errors by type and apply fixes
            # This is a placeholder for selective fixing
            results = current_analyzer.apply_auto_fixes()
        else:
            # Fix all auto-fixable errors
            print("🔧 Fixing all auto-fixable errors...")
            results = current_analyzer.apply_auto_fixes()
        
        return jsonify({
            'status': 'success',
            'data': results
        })
        
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/fix-error/<error_type>/<symbol_name>', methods=['POST'])
def fix_specific_error(error_type, symbol_name):
    """Fix a specific error by type and symbol name"""
    global current_analyzer
    
    if not current_analyzer:
        return jsonify({'error': 'No analysis data available. Run analysis first.'}), 404
    
    try:
        print(f"🔧 Fixing {error_type} for symbol: {symbol_name}")
        
        # Find the specific error
        target_error = None
        for error in current_analyzer.errors:
            if error.error_type == error_type and error.symbol_name == symbol_name:
                target_error = error
                break
        
        if not target_error:
            return jsonify({'error': 'Error not found'}), 404
        
        if not target_error.auto_fixable:
            return jsonify({'error': 'Error is not auto-fixable'}), 400
        
        # Apply fix (placeholder implementation)
        success = False
        if error_type == "ImportError":
            success = current_analyzer._fix_import_error(target_error)
        elif error_type == "DeadCode":
            success = current_analyzer._fix_dead_code(target_error)
        
        if success:
            # Remove the error from the list
            current_analyzer.errors.remove(target_error)
            
            return jsonify({
                'status': 'success',
                'message': f'Fixed {error_type} for {symbol_name}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to fix {error_type} for {symbol_name}'
            }), 500
        
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current metrics summary"""
    global current_analysis
    
    if not current_analysis:
        return jsonify({'error': 'No analysis data available. Run analysis first.'}), 404
    
    try:
        return jsonify({
            'status': 'success',
            'data': current_analysis.metrics_summary
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/file-tree', methods=['GET'])
def get_file_tree():
    """Get file tree structure"""
    global current_analysis
    
    if not current_analysis:
        return jsonify({'error': 'No analysis data available. Run analysis first.'}), 404
    
    try:
        return jsonify({
            'status': 'success',
            'data': asdict(current_analysis.file_tree)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/visualizations/<viz_type>', methods=['GET'])
def get_visualization(viz_type):
    """Get specific visualization data"""
    global current_analysis
    
    if not current_analysis:
        return jsonify({'error': 'No analysis data available. Run analysis first.'}), 404
    
    try:
        viz_data = None
        
        if viz_type == 'dependency-graph':
            viz_data = current_analysis.dependency_graph
        elif viz_type == 'call-graph':
            viz_data = current_analysis.call_graph
        elif viz_type == 'complexity-heatmap':
            viz_data = current_analysis.complexity_heatmap
        elif viz_type == 'error-blast-radius':
            viz_data = current_analysis.error_blast_radius
        else:
            return jsonify({'error': f'Unknown visualization type: {viz_type}'}), 400
        
        return jsonify({
            'status': 'success',
            'data': viz_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Enhanced Codebase Analytics API',
        'version': '1.0.0',
        'has_analysis_data': current_analysis is not None
    })


@app.route('/api/demo', methods=['POST'])
def demo_analysis():
    """Demo endpoint with mock data for testing frontend"""
    try:
        # Generate mock analysis data
        mock_data = {
            'dependency_graph': {
                'nodes': [
                    {'id': 'file:main.py', 'label': 'main.py', 'type': 'file', 'group': 'file'},
                    {'id': 'file:utils.py', 'label': 'utils.py', 'type': 'file', 'group': 'file'},
                    {'id': 'file:config.py', 'label': 'config.py', 'type': 'file', 'group': 'file'}
                ],
                'edges': [
                    {'from': 'file:main.py', 'to': 'file:utils.py', 'type': 'import'},
                    {'from': 'file:main.py', 'to': 'file:config.py', 'type': 'import'}
                ],
                'layout': 'hierarchical'
            },
            'call_graph': {
                'nodes': [
                    {'id': 'func:main', 'label': 'main()', 'type': 'function', 'complexity': 5, 'color': '#00ff00', 'size': 20},
                    {'id': 'func:process_data', 'label': 'process_data()', 'type': 'function', 'complexity': 15, 'color': '#ffff00', 'size': 30}
                ],
                'edges': [
                    {'from': 'func:main', 'to': 'func:process_data', 'type': 'calls'}
                ]
            },
            'complexity_heatmap': {
                'data': [
                    {'name': 'main.py', 'avg_complexity': 8.5, 'max_complexity': 15, 'color': '#ffff00'},
                    {'name': 'utils.py', 'avg_complexity': 4.2, 'max_complexity': 8, 'color': '#00ff00'}
                ]
            },
            'error_blast_radius': {
                'nodes': [
                    {'id': 'error:ImportError:0', 'label': 'ImportError: missing_module', 'type': 'error', 'severity': 'high', 'color': '#ff4444', 'size': 20}
                ],
                'edges': []
            },
            'file_tree': {
                'name': 'demo-project',
                'path': '',
                'type': 'directory',
                'children': [
                    {'name': 'main.py', 'path': 'main.py', 'type': 'file', 'lines_of_code': 150, 'error_count': 2, 'complexity_score': 8.5}
                ]
            },
            'metrics_summary': {
                'total_files': 5,
                'total_functions': 12,
                'total_classes': 3,
                'total_lines': 450,
                'average_complexity': 6.8,
                'max_complexity': 15,
                'total_errors': 3,
                'error_breakdown': {'ImportError': 1, 'ComplexityError': 1, 'DeadCode': 1}
            },
            'errors': [
                {
                    'error_type': 'ImportError',
                    'severity': 'high',
                    'message': 'Cannot resolve import: missing_module',
                    'file_path': 'main.py',
                    'line_number': 5,
                    'symbol_name': 'missing_module',
                    'auto_fixable': True,
                    'blast_radius': ['main.py']
                }
            ],
            'fixable_errors_count': 2
        }
        
        return jsonify({
            'status': 'success',
            'data': mock_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("🚀 Starting Enhanced Codebase Analytics API Server...")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🔍 API endpoints:")
    print("  POST /api/analyze - Analyze repository")
    print("  GET  /api/errors - Get detected errors")
    print("  POST /api/fix-errors - Fix auto-fixable errors")
    print("  GET  /api/metrics - Get metrics summary")
    print("  GET  /api/file-tree - Get file tree")
    print("  GET  /api/visualizations/<type> - Get visualization data")
    print("  POST /api/demo - Demo with mock data")
    print("  GET  /api/health - Health check")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

