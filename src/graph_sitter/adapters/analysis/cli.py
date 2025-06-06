#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE ANALYSIS CLI 🚀

Simple command-line interface for the comprehensive analysis system.
Consolidates all analysis functionality into easy-to-use commands.

Usage:
    python -m graph_sitter.adapters.analysis.cli <path>
    python -m graph_sitter.adapters.analysis.cli <path> --comprehensive
    python -m graph_sitter.adapters.analysis.cli <path> --quick
    python -m graph_sitter.adapters.analysis.cli <path> --output results.json
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from .core.engine import (
    ComprehensiveAnalysisEngine, 
    AnalysisConfig, 
    analyze_codebase, 
    quick_analysis
)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="🚀 Comprehensive Codebase Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/code                    # Basic analysis
  %(prog)s /path/to/code --comprehensive    # Full analysis with all features
  %(prog)s /path/to/code --quick            # Quick analysis (basic metrics only)
  %(prog)s /path/to/code --output results.json  # Save results to file
  %(prog)s /path/to/code --no-import-loops  # Skip import loop detection
  %(prog)s /path/to/code --training-data    # Generate training data for ML
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "path",
        help="Path to the codebase to analyze"
    )
    
    # Analysis options
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Enable all analysis features (default)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick analysis with basic metrics only"
    )
    
    parser.add_argument(
        "--no-import-loops",
        action="store_true",
        help="Skip import loop detection"
    )
    
    parser.add_argument(
        "--no-dead-code",
        action="store_true",
        help="Skip dead code detection"
    )
    
    parser.add_argument(
        "--training-data",
        action="store_true",
        help="Generate training data for ML models"
    )
    
    parser.add_argument(
        "--no-graph-analysis",
        action="store_true",
        help="Skip graph structure analysis"
    )
    
    # Configuration options
    parser.add_argument(
        "--no-advanced-config",
        action="store_true",
        help="Disable advanced CodebaseConfig features"
    )
    
    parser.add_argument(
        "--include-external",
        action="store_true",
        help="Include external modules in analysis"
    )
    
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output file path for results (JSON format)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "summary"],
        default="summary",
        help="Output format (default: summary)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    return parser


def create_config_from_args(args) -> AnalysisConfig:
    """Create analysis configuration from command-line arguments."""
    if args.quick:
        return AnalysisConfig(
            detect_import_loops=False,
            detect_dead_code=False,
            generate_training_data=False,
            analyze_graph_structure=True,
            use_advanced_config=not args.no_advanced_config
        )
    
    return AnalysisConfig(
        use_advanced_config=not args.no_advanced_config,
        detect_import_loops=not args.no_import_loops,
        detect_dead_code=not args.no_dead_code,
        generate_training_data=args.training_data,
        analyze_graph_structure=not args.no_graph_analysis,
        ignore_external_modules=not args.include_external,
        ignore_test_files=not args.include_tests
    )


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
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"❌ Error: Path '{path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Configure logging based on verbosity
    import logging
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    elif args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING)
    
    try:
        if not args.quiet:
            print(f"🔍 Analyzing codebase: {path}")
            if args.quick:
                print("⚡ Quick analysis mode")
            elif args.comprehensive or not any([args.no_import_loops, args.no_dead_code]):
                print("🚀 Comprehensive analysis mode")
        
        # Perform analysis
        if args.quick:
            result_dict = quick_analysis(path)
            
            if not args.quiet:
                print("\n📊 Quick Analysis Results:")
                print(f"Files: {result_dict['files']}")
                print(f"Functions: {result_dict['functions']}")
                print(f"Classes: {result_dict['classes']}")
                print(f"Imports: {result_dict['imports']}")
                print(f"Analysis Time: {result_dict['analysis_time']:.2f}s")
            
            # Save results if requested
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(result_dict, f, indent=2, default=str)
                if not args.quiet:
                    print(f"\n💾 Results saved to: {args.output}")
        
        else:
            # Full analysis
            config = create_config_from_args(args)
            result = analyze_codebase(path, config)
            
            # Output results
            if args.format == "json" or args.output:
                if args.output:
                    result.save_to_file(args.output)
                    if not args.quiet:
                        print(f"💾 Results saved to: {args.output}")
                else:
                    print(result.to_json())
            else:
                if not args.quiet:
                    print_summary(result, args.verbose)
    
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

