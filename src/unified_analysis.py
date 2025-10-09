#!/usr/bin/env python3
"""
Unified Comprehensive Analysis System - Graph-Sitter Self-Analysis

This tool combines ALL integrated adapters and tools to perform the most comprehensive
analysis possible on the graph-sitter codebase itself:

1. GraphSitter Adapter - All structural analysis tools
2. LSP Adapter - Real-time diagnostics from Pyright & mypy
3. AutoGenLib Adapter - AI-powered error context and fixing
4. Static Analysis Tools - Ruff, Radon, Bandit, Safety

Usage:
    python src/unified_analysis.py --repo /path/to/repo
    python src/unified_analysis.py --repo . --comprehensive
    python src/unified_analysis.py --repo . --output report.json
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

# Rich output for beautiful terminal display
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Setup logging first
def setup_logger(name: str, level=logging.INFO):
    """Simple logger setup."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Our integrated adapters
try:
    import sys
    from pathlib import Path
    
    # Add src to path for imports
    src_path = Path(__file__).parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from graph_sitter_adapter import GraphSitterAdapter
    from lsp_adapter import LSPAdapter
    from autogenlib_adapter import AutoGenLibAdapter
    ADAPTERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import adapters: {e}")
    ADAPTERS_AVAILABLE = False
    GraphSitterAdapter = None
    LSPAdapter = None
    AutoGenLibAdapter = None

# Graph-sitter core
try:
    from graph_sitter.core.codebase import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    try:
        from graph_sitter import Codebase
        GRAPH_SITTER_AVAILABLE = True
    except ImportError:
        GRAPH_SITTER_AVAILABLE = False
        Codebase = None


@dataclass
class AnalysisReport:
    """Comprehensive analysis report structure."""
    
    timestamp: str
    repository_path: str
    total_files: int
    total_lines: int
    
    # GraphSitter Analysis
    dead_code_count: int
    circular_dependencies: int
    complexity_issues: int
    
    # LSP Diagnostics
    type_errors: int
    type_warnings: int
    lsp_total_diagnostics: int
    
    # AutoGenLib
    cached_fixes: int
    
    # Static Analysis
    ruff_issues: int
    security_issues: int
    
    # Aggregated
    total_issues: int
    critical_issues: int
    high_priority_issues: int
    medium_priority_issues: int
    
    # Detailed results
    detailed_results: Dict[str, Any] = None


