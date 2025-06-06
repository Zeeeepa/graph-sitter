#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE ANALYSIS CLI - CONSOLIDATED FROM ALL PRs AND CODE FILES 🚀

Unified command-line interface that provides access to all analysis capabilities:
- All features from PRs #211, #212, #213, #214, #215
- Enhanced functionality from graph_sitter_enhancements.py
- Comprehensive analysis from legacy_analyze_codebase.py
- Advanced features from legacy_analyze_codebase_enhanced.py
- Enhanced analyzer capabilities from legacy_enhanced_analyzer.py

Features:
- Basic to comprehensive analysis modes
- Tree-sitter query patterns and visualization
- Quality metrics and complexity analysis
- Import loop detection and dead code analysis
- AI-powered insights and training data generation
- Interactive HTML reports with D3.js visualizations
- Graph-sitter integration with advanced settings
- Multiple output formats (JSON, HTML, text)
- Preset configurations for different use cases

Usage Examples:
    # Basic analysis
    python -m graph_sitter.adapters.analysis.cli /path/to/code
    
    # Comprehensive analysis with HTML report
    python -m graph_sitter.adapters.analysis.cli /path/to/code --comprehensive --export-html report.html
    
    # Tree-sitter analysis with visualization
    python -m graph_sitter.adapters.analysis.cli /path/to/code --tree-sitter --visualize --open-browser
    
    # Quality-focused analysis
    python -m graph_sitter.adapters.analysis.cli /path/to/code --preset quality
    
    # AI-powered analysis (requires API key)
    python -m graph_sitter.adapters.analysis.cli /path/to/code --ai-insights --api-key YOUR_KEY
    
    # Generate training data for ML
    python -m graph_sitter.adapters.analysis.cli /path/to/code --generate-training-data
    
    # Import loop detection
    python -m graph_sitter.adapters.analysis.cli /path/to/code --detect-import-loops
    
    # Dead code detection
    python -m graph_sitter.adapters.analysis.cli /path/to/code --detect-dead-code
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from .core.engine import AnalysisEngine
from .core.config import AnalysisConfig


class AnalysisPresets:
    """Predefined analysis configurations for common use cases."""
    
    @staticmethod
    def basic() -> AnalysisConfig:
        """Basic analysis with essential metrics."""
        return AnalysisConfig(
            enable_metrics=True,
            enable_pattern_detection=False,
            enable_visualization=False,
            enable_ai_insights=False,
            debug=False
        )
    
    @staticmethod
    def comprehensive() -> AnalysisConfig:
        """Comprehensive analysis with all features enabled."""
        return AnalysisConfig(
            enable_metrics=True,
            enable_pattern_detection=True,
            enable_visualization=True,
            enable_ai_insights=False,  # Requires API key
            enable_graph_sitter=True,
            debug=False
        )
    
    @staticmethod
    def quality_focused() -> AnalysisConfig:
        """Quality-focused analysis for code review."""
        return AnalysisConfig(
            enable_metrics=True,
            enable_pattern_detection=True,
            enable_visualization=False,
            enable_ai_insights=False,
            focus_on_quality=True,
            debug=False
        )
    
    @staticmethod
    def performance_focused() -> AnalysisConfig:
        """Performance-focused analysis for optimization."""
        return AnalysisConfig(
            enable_metrics=True,
            enable_pattern_detection=True,
            enable_visualization=True,
            enable_ai_insights=False,
            focus_on_performance=True,
            debug=False
        )
    
    @staticmethod
    def ai_powered() -> AnalysisConfig:
        """AI-powered analysis with insights and training data."""
        return AnalysisConfig(
            enable_metrics=True,
            enable_pattern_detection=True,
            enable_visualization=True,
            enable_ai_insights=True,
            generate_training_data=True,
            debug=False
        )

