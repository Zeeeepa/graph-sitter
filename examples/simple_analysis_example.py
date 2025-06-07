#!/usr/bin/env python3
"""
🚀 SUPER COMPREHENSIVE SINGLE-MODE ANALYSIS EXAMPLE 🚀

This example demonstrates the simplest way to perform comprehensive
codebase analysis with interactive exploration capabilities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.contexten.extensions.graph_sitter.code_analysis import analyze_codebase

def main():
    """Example of super comprehensive single-mode analysis."""
    
    print("🚀 SUPER COMPREHENSIVE ANALYSIS EXAMPLE")
    print("=" * 50)
    
    # Example 1: Simple comprehensive analysis
    print("\n📊 Example 1: Basic comprehensive analysis")
    result = analyze_codebase(".", auto_open=False, include_interactive=False)
    print(result)
    
    # Example 2: Analysis with interactive exploration
    print("\n🌐 Example 2: Analysis with interactive web interface")
    print("(This would open a browser with interactive analysis)")
    # result = analyze_codebase(".", auto_open=True, include_interactive=True)
    
    # Example 3: Programmatic access to results
    print("\n���� Example 3: Programmatic access to results")
    if result.total_files > 0:
        print(f"Quality Score: {result.quality_score:.1f}/10")
        print(f"Files analyzed: {result.total_files}")
        print(f"Functions found: {result.total_functions}")
        print(f"Classes found: {result.total_classes}")
        
        if result.import_loops > 0:
            print(f"⚠️  Import loops detected: {result.import_loops}")
        if result.dead_code_items > 0:
            print(f"🗑️  Dead code items: {result.dead_code_items}")
        if result.security_issues > 0:
            print(f"🔒 Security issues: {result.security_issues}")
    else:
        print("No files found to analyze (dependencies not available)")
    
    # Quick analysis example
    print("\n" + "="*50)
    print("QUICK ANALYSIS EXAMPLE")
    print("="*50)
    
    from src.contexten.extensions.graph_sitter.code_analysis import quick_analyze

    # Example 4: Different analysis modes
    print("\n⚡ Example 4: Quick analysis mode")
    quick_result = quick_analyze(".")
    print(f"Quick analysis completed in {quick_result.analysis_time:.2f}s")
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    main()
