#!/usr/bin/env python3
"""
API Server for Comprehensive Codebase Analysis
Provides REST endpoints for analysis results and visualization data.
"""

import json
import traceback
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from analysis import load_codebase, analyze_codebase, AnalysisResults
from visualize import generate_visualization_data

app = Flask(__name__)


@app.route('/')
def index():
    """API documentation endpoint"""
    return jsonify({
        "message": "Comprehensive Codebase Analysis API",
        "endpoints": {
            "/analyze/<username>/<repo>": "GET - Complete codebase analysis",
            "/visualize/<username>/<repo>": "GET - Interactive visualization data",
            "/health": "GET - Health check"
        },
        "example_usage": [
            "GET /analyze/codegen-sh/graph-sitter",
            "GET /visualize/codegen-sh/graph-sitter"
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "codebase-analysis-api"})


@app.route('/analyze/<username>/<repo>')
def analyze_repo(username: str, repo: str):
    """Analyze a repository and return comprehensive results"""
    try:
        # Construct repo path (assuming local repos)
        repo_path = f"./{repo}" if repo == "graph-sitter" else f"./{username}-{repo}"
        
        if not Path(repo_path).exists():
            return jsonify({
                "error": f"Repository not found: {repo_path}",
                "suggestion": "Make sure the repository is cloned locally"
            }), 404
        
        # Load and analyze codebase
        codebase = load_codebase(repo_path)
        results = analyze_codebase(codebase)
        
        # Convert results to JSON-serializable format
        response_data = {
            "repository": f"{username}/{repo}",
            "analysis_results": {
                "summary": results.summary,
                "most_important_functions": results.most_important_functions,
                "issues_by_severity": {
                    severity: [str(issue) for issue in issues]
                    for severity, issues in results.issues_by_severity.items()
                },
                "halstead_metrics": results.halstead_metrics,
                "entry_points": results.entry_points
            },
            "status": "success"
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "traceback": traceback.format_exc(),
            "repository": f"{username}/{repo}",
            "status": "error"
        }), 500


@app.route('/visualize/<username>/<repo>')
def visualize_repo(username: str, repo: str):
    """Generate visualization data for a repository"""
    try:
        # Construct repo path
        repo_path = f"./{repo}" if repo == "graph-sitter" else f"./{username}-{repo}"
        
        if not Path(repo_path).exists():
            return jsonify({
                "error": f"Repository not found: {repo_path}",
                "suggestion": "Make sure the repository is cloned locally"
            }), 404
        
        # Load and analyze codebase
        codebase = load_codebase(repo_path)
        results = analyze_codebase(codebase)
        
        # Generate visualization data
        viz_data = generate_visualization_data(results)
        
        response_data = {
            "repository": f"{username}/{repo}",
            "visualization_data": viz_data,
            "status": "success"
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            "error": f"Visualization generation failed: {str(e)}",
            "traceback": traceback.format_exc(),
            "repository": f"{username}/{repo}",
            "status": "error"
        }), 500


@app.route('/dashboard/<username>/<repo>')
def dashboard(username: str, repo: str):
    """Interactive dashboard for repository analysis"""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Codebase Analysis Dashboard - {{ repo_name }}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .metrics { display: flex; gap: 20px; flex-wrap: wrap; }
            .metric { background: #e8f4f8; padding: 15px; border-radius: 5px; min-width: 150px; }
            .chart { height: 400px; margin: 20px 0; }
            .error { color: red; background: #ffe6e6; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Codebase Analysis Dashboard</h1>
            <h2>{{ repo_name }}</h2>
        </div>
        
        <div class="section">
            <h3>📊 Loading Analysis...</h3>
            <p>Fetching comprehensive analysis data...</p>
            <div id="loading">⏳ Please wait...</div>
        </div>
        
        <div id="content" style="display: none;">
            <div class="section">
                <h3>📈 Summary Metrics</h3>
                <div class="metrics" id="metrics"></div>
            </div>
            
            <div class="section">
                <h3>🚨 Issues Overview</h3>
                <div class="chart" id="issues-chart"></div>
            </div>
            
            <div class="section">
                <h3>🔧 Most Important Functions</h3>
                <div id="important-functions"></div>
            </div>
            
            <div class="section">
                <h3>📊 Halstead Metrics</h3>
                <div class="chart" id="halstead-chart"></div>
            </div>
        </div>
        
        <script>
            // Fetch analysis data
            fetch('/analyze/{{ username }}/{{ repo }}')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    if (data.status === 'error') {
                        document.getElementById('content').innerHTML = 
                            '<div class="error">Error: ' + data.error + '</div>';
                        return;
                    }
                    
                    const results = data.analysis_results;
                    
                    // Display metrics
                    const metricsDiv = document.getElementById('metrics');
                    Object.entries(results.summary).forEach(([key, value]) => {
                        const metricDiv = document.createElement('div');
                        metricDiv.className = 'metric';
                        metricDiv.innerHTML = '<strong>' + key.replace('_', ' ').toUpperCase() + '</strong><br>' + value;
                        metricsDiv.appendChild(metricDiv);
                    });
                    
                    // Issues chart
                    const issuesData = [{
                        x: ['Critical', 'Major', 'Minor'],
                        y: [
                            results.summary.critical_issues,
                            results.summary.major_issues,
                            results.summary.minor_issues
                        ],
                        type: 'bar',
                        marker: { color: ['#ff4444', '#ff8800', '#ffcc00'] }
                    }];
                    
                    Plotly.newPlot('issues-chart', issuesData, {
                        title: 'Issues by Severity',
                        xaxis: { title: 'Severity' },
                        yaxis: { title: 'Count' }
                    });
                    
                    // Important functions
                    const functionsDiv = document.getElementById('important-functions');
                    const mostCalls = results.most_important_functions.most_calls;
                    const mostCalled = results.most_important_functions.most_called;
                    
                    functionsDiv.innerHTML = 
                        '<p><strong>Makes Most Calls:</strong> ' + mostCalls.name + ' (' + mostCalls.call_count + ' calls)</p>' +
                        '<p><strong>Most Called:</strong> ' + mostCalled.name + ' (' + mostCalled.usage_count + ' usages)</p>';
                    
                    // Halstead metrics chart
                    const halsteadData = [{
                        labels: Object.keys(results.halstead_metrics),
                        values: Object.values(results.halstead_metrics),
                        type: 'pie'
                    }];
                    
                    Plotly.newPlot('halstead-chart', halsteadData, {
                        title: 'Halstead Complexity Metrics'
                    });
                })
                .catch(error => {
                    document.getElementById('loading').innerHTML = 
                        '<div class="error">Failed to load analysis: ' + error + '</div>';
                });
        </script>
    </body>
    </html>
    """
    
    return render_template_string(dashboard_html, 
                                username=username, 
                                repo=repo, 
                                repo_name=f"{username}/{repo}")


if __name__ == '__main__':
    print("🚀 Starting Comprehensive Codebase Analysis API Server")
    print("📍 Available endpoints:")
    print("   GET / - API documentation")
    print("   GET /analyze/<username>/<repo> - Complete analysis")
    print("   GET /visualize/<username>/<repo> - Visualization data")
    print("   GET /dashboard/<username>/<repo> - Interactive dashboard")
    print("   GET /health - Health check")
    print("\n🌐 Example URLs:")
    print("   http://localhost:5000/analyze/codegen-sh/graph-sitter")
    print("   http://localhost:5000/dashboard/codegen-sh/graph-sitter")
    print("   http://localhost:5000/visualize/codegen-sh/graph-sitter")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
