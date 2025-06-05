#!/usr/bin/env python3
"""
Contexten Integration Example

This example demonstrates how to use the new Analysis functionality
within contexten for automated codebase analysis and reporting.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph_sitter import Codebase


def analyze_repository_for_contexten(repo_path: str) -> dict:
    """
    Analyze a repository and return structured data for contexten.
    
    This function demonstrates the exact API pattern requested:
    - Simple import and usage
    - Comprehensive analysis
    - Structured output for integration
    
    Args:
        repo_path: Path to repository or repo name (owner/repo)
        
    Returns:
        Dictionary with analysis results, dashboard URL, and recommendations
    """
    print(f"🔍 Analyzing repository: {repo_path}")
    
    # Create analysis using the new API
    analysis = Codebase.AnalysisFromPath(repo_path)
    
    # Run comprehensive analysis
    report = analysis.run_comprehensive_analysis()
    
    # Generate dashboard
    dashboard_url = analysis.open_dashboard()
    
    # Get structured results for contexten
    results = {
        'repository': repo_path,
        'health_score': analysis.get_health_score(),
        'dashboard_url': dashboard_url,
        'summary': {
            'total_files': report.summary.get('total_files', 0),
            'total_functions': report.summary.get('total_functions', 0),
            'total_classes': report.summary.get('total_classes', 0),
            'total_issues': len(report.issues)
        },
        'issues_summary': analysis.get_issues_summary(),
        'recommendations': analysis.get_recommendations(),
        'available_visualizations': analysis.visualization_interface.get_available_visualizations()
    }
    
    return results


def main():
    """
    Demonstrate contexten integration patterns.
    """
    print("🤖 Contexten Integration Demo")
    print("=" * 40)
    
    # Example 1: Analyze current repository
    print("\n📊 Analyzing current repository...")
    try:
        results = analyze_repository_for_contexten(".")
        
        print("✅ Analysis completed!")
        print(f"   Health Score: {results['health_score']:.1f}/100")
        print(f"   Files: {results['summary']['total_files']}")
        print(f"   Functions: {results['summary']['total_functions']}")
        print(f"   Classes: {results['summary']['total_classes']}")
        print(f"   Issues: {results['summary']['total_issues']}")
        print(f"   Dashboard: {results['dashboard_url']}")
        
        # Show critical issues
        critical_issues = results['issues_summary'].get('critical_issues', [])
        if critical_issues:
            print(f"\n⚠️  Critical Issues Found: {len(critical_issues)}")
            for issue in critical_issues[:3]:  # Show first 3
                print(f"   - {issue.get('title', 'Unknown issue')}")
        
        # Show recommendations
        recommendations = results['recommendations']
        if recommendations:
            print(f"\n💡 Top Recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"   - {rec}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Show the exact API usage for contexten
    print("\n📋 Contexten Integration Code:")
    print("-" * 30)
    
    integration_code = '''
# In your contexten agent or workflow:

from graph_sitter import Codebase

# Method 1: Analyze any repository
analysis = Codebase.AnalysisFromPath('fastapi/fastapi')
report = analysis.run_comprehensive_analysis()

# Method 2: Chain from existing codebase
codebase = Codebase.from_repo('fastapi/fastapi')
analysis = codebase.Analysis()
report = analysis.run_comprehensive_analysis()

# Get key metrics
health_score = analysis.get_health_score()
issues = analysis.get_issues_summary()
dashboard_url = analysis.open_dashboard()

# Get specific visualizations
dependency_graph = analysis.get_visualization('dependency')
blast_radius = analysis.get_visualization('blast_radius', 'MyClass')
complexity_map = analysis.get_visualization('complexity_heatmap')

# Export results
analysis.export_results('report.json', format='json')
analysis.export_results('report.html', format='html')
'''
    
    print(integration_code)
    
    # Example 3: Demonstrate visualization selection
    print("\n🎨 Visualization Options:")
    print("-" * 30)
    
    try:
        analysis = Codebase.AnalysisFromPath(".")
        viz_types = analysis.visualization_interface.get_available_visualizations()
        
        print("Available visualization types:")
        for viz_type, description in viz_types.items():
            print(f"   {viz_type}: {description}")
        
        print("\nExample usage:")
        print("   # Get dependency analysis")
        print("   dep_viz = analysis.get_visualization('dependency')")
        print("   ")
        print("   # Get blast radius for specific function")
        print("   blast_viz = analysis.get_visualization('blast_radius', 'function_name')")
        print("   ")
        print("   # Get complexity heatmap")
        print("   complexity_viz = analysis.get_visualization('complexity_heatmap')")
        
    except Exception as e:
        print(f"❌ Error getting visualizations: {e}")
    
    print("\n✅ Contexten Integration Demo Complete!")
    print("\nKey Integration Points:")
    print("🔗 Simple import: from graph_sitter import Codebase")
    print("🔗 One-line analysis: Codebase.AnalysisFromPath('repo')")
    print("🔗 Comprehensive reporting with health scores")
    print("🔗 Interactive dashboard generation")
    print("🔗 Flexible visualization system")
    print("🔗 Export capabilities for further processing")


if __name__ == "__main__":
    main()