def create_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser with all options from all sources."""
    parser = argparse.ArgumentParser(
        description="🚀 Comprehensive Codebase Analysis Tool - Consolidated from All PRs and Code Files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/code                                    # Basic analysis
  %(prog)s /path/to/code --comprehensive                    # Full analysis
  %(prog)s /path/to/code --preset quality                   # Quality-focused
  %(prog)s /path/to/code --tree-sitter --visualize          # Tree-sitter visualization
  %(prog)s /path/to/code --ai-insights --api-key KEY        # AI-powered analysis
  %(prog)s /path/to/code --export-html report.html          # HTML report
  %(prog)s /path/to/code --detect-import-loops              # Import loop detection
  %(prog)s /path/to/code --detect-dead-code                 # Dead code detection
  %(prog)s /path/to/code --generate-training-data           # ML training data
        """
    )
    
    # Positional arguments
    parser.add_argument(
        'path',
        help='Path to codebase or repository to analyze'
    )
    
    # Analysis presets
    preset_group = parser.add_argument_group('Analysis Presets')
    preset_group.add_argument(
        '--preset',
        choices=['basic', 'comprehensive', 'quality', 'performance', 'ai'],
        help='Use predefined analysis configuration'
    )
    
    # Core analysis options
    core_group = parser.add_argument_group('Core Analysis Options')
    core_group.add_argument(
        '--comprehensive',
        action='store_true',
        help='Enable comprehensive analysis with all features'
    )
    core_group.add_argument(
        '--fast',
        action='store_true',
        help='Fast analysis with basic metrics only'
    )
    core_group.add_argument(
        '--metrics',
        action='store_true',
        help='Enable quality and complexity metrics'
    )
    core_group.add_argument(
        '--patterns',
        action='store_true',
        help='Enable pattern detection and code smells'
    )
    
    # Tree-sitter and visualization options
    viz_group = parser.add_argument_group('Visualization Options')
    viz_group.add_argument(
        '--tree-sitter',
        action='store_true',
        help='Enable tree-sitter query patterns and analysis'
    )
    viz_group.add_argument(
        '--visualize',
        action='store_true',
        help='Generate interactive visualizations'
    )
    viz_group.add_argument(
        '--export-html',
        metavar='FILE',
        help='Export HTML report with visualizations'
    )
    viz_group.add_argument(
        '--open-browser',
        action='store_true',
        help='Open HTML report in browser automatically'
    )
    
    # Detection options
    detection_group = parser.add_argument_group('Detection Options')
    detection_group.add_argument(
        '--detect-import-loops',
        action='store_true',
        help='Detect circular import dependencies'
    )
    detection_group.add_argument(
        '--detect-dead-code',
        action='store_true',
        help='Detect unused functions, classes, and variables'
    )
    detection_group.add_argument(
        '--detect-patterns',
        action='store_true',
        help='Detect code patterns and anti-patterns'
    )
    
    # AI and ML options
    ai_group = parser.add_argument_group('AI and ML Options')
    ai_group.add_argument(
        '--ai-insights',
        action='store_true',
        help='Generate AI-powered code insights'
    )
    ai_group.add_argument(
        '--generate-training-data',
        action='store_true',
        help='Generate training data for ML models'
    )
    ai_group.add_argument(
        '--api-key',
        metavar='KEY',
        help='API key for AI services (OpenAI, etc.)'
    )
    
    # Graph-sitter advanced options
    graph_group = parser.add_argument_group('Graph-sitter Advanced Options')
    graph_group.add_argument(
        '--enable-graph-sitter',
        action='store_true',
        help='Enable graph-sitter integration'
    )
    graph_group.add_argument(
        '--lazy-loading',
        action='store_true',
        help='Enable lazy graph loading for performance'
    )
    graph_group.add_argument(
        '--method-usages',
        action='store_true',
        help='Enable method usage resolution'
    )
    graph_group.add_argument(
        '--generics',
        action='store_true',
        help='Enable generic type resolution'
    )
    graph_group.add_argument(
        '--full-range-index',
        action='store_true',
        help='Enable complete range-to-node indexing'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output',
        '-o',
        metavar='FILE',
        help='Output file path'
    )
    output_group.add_argument(
        '--format',
        choices=['json', 'html', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    output_group.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )
    output_group.add_argument(
        '--debug',
        action='store_true',
        help='Debug mode with detailed logging'
    )
    output_group.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Quiet mode - minimal output'
    )
    
    # Legacy compatibility options
    legacy_group = parser.add_argument_group('Legacy Compatibility')
    legacy_group.add_argument(
        '--legacy-mode',
        action='store_true',
        help='Use legacy analysis mode for compatibility'
    )
    legacy_group.add_argument(
        '--include-tests',
        action='store_true',
        default=True,
        help='Include test files in analysis'
    )
    legacy_group.add_argument(
        '--include-docs',
        action='store_true',
        default=True,
        help='Include documentation files in analysis'
    )
    
    return parser

