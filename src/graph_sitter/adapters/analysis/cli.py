"""
🖥️ Unified Analysis CLI and API

Comprehensive command-line interface and API for all analysis features:
- Unified CLI replacing scattered analysis scripts
- Rich argument parsing with subcommands
- Integration with all analysis modules
- Progress reporting and interactive features
- Batch processing capabilities
- Configuration management
- Export and visualization options

Provides a single entry point for all codebase analysis functionality.
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict

try:
    from graph_sitter.core.codebase import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    print("Warning: Graph-sitter not available. Some functionality will be limited.")
    GRAPH_SITTER_AVAILABLE = False
    Codebase = object

from .core import AnalysisEngine, CodebaseAnalyzer
from .metrics import MetricsCalculator, ComplexityAnalyzer
from .tree_sitter_enhancements import TreeSitterAnalyzer, QueryPatternEngine
from .visualization import VisualizationEngine, HTMLReportGenerator
from .ai_integration import AIAnalyzer, AutomatedIssueDetector, CodeImprovementSuggester
from .config import (
    ComprehensiveAnalysisConfig, ConfigurationManager, ConfigurationPresets,
    AnalysisLevel, ExportFormat, VisualizationTheme
)


class ProgressReporter:
    """Progress reporting for long-running operations"""
    
    def __init__(self, total_steps: int = 100, show_progress: bool = True):
        self.total_steps = total_steps
        self.current_step = 0
        self.show_progress = show_progress
        self.start_time = time.time()
    
    def update(self, step: int, message: str = ""):
        """Update progress"""
        self.current_step = step
        if self.show_progress:
            percentage = (step / self.total_steps) * 100
            elapsed = time.time() - self.start_time
            
            # Simple progress bar
            bar_length = 40
            filled_length = int(bar_length * step // self.total_steps)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            print(f'\r[{bar}] {percentage:.1f}% - {message} ({elapsed:.1f}s)', end='', flush=True)
    
    def finish(self, message: str = "Complete"):
        """Finish progress reporting"""
        if self.show_progress:
            elapsed = time.time() - self.start_time
            print(f'\n✅ {message} (Total time: {elapsed:.1f}s)')


class AnalysisCLI:
    """
    Main CLI class for analysis operations
    """
    
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.config = None
        self.progress_reporter = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser"""
        parser = argparse.ArgumentParser(
            description="🔍 Graph-sitter Comprehensive Codebase Analysis Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze ./src --output report.html
  %(prog)s metrics ./src --format json
  %(prog)s visualize ./src --theme dark --interactive
  %(prog)s ai-analyze ./src --types quality security
  %(prog)s config create --preset development
  %(prog)s batch-process ./projects --workers 4
            """
        )
        
        # Global options
        parser.add_argument('--config', '-c', type=str, help='Configuration file path')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
        parser.add_argument('--no-progress', action='store_true', help='Disable progress reporting')
        
        # Create subparsers
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Analyze command
        self._add_analyze_parser(subparsers)
        
        # Metrics command
        self._add_metrics_parser(subparsers)
        
        # Visualize command
        self._add_visualize_parser(subparsers)
        
        # AI analysis command
        self._add_ai_analyze_parser(subparsers)
        
        # Tree-sitter command
        self._add_tree_sitter_parser(subparsers)
        
        # Configuration command
        self._add_config_parser(subparsers)
        
        # Batch processing command
        self._add_batch_parser(subparsers)
        
        # Export command
        self._add_export_parser(subparsers)
        
        return parser
    
    def _add_analyze_parser(self, subparsers):
        """Add analyze subcommand"""
        parser = subparsers.add_parser('analyze', help='Comprehensive codebase analysis')
        parser.add_argument('path', help='Path to analyze (file or directory)')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--format', choices=['json', 'html', 'text'], default='html',
                          help='Output format')
        parser.add_argument('--level', choices=['basic', 'standard', 'comprehensive', 'deep'],
                          default='standard', help='Analysis depth level')
        parser.add_argument('--include-tests', action='store_true', help='Include test files')
        parser.add_argument('--include-docs', action='store_true', help='Include documentation')
        parser.add_argument('--exclude-patterns', nargs='*', help='Patterns to exclude')
    
    def _add_metrics_parser(self, subparsers):
        """Add metrics subcommand"""
        parser = subparsers.add_parser('metrics', help='Calculate code quality metrics')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--format', choices=['json', 'csv', 'text'], default='text',
                          help='Output format')
        parser.add_argument('--metrics', nargs='*', 
                          choices=['complexity', 'halstead', 'maintainability', 'quality'],
                          help='Specific metrics to calculate')
        parser.add_argument('--threshold', type=float, help='Quality threshold for warnings')
    
    def _add_visualize_parser(self, subparsers):
        """Add visualize subcommand"""
        parser = subparsers.add_parser('visualize', help='Generate visualizations')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--theme', choices=['light', 'dark', 'high_contrast'], 
                          default='light', help='Visualization theme')
        parser.add_argument('--interactive', action='store_true', help='Generate interactive charts')
        parser.add_argument('--charts', nargs='*',
                          choices=['complexity', 'dependencies', 'hierarchy', 'metrics'],
                          help='Specific charts to generate')
        parser.add_argument('--auto-open', action='store_true', help='Auto-open generated report')
    
    def _add_ai_analyze_parser(self, subparsers):
        """Add AI analysis subcommand"""
        parser = subparsers.add_parser('ai-analyze', help='AI-powered code analysis')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--types', nargs='*',
                          choices=['quality', 'security', 'performance', 'maintainability'],
                          default=['quality'], help='Analysis types')
        parser.add_argument('--provider', choices=['openai', 'claude', 'local'],
                          default='openai', help='AI provider')
        parser.add_argument('--model', help='AI model to use')
        parser.add_argument('--max-requests', type=int, default=150, help='Max AI requests')
        parser.add_argument('--auto-fix', action='store_true', help='Apply automatic fixes')
    
    def _add_tree_sitter_parser(self, subparsers):
        """Add tree-sitter subcommand"""
        parser = subparsers.add_parser('tree-sitter', help='Tree-sitter analysis')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--language', default='python', help='Programming language')
        parser.add_argument('--patterns', nargs='*', help='Query patterns to execute')
        parser.add_argument('--visualize-tree', action='store_true', help='Visualize syntax tree')
        parser.add_argument('--export-format', choices=['text', 'json', 'dot'],
                          default='text', help='Export format')
    
    def _add_config_parser(self, subparsers):
        """Add configuration subcommand"""
        parser = subparsers.add_parser('config', help='Configuration management')
        config_subparsers = parser.add_subparsers(dest='config_action')
        
        # Create config
        create_parser = config_subparsers.add_parser('create', help='Create configuration')
        create_parser.add_argument('--preset', choices=['development', 'production', 'research', 'lightweight'],
                                 help='Use predefined preset')
        create_parser.add_argument('--output', '-o', default='analysis_config.json',
                                 help='Output configuration file')
        
        # Validate config
        validate_parser = config_subparsers.add_parser('validate', help='Validate configuration')
        validate_parser.add_argument('config_file', help='Configuration file to validate')
        
        # Show config
        show_parser = config_subparsers.add_parser('show', help='Show current configuration')
        show_parser.add_argument('--format', choices=['json', 'yaml', 'text'], default='text')
    
    def _add_batch_parser(self, subparsers):
        """Add batch processing subcommand"""
        parser = subparsers.add_parser('batch', help='Batch process multiple projects')
        parser.add_argument('paths', nargs='+', help='Paths to process')
        parser.add_argument('--output-dir', '-o', default='./batch_results',
                          help='Output directory')
        parser.add_argument('--workers', type=int, default=4, help='Number of worker processes')
        parser.add_argument('--analysis-types', nargs='*',
                          choices=['analyze', 'metrics', 'visualize', 'ai-analyze'],
                          default=['analyze'], help='Analysis types to run')
        parser.add_argument('--continue-on-error', action='store_true',
                          help='Continue processing on errors')
    
    def _add_export_parser(self, subparsers):
        """Add export subcommand"""
        parser = subparsers.add_parser('export', help='Export analysis results')
        parser.add_argument('input_file', help='Input analysis file')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--format', choices=['json', 'html', 'csv', 'pdf'],
                          required=True, help='Export format')
        parser.add_argument('--template', help='Custom template file')
        parser.add_argument('--include-source', action='store_true',
                          help='Include source code in export')
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Load configuration
            self.config = self._load_configuration(parsed_args)
            
            # Set up progress reporting
            if not parsed_args.quiet and not parsed_args.no_progress:
                self.progress_reporter = ProgressReporter(show_progress=True)
            
            # Execute command
            if parsed_args.command == 'analyze':
                return self._execute_analyze(parsed_args)
            elif parsed_args.command == 'metrics':
                return self._execute_metrics(parsed_args)
            elif parsed_args.command == 'visualize':
                return self._execute_visualize(parsed_args)
            elif parsed_args.command == 'ai-analyze':
                return self._execute_ai_analyze(parsed_args)
            elif parsed_args.command == 'tree-sitter':
                return self._execute_tree_sitter(parsed_args)
            elif parsed_args.command == 'config':
                return self._execute_config(parsed_args)
            elif parsed_args.command == 'batch':
                return self._execute_batch(parsed_args)
            elif parsed_args.command == 'export':
                return self._execute_export(parsed_args)
            else:
                parser.print_help()
                return 1
                
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 130
        except Exception as e:
            if parsed_args.verbose:
                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")
            return 1
    
    def _load_configuration(self, args) -> ComprehensiveAnalysisConfig:
        """Load configuration from file or create default"""
        if hasattr(args, 'config') and args.config:
            return self.config_manager.load_config(args.config)
        else:
            return self.config_manager.load_config()
    
    def _execute_analyze(self, args) -> int:
        """Execute comprehensive analysis"""
        print(f"🔍 Analyzing: {args.path}")
        
        if self.progress_reporter:
            self.progress_reporter.update(10, "Initializing analysis")
        
        try:
            # Create analyzer
            analyzer = CodebaseAnalyzer(asdict(self.config))
            
            if self.progress_reporter:
                self.progress_reporter.update(20, "Loading codebase")
            
            # Load codebase
            if GRAPH_SITTER_AVAILABLE:
                if Path(args.path).is_file():
                    # Single file analysis
                    results = self._analyze_single_file(args.path, analyzer)
                else:
                    # Directory analysis
                    codebase = Codebase.from_repo(args.path)
                    results = analyzer.analyze_codebase(codebase)
            else:
                results = self._fallback_analysis(args.path)
            
            if self.progress_reporter:
                self.progress_reporter.update(80, "Generating output")
            
            # Generate output
            output_path = self._generate_output(results, args.output, args.format)
            
            if self.progress_reporter:
                self.progress_reporter.finish("Analysis complete")
            
            print(f"✅ Analysis complete: {output_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return 1
    
    def _execute_metrics(self, args) -> int:
        """Execute metrics calculation"""
        print(f"📊 Calculating metrics: {args.path}")
        
        try:
            calculator = MetricsCalculator()
            
            if Path(args.path).is_file():
                # Single file metrics
                with open(args.path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                metrics = calculator.calculate_quality_metrics(source_code, args.path)
                results = {"file_metrics": {args.path: asdict(metrics)}}
            else:
                # Directory metrics
                analyzer = ComplexityAnalyzer()
                results = analyzer.analyze_directory(args.path)
            
            # Generate output
            output_path = self._generate_output(results, args.output, args.format)
            
            print(f"✅ Metrics calculated: {output_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Metrics calculation failed: {e}")
            return 1
    
    def _execute_visualize(self, args) -> int:
        """Execute visualization generation"""
        print(f"📈 Generating visualizations: {args.path}")
        
        try:
            # First analyze the codebase
            analyzer = CodebaseAnalyzer()
            if GRAPH_SITTER_AVAILABLE and Path(args.path).is_dir():
                codebase = Codebase.from_repo(args.path)
                analysis_results = analyzer.analyze_codebase(codebase)
            else:
                analysis_results = self._fallback_analysis(args.path)
            
            # Generate visualizations
            viz_engine = VisualizationEngine()
            output_path = args.output or f"visualization_report_{int(time.time())}.html"
            
            report_path = viz_engine.generate_comprehensive_report(
                asdict(analysis_results), output_path
            )
            
            if args.auto_open:
                import webbrowser
                webbrowser.open(f"file://{Path(report_path).absolute()}")
            
            print(f"✅ Visualizations generated: {report_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Visualization generation failed: {e}")
            return 1
    
    def _execute_ai_analyze(self, args) -> int:
        """Execute AI-powered analysis"""
        print(f"🤖 AI Analysis: {args.path}")
        
        if not self.config.analysis.enable_ai_analysis:
            print("❌ AI analysis is disabled in configuration")
            return 1
        
        try:
            ai_analyzer = AIAnalyzer()
            
            if GRAPH_SITTER_AVAILABLE and Path(args.path).is_dir():
                codebase = Codebase.from_repo(args.path)
                results = ai_analyzer.batch_analyze_codebase(codebase, args.types)
            else:
                print("⚠️ AI analysis requires graph-sitter and directory input")
                return 1
            
            # Generate output
            output_path = self._generate_output(results, args.output, 'json')
            
            print(f"✅ AI analysis complete: {output_path}")
            return 0
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return 1
    
    def _execute_tree_sitter(self, args) -> int:
        """Execute tree-sitter analysis"""
        print(f"🌳 Tree-sitter analysis: {args.path}")
        
        try:
            analyzer = TreeSitterAnalyzer(args.language)
            
            if Path(args.path).is_file():
                with open(args.path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                results = analyzer.analyze_structure(source_code, args.path)
            else:
                print("⚠️ Tree-sitter analysis currently supports single files only")
                return 1
            
            # Generate output
            output_path = self._generate_output(results, args.output, args.export_format)
            
            print(f"✅ Tree-sitter analysis complete: {output_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Tree-sitter analysis failed: {e}")
            return 1
    
    def _execute_config(self, args) -> int:
        """Execute configuration management"""
        if args.config_action == 'create':
            return self._create_config(args)
        elif args.config_action == 'validate':
            return self._validate_config(args)
        elif args.config_action == 'show':
            return self._show_config(args)
        else:
            print("❌ Unknown config action")
            return 1
    
    def _create_config(self, args) -> int:
        """Create configuration file"""
        try:
            if args.preset:
                config = getattr(ConfigurationPresets, f'get_{args.preset}_preset')()
            else:
                config = self.config_manager.create_default_config()
            
            success = self.config_manager.save_config(config, args.output)
            
            if success:
                print(f"✅ Configuration created: {args.output}")
                return 0
            else:
                print(f"❌ Failed to create configuration")
                return 1
                
        except Exception as e:
            print(f"❌ Configuration creation failed: {e}")
            return 1
    
    def _validate_config(self, args) -> int:
        """Validate configuration file"""
        try:
            config = self.config_manager.load_config(args.config_file)
            is_valid, issues = self.config_manager.validate_config(config)
            
            if is_valid:
                print("✅ Configuration is valid")
                return 0
            else:
                print("❌ Configuration validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
                
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return 1
    
    def _show_config(self, args) -> int:
        """Show current configuration"""
        try:
            if args.format == 'json':
                print(json.dumps(asdict(self.config), indent=2, default=str))
            else:
                print("Current Configuration:")
                print(f"  Analysis Level: {self.config.analysis.analysis_level.value}")
                print(f"  AI Analysis: {self.config.analysis.enable_ai_analysis}")
                print(f"  Tree-sitter: {self.config.analysis.enable_tree_sitter}")
                print(f"  Output Format: {self.config.export.default_export_format.value}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to show configuration: {e}")
            return 1
    
    def _execute_batch(self, args) -> int:
        """Execute batch processing"""
        print(f"🔄 Batch processing {len(args.paths)} paths")
        
        # Implementation would handle parallel processing
        print("⚠️ Batch processing not yet implemented")
        return 1
    
    def _execute_export(self, args) -> int:
        """Execute export operation"""
        print(f"📤 Exporting: {args.input_file}")
        
        # Implementation would handle format conversion
        print("⚠️ Export functionality not yet implemented")
        return 1
    
    def _analyze_single_file(self, file_path: str, analyzer) -> Dict[str, Any]:
        """Analyze a single file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Basic file analysis
        calculator = MetricsCalculator()
        metrics = calculator.calculate_quality_metrics(source_code, file_path)
        
        return {
            "file_path": file_path,
            "metrics": asdict(metrics),
            "analysis_type": "single_file"
        }
    
    def _fallback_analysis(self, path: str) -> Dict[str, Any]:
        """Fallback analysis when graph-sitter is not available"""
        return {
            "path": path,
            "analysis_type": "fallback",
            "message": "Limited analysis - graph-sitter not available",
            "timestamp": time.time()
        }
    
    def _generate_output(self, results: Any, output_path: Optional[str], 
                        format_type: str) -> str:
        """Generate output in specified format"""
        if not output_path:
            timestamp = int(time.time())
            output_path = f"analysis_results_{timestamp}.{format_type}"
        
        if format_type == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
        elif format_type == 'html':
            # Generate HTML report
            viz_engine = VisualizationEngine()
            output_path = viz_engine.generate_comprehensive_report(results, output_path)
        else:
            # Text format
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(results))
        
        return output_path


# Convenience functions for direct use

def run_analysis_cli(args: Optional[List[str]] = None) -> int:
    """Run the analysis CLI"""
    cli = AnalysisCLI()
    return cli.run(args)


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments"""
    cli = AnalysisCLI()
    parser = cli.create_parser()
    return parser.parse_args(args)


def execute_analysis_command(command: str, path: str, **kwargs) -> Dict[str, Any]:
    """Execute analysis command programmatically"""
    cli = AnalysisCLI()
    
    # Convert command to args
    args = [command, path]
    for key, value in kwargs.items():
        if isinstance(value, bool) and value:
            args.append(f'--{key.replace("_", "-")}')
        elif value is not None:
            args.extend([f'--{key.replace("_", "-")}', str(value)])
    
    return cli.run(args)


# Main entry point
def main():
    """Main entry point for the CLI"""
    cli = AnalysisCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

