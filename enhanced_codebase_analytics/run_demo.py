#!/usr/bin/env python3
"""
Enhanced Codebase Analytics Demo Runner
Demonstrates the enhanced analytics capabilities with visualization
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from enhanced_analytics import analyze_codebase_enhanced, EnhancedCodebaseAnalyzer
from graph_sitter import Codebase


def run_demo_analysis(repo_path: str = "fastapi/fastapi"):
    """Run a demo analysis and display results"""
    
    print("🚀 Enhanced Codebase Analytics Demo")
    print("=" * 50)
    print(f"📊 Analyzing: {repo_path}")
    print()
    
    try:
        # Perform analysis
        results = analyze_codebase_enhanced(repo_path)
        
        # Display results
        print("📈 ANALYSIS RESULTS")
        print("-" * 30)
        
        # Metrics Summary
        metrics = results.metrics_summary
        print(f"📁 Total Files: {metrics['total_files']}")
        print(f"🔧 Total Functions: {metrics['total_functions']}")
        print(f"📦 Total Classes: {metrics['total_classes']}")
        print(f"📝 Total Lines: {metrics['total_lines']}")
        print(f"🔄 Average Complexity: {metrics['average_complexity']}")
        print(f"⚠️  Max Complexity: {metrics['max_complexity']}")
        print(f"🚨 Total Errors: {metrics['total_errors']}")
        print()
        
        # Error Breakdown
        if metrics.get('error_breakdown'):
            print("🚨 ERROR BREAKDOWN")
            print("-" * 20)
            for error_type, count in metrics['error_breakdown'].items():
                print(f"  {error_type}: {count}")
            print()
        
        # File Tree Summary
        print("🌳 FILE TREE STRUCTURE")
        print("-" * 25)
        print_file_tree(results.file_tree, max_depth=2)
        print()
        
        # Dependency Graph Info
        dep_graph = results.dependency_graph
        print("🔗 DEPENDENCY ANALYSIS")
        print("-" * 25)
        print(f"  Nodes: {len(dep_graph['nodes'])}")
        print(f"  Edges: {len(dep_graph['edges'])}")
        print(f"  Layout: {dep_graph.get('layout', 'N/A')}")
        print()
        
        # Call Graph Info
        call_graph = results.call_graph
        print("📞 CALL GRAPH ANALYSIS")
        print("-" * 25)
        print(f"  Functions: {len(call_graph['nodes'])}")
        print(f"  Call Relationships: {len(call_graph['edges'])}")
        print()
        
        # Complexity Heatmap
        complexity_data = results.complexity_heatmap['data']
        if complexity_data:
            print("🌡️  COMPLEXITY HEATMAP (Top 5)")
            print("-" * 30)
            sorted_files = sorted(complexity_data, key=lambda x: x['avg_complexity'], reverse=True)[:5]
            for file_data in sorted_files:
                print(f"  {file_data['name']}: {file_data['avg_complexity']:.1f} (max: {file_data['max_complexity']})")
            print()
        
        # Error Blast Radius
        error_graph = results.error_blast_radius
        print("💥 ERROR BLAST RADIUS")
        print("-" * 25)
        error_nodes = [node for node in error_graph['nodes'] if node['type'] == 'error']
        affected_files = [node for node in error_graph['nodes'] if node['type'] == 'affected_file']
        print(f"  Error Sources: {len(error_nodes)}")
        print(f"  Affected Files: {len(affected_files)}")
        print()
        
        # Save results to file
        output_file = "analysis_results.json"
        save_results_to_file(results, output_file)
        print(f"💾 Results saved to: {output_file}")
        print()
        
        print("✅ Demo analysis complete!")
        print()
        print("🌐 To view interactive visualizations:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Run API server: python backend/api_server.py")
        print("3. Open browser: http://localhost:5000")
        
        return results
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def print_file_tree(node, level=0, max_depth=3):
    """Print file tree structure with limited depth"""
    if level > max_depth:
        return
    
    indent = "  " * level
    icon = "📁" if node.type == "directory" else "📄"
    
    info_parts = []
    if node.type == "file":
        if node.lines_of_code:
            info_parts.append(f"{node.lines_of_code} lines")
        if node.error_count > 0:
            info_parts.append(f"{node.error_count} errors")
        if node.complexity_score:
            info_parts.append(f"complexity: {node.complexity_score:.1f}")
    
    info_str = f" ({', '.join(info_parts)})" if info_parts else ""
    
    print(f"{indent}{icon} {node.name}{info_str}")
    
    if node.children and level < max_depth:
        for child in node.children[:5]:  # Limit to first 5 children
            print_file_tree(child, level + 1, max_depth)
        
        if len(node.children) > 5:
            print(f"{indent}  ... and {len(node.children) - 5} more")


def save_results_to_file(results, filename):
    """Save analysis results to JSON file"""
    try:
        # Convert results to JSON-serializable format
        from dataclasses import asdict
        
        output_data = {
            'dependency_graph': results.dependency_graph,
            'call_graph': results.call_graph,
            'complexity_heatmap': results.complexity_heatmap,
            'error_blast_radius': results.error_blast_radius,
            'file_tree': asdict(results.file_tree),
            'metrics_summary': results.metrics_summary
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
            
    except Exception as e:
        print(f"⚠️  Warning: Could not save results to file: {str(e)}")


def run_interactive_demo():
    """Run interactive demo with user input"""
    print("🎯 Enhanced Codebase Analytics - Interactive Demo")
    print("=" * 55)
    print()
    
    while True:
        print("Choose an option:")
        print("1. Analyze a GitHub repository (e.g., 'fastapi/fastapi')")
        print("2. Analyze a local directory")
        print("3. Run with default demo repository")
        print("4. Exit")
        print()
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            repo_path = input("Enter GitHub repository (owner/repo): ").strip()
            if repo_path:
                run_demo_analysis(repo_path)
            else:
                print("❌ Invalid repository path")
        
        elif choice == "2":
            local_path = input("Enter local directory path: ").strip()
            if local_path and os.path.exists(local_path):
                run_demo_analysis(local_path)
            else:
                print("❌ Directory not found")
        
        elif choice == "3":
            run_demo_analysis("fastapi/fastapi")
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")
        
        print("\n" + "=" * 55 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run with command line argument
        repo_path = sys.argv[1]
        run_demo_analysis(repo_path)
    else:
        # Run interactive demo
        run_interactive_demo()

