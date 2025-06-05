#!/usr/bin/env python3
"""
Unified Dashboard Example - Updated visualization example using the new comprehensive analysis system.

This example shows how the new unified analysis system simplifies codebase visualization
while providing more comprehensive insights than the previous scattered approach.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the new unified system
from graph_sitter.core.codebase import Codebase
from graph_sitter.adapters.analysis.comprehensive_analysis import (
    ComprehensiveAnalysis, 
    analyze_codebase
)
from graph_sitter.adapters.visualizations.html_dashboard import generate_html_dashboard
from graph_sitter.adapters.visualizations.react_dashboard.dashboard_app import create_dashboard_app


def unified_blast_radius_analysis():
    """
    Unified blast radius analysis - replaces the old blast_radius.py approach.
    
    The new system automatically includes blast radius analysis as part of the
    comprehensive analysis, making it much simpler to use.
    """
    print("💥 Unified Blast Radius Analysis")
    print("=" * 50)
    
    # Old way (multiple files, complex setup):
    # from blast_radius import BlastRadiusAnalyzer
    # from dependency_trace import DependencyTracer
    # from method_relationships import MethodAnalyzer
    # analyzer = BlastRadiusAnalyzer(codebase)
    # tracer = DependencyTracer(codebase)
    # method_analyzer = MethodAnalyzer(codebase)
    # ... complex orchestration ...
    
    # New way (single line, comprehensive results):
    codebase = Codebase.from_repo("fastapi/fastapi", language="python")
    result = analyze_codebase(codebase, auto_detect=False)
    
    if result:
        print(f"✅ Comprehensive analysis completed")
        print(f"📊 Health Score: {result.analysis_summary.health_score:.1f}/100")
        
        # The blast radius data is now automatically included
        blast_radius_data = result.visualization_data.get('blast_radius', {})
        print(f"💥 Blast radius analysis included in comprehensive results")
        
        # Generate interactive dashboard with blast radius visualization
        dashboard_path = generate_html_dashboard(result, "unified_blast_radius_dashboard.html")
        print(f"📄 Interactive dashboard: {dashboard_path}")
        
        # Show issues that might affect blast radius
        high_impact_issues = [
            issue for issue in result.issues 
            if issue.severity in ['critical', 'high'] and issue.category in ['error', 'security']
        ]
        
        print(f"🎯 High-impact issues (affect blast radius): {len(high_impact_issues)}")
        for issue in high_impact_issues[:3]:
            print(f"   - {issue.title} ({issue.severity})")
            if issue.file_path:
                print(f"     📁 {issue.file_path}")


def unified_call_trace_analysis():
    """
    Unified call trace analysis - replaces the old call_trace.py approach.
    
    Call graph analysis is now automatically included in the comprehensive analysis.
    """
    print("\n📞 Unified Call Trace Analysis")
    print("=" * 50)
    
    # Old way (separate script, manual setup):
    # from call_trace import CallTraceAnalyzer
    # analyzer = CallTraceAnalyzer(codebase)
    # call_graph = analyzer.build_call_graph()
    # trace_data = analyzer.trace_calls(target_function)
    # ... manual visualization setup ...
    
    # New way (automatic as part of comprehensive analysis):
    codebase = Codebase.from_repo("requests/requests", language="python")
    result = analyze_codebase(codebase, auto_detect=False)
    
    if result:
        print(f"✅ Call graph analysis included automatically")
        
        # Call graph data is now part of the comprehensive result
        call_graph_data = result.call_graph_data
        print(f"📞 Call graph nodes: {len(call_graph_data.get('nodes', []))}")
        print(f"🔗 Call relationships: {len(call_graph_data.get('edges', []))}")
        
        # Function contexts provide detailed call information
        print(f"🔧 Function contexts analyzed: {len(result.function_contexts)}")
        
        # Generate dashboard with call graph visualization
        dashboard_path = generate_html_dashboard(result, "unified_call_trace_dashboard.html")
        print(f"📄 Interactive call graph dashboard: {dashboard_path}")
        
        # Show functions with potential call issues
        call_issues = [
            issue for issue in result.issues 
            if issue.function_name and 'call' in issue.description.lower()
        ]
        print(f"📞 Call-related issues found: {len(call_issues)}")


def unified_dependency_analysis():
    """
    Unified dependency analysis - replaces the old dependency_trace.py approach.
    
    Dependency analysis is now automatically included with circular dependency detection,
    import analysis, and dependency graph generation.
    """
    print("\n🔗 Unified Dependency Analysis")
    print("=" * 50)
    
    # Old way (separate script, limited scope):
    # from dependency_trace import DependencyAnalyzer
    # analyzer = DependencyAnalyzer(codebase)
    # deps = analyzer.analyze_dependencies()
    # circular = analyzer.find_circular_dependencies()
    # ... manual processing ...
    
    # New way (comprehensive dependency analysis):
    codebase = Codebase.from_repo("django/django", language="python")
    result = analyze_codebase(codebase, auto_detect=False)
    
    if result:
        print(f"✅ Dependency analysis completed automatically")
        
        # Dependency analysis is comprehensive and includes:
        dependency_data = result.dependency_analysis
        if dependency_data:
            circular_deps = getattr(dependency_data, 'circular_dependencies', [])
            print(f"🔄 Circular dependencies found: {len(circular_deps)}")
            
            # Show circular dependency issues
            circular_issues = [
                issue for issue in result.issues 
                if 'circular' in issue.title.lower()
            ]
            print(f"⚠️ Circular dependency issues: {len(circular_issues)}")
            for issue in circular_issues[:2]:
                print(f"   - {issue.title}")
        
        # Generate dashboard with dependency visualization
        dashboard_path = generate_html_dashboard(result, "unified_dependency_dashboard.html")
        print(f"📄 Interactive dependency dashboard: {dashboard_path}")


def unified_method_relationships():
    """
    Unified method relationships analysis - replaces the old method_relationships.py approach.
    
    Method and function relationship analysis is now part of the comprehensive system.
    """
    print("\n🔧 Unified Method Relationships Analysis")
    print("=" * 50)
    
    # Old way (separate analysis, limited context):
    # from method_relationships import MethodRelationshipAnalyzer
    # analyzer = MethodRelationshipAnalyzer(codebase)
    # relationships = analyzer.analyze_method_relationships()
    # inheritance = analyzer.analyze_inheritance()
    # ... manual correlation ...
    
    # New way (comprehensive function and method analysis):
    codebase = Codebase.from_repo("flask/flask", language="python")
    result = analyze_codebase(codebase, auto_detect=False)
    
    if result:
        print(f"✅ Method relationships analyzed comprehensively")
        
        # Function contexts provide detailed relationship information
        function_contexts = result.function_contexts
        print(f"🔧 Functions analyzed: {len(function_contexts)}")
        
        # Enhanced analysis includes method relationships
        enhanced_analysis = result.enhanced_analysis
        if enhanced_analysis:
            print(f"📊 Enhanced analysis includes method relationships")
        
        # Show function-related issues
        function_issues = [
            issue for issue in result.issues 
            if issue.function_name or 'function' in issue.description.lower()
        ]
        print(f"🔧 Function-related issues: {len(function_issues)}")
        
        # Generate dashboard with method relationship visualization
        dashboard_path = generate_html_dashboard(result, "unified_method_relationships_dashboard.html")
        print(f"📄 Interactive method relationships dashboard: {dashboard_path}")


def comprehensive_visualization_demo():
    """
    Demonstrate the comprehensive visualization capabilities that replace
    all the individual visualization scripts.
    """
    print("\n🎨 Comprehensive Visualization Demo")
    print("=" * 50)
    
    # Analyze a codebase with the unified system
    codebase = Codebase.from_repo("scikit-learn/scikit-learn", language="python")
    
    # Create analyzer for custom configuration
    analyzer = ComprehensiveAnalysis(codebase, auto_detect=False)
    
    # Run comprehensive analysis
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            analyzer.run_comprehensive_analysis(
                include_visualizations=True,
                generate_dashboard=True
            )
        )
        
        print(f"✅ Comprehensive analysis completed")
        print(f"📊 Analysis Summary:")
        print(f"   - Files: {result.analysis_summary.total_files}")
        print(f"   - Functions: {result.analysis_summary.total_functions}")
        print(f"   - Classes: {result.analysis_summary.total_classes}")
        print(f"   - Issues: {result.analysis_summary.total_issues}")
        print(f"   - Health Score: {result.analysis_summary.health_score:.1f}/100")
        
        # Generate HTML dashboard (replaces all individual visualization files)
        dashboard_path = generate_html_dashboard(result, "comprehensive_visualization_dashboard.html")
        print(f"📄 Comprehensive dashboard: {dashboard_path}")
        
        # Create interactive React dashboard
        dashboard_app = create_dashboard_app(result, port=8001)
        dashboard_url = analyzer.generate_dashboard_url("http://localhost:8001")
        
        print(f"🚀 Interactive dashboard available at: {dashboard_url}")
        print(f"   - Dependency Analysis: {dashboard_url}?viz=dependency")
        print(f"   - Call Graph: {dashboard_url}?viz=callgraph")
        print(f"   - Complexity Heatmap: {dashboard_url}?viz=complexity")
        print(f"   - Blast Radius: {dashboard_url}?viz=blast-radius")
        
        # Save comprehensive results
        results_path = result.save_results("comprehensive_analysis_results.json")
        print(f"💾 Complete results saved: {results_path}")
        
        print("\n🎯 What's New vs. Old Approach:")
        print("   ✅ Single analysis run instead of 4+ separate scripts")
        print("   ✅ Automatic issue detection and categorization")
        print("   ✅ Interactive HTML dashboard with all visualizations")
        print("   ✅ React dashboard with real-time filtering and exploration")
        print("   ✅ Comprehensive health scoring and recommendations")
        print("   ✅ Unified API that's much simpler to use")
        
    finally:
        loop.close()


def main():
    """Run all unified visualization examples."""
    print("🎨 Unified Visualization System Examples")
    print("=" * 80)
    print("This demonstrates how the new unified analysis system replaces")
    print("the previous scattered visualization scripts with a single,")
    print("comprehensive approach that's much easier to use.\n")
    
    try:
        # Run all examples
        unified_blast_radius_analysis()
        unified_call_trace_analysis()
        unified_dependency_analysis()
        unified_method_relationships()
        comprehensive_visualization_demo()
        
        print("\n🎉 All unified visualization examples completed!")
        
        print("\n📈 Benefits of the Unified System:")
        print("   🚀 10x simpler API - one function call vs. multiple scripts")
        print("   🔍 Comprehensive analysis - all types included automatically")
        print("   🎯 Issue detection - automatic identification of problems")
        print("   📊 Health scoring - overall codebase quality assessment")
        print("   🌐 Interactive dashboards - HTML + React visualizations")
        print("   ⚡ Better performance - parallel analysis execution")
        print("   🔧 Easier maintenance - single system vs. scattered scripts")
        
        print("\n📚 Migration Guide:")
        print("   Old: blast_radius.py → New: analyze_codebase() with blast radius included")
        print("   Old: call_trace.py → New: analyze_codebase() with call graph included")
        print("   Old: dependency_trace.py → New: analyze_codebase() with dependency analysis")
        print("   Old: method_relationships.py → New: analyze_codebase() with function contexts")
        print("   Old: Multiple HTML files → New: Single interactive dashboard")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()

