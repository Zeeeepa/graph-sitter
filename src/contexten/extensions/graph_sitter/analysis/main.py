#!/usr/bin/env python3
"""
🚀 UNIFIED CODEBASE ANALYSIS TOOL 🚀

A comprehensive, powerful executable that consolidates all analysis capabilities using
official tree-sitter patterns and methods. This tool has been completely rewritten
to use standardized tree-sitter integration and eliminate legacy technical debt.

Features:
- Official tree-sitter API integration (TSParser → TSLanguage → TSTree → TSNode)
- Standardized query patterns using tree-sitter Query objects
- Consolidated analysis engine with proper error handling
- Performance-optimized tree traversal using TreeCursor
- Field-based node access using official methods
- Proper dependency management (no more try/catch patterns)
- Unified interface for all analysis operations

Usage:
    python -m graph_sitter.adapters.analysis path/to/code
    python -m graph_sitter.adapters.analysis --repo fastapi/fastapi
    python -m graph_sitter.adapters.analysis . --format json --output results.json
    python -m graph_sitter.adapters.analysis . --comprehensive --visualize
    python -m graph_sitter.adapters.analysis . --quick-analyze
"""

import argparse
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import unified analysis components
from .unified_analyzer import UnifiedAnalyzer, CodebaseAnalysisResult
from .core.tree_sitter_core import get_tree_sitter_core

# Legacy imports for backward compatibility
from .core.models import AnalysisOptions, create_default_analysis_options

# ============================================================================
# OUTPUT FORMATTING FUNCTIONS
# ============================================================================

def format_analysis_results(results: Dict[str, Any], format_type: str = "text") -> str:
    """Format analysis results for output."""
    if format_type == "json":
        return json.dumps(results, indent=2, default=str)
    elif format_type == "yaml":
        try:
            import yaml
            return yaml.dump(results, default_flow_style=False)
        except ImportError:
            logger.warning("PyYAML not available, falling back to JSON")
            return json.dumps(results, indent=2, default=str)
    else:
        return format_text_output(results)


