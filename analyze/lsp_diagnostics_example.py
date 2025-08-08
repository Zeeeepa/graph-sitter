#!/usr/bin/env python3
"""
Example: Transaction-Aware LSP Integration with Graph-Sitter

This example demonstrates how to use Graph-Sitter's new LSP integration
to get real-time error detection and diagnostic information that stays
synchronized with codebase changes.
"""

import sys
from pathlib import Path

# Add the src directory to the path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter import Codebase
from graph_sitter.core.diagnostics import add_diagnostic_capabilities


def main():
    """Demonstrate LSP integration with Graph-Sitter."""
    
    print("🚀 Graph-Sitter LSP Integration Demo")
    print("=" * 50)
    
    # Initialize codebase with LSP integration
    # Note: This will automatically include diagnostic capabilities if available
    try:
        codebase = Codebase("./", enable_lsp=True)
        print(f"✅ Codebase initialized: {codebase.name}")
        print(f"📁 Repository path: {codebase.repo_path}")
        print(f"🔧 Language: {codebase.language}")
    except Exception as e:
        print(f"❌ Failed to initialize codebase: {e}")
        return
    
    # Check LSP status
    print("\n🔍 LSP Integration Status:")
    print("-" * 30)
    
    if hasattr(codebase, 'is_lsp_enabled'):
        lsp_enabled = codebase.is_lsp_enabled()
        print(f"LSP Enabled: {'✅ Yes' if lsp_enabled else '❌ No'}")
        
        if lsp_enabled:
            status = codebase.get_lsp_status()
            print(f"Serena Available: {'✅ Yes' if status.get('serena_available') else '❌ No'}")
            print(f"Bridge Initialized: {'✅ Yes' if status.get('bridge_initialized') else '❌ No'}")
            print(f"Cached Files: {status.get('cached_files', 0)}")
        else:
            print("💡 To enable LSP integration, install Serena dependencies:")
            print("   pip install graph-sitter[serena]")
    else:
        print("❌ LSP integration not available")
        print("💡 Make sure diagnostic capabilities are properly imported")
    
    # Demonstrate error detection
    print("\n🐛 Error Detection:")
    print("-" * 20)
    
    if hasattr(codebase, 'errors'):
        errors = codebase.errors
        print(f"Total errors found: {len(errors)}")
        
        if errors:
            print("\n📋 Error Details:")
            for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
                print(f"\n{i}. {error.file_path}:{error.line}:{error.column}")
                print(f"   Severity: {error.severity.upper()}")
                print(f"   Message: {error.message}")
                if error.code:
                    print(f"   Code: {error.code}")
                
                # Show context for first error
                if i == 1:
                    print(f"\n   Context:")
                    context = error.get_context(lines_before=2, lines_after=2)
                    for line in context.split('\n'):
                        print(f"   {line}")
        else:
            print("🎉 No errors found in the codebase!")
    else:
        print("❌ Error detection not available")
    
    # Demonstrate warnings
    print(f"\n⚠️  Warning Detection:")
    print("-" * 22)
    
    if hasattr(codebase, 'warnings'):
        warnings = codebase.warnings
        print(f"Total warnings found: {len(warnings)}")
        
        if warnings:
            for i, warning in enumerate(warnings[:3], 1):  # Show first 3 warnings
                print(f"{i}. {warning.file_path}:{warning.line} - {warning.message}")
        else:
            print("✨ No warnings found!")
    else:
        print("❌ Warning detection not available")
    
    # Demonstrate hints
    print(f"\n💡 Hints and Suggestions:")
    print("-" * 25)
    
    if hasattr(codebase, 'hints'):
        hints = codebase.hints
        print(f"Total hints found: {len(hints)}")
        
        if hints:
            for i, hint in enumerate(hints[:3], 1):  # Show first 3 hints
                print(f"{i}. {hint.file_path}:{hint.line} - {hint.message}")
        else:
            print("👍 No hints available")
    else:
        print("❌ Hint detection not available")
    
    # Demonstrate file-specific diagnostics
    print(f"\n📄 File-Specific Diagnostics:")
    print("-" * 30)
    
    if hasattr(codebase, 'get_file_diagnostics'):
        # Find a Python file to analyze
        python_files = [f for f in codebase.files if f.path.suffix == '.py']
        
        if python_files:
            sample_file = python_files[0]
            file_diagnostics = codebase.get_file_diagnostics(str(sample_file.path))
            
            print(f"Analyzing: {sample_file.path}")
            print(f"Diagnostics found: {len(file_diagnostics)}")
            
            for diag in file_diagnostics[:2]:  # Show first 2 diagnostics
                print(f"  - Line {diag.line}: {diag.message} ({diag.severity})")
        else:
            print("No Python files found for analysis")
    else:
        print("❌ File-specific diagnostics not available")
    
    # Demonstrate transaction-aware updates
    print(f"\n🔄 Transaction-Aware Updates:")
    print("-" * 32)
    
    if hasattr(codebase, 'refresh_diagnostics'):
        print("Refreshing diagnostic information...")
        codebase.refresh_diagnostics()
        print("✅ Diagnostics refreshed")
        
        # Show updated counts
        if hasattr(codebase, 'diagnostics'):
            total_diagnostics = len(codebase.diagnostics)
            print(f"Total diagnostics after refresh: {total_diagnostics}")
    else:
        print("❌ Diagnostic refresh not available")
    
    # Summary
    print(f"\n📊 Summary:")
    print("-" * 12)
    
    if hasattr(codebase, 'diagnostics'):
        all_diagnostics = codebase.diagnostics
        error_count = len([d for d in all_diagnostics if d.severity == 'error'])
        warning_count = len([d for d in all_diagnostics if d.severity == 'warning'])
        hint_count = len([d for d in all_diagnostics if d.severity in ['hint', 'information']])
        
        print(f"🔴 Errors: {error_count}")
        print(f"🟡 Warnings: {warning_count}")
        print(f"🔵 Hints: {hint_count}")
        print(f"📈 Total: {len(all_diagnostics)}")
    else:
        print("❌ Diagnostic summary not available")
    
    print(f"\n🎯 Integration Features Demonstrated:")
    print("  ✅ Real-time error detection")
    print("  ✅ Transaction-aware diagnostics")
    print("  ✅ File-specific analysis")
    print("  ✅ Multi-severity diagnostics (errors, warnings, hints)")
    print("  ✅ Contextual error information")
    print("  ✅ LSP status monitoring")
    
    print(f"\n🚀 Graph-Sitter + Serena LSP Integration Complete!")


if __name__ == "__main__":
    main()
