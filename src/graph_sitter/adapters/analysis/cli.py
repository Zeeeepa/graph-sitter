#!/usr/bin/env python3
"""
🚀 ENHANCED COMPREHENSIVE ANALYSIS CLI 🚀

Command-line interface for the enhanced comprehensive analysis system.
Supports all advanced features including import loop detection, dead code analysis,
training data generation, graph structure analysis, and enhanced metrics.

Usage:
    python -m graph_sitter.adapters.analysis.cli /path/to/code
    python -m graph_sitter.adapters.analysis.cli . --comprehensive
    python -m graph_sitter.adapters.analysis.cli . --import-loops --dead-code
    python -m graph_sitter.adapters.analysis.cli . --training-data --output training.json
    python -m graph_sitter.adapters.analysis.cli . --enhanced-metrics --graph-analysis
    python -m graph_sitter.adapters.analysis.cli . --quick --quiet
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from .core.engine import ComprehensiveAnalysisEngine, AnalysisConfig, AnalysisPresets, AnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all enhanced options."""
    parser = argparse.ArgumentParser(
        description="🚀 Enhanced Comprehensive Codebase Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/code                    # Basic analysis
  %(prog)s . --comprehensive               # Full comprehensive analysis
  %(prog)s . --import-loops --dead-code    # Specific analysis types
  %(prog)s . --training-data --output ml_data.json  # Generate ML training data
  %(prog)s . --enhanced-metrics --graph-analysis    # Advanced metrics and graph analysis
  %(prog)s . --quick --quiet               # Fast analysis with minimal output
  %(prog)s . --preset quality             # Use quality-focused preset
  %(prog)s . --preset performance         # Use performance-focused preset

Analysis Types:
  --import-loops        Detect circular import dependencies
  --dead-code          Find potentially unused code
  --training-data      Generate ML training data
  --graph-analysis     Analyze code graph structure
  --enhanced-metrics   Generate enhanced function/class metrics

Presets:
  comprehensive        Enable all analysis features (default)
  quality             Focus on code quality metrics
  performance         Fast analysis with essential features only
  minimal             Basic analysis only

Output Formats:
  json                Structured JSON output
  text                Human-readable text output
  summary             Brief summary only
        """
    )
    
    # Positional arguments
    parser.add_argument(
        'path',
        help='Path to the codebase to analyze'
    )
    
    # Analysis type options
    analysis_group = parser.add_argument_group('Analysis Options')
    analysis_group.add_argument(
        '--comprehensive',
        action='store_true',
        help='Enable all analysis features (import loops, dead code, training data, graph analysis, enhanced metrics)'
    )
    analysis_group.add_argument(
        '--import-loops',
        action='store_true',
        help='Detect circular import dependencies'
    )
    analysis_group.add_argument(
        '--dead-code',
        action='store_true',
        help='Find potentially unused code'
    )
    analysis_group.add_argument(
        '--training-data',
        action='store_true',
        help='Generate training data for ML models'
    )
    analysis_group.add_argument(
        '--graph-analysis',
        action='store_true',
        help='Analyze code graph structure and dependencies'
    )
    analysis_group.add_argument(
        '--enhanced-metrics',
        action='store_true',
        help='Generate enhanced function and class metrics'
    )
    
    # Preset options
    preset_group = parser.add_argument_group('Preset Configurations')
    preset_group.add_argument(
        '--preset',
        choices=['comprehensive', 'quality', 'performance', 'minimal'],
        help='Use predefined analysis configuration'
    )
    preset_group.add_argument(
        '--quick',
        action='store_true',
        help='Quick analysis (equivalent to --preset performance)'
    )
    
    # Performance options
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument(
        '--max-functions',
        type=int,
        default=100,
        help='Maximum number of functions to analyze for enhanced metrics (default: 100)'
    )
    perf_group.add_argument(
        '--max-classes',
        type=int,
        default=100,
        help='Maximum number of classes to analyze for enhanced metrics (default: 100)'
    )
    perf_group.add_argument(
        '--ignore-external',
        action='store_true',
        help='Ignore external modules in analysis'
    )
    perf_group.add_argument(
        '--ignore-tests',
        action='store_true',
        help='Ignore test files in analysis'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output', '-o',
        help='Output file path (default: stdout)'
    )
    output_group.add_argument(
        '--format', '-f',
        choices=['json', 'text', 'summary'],
        default='text',
        help='Output format (default: text)'
    )
    output_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    output_group.add_argument(
        '--no-recommendations',
        action='store_true',
        help='Suppress recommendations in output'
    )
    
    # Phase 2 features - Tree-sitter queries
    parser.add_argument('--query-patterns', action='store_true',
                       help='Enable tree-sitter query patterns analysis')
    parser.add_argument('--query-categories', nargs='+', 
                       default=['function', 'class', 'security', 'performance'],
                       help='Query pattern categories to execute')
    parser.add_argument('--custom-patterns', nargs='+', default=[],
                       help='Custom query pattern names to execute')
    
    # Phase 2 features - Visualization
    parser.add_argument('--html-report', action='store_true',
                       help='Generate interactive HTML report')
    parser.add_argument('--html-output', type=str,
                       help='Output path for HTML report')
    parser.add_argument('--report-theme', choices=['default', 'dark', 'light', 'professional'],
                       default='default', help='HTML report theme')
    
    # Phase 2 features - Performance optimization
    parser.add_argument('--enable-caching', action='store_true', default=True,
                       help='Enable result caching')
    parser.add_argument('--cache-backend', choices=['memory', 'file', 'redis'],
                       default='memory', help='Cache backend to use')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='Enable parallel processing')
    parser.add_argument('--max-workers', type=int,
                       help='Maximum number of worker threads/processes')
    
    # Phase 2 features - Advanced configuration
    parser.add_argument('--language', type=str,
                       help='Primary language of the codebase')
    parser.add_argument('--codebase-size', choices=['small', 'medium', 'large'],
                       default='medium', help='Size category of the codebase')
    parser.add_argument('--optimization-level', choices=['minimal', 'balanced', 'aggressive'],
                       default='balanced', help='Analysis optimization level')
    parser.add_argument('--lazy-graph', action='store_true', default=True,
                       help='Enable lazy graph loading')

    return parser


def create_config_from_args(args) -> AnalysisConfig:
    """Create AnalysisConfig from command line arguments."""
    
    # Handle presets first
    if args.preset:
        config = get_preset_config(args.preset)
    else:
        config = AnalysisConfig()
    
    # Override with specific arguments
    if hasattr(args, 'import_loops'):
        config.detect_import_loops = args.import_loops
    if hasattr(args, 'dead_code'):
        config.detect_dead_code = args.dead_code
    if hasattr(args, 'training_data'):
        config.generate_training_data = args.training_data
    if hasattr(args, 'graph_analysis'):
        config.analyze_graph_structure = args.graph_analysis
    if hasattr(args, 'enhanced_metrics'):
        config.enhanced_metrics = args.enhanced_metrics
    if hasattr(args, 'max_functions'):
        config.max_functions = args.max_functions
    if hasattr(args, 'max_classes'):
        config.max_classes = args.max_classes
    
    # Phase 2 features - Tree-sitter queries
    if hasattr(args, 'query_patterns'):
        config.enable_query_patterns = args.query_patterns
    if hasattr(args, 'query_categories'):
        config.query_categories = args.query_categories
    if hasattr(args, 'custom_patterns'):
        config.custom_query_patterns = args.custom_patterns
    
    # Phase 2 features - Visualization
    if hasattr(args, 'html_report'):
        config.generate_html_report = args.html_report
    if hasattr(args, 'html_output'):
        config.html_report_path = args.html_output
    if hasattr(args, 'report_theme'):
        config.report_theme = args.report_theme
    
    # Phase 2 features - Performance optimization
    if hasattr(args, 'enable_caching'):
        config.enable_caching = args.enable_caching
    if hasattr(args, 'cache_backend'):
        config.cache_backend = args.cache_backend
    if hasattr(args, 'parallel'):
        config.enable_parallel_processing = args.parallel
    if hasattr(args, 'max_workers'):
        config.max_workers = args.max_workers
    
    # Phase 2 features - Advanced configuration
    if hasattr(args, 'language'):
        config.codebase_language = args.language
    if hasattr(args, 'codebase_size'):
        config.codebase_size = args.codebase_size
    if hasattr(args, 'optimization_level'):
        config.optimization_level = args.optimization_level
    if hasattr(args, 'lazy_graph'):
        config.enable_lazy_graph = args.lazy_graph
    
    return config


def format_output(result: AnalysisResult, args) -> str:
    """Format analysis results for display."""
    
    output_format = getattr(args, 'output_format', getattr(args, 'format', 'text'))
    
    if output_format == 'json':
        return format_json_output(result)
    
    # Text output
    output = []
    
    # Header with enhanced information
    output.append("🚀 ENHANCED COMPREHENSIVE ANALYSIS REPORT")
    output.append("=" * 60)
    output.append(f"📁 Path: {result.path}")
    output.append(f"⏱️  Time: {result.analysis_time:.2f}s")
    output.append("")
    
    # Overview section
    output.append("📊 OVERVIEW")
    output.append(f"Files: {result.total_files}")
    output.append(f"Functions: {result.total_functions}")
    output.append(f"Classes: {result.total_classes}")
    output.append(f"Lines: {result.total_lines:,}")
    output.append("")
    
    # Analysis results
    output.append("🔍 ANALYSIS RESULTS")
    output.append(f"Import Loops: {len(result.import_loops)}")
    output.append(f"Dead Code Items: {len(result.dead_code)}")
    output.append(f"Training Data: {len(result.training_data)}")
    output.append(f"Enhanced Metrics: {len(result.enhanced_function_metrics)} functions, {len(result.enhanced_class_metrics)} classes")
    
    # Phase 2 results
    if result.query_results:
        output.append("")
        output.append("🌳 QUERY PATTERN RESULTS")
        total_matches = sum(result.pattern_matches.values())
        output.append(f"Total Patterns: {len(result.query_results)}")
        output.append(f"Total Matches: {total_matches}")
        
        if result.pattern_matches:
            output.append("Matches by Category:")
            for category, count in result.pattern_matches.items():
                output.append(f"  {category}: {count}")
    
    if result.performance_metrics:
        output.append("")
        output.append("⚡ PERFORMANCE METRICS")
        perf = result.performance_metrics
        if 'operation' in perf:
            op = perf['operation']
            output.append(f"Items Processed: {op.get('items_processed', 0)}")
            output.append(f"Items/Second: {op.get('items_per_second', 0):.1f}")
        
        if 'cache' in perf:
            cache = perf['cache']
            output.append(f"Cache Hit Rate: {cache.get('hit_rate', 0):.1%}")
            output.append(f"Cache Backend: {cache.get('backend', 'unknown')}")
        
        if 'memory' in perf:
            memory = perf['memory']
            output.append(f"Peak Memory: {memory.get('peak_mb', 0):.1f}MB")
    
    if result.html_report_path:
        output.append("")
        output.append("📊 INTERACTIVE REPORT")
        output.append(f"HTML Report: {result.html_report_path}")
    
    # Recommendations section
    quiet = getattr(args, 'quiet', False)
    if result.recommendations and not quiet:
        output.append("")
        output.append("💡 RECOMMENDATIONS")
        for i, rec in enumerate(result.recommendations[:5], 1):
            output.append(f"{i}. {rec}")
    
    return "\n".join(output)


def format_json_output(result: AnalysisResult) -> str:
    """Format result as JSON."""
    try:
        # Convert dataclass to dict, handling nested objects
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Error formatting JSON output: {e}")
        return json.dumps({"error": str(e)}, indent=2)


def print_summary(result, verbose: bool = False):
    """Print analysis results summary."""
    print("🚀 Comprehensive Codebase Analysis Results")
    print("=" * 50)
    
    # Basic statistics
    print(f"📁 Files: {result.total_files}")
    print(f"⚡ Functions: {result.total_functions}")
    print(f"🏗️  Classes: {result.total_classes}")
    print(f"📦 Imports: {result.total_imports}")
    print(f"⏱️  Analysis Time: {result.analysis_time:.2f}s")
    
    # Import loops
    if result.import_loops:
        print(f"\n🔄 Import Loops Found: {len(result.import_loops)}")
        if verbose:
            for i, loop in enumerate(result.import_loops[:5]):  # Show first 5
                print(f"  {i+1}. {' -> '.join(loop.files)} ({loop.severity})")
            if len(result.import_loops) > 5:
                print(f"  ... and {len(result.import_loops) - 5} more")
    
    # Dead code
    if result.dead_code:
        print(f"\n💀 Dead Code Items: {len(result.dead_code)}")
        if verbose:
            dead_by_type = {}
            for item in result.dead_code:
                dead_by_type[item.type] = dead_by_type.get(item.type, 0) + 1
            for code_type, count in dead_by_type.items():
                print(f"  {code_type.title()}s: {count}")
    
    # Training data
    if result.training_data:
        print(f"\n🤖 Training Data Items: {len(result.training_data)}")
    
    # Graph metrics
    if result.graph_metrics:
        print(f"\n📊 Graph Analysis:")
        if 'symbol_distribution' in result.graph_metrics:
            symbol_dist = result.graph_metrics['symbol_distribution']
            for symbol_type, count in list(symbol_dist.items())[:5]:
                print(f"  {symbol_type}: {count}")
        
        if 'file_extensions' in result.graph_metrics:
            file_ext = result.graph_metrics['file_extensions']
            print(f"  File types: {len(file_ext)}")
    
    print("\n✅ Analysis Complete!")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"❌ Error: Path '{path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create configuration
        config = create_config_from_args(args)
        
        # Create analysis engine
        engine = ComprehensiveAnalysisEngine()
        
        # Perform analysis
        if not args.quiet:
            print(f"🚀 Starting enhanced analysis of: {path}")
        
        result = engine.analyze(path, config)
        
        # Format output
        output = format_output(result, args)
        
        # Write output
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(output)
            if not args.quiet:
                print(f"📄 Results written to: {output_path}")
        else:
            print(output)
        
        # Exit with appropriate code
        if result.summary.get('issues', {}).get('critical_issues', 0) > 0:
            sys.exit(1)  # Critical issues found
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error during analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
