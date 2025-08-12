#!/usr/bin/env python3
"""
Visualization Data Generation for Comprehensive Codebase Analysis
Generates data structures for interactive charts, graphs, and dashboards.
"""

import json
from typing import Dict, List, Any, Optional
from collections import defaultdict
from analysis import AnalysisResults, Issue, IssueSeverity


def generate_visualization_data(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate comprehensive visualization data from analysis results"""
    
    viz_data = {
        "repository_tree": generate_repository_tree(analysis_results),
        "issue_heatmap": generate_issue_heatmap(analysis_results),
        "severity_distribution": generate_severity_distribution(analysis_results),
        "function_complexity": generate_function_complexity_data(analysis_results),
        "dependency_graph": generate_dependency_graph(analysis_results),
        "metrics_dashboard": generate_metrics_dashboard(analysis_results),
        "dead_code_visualization": generate_dead_code_visualization(analysis_results),
        "entry_points_map": generate_entry_points_map(analysis_results)
    }
    
    return viz_data


def generate_repository_tree(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate repository tree structure with issue counts"""
    
    # Group issues by file path
    issues_by_file = defaultdict(lambda: {"critical": 0, "major": 0, "minor": 0})
    
    for severity, issues in analysis_results.issues_by_severity.items():
        for issue in issues:
            filepath = issue.filepath
            issues_by_file[filepath][severity] += 1
    
    # Build tree structure
    tree = {
        "name": "Repository Root",
        "type": "directory",
        "children": [],
        "issues": {"critical": 0, "major": 0, "minor": 0}
    }
    
    # Process each file path
    for filepath, issue_counts in issues_by_file.items():
        parts = filepath.split('/')
        current_node = tree
        
        # Navigate/create directory structure
        for i, part in enumerate(parts[:-1]):  # All but the last part (filename)
            # Look for existing directory
            existing_dir = None
            for child in current_node["children"]:
                if child["name"] == part and child["type"] == "directory":
                    existing_dir = child
                    break
            
            if existing_dir:
                current_node = existing_dir
            else:
                # Create new directory
                new_dir = {
                    "name": part,
                    "type": "directory",
                    "children": [],
                    "issues": {"critical": 0, "major": 0, "minor": 0}
                }
                current_node["children"].append(new_dir)
                current_node = new_dir
        
        # Add the file
        if parts:  # Make sure we have parts
            filename = parts[-1]
            file_node = {
                "name": filename,
                "type": "file",
                "issues": issue_counts,
                "path": filepath
            }
            current_node["children"].append(file_node)
            
            # Bubble up issue counts
            _bubble_up_issues(tree, issue_counts)
    
    return tree


def _bubble_up_issues(node: Dict[str, Any], issue_counts: Dict[str, int]) -> None:
    """Bubble up issue counts to parent directories"""
    if "issues" in node:
        for severity, count in issue_counts.items():
            node["issues"][severity] += count


def generate_issue_heatmap(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate heatmap data for issue distribution"""
    
    heatmap_data = {
        "files": [],
        "severities": ["critical", "major", "minor"],
        "data": []
    }
    
    # Collect unique files with issues
    files_with_issues = set()
    for issues in analysis_results.issues_by_severity.values():
        for issue in issues:
            files_with_issues.add(issue.filepath)
    
    heatmap_data["files"] = sorted(list(files_with_issues))
    
    # Build heatmap matrix
    for filepath in heatmap_data["files"]:
        row = []
        for severity in heatmap_data["severities"]:
            count = sum(1 for issue in analysis_results.issues_by_severity.get(severity, [])
                       if issue.filepath == filepath)
            row.append(count)
        heatmap_data["data"].append(row)
    
    return heatmap_data


def generate_severity_distribution(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate pie chart data for issue severity distribution"""
    
    distribution = {
        "labels": ["Critical", "Major", "Minor"],
        "values": [
            len(analysis_results.issues_by_severity.get("critical", [])),
            len(analysis_results.issues_by_severity.get("major", [])),
            len(analysis_results.issues_by_severity.get("minor", []))
        ],
        "colors": ["#ff4444", "#ff8800", "#ffcc00"]
    }
    
    return distribution


def generate_function_complexity_data(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate scatter plot data for function complexity analysis"""
    
    complexity_data = {
        "functions": [],
        "complexity_scores": [],
        "parameter_counts": [],
        "call_counts": [],
        "labels": []
    }
    
    # Extract function data from most_important_functions
    if "most_calls" in analysis_results.most_important_functions:
        most_calls = analysis_results.most_important_functions["most_calls"]
        complexity_data["functions"].append(most_calls.get("name", "Unknown"))
        complexity_data["complexity_scores"].append(most_calls.get("call_count", 0))
        complexity_data["parameter_counts"].append(0)  # Would need actual parameter data
        complexity_data["call_counts"].append(most_calls.get("call_count", 0))
        complexity_data["labels"].append(f"Most Calls: {most_calls.get('name', 'Unknown')}")
    
    if "most_called" in analysis_results.most_important_functions:
        most_called = analysis_results.most_important_functions["most_called"]
        complexity_data["functions"].append(most_called.get("name", "Unknown"))
        complexity_data["complexity_scores"].append(most_called.get("usage_count", 0))
        complexity_data["parameter_counts"].append(0)  # Would need actual parameter data
        complexity_data["call_counts"].append(0)
        complexity_data["labels"].append(f"Most Called: {most_called.get('name', 'Unknown')}")
    
    return complexity_data


def generate_dependency_graph(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate network graph data for dependencies"""
    
    # Simplified dependency graph based on available data
    nodes = []
    edges = []
    
    # Add entry points as nodes
    for i, entry_point in enumerate(analysis_results.entry_points):
        nodes.append({
            "id": f"entry_{i}",
            "label": entry_point.split("::")[-1] if "::" in entry_point else entry_point,
            "type": "entry_point",
            "size": 20,
            "color": "#4CAF50"
        })
    
    # Add important functions as nodes
    if analysis_results.most_important_functions:
        most_calls = analysis_results.most_important_functions.get("most_calls", {})
        most_called = analysis_results.most_important_functions.get("most_called", {})
        
        if most_calls.get("name"):
            nodes.append({
                "id": "most_calls",
                "label": most_calls["name"],
                "type": "high_complexity",
                "size": 15,
                "color": "#FF9800"
            })
        
        if most_called.get("name"):
            nodes.append({
                "id": "most_called",
                "label": most_called["name"],
                "type": "high_usage",
                "size": 15,
                "color": "#2196F3"
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "layout": "force_directed"
    }


def generate_metrics_dashboard(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate dashboard metrics data"""
    
    dashboard_data = {
        "summary_cards": [],
        "charts": []
    }
    
    # Summary cards
    summary = analysis_results.summary
    dashboard_data["summary_cards"] = [
        {"title": "Total Files", "value": summary.get("total_files", 0), "icon": "📁"},
        {"title": "Total Functions", "value": summary.get("total_functions", 0), "icon": "⚡"},
        {"title": "Total Classes", "value": summary.get("total_classes", 0), "icon": "🏗️"},
        {"title": "Total Issues", "value": summary.get("total_issues", 0), "icon": "🚨"},
        {"title": "Entry Points", "value": summary.get("entry_points", 0), "icon": "🎯"}
    ]
    
    # Halstead metrics chart
    if analysis_results.halstead_metrics:
        dashboard_data["charts"].append({
            "type": "bar",
            "title": "Halstead Complexity Metrics",
            "data": {
                "labels": list(analysis_results.halstead_metrics.keys()),
                "values": list(analysis_results.halstead_metrics.values())
            }
        })
    
    # Issues by severity chart
    dashboard_data["charts"].append({
        "type": "doughnut",
        "title": "Issues by Severity",
        "data": generate_severity_distribution(analysis_results)
    })
    
    return dashboard_data


def generate_dead_code_visualization(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate visualization for dead code analysis"""
    
    # Placeholder for dead code visualization
    # In a real implementation, this would analyze unused functions, classes, etc.
    dead_code_data = {
        "dead_functions": [],
        "unused_imports": [],
        "blast_radius": {},
        "cleanup_suggestions": []
    }
    
    # Analyze issues for potential dead code indicators
    for severity, issues in analysis_results.issues_by_severity.items():
        for issue in issues:
            if "unused" in issue.message.lower():
                dead_code_data["dead_functions"].append({
                    "name": issue.function_name or issue.class_name,
                    "file": issue.filepath,
                    "type": issue.symbol_type,
                    "reason": issue.message
                })
    
    return dead_code_data


def generate_entry_points_map(analysis_results: AnalysisResults) -> Dict[str, Any]:
    """Generate visualization for entry points mapping"""
    
    entry_points_data = {
        "entry_points": [],
        "connections": [],
        "importance_scores": {}
    }
    
    for entry_point in analysis_results.entry_points:
        # Parse entry point information
        if "::" in entry_point:
            file_path, function_name = entry_point.split("::", 1)
        else:
            file_path = entry_point
            function_name = "main"
        
        entry_points_data["entry_points"].append({
            "id": entry_point,
            "file": file_path,
            "function": function_name,
            "type": "entry_point"
        })
        
        # Calculate importance score (simplified)
        importance_score = 10  # Base score for entry points
        entry_points_data["importance_scores"][entry_point] = importance_score
    
    return entry_points_data


def export_visualization_data(viz_data: Dict[str, Any], output_file: str = "visualization_data.json") -> None:
    """Export visualization data to JSON file"""
    
    try:
        with open(output_file, 'w') as f:
            json.dump(viz_data, f, indent=2, default=str)
        print(f"✅ Visualization data exported to {output_file}")
    except Exception as e:
        print(f"❌ Error exporting visualization data: {e}")


if __name__ == "__main__":
    # Test visualization generation
    from analysis import AnalysisResults
    
    # Create sample results for testing
    sample_results = AnalysisResults()
    sample_results.summary = {
        "total_files": 100,
        "total_functions": 500,
        "total_classes": 50,
        "total_issues": 25,
        "entry_points": 5
    }
    
    # Generate visualization data
    viz_data = generate_visualization_data(sample_results)
    
    print("🎨 Generated visualization data:")
    for key, value in viz_data.items():
        print(f"  {key}: {type(value).__name__}")
    
    # Export to file
    export_visualization_data(viz_data)
