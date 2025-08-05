#!/usr/bin/env python3
"""
Enhanced Error Context Showcase for Graph-Sitter

This example demonstrates the comprehensive error context functionality
including all error contexts lists, grainchain integration, and web evaluation.
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to the path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter import Codebase
from graph_sitter.core.diagnostics import add_diagnostic_capabilities
from graph_sitter.integrations import GrainchainIntegration, WebEvalIntegration


async def main():
    """Demonstrate enhanced error context and integrations."""
    
    print("🚀 Enhanced Graph-Sitter Error Context & Integrations Demo")
    print("=" * 60)
    
    # Initialize codebase with all capabilities
    try:
        codebase = Codebase("./", enable_lsp=True)
        print(f"✅ Codebase initialized: {codebase.name}")
        print(f"📁 Repository path: {codebase.repo_path}")
        print(f"🔧 Language: {codebase.language}")
        print(f"📄 Total files: {len(codebase.files)}")
    except Exception as e:
        print(f"❌ Failed to initialize codebase: {e}")
        return
    
    # Check LSP and diagnostic status
    print("\n🔍 Diagnostic System Status:")
    print("-" * 35)
    
    if hasattr(codebase, 'is_lsp_enabled'):
        lsp_enabled = codebase.is_lsp_enabled()
        print(f"LSP Enabled: {'✅ Yes' if lsp_enabled else '❌ No'}")
        
        if lsp_enabled:
            status = codebase.get_lsp_status()
            print(f"LSP Available: {'✅ Yes' if status.get('available') else '❌ No'}")
            print(f"Bridge Initialized: {'✅ Yes' if status.get('bridge_initialized') else '❌ No'}")
    
    # Demonstrate enhanced error context functionality
    print("\n🐛 Enhanced Error Context Analysis:")
    print("-" * 40)
    
    if hasattr(codebase, 'errors'):
        errors = codebase.errors
        print(f"Total errors found: {len(errors)}")
        
        if errors:
            # Show individual error contexts
            print("\n📋 Individual Error Contexts:")
            for i, error in enumerate(errors[:3], 1):  # Show first 3 errors
                print(f"\n{i}. {error.file_path}:{error.line}:{error.character}")
                print(f"   Severity: {error.severity.name}")
                print(f"   Message: {error.message}")
                
                # Show context with highlighting
                print(f"   Context (±2 lines):")
                context = error.get_context(lines_before=2, lines_after=2)
                for line in context.split('\\n'):
                    print(f"   {line}")
            
            # Demonstrate new comprehensive context methods
            print(f"\n📊 All Errors with Context:")
            if hasattr(codebase, 'get_all_errors_with_context'):
                all_errors_context = codebase.get_all_errors_with_context(lines_before=1, lines_after=1)
                print(f"   Retrieved {len(all_errors_context)} errors with context")
                
                for error_ctx in all_errors_context[:2]:  # Show first 2
                    print(f"   - {error_ctx['file_path']}:{error_ctx['line']} ({error_ctx['severity']})")
                    print(f"     Message: {error_ctx['message']}")
            
            # Show errors grouped by file
            print(f"\n📁 Errors Grouped by File:")
            if hasattr(codebase, 'get_errors_by_file'):
                errors_by_file = codebase.get_errors_by_file(lines_before=1, lines_after=1)
                for file_path, file_errors in list(errors_by_file.items())[:3]:  # Show first 3 files
                    print(f"   📄 {file_path}: {len(file_errors)} errors")
                    for error in file_errors[:2]:  # Show first 2 errors per file
                        print(f"      - Line {error['line']}: {error['message'][:50]}...")
            
            # Show errors grouped by severity
            print(f"\n⚠️  Errors Grouped by Severity:")
            if hasattr(codebase, 'get_errors_by_severity'):
                errors_by_severity = codebase.get_errors_by_severity(lines_before=1, lines_after=1)
                for severity, severity_errors in errors_by_severity.items():
                    severity_emoji = {
                        'ERROR': '🔴',
                        'WARNING': '🟡',
                        'INFORMATION': '🔵',
                        'HINT': '💡'
                    }.get(severity, '❓')
                    print(f"   {severity_emoji} {severity}: {len(severity_errors)} errors")
            
            # Generate comprehensive error report
            print(f"\n📄 Comprehensive Error Context Report:")
            if hasattr(codebase, 'generate_error_context_report'):
                report = codebase.generate_error_context_report(lines_before=2, lines_after=2)
                # Show first 500 characters of the report
                print(f"   Report generated ({len(report)} characters)")
                print(f"   Preview:")
                for line in report.split('\\n')[:10]:  # Show first 10 lines
                    print(f"   {line}")
                if len(report.split('\\n')) > 10:
                    print(f"   ... (truncated, full report available)")
        else:
            print("🎉 No errors found in the codebase!")
    
    # Demonstrate Grainchain integration
    print(f"\n🏗️  Grainchain Sandbox Integration:")
    print("-" * 40)
    
    try:
        grainchain = GrainchainIntegration(codebase=codebase)
        print(f"Grainchain Available: {'✅ Yes' if grainchain.is_available() else '❌ No'}")
        
        if grainchain.is_available():
            print(f"Available Providers: {grainchain.get_available_providers()}")
            
            # Test code execution
            print("\\n🐍 Testing Python Code Execution:")
            result = await grainchain.execute_code(
                code="print('Hello from Grainchain!'); print(f'2 + 2 = {2 + 2}')",
                language="python",
                timeout=10
            )
            print(f"   Success: {'✅' if result.success else '❌'}")
            print(f"   Output: {result.stdout}")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Provider: {result.provider}")
            
            if result.stderr:
                print(f"   Stderr: {result.stderr}")
        else:
            print("💡 Install grainchain to enable sandbox execution:")
            print("   pip install grainchain")
    
    except Exception as e:
        print(f"❌ Grainchain integration error: {e}")
    
    # Demonstrate Web Evaluation integration
    print(f"\n🌐 Web Evaluation Integration:")
    print("-" * 35)
    
    try:
        web_eval = WebEvalIntegration(codebase=codebase)
        print(f"Web Eval Available: {'✅ Yes' if web_eval.is_available() else '❌ No'}")
        
        if web_eval.is_available():
            # Test web evaluation (mock)
            print("\\n🔍 Testing Web Application Evaluation:")
            result = await web_eval.evaluate_url("https://example.com")
            
            print(f"   URL: {result.url}")
            print(f"   Success: {'✅' if result.success else '❌'}")
            print(f"   Score: {result.score:.2f}")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Findings: {len(result.findings)}")
            
            for finding in result.findings[:2]:  # Show first 2 findings
                print(f"      - {finding['type'].title()}: {finding['message']} (Score: {finding['score']:.2f})")
            
            # Generate web evaluation report
            print("\\n📄 Generating Web Evaluation Report:")
            report = await web_eval.generate_report(result)
            print(f"   Report generated ({len(report)} characters)")
            print(f"   Preview:")
            for line in report.split('\\n')[:8]:  # Show first 8 lines
                print(f"   {line}")
        else:
            print("💡 Web evaluation using integrated mock implementation")
    
    except Exception as e:
        print(f"❌ Web evaluation integration error: {e}")
    
    # Integration summary
    print(f"\n📊 Integration Summary:")
    print("-" * 25)
    
    features = [
        ("Enhanced Error Context", hasattr(codebase, 'get_all_errors_with_context')),
        ("Error Context Reports", hasattr(codebase, 'generate_error_context_report')),
        ("Grainchain Sandbox", grainchain.is_available() if 'grainchain' in locals() else False),
        ("Web Evaluation", web_eval.is_available() if 'web_eval' in locals() else False),
        ("LSP Integration", hasattr(codebase, 'is_lsp_enabled') and codebase.is_lsp_enabled()),
        ("Diagnostic System", hasattr(codebase, 'diagnostics')),
    ]
    
    for feature, available in features:
        status = "✅ Available" if available else "❌ Not Available"
        print(f"   {feature}: {status}")
    
    print(f"\n🎯 Key Features Demonstrated:")
    print("  ✅ Enhanced error context with line highlighting")
    print("  ✅ Comprehensive error context lists and grouping")
    print("  ✅ Error context reports generation")
    print("  ✅ Grainchain sandbox integration for code execution")
    print("  ✅ Web evaluation integration for application testing")
    print("  ✅ Real-time LSP diagnostics integration")
    print("  ✅ Multi-severity error analysis")
    
    print(f"\n🚀 Graph-Sitter Enhanced Integration Demo Complete!")


if __name__ == "__main__":
    asyncio.run(main())