def format_text_output(results: Dict[str, Any]) -> str:
    """Format results as human-readable text."""
    output = []
    
    # Header
    output.append("🚀 UNIFIED CODEBASE ANALYSIS REPORT 🚀")
    output.append("=" * 60)
    
    # Analysis metadata
    if "analysis_metadata" in results:
        metadata = results["analysis_metadata"]
        output.append(f"📊 Analysis Type: {metadata.get('analyzer_type', 'unknown')}")
        output.append(f"🔧 Graph-Sitter: {'✅ Enabled' if metadata.get('graph_sitter_enabled') else '❌ Disabled'}")
        output.append(f"⚙️ Advanced Config: {'✅ Yes' if metadata.get('advanced_config') else '❌ No'}")
        output.append(f"⏱️ Total Time: {metadata.get('total_time', 0):.2f}s")
        output.append("")
    
    # Core analysis summary
    if "summary_statistics" in results:
        stats = results["summary_statistics"]
        output.append("📈 OVERVIEW")
        output.append("-" * 20)
        
        overview = stats.get("overview", {})
        output.append(f"📁 Files: {overview.get('total_files', 0):,}")
        output.append(f"🔧 Functions: {overview.get('total_functions', 0):,}")
        output.append(f"🏗️ Classes: {overview.get('total_classes', 0):,}")
        output.append(f"📝 Lines: {overview.get('total_lines', 0):,}")
        output.append(f"⚡ Speed: {overview.get('files_per_second', 0)} files/sec")
        output.append("")
        
        # Quality metrics
        quality = stats.get("quality_metrics", {})
        output.append("🎯 QUALITY METRICS")
        output.append("-" * 20)
        output.append(f"🔧 Maintainability Index: {quality.get('average_maintainability_index', 0)}")
        output.append(f"🌀 Cyclomatic Complexity: {quality.get('average_cyclomatic_complexity', 0)}")
        output.append(f"📊 Halstead Volume: {quality.get('average_halstead_volume', 0)}")
        output.append(f"💬 Comment Density: {quality.get('comment_density', 0)}%")
        output.append(f"⚠️ Technical Debt Ratio: {quality.get('technical_debt_ratio', 0)}")
        output.append("")
        
        # Issues summary
        issues = stats.get("issues_summary", {})
        output.append("🚨 ISSUES SUMMARY")
        output.append("-" * 20)
        output.append(f"📊 Total Issues: {issues.get('total_issues', 0)}")
        output.append(f"🔴 Critical: {issues.get('critical', 0)}")
        output.append(f"🟡 Major: {issues.get('major', 0)}")
        output.append(f"🔵 Minor: {issues.get('minor', 0)}")
        output.append(f"ℹ️ Info: {issues.get('info', 0)}")
        output.append(f"⏰ Estimated Debt: {issues.get('estimated_debt_hours', 0):.1f} hours")
        output.append("")
    
    # Enhanced analyses
    if "import_loops" in results and results["import_loops"].get("summary"):
        loop_summary = results["import_loops"]["summary"]
        output.append("🔄 IMPORT LOOPS")
        output.append("-" * 20)
        output.append(f"Total Loops: {loop_summary.get('total_loops', 0)}")
        output.append(f"🔴 Critical: {loop_summary.get('critical_loops', 0)}")
        output.append(f"🟡 Warning: {loop_summary.get('warning_loops', 0)}")
        output.append(f"ℹ️ Info: {loop_summary.get('info_loops', 0)}")
        
        recommendations = results["import_loops"].get("recommendations", [])
        if recommendations:
            output.append("\n💡 Recommendations:")
            for rec in recommendations:
                output.append(f"  • {rec}")
        output.append("")
    
    if "dead_code" in results and results["dead_code"].get("summary"):
        dead_summary = results["dead_code"]["summary"]
        output.append("🗑️ DEAD CODE")
        output.append("-" * 20)
        output.append(f"Total Items: {dead_summary.get('total_dead_code_items', 0)}")
        output.append(f"🔧 Functions: {dead_summary.get('dead_functions', 0)}")
        output.append(f"🏗️ Classes: {dead_summary.get('dead_classes', 0)}")
        output.append(f"📊 Variables: {dead_summary.get('dead_variables', 0)}")
        
        recommendations = results["dead_code"].get("recommendations", [])
        if recommendations:
            output.append("\n💡 Recommendations:")
            for rec in recommendations:
                output.append(f"  • {rec}")
        output.append("")
    
    if "training_data" in results and results["training_data"].get("metadata"):
        training_meta = results["training_data"]["metadata"]
        output.append("🤖 TRAINING DATA")
        output.append("-" * 20)
        output.append(f"Total Functions: {training_meta.get('total_functions', 0)}")
        output.append(f"Processed: {training_meta.get('processed_functions', 0)}")
        output.append(f"Coverage: {training_meta.get('coverage_percentage', 0):.1f}%")
        output.append(f"Avg Dependencies: {training_meta.get('avg_dependencies_per_function', 0):.1f}")
        output.append(f"Avg Usages: {training_meta.get('avg_usages_per_function', 0):.1f}")
        output.append("")
    
    if "graph_analysis" in results and results["graph_analysis"].get("graph_analysis"):
        graph_data = results["graph_analysis"]["graph_analysis"]
        output.append("🕸️ GRAPH STRUCTURE")
        output.append("-" * 20)
        output.append(f"Nodes: {graph_data.get('total_nodes', 0):,}")
        output.append(f"Edges: {graph_data.get('total_edges', 0):,}")
        output.append(f"Symbol Usage Edges: {graph_data.get('symbol_usage_edges', 0):,}")
        output.append(f"Import Resolution Edges: {graph_data.get('import_resolution_edges', 0):,}")
        output.append(f"Export Edges: {graph_data.get('export_edges', 0):,}")
        
        insights = results["graph_analysis"].get("insights", [])
        if insights:
            output.append("\n🔍 Insights:")
            for insight in insights:
                output.append(f"  • {insight}")
        output.append("")
    
    # Footer
    output.append("✅ Analysis Complete!")
    output.append("=" * 60)
    
    return "\n".join(output)


