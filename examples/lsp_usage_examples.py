#!/usr/bin/env python3
"""
Comprehensive LSP Usage Examples

This file demonstrates all the new LSP error retrieval capabilities
with practical, real-world examples that developers can use immediately.
"""

from graph_sitter import Codebase
import time
import json
from pathlib import Path


def basic_error_analysis_example():
    """Example 1: Basic Error Analysis"""
    print("=" * 60)
    print("EXAMPLE 1: BASIC ERROR ANALYSIS")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Get all errors - the most basic operation
    all_errors = codebase.errors()
    print(f"📊 Found {len(all_errors)} total errors in codebase")
    
    # Get error summary for overview
    summary = codebase.error_summary()
    print(f"📈 Error Summary:")
    print(f"   • Total diagnostics: {summary['total_diagnostics']}")
    print(f"   • Errors: {summary['error_count']}")
    print(f"   • Warnings: {summary['warning_count']}")
    print(f"   • Info messages: {summary['info_count']}")
    print(f"   • Files with errors: {summary['files_with_errors']}")
    
    # Get errors by severity
    critical_errors = codebase.errors_by_severity("ERROR")
    warnings = codebase.errors_by_severity("WARNING")
    print(f"🔴 Critical errors: {len(critical_errors)}")
    print(f"🟡 Warnings: {len(warnings)}")
    
    # Show error hotspots
    hotspots = codebase.error_hotspots()
    if hotspots:
        print(f"🔥 Top error hotspots:")
        for i, hotspot in enumerate(hotspots[:3], 1):
            print(f"   {i}. {hotspot['file_path']}: {hotspot['error_count']} errors")
    
    print()


