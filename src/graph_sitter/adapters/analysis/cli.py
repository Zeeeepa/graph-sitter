"""
Analysis CLI Interface

Provides command-line interface for all analysis features.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .core.engine import AnalysisEngine
from .core.config import AnalysisConfig


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Graph-sitter Codebase Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/codebase
  %(prog)s . --format json --output results.json
  %(prog)s . --comprehensive --export-html analysis.html
  %(prog)s . --debug --verbose
        """
    )
    
    # Positional arguments
    parser.add_argument(
        'path',
        help='Path to codebase or repository'
    )
    
    # Analysis options
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run comprehensive analysis with all features'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run fast analysis with minimal features'
    )
    
    # Feature toggles
    parser.add_argument(
        '--enable-metrics',
        action='store_true',
        default=True,
        help='Enable code quality and complexity metrics'
    )
    
    parser.add_argument(
        '--enable-visualization',
        action='store_true',
        default=True,
        help='Enable tree-sitter visualization'
    )
    
    parser.add_argument(
        '--enable-detection',
        action='store_true',
        default=True,
        help='Enable pattern and dead code detection'
    )
    
    parser.add_argument(
        '--enable-ai',
        action='store_true',
        help='Enable AI-powered insights (requires API keys)'
    )
    
    # Output options
    parser.add_argument(
        '--format',
        choices=['json', 'html', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path'
    )
    
    parser.add_argument(
        '--export-html',
        help='Export HTML visualization to specified file'
    )
    
    # Graph-sitter options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--method-usages',
        action='store_true',
        default=True,
        help='Enable method usage resolution'
    )
    
    parser.add_argument(
        '--generics',
        action='store_true',
        default=True,
        help='Enable generic type resolution'
    )
    
    parser.add_argument(
        '--lazy-graph',
        action='store_true',
        help='Enable experimental lazy graph parsing'
    )
    
    # File filtering
    parser.add_argument(
        '--include-tests',
        action='store_true',
        default=True,
        help='Include test files in analysis'
    )
    
    parser.add_argument(
        '--include-docs',
        action='store_true',
        default=True,
        help='Include documentation files in analysis'
    )
    
    parser.add_argument(
        '--exclude',
        action='append',
        help='Exclude patterns (can be used multiple times)'
    )
    
    # API keys
    parser.add_argument(
        '--openai-key',
        help='OpenAI API key for AI features'
    )
    
    parser.add_argument(
        '--anthropic-key',
        help='Anthropic API key for AI features'
    )
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create analysis configuration
        config = create_config_from_args(args)
        
        # Create and run analysis engine
        engine = AnalysisEngine(config)
        result = engine.analyze_codebase(args.path)
        
        # Export results
        if args.output:
            output_path = engine.export_results(args.output)
            print(f"Results exported to: {output_path}")
        elif args.export_html:
            # Set format to HTML and export
            config.output_format = 'html'
            config.export_html = True
            engine.config = config
            output_path = engine.export_results(args.export_html)
            print(f"HTML visualization exported to: {output_path}")
        else:
            # Print to stdout
            if config.output_format == 'json':
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print_text_summary(result)
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def create_config_from_args(args) -> AnalysisConfig:
    """Create AnalysisConfig from command-line arguments."""
    config = AnalysisConfig()
    
    # Basic options
    config.debug = args.debug
    config.verbose = args.verbose
    config.include_tests = args.include_tests
    config.include_docs = args.include_docs
    config.output_format = args.format
    
    # Feature toggles
    if args.comprehensive:
        config.enable_metrics = True
        config.enable_visualization = True
        config.enable_pattern_detection = True
        config.enable_dead_code_detection = True
        config.enable_import_loop_detection = True
        config.method_usages = True
        config.generics = True
        config.full_range_index = True
    elif args.fast:
        config.enable_metrics = True
        config.enable_visualization = False
        config.enable_pattern_detection = False
        config.enable_dead_code_detection = False
        config.enable_import_loop_detection = False
        config.exp_lazy_graph = True
        config.method_usages = False
        config.generics = False
    else:
        config.enable_metrics = args.enable_metrics
        config.enable_visualization = args.enable_visualization
        config.enable_pattern_detection = args.enable_detection
        config.enable_dead_code_detection = args.enable_detection
        config.enable_import_loop_detection = args.enable_detection
    
    # AI features
    config.enable_ai_insights = args.enable_ai
    if args.openai_key:
        config.openai_api_key = args.openai_key
    if args.anthropic_key:
        config.anthropic_api_key = args.anthropic_key
    
    # Graph-sitter options
    config.method_usages = args.method_usages
    config.generics = args.generics
    config.exp_lazy_graph = args.lazy_graph
    
    # File filtering
    if args.exclude:
        config.exclude_patterns.extend(args.exclude)
    
    # HTML export
    if args.export_html:
        config.export_html = True
        config.html_template = args.export_html
    
    return config


def print_text_summary(result):
    """Print a text summary of analysis results."""
    print("=" * 60)
    print("CODEBASE ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Path: {result.codebase_path}")
    print(f"Language: {result.language}")
    print(f"Files: {result.total_files}")
    print(f"Lines: {result.total_lines}")
    print(f"Analysis Time: {result.analysis_time:.2f}s")
    print()
    
    # Quality metrics
    if result.quality_metrics:
        print("QUALITY METRICS")
        print("-" * 20)
        print(f"Maintainability Index: {result.quality_metrics.get('maintainability_index', 'N/A')}")
        overall = result.quality_metrics.get('overall_stats', {})
        if overall:
            print(f"Total Functions: {overall.get('total_functions', 'N/A')}")
            print(f"Total Classes: {overall.get('total_classes', 'N/A')}")
            print(f"Average Comment Ratio: {overall.get('average_comment_ratio', 'N/A'):.2%}")
        print()
    
    # Complexity metrics
    if result.complexity_metrics:
        print("COMPLEXITY METRICS")
        print("-" * 20)
        overall = result.complexity_metrics.get('overall_complexity', {})
        if overall:
            files = overall.get('files', {})
            functions = overall.get('functions', {})
            print(f"Average File Complexity: {files.get('avg_cyclomatic', 'N/A')}")
            print(f"Max File Complexity: {files.get('max_cyclomatic', 'N/A')}")
            print(f"Average Function Complexity: {functions.get('avg_cyclomatic', 'N/A')}")
            print(f"Max Function Complexity: {functions.get('max_cyclomatic', 'N/A')}")
        print()
    
    # Issues
    issues_count = len(result.import_loops) + len(result.dead_code) + len(result.patterns)
    if issues_count > 0:
        print("ISSUES DETECTED")
        print("-" * 20)
        print(f"Import Loops: {len(result.import_loops)}")
        print(f"Dead Code Items: {len(result.dead_code)}")
        print(f"Pattern Issues: {len(result.patterns)}")
        print()
    
    # Errors and warnings
    if result.errors:
        print("ERRORS")
        print("-" * 20)
        for error in result.errors:
            print(f"- {error}")
        print()
    
    if result.warnings:
        print("WARNINGS")
        print("-" * 20)
        for warning in result.warnings:
            print(f"- {warning}")
        print()


if __name__ == '__main__':
    main()

