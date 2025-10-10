#!/usr/bin/env python3
"""Main Analysis CLI - Orchestrates all analysis layers

This is the main entry point for comprehensive code analysis combining:
- Graph-sitter: Structural codebase analysis
- LSP (Language Server Protocol): Real-time diagnostics
- AutoGenLib: AI-powered error fixing
- External libs: Ruff, MyPy, Pylint integration

Usage:
    python main_analysis.py --repo /path/to/codebase
    python main_analysis.py --repo /path/to/codebase --comprehensive
    python main_analysis.py --repo /path/to/codebase --fix-errors
    python main_analysis.py --repo /path/to/codebase --interactive
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import time

# Rich for beautiful terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Import our analysis modules
try:
    from graph_sitter import Codebase
    from graph_sitter_analysis import GraphSitterAnalyzer
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    GRAPH_SITTER_AVAILABLE = False
    logging.warning(f"Graph-sitter not available: {e}")

try:
    from lsp_diagnostics import LSPDiagnosticsManager
    from solidlsp.ls_config import Language
    LSP_AVAILABLE = True
except ImportError as e:
    LSP_AVAILABLE = False
    logging.warning(f"LSP not available: {e}")

try:
    from autogenlib_adapter import (
        get_ai_fix_context,
        resolve_diagnostic_with_ai
    )
    AUTOGENLIB_AVAILABLE = True
except ImportError as e:
    AUTOGENLIB_AVAILABLE = False
    logging.warning(f"AutoGenLib not available: {e}")

try:
    from libs_analysis import ExternalToolsAnalyzer, LibAnalysisResult
    LIBS_AVAILABLE = True
except ImportError as e:
    LIBS_AVAILABLE = False
    logging.warning(f"External libs analysis not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """Comprehensive analysis report combining all layers."""
    repo_path: str
    timestamp: float
    graph_sitter_results: Optional[Dict[str, Any]] = None
    lsp_results: Optional[Dict[str, Any]] = None
    libs_results: Optional[Dict[str, List[Dict]]] = None
    autogenlib_fixes: Optional[List[Dict]] = None
    summary: Optional[Dict[str, int]] = None


class ComprehensiveAnalyzer:
    """Main orchestrator for multi-layer code analysis."""
    
    def __init__(self, repo_path: str, console: Optional[Console] = None):
        self.repo_path = Path(repo_path).resolve()
        self.console = console or (Console() if RICH_AVAILABLE else None)
        
        # Initialize components
        self.codebase = None
        self.gs_analyzer = None
        self.lsp_manager = None
        self.libs_analyzer = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all analysis components."""
        if self.console:
            self.console.print(f"[bold blue]🔧 Initializing analysis for:[/] {self.repo_path}")
        
        # Graph-sitter
        if GRAPH_SITTER_AVAILABLE:
            try:
                self.codebase = Codebase(str(self.repo_path))
                self.gs_analyzer = GraphSitterAnalyzer(self.codebase)
                if self.console:
                    self.console.print("[green]✓[/] Graph-sitter initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Graph-sitter: {e}")
        
        # LSP
        if LSP_AVAILABLE:
            try:
                self.lsp_manager = LSPDiagnosticsManager(
                    str(self.repo_path),
                    Language.PYTHON
                )
                if self.console:
                    self.console.print("[green]✓[/] LSP initialized")
            except Exception as e:
                logger.error(f"Failed to initialize LSP: {e}")
        
        # External libs
        if LIBS_AVAILABLE:
            try:
                self.libs_analyzer = ExternalToolsAnalyzer(str(self.repo_path))
                if self.console:
                    self.console.print("[green]✓[/] External tools initialized")
            except Exception as e:
                logger.error(f"Failed to initialize external tools: {e}")
    
    def analyze(self, comprehensive: bool = True, fix_errors: bool = False) -> AnalysisReport:
        """Run comprehensive analysis."""
        report = AnalysisReport(
            repo_path=str(self.repo_path),
            timestamp=time.time()
        )
        
        # Graph-sitter analysis
        if self.gs_analyzer and comprehensive:
            if self.console:
                self.console.print("\n[bold cyan]📊 Running Graph-sitter analysis...[/]")
            try:
                report.graph_sitter_results = self.gs_analyzer.get_codebase_overview()
            except Exception as e:
                logger.error(f"Graph-sitter analysis failed: {e}")
        
        # LSP diagnostics
        if self.lsp_manager:
            if self.console:
                self.console.print("\n[bold cyan]🔍 Running LSP diagnostics...[/]")
            try:
                diagnostics = self.lsp_manager.collect_diagnostics()
                report.lsp_results = {
                    'diagnostics_count': len(diagnostics),
                    'diagnostics': diagnostics[:50]  # Limit for report
                }
            except Exception as e:
                logger.error(f"LSP analysis failed: {e}")
        
        # External tools
        if self.libs_analyzer:
            if self.console:
                self.console.print("\n[bold cyan]🛠️  Running external tools (Ruff, MyPy)...[/]")
            try:
                all_results = self.libs_analyzer.run_all_tools()
                report.libs_results = {
                    tool: [asdict(r) for r in results]
                    for tool, results in all_results.items()
                }
            except Exception as e:
                logger.error(f"External tools analysis failed: {e}")
        
        # AutoGenLib fixes (if requested)
        if fix_errors and AUTOGENLIB_AVAILABLE and self.lsp_manager and self.codebase:
            if self.console:
                self.console.print("\n[bold cyan]🤖 Generating AI fixes...[/]")
            try:
                report.autogenlib_fixes = self._generate_fixes()
            except Exception as e:
                logger.error(f"AutoGenLib fixes failed: {e}")
        
        # Generate summary
        report.summary = self._generate_summary(report)
        
        return report
    
    def _generate_fixes(self) -> List[Dict]:
        """Generate AI-powered fixes for detected issues."""
        fixes = []
        # Implementation would use autogenlib_adapter
        return fixes
    
    def _generate_summary(self, report: AnalysisReport) -> Dict[str, int]:
        """Generate summary statistics."""
        summary = {
            'total_files': 0,
            'total_errors': 0,
            'total_warnings': 0
        }
        
        if report.graph_sitter_results:
            summary['total_files'] = report.graph_sitter_results.get('file_count', 0)
        
        if report.lsp_results:
            summary['total_errors'] += report.lsp_results.get('diagnostics_count', 0)
        
        if report.libs_results:
            for tool_results in report.libs_results.values():
                summary['total_warnings'] += len(tool_results)
        
        return summary
    
    def display_report(self, report: AnalysisReport):
        """Display analysis report in terminal."""
        if not self.console:
            # Fallback to JSON if Rich not available
            print(json.dumps(asdict(report), indent=2, default=str))
            return
        
        # Display with Rich
        self.console.print("\n" + "="*80)
        self.console.print(Panel.fit(
            f"[bold]Analysis Complete[/]\n"
            f"Repo: {report.repo_path}\n"
            f"Files: {report.summary.get('total_files', 0)}\n"
            f"Errors: {report.summary.get('total_errors', 0)}\n"
            f"Warnings: {report.summary.get('total_warnings', 0)}",
            title="📊 Analysis Report",
            border_style="green"
        ))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Python Code Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --repo /path/to/project
  %(prog)s --repo /path/to/project --comprehensive
  %(prog)s --repo /path/to/project --fix-errors
  %(prog)s --repo /path/to/project --output report.json
        """
    )
    
    parser.add_argument(
        '--repo',
        required=True,
        help='Path to the codebase to analyze'
    )
    
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run comprehensive analysis (all layers)'
    )
    
    parser.add_argument(
        '--fix-errors',
        action='store_true',
        help='Generate AI-powered fixes for detected errors'
    )
    
    parser.add_argument(
        '--output',
        help='Save report to JSON file'
    )
    
    parser.add_argument(
        '--no-rich',
        action='store_true',
        help='Disable Rich terminal output'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize console
    console = None if args.no_rich else (Console() if RICH_AVAILABLE else None)
    
    # Check repo exists
    if not Path(args.repo).exists():
        print(f"Error: Repository path does not exist: {args.repo}")
        sys.exit(1)
    
    # Run analysis
    try:
        analyzer = ComprehensiveAnalyzer(args.repo, console)
        report = analyzer.analyze(
            comprehensive=args.comprehensive,
            fix_errors=args.fix_errors
        )
        
        # Display results
        analyzer.display_report(report)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            print(f"\n✅ Report saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
