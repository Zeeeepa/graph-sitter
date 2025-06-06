#!/usr/bin/env python3
"""
Analysis CLI

Command-line interface for codebase analysis.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .analyzer import CodebaseAnalyzer
from .config.analysis_config import AnalysisConfig


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Comprehensive codebase analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python -m graph_sitter.adapters.analysis.cli path/to/code
  
  # Quick analysis with JSON output
  python -m graph_sitter.adapters.analysis.cli path/to/code --quick --output results.json
  
  # Comprehensive analysis with HTML report
  python -m graph_sitter.adapters.analysis.cli path/to/code --comprehensive --html report.html
  
  # Tree-sitter analysis with visualization
  python -m graph_sitter.adapters.analysis.cli path/to/code --tree-sitter --visualize --output-dir analysis/
  
  # Export HTML report only
  python -m graph_sitter.adapters.analysis.cli path/to/code --export-html analysis.html
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "codebase_path",
        help="Path to the codebase to analyze"
    )
    
    # Analysis modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--quick",
        action="store_true",
        help="Perform quick analysis with minimal features"
    )
    mode_group.add_argument(
        "--comprehensive",
        action="store_true",
        help="Perform comprehensive analysis with all features"
    )
    
    # Feature flags
    parser.add_argument(
        "--tree-sitter",
        action="store_true",
        help="Enable tree-sitter integration and syntax analysis"
    )
    parser.add_argument(
        "--ai-analysis",
        action="store_true",
        help="Enable AI-powered code analysis"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Enable visualization generation"
    )
    parser.add_argument(
        "--no-dead-code",
        action="store_true",
        help="Disable dead code detection"
    )
    parser.add_argument(
        "--no-dependencies",
        action="store_true",
        help="Disable dependency analysis"
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Disable test analysis"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output file for analysis results"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for multiple analysis files"
    )
    parser.add_argument(
        "--export-html",
        help="Export HTML report to specified file"
    )
    parser.add_argument(
        "--export-json",
        help="Export JSON data to specified file"
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "text"],
        default="json",
        help="Output format (default: json)"
    )
    
    # Configuration options
    parser.add_argument(
        "--title",
        help="Custom title for reports"
    )
    parser.add_argument(
        "--include-source",
        action="store_true",
        help="Include source code snippets in reports"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=1000,
        help="Maximum number of files to analyze"
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=1024,
        help="Maximum file size to analyze (KB)"
    )
    
    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output"
    )
    
    return parser


def setup_logging(debug: bool = False, verbose: bool = False, quiet: bool = False):
    """Setup logging configuration."""
    if quiet:
        level = logging.ERROR
    elif debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_config_from_args(args) -> AnalysisConfig:
    """Create analysis configuration from command-line arguments."""
    if args.quick:
        config = AnalysisConfig.get_basic_config()
    elif args.comprehensive:
        config = AnalysisConfig.get_comprehensive_config()
    else:
        config = AnalysisConfig()
    
    # Apply feature flags
    if args.tree_sitter:
        config.enable_tree_sitter = True
    if args.ai_analysis:
        config.enable_ai_analysis = True
    if args.visualize:
        config.enable_visualization = True
        config.export_visualizations = True
    if args.no_dead_code:
        config.enable_dead_code_detection = False
    if args.no_dependencies:
        config.enable_dependency_analysis = False
    if args.no_tests:
        config.enable_test_analysis = False
    
    # Apply configuration options
    config.max_file_size_kb = args.max_file_size
    config.performance.max_files_per_batch = min(args.max_files, config.performance.max_files_per_batch)
    
    # Debug settings
    if args.debug:
        config.graph_sitter.debug = True
        config.performance.enable_memory_monitoring = True
        config.performance.enable_progress_reporting = True
    
    # Output format
    if args.format == "html":
        config.output_formats = {"html"}
    elif args.format == "text":
        config.output_formats = {"text"}
    else:
        config.output_formats = {"json"}
    
    return config


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug, args.verbose, args.quiet)
    logger = logging.getLogger(__name__)
    
    # Validate codebase path
    codebase_path = Path(args.codebase_path)
    if not codebase_path.exists():
        logger.error(f"Codebase path does not exist: {codebase_path}")
        sys.exit(1)
    
    try:
        # Create configuration
        config = create_config_from_args(args)
        
        # Create analyzer
        analyzer = CodebaseAnalyzer(config)
        
        # Handle different operation modes
        if args.export_html:
            # Export HTML report only
            success = analyzer.export_html(
                codebase_path,
                args.export_html,
                args.title,
                args.include_source
            )
            if success:
                print(f"HTML report exported to: {args.export_html}")
            else:
                logger.error("Failed to export HTML report")
                sys.exit(1)
                
        elif args.export_json:
            # Export JSON data only
            success = analyzer.export_json(codebase_path, args.export_json)
            if success:
                print(f"JSON data exported to: {args.export_json}")
            else:
                logger.error("Failed to export JSON data")
                sys.exit(1)
                
        elif args.output_dir:
            # Full analysis with output directory
            if args.comprehensive:
                result = analyzer.comprehensive_analyze(codebase_path, args.output_dir)
            elif args.tree_sitter:
                result = analyzer.analyze_with_tree_sitter(codebase_path, args.output_dir)
            else:
                result = analyzer.analyze(codebase_path, args.output_dir)
            
            print(f"Analysis completed. Results saved to: {args.output_dir}")
            print_summary(result)
            
        elif args.output:
            # Analysis with single output file
            if args.quick:
                result = analyzer.quick_analyze(codebase_path, args.output)
            else:
                result = analyzer.analyze(codebase_path)
                analyzer._save_result(result, args.output)
            
            print(f"Analysis completed. Results saved to: {args.output}")
            print_summary(result)
            
        else:
            # Analysis with console output
            if args.quick:
                result = analyzer.quick_analyze(codebase_path)
            elif args.comprehensive:
                result = analyzer.comprehensive_analyze(codebase_path, "analysis_output")
            else:
                result = analyzer.analyze(codebase_path)
            
            print_summary(result)
            
            # Print issues if any
            if result.issues:
                print("\n🚨 Issues Found:")
                for issue in result.issues[:10]:  # Show first 10 issues
                    severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.get("severity", "info"), "⚪")
                    print(f"  {severity_icon} {issue.get('type', 'Unknown')}: {issue.get('message', 'No message')}")
                
                if len(result.issues) > 10:
                    print(f"  ... and {len(result.issues) - 10} more issues")
    
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_summary(result):
    """Print a summary of analysis results."""
    print("\n📊 Analysis Summary")
    print("=" * 50)
    
    # Codebase overview
    if result.codebase_summary:
        nodes = result.codebase_summary.get("nodes", {})
        print(f"📁 Files: {nodes.get('files', 0)}")
        print(f"🔧 Functions: {nodes.get('functions', 0)}")
        print(f"🏗️  Classes: {nodes.get('classes', 0)}")
        print(f"📦 Symbols: {nodes.get('symbols', 0)}")
    
    # Metrics
    if result.metrics:
        quality = result.metrics.get("quality_metrics", {})
        print(f"\n📈 Quality Metrics")
        print(f"  Test Coverage: {quality.get('test_coverage_estimate', 0) * 100:.1f}%")
        print(f"  Dead Code Items: {quality.get('dead_code_count', 0)}")
        print(f"  Issues Found: {quality.get('issue_count', 0)}")
    
    # Execution info
    print(f"\n⏱️  Execution Time: {result.execution_time:.2f}s")
    print(f"📅 Generated: {result.timestamp}")


if __name__ == "__main__":
    main()

