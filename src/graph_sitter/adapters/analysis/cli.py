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

from .core.engine import ComprehensiveAnalysisEngine, AnalysisConfig, AnalysisPresets

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
    
    return parser


def create_config_from_args(args) -> AnalysisConfig:
    """Create analysis configuration from command line arguments."""
    
    # Handle presets first
    if args.preset:
        if args.preset == 'comprehensive':
            config = AnalysisPresets.comprehensive()
        elif args.preset == 'quality':
            config = AnalysisPresets.quality_focused()
        elif args.preset == 'performance':
            config = AnalysisPresets.performance()
        elif args.preset == 'minimal':
            config = AnalysisPresets.minimal()
        else:
            config = AnalysisConfig()
    elif args.quick:
        config = AnalysisPresets.performance()
    elif args.comprehensive:
        config = AnalysisPresets.comprehensive()
    else:
        # Create custom config based on individual flags
        config = AnalysisConfig(
            detect_import_loops=args.import_loops,
            detect_dead_code=args.dead_code,
            generate_training_data=args.training_data,
            analyze_graph_structure=args.graph_analysis,
            enhanced_metrics=args.enhanced_metrics
        )
    
    # Override with specific arguments
    if hasattr(args, 'max_functions'):
        config.max_functions = args.max_functions
    if hasattr(args, 'max_classes'):
        config.max_classes = args.max_classes
    if hasattr(args, 'ignore_external'):
        config.ignore_external_modules = args.ignore_external
    if hasattr(args, 'ignore_tests'):
        config.ignore_test_files = args.ignore_tests
    
    return config


def format_output(result, args):
    """Format analysis results based on output format."""
    if args.format == 'json':
        return json.dumps(result.__dict__, indent=2, default=str)
    elif args.format == 'summary':
        return f"""🚀 ENHANCED ANALYSIS SUMMARY
Path: {result.path}
Files: {result.total_files} | Functions: {result.total_functions} | Classes: {result.total_classes}
Analysis Time: {result.analysis_time:.2f}s
Import Loops: {len(result.import_loops)} | Dead Code: {len(result.dead_code)}
Training Data: {len(result.training_data)} items
"""
    else:  # text format
        return f"""🚀 ENHANCED COMPREHENSIVE ANALYSIS REPORT
{'='*60}
📁 Path: {result.path}
⏱️  Time: {result.analysis_time:.2f}s

📊 OVERVIEW
Files: {result.total_files}
Functions: {result.total_functions}
Classes: {result.total_classes}
Lines: {result.total_lines:,}

🔍 ANALYSIS RESULTS
Import Loops: {len(result.import_loops)}
Dead Code Items: {len(result.dead_code)}
Training Data: {len(result.training_data)}
Enhanced Metrics: {len(result.enhanced_function_metrics)} functions, {len(result.enhanced_class_metrics)} classes

💡 RECOMMENDATIONS
{chr(10).join(f'{i+1}. {rec}' for i, rec in enumerate(result.recommendations[:5]))}
"""


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
