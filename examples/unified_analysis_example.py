#!/usr/bin/env python3
"""
Unified Analysis Example - Demonstrates the new simplified API for comprehensive codebase analysis.

This example shows how to use the new unified analysis system that automatically detects
when analysis should be triggered and provides comprehensive results with interactive dashboards.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the new unified analysis system
from graph_sitter.core.codebase import Codebase
from graph_sitter.adapters.analysis.comprehensive_analysis import (
    ComprehensiveAnalysis, 
    analyze_codebase, 
    quick_analysis
)
from graph_sitter.adapters.visualizations.html_dashboard import generate_html_dashboard
from graph_sitter.adapters.visualizations.react_dashboard.dashboard_app import create_dashboard_app


def example_1_simple_analysis():
    """Example 1: Simple analysis with automatic detection."""
    print("🔍 Example 1: Simple Analysis with Auto-Detection")
    print("=" * 60)
    
    # The new API automatically detects if analysis should be triggered
    # based on repository name, directory structure, or file names
    codebase = Codebase.from_repo("fastapi/fastapi", language="python")
    
    # This will automatically detect that comprehensive analysis should be run
    # and return a complete analysis result with issues, visualizations, and dashboard
    result = analyze_codebase(codebase, auto_detect=True)
    
    if result:
        print(f"✅ Analysis completed for {result.codebase_name}")
        print(f"📊 Health Score: {result.analysis_summary.health_score:.1f}/100")
        print(f"🚨 Total Issues: {result.analysis_summary.total_issues}")
        print(f"   - Critical: {result.analysis_summary.critical_issues}")
        print(f"   - High: {result.analysis_summary.high_issues}")
        print(f"   - Medium: {result.analysis_summary.medium_issues}")
        print(f"   - Low: {result.analysis_summary.low_issues}")
        
        # Generate HTML dashboard
        dashboard_path = generate_html_dashboard(result, "fastapi_analysis_dashboard.html")
        print(f"📄 HTML Dashboard: {dashboard_path}")
        
        # Save detailed results
        results_path = result.save_results("fastapi_analysis_results.json")
        print(f"💾 Results saved: {results_path}")
    else:
        print("ℹ️ Auto-detection did not trigger analysis (no 'analysis' keywords found)")


def example_2_forced_analysis():
    """Example 2: Force analysis regardless of auto-detection."""
    print("\n🔍 Example 2: Forced Comprehensive Analysis")
    print("=" * 60)
    
    # Force analysis even if auto-detection doesn't trigger
    codebase = Codebase.from_repo("django/django", language="python")
    
    # Create analyzer with auto_detect=False to force analysis
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
        
        print(f"✅ Forced analysis completed for {result.codebase_name}")
        print(f"📊 Analysis Duration: {result.analysis_summary.analysis_duration:.2f}s")
        print(f"📁 Files Analyzed: {result.analysis_summary.total_files}")
        print(f"🔧 Functions Found: {result.analysis_summary.total_functions}")
        print(f"🏗️ Classes Found: {result.analysis_summary.total_classes}")
        
        # Show top issues
        print("\n🚨 Top Issues:")
        for i, issue in enumerate(result.issues[:5], 1):
            print(f"   {i}. [{issue.severity.upper()}] {issue.title}")
            if issue.file_path:
                print(f"      📁 {issue.file_path}")
            if issue.fix_suggestion:
                print(f"      💡 {issue.fix_suggestion}")
        
    finally:
        loop.close()


def example_3_analysis_with_keyword_detection():
    """Example 3: Analysis triggered by keyword detection."""
    print("\n🔍 Example 3: Analysis with Keyword Detection")
    print("=" * 60)
    
    # This repository name contains 'analysis' so it should trigger automatically
    try:
        result = quick_analysis("your-org/codebase-analysis-tool", language="python")
        
        if result:
            print(f"✅ Auto-triggered analysis for repository with 'analysis' in name")
            print(f"🎯 Detection worked! Analysis completed.")
            
            # Show analysis summary
            summary = result.analysis_summary
            print(f"📊 Summary:")
            print(f"   - Health Score: {summary.health_score:.1f}/100")
            print(f"   - Total Issues: {summary.total_issues}")
            print(f"   - Analysis Time: {summary.analysis_duration:.2f}s")
            
        else:
            print("❌ Analysis was not triggered (repository might not exist)")
            
    except Exception as e:
        print(f"ℹ️ Could not analyze repository (might not exist): {e}")
        print("   This is expected for demo purposes")


def example_4_interactive_dashboard():
    """Example 4: Launch interactive React dashboard."""
    print("\n🔍 Example 4: Interactive React Dashboard")
    print("=" * 60)
    
    # Analyze a real repository
    codebase = Codebase.from_repo("requests/requests", language="python")
    result = analyze_codebase(codebase, auto_detect=False)  # Force analysis
    
    if result:
        print(f"✅ Analysis completed for {result.codebase_name}")
        
        # Generate HTML dashboard
        html_path = generate_html_dashboard(result, "requests_dashboard.html")
        print(f"📄 HTML Dashboard generated: {html_path}")
        
        # Create and start React dashboard server
        print("🚀 Starting interactive React dashboard server...")
        dashboard_app = create_dashboard_app(result, port=8000)
        
        print("🌐 Dashboard available at:")
        print(f"   - HTML Dashboard: file://{Path(html_path).absolute()}")
        print(f"   - React Dashboard: http://localhost:8000")
        print(f"   - API Endpoint: http://localhost:8000/api/analysis/{result.codebase_id}")
        
        # In a real scenario, you would run the server:
        # dashboard_app.run(debug=True)
        print("   (Server not started in example - uncomment dashboard_app.run() to start)")


def example_5_custom_analysis_pipeline():
    """Example 5: Custom analysis with specific components."""
    print("\n🔍 Example 5: Custom Analysis Pipeline")
    print("=" * 60)
    
    # Create codebase
    codebase = Codebase.from_repo("flask/flask", language="python")
    
    # Create custom analyzer
    analyzer = ComprehensiveAnalysis(codebase, auto_detect=False)
    
    # Check what would trigger auto-detection
    would_trigger = analyzer.should_trigger_analysis()
    print(f"🤖 Auto-detection would trigger: {would_trigger}")
    
    # Run analysis with custom settings
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            analyzer.run_comprehensive_analysis(
                include_visualizations=True,
                generate_dashboard=True
            )
        )
        
        print(f"✅ Custom analysis completed")
        
        # Filter issues by severity
        critical_issues = result.get_issues_by_severity('critical')
        security_issues = result.get_issues_by_category('security')
        
        print(f"🔥 Critical Issues: {len(critical_issues)}")
        print(f"🔒 Security Issues: {len(security_issues)}")
        
        # Show function contexts
        print(f"🔧 Function Contexts Analyzed: {len(result.function_contexts)}")
        for context in result.function_contexts[:3]:
            print(f"   - {context.function_name}")
        
        # Generate dashboard URL
        dashboard_url = analyzer.generate_dashboard_url("http://localhost:8000")
        print(f"🌐 Dashboard URL: {dashboard_url}")
        
    finally:
        loop.close()


def main():
    """Run all examples."""
    print("🎯 Unified Analysis System Examples")
    print("=" * 80)
    print("This demonstrates the new simplified API for comprehensive codebase analysis.")
    print("The system automatically detects when analysis should be triggered and provides")
    print("comprehensive results with interactive dashboards.\n")
    
    try:
        # Run examples
        example_1_simple_analysis()
        example_2_forced_analysis()
        example_3_analysis_with_keyword_detection()
        example_4_interactive_dashboard()
        example_5_custom_analysis_pipeline()
        
        print("\n🎉 All examples completed!")
        print("\n📚 Key Features Demonstrated:")
        print("   ✅ Automatic analysis detection based on keywords")
        print("   ✅ Comprehensive issue identification and categorization")
        print("   ✅ HTML dashboard generation with issue listings")
        print("   ✅ Interactive React dashboard with visualizations")
        print("   ✅ Simplified API that consolidates all analysis types")
        print("   ✅ Customizable analysis pipelines")
        
        print("\n🚀 Next Steps:")
        print("   1. Open the generated HTML dashboards in your browser")
        print("   2. Start the React dashboard server for interactive exploration")
        print("   3. Use the API endpoints for custom integrations")
        print("   4. Explore the saved JSON results for detailed analysis data")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n❌ Error running examples: {e}")
        print("   This might be due to network issues or repository access.")
        print("   Try running individual examples or check your internet connection.")


if __name__ == "__main__":
    main()