class UnifiedAnalyzer:
    """Orchestrates all analysis tools to provide comprehensive codebase insights."""
    
    def __init__(self, repo_path: str, verbose: bool = False):
        """Initialize the unified analyzer.
        
        Args:
            repo_path: Path to the repository to analyze
            verbose: Enable verbose logging
        """
        self.repo_path = Path(repo_path).resolve()
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = setup_logger(__name__, level=logging.DEBUG if verbose else logging.INFO)
        
        # Initialize adapters
        self.gs_adapter = None
        self.lsp_adapter = None
        self.autogenlib_adapter = None
        
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize all available adapters."""
        if not ADAPTERS_AVAILABLE:
            self.logger.warning("Adapters not available - limited functionality")
            return
        
        if not GRAPH_SITTER_AVAILABLE:
            self.logger.warning("Graph-sitter not available")
            return
        
        try:
            # Initialize codebase
            self.logger.info(f"Initializing codebase: {self.repo_path}")
            codebase = Codebase(str(self.repo_path))
            
            # Initialize adapters
            self.gs_adapter = GraphSitterAdapter(codebase)
            self.logger.info("✓ GraphSitter adapter initialized")
            
            self.lsp_adapter = LSPAdapter(str(self.repo_path))
            self.logger.info("✓ LSP adapter initialized")
            
            self.autogenlib_adapter = AutoGenLibAdapter(codebase)
            self.logger.info("✓ AutoGenLib adapter initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize adapters: {e}")
            if self.verbose:
                import traceback
                self.logger.error(traceback.format_exc())
    
    def run_comprehensive_analysis(self) -> AnalysisReport:
        """Run all analysis passes and aggregate results."""
        
        if self.console:
            self.console.print(Panel.fit(
                "[bold blue]🔍 Starting Comprehensive Analysis[/bold blue]\n"
                f"Repository: {self.repo_path}",
                border_style="blue"
            ))
        
        start_time = time.time()
        detailed_results = {}
        
        # 1. GraphSitter Analysis
        if self.console:
            self.console.print("\n[bold cyan]═══ Phase 1: GraphSitter Structural Analysis ═══[/bold cyan]")
        
        gs_results = self._run_graphsitter_analysis()
        detailed_results['graphsitter'] = gs_results
        
        # 2. LSP Diagnostics
        if self.console:
            self.console.print("\n[bold cyan]═══ Phase 2: LSP Diagnostics (Type Checking) ═══[/bold cyan]")
        
        lsp_results = self._run_lsp_analysis()
        detailed_results['lsp'] = lsp_results
        
        # 3. AutoGenLib Cache Analysis
        if self.console:
            self.console.print("\n[bold cyan]═══ Phase 3: AutoGenLib Cache Analysis ═══[/bold cyan]")
        
        autogenlib_results = self._run_autogenlib_analysis()
        detailed_results['autogenlib'] = autogenlib_results
        
        # 4. Static Analysis Tools
        if self.console:
            self.console.print("\n[bold cyan]═══ Phase 4: Static Analysis Tools ═══[/bold cyan]")
        
        static_results = self._run_static_analysis()
        detailed_results['static_analysis'] = static_results
        
        # Aggregate results
        elapsed = time.time() - start_time
        report = self._create_report(detailed_results, elapsed)
        
        return report
    
    def _run_graphsitter_analysis(self) -> Dict[str, Any]:
        """Run GraphSitter adapter analysis."""
        if not self.gs_adapter:
            return {"error": "GraphSitter adapter not available"}
        
        results = {}
        
        try:
            # Overview
            if self.console:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    task = progress.add_task("Getting codebase overview...", total=None)
                    overview = self.gs_adapter.get_codebase_overview()
                    progress.update(task, completed=True)
            else:
                overview = self.gs_adapter.get_codebase_overview()
            
            results['overview'] = overview
            self.logger.info(f"Files analyzed: {overview.get('total_files', 0)}")
            
            # Dead code detection
            if self.console:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    task = progress.add_task("Detecting dead code...", total=None)
                    dead_code = self.gs_adapter.find_dead_code()
                    progress.update(task, completed=True)
            else:
                dead_code = self.gs_adapter.find_dead_code()
            
            results['dead_code'] = dead_code
            unused_count = len(dead_code.get('unused_symbols', []))
            self.logger.info(f"Dead code items: {unused_count}")
            
            # Circular dependencies
            if self.console:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    task = progress.add_task("Analyzing dependencies...", total=None)
                    circular = self.gs_adapter.detect_circular_dependencies()
                    progress.update(task, completed=True)
            else:
                circular = self.gs_adapter.detect_circular_dependencies()
            
            results['circular_dependencies'] = circular
            cycles_count = len(circular.get('cycles', []))
            self.logger.info(f"Circular dependency cycles: {cycles_count}")
            
            # Import graph
            import_graph = self.gs_adapter.generate_import_graph()
            results['import_graph'] = import_graph
            
            # Directory structure
            dir_structure = self.gs_adapter.list_directory_structure(max_depth=2)
            results['directory_structure'] = dir_structure
            
            # Comprehensive statistics
            stats = self.gs_adapter.get_codebase_statistics()
            results['statistics'] = stats
            
        except Exception as e:
            self.logger.error(f"GraphSitter analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def _run_lsp_analysis(self) -> Dict[str, Any]:
        """Run LSP adapter diagnostics."""
        if not self.lsp_adapter:
            return {"error": "LSP adapter not available"}
        
        results = {}
        
        try:
            # Get all diagnostics from all servers
            if self.console:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    task = progress.add_task("Running Pyright...", total=None)
                    pyright_diags = self.lsp_adapter.get_pyright_diagnostics()
                    progress.update(task, completed=True)
                    
                    task = progress.add_task("Running mypy...", total=None)
                    mypy_diags = self.lsp_adapter.get_mypy_diagnostics()
                    progress.update(task, completed=True)
            else:
                pyright_diags = self.lsp_adapter.get_pyright_diagnostics()
                mypy_diags = self.lsp_adapter.get_mypy_diagnostics()
            
            results['pyright'] = {
                'count': len(pyright_diags),
                'diagnostics': [asdict(d) for d in pyright_diags[:100]]  # Limit to 100
            }
            
            results['mypy'] = {
                'count': len(mypy_diags),
                'diagnostics': [asdict(d) for d in mypy_diags[:100]]
            }
            
            # Get errors only
            errors = self.lsp_adapter.get_errors_only()
            results['errors_only'] = {
                'count': len(errors),
                'diagnostics': [asdict(d) for d in errors[:50]]
            }
            
            # Get summary
            summary = self.lsp_adapter.get_diagnostic_summary()
            results['summary'] = summary
            
            self.logger.info(f"Total LSP diagnostics: {summary.get('total', 0)}")
            self.logger.info(f"  Errors: {summary.get('by_severity', {}).get('error', 0)}")
            self.logger.info(f"  Warnings: {summary.get('by_severity', {}).get('warning', 0)}")
            
        except Exception as e:
            self.logger.error(f"LSP analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def _run_autogenlib_analysis(self) -> Dict[str, Any]:
        """Run AutoGenLib adapter analysis."""
        if not self.autogenlib_adapter:
            return {"error": "AutoGenLib adapter not available"}
        
        results = {}
        
        try:
            # Get cache statistics
            cache_stats = self.autogenlib_adapter.get_cache_stats()
            results['cache_stats'] = cache_stats
            
            self.logger.info(f"Cache hits: {cache_stats.get('hits', 0)}")
            self.logger.info(f"Cache misses: {cache_stats.get('misses', 0)}")
            self.logger.info(f"Cached fixes: {cache_stats.get('total_cached', 0)}")
            
        except Exception as e:
            self.logger.error(f"AutoGenLib analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def _run_static_analysis(self) -> Dict[str, Any]:
        """Run static analysis tools."""
        results = {}
        
        # Try running ruff
        try:
            if self.console:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    task = progress.add_task("Running ruff...", total=None)
                    ruff_result = self._run_ruff()
                    progress.update(task, completed=True)
            else:
                ruff_result = self._run_ruff()
            
            results['ruff'] = ruff_result
        except Exception as e:
            results['ruff'] = {"error": str(e)}
        
        # Try running bandit (security)
        try:
            bandit_result = self._run_bandit()
            results['bandit'] = bandit_result
        except Exception as e:
            results['bandit'] = {"error": str(e)}
        
        return results
    
    def _run_ruff(self) -> Dict[str, Any]:
        """Run ruff linter."""
        import subprocess
        
        try:
            result = subprocess.run(
                ['ruff', 'check', str(self.repo_path), '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                issues = json.loads(result.stdout)
                return {
                    'count': len(issues),
                    'issues': issues[:100]  # Limit
                }
            else:
                return {'count': 0, 'issues': []}
                
        except FileNotFoundError:
            return {'error': 'ruff not installed'}
        except subprocess.TimeoutExpired:
            return {'error': 'ruff timed out'}
        except Exception as e:
            return {'error': str(e)}
    
    def _run_bandit(self) -> Dict[str, Any]:
        """Run bandit security scanner."""
        import subprocess
        
        try:
            result = subprocess.run(
                ['bandit', '-r', str(self.repo_path), '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                return {
                    'count': len(data.get('results', [])),
                    'high_severity': len([r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']),
                    'medium_severity': len([r for r in data.get('results', []) if r.get('issue_severity') == 'MEDIUM']),
                    'issues': data.get('results', [])[:50]
                }
            else:
                return {'count': 0}
                
        except FileNotFoundError:
            return {'error': 'bandit not installed'}
        except subprocess.TimeoutExpired:
            return {'error': 'bandit timed out'}
        except Exception as e:
            return {'error': str(e)}
    
    def _create_report(self, detailed_results: Dict[str, Any], elapsed: float) -> AnalysisReport:
        """Create final analysis report from all results."""
        
        # Extract metrics
        gs = detailed_results.get('graphsitter', {})
        lsp = detailed_results.get('lsp', {})
        autogenlib = detailed_results.get('autogenlib', {})
        static = detailed_results.get('static_analysis', {})
        
        # Aggregate counts - handle potential errors in data structure
        overview = gs.get('overview', {}) if isinstance(gs, dict) else {}
        total_files = overview.get('total_files', 0) if isinstance(overview, dict) else 0
        total_lines = overview.get('lines_of_code', 0) if isinstance(overview, dict) else 0
        
        # Handle dead_code which might be an error or list
        dead_code = gs.get('dead_code', {}) if isinstance(gs, dict) else {}
        if isinstance(dead_code, dict):
            dead_code_count = len(dead_code.get('unused_symbols', []))
        elif isinstance(dead_code, list):
            dead_code_count = len(dead_code)
        else:
            dead_code_count = 0
        
        # Handle circular_dependencies
        circular = gs.get('circular_dependencies', {}) if isinstance(gs, dict) else {}
        circular_dependencies = len(circular.get('cycles', [])) if isinstance(circular, dict) else 0
        
        lsp_summary = lsp.get('summary', {})
        type_errors = lsp_summary.get('by_severity', {}).get('error', 0)
        type_warnings = lsp_summary.get('by_severity', {}).get('warning', 0)
        lsp_total = lsp_summary.get('total', 0)
        
        cached_fixes = autogenlib.get('cache_stats', {}).get('total_cached', 0)
        
        ruff_count = static.get('ruff', {}).get('count', 0)
        security_count = static.get('bandit', {}).get('count', 0)
        
        # Aggregate priorities
        total_issues = dead_code_count + lsp_total + ruff_count + security_count
        critical = type_errors + security_count
        high_priority = circular_dependencies + dead_code_count
        medium_priority = type_warnings + ruff_count
        
        report = AnalysisReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            repository_path=str(self.repo_path),
            total_files=total_files,
            total_lines=total_lines,
            dead_code_count=dead_code_count,
            circular_dependencies=circular_dependencies,
            complexity_issues=0,  # TODO
            type_errors=type_errors,
            type_warnings=type_warnings,
            lsp_total_diagnostics=lsp_total,
            cached_fixes=cached_fixes,
            ruff_issues=ruff_count,
            security_issues=security_count,
            total_issues=total_issues,
            critical_issues=critical,
            high_priority_issues=high_priority,
            medium_priority_issues=medium_priority,
            detailed_results=detailed_results
        )
        
        # Display summary
        self._display_report(report, elapsed)
        
        return report
    
    def _display_report(self, report: AnalysisReport, elapsed: float):
        """Display analysis report in terminal."""
        
        if not self.console:
            # Fallback to simple print
            print("\n" + "=" * 70)
            print("ANALYSIS REPORT")
            print("=" * 70)
            print(f"Repository: {report.repository_path}")
            print(f"Total Files: {report.total_files}")
            print(f"Total Lines: {report.total_lines}")
            print(f"Total Issues: {report.total_issues}")
            print(f"  Critical: {report.critical_issues}")
            print(f"  High: {report.high_priority_issues}")
            print(f"  Medium: {report.medium_priority_issues}")
            print(f"Elapsed Time: {elapsed:.2f}s")
            print("=" * 70)
            return
        
        # Rich output
        self.console.print("\n")
        self.console.print(Panel.fit(
            f"[bold green]✓ Analysis Complete[/bold green]\n"
            f"Elapsed Time: {elapsed:.2f}s",
            border_style="green"
        ))
        
        # Summary table
        table = Table(title="Analysis Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Count", justify="right", style="yellow")
        
        table.add_row("Total Files", str(report.total_files))
        table.add_row("Total Lines of Code", f"{report.total_lines:,}")
        table.add_row("", "")
        table.add_row("[bold]Dead Code Items[/bold]", str(report.dead_code_count))
        table.add_row("[bold]Circular Dependencies[/bold]", str(report.circular_dependencies))
        table.add_row("", "")
        table.add_row("[bold red]Type Errors[/bold red]", str(report.type_errors))
        table.add_row("[bold yellow]Type Warnings[/bold yellow]", str(report.type_warnings))
        table.add_row("LSP Total Diagnostics", str(report.lsp_total_diagnostics))
        table.add_row("", "")
        table.add_row("Ruff Issues", str(report.ruff_issues))
        table.add_row("Security Issues", str(report.security_issues))
        table.add_row("", "")
        table.add_row("[bold]TOTAL ISSUES[/bold]", f"[bold]{report.total_issues}[/bold]")
        table.add_row("  └─ Critical", f"[red]{report.critical_issues}[/red]")
        table.add_row("  └─ High Priority", f"[yellow]{report.high_priority_issues}[/yellow]")
        table.add_row("  └─ Medium Priority", str(report.medium_priority_issues))
        
        self.console.print(table)
        self.console.print()


def main():
    """Main entry point for unified analysis."""
    parser = argparse.ArgumentParser(
        description="Unified Comprehensive Analysis - Analyze graph-sitter with ALL integrated tools"
    )
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='Path to repository to analyze'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (optional)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run most comprehensive analysis (may take longer)'
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = UnifiedAnalyzer(args.repo, verbose=args.verbose)
    
    # Run analysis
    report = analyzer.run_comprehensive_analysis()
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            # Convert report to dict
            report_dict = asdict(report)
            json.dump(report_dict, f, indent=2, default=str)
        
        print(f"\n✓ Report saved to: {output_path}")
    
    # Exit with code based on critical issues
    if report.critical_issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
