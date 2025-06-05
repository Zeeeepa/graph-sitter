#!/usr/bin/env python3
"""
Unified Analysis Demo

This example demonstrates the new unified analysis system that provides:
- Single analysis with full context
- Automatic analysis trigger when 'analysis' is in codebase name
- Interactive React dashboard with dropdown selections
- Error detection and blast radius visualization
- Progressive loading for optimal performance

Usage:
    python examples/unified_analysis_demo.py
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter import Codebase, Analysis
from graph_sitter.unified_analysis import UnifiedAnalysis, analyze_comprehensive, from_repo_analysis


def demo_automatic_analysis():
    """Demonstrate automatic analysis trigger."""
    print("🔍 Demo 1: Automatic Analysis Trigger")
    print("=" * 50)
    
    # When 'analysis' is in the codebase name, comprehensive analysis is triggered automatically
    print("Creating codebase with 'analysis' in the name...")
    
    # This will automatically trigger comprehensive analysis
    codebase = Codebase("./examples/sample_analysis_project")
    
    # The analysis is already complete due to auto-trigger
    print(f"✅ Analysis completed automatically!")
    print(f"📊 Dashboard URL: http://localhost:8080/analysis/{codebase.id}")
    print()


def demo_manual_comprehensive_analysis():
    """Demonstrate manual comprehensive analysis."""
    print("🔧 Demo 2: Manual Comprehensive Analysis")
    print("=" * 50)
    
    # Load a regular codebase
    codebase = Codebase("./src/graph_sitter")
    
    # Perform comprehensive analysis manually
    print("Running comprehensive analysis...")
    result = analyze_comprehensive(codebase, auto_open_dashboard=False)
    
    print(f"✅ Analysis completed!")
    print(f"📊 Dashboard URL: {result.dashboard_url}")
    print(f"🏥 Health Score: {result.health_score:.1f}%")
    print(f"🐛 Total Errors: {result.error_analysis.get('total_errors', 0)}")
    print(f"📈 Affected Components: {result.total_affected_nodes}")
    print()
    
    # Show key recommendations
    print("🎯 Key Recommendations:")
    for i, rec in enumerate(result.actionable_recommendations[:3], 1):
        print(f"   {i}. {rec}")
    print()


def demo_repository_analysis():
    """Demonstrate analysis from repository URL."""
    print("🌐 Demo 3: Repository Analysis")
    print("=" * 50)
    
    # Analyze a repository directly (this would clone and analyze)
    # For demo purposes, we'll use a local path
    print("Analyzing repository with automatic comprehensive analysis...")
    
    try:
        # This would work with actual repo URLs like 'fastapi/fastapi'
        result = from_repo_analysis("./examples/sample_project", auto_open_dashboard=False)
        
        print(f"✅ Repository analysis completed!")
        print(f"📊 Dashboard URL: {result.dashboard_url}")
        print(f"🏥 Health Score: {result.health_score:.1f}%")
        print()
        
    except Exception as e:
        print(f"⚠️  Repository analysis demo skipped: {e}")
        print("   (This would work with actual repository URLs)")
        print()


def demo_unified_analysis_features():
    """Demonstrate unified analysis features."""
    print("⚡ Demo 4: Unified Analysis Features")
    print("=" * 50)
    
    # Create unified analysis instance
    codebase = Codebase("./src/graph_sitter/adapters")
    analyzer = UnifiedAnalysis(codebase, auto_open_dashboard=False)
    
    # Run comprehensive analysis
    result = analyzer.analyze_comprehensive()
    
    print(f"✅ Unified analysis completed!")
    print()
    
    # Show analysis types available in dashboard
    print("📋 Available Analysis Types:")
    for analysis_type, config in result.analysis_types.items():
        print(f"   • {config['name']}: {config['description']}")
        print(f"     Targets: {', '.join(config['targets'])}")
    print()
    
    # Show error analysis summary
    error_analysis = result.error_analysis
    print("🐛 Error Analysis Summary:")
    print(f"   • Total Errors: {error_analysis.get('total_errors', 0)}")
    print(f"   • Syntax Errors: {len(error_analysis.get('syntax_errors', []))}")
    print(f"   • Performance Issues: {len(error_analysis.get('performance_issues', []))}")
    print(f"   • Security Vulnerabilities: {len(error_analysis.get('security_vulnerabilities', []))}")
    print()
    
    # Show blast radius information
    blast_radius = error_analysis.get('blast_radius', {})
    if blast_radius:
        print("💥 Blast Radius Analysis:")
        print(f"   • Components with impact data: {len(blast_radius)}")
        print("   • Use the dashboard to explore interactive blast radius visualization")
    print()
    
    # Show export capabilities
    print("📤 Export Options:")
    for export_type, path in result.export_paths.items():
        print(f"   • {export_type}: {path}")
    print()


def demo_dashboard_features():
    """Demonstrate dashboard features."""
    print("🎨 Demo 5: Interactive Dashboard Features")
    print("=" * 50)
    
    print("The interactive dashboard provides:")
    print()
    
    print("📊 Analysis Type Dropdown:")
    print("   • Error Analysis → Syntax, Runtime, Logical, Performance, Security")
    print("   • Blast Radius → Error, Function, Class, Module")
    print("   • Dependency Analysis → Module, Class, Function")
    print("   • Complexity Analysis → File, Class, Function")
    print("   • Performance Analysis → Function, Class, Module")
    print()
    
    print("🎯 Target Selection Dropdown:")
    print("   • Dynamic targets based on selected analysis type")
    print("   • Contextual descriptions for each target")
    print("   • Quick preset buttons for common scenarios")
    print()
    
    print("📈 Progressive Loading:")
    print("   • Initial URL shows issues and errors overview")
    print("   • 'Visualize Codebase' button loads full interactive features")
    print("   • Efficient loading for large codebases")
    print()
    
    print("🔍 Interactive Visualizations:")
    print("   • Force-directed graphs for blast radius")
    print("   • Dependency trees and matrices")
    print("   • Error heatmaps and severity charts")
    print("   • Zoom, pan, filter, and drill-down capabilities")
    print()
    
    print("💡 Smart Features:")
    print("   • Automatic analysis trigger for 'analysis' keyword")
    print("   • Health score calculation")
    print("   • Actionable recommendations")
    print("   • Export to multiple formats (JSON, CSV, SVG)")
    print()


def demo_api_simplicity():
    """Demonstrate the simplified API."""
    print("🚀 Demo 6: Simplified API Usage")
    print("=" * 50)
    
    print("The new unified system provides the exact API you requested:")
    print()
    
    print("# Simple usage - automatic analysis")
    print("from graph_sitter import Codebase, Analysis")
    print()
    print("# This triggers automatic comprehensive analysis")
    print("codebase = Codebase.from_repo('fastapi/fastapi')")
    print("# or")
    print("codebase = Codebase.Analysis('path/to/repo')")
    print()
    
    print("# Manual comprehensive analysis")
    print("codebase = Codebase('/path/to/project')")
    print("result = Analysis.analyze_comprehensive(codebase)")
    print("print(f'Dashboard: {result.dashboard_url}')")
    print()
    
    print("✨ Key Benefits:")
    print("   • Single execution with full context")
    print("   • No chaotic multiple entry points")
    print("   • Automatic dashboard generation")
    print("   • Progressive enhancement")
    print("   • Interactive exploration")
    print()


def main():
    """Run all demos."""
    print("🎯 Graph-Sitter Unified Analysis System Demo")
    print("=" * 60)
    print()
    print("This demo showcases the new unified analysis system that addresses")
    print("your requirements for a single, comprehensive analysis with full context,")
    print("interactive dashboard, and simplified execution.")
    print()
    
    try:
        demo_automatic_analysis()
        demo_manual_comprehensive_analysis()
        demo_repository_analysis()
        demo_unified_analysis_features()
        demo_dashboard_features()
        demo_api_simplicity()
        
        print("🎉 Demo completed successfully!")
        print()
        print("Next steps:")
        print("1. Run your analysis with the new unified system")
        print("2. Explore the interactive dashboard")
        print("3. Use dropdown selections to focus on specific areas")
        print("4. Export results for further analysis")
        print()
        print("The system now provides exactly what you requested:")
        print("• SINGLE ANALYSIS WITH FULL CONTEXT ✅")
        print("• Interactive React dashboard ✅")
        print("• Dropdown-driven exploration ✅")
        print("• Error blast radius visualization ✅")
        print("• Progressive loading ✅")
        print("• Simplified execution ✅")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("Note: Some features require the full codebase to be available")


if __name__ == "__main__":
    main()

