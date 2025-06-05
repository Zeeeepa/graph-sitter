#!/usr/bin/env python3
"""
Example demonstrating the new Analysis API for graph-sitter.

This example shows how to use the new unified Analysis interface to perform
comprehensive codebase analysis with automatic report generation.
"""

from graph_sitter import Codebase, Analysis

def main():
    print("🚀 Graph-Sitter Analysis API Example")
    print("=" * 50)
    
    # Example 1: Repository Analysis with auto-run
    print("\n📊 Example 1: Repository Analysis (Auto-run)")
    print("-" * 40)
    
    try:
        # This syntax automatically triggers comprehensive analysis
        analysis = Codebase.from_repo.Analysis('fastapi/fastapi')
        
        print("✅ Analysis completed!")
        print(f"📈 Summary: {analysis.get_summary_metrics()}")
        print(f"🚨 Issues found: {len(analysis.get_all_issues())}")
        print(f"💡 Recommendations: {len(analysis.get_recommendations())}")
        
    except Exception as e:
        print(f"❌ Repository analysis failed: {e}")
    
    # Example 2: Local Repository Analysis
    print("\n📁 Example 2: Local Repository Analysis")
    print("-" * 40)
    
    try:
        # Analyze a local repository
        analysis = Codebase.Analysis("./", auto_run=True)
        
        print("✅ Local analysis completed!")
        
        # Get detailed results
        issues = analysis.get_all_issues()
        print(f"\n🔍 Found {len(issues)} issues:")
        
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  • {issue['type']}: {issue['description']}")
        
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more issues")
        
    except Exception as e:
        print(f"❌ Local analysis failed: {e}")
    
    # Example 3: Manual Analysis with Custom Configuration
    print("\n⚙️ Example 3: Manual Analysis with Custom Config")
    print("-" * 40)
    
    try:
        from graph_sitter.core.analysis import AnalysisConfig
        
        # Create custom configuration
        config = AnalysisConfig(
            include_dead_code=True,
            include_dependencies=True,
            include_call_graph=False,  # Skip call graph for faster analysis
            include_metrics=True,
            generate_html_report=True,
            output_dir="./analysis_output"
        )
        
        # Create analysis instance without auto-run
        analysis = Analysis.from_path("./", config=config)
        
        # Run specific analysis types
        print("🔍 Running custom analysis...")
        results = analysis.run_comprehensive_analysis()
        
        print(f"✅ Custom analysis completed with {len(results)} analyzers!")
        
        # Show analysis types that were run
        for analysis_type, result in results.items():
            issue_count = len(result.issues)
            print(f"  📊 {analysis_type}: {issue_count} issues found")
        
    except Exception as e:
        print(f"❌ Custom analysis failed: {e}")
    
    # Example 4: Analysis with Contexten Integration
    print("\n🔗 Example 4: Contexten Integration")
    print("-" * 40)
    
    try:
        # This shows how contexten would use the Analysis API
        from graph_sitter import Codebase
        
        # Contexten-style usage
        codebase = Codebase.from_repo.Analysis('python/cpython')
        
        print("✅ Contexten-style analysis initiated!")
        print("📄 HTML report and dashboard generated automatically")
        print("🎛️ Interactive visualizations available")
        
    except Exception as e:
        print(f"❌ Contexten integration example failed: {e}")
    
    print("\n🎉 Analysis API examples completed!")
    print("\nKey Features Demonstrated:")
    print("• Codebase.from_repo.Analysis() - Auto-analysis from GitHub")
    print("• Codebase.Analysis() - Local repository analysis")
    print("• Custom configuration options")
    print("• Automatic HTML report generation")
    print("• Interactive dashboard creation")
    print("• Issue detection and recommendations")


if __name__ == "__main__":
    main()
