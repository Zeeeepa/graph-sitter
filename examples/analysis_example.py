#!/usr/bin/env python3
"""
Comprehensive example demonstrating the graph-sitter analysis functionality.

This example shows how to use the analysis module to perform comprehensive
code analysis following the patterns from https://graph-sitter.com/tutorials/at-a-glance
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    """Main example function."""
    print("🔍 Graph-sitter Analysis Example")
    print("=" * 50)
    
    try:
        # Method 1: Using Codebase class (preferred)
        print("\n📋 Method 1: Using Codebase.Analysis()")
        print("-" * 40)
        
        try:
            from graph_sitter import Codebase
            
            # Analyze local repository
            codebase = Codebase(".")
            result = codebase.Analysis()
            
            print("✅ Successfully used Codebase.Analysis()")
            print_summary(result)
            
        except ImportError as e:
            print(f"⚠️  Codebase import failed (expected in some environments): {e}")
            print("   Falling back to direct analysis...")
        
        # Method 2: Direct analysis (always works)
        print("\n📋 Method 2: Direct Analysis")
        print("-" * 40)
        
        from graph_sitter.adapters.analysis import analyze_codebase, format_analysis_results
        
        # Analyze the analysis module itself
        analysis_path = Path(__file__).parent.parent / "src" / "graph_sitter" / "adapters" / "analysis"
        result = analyze_codebase(analysis_path)
        
        print("✅ Successfully performed direct analysis")
        print_summary(result)
        
        # Method 3: Detailed analysis with custom reporting
        print("\n📋 Method 3: Detailed Analysis Report")
        print("-" * 40)
        
        show_detailed_analysis(result)
        
        # Method 4: JSON output
        print("\n📋 Method 4: JSON Output")
        print("-" * 40)
        
        import json
        json_data = result.to_dict()
        print("✅ JSON conversion successful")
        print(f"   JSON keys: {list(json_data.keys())}")
        print(f"   Summary: {json_data['summary']}")
        
    except Exception as e:
        print(f"❌ Error in example: {e}")
        import traceback
        traceback.print_exc()


def print_summary(result):
    """Print a summary of analysis results."""
    print(f"   📁 Files analyzed: {result.total_files}")
    print(f"   🔧 Functions found: {result.total_functions}")
    print(f"   🏗️  Classes found: {result.total_classes}")
    print(f"   📏 Total lines: {result.total_lines}")
    print(f"   💀 Dead code items: {len(result.dead_code_items)}")
    print(f"   ⚠️  Issues found: {len(result.issues)}")
    print(f"   📊 Maintainability: {result.maintainability_index:.1f}/100")


def show_detailed_analysis(result):
    """Show detailed analysis results."""
    from graph_sitter.adapters.analysis import format_analysis_results
    
    # Show formatted results (truncated for example)
    formatted = format_analysis_results(result)
    lines = formatted.split('\n')
    
    print("📋 Formatted Analysis Results (first 20 lines):")
    for i, line in enumerate(lines[:20]):
        print(f"   {line}")
    
    if len(lines) > 20:
        print(f"   ... and {len(lines) - 20} more lines")
    
    # Show some specific examples
    if result.dead_code_items:
        print(f"\n💀 Dead Code Examples:")
        for item in result.dead_code_items[:3]:
            print(f"   • {item.type.title()}: {item.name}")
            print(f"     Location: {item.file_path}:{item.line_start}-{item.line_end}")
            print(f"     Reason: {item.reason}")
    
    if result.issues:
        print(f"\n⚠️  Issue Examples:")
        for issue in result.issues[:3]:
            print(f"   • {issue.severity.title()}: {issue.message}")
            print(f"     Location: {issue.file_path}:{issue.line_start}")
    
    if result.function_metrics:
        print(f"\n🔧 Complex Functions:")
        complex_funcs = sorted(result.function_metrics, 
                             key=lambda x: x.cyclomatic_complexity, 
                             reverse=True)[:3]
        for func in complex_funcs:
            print(f"   • {func.name} (complexity: {func.cyclomatic_complexity})")
            print(f"     Location: {func.file_path}:{func.line_start}-{func.line_end}")


def demonstrate_api_usage():
    """Demonstrate the API as specified in the requirements."""
    print("\n🎯 API Usage Demonstration")
    print("=" * 50)
    
    # This demonstrates the exact API requested by the user
    examples = [
        "# Analyze local repository",
        "codebase = Codebase('path/to/git/repo')",
        "result = codebase.Analysis()",
        "",
        "# Analyze remote repository",
        "codebase = Codebase.from_repo('fastapi/fastapi')",
        "result = codebase.Analysis()",
        "",
        "# Expected output format:",
        "# Analysis Results:",
        "#   • Total Files: 100",
        "#   • Total Functions: 2",
        "#   • Total Classes: 2",
        "#",
        "#   • Dead Code Items: 2",
        "# 'location' 'range of dead code and functions/classes included in it'",
        "# graph_sitter/src/graph_sitter/adapters/analysis.py 'xxx' 'xxxxxx'",
        "#",
        "#   • Issues: 2"
    ]
    
    for line in examples:
        print(f"   {line}")


if __name__ == "__main__":
    main()
    demonstrate_api_usage()
    print("\n✅ Example completed successfully!")
    print("\n💡 Try running this example with different repository paths!")
    print("   python examples/analysis_example.py")

