#!/usr/bin/env python3
"""
Comprehensive analysis example with HTML reports and interactive dashboards.

This example demonstrates the full capabilities of the graph-sitter Analysis
system including report generation, visualizations, and dashboard creation.
"""

import os
import tempfile
from pathlib import Path

from graph_sitter import Codebase, Analysis
from graph_sitter.core.analysis import AnalysisConfig
from graph_sitter.adapters.adapter import (
    UnifiedAnalyzer,
    generate_analysis_report,
    analyze_codebase
)


def main():
    print("🔬 Comprehensive Analysis with Reports Example")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("./analysis_reports")
    output_dir.mkdir(exist_ok=True)
    
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    # Example 1: Quick Analysis with Default Reports
    print("\n⚡ Example 1: Quick Analysis with Default Reports")
    print("-" * 50)
    
    try:
        # Generate comprehensive analysis report for current directory
        report_files = generate_analysis_report(
            codebase=Codebase("./"),
            output_dir=str(output_dir / "quick_analysis"),
            title="Graph-Sitter Quick Analysis Report",
            include_dashboard=True
        )
        
        print("✅ Quick analysis completed!")
        for file_type, file_path in report_files.items():
            if isinstance(file_path, str):
                print(f"  📄 {file_type}: {file_path}")
        
    except Exception as e:
        print(f"❌ Quick analysis failed: {e}")
    
    # Example 2: Detailed Analysis with Custom Configuration
    print("\n🔧 Example 2: Detailed Analysis with Custom Config")
    print("-" * 50)
    
    try:
        # Create detailed configuration
        config = AnalysisConfig(
            include_dead_code=True,
            include_dependencies=True,
            include_call_graph=True,
            include_metrics=True,
            include_function_context=True,
            generate_html_report=True,
            generate_interactive_dashboard=True,
            output_dir=str(output_dir / "detailed_analysis"),
            report_title="Detailed Graph-Sitter Analysis"
        )
        
        # Create codebase and analyzer
        codebase = Codebase("./")
        analyzer = UnifiedAnalyzer(codebase, config)
        
        # Run comprehensive analysis
        print("🔍 Running comprehensive analysis...")
        results = analyzer.run_comprehensive_analysis()
        
        # Generate HTML report
        print("📄 Generating HTML report...")
        html_report = analyzer.generate_html_report(
            str(output_dir / "detailed_analysis"),
            "Detailed Analysis Report"
        )
        
        # Create visualizations
        print("📊 Creating visualizations...")
        visualizations = analyzer.create_visualizations(
            str(output_dir / "detailed_analysis" / "visualizations")
        )
        
        print("✅ Detailed analysis completed!")
        print(f"  📄 HTML Report: {html_report}")
        for viz_type, viz_path in visualizations.items():
            print(f"  📊 {viz_type}: {viz_path}")
        
        # Show summary
        summary = analyzer.get_summary()
        print(f"\n📈 Analysis Summary:")
        print(f"  • Analyzers run: {summary['analyzers_run']}")
        print(f"  • Total issues: {summary['total_issues']}")
        print(f"  • Errors: {summary['issues_by_severity']['error']}")
        print(f"  • Warnings: {summary['issues_by_severity']['warning']}")
        print(f"  • Info: {summary['issues_by_severity']['info']}")
        print(f"  • Recommendations: {summary['total_recommendations']}")
        
    except Exception as e:
        print(f"❌ Detailed analysis failed: {e}")
    
    # Example 3: Repository Analysis with Full Pipeline
    print("\n🌐 Example 3: Repository Analysis Pipeline")
    print("-" * 50)
    
    try:
        # Analyze a small public repository
        print("🔍 Analyzing repository...")
        
        # Use the new Analysis API
        analysis = Codebase.from_repo.Analysis('octocat/Hello-World')
        
        print("✅ Repository analysis completed!")
        
        # Get results summary
        summary = analysis.get_summary_metrics()
        issues = analysis.get_all_issues()
        recommendations = analysis.get_recommendations()
        
        print(f"\n📊 Repository Analysis Results:")
        print(f"  • Total issues: {len(issues)}")
        print(f"  • Recommendations: {len(recommendations)}")
        
        # Show top issues
        if issues:
            print(f"\n🚨 Top Issues:")
            for issue in issues[:3]:
                print(f"  • {issue.get('type', 'unknown')}: {issue.get('description', 'No description')}")
        
        # Show top recommendations
        if recommendations:
            print(f"\n💡 Top Recommendations:")
            for rec in recommendations[:3]:
                print(f"  • {rec}")
        
    except Exception as e:
        print(f"❌ Repository analysis failed: {e}")
    
    # Example 4: Interactive Dashboard Demo
    print("\n🎛️ Example 4: Interactive Dashboard Demo")
    print("-" * 50)
    
    try:
        from graph_sitter.adapters.visualizations.dashboard import InteractiveDashboard
        from graph_sitter.adapters.visualizations.interactive import create_default_dashboard
        
        # Create sample analysis results for demo
        codebase = Codebase("./")
        results = analyze_codebase(codebase, analysis_types=['metrics', 'dead_code'])
        
        if results:
            # Create interactive dashboard
            dashboard = InteractiveDashboard()
            dashboard_path = dashboard.create_dashboard(
                results,
                str(output_dir / "interactive_dashboard")
            )
            
            print(f"✅ Interactive dashboard created: {dashboard_path}")
            print("🌐 Open the dashboard in your browser to explore the results!")
            
            # Create default visualization components
            default_viz = create_default_dashboard(results)
            
            # Save as standalone HTML
            standalone_path = output_dir / "interactive_dashboard" / "standalone_visualizations.html"
            with open(standalone_path, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Graph-Sitter Visualizations</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Graph-Sitter Analysis Visualizations</h1>
    {default_viz}
</body>
</html>
                """)
            
            print(f"📊 Standalone visualizations: {standalone_path}")
        
    except Exception as e:
        print(f"❌ Dashboard demo failed: {e}")
    
    # Example 5: Contexten Integration Pattern
    print("\n🔗 Example 5: Contexten Integration Pattern")
    print("-" * 50)
    
    try:
        # This demonstrates how contexten would integrate with the Analysis API
        
        # Step 1: Initialize analysis
        analysis = Codebase.Analysis("./", auto_run=False)
        
        # Step 2: Configure for contexten needs
        analysis.config.generate_html_report = True
        analysis.config.generate_interactive_dashboard = True
        analysis.config.output_dir = str(output_dir / "contexten_integration")
        
        # Step 3: Run analysis
        print("🔍 Running contexten-style analysis...")
        results = analysis.run_comprehensive_analysis()
        
        # Step 4: Extract data for contexten
        contexten_data = {
            'analysis_summary': analysis.get_summary_metrics(),
            'issues': [issue.to_dict() if hasattr(issue, 'to_dict') else issue for issue in analysis.get_all_issues()],
            'recommendations': analysis.get_recommendations(),
            'report_url': f"file://{output_dir}/contexten_integration/analysis_report.html",
            'dashboard_url': f"file://{output_dir}/contexten_integration/interactive_dashboard.html"
        }
        
        print("✅ Contexten integration pattern completed!")
        print(f"📊 Analysis data ready for contexten consumption")
        print(f"🔗 Report URL: {contexten_data['report_url']}")
        print(f"🎛️ Dashboard URL: {contexten_data['dashboard_url']}")
        
    except Exception as e:
        print(f"❌ Contexten integration failed: {e}")
    
    print(f"\n🎉 Comprehensive analysis examples completed!")
    print(f"📁 All reports saved to: {output_dir.absolute()}")
    print("\nGenerated Files:")
    print("• HTML reports with interactive features")
    print("• Interactive dashboards with Vue.js")
    print("• Standalone visualizations with Plotly")
    print("• JSON data files for external tools")
    print("• CSV exports for spreadsheet analysis")


if __name__ == "__main__":
    main()
