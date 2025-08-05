"""
Advanced Analytics Example for Graph-Sitter

Demonstrates the comprehensive analytics system with all analyzers:
- Complexity analysis
- Performance analysis  
- Security analysis
- Dead code detection
- Dependency analysis
- Dashboard generation
"""

import graph_sitter
from graph_sitter.analytics import (
    AnalyticsEngine, 
    AnalysisConfig,
    AnalyticsDashboard,
    AnalyticsAPI
)


def main():
    """Run comprehensive analytics on the current codebase."""
    
    print("🚀 Starting Advanced Analytics Example")
    print("=" * 50)
    
    # Load the current codebase
    print("📁 Loading codebase...")
    codebase = graph_sitter.Codebase.from_directory(".")
    print(f"   Loaded {len(list(codebase.files))} files")
    
    # Configure analytics engine
    print("\n⚙️  Configuring analytics engine...")
    config = AnalysisConfig(
        enable_complexity=True,
        enable_performance=True,
        enable_security=True,
        enable_dead_code=True,
        enable_dependency=True,
        max_workers=4,
        deep_analysis=True,
        generate_reports=True
    )
    
    # Initialize analytics engine
    engine = AnalyticsEngine(config)
    print(f"   Configured with {len(engine.analyzers)} analyzers")
    
    # Run comprehensive analysis
    print("\n🔍 Running comprehensive analysis...")
    print("   This may take a few minutes for large codebases...")
    
    try:
        report = engine.analyze_codebase(codebase)
        
        print(f"\n✅ Analysis completed in {report.execution_time:.2f} seconds")
        print(f"   Overall Quality Score: {report.overall_quality_score:.1f}/100")
        print(f"   Total Issues Found: {report.total_findings}")
        
        # Display summary statistics
        print("\n📊 Summary Statistics:")
        stats = report.get_summary_stats()
        print(f"   Files Analyzed: {stats['total_files']:,}")
        print(f"   Lines Analyzed: {stats['total_lines']:,}")
        print(f"   Critical Issues: {stats['critical_issues']}")
        print(f"   High Issues: {stats['high_issues']}")
        print(f"   Medium Issues: {stats['medium_issues']}")
        print(f"   Low Issues: {stats['low_issues']}")
        
        # Display analyzer results
        print("\n🔬 Analyzer Results:")
        for analyzer_name, result in report.analysis_results.items():
            if result.status == "completed":
                print(f"   {analyzer_name.title()}:")
                print(f"     Quality Score: {result.metrics.quality_score:.1f}/100")
                print(f"     Issues Found: {len(result.findings)}")
                print(f"     Execution Time: {result.metrics.execution_time:.2f}s")
            else:
                print(f"   {analyzer_name.title()}: {result.status}")
                if result.error_message:
                    print(f"     Error: {result.error_message}")
        
        # Show top critical findings
        critical_findings = report.critical_findings
        if critical_findings:
            print(f"\n🚨 Top Critical Issues ({len(critical_findings)} total):")
            for finding in critical_findings[:5]:
                print(f"   • {finding.title}")
                print(f"     File: {finding.file_path}")
                if finding.line_number:
                    print(f"     Line: {finding.line_number}")
                print(f"     {finding.description}")
                print()
        
        # Show recommendations
        if report.recommendations:
            print("💡 Top Recommendations:")
            for i, rec in enumerate(report.recommendations[:5], 1):
                print(f"   {i}. {rec}")
        
        # Generate dashboard
        print("\n📈 Generating dashboard...")
        dashboard = AnalyticsDashboard()
        dashboard_data = dashboard.create_comprehensive_dashboard(report)
        
        # Export reports
        print("\n💾 Exporting reports...")
        
        # Export JSON report
        json_path = "analytics_report.json"
        report.save_to_file(json_path)
        print(f"   JSON report saved to: {json_path}")
        
        # Export HTML dashboard
        html_path = "analytics_dashboard.html"
        dashboard.export_dashboard(dashboard_data, html_path, "html")
        print(f"   HTML dashboard saved to: {html_path}")
        
        # Demonstrate API usage
        print("\n🌐 Demonstrating API usage...")
        api = AnalyticsAPI()
        
        # Start analysis via API
        api_result = api.analyze_codebase(codebase, config.__dict__)
        job_id = api_result.get("job_id")
        
        if job_id:
            print(f"   Analysis job started: {job_id}")
            
            # Get results
            results = api.get_analysis_results(job_id, "summary")
            if results["status"] == "success":
                print(f"   API analysis completed successfully")
            
            # Generate dashboard via API
            dashboard_result = api.generate_dashboard(job_id)
            if dashboard_result["status"] == "success":
                print(f"   Dashboard generated via API")
        
        # Show specific analyzer insights
        print("\n🎯 Specific Analyzer Insights:")
        
        # Complexity insights
        complexity_result = report.get_analyzer_result("complexity")
        if complexity_result and complexity_result.status == "completed":
            complexity_metrics = complexity_result.metrics.complexity_metrics
            if complexity_metrics:
                avg_complexity = complexity_metrics.get("average_cyclomatic_complexity", 0)
                print(f"   Complexity: Average cyclomatic complexity is {avg_complexity:.1f}")
                
                if "highest_complexity_functions" in complexity_metrics:
                    top_complex = complexity_metrics["highest_complexity_functions"][:3]
                    if top_complex:
                        print(f"   Most complex functions:")
                        for func in top_complex:
                            print(f"     • {func['name']}: {func['cyclomatic_complexity']}")
        
        # Security insights
        security_result = report.get_analyzer_result("security")
        if security_result and security_result.status == "completed":
            security_metrics = security_result.metrics.security_metrics
            if security_metrics:
                vuln_count = security_metrics.get("vulnerabilities_found", 0)
                if vuln_count > 0:
                    print(f"   Security: Found {vuln_count} potential vulnerabilities")
                    
                    vuln_types = security_metrics.get("vulnerability_types", {})
                    if vuln_types:
                        print(f"   Vulnerability types: {', '.join(vuln_types.keys())}")
        
        # Dead code insights
        dead_code_result = report.get_analyzer_result("dead_code")
        if dead_code_result and dead_code_result.status == "completed":
            dead_code_metrics = dead_code_result.metrics.dead_code_metrics
            if dead_code_metrics:
                dead_functions = dead_code_metrics.get("dead_functions", 0)
                unused_imports = dead_code_metrics.get("unused_imports", 0)
                if dead_functions > 0 or unused_imports > 0:
                    print(f"   Dead Code: {dead_functions} unused functions, {unused_imports} unused imports")
        
        # Performance insights
        performance_result = report.get_analyzer_result("performance")
        if performance_result and performance_result.status == "completed":
            perf_metrics = performance_result.metrics.performance_metrics
            if perf_metrics:
                perf_issues = perf_metrics.get("performance_issues_found", 0)
                if perf_issues > 0:
                    print(f"   Performance: Found {perf_issues} potential performance issues")
        
        # Dependency insights
        dependency_result = report.get_analyzer_result("dependency")
        if dependency_result and dependency_result.status == "completed":
            dep_metrics = dependency_result.metrics.dependency_metrics
            if dep_metrics:
                circular_deps = dep_metrics.get("circular_dependency_count", 0)
                avg_coupling = dep_metrics.get("average_coupling", 0)
                print(f"   Dependencies: {circular_deps} circular dependencies, {avg_coupling:.1f} average coupling")
        
        print(f"\n🎉 Advanced analytics completed successfully!")
        print(f"   Check {html_path} for interactive dashboard")
        print(f"   Check {json_path} for detailed JSON report")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

