#!/usr/bin/env python3
"""
Comprehensive Error Analysis Demo

This demo shows how to use the enhanced Serena integration for comprehensive
error analysis, context tracking, and dependency mapping using existing
graph-sitter and Serena capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena import (
    SerenaAPI,
    ComprehensiveErrorAnalyzer,
    ErrorContext,
    get_codebase_error_analysis,
    analyze_file_errors,
    find_function_relationships,
    create_serena_api
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


def demo_basic_error_detection(api: SerenaAPI) -> None:
    """Demonstrate basic error detection capabilities."""
    print_section("BASIC ERROR DETECTION")
    
    # Get all errors in the codebase
    all_errors = api.get_all_errors()
    print(f"📊 Total errors found: {len(all_errors)}")
    
    if all_errors:
        print("\n🔍 Sample errors:")
        for i, error in enumerate(all_errors[:5]):  # Show first 5 errors
            print(f"  {i+1}. {error['file_path']}:{error['line']} - {error['message'][:80]}...")
    
    # Get error summary
    summary = api.get_error_summary()
    print(f"\n📈 Error Summary:")
    print(f"  - Total errors: {summary.get('total_errors', 0)}")
    print(f"  - Total warnings: {summary.get('total_warnings', 0)}")
    print(f"  - Total diagnostics: {summary.get('total_diagnostics', 0)}")
    print(f"  - LSP enabled: {summary.get('lsp_status', {}).get('enabled', False)}")
    print(f"  - Serena available: {summary.get('serena_available', False)}")
    
    # Show most problematic files
    if 'most_problematic_files' in summary:
        print(f"\n🚨 Most problematic files:")
        for file_info in summary['most_problematic_files'][:5]:
            print(f"  - {file_info['file_path']}: {file_info['error_count']} errors")


def demo_comprehensive_error_context(api: SerenaAPI) -> None:
    """Demonstrate comprehensive error context analysis."""
    print_section("COMPREHENSIVE ERROR CONTEXT ANALYSIS")
    
    # Get all errors with full context
    errors_with_context = api.get_all_errors_with_context()
    print(f"📊 Errors with context: {len(errors_with_context)}")
    
    if errors_with_context:
        # Show detailed analysis for first error
        context = errors_with_context[0]
        error = context['error']
        
        print(f"\n🔍 Detailed analysis for: {error['file_path']}:{error['line']}")
        print(f"   Message: {error['message']}")
        print(f"   Severity: {error['severity']}")
        
        print_subsection("Function Call Analysis")
        print(f"   Functions calling this error point: {len(context['calling_functions'])}")
        for caller in context['calling_functions'][:3]:
            print(f"     - {caller.get('function_name', 'unknown')} in {caller.get('file_path', 'unknown')}")
        
        print(f"   Functions called by this error point: {len(context['called_functions'])}")
        for called in context['called_functions'][:3]:
            print(f"     - {called.get('function_name', 'unknown')} in {called.get('file_path', 'unknown')}")
        
        print_subsection("Parameter Issues")
        if context['parameter_issues']:
            print(f"   Parameter issues found: {len(context['parameter_issues'])}")
            for param in context['parameter_issues'][:3]:
                print(f"     - {param.get('issue_type', 'unknown')}: {param.get('parameter_name', 'unknown')}")
        else:
            print("   No parameter issues detected")
        
        print_subsection("Dependencies")
        if context['dependency_chain']:
            print(f"   Dependencies: {len(context['dependency_chain'])}")
            for dep in context['dependency_chain'][:5]:
                print(f"     - {dep}")
        else:
            print("   No dependencies found")
        
        print_subsection("Related Symbols")
        if context['related_symbols']:
            print(f"   Related symbols: {len(context['related_symbols'])}")
            for symbol in context['related_symbols'][:3]:
                print(f"     - {symbol.get('symbol_name', 'unknown')} ({symbol.get('symbol_type', 'unknown')})")
        
        print_subsection("Fix Suggestions")
        if context['fix_suggestions']:
            print("   Suggested fixes:")
            for suggestion in context['fix_suggestions']:
                print(f"     - {suggestion}")
        
        print_subsection("Code Context")
        if context['code_context']:
            print("   Code context:")
            print("   " + "\n   ".join(context['code_context'].split('\n')[:10]))


def demo_parameter_analysis(api: SerenaAPI) -> None:
    """Demonstrate parameter usage analysis."""
    print_section("PARAMETER USAGE ANALYSIS")
    
    # Get unused parameters
    unused_params = api.get_unused_parameters()
    print(f"📊 Unused parameters found: {len(unused_params)}")
    
    if unused_params:
        print("\n🔍 Sample unused parameters:")
        for param in unused_params[:5]:
            print(f"  - {param['parameter_name']} in {param['function_name']} ({param['file_path']})")
            if param.get('suggestion'):
                print(f"    💡 Suggestion: {param['suggestion']}")
    
    # Get wrong parameters
    wrong_params = api.get_wrong_parameters()
    print(f"\n📊 Wrong parameters found: {len(wrong_params)}")
    
    if wrong_params:
        print("\n🔍 Sample wrong parameters:")
        for param in wrong_params[:5]:
            print(f"  - {param['parameter_name']} in {param['function_name']} ({param['file_path']})")
            print(f"    Issue: {param.get('issue_type', 'unknown')}")
            if param.get('expected_type') and param.get('actual_type'):
                print(f"    Expected: {param['expected_type']}, Got: {param['actual_type']}")
            if param.get('suggestion'):
                print(f"    💡 Suggestion: {param['suggestion']}")


def demo_function_relationships(api: SerenaAPI) -> None:
    """Demonstrate function relationship analysis."""
    print_section("FUNCTION RELATIONSHIP ANALYSIS")
    
    # Find a function to analyze (use the first error's function)
    all_errors = api.get_all_errors()
    if not all_errors:
        print("No errors found to analyze function relationships")
        return
    
    # Try to find a function name from the first error
    first_error = all_errors[0]
    file_path = first_error['file_path']
    
    print(f"🔍 Analyzing relationships for functions in: {file_path}")
    
    # Get file errors with context to find function names
    errors_with_context = api.get_all_errors_with_context()
    if errors_with_context:
        context = errors_with_context[0]
        
        # Look for function names in calling or called functions
        function_name = None
        if context['calling_functions']:
            function_name = context['calling_functions'][0].get('function_name')
        elif context['called_functions']:
            function_name = context['called_functions'][0].get('function_name')
        
        if function_name and function_name != 'unknown':
            print(f"\n📊 Analyzing function: {function_name}")
            
            # Get function callers
            callers = api.get_function_callers(function_name)
            print(f"   Functions that call {function_name}: {len(callers)}")
            for caller in callers[:3]:
                print(f"     - {caller.get('caller_function', 'unknown')} in {caller.get('file_path', 'unknown')}")
            
            # Find symbol usage
            symbol_usage = api.find_symbol_usage(function_name)
            print(f"   Symbol usage locations: {len(symbol_usage)}")
            for usage in symbol_usage[:3]:
                print(f"     - {usage.get('file_path', 'unknown')}:{usage.get('line_number', 0)}")
            
            # Get related symbols
            related_symbols = api.get_related_symbols(function_name)
            print(f"   Related symbols: {len(related_symbols)}")
            for symbol in related_symbols[:3]:
                print(f"     - {symbol.get('symbol_name', 'unknown')} ({symbol.get('symbol_type', 'unknown')})")


def demo_dependency_analysis(api: SerenaAPI) -> None:
    """Demonstrate dependency analysis."""
    print_section("DEPENDENCY ANALYSIS")
    
    # Get dependency graph
    dependency_graph = api.get_dependency_graph()
    print(f"📊 Files with dependencies: {len(dependency_graph)}")
    
    if dependency_graph:
        print("\n🔍 Sample file dependencies:")
        for file_path, deps in list(dependency_graph.items())[:5]:
            if deps:  # Only show files with dependencies
                print(f"  {file_path}:")
                for dep in deps[:5]:  # Show first 5 dependencies
                    print(f"    - {dep}")
        
        # Find files with most dependencies
        files_by_deps = sorted(dependency_graph.items(), key=lambda x: len(x[1]), reverse=True)
        print(f"\n📈 Files with most dependencies:")
        for file_path, deps in files_by_deps[:5]:
            if deps:
                print(f"  {file_path}: {len(deps)} dependencies")


def demo_file_specific_analysis(api: SerenaAPI) -> None:
    """Demonstrate file-specific error analysis."""
    print_section("FILE-SPECIFIC ERROR ANALYSIS")
    
    # Get all errors to find a file with errors
    all_errors = api.get_all_errors()
    if not all_errors:
        print("No errors found for file-specific analysis")
        return
    
    # Analyze the first file with errors
    target_file = all_errors[0]['file_path']
    print(f"🔍 Analyzing file: {target_file}")
    
    # Get file errors
    file_errors = api.get_file_errors(target_file)
    print(f"   Errors in file: {len(file_errors)}")
    
    # Get file dependencies
    file_deps = api.get_file_dependencies(target_file)
    print(f"   Dependencies: {len(file_deps)}")
    if file_deps:
        for dep in file_deps[:5]:
            print(f"     - {dep}")
    
    # Get error context for first error in file
    if file_errors:
        first_error = file_errors[0]
        context = api.get_error_context(first_error['file_path'], first_error['line'])
        if context:
            print(f"\n   Error context for line {first_error['line']}:")
            print(f"     Message: {context['error']['message']}")
            print(f"     Calling functions: {len(context['calling_functions'])}")
            print(f"     Called functions: {len(context['called_functions'])}")
            print(f"     Fix suggestions: {len(context['fix_suggestions'])}")


def demo_convenience_functions() -> None:
    """Demonstrate convenience functions for quick analysis."""
    print_section("CONVENIENCE FUNCTIONS")
    
    # Use convenience function for full codebase analysis
    print("🚀 Running comprehensive codebase analysis...")
    
    try:
        # Create codebase (assuming we're in the graph-sitter directory)
        repo_path = Path(__file__).parent.parent
        codebase = Codebase(str(repo_path))
        
        # Use convenience function
        analysis = get_codebase_error_analysis(codebase)
        
        print("✅ Analysis complete!")
        print(f"   Total errors: {analysis['error_summary'].get('total_errors', 0)}")
        print(f"   Errors with context: {len(analysis['all_errors_with_context'])}")
        print(f"   Unused parameters: {len(analysis['unused_parameters'])}")
        print(f"   Wrong parameters: {len(analysis['wrong_parameters'])}")
        print(f"   Files in dependency graph: {len(analysis['dependency_graph'])}")
        
        # Show status
        status = analysis['status']
        print(f"\n📊 System Status:")
        print(f"   Error analyzer: {'✅' if status['error_analyzer_initialized'] else '❌'}")
        print(f"   MCP bridge: {'✅' if status['mcp_bridge_available'] else '❌'}")
        print(f"   Semantic tools: {'✅' if status['semantic_tools_available'] else '❌'}")
        print(f"   LSP enabled: {'✅' if status['lsp_enabled'] else '❌'}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")


def main():
    """Main demo function."""
    print("🚀 Comprehensive Error Analysis Demo")
    print("Using existing graph-sitter and Serena capabilities")
    
    try:
        # Create codebase (assuming we're in the graph-sitter directory)
        repo_path = Path(__file__).parent.parent
        print(f"📁 Analyzing repository: {repo_path}")
        
        codebase = Codebase(str(repo_path))
        
        # Create Serena API
        print("🔧 Initializing Serena API...")
        api = create_serena_api(codebase, enable_lsp=True)
        
        try:
            # Run all demos
            demo_basic_error_detection(api)
            demo_comprehensive_error_context(api)
            demo_parameter_analysis(api)
            demo_function_relationships(api)
            demo_dependency_analysis(api)
            demo_file_specific_analysis(api)
            
            # Show final status
            print_section("FINAL STATUS")
            status = api.get_status()
            print("🎯 Serena Integration Status:")
            for key, value in status.items():
                icon = "✅" if value else "❌"
                print(f"   {key}: {icon} {value}")
            
        finally:
            # Clean shutdown
            print("\n🔧 Shutting down Serena API...")
            api.shutdown()
        
        # Demo convenience functions
        demo_convenience_functions()
        
        print_section("DEMO COMPLETE")
        print("✅ All demos completed successfully!")
        print("\n💡 Key Features Demonstrated:")
        print("   - Comprehensive error detection using existing diagnostics")
        print("   - Function call chain analysis (callers and callees)")
        print("   - Parameter usage analysis (unused, wrong types)")
        print("   - Dependency tracking and mapping")
        print("   - Symbol relationship analysis")
        print("   - Real-time error context with fix suggestions")
        print("   - Clean API for easy integration")
        
        print("\n🎯 Usage Examples:")
        print("   from graph_sitter.extensions.serena import SerenaAPI")
        print("   api = SerenaAPI(codebase)")
        print("   errors = api.get_all_errors_with_context()")
        print("   unused_params = api.get_unused_parameters()")
        print("   relationships = api.get_function_callers('function_name')")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
