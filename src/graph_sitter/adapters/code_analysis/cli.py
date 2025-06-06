"""
🖥️ Unified Analysis CLI

Consolidated command-line interface combining features from all tools:
- analyze_codebase.py CLI
- analyze_codebase_enhanced.py CLI  
- enhanced_analyzer.py CLI
- All PR CLI features

Provides a single, comprehensive command-line interface for all analysis functionality.
"""

import argparse
import json
import sys
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional

from .core.engine import CodebaseAnalyzer
from .core.config import AnalysisConfig, AnalysisPresets, create_custom_config
from .legacy.compatibility import migrate_to_new_system


class AnalysisCLI:
    """
    Comprehensive CLI for codebase analysis.
    
    Consolidates all command-line functionality from existing tools.
    """
    
    def __init__(self):
        self.start_time = time.time()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser"""
        parser = argparse.ArgumentParser(
            description="🔍 Comprehensive Codebase Analysis Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze ./src
  %(prog)s analyze ./src --preset comprehensive --output report.html
  %(prog)s analyze ./src --ai-analysis --api-key YOUR_KEY
  %(prog)s analyze ./src --format json --output results.json
  %(prog)s quick ./src
  %(prog)s quality ./src --threshold 8.0
  %(prog)s legacy-migrate  # Show migration guide

Presets:
  quick          - Fast analysis with basic metrics
  standard       - Standard analysis with core features  
  comprehensive  - Full analysis with all features
  quality        - Quality-focused analysis
  security       - Security-focused analysis
  ai-powered     - AI-powered analysis (requires API key)
  enhanced       - Enhanced with graph-sitter features
  performance    - Optimized for large codebases

Legacy Compatibility:
  This tool replaces analyze_codebase.py, analyze_codebase_enhanced.py,
  and enhanced_analyzer.py with a unified interface.
            """
        )
        
        # Global options
        parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
        parser.add_argument('--config-file', type=str, help='Configuration file path')
        
        # Create subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Main analyze command
        self._add_analyze_parser(subparsers)
        
        # Quick analysis command
        self._add_quick_parser(subparsers)
        
        # Quality analysis command
        self._add_quality_parser(subparsers)
        
        # Security analysis command
        self._add_security_parser(subparsers)
        
        # AI analysis command
        self._add_ai_parser(subparsers)
        
        # Legacy commands for compatibility
        self._add_legacy_parsers(subparsers)
        
        # Utility commands
        self._add_utility_parsers(subparsers)
        
        return parser
    
    def _add_analyze_parser(self, subparsers):
        """Add main analyze command"""
        parser = subparsers.add_parser('analyze', help='Comprehensive codebase analysis')
        parser.add_argument('path', help='Path to analyze (file or directory)')
        parser.add_argument('--preset', choices=[
            'quick', 'standard', 'comprehensive', 'quality', 'security', 
            'ai-powered', 'enhanced', 'performance'
        ], default='standard', help='Analysis preset')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--format', choices=['json', 'html', 'text'], 
                          default='text', help='Output format')
        
        # Feature toggles
        parser.add_argument('--no-metrics', action='store_true', 
                          help='Disable metrics calculation')
        parser.add_argument('--no-patterns', action='store_true',
                          help='Disable pattern detection')
        parser.add_argument('--no-visualization', action='store_true',
                          help='Disable visualization generation')
        parser.add_argument('--no-graph-sitter', action='store_true',
                          help='Disable graph-sitter integration')
        
        # AI options
        parser.add_argument('--ai-analysis', action='store_true',
                          help='Enable AI-powered analysis')
        parser.add_argument('--api-key', help='AI API key')
        parser.add_argument('--ai-provider', choices=['openai', 'claude', 'local'],
                          default='openai', help='AI provider')
        parser.add_argument('--ai-model', help='AI model to use')
        
        # Advanced options
        parser.add_argument('--training-data', action='store_true',
                          help='Generate training data for ML')
        parser.add_argument('--dead-code', action='store_true',
                          help='Focus on dead code detection')
        parser.add_argument('--import-loops', action='store_true',
                          help='Focus on import loop detection')
        parser.add_argument('--advanced-config', action='store_true',
                          help='Use advanced graph-sitter configuration')
        
        # Output options
        parser.add_argument('--open-browser', action='store_true',
                          help='Auto-open HTML report in browser')
        parser.add_argument('--save-config', help='Save used configuration to file')
        
        # Legacy compatibility options
        parser.add_argument('--comprehensive', action='store_true',
                          help='Legacy: comprehensive analysis')
        parser.add_argument('--visualize', action='store_true',
                          help='Legacy: enable visualization')
        parser.add_argument('--tree-sitter', action='store_true',
                          help='Legacy: enable tree-sitter features')
        parser.add_argument('--export-html', help='Legacy: export HTML report')
    
    def _add_quick_parser(self, subparsers):
        """Add quick analysis command"""
        parser = subparsers.add_parser('quick', help='Quick analysis with basic metrics')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--format', choices=['json', 'text'], default='text')
    
    def _add_quality_parser(self, subparsers):
        """Add quality analysis command"""
        parser = subparsers.add_parser('quality', help='Quality-focused analysis')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--threshold', type=float, default=7.0,
                          help='Quality threshold (0-10)')
        parser.add_argument('--fail-on-threshold', action='store_true',
                          help='Exit with error if quality below threshold')
    
    def _add_security_parser(self, subparsers):
        """Add security analysis command"""
        parser = subparsers.add_parser('security', help='Security-focused analysis')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--output', '-o', help='Output file path')
        parser.add_argument('--ai-security', action='store_true',
                          help='Enable AI-powered security analysis')
        parser.add_argument('--api-key', help='AI API key for security analysis')
    
    def _add_ai_parser(self, subparsers):
        """Add AI analysis command"""
        parser = subparsers.add_parser('ai', help='AI-powered analysis')
        parser.add_argument('path', help='Path to analyze')
        parser.add_argument('--api-key', required=True, help='AI API key')
        parser.add_argument('--provider', choices=['openai', 'claude', 'local'],
                          default='openai', help='AI provider')
        parser.add_argument('--model', help='AI model to use')
        parser.add_argument('--analysis-types', nargs='+',
                          choices=['quality', 'security', 'performance', 'maintainability'],
                          default=['quality'], help='Types of AI analysis')
        parser.add_argument('--output', '-o', help='Output file path')
    
    def _add_legacy_parsers(self, subparsers):
        """Add legacy compatibility commands"""
        # Legacy analyze_codebase command
        legacy_parser = subparsers.add_parser('legacy-analyze', 
                                            help='Legacy analyze_codebase compatibility')
        legacy_parser.add_argument('path', help='Path to analyze')
        legacy_parser.add_argument('--use-graph-sitter', action='store_true', default=True)
        legacy_parser.add_argument('--comprehensive', action='store_true')
        legacy_parser.add_argument('--visualize', action='store_true')
        legacy_parser.add_argument('--export-html', help='Export HTML file')
        legacy_parser.add_argument('--format', choices=['json', 'text'], default='text')
        legacy_parser.add_argument('--output', help='Output file')
        
        # Legacy enhanced analyzer command
        enhanced_parser = subparsers.add_parser('legacy-enhanced',
                                              help='Legacy enhanced_analyzer compatibility')
        enhanced_parser.add_argument('path', help='Path to analyze')
        enhanced_parser.add_argument('--training-data', action='store_true')
        enhanced_parser.add_argument('--import-loops', action='store_true')
        enhanced_parser.add_argument('--dead-code', action='store_true')
        enhanced_parser.add_argument('--graph-analysis', action='store_true')
        enhanced_parser.add_argument('--output', help='Output file')
    
    def _add_utility_parsers(self, subparsers):
        """Add utility commands"""
        # Migration guide
        subparsers.add_parser('legacy-migrate', help='Show migration guide')
        
        # Configuration commands
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_sub = config_parser.add_subparsers(dest='config_action')
        
        # Create config
        create_config = config_sub.add_parser('create', help='Create configuration file')
        create_config.add_argument('--preset', choices=[
            'quick', 'standard', 'comprehensive', 'quality', 'security',
            'ai-powered', 'enhanced', 'performance'
        ], default='standard')
        create_config.add_argument('--output', '-o', default='analysis_config.json')
        
        # Validate config
        validate_config = config_sub.add_parser('validate', help='Validate configuration')
        validate_config.add_argument('config_file', help='Configuration file to validate')
        
        # Show presets
        subparsers.add_parser('presets', help='Show available presets')
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Handle no command
            if not parsed_args.command:
                parser.print_help()
                return 1
            
            # Set up logging
            self._setup_logging(parsed_args)
            
            # Execute command
            if parsed_args.command == 'analyze':
                return self._execute_analyze(parsed_args)
            elif parsed_args.command == 'quick':
                return self._execute_quick(parsed_args)
            elif parsed_args.command == 'quality':
                return self._execute_quality(parsed_args)
            elif parsed_args.command == 'security':
                return self._execute_security(parsed_args)
            elif parsed_args.command == 'ai':
                return self._execute_ai(parsed_args)
            elif parsed_args.command == 'legacy-analyze':
                return self._execute_legacy_analyze(parsed_args)
            elif parsed_args.command == 'legacy-enhanced':
                return self._execute_legacy_enhanced(parsed_args)
            elif parsed_args.command == 'legacy-migrate':
                return self._execute_migrate(parsed_args)
            elif parsed_args.command == 'config':
                return self._execute_config(parsed_args)
            elif parsed_args.command == 'presets':
                return self._execute_presets(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                return 1
                
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 130
        except Exception as e:
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")
            return 1
    
    def _setup_logging(self, args):
        """Setup logging based on arguments"""
        import logging
        
        if args.quiet:
            level = logging.WARNING
        elif args.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _execute_analyze(self, args) -> int:
        """Execute main analyze command"""
        print(f"🔍 Analyzing: {args.path}")
        
        try:
            # Create configuration
            config = self._create_config_from_args(args)
            
            # Create analyzer
            analyzer = CodebaseAnalyzer(config)
            
            # Run analysis
            result = analyzer.analyze(args.path)
            
            if not result.success:
                print(f"❌ Analysis failed: {result.error}")
                return 1
            
            # Generate output
            self._generate_output(result, args)
            
            # Print summary
            if not args.quiet:
                result.print_summary()
            
            print(f"✅ Analysis completed in {result.analysis_duration:.2f}s")
            return 0
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return 1
    
    def _execute_quick(self, args) -> int:
        """Execute quick analysis"""
        print(f"⚡ Quick analysis: {args.path}")
        
        config = AnalysisPresets.quick()
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(args.path)
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error}")
            return 1
        
        self._generate_output(result, args)
        
        if not args.quiet:
            result.print_summary()
        
        return 0
    
    def _execute_quality(self, args) -> int:
        """Execute quality analysis"""
        print(f"📊 Quality analysis: {args.path}")
        
        config = AnalysisPresets.quality_focused()
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(args.path)
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error}")
            return 1
        
        # Check quality threshold
        if result.quality_metrics:
            avg_quality = sum(m.quality_score for m in result.quality_metrics.values()) / len(result.quality_metrics)
            
            if avg_quality < args.threshold:
                print(f"⚠️ Quality score {avg_quality:.1f} below threshold {args.threshold}")
                if args.fail_on_threshold:
                    return 1
        
        self._generate_output(result, args)
        result.print_summary()
        
        return 0
    
    def _execute_security(self, args) -> int:
        """Execute security analysis"""
        print(f"🔒 Security analysis: {args.path}")
        
        config = AnalysisPresets.security_focused()
        
        if args.ai_security and args.api_key:
            config.enable_ai_analysis = True
            config.ai_config.enabled = True
            config.ai_config.api_key = args.api_key
            config.ai_config.analysis_types = ['security']
        
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(args.path)
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error}")
            return 1
        
        self._generate_output(result, args)
        result.print_summary()
        
        return 0
    
    def _execute_ai(self, args) -> int:
        """Execute AI analysis"""
        print(f"🤖 AI analysis: {args.path}")
        
        config = AnalysisPresets.ai_powered()
        config.ai_config.api_key = args.api_key
        config.ai_config.provider = args.provider
        config.ai_config.analysis_types = args.analysis_types
        
        if args.model:
            config.ai_config.model = args.model
        
        analyzer = CodebaseAnalyzer(config)
        result = analyzer.analyze(args.path)
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error}")
            return 1
        
        self._generate_output(result, args)
        result.print_summary()
        
        return 0
    
    def _execute_legacy_analyze(self, args) -> int:
        """Execute legacy analyze_codebase compatibility"""
        print("⚠️ Using legacy compatibility mode. Consider migrating to 'analyze' command.")
        
        from .legacy.compatibility import LegacyAnalyzerWrapper
        
        wrapper = LegacyAnalyzerWrapper(args.use_graph_sitter)
        result = wrapper.analyze_codebase(
            args.path,
            comprehensive=args.comprehensive,
            visualize=args.visualize,
            export_html=args.export_html,
            format=args.format
        )
        
        self._output_legacy_result(result, args)
        return 0
    
    def _execute_legacy_enhanced(self, args) -> int:
        """Execute legacy enhanced analyzer compatibility"""
        print("⚠️ Using legacy enhanced compatibility mode. Consider migrating to 'analyze --preset enhanced'.")
        
        from .legacy.compatibility import EnhancedCodebaseAnalyzer
        
        analyzer = EnhancedCodebaseAnalyzer(True)
        
        if args.training_data:
            result = analyzer.analyze_training_data(args.path)
        elif args.import_loops:
            result = analyzer.analyze_import_loops(args.path)
        elif args.dead_code:
            result = analyzer.analyze_dead_code(args.path)
        else:
            result = analyzer.analyze_codebase_enhanced(args.path)
        
        self._output_legacy_result(result, args)
        return 0
    
    def _execute_migrate(self, args) -> int:
        """Execute migration guide"""
        migrate_to_new_system()
        return 0
    
    def _execute_config(self, args) -> int:
        """Execute configuration commands"""
        if args.config_action == 'create':
            return self._create_config_file(args)
        elif args.config_action == 'validate':
            return self._validate_config_file(args)
        else:
            print("Unknown config action")
            return 1
    
    def _execute_presets(self, args) -> int:
        """Show available presets"""
        print("📋 Available Analysis Presets:")
        print("=" * 40)
        
        presets = {
            'quick': 'Fast analysis with basic metrics',
            'standard': 'Standard analysis with core features',
            'comprehensive': 'Full analysis with all features',
            'quality': 'Quality-focused analysis',
            'security': 'Security-focused analysis',
            'ai-powered': 'AI-powered analysis (requires API key)',
            'enhanced': 'Enhanced with graph-sitter features',
            'performance': 'Optimized for large codebases'
        }
        
        for preset, description in presets.items():
            print(f"  {preset:<15} - {description}")
        
        return 0
    
    def _create_config_from_args(self, args) -> AnalysisConfig:
        """Create configuration from command line arguments"""
        # Start with preset
        if hasattr(args, 'preset'):
            preset_map = {
                'quick': AnalysisPresets.quick,
                'standard': AnalysisPresets.standard,
                'comprehensive': AnalysisPresets.comprehensive,
                'quality': AnalysisPresets.quality_focused,
                'security': AnalysisPresets.security_focused,
                'ai-powered': AnalysisPresets.ai_powered,
                'enhanced': AnalysisPresets.enhanced,
                'performance': AnalysisPresets.performance_optimized
            }
            config = preset_map.get(args.preset, AnalysisPresets.standard)()
        else:
            config = AnalysisPresets.standard()
        
        # Apply feature toggles
        if hasattr(args, 'no_metrics') and args.no_metrics:
            config.enable_metrics = False
        if hasattr(args, 'no_patterns') and args.no_patterns:
            config.enable_pattern_detection = False
        if hasattr(args, 'no_visualization') and args.no_visualization:
            config.enable_visualization = False
        if hasattr(args, 'no_graph_sitter') and args.no_graph_sitter:
            config.enable_graph_sitter = False
        
        # Apply AI options
        if hasattr(args, 'ai_analysis') and args.ai_analysis:
            config.enable_ai_analysis = True
            config.ai_config.enabled = True
            
            if hasattr(args, 'api_key') and args.api_key:
                config.ai_config.api_key = args.api_key
            if hasattr(args, 'ai_provider') and args.ai_provider:
                config.ai_config.provider = args.ai_provider
            if hasattr(args, 'ai_model') and args.ai_model:
                config.ai_config.model = args.ai_model
        
        # Apply advanced options
        if hasattr(args, 'training_data') and args.training_data:
            config.generate_training_data = True
        if hasattr(args, 'advanced_config') and args.advanced_config:
            config.use_advanced_graph_sitter_config = True
        
        # Apply legacy compatibility options
        if hasattr(args, 'comprehensive') and args.comprehensive:
            config.analysis_level = 'comprehensive'
        if hasattr(args, 'visualize') and args.visualize:
            config.enable_visualization = True
        if hasattr(args, 'tree_sitter') and args.tree_sitter:
            config.enable_graph_sitter = True
        
        # Apply output options
        if hasattr(args, 'open_browser') and args.open_browser:
            config.visualization_config.auto_open_browser = True
        
        return config
    
    def _generate_output(self, result, args):
        """Generate output based on arguments"""
        if hasattr(args, 'output') and args.output:
            output_path = args.output
        else:
            # Generate default output path
            timestamp = int(time.time())
            if hasattr(args, 'format'):
                ext = args.format
            else:
                ext = 'json'
            output_path = f"analysis_result_{timestamp}.{ext}"
        
        # Handle different output formats
        if hasattr(args, 'format'):
            if args.format == 'json':
                result.save_to_file(output_path)
                print(f"📄 Results saved to: {output_path}")
            elif args.format == 'html':
                if result.report_path:
                    print(f"📋 HTML report: {result.report_path}")
                    if hasattr(args, 'open_browser') and args.open_browser:
                        webbrowser.open(f"file://{Path(result.report_path).absolute()}")
                else:
                    print("⚠️ HTML report not generated")
            elif args.format == 'text':
                # Print text summary
                result.print_summary()
        
        # Handle legacy export options
        if hasattr(args, 'export_html') and args.export_html:
            if result.report_path:
                # Copy report to specified location
                import shutil
                shutil.copy2(result.report_path, args.export_html)
                print(f"📋 HTML exported to: {args.export_html}")
        
        # Save configuration if requested
        if hasattr(args, 'save_config') and args.save_config:
            from .core.config import save_config_to_file
            save_config_to_file(result.analysis_config, args.save_config)
            print(f"⚙️ Configuration saved to: {args.save_config}")
    
    def _output_legacy_result(self, result, args):
        """Output legacy format result"""
        if hasattr(args, 'output') and args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"📄 Results saved to: {args.output}")
        else:
            # Print summary
            print("\n📊 Analysis Summary:")
            print(f"Files: {result.get('file_count', 0)}")
            print(f"Functions: {result.get('function_count', 0)}")
            print(f"Classes: {result.get('class_count', 0)}")
            
            if 'quality_metrics' in result:
                print(f"Quality metrics calculated for {len(result['quality_metrics'])} files")
            
            if 'dead_code' in result:
                print(f"Dead code items: {len(result['dead_code'])}")
            
            if 'import_loops' in result:
                print(f"Import loops: {len(result['import_loops'])}")
    
    def _create_config_file(self, args) -> int:
        """Create configuration file"""
        try:
            preset_map = {
                'quick': AnalysisPresets.quick,
                'standard': AnalysisPresets.standard,
                'comprehensive': AnalysisPresets.comprehensive,
                'quality': AnalysisPresets.quality_focused,
                'security': AnalysisPresets.security_focused,
                'ai-powered': AnalysisPresets.ai_powered,
                'enhanced': AnalysisPresets.enhanced,
                'performance': AnalysisPresets.performance_optimized
            }
            
            config = preset_map[args.preset]()
            
            from .core.config import save_config_to_file
            save_config_to_file(config, args.output)
            
            print(f"✅ Configuration created: {args.output}")
            return 0
            
        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return 1
    
    def _validate_config_file(self, args) -> int:
        """Validate configuration file"""
        try:
            from .core.config import load_config_from_file
            config = load_config_from_file(args.config_file)
            
            print(f"✅ Configuration is valid: {args.config_file}")
            print(f"Analysis level: {config.analysis_level}")
            print(f"Features enabled: {sum([
                config.enable_metrics,
                config.enable_pattern_detection,
                config.enable_ai_analysis,
                config.enable_visualization,
                config.enable_graph_sitter
            ])}/5")
            
            return 0
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return 1


def main():
    """Main entry point for the CLI"""
    cli = AnalysisCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