def save_analysis_results(results: Dict[str, Any], output_path: str, format_type: str = "json"):
    """Save analysis results to file."""
    try:
        formatted_output = format_analysis_results(results, format_type)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        
        logger.info(f"Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise


# ============================================================================
# REPOSITORY ANALYSIS (from original repo_analytics)
# ============================================================================

def analyze_repo(repo_url: str) -> Dict[str, Any]:
    """Analyze a repository and return comprehensive metrics."""
    if not GRAPH_SITTER_AVAILABLE:
        raise ImportError("Graph-sitter is required for repository analysis")
    
    try:
        analyzer = UnifiedAnalyzer(use_graph_sitter=True)
        result = analyze_from_repo(repo_url)
        
        # Get repository description
        try:
            import requests
            api_url = f"https://api.github.com/repos/{repo_url}"
            response = requests.get(api_url)
            if response.status_code == 200:
                repo_data = response.json()
                desc = repo_data.get("description", "No description available")
            else:
                desc = ""
        except Exception:
            desc = ""
        
        return {
            "repo_url": repo_url,
            "description": desc,
            "num_files": result.total_files,
            "num_functions": result.total_functions,
            "num_classes": result.total_classes,
            "line_metrics": {
                "total": {
                    "loc": result.total_lines,
                    "lloc": result.total_logical_lines,
                    "sloc": result.total_source_lines,
                    "comments": result.total_comment_lines,
                    "comment_density": result.comment_density,
                }
            },
            "cyclomatic_complexity": {
                "average": result.average_cyclomatic_complexity,
            },
            "depth_of_inheritance": {
                "average": result.average_depth_of_inheritance,
            },
            "halstead_metrics": {
                "total_volume": int(result.average_halstead_volume * result.total_functions),
                "average_volume": int(result.average_halstead_volume),
            },
            "maintainability_index": {
                "average": int(result.average_maintainability_index),
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing repository {repo_url}: {e}")
        raise


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="🚀 Unified Codebase Analysis Tool - Comprehensive code quality analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .                                    # Analyze current directory
  %(prog)s /path/to/code --comprehensive        # Full analysis with all features
  %(prog)s . --format json --output results.json  # Save results as JSON
  %(prog)s --repo fastapi/fastapi               # Analyze remote repository
  %(prog)s . --training-data --output ml.json  # Generate ML training data
  %(prog)s . --import-loops --dead-code        # Focus on specific analyses
  %(prog)s . --quick-analyze                   # Quick analysis only
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "path",
        nargs="?",
        help="Path to the codebase to analyze"
    )
    input_group.add_argument(
        "--repo",
        help="Remote repository to analyze (e.g., 'fastapi/fastapi')"
    )
    
    # Analysis options
    analysis_group = parser.add_argument_group("Analysis Options")
    analysis_group.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive analysis with all features"
    )
    analysis_group.add_argument(
        "--quick-analyze",
        action="store_true",
        help="Run quick analysis with basic metrics only"
    )
    analysis_group.add_argument(
        "--training-data",
        action="store_true",
        help="Generate training data for ML models"
    )
    analysis_group.add_argument(
        "--import-loops",
        action="store_true",
        help="Detect circular import dependencies"
    )
    analysis_group.add_argument(
        "--dead-code",
        action="store_true",
        help="Detect unused code"
    )
    analysis_group.add_argument(
        "--enhanced-metrics",
        action="store_true",
        help="Generate enhanced function and class metrics"
    )
    analysis_group.add_argument(
        "--graph-analysis",
        action="store_true",
        help="Perform graph structure analysis"
    )
    
    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--no-graph-sitter",
        action="store_true",
        help="Disable graph-sitter enhanced analysis"
    )
    config_group.add_argument(
        "--advanced-config",
        action="store_true",
        help="Use advanced graph-sitter configuration"
    )
    config_group.add_argument(
        "--extensions",
        nargs="+",
        default=[".py"],
        help="File extensions to analyze (default: .py)"
    )
    config_group.add_argument(
        "--max-complexity",
        type=int,
        default=10,
        help="Maximum allowed cyclomatic complexity (default: 10)"
    )
    config_group.add_argument(
        "--min-maintainability",
        type=int,
        default=20,
        help="Minimum maintainability index (default: 20)"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)"
    )
    output_group.add_argument(
        "--output",
        help="Output file path (prints to stdout if not specified)"
    )
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    output_group.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main():
    """Main entry point for the analysis tool."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Handle repository analysis (legacy compatibility)
        if args.repo:
            logger.info(f"Running repository analytics for: {args.repo}")
            results = analyze_repo(args.repo)
            
            # Format repo analytics output
            print("\n📊 Repository Analysis Report 📊")
            print("=" * 50)
            print(f"📁 Repository: {results['repo_url']}")
            print(f"📝 Description: {results['description']}")
            print("\n📈 Basic Metrics:")
            print(f"  • Files: {results['num_files']}")
            print(f"  • Functions: {results['num_functions']}")
            print(f"  • Classes: {results['num_classes']}")

            print("\n📏 Line Metrics:")
            line_metrics = results["line_metrics"]["total"]
            print(f"  • Lines of Code: {line_metrics['loc']:,}")
            print(f"  • Logical Lines: {line_metrics['lloc']:,}")
            print(f"  • Source Lines: {line_metrics['sloc']:,}")
            print(f"  • Comments: {line_metrics['comments']:,}")
            print(f"  • Comment Density: {line_metrics['comment_density']:.1f}%")

            print("\n🔄 Complexity Metrics:")
            print(f"  • Average Cyclomatic Complexity: {results['cyclomatic_complexity']['average']:.1f}")
            print(f"  • Average Maintainability Index: {results['maintainability_index']['average']}")
            print(f"  • Average Depth of Inheritance: {results['depth_of_inheritance']['average']:.1f}")
            print(f"  • Total Halstead Volume: {results['halstead_metrics']['total_volume']:,}")
            print(f"  • Average Halstead Volume: {results['halstead_metrics']['average_volume']:,}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Results saved to: {args.output}")
            
            return
        
        # Determine analysis path
        analysis_path = os.path.abspath(args.path)
        if not os.path.exists(analysis_path):
            logger.error(f"Path does not exist: {analysis_path}")
            sys.exit(1)
        
        logger.info(f"Analyzing local path: {analysis_path}")
        
        # Create analyzer
        use_graph_sitter = not args.no_graph_sitter
        analyzer = UnifiedAnalyzer(
            use_graph_sitter=use_graph_sitter,
            use_advanced_config=args.advanced_config
        )
        
        if use_graph_sitter and GRAPH_SITTER_AVAILABLE:
            logger.info("Using graph-sitter enhanced analysis")
        else:
            logger.info("Using AST-based analysis")
        
        # Configure analysis options
        options = create_default_analysis_options()
        options.extensions = args.extensions
        options.max_complexity = args.max_complexity
        options.min_maintainability = args.min_maintainability
        
        # Determine analysis type
        if args.comprehensive:
            logger.info("Running comprehensive analysis with all features...")
            options.include_dead_code = True
            options.include_import_loops = True
            options.include_training_data = True
            options.include_enhanced_metrics = True
            options.include_graph_analysis = True
            results = analyzer.analyze_comprehensive(analysis_path, options)
        
        elif args.quick_analyze:
            logger.info("Running quick analysis...")
            results = analyzer.quick_analyze(analysis_path)
        
        elif args.training_data:
            logger.info("Generating training data...")
            results = analyzer.analyze_for_ml_training(analysis_path)
        
        elif any([args.import_loops, args.dead_code, args.enhanced_metrics, args.graph_analysis]):
            logger.info("Running specialized analyses...")
            results = {}
            
            if args.import_loops:
                results["import_loops"] = analyzer.analyze_import_loops(analysis_path)
            if args.dead_code:
                results["dead_code"] = analyzer.analyze_dead_code(analysis_path)
            if args.enhanced_metrics:
                results["enhanced_metrics"] = analyzer.analyze_enhanced_metrics(analysis_path)
            if args.graph_analysis:
                results["graph_analysis"] = analyzer.analyze_graph_structure(analysis_path)
        
        else:
            logger.info("Running standard codebase analysis...")
            core_result = analyzer.analyze_codebase(analysis_path, options.extensions)
            results = {
                "core_analysis": core_result.__dict__,
                "summary_statistics": analyzer.quick_analyze(analysis_path)
            }
        
        # Format and output results
        formatted_output = format_analysis_results(results, args.format)
        
        if args.output:
            save_analysis_results(results, args.output, args.format)
            if not args.quiet:
                print(f"✅ Analysis complete! Results saved to {args.output}")
        else:
            print(formatted_output)
        
        # Exit with appropriate code based on issues found
        if "core_analysis" in results and "issues" in results["core_analysis"]:
            issues = results["core_analysis"]["issues"]
            critical_issues = len([i for i in issues if i.get("severity") == "critical"])
            major_issues = len([i for i in issues if i.get("severity") == "major"])
        else:
            critical_issues = major_issues = 0
        
        if critical_issues > 0:
            sys.exit(2)  # Critical issues found
        elif major_issues > 0:
            sys.exit(1)  # Major issues found
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


# ============================================================================
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# ============================================================================

def analyze_codebase(path: str, use_graph_sitter: bool = True) -> Dict[str, Any]:
    """Convenience function for programmatic use."""
    analyzer = UnifiedAnalyzer(use_graph_sitter=use_graph_sitter)
    result = analyzer.analyze_codebase(path)
    return result.__dict__


def analyze_comprehensive(path: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for comprehensive analysis."""
    analyzer = UnifiedAnalyzer(**kwargs)
    return analyzer.analyze_comprehensive(path)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
