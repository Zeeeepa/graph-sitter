#!/usr/bin/env python3
"""
LSP Usage Examples

This file demonstrates how to use the unified LSP API for error retrieval
and code intelligence with the enhanced Graph-Sitter Codebase.
"""

from graph_sitter.enhanced import Codebase, ErrorSeverity, ErrorType, Position, Range
from datetime import datetime, timedelta
import time


def basic_error_retrieval_example():
    """Basic example of error retrieval."""
    print("=== Basic Error Retrieval Example ===")
    
    # Initialize codebase with LSP
    codebase = Codebase("./my-project")
    
    # Get all errors
    all_errors = codebase.errors()
    print(f"Found {len(all_errors.errors)} errors")
    
    # Get detailed context for a specific error
    if all_errors.errors:
        error_context = codebase.full_error_context(all_errors.errors[0].id)
        print(f"Error context: {error_context.error.message}")
    
    # Get errors in a specific file
    file_errors = codebase.errors_by_file("src/main.py")
    print(f"Errors in main.py: {len(file_errors.errors)}")
    
    # Get error summary
    summary = codebase.error_summary()
    print(f"Errors: {summary.error_count}, Warnings: {summary.warning_count}")


def advanced_error_filtering_example():
    """Advanced error filtering and analysis."""
    print("\n=== Advanced Error Filtering Example ===")
    
    codebase = Codebase("./my-project")
    
    # Filter by severity
    critical_errors = codebase.errors_by_severity(ErrorSeverity.ERROR)
    warnings = codebase.errors_by_severity(ErrorSeverity.WARNING)
    
    print(f"Critical errors: {len(critical_errors.errors)}")
    print(f"Warnings: {len(warnings.errors)}")
    
    # Filter by error type
    syntax_errors = codebase.errors_by_type(ErrorType.SYNTAX)
    import_errors = codebase.errors_by_type(ErrorType.IMPORT)
    
    print(f"Syntax errors: {len(syntax_errors.errors)}")
    print(f"Import errors: {len(import_errors.errors)}")
    
    # Get recent errors (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_errors = codebase.recent_errors(one_hour_ago)
    print(f"Recent errors: {len(recent_errors.errors)}")
    
    # Get error hotspots
    hotspots = codebase.error_hotspots()
    print("Error hotspots:")
    for hotspot in hotspots[:5]:  # Top 5
        print(f"  {hotspot['file_path']}: {hotspot['error_count']} errors")


def real_time_monitoring_example():
    """Real-time error monitoring example."""
    print("\n=== Real-time Error Monitoring Example ===")
    
    codebase = Codebase("./my-project")
    
    # Define callback for error changes
    def on_error_change(errors):
        print(f"🔄 Errors updated: {len(errors.errors)} total errors")
        if errors.error_count > 0:
            print(f"⚠️  {errors.error_count} critical errors detected!")
    
    # Start monitoring
    print("Starting real-time error monitoring...")
    codebase.watch_errors(on_error_change)
    
    # Simulate some work
    print("Monitoring for 10 seconds...")
    time.sleep(10)
    
    # Stop monitoring
    codebase.unwatch_errors(on_error_change)
    print("Stopped monitoring")


def auto_fix_example():
    """Auto-fix errors example."""
    print("\n=== Auto-fix Errors Example ===")
    
    codebase = Codebase("./my-project")
    
    # Get all errors
    errors = codebase.errors()
    print(f"Total errors before fixing: {len(errors.errors)}")
    
    # Find fixable errors
    fixable_errors = [e for e in errors.errors if e.has_quick_fix]
    print(f"Fixable errors: {len(fixable_errors)}")
    
    if fixable_errors:
        # Get quick fixes for the first error
        error_id = fixable_errors[0].id
        quick_fixes = codebase.get_quick_fixes(error_id)
        
        print(f"Available fixes for error {error_id}:")
        for fix in quick_fixes:
            print(f"  - {fix.title}: {fix.description}")
        
        # Apply the first fix
        if quick_fixes:
            success = codebase.apply_error_fix(error_id, quick_fixes[0].id)
            print(f"Fix applied successfully: {success}")
    
    # Auto-fix all fixable errors
    fixable_ids = [e.id for e in fixable_errors]
    if fixable_ids:
        results = codebase.auto_fix_errors(fixable_ids)
        fixed_count = sum(results.values())
        print(f"Auto-fixed {fixed_count} out of {len(results)} errors")


