#!/usr/bin/env python3
"""
Standalone Analysis CLI

A simple CLI interface for testing the unified analysis system.
"""

import sys
import os
import argparse
import json
import time

# Add the analysis module to path
sys.path.insert(0, 'src/graph_sitter/adapters/analysis')

try:
    from tools.unified_analyzer import UnifiedCodebaseAnalyzer
    from quick_analyze import quick_analyze, get_codebase_summary, analyze_quality_metrics
    from config.analysis_config import AnalysisConfig, PresetConfigs
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import analysis modules: {e}")
    ANALYSIS_AVAILABLE = False


def format_results(results, format_type="text"):
    """Format analysis results."""
    if format_type == "json":
        return json.dumps(results, indent=2, default=str)
    
    # Text format
    output = []
    output.append("🚀 ANALYSIS RESULTS")
    output.append("=" * 50)
    
    if "summary" in results:
        summary = results["summary"]
        if "overview" in summary:
            overview = summary["overview"]
            output.append(f"📁 Files: {overview.get('total_files', 0):,}")
            output.append(f"🔧 Functions: {overview.get('total_functions', 0):,}")
            output.append(f"📝 Lines: {overview.get('total_lines', 0):,}")
        
        if "quality_metrics" in summary:
            quality = summary["quality_metrics"]
            output.append(f"🎯 Maintainability: {quality.get('average_maintainability_index', 0)}")
            output.append(f"🌀 Complexity: {quality.get('average_cyclomatic_complexity', 0)}")
    
    if "basic_metrics" in results:
        metrics = results["basic_metrics"]
        output.append(f"📁 Files: {metrics.get('total_files', 0):,}")
        output.append(f"🔧 Functions: {metrics.get('total_functions', 0):,}")
        output.append(f"📝 Lines: {metrics.get('total_lines', 0):,}")
        output.append(f"💬 Comment Density: {metrics.get('comment_density', 0):.1f}%")
    
    return "\n".join(output)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Standalone Analysis CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--quick", action="store_true", help="Quick analysis only")
    parser.add_argument("--comprehensive", action="store_true", help="Comprehensive analysis")
    parser.add_argument("--quality", action="store_true", help="Quality metrics only")
    parser.add_argument("--summary", action="store_true", help="Codebase summary")
    parser.add_argument("--no-graph-sitter", action="store_true", help="Disable graph-sitter")
    
    args = parser.parse_args()
    
    if not ANALYSIS_AVAILABLE:
        print("❌ Analysis modules not available")
        return 1
    
    if not os.path.exists(args.path):
        print(f"❌ Path does not exist: {args.path}")
        return 1
    
    print(f"🔍 Analyzing: {args.path}")
    start_time = time.time()
    
    try:
        use_graph_sitter = not args.no_graph_sitter
        
        if args.quick:
            print("⚡ Running quick analysis...")
            results = quick_analyze(args.path, use_graph_sitter=use_graph_sitter)
        
        elif args.quality:
            print("🎯 Running quality metrics analysis...")
            results = analyze_quality_metrics(args.path)
        
        elif args.summary:
            print("📊 Generating codebase summary...")
            results = get_codebase_summary(args.path)
        
        elif args.comprehensive:
            print("🚀 Running comprehensive analysis...")
            analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=use_graph_sitter)
            results = analyzer.analyze_comprehensive(args.path)
        
        else:
            print("📈 Running standard analysis...")
            analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=use_graph_sitter)
            core_result = analyzer.analyze_codebase(args.path)
            results = {
                "basic_metrics": {
                    "total_files": core_result.total_files,
                    "total_functions": core_result.total_functions,
                    "total_classes": getattr(core_result, 'total_classes', 0),
                    "total_lines": core_result.total_lines,
                    "comment_density": core_result.comment_density
                },
                "quality_metrics": {
                    "maintainability_index": core_result.average_maintainability_index,
                    "cyclomatic_complexity": core_result.average_cyclomatic_complexity,
                    "technical_debt_ratio": core_result.technical_debt_ratio
                },
                "analysis_time": core_result.analysis_time
            }
        
        analysis_time = time.time() - start_time
        print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
        
        # Format and output results
        formatted_output = format_results(results, args.format)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(formatted_output)
            print(f"💾 Results saved to: {args.output}")
        else:
            print("\n" + formatted_output)
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