def configure_logging(args):
    """Configure logging based on command line arguments."""
    if args.quiet:
        level = logging.WARNING
    elif args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_config_from_args(args) -> AnalysisConfig:
    """Create AnalysisConfig from command line arguments."""
    
    # Start with preset if specified
    if args.preset:
        if args.preset == 'basic':
            config = AnalysisPresets.basic()
        elif args.preset == 'comprehensive':
            config = AnalysisPresets.comprehensive()
        elif args.preset == 'quality':
            config = AnalysisPresets.quality_focused()
        elif args.preset == 'performance':
            config = AnalysisPresets.performance_focused()
        elif args.preset == 'ai':
            config = AnalysisPresets.ai_powered()
        else:
            config = AnalysisConfig()
    else:
        config = AnalysisConfig()
    
    # Override with specific arguments
    if args.comprehensive:
        config.enable_metrics = True
        config.enable_pattern_detection = True
        config.enable_visualization = True
        config.enable_graph_sitter = True
    
    if args.fast:
        config.enable_metrics = True
        config.enable_pattern_detection = False
        config.enable_visualization = False
        config.enable_ai_insights = False
    
    # Individual feature flags
    if args.metrics:
        config.enable_metrics = True
    
    if args.patterns or args.detect_patterns:
        config.enable_pattern_detection = True
    
    if args.tree_sitter or args.visualize:
        config.enable_visualization = True
        config.enable_graph_sitter = True
    
    if args.detect_import_loops:
        config.enable_pattern_detection = True
        config.detect_import_loops = True
    
    if args.detect_dead_code:
        config.enable_pattern_detection = True
        config.detect_dead_code = True
    
    if args.ai_insights or args.generate_training_data:
        config.enable_ai_insights = True
        if args.api_key:
            config.ai_api_key = args.api_key
    
    if args.generate_training_data:
        config.generate_training_data = True
    
    # Graph-sitter options
    if args.enable_graph_sitter:
        config.enable_graph_sitter = True
    
    if args.lazy_loading:
        config.lazy_loading = True
    
    # Advanced graph-sitter settings
    advanced_settings = {}
    if args.method_usages:
        advanced_settings['method_usages'] = True
    if args.generics:
        advanced_settings['generics'] = True
    if args.full_range_index:
        advanced_settings['full_range_index'] = True
    
    if advanced_settings:
        config.advanced_graph_sitter_settings = advanced_settings
    
    # Output options
    if args.export_html:
        config.export_html = True
        config.html_output_path = args.export_html
    
    if args.open_browser:
        config.open_browser = True
    
    # Debug and logging
    config.debug = args.debug
    config.verbose = args.verbose
    config.quiet = args.quiet
    
    # Legacy options
    if args.legacy_mode:
        config.legacy_mode = True
    
    config.include_tests = args.include_tests
    config.include_docs = args.include_docs
    
    return config

def print_summary(result, config: AnalysisConfig):
    """Print analysis summary to console."""
    if config.quiet:
        return
    
    print("\n" + "="*60)
    print("🚀 COMPREHENSIVE CODEBASE ANALYSIS RESULTS")
    print("="*60)
    
    print(f"📁 Path: {result.path}")
    print(f"⏱️  Duration: {result.analysis_duration:.2f} seconds")
    print(f"📅 Timestamp: {time.ctime(result.timestamp)}")
    
    # Quality metrics summary
    if hasattr(result, 'quality_metrics') and result.quality_metrics:
        print(f"\n📊 Quality Metrics:")
        for key, value in result.quality_metrics.items():
            print(f"   {key}: {value}")
    
    # Complexity metrics summary
    if hasattr(result, 'complexity_metrics') and result.complexity_metrics:
        print(f"\n🔧 Complexity Metrics:")
        for key, value in result.complexity_metrics.items():
            print(f"   {key}: {value}")
    
    # Pattern detection summary
    if hasattr(result, 'patterns') and result.patterns:
        print(f"\n🔍 Patterns Detected: {len(result.patterns)}")
    
    # Import loops summary
    if hasattr(result, 'import_loops') and result.import_loops:
        print(f"\n🔄 Import Loops: {len(result.import_loops)}")
    
    # Dead code summary
    if hasattr(result, 'dead_code') and result.dead_code:
        print(f"\n💀 Dead Code Items: {len(result.dead_code)}")
    
    # AI insights summary
    if hasattr(result, 'ai_insights') and result.ai_insights:
        print(f"\n🤖 AI Insights Generated")
    
    # Training data summary
    if hasattr(result, 'training_data') and result.training_data:
        print(f"\n📚 Training Data Items: {len(result.training_data)}")
    
    print("\n" + "="*60)

def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(args)
    
    # Validate arguments
    if args.ai_insights and not args.api_key:
        print("❌ Error: --ai-insights requires --api-key", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.path).exists():
        print(f"❌ Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create configuration
        config = create_config_from_args(args)
        
        # Initialize analysis engine
        engine = AnalysisEngine(config)
        
        # Run analysis
        print(f"🚀 Starting comprehensive analysis of: {args.path}")
        result = engine.analyze_codebase(args.path)
        
        # Print summary
        print_summary(result, config)
        
        # Export results
        if args.output:
            engine.export_results(args.output, args.format)
            print(f"📄 Results exported to: {args.output}")
        
        if args.export_html:
            engine.export_results(args.export_html, 'html')
            print(f"🌐 HTML report exported to: {args.export_html}")
        
        print("✅ Analysis completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# Convenience functions for programmatic access
def analyze_codebase(path: str, config: Optional[AnalysisConfig] = None):
    """Convenience function for programmatic codebase analysis."""
    if config is None:
        config = AnalysisPresets.comprehensive()
    
    engine = AnalysisEngine(config)
    return engine.analyze_codebase(path)

def quick_analysis(path: str):
    """Quick analysis with basic metrics."""
    return analyze_codebase(path, AnalysisPresets.basic())

def comprehensive_analysis(path: str):
    """Comprehensive analysis with all features."""
    return analyze_codebase(path, AnalysisPresets.comprehensive())

def quality_analysis(path: str):
    """Quality-focused analysis."""
    return analyze_codebase(path, AnalysisPresets.quality_focused())

if __name__ == '__main__':
    main()