def code_intelligence_example():
    """Code intelligence features example."""
    print("\n=== Code Intelligence Example ===")
    
    codebase = Codebase("./my-project")
    
    # Test position for examples
    pos = Position(line=10, character=5)
    
    # Code completions
    completions = codebase.completions("src/main.py", pos)
    print(f"Available completions: {len(completions)}")
    for comp in completions[:3]:  # Show first 3
        print(f"  - {comp.label}: {comp.detail or 'No detail'}")
    
    # Hover information
    hover = codebase.hover_info("src/main.py", pos)
    if hover:
        print(f"Hover info: {hover.contents[:100]}...")  # First 100 chars
    
    # Go to definition
    definitions = codebase.definitions("MyClass")
    print(f"Definitions for 'MyClass': {len(definitions)}")
    for definition in definitions:
        print(f"  - {definition.name} at {definition.location}")
    
    # Find references
    references = codebase.references("MyClass")
    print(f"References to 'MyClass': {len(references)}")


def refactoring_example():
    """Code refactoring example."""
    print("\n=== Code Refactoring Example ===")
    
    codebase = Codebase("./my-project")
    
    # Rename symbol
    print("Renaming symbol 'old_function' to 'new_function'...")
    success = codebase.rename_symbol("old_function", "new_function")
    print(f"Rename successful: {success}")
    
    # Extract method
    range_obj = Range(Position(10, 0), Position(20, 0))
    print("Extracting method from selected range...")
    success = codebase.extract_method("src/main.py", range_obj)
    print(f"Method extraction successful: {success}")
    
    # Organize imports
    print("Organizing imports in main.py...")
    success = codebase.organize_imports("src/main.py")
    print(f"Import organization successful: {success}")
    
    # Get available code actions
    actions = codebase.code_actions("src/main.py", range_obj)
    print(f"Available code actions: {len(actions)}")
    for action in actions[:3]:  # Show first 3
        print(f"  - {action.get('title', 'Unknown action')}")


def semantic_analysis_example():
    """Semantic analysis example."""
    print("\n=== Semantic Analysis Example ===")
    
    codebase = Codebase("./my-project")
    
    # Document symbols
    symbols = codebase.document_symbols("src/main.py")
    print(f"Document symbols in main.py: {len(symbols)}")
    for symbol in symbols[:5]:  # Show first 5
        print(f"  - {symbol.name} ({symbol.kind})")
    
    # Workspace symbol search
    search_results = codebase.workspace_symbols("MyClass")
    print(f"Workspace symbols matching 'MyClass': {len(search_results)}")
    
    # Call hierarchy
    hierarchy = codebase.call_hierarchy("main_function")
    print(f"Call hierarchy for 'main_function':")
    print(f"  - Callers: {len(hierarchy.get('callers', []))}")
    print(f"  - Callees: {len(hierarchy.get('callees', []))}")
    
    # Semantic tokens
    tokens = codebase.semantic_tokens("src/main.py")
    print(f"Semantic tokens in main.py: {len(tokens)}")


def health_and_diagnostics_example():
    """Health monitoring and diagnostics example."""
    print("\n=== Health and Diagnostics Example ===")
    
    codebase = Codebase("./my-project")
    
    # Overall health check
    health = codebase.health_check()
    print(f"Overall health score: {health.overall_score:.2f}")
    print(f"Error score: {health.error_score:.2f}")
    print(f"Warning score: {health.warning_score:.2f}")
    print(f"LSP health: {health.lsp_health}")
    
    print("Recommendations:")
    for rec in health.recommendations:
        print(f"  - {rec}")
    
    # LSP status
    status = codebase.lsp_status()
    print(f"\nLSP Status:")
    print(f"  - Running: {status.is_running}")
    print(f"  - Server: {status.server_info.get('name', 'Unknown')}")
    print(f"  - Last heartbeat: {status.last_heartbeat}")
    
    # Capabilities
    capabilities = codebase.capabilities()
    print(f"\nLSP Capabilities:")
    print(f"  - Completion: {capabilities.completion}")
    print(f"  - Hover: {capabilities.hover}")
    print(f"  - Diagnostics: {capabilities.diagnostics}")
    print(f"  - Refactoring: {capabilities.rename}")
    
    # All diagnostics
    diagnostics = codebase.diagnostics()
    print(f"\nDiagnostics summary:")
    print(f"  - Total: {diagnostics.total_count}")
    print(f"  - Errors: {diagnostics.error_count}")
    print(f"  - Warnings: {diagnostics.warning_count}")
    print(f"  - Info: {diagnostics.info_count}")