def detailed_error_context_example():
    """Example 2: Detailed Error Context Analysis"""
    print("=" * 60)
    print("EXAMPLE 2: DETAILED ERROR CONTEXT ANALYSIS")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Get first few errors for detailed analysis
    all_errors = codebase.errors()
    
    if all_errors:
        print(f"🔍 Analyzing first {min(3, len(all_errors))} errors in detail:")
        
        for i, error in enumerate(all_errors[:3], 1):
            error_id = getattr(error, 'id', f'error_{i}')
            print(f"\n--- Error {i} ---")
            
            # Get full context
            context = codebase.full_error_context(error_id)
            if context:
                print(f"📁 File: {context['file_path']}")
                print(f"📍 Location: Line {context['line']}, Character {context['character']}")
                print(f"💬 Message: {context['message']}")
                print(f"⚠️  Severity: {context['severity']}")
                
                # Show context lines if available
                if context.get('context_lines'):
                    ctx_lines = context['context_lines']
                    if ctx_lines.get('error_line'):
                        print(f"📝 Error line: {ctx_lines['error_line'].strip()}")
            
            # Get fix suggestions
            suggestions = codebase.error_suggestions(error_id)
            if suggestions:
                print(f"💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"   • {suggestion}")
            
            # Get impact analysis
            impact = codebase.error_impact_analysis(error_id)
            if impact:
                print(f"📊 Impact: {impact.get('severity_impact', 'Unknown')} severity")
                print(f"🔧 Fix complexity: {impact.get('fix_complexity', 'Unknown')}")
            
            # Get related symbols
            related_symbols = codebase.error_related_symbols(error_id)
            if related_symbols:
                print(f"🔗 Related symbols: {', '.join(related_symbols[:5])}")
    else:
        print("✅ No errors found in codebase!")
    
    print()


def real_time_monitoring_example():
    """Example 3: Real-time Error Monitoring"""
    print("=" * 60)
    print("EXAMPLE 3: REAL-TIME ERROR MONITORING")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Set up real-time error monitoring
    print("🔄 Setting up real-time error monitoring...")
    
    def error_change_callback(errors):
        timestamp = time.strftime("%H:%M:%S")
        error_count = len([e for e in errors if e.severity == 1])
        warning_count = len([e for e in errors if e.severity == 2])
        print(f"[{timestamp}] 📊 Errors: {error_count}, Warnings: {warning_count}")
        
        # Alert on new critical errors
        if error_count > 0:
            print(f"🚨 ALERT: {error_count} critical errors detected!")
    
    # Start monitoring
    monitoring_active = codebase.watch_errors(error_change_callback)
    if monitoring_active:
        print("✅ Real-time monitoring activated")
        
        # Simulate monitoring for a few seconds
        print("⏱️  Monitoring for 5 seconds...")
        time.sleep(5)
        
        # Force refresh to trigger callback
        print("🔄 Forcing error refresh...")
        codebase.refresh_errors()
    else:
        print("❌ Could not activate real-time monitoring")
    
    # Demonstrate error stream
    print("\n🌊 Demonstrating error stream (first 3 updates):")
    stream_count = 0
    for errors in codebase.error_stream():
        stream_count += 1
        print(f"Stream update {stream_count}: {len(errors)} total diagnostics")
        if stream_count >= 3:
            break
    
    print()


def automated_error_resolution_example():
    """Example 4: Automated Error Resolution"""
    print("=" * 60)
    print("EXAMPLE 4: AUTOMATED ERROR RESOLUTION")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Find errors that can be auto-fixed
    all_errors = codebase.errors()
    fixable_errors = []
    
    print(f"🔍 Analyzing {len(all_errors)} errors for auto-fix potential...")
    
    for error in all_errors[:10]:  # Check first 10 errors
        error_id = getattr(error, 'id', f'error_{hash(str(error))}')
        quick_fixes = codebase.get_quick_fixes(error_id)
        
        if quick_fixes:
            fixable_errors.append(error_id)
            print(f"🔧 Can fix: {getattr(error, 'message', 'Unknown error')}")
            for fix in quick_fixes:
                print(f"   • {fix.get('title', 'Unknown fix')}: {fix.get('description', 'No description')}")
    
    if fixable_errors:
        print(f"\n🚀 Attempting to auto-fix {len(fixable_errors)} errors...")
        
        # Auto-fix all fixable errors
        fixed_errors = codebase.auto_fix_errors(fixable_errors)
        
        print(f"✅ Successfully fixed {len(fixed_errors)} out of {len(fixable_errors)} errors")
        
        if len(fixed_errors) < len(fixable_errors):
            failed_count = len(fixable_errors) - len(fixed_errors)
            print(f"⚠️  {failed_count} errors could not be auto-fixed")
    else:
        print("ℹ️  No auto-fixable errors found")
    
    print()


def code_intelligence_example():
    """Example 5: Code Intelligence Features"""
    print("=" * 60)
    print("EXAMPLE 5: CODE INTELLIGENCE FEATURES")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Find a Python file to analyze
    python_files = [f for f in codebase.files if str(f.filepath).endswith('.py')]
    
    if python_files:
        test_file = str(python_files[0].filepath)
        print(f"🔍 Analyzing code intelligence for: {test_file}")
        
        # Get completions at a specific position
        completions = codebase.completions(test_file, (10, 5))
        print(f"💡 Available completions at line 10, char 5: {len(completions)}")
        
        # Get hover information
        hover = codebase.hover_info(test_file, (10, 5))
        if hover:
            print(f"🖱️  Hover info available: {type(hover)}")
        
        # Get document symbols
        doc_symbols = codebase.document_symbols(test_file)
        print(f"📋 Document symbols found: {len(doc_symbols)}")
        
        if doc_symbols:
            print("   Top symbols:")
            for symbol in doc_symbols[:5]:
                print(f"   • {symbol.get('name', 'Unknown')} ({symbol.get('kind', 'unknown')})")
        
        # Search workspace symbols
        workspace_symbols = codebase.workspace_symbols("test")
        print(f"🔍 Workspace symbols matching 'test': {len(workspace_symbols)}")
        
        # Get semantic tokens
        semantic_tokens = codebase.semantic_tokens(test_file)
        print(f"🎨 Semantic tokens: {len(semantic_tokens)}")
        
    else:
        print("ℹ️  No Python files found for code intelligence demo")
    
    print()


def refactoring_and_code_actions_example():
    """Example 6: Refactoring and Code Actions"""
    print("=" * 60)
    print("EXAMPLE 6: REFACTORING AND CODE ACTIONS")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Find a file to demonstrate refactoring
    if codebase.files:
        test_file = str(codebase.files[0].filepath)
        print(f"🔧 Demonstrating refactoring capabilities on: {test_file}")
        
        # Get available code actions
        range_obj = {
            "start": {"line": 1, "character": 0},
            "end": {"line": 10, "character": 0}
        }
        
        code_actions = codebase.code_actions(test_file, range_obj)
        print(f"⚡ Available code actions: {len(code_actions)}")
        
        for action in code_actions:
            print(f"   • {action.get('title', 'Unknown action')} ({action.get('kind', 'unknown')})")
        
        # Demonstrate symbol renaming (dry run)
        if codebase.symbols:
            first_symbol = codebase.symbols[0]
            old_name = first_symbol.name
            new_name = f"{old_name}_renamed"
            
            rename_result = codebase.rename_symbol(old_name, new_name)
            if rename_result.get('success'):
                changes = rename_result.get('changes', [])
                print(f"🔄 Symbol rename simulation: {old_name} → {new_name}")
                print(f"   Would affect {len(changes)} locations")
            else:
                print(f"❌ Could not rename symbol: {old_name}")
        
        # Demonstrate extract method
        extract_result = codebase.extract_method(test_file, range_obj)
        if extract_result.get('success'):
            method_name = extract_result.get('new_method_name', 'unknown')
            print(f"📤 Extract method simulation: would create '{method_name}'")
        
        # Demonstrate organize imports
        organize_result = codebase.organize_imports(test_file)
        if organize_result.get('success'):
            print(f"📚 Organize imports: would reorganize imports in {test_file}")
    
    print()


def health_monitoring_dashboard():
    """Example 7: Comprehensive Health Dashboard"""
    print("=" * 60)
    print("EXAMPLE 7: COMPREHENSIVE HEALTH DASHBOARD")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Get overall health assessment
    health = codebase.health_check()
    
    print(f"🏥 CODEBASE HEALTH REPORT")
    print(f"   Overall Score: {health['health_score']}/100")
    print(f"   Status: {health['health_status']}")
    
    # Detailed error breakdown
    error_summary = health['error_summary']
    print(f"\n📊 ERROR BREAKDOWN:")
    print(f"   Total Issues: {error_summary['total_diagnostics']}")
    print(f"   🔴 Errors: {error_summary['error_count']}")
    print(f"   🟡 Warnings: {error_summary['warning_count']}")
    print(f"   🔵 Info: {error_summary['info_count']}")
    print(f"   📁 Files Affected: {error_summary['files_with_errors']}")
    
    # Show recommendations
    recommendations = health.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # LSP Status
    lsp_status = codebase.lsp_status()
    print(f"\n🔌 LSP STATUS:")
    print(f"   Available: {'✅' if lsp_status['lsp_available'] else '❌'}")
    if lsp_status.get('servers'):
        print(f"   Servers: {', '.join(lsp_status['servers'])}")
    
    # Available capabilities
    capabilities = codebase.capabilities()
    print(f"\n⚙️  AVAILABLE CAPABILITIES:")
    for cap_name, available in capabilities.items():
        status_icon = "✅" if available else "❌"
        cap_display = cap_name.replace('_', ' ').title()
        print(f"   {status_icon} {cap_display}")
    
    # Error trends
    trends = codebase.error_trends()
    print(f"\n📈 ERROR TRENDS:")
    print(f"   Current Trend: {trends.get('trend', 'Unknown')}")
    print(f"   Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(trends.get('timestamp', time.time())))}")
    
    # Most common errors
    common_errors = codebase.most_common_errors()
    if common_errors:
        print(f"\n🔄 MOST COMMON ERRORS:")
        for i, error in enumerate(common_errors[:3], 1):
            print(f"   {i}. {error['message'][:60]}... (occurs {error['count']} times)")
    
    print()


def advanced_analysis_example():
    """Example 8: Advanced Analysis and Reporting"""
    print("=" * 60)
    print("EXAMPLE 8: ADVANCED ANALYSIS AND REPORTING")
    print("=" * 60)
    
    codebase = Codebase(".")
    
    # Generate comprehensive analysis report
    report = {
        "timestamp": time.time(),
        "codebase_path": str(codebase.repo_path),
        "analysis": {}
    }
    
    # Basic metrics
    all_errors = codebase.errors()
    report["analysis"]["total_files"] = len(codebase.files)
    report["analysis"]["total_symbols"] = len(codebase.symbols)
    report["analysis"]["total_diagnostics"] = len(all_errors)
    
    # Error analysis by type
    syntax_errors = codebase.errors_by_type("syntax")
    semantic_errors = codebase.errors_by_type("semantic")
    lint_errors = codebase.errors_by_type("lint")
    
    report["analysis"]["error_breakdown"] = {
        "syntax": len(syntax_errors),
        "semantic": len(semantic_errors),
        "lint": len(lint_errors)
    }
    
    # File-level analysis
    file_analysis = {}
    for file in codebase.files[:10]:  # Analyze first 10 files
        file_path = str(file.filepath)
        file_errors = codebase.errors_by_file(file_path)
        file_symbols = codebase.document_symbols(file_path)
        
        file_analysis[file_path] = {
            "errors": len(file_errors),
            "symbols": len(file_symbols),
            "lines": getattr(file, 'line_count', 0)
        }
    
    report["analysis"]["file_analysis"] = file_analysis
    
    # Health metrics
    health = codebase.health_check()
    report["analysis"]["health"] = {
        "score": health["health_score"],
        "status": health["health_status"]
    }
    
    # Capabilities assessment
    capabilities = codebase.capabilities()
    report["analysis"]["capabilities"] = capabilities
    
    # Print summary
    print(f"📋 ADVANCED ANALYSIS REPORT")
    print(f"   Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Codebase: {report['codebase_path']}")
    print(f"   Files Analyzed: {report['analysis']['total_files']}")
    print(f"   Symbols Found: {report['analysis']['total_symbols']}")
    print(f"   Total Diagnostics: {report['analysis']['total_diagnostics']}")
    
    print(f"\n🔍 ERROR TYPE BREAKDOWN:")
    breakdown = report['analysis']['error_breakdown']
    print(f"   Syntax Errors: {breakdown['syntax']}")
    print(f"   Semantic Errors: {breakdown['semantic']}")
    print(f"   Lint Issues: {breakdown['lint']}")
    
    print(f"\n📁 TOP FILES BY ERROR COUNT:")
    file_errors = [(path, data['errors']) for path, data in file_analysis.items()]
    file_errors.sort(key=lambda x: x[1], reverse=True)
    
    for i, (file_path, error_count) in enumerate(file_errors[:5], 1):
        print(f"   {i}. {Path(file_path).name}: {error_count} errors")
    
    # Save report to file
    report_file = "codebase_analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: {report_file}")
    print()


def main():
    """Run all examples"""
    print("🚀 COMPREHENSIVE LSP API USAGE EXAMPLES")
    print("This demonstrates all the new LSP error retrieval capabilities")
    print("=" * 80)
    
    try:
        # Run all examples
        basic_error_analysis_example()
        detailed_error_context_example()
        real_time_monitoring_example()
        automated_error_resolution_example()
        code_intelligence_example()
        refactoring_and_code_actions_example()
        health_monitoring_dashboard()
        advanced_analysis_example()
        
        print("✅ All examples completed successfully!")
        print("\n🎯 KEY TAKEAWAYS:")
        print("   • All Serena LSP features are now easily retrievable from codebase object")
        print("   • Comprehensive error analysis with context and suggestions")
        print("   • Real-time monitoring and automated error resolution")
        print("   • Full code intelligence: completions, hover, definitions, references")
        print("   • Advanced refactoring and code actions")
        print("   • Health monitoring and capability assessment")
        print("   • Perfect for CI/CD, IDE integration, and automated code quality")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("This might be expected if running on a codebase without LSP setup")
        print("The API is still available and will work when properly configured")


if __name__ == "__main__":
    main()

