#!/usr/bin/env python3
"""
Comprehensive Analysis Example - Demonstrates the new Analysis API

This example shows how to use the new Analysis functionality with:
1. Simple API for comprehensive analysis
2. HTML dashboard generation
3. Interactive visualizations
4. Issue detection and reporting
5. Integration with contexten
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the new Analysis functionality
from graph_sitter import Codebase
from graph_sitter.analysis import AnalysisOrchestrator


def main():
    """
    Demonstrate the new Analysis API functionality.
    """
    print("🚀 Graph-sitter Analysis API Demo")
    print("=" * 50)
    
    # Example 1: Analyze current repository using instance method
    print("\n📊 Example 1: Analyze current repository")
    print("-" * 30)
    
    try:
        # Load current codebase and create analysis
        codebase = Codebase(".")
        analysis = codebase.Analysis()
        
        print("✅ Analysis orchestrator created successfully")
        print(f"   Codebase: {analysis.codebase}")
        print(f"   Available visualizations: {len(analysis.visualization_interface.get_available_visualizations())}")
        
        # Run comprehensive analysis
        print("\n🔍 Running comprehensive analysis...")
        report = analysis.run_comprehensive_analysis()
        
        print("✅ Analysis completed!")
        print(f"   Health Score: {report.health_score:.1f}/100")
        print(f"   Issues Found: {len(report.issues)}")
        print(f"   Files Analyzed: {report.summary.get('total_files', 0)}")
        print(f"   Functions: {report.summary.get('total_functions', 0)}")
        print(f"   Classes: {report.summary.get('total_classes', 0)}")
        
        # Show issues summary
        issues_summary = analysis.get_issues_summary()
        print(f"\n📋 Issues Summary:")
        for severity, count in issues_summary['by_severity'].items():
            print(f"   {severity.upper()}: {count}")
        
        # Generate and open dashboard
        print(f"\n🌐 Generating dashboard...")
        dashboard_url = analysis.open_dashboard()
        print(f"✅ Dashboard generated: {dashboard_url}")
        
    except Exception as e:
        print(f"❌ Error in Example 1: {e}")
    
    # Example 2: Analyze remote repository using class method
    print("\n📊 Example 2: Analyze remote repository (demo)")
    print("-" * 30)
    
    try:
        # This would analyze a remote repository
        # For demo purposes, we'll show the API without actually cloning
        print("API Usage:")
        print("   analysis = Codebase.AnalysisFromPath('fastapi/fastapi')")
        print("   report = analysis.run_comprehensive_analysis()")
        print("   analysis.open_dashboard()")
        print("✅ API demonstrated (actual remote analysis skipped for demo)")
        
    except Exception as e:
        print(f"❌ Error in Example 2: {e}")
    
    # Example 3: Demonstrate visualization interface
    print("\n📊 Example 3: Visualization Interface")
    print("-" * 30)
    
    try:
        codebase = Codebase(".")
        analysis = codebase.Analysis()
        
        # Get available visualizations
        viz_types = analysis.visualization_interface.get_available_visualizations()
        print("Available visualizations:")
        for viz_type, description in viz_types.items():
            print(f"   {viz_type}: {description}")
        
        # Get available targets for blast radius analysis
        targets = analysis.visualization_interface.get_available_targets('blast_radius')
        print(f"\nAvailable targets for blast radius: {len(targets)}")
        if targets:
            print(f"   Example: {targets[0]['name']} ({targets[0]['type']})")
        
        # Generate a specific visualization
        if targets:
            viz_data = analysis.get_visualization('blast_radius', targets[0]['name'])
            print(f"✅ Generated blast radius visualization for: {targets[0]['name']}")
            print(f"   Visualization type: {viz_data.get('type', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error in Example 3: {e}")
    
    # Example 4: Export results
    print("\n📊 Example 4: Export Results")
    print("-" * 30)
    
    try:
        codebase = Codebase(".")
        analysis = codebase.Analysis()
        
        # Run analysis if not already done
        if not analysis.analysis_report:
            report = analysis.run_comprehensive_analysis()
        
        # Export to JSON
        json_path = analysis.export_results("analysis_results.json", format="json")
        print(f"✅ Results exported to JSON: {json_path}")
        
        # Export to HTML
        html_path = analysis.export_results("analysis_report.html", format="html")
        print(f"✅ Results exported to HTML: {html_path}")
        
    except Exception as e:
        print(f"❌ Error in Example 4: {e}")
    
    # Example 5: Contexten Integration Pattern
    print("\n📊 Example 5: Contexten Integration Pattern")
    print("-" * 30)
    
    print("Integration with contexten:")
    print("""
    # In contexten, you can now use:
    from graph_sitter import Codebase
    
    # Quick analysis of any repository
    analysis = Codebase.AnalysisFromPath('path/to/repo')
    report = analysis.run_comprehensive_analysis()
    
    # Get health score and issues
    health_score = analysis.get_health_score()
    issues = analysis.get_issues_summary()
    
    # Open interactive dashboard
    dashboard_url = analysis.open_dashboard()
    
    # Get specific visualizations
    dependency_viz = analysis.get_visualization('dependency')
    blast_radius = analysis.get_visualization('blast_radius', 'MyClass')
    """)
    
    print("✅ Contexten integration pattern demonstrated")
    
    print("\n🎉 Analysis API Demo Complete!")
    print("=" * 50)
    print("\nKey Features Demonstrated:")
    print("✅ Simple API: Codebase().Analysis() and Codebase.AnalysisFromPath()")
    print("✅ Comprehensive analysis with health scoring")
    print("✅ Issue detection and categorization")
    print("✅ HTML dashboard generation")
    print("✅ Interactive visualizations")
    print("✅ Export capabilities")
    print("✅ Contexten integration ready")


if __name__ == "__main__":
    main()