def comprehensive_analysis_example():
    """Comprehensive codebase analysis example."""
    print("\n=== Comprehensive Analysis Example ===")
    
    def analyze_codebase(project_path):
        """Complete codebase analysis workflow."""
        
        # Initialize
        codebase = Codebase(project_path)
        print(f"🔍 Analyzing codebase: {codebase.name}")
        
        # Check LSP status first
        status = codebase.lsp_status()
        if not status.is_running:
            print("❌ LSP server not running - limited functionality available")
            return None
        
        print("✅ LSP server running")
        
        # Overall health assessment
        health = codebase.health_check()
        print(f"📊 Overall health score: {health.overall_score:.2f}")
        
        if health.overall_score < 0.7:
            print("⚠️  Codebase health needs attention!")
        elif health.overall_score > 0.9:
            print("🎉 Excellent codebase health!")
        
        # Error analysis
        errors = codebase.errors()
        print(f"\n📋 Error Analysis:")
        print(f"  - Total issues: {errors.total_count}")
        print(f"  - Critical errors: {errors.error_count}")
        print(f"  - Warnings: {errors.warning_count}")
        print(f"  - Info messages: {errors.info_count}")
        
        # Error trends
        trends = codebase.error_trends()
        print(f"  - Trend: {trends.get('direction', 'stable')}")
        
        # Hotspot analysis
        hotspots = codebase.error_hotspots()
        if hotspots:
            print(f"\n🔥 Top error hotspots:")
            for i, hotspot in enumerate(hotspots[:5], 1):
                print(f"  {i}. {hotspot['file_path']}: {hotspot['error_count']} errors")
        
        # Common error types
        common_errors = codebase.most_common_errors()
        if common_errors:
            print(f"\n📈 Most common error types:")
            for error_type in common_errors[:3]:
                print(f"  - {error_type['type']}: {error_type['count']} occurrences")
        
        # Auto-fix opportunities
        critical_errors = codebase.errors_by_severity(ErrorSeverity.ERROR)
        fixable = [e for e in critical_errors.errors if e.has_quick_fix]
        
        if fixable:
            print(f"\n🔧 Auto-fix opportunities: {len(fixable)} errors can be auto-fixed")
            
            # Demonstrate auto-fixing
            print("Attempting to auto-fix errors...")
            fix_results = codebase.auto_fix_errors([e.id for e in fixable[:3]])  # Fix first 3
            fixed_count = sum(fix_results.values())
            print(f"✅ Successfully auto-fixed {fixed_count} errors")
        
        # Recommendations
        if health.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in health.recommendations:
                print(f"  - {rec}")
        
        # Set up monitoring for demonstration
        print(f"\n📡 Setting up real-time monitoring...")
        
        def monitor_callback(error_collection):
            print(f"📊 Real-time update: {len(error_collection.errors)} total errors")
        
        codebase.watch_errors(monitor_callback)
        
        # Monitor for a short time
        print("Monitoring for 5 seconds...")
        time.sleep(5)
        
        # Clean up
        codebase.unwatch_errors(monitor_callback)
        
        print("✅ Analysis complete!")
        return codebase
    
    # Run the comprehensive analysis
    result = analyze_codebase("./my-project")
    
    if result:
        print(f"\n🎯 Final Summary:")
        final_health = result.health_check()
        print(f"Final health score: {final_health.overall_score:.2f}")


def error_context_deep_dive_example():
    """Deep dive into error context and analysis."""
    print("\n=== Error Context Deep Dive Example ===")
    
    codebase = Codebase("./my-project")
    
    # Get errors and analyze the first one in detail
    errors = codebase.errors()
    if not errors.errors:
        print("No errors found - codebase is clean!")
        return
    
    error = errors.errors[0]
    print(f"Analyzing error: {error.id}")
    print(f"Message: {error.message}")
    print(f"Severity: {error.severity.value}")
    print(f"Type: {error.error_type.value}")
    print(f"File: {error.file_path}")
    
    # Get full context
    context = codebase.full_error_context(error.id)
    if context:
        print(f"\n📄 Surrounding code:")
        print(context.surrounding_code[:200] + "..." if len(context.surrounding_code) > 200 else context.surrounding_code)
        
        print(f"\n🔗 Related errors: {len(context.related_errors)}")
        for related in context.related_errors[:3]:  # Show first 3
            print(f"  - {related.message}")
        
        print(f"\n💡 Fix suggestions:")
        for suggestion in context.fix_suggestions:
            print(f"  - {suggestion}")
        
        print(f"\n📊 Impact analysis:")
        impact = context.impact_analysis
        print(f"  - Blocking: {impact.get('blocking', False)}")
        print(f"  - Affects compilation: {impact.get('affects_compilation', False)}")
        print(f"  - Priority: {impact.get('priority', 'unknown')}")
        print(f"  - Estimated fix time: {impact.get('estimated_fix_time', 'unknown')}")
    
    # Get related symbols
    related_symbols = codebase.error_related_symbols(error.id)
    if related_symbols:
        print(f"\n🔤 Related symbols: {', '.join(related_symbols)}")
    
    # Get specific suggestions
    suggestions = codebase.error_suggestions(error.id)
    if suggestions:
        print(f"\n🎯 Specific suggestions:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")


def main():
    """Run all examples."""
    print("🚀 LSP Usage Examples")
    print("=" * 50)
    
    try:
        # Run all examples
        basic_error_retrieval_example()
        advanced_error_filtering_example()
        real_time_monitoring_example()
        auto_fix_example()
        code_intelligence_example()
        refactoring_example()
        semantic_analysis_example()
        health_and_diagnostics_example()
        error_context_deep_dive_example()
        comprehensive_analysis_example()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

