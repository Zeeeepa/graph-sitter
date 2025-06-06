#!/usr/bin/env python3
"""
Unified Analysis CLI

Command-line interface for the comprehensive codebase analysis system.
Provides access to all analysis features through a single, powerful tool.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .core.engine import AnalysisEngine, analyze_codebase
from .core.config import AnalysisConfig, AnalysisPresets, AnalysisResult
from .ai.training_data import TrainingDataGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('analysis.log')
    ]
)
logger = logging.getLogger(__name__)


class AnalysisCLI:
    """Command-line interface for codebase analysis."""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.training_data_generator = TrainingDataGenerator()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='🚀 Comprehensive Codebase Analysis Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s /path/to/code                           # Basic analysis
  %(prog)s . --comprehensive                       # Full analysis with all features
  %(prog)s . --preset quality                      # Quality-focused analysis
  %(prog)s . --export-html report.html             # Generate HTML report
  %(prog)s . --generate-training-data              # Generate ML training data
  %(prog)s . --ai-insights --api-key YOUR_KEY     # AI-powered analysis
  %(prog)s . --visualize --open-browser           # Interactive visualization
  %(prog)s . --config analysis.json               # Use custom configuration
  %(prog)s . --output results.json --format json  # Export to JSON

Presets:
  basic         - Basic analysis (fast)
  comprehensive - Full analysis with all features
  quality       - Quality and maintainability focused
  performance   - Performance optimized for large codebases
  ai            - AI-enhanced analysis (requires API key)

For more information, visit: https://github.com/Zeeeepa/graph-sitter
            """
        )
        
        # Positional arguments
        parser.add_argument(
            'path',
            help='Path to the codebase to analyze'
        )
        
        # Analysis options
        analysis_group = parser.add_argument_group('Analysis Options')
        analysis_group.add_argument(
            '--preset',
            choices=['basic', 'comprehensive', 'quality', 'performance', 'ai'],
            help='Use a predefined analysis configuration'
        )
        analysis_group.add_argument(
            '--config',
            help='Path to custom configuration file (JSON)'
        )
        analysis_group.add_argument(
            '--comprehensive',
            action='store_true',
            help='Enable comprehensive analysis with all features'
        )
        analysis_group.add_argument(
            '--extensions',
            nargs='+',
            default=['.py'],
            help='File extensions to analyze (default: .py)'
        )
        analysis_group.add_argument(
            '--exclude',
            nargs='+',
            help='Patterns to exclude from analysis'
        )
        
        # Feature toggles
        features_group = parser.add_argument_group('Feature Toggles')
        features_group.add_argument(
            '--no-graph-sitter',
            action='store_true',
            help='Disable graph-sitter analysis (use AST only)'
        )
        features_group.add_argument(
            '--quality-metrics',
            action='store_true',
            help='Enable quality metrics analysis'
        )
        features_group.add_argument(
            '--complexity-analysis',
            action='store_true',
            help='Enable complexity analysis'
        )
        features_group.add_argument(
            '--pattern-detection',
            action='store_true',
            help='Enable pattern and anti-pattern detection'
        )
        features_group.add_argument(
            '--dead-code-detection',
            action='store_true',
            help='Enable dead code detection'
        )
        features_group.add_argument(
            '--import-loop-detection',
            action='store_true',
            help='Enable circular import detection'
        )
        features_group.add_argument(
            '--ai-insights',
            action='store_true',
            help='Enable AI-powered insights (requires API key)'
        )
        
        # AI options
        ai_group = parser.add_argument_group('AI Options')
        ai_group.add_argument(
            '--api-key',
            help='API key for AI analysis'
        )
        ai_group.add_argument(
            '--ai-model',
            default='gpt-3.5-turbo',
            help='AI model to use (default: gpt-3.5-turbo)'
        )
        ai_group.add_argument(
            '--max-ai-requests',
            type=int,
            default=100,
            help='Maximum AI requests (default: 100)'
        )
        
        # Visualization options
        viz_group = parser.add_argument_group('Visualization Options')
        viz_group.add_argument(
            '--visualize',
            action='store_true',
            help='Generate interactive visualizations'
        )
        viz_group.add_argument(
            '--export-html',
            help='Export HTML visualization to file'
        )
        viz_group.add_argument(
            '--open-browser',
            action='store_true',
            help='Open visualization in browser'
        )
        
        # Output options
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument(
            '--output', '-o',
            help='Output file path'
        )
        output_group.add_argument(
            '--format',
            choices=['json', 'text', 'html'],
            default='text',
            help='Output format (default: text)'
        )
        output_group.add_argument(
            '--output-dir',
            help='Output directory for generated files'
        )
        output_group.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress progress output'
        )
        output_group.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        # Training data options
        training_group = parser.add_argument_group('Training Data Options')
        training_group.add_argument(
            '--generate-training-data',
            action='store_true',
            help='Generate machine learning training data'
        )
        training_group.add_argument(
            '--training-data-types',
            nargs='+',
            choices=['function_analysis', 'complexity_prediction', 'quality_assessment', 'refactoring_suggestions'],
            help='Types of training data to generate'
        )
        training_group.add_argument(
            '--training-output',
            help='Output file for training data (JSON)'
        )
        
        # Performance options
        perf_group = parser.add_argument_group('Performance Options')
        perf_group.add_argument(
            '--parallel',
            action='store_true',
            help='Enable parallel processing'
        )
        perf_group.add_argument(
            '--max-workers',
            type=int,
            default=4,
            help='Maximum worker processes (default: 4)'
        )
        perf_group.add_argument(
            '--max-file-size',
            type=int,
            default=1024*1024,
            help='Maximum file size to analyze in bytes (default: 1MB)'
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with the given arguments."""
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Configure logging
            if parsed_args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
            elif parsed_args.quiet:
                logging.getLogger().setLevel(logging.WARNING)
            
            # Validate arguments
            self._validate_args(parsed_args)
            
            # Create configuration
            config = self._create_config(parsed_args)
            
            # Print banner
            if not parsed_args.quiet:
                self._print_banner()
            
            # Run analysis
            result = self._run_analysis(parsed_args, config)
            
            # Handle training data generation
            if parsed_args.generate_training_data:
                self._generate_training_data(parsed_args, result)
            
            # Generate output
            self._generate_output(parsed_args, result)
            
            # Print summary
            if not parsed_args.quiet:
                result.print_summary()
            
            return 0
        
        except KeyboardInterrupt:
            logger.info("Analysis interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            if parsed_args.verbose if 'parsed_args' in locals() else False:
                import traceback
                traceback.print_exc()
            return 1
    
    def _validate_args(self, args) -> None:
        """Validate command-line arguments."""
        # Check if path exists
        if not os.path.exists(args.path):
            raise ValueError(f"Path does not exist: {args.path}")
        
        # Check AI requirements
        if args.ai_insights and not args.api_key:
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("AI insights require --api-key or OPENAI_API_KEY environment variable")
        
        # Check output directory
        if args.output_dir and not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir, exist_ok=True)
    
    def _create_config(self, args) -> AnalysisConfig:
        """Create analysis configuration from arguments."""
        # Start with preset if specified
        if args.preset:
            config = getattr(AnalysisPresets, args.preset)()
        elif args.config:
            config = AnalysisConfig.from_file(args.config)
        else:
            config = AnalysisConfig()
        
        # Override with command-line arguments
        if args.comprehensive:
            config = AnalysisPresets.comprehensive()
        
        # Feature toggles
        if args.no_graph_sitter:
            config.use_graph_sitter = False
        if args.quality_metrics:
            config.enable_quality_metrics = True
        if args.complexity_analysis:
            config.enable_complexity_analysis = True
        if args.pattern_detection:
            config.enable_pattern_detection = True
        if args.dead_code_detection:
            config.enable_dead_code_detection = True
        if args.import_loop_detection:
            config.enable_import_loop_detection = True
        if args.ai_insights:
            config.enable_ai_analysis = True
        
        # AI configuration
        if args.api_key:
            config.ai_api_key = args.api_key
        elif os.getenv('OPENAI_API_KEY'):
            config.ai_api_key = os.getenv('OPENAI_API_KEY')
        
        if args.ai_model:
            config.ai_model = args.ai_model
        if args.max_ai_requests:
            config.max_ai_requests = args.max_ai_requests
        
        # Visualization
        if args.visualize or args.export_html:
            config.generate_visualizations = True
        if args.export_html:
            config.export_html = True
        
        # File options
        if args.extensions:
            config.extensions = args.extensions
        if args.exclude:
            config.exclude_patterns.extend(args.exclude)
        
        # Performance options
        if args.parallel:
            config.parallel_processing = True
        if args.max_workers:
            config.max_workers = args.max_workers
        if args.max_file_size:
            config.max_file_size = args.max_file_size
        
        # Output options
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.verbose:
            config.verbose = True
        
        return config
    
    def _run_analysis(self, args, config: AnalysisConfig) -> AnalysisResult:
        """Run the codebase analysis."""
        if not args.quiet:
            print(f"🔍 Analyzing codebase: {args.path}")
            print(f"📊 Configuration: {config.to_dict()}")
        
        start_time = time.time()
        
        # Run analysis
        result = analyze_codebase(args.path, config)
        
        analysis_time = time.time() - start_time
        
        if not args.quiet:
            print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
        
        return result
    
    def _generate_training_data(self, args, result: AnalysisResult) -> None:
        """Generate training data if requested."""
        if not args.quiet:
            print("🤖 Generating training data...")
        
        try:
            # Determine data types
            data_types = args.training_data_types or ['function_analysis', 'complexity_prediction']
            
            # Generate training data
            # Note: This would need access to the original codebase object
            # For now, we'll create a placeholder
            training_data = {
                'metadata': {
                    'source': 'analysis_result',
                    'timestamp': time.time(),
                    'data_types': data_types
                },
                'note': 'Training data generation requires direct codebase access'
            }
            
            # Save training data
            output_path = args.training_output or 'training_data.json'
            with open(output_path, 'w') as f:
                json.dump(training_data, f, indent=2, default=str)
            
            if not args.quiet:
                print(f"💾 Training data saved to: {output_path}")
        
        except Exception as e:
            logger.error(f"Training data generation failed: {e}")
    
    def _generate_output(self, args, result: AnalysisResult) -> None:
        """Generate output files."""
        # JSON output
        if args.format == 'json' or args.output:
            output_path = args.output or 'analysis_results.json'
            result.save_to_file(output_path)
            if not args.quiet:
                print(f"💾 Results saved to: {output_path}")
        
        # HTML visualization
        if args.export_html:
            try:
                from .visualization.tree_sitter import TreeSitterVisualizer
                visualizer = TreeSitterVisualizer()
                
                if result.visualization_data:
                    visualizer.export_html(result.visualization_data, args.export_html)
                    if not args.quiet:
                        print(f"🎨 Visualization exported to: {args.export_html}")
                    
                    if args.open_browser:
                        visualizer.open_in_browser(args.export_html)
                else:
                    logger.warning("No visualization data available")
            
            except Exception as e:
                logger.error(f"Visualization export failed: {e}")
        
        # Text report
        if args.format == 'text' and not args.quiet:
            self._print_text_report(result)
    
    def _print_banner(self) -> None:
        """Print the application banner."""
        banner = """
🚀 COMPREHENSIVE CODEBASE ANALYSIS TOOL 🚀
==========================================
        
Powered by Graph-sitter Analysis Framework
        """
        print(banner)
    
    def _print_text_report(self, result: AnalysisResult) -> None:
        """Print a detailed text report."""
        print("\n" + "="*60)
        print("📊 DETAILED ANALYSIS REPORT")
        print("="*60)
        
        # Summary stats
        stats = result.get_summary_stats()
        print(f"\n📈 SUMMARY STATISTICS")
        print("-" * 30)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Quality metrics
        if result.quality_metrics:
            quality = result.get_quality_summary()
            print(f"\n🎯 QUALITY METRICS")
            print("-" * 30)
            for key, value in quality.items():
                if value > 0:
                    print(f"{key.replace('_', ' ').title()}: {value:.1f}%")
        
        # Complexity analysis
        if result.complexity_metrics:
            complexity = result.get_complexity_summary()
            print(f"\n🔢 COMPLEXITY ANALYSIS")
            print("-" * 30)
            for key, value in complexity.items():
                if isinstance(value, (int, float)):
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Issues summary
        issues = result.get_issues_summary()
        if issues['total_issues'] > 0:
            print(f"\n⚠️  ISSUES DETECTED")
            print("-" * 30)
            for key, value in issues.items():
                if isinstance(value, int) and value > 0:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        # AI insights
        if result.ai_insights and result.ai_insights.get('recommendations'):
            print(f"\n🤖 AI RECOMMENDATIONS")
            print("-" * 30)
            for rec in result.ai_insights['recommendations'][:5]:  # Top 5
                print(f"• {rec.get('title', 'Unknown')}")
                print(f"  {rec.get('description', '')}")
                print()


def main():
    """Main entry point for the CLI."""
    cli = AnalysisCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())

