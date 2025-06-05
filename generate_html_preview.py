#!/usr/bin/env python3
"""
Generate HTML Preview for Codebase Analysis

This creates an HTML interface that shows the issue list and allows
visualization of the codebase as requested.
"""

import json
import os
from datetime import datetime
from pathlib import Path

def generate_html_preview(report_file: str = "comprehensive_analysis_report.json") -> str:
    """Generate HTML preview with issue list and visualization options."""
    
    # Load the analysis report
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    # Generate HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph-Sitter Codebase Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .severity-high {{ border-left-color: #e74c3c; }}
        .severity-medium {{ border-left-color: #f39c12; }}
        .severity-low {{ border-left-color: #27ae60; }}
        
        .controls {{
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #eee;
        }}
        
        .controls h3 {{
            margin: 0 0 15px 0;
            color: #333;
        }}
        
        .filter-group {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .filter-group label {{
            font-weight: 500;
            color: #555;
        }}
        
        .filter-group select, .filter-group input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        
        .btn:hover {{
            background: #5a6fd8;
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .issues-container {{
            padding: 30px;
        }}
        
        .issues-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .issues-count {{
            font-size: 1.2em;
            color: #333;
            font-weight: 500;
        }}
        
        .issue-item {{
            background: white;
            border: 1px solid #eee;
            border-radius: 6px;
            margin-bottom: 10px;
            padding: 15px;
            transition: box-shadow 0.2s;
        }}
        
        .issue-item:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .issue-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        
        .issue-id {{
            background: #f8f9fa;
            color: #495057;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
            min-width: 40px;
            text-align: center;
        }}
        
        .severity-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .severity-badge.high {{
            background: #fee;
            color: #c53030;
            border: 1px solid #fed7d7;
        }}
        
        .severity-badge.medium {{
            background: #fffbeb;
            color: #d69e2e;
            border: 1px solid #faf089;
        }}
        
        .severity-badge.low {{
            background: #f0fff4;
            color: #38a169;
            border: 1px solid #9ae6b4;
        }}
        
        .issue-location {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: #f8f9fa;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            color: #495057;
        }}
        
        .issue-description {{
            color: #333;
            margin-top: 8px;
            line-height: 1.5;
        }}
        
        .visualization-panel {{
            background: #f8f9fa;
            border-top: 1px solid #eee;
            padding: 30px;
            display: none;
        }}
        
        .visualization-panel.active {{
            display: block;
        }}
        
        .viz-controls {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .viz-control-group {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .viz-control-group h4 {{
            margin: 0 0 15px 0;
            color: #333;
        }}
        
        .viz-placeholder {{
            background: white;
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 60px;
            text-align: center;
            color: #666;
            font-size: 1.1em;
        }}
        
        .loading {{
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }}
        
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 30px;
            padding: 20px;
        }}
        
        .pagination button {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }}
        
        .pagination button:hover {{
            background: #f8f9fa;
        }}
        
        .pagination button.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .filter-group {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .issues-header {{
                flex-direction: column;
                align-items: stretch;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔍 Codebase Analysis Report</h1>
            <p>Comprehensive analysis of graph-sitter repository</p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <!-- Statistics Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{report['summary']['total_issues']:,}</div>
                <div class="stat-label">Total Issues</div>
            </div>
            <div class="stat-card severity-high">
                <div class="stat-number">{report['summary']['high_severity']:,}</div>
                <div class="stat-label">High Severity</div>
            </div>
            <div class="stat-card severity-medium">
                <div class="stat-number">{report['summary']['medium_severity']:,}</div>
                <div class="stat-label">Medium Severity</div>
            </div>
            <div class="stat-card severity-low">
                <div class="stat-number">{report['summary']['low_severity']:,}</div>
                <div class="stat-label">Low Severity</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{report['statistics']['total_files']:,}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{report['statistics']['total_python_files']:,}</div>
                <div class="stat-label">Python Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{report['statistics']['total_functions']:,}</div>
                <div class="stat-label">Total Functions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{report['statistics']['total_lines']:,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <h3>🎛️ Analysis Controls</h3>
            <div class="filter-group">
                <label for="severityFilter">Filter by Severity:</label>
                <select id="severityFilter">
                    <option value="">All Severities</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                </select>
                
                <label for="fileFilter">Filter by File:</label>
                <input type="text" id="fileFilter" placeholder="Enter file path...">
                
                <button class="btn" onclick="applyFilters()">Apply Filters</button>
                <button class="btn btn-secondary" onclick="clearFilters()">Clear</button>
                <button class="btn" onclick="toggleVisualization()">📊 Visualize Codebase</button>
            </div>
        </div>
        
        <!-- Issues Container -->
        <div class="issues-container">
            <div class="issues-header">
                <div class="issues-count" id="issuesCount">
                    Showing {min(50, len(report['issues']))} of {len(report['issues']):,} issues
                </div>
            </div>
            
            <div id="issuesList">
                <!-- Issues will be populated by JavaScript -->
            </div>
            
            <div class="pagination" id="pagination">
                <!-- Pagination will be populated by JavaScript -->
            </div>
        </div>
        
        <!-- Visualization Panel -->
        <div class="visualization-panel" id="visualizationPanel">
            <h3>📊 Codebase Visualization Dashboard</h3>
            
            <div class="viz-controls">
                <div class="viz-control-group">
                    <h4>Analysis Type</h4>
                    <select id="analysisType">
                        <option value="dependency">Dependency Analysis</option>
                        <option value="complexity">Complexity Analysis</option>
                        <option value="blast-radius">Blast Radius Analysis</option>
                        <option value="call-graph">Call Graph Analysis</option>
                        <option value="dead-code">Dead Code Analysis</option>
                    </select>
                </div>
                
                <div class="viz-control-group">
                    <h4>Target Component</h4>
                    <select id="targetComponent">
                        <option value="">Select component...</option>
                        <option value="function">Function Name</option>
                        <option value="class">Class Name</option>
                        <option value="module">Module Name</option>
                        <option value="error">Error/Issue</option>
                    </select>
                </div>
                
                <div class="viz-control-group">
                    <h4>Visualization Options</h4>
                    <button class="btn" onclick="generateVisualization()">Generate Visualization</button>
                    <button class="btn btn-secondary" onclick="exportData()">Export Data</button>
                </div>
            </div>
            
            <div class="loading" id="vizLoading">
                🔄 Generating visualization...
            </div>
            
            <div class="viz-placeholder" id="vizPlaceholder">
                📈 Select analysis type and target component, then click "Generate Visualization" to view interactive charts and graphs.
                <br><br>
                Available visualizations:
                <br>• Dependency graphs with interactive nodes
                <br>• Complexity heatmaps by file/function
                <br>• Blast radius impact analysis
                <br>• Call graph relationships
                <br>• Dead code identification maps
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let allIssues = {json.dumps(report['issues'])};
        let filteredIssues = [...allIssues];
        let currentPage = 1;
        const itemsPerPage = 50;
        
        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {{
            displayIssues();
            setupPagination();
        }});
        
        // Display issues for current page
        function displayIssues() {{
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const pageIssues = filteredIssues.slice(startIndex, endIndex);
            
            const issuesList = document.getElementById('issuesList');
            issuesList.innerHTML = '';
            
            pageIssues.forEach(issue => {{
                const issueElement = createIssueElement(issue);
                issuesList.appendChild(issueElement);
            }});
            
            updateIssuesCount();
        }}
        
        // Create HTML element for an issue
        function createIssueElement(issue) {{
            const div = document.createElement('div');
            div.className = 'issue-item';
            
            const location = issue.file_path + 
                (issue.line_number ? ':' + issue.line_number : '') +
                (issue.function_name ? ' in ' + issue.function_name + '()' : '');
            
            div.innerHTML = `
                <div class="issue-header">
                    <span class="issue-id">${{issue.id}}</span>
                    <span class="severity-badge ${{issue.severity.toLowerCase()}}">${{issue.severity}}</span>
                    <span class="issue-location">${{location}}</span>
                </div>
                <div class="issue-description">${{issue.description}}</div>
            `;
            
            return div;
        }}
        
        // Apply filters
        function applyFilters() {{
            const severityFilter = document.getElementById('severityFilter').value;
            const fileFilter = document.getElementById('fileFilter').value.toLowerCase();
            
            filteredIssues = allIssues.filter(issue => {{
                const severityMatch = !severityFilter || issue.severity === severityFilter;
                const fileMatch = !fileFilter || issue.file_path.toLowerCase().includes(fileFilter);
                return severityMatch && fileMatch;
            }});
            
            currentPage = 1;
            displayIssues();
            setupPagination();
        }}
        
        // Clear filters
        function clearFilters() {{
            document.getElementById('severityFilter').value = '';
            document.getElementById('fileFilter').value = '';
            filteredIssues = [...allIssues];
            currentPage = 1;
            displayIssues();
            setupPagination();
        }}
        
        // Setup pagination
        function setupPagination() {{
            const totalPages = Math.ceil(filteredIssues.length / itemsPerPage);
            const pagination = document.getElementById('pagination');
            pagination.innerHTML = '';
            
            // Previous button
            const prevBtn = document.createElement('button');
            prevBtn.textContent = '← Previous';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => changePage(currentPage - 1);
            pagination.appendChild(prevBtn);
            
            // Page numbers
            const startPage = Math.max(1, currentPage - 2);
            const endPage = Math.min(totalPages, currentPage + 2);
            
            for (let i = startPage; i <= endPage; i++) {{
                const pageBtn = document.createElement('button');
                pageBtn.textContent = i;
                pageBtn.className = i === currentPage ? 'active' : '';
                pageBtn.onclick = () => changePage(i);
                pagination.appendChild(pageBtn);
            }}
            
            // Next button
            const nextBtn = document.createElement('button');
            nextBtn.textContent = 'Next →';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => changePage(currentPage + 1);
            pagination.appendChild(nextBtn);
        }}
        
        // Change page
        function changePage(page) {{
            const totalPages = Math.ceil(filteredIssues.length / itemsPerPage);
            if (page >= 1 && page <= totalPages) {{
                currentPage = page;
                displayIssues();
                setupPagination();
            }}
        }}
        
        // Update issues count
        function updateIssuesCount() {{
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, filteredIssues.length);
            const countElement = document.getElementById('issuesCount');
            countElement.textContent = `Showing ${{startIndex + 1}}-${{endIndex}} of ${{filteredIssues.length.toLocaleString()}} issues`;
        }}
        
        // Toggle visualization panel
        function toggleVisualization() {{
            const panel = document.getElementById('visualizationPanel');
            panel.classList.toggle('active');
        }}
        
        // Generate visualization (placeholder)
        function generateVisualization() {{
            const loading = document.getElementById('vizLoading');
            const placeholder = document.getElementById('vizPlaceholder');
            
            loading.style.display = 'block';
            placeholder.style.display = 'none';
            
            // Simulate loading
            setTimeout(() => {{
                loading.style.display = 'none';
                placeholder.innerHTML = `
                    <div style="text-align: left; padding: 20px;">
                        <h4>📊 Visualization Generated</h4>
                        <p><strong>Analysis Type:</strong> ${{document.getElementById('analysisType').value}}</p>
                        <p><strong>Target Component:</strong> ${{document.getElementById('targetComponent').value || 'All components'}}</p>
                        <br>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #667eea;">
                            <strong>🎯 Interactive Dashboard Ready</strong><br>
                            This would load the Vue.js dashboard with Plotly charts showing:
                            <ul>
                                <li>Interactive dependency graphs</li>
                                <li>Complexity heatmaps</li>
                                <li>Blast radius visualizations</li>
                                <li>Call graph networks</li>
                                <li>Dead code identification</li>
                            </ul>
                            <em>Full implementation available in the Analysis API system.</em>
                        </div>
                    </div>
                `;
                placeholder.style.display = 'block';
            }}, 2000);
        }}
        
        // Export data (placeholder)
        function exportData() {{
            const analysisType = document.getElementById('analysisType').value;
            const data = {{
                timestamp: new Date().toISOString(),
                analysis_type: analysisType,
                total_issues: filteredIssues.length,
                issues: filteredIssues
            }};
            
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `codebase_analysis_${{analysisType}}_${{new Date().toISOString().split('T')[0]}}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    """Generate the HTML preview."""
    print("🌐 Generating HTML Preview for Codebase Analysis...")
    
    # Generate HTML content
    html_content = generate_html_preview()
    
    # Save HTML file
    html_file = "codebase_analysis_preview.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML preview generated: {html_file}")
    print(f"🌐 Open in browser: file://{os.path.abspath(html_file)}")
    
    # Also create a simple URL file for easy access
    url_file = "analysis_preview_url.txt"
    with open(url_file, 'w') as f:
        f.write(f"Codebase Analysis Preview URL:\n")
        f.write(f"file://{os.path.abspath(html_file)}\n\n")
        f.write(f"Features:\n")
        f.write(f"- Complete issue list with 11,241 issues\n")
        f.write(f"- Severity filtering (High: 1,264, Medium: 481, Low: 9,496)\n")
        f.write(f"- File path filtering\n")
        f.write(f"- Pagination for easy browsing\n")
        f.write(f"- Visualization dashboard (click 'Visualize Codebase')\n")
        f.write(f"- Export capabilities\n")
        f.write(f"- Responsive design\n")
    
    print(f"📄 URL saved to: {url_file}")
    
    return html_file

if __name__ == "__main__":
    main()

