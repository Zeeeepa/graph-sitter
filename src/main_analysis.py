#!/usr/bin/env python3
"""Main CLI entry point for graph-sitter analysis."""

import click
import sys
from pathlib import Path
from typing import Optional

from graph_sitter import Codebase
from graph_sitter_adapter import GraphSitterAdapter
from autogenlib_adapter import AutoGenLibAdapter  
from lib_analysis import AnalysisOrchestrator
from lsp_diagnostics import LSPDiagnosticsManager
from analysis_utils import setup_logger

logger = setup_logger(__name__)

# Try importing rich for better terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


@click.group()
@click.version_option(version="2.0.0-alpha")
def cli():
    """Graph-Sitter Analysis CLI - Advanced codebase analysis tool."""
    pass


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--tools', default='all', help='Tools to run (comma-separated: ruff,mypy,pyright)')
@click.option('--format', type=click.Choice(['text', 'json', 'html']), default='text')
@click.option('--output', '-o', help='Output file path')
def repo(repo_path: str, tools: str, format: str, output: Optional[str]):
    """Analyze an entire repository."""
    try:
        if HAS_RICH:
            console.print(f"[bold blue]Analyzing repository:[/bold blue] {repo_path}")
        else:
            print(f"Analyzing repository: {repo_path}")
        
        # Initialize codebase
        codebase = Codebase(repo_path)
        
        # Run analysis
        orchestrator = AnalysisOrchestrator()
        
        if tools != 'all':
            tool_list = [t.strip() for t in tools.split(',')]
        else:
            tool_list = None
        
        result = orchestrator.run_analysis(repo_path, tools=tool_list)
        
        # Display results
        if format == 'text':
            _display_text_results(result)
        elif format == 'json':
            import json
            output_str = json.dumps(result, indent=2, default=str)
            if output:
                Path(output).write_text(output_str)
            else:
                print(output_str)
        elif format == 'html':
            html_output = _generate_html_report(result)
            if output:
                Path(output).write_text(html_output)
            else:
                print(html_output)
        
        # Exit code based on errors
        error_count = result['statistics'].get('by_severity', {}).get('error', 0)
        sys.exit(1 if error_count > 0 else 0)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if HAS_RICH:
            console.print(f"[bold red]Error:[/bold red] {e}")
        else:
            print(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--tools', default='all', help='Tools to run')
@click.option('--resolve', is_flag=True, help='Enable AI resolution')
def code(file_path: str, tools: str, resolve: bool):
    """Analyze a single code file."""
    try:
        if HAS_RICH:
            console.print(f"[bold blue]Analyzing file:[/bold blue] {file_path}")
        else:
            print(f"Analyzing file: {file_path}")
        
        # Get repo root
        repo_path = _find_repo_root(Path(file_path))
        if not repo_path:
            repo_path = Path(file_path).parent
        
        # Initialize
        codebase = Codebase(str(repo_path))
        orchestrator = AnalysisOrchestrator()
        
        if tools != 'all':
            tool_list = [t.strip() for t in tools.split(',')]
        else:
            tool_list = None
        
        # Run analysis
        result = orchestrator.run_analysis(file_path, tools=tool_list)
        
        # Display results
        _display_text_results(result)
        
        # AI resolution if requested
        if resolve and result['errors']:
            _run_resolution_interactive(codebase, result['errors'])
        
        error_count = result['statistics'].get('by_severity', {}).get('error', 0)
        sys.exit(1 if error_count > 0 else 0)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if HAS_RICH:
            console.print(f"[bold red]Error:[/bold red] {e}")
        else:
            print(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--repo', type=click.Path(exists=True), help='Repository path')
@click.option('--auto', is_flag=True, help='Non-interactive mode')
def resolve(repo: Optional[str], auto: bool):
    """AI-powered error resolution mode."""
    try:
        if not repo:
            repo = '.'
        
        if HAS_RICH:
            console.print("[bold blue]AI Resolution Mode[/bold blue]")
        else:
            print("AI Resolution Mode")
        
        # Initialize
        codebase = Codebase(repo)
        gs_adapter = GraphSitterAdapter(codebase)
        ai_adapter = AutoGenLibAdapter(codebase, gs_adapter)
        
        # Run analysis first
        orchestrator = AnalysisOrchestrator()
        result = orchestrator.run_analysis(repo)
        
        if not result['errors']:
            if HAS_RICH:
                console.print("[green]No errors found![/green]")
            else:
                print("No errors found!")
            return
        
        # Show errors
        if HAS_RICH:
            console.print(f"\n[yellow]Found {len(result['errors'])} errors[/yellow]")
        else:
            print(f"\nFound {len(result['errors'])} errors")
        
        # Resolve errors
        if auto:
            # Auto mode: resolve all
            fixes = ai_adapter.resolve_multiple_errors(result['errors'][:10])
            _display_fixes(fixes)
        else:
            # Interactive mode
            _run_resolution_interactive(codebase, result['errors'])
        
    except Exception as e:
        logger.error(f"Resolution failed: {e}")
        if HAS_RICH:
            console.print(f"[bold red]Error:[/bold red] {e}")
        else:
            print(f"Error: {e}")
        sys.exit(1)


def _display_text_results(result: dict):
    """Display results in text format."""
    if HAS_RICH and console:
        # Rich output
        console.print(f"\n[bold]Analysis Results[/bold]")
        console.print(f"Duration: {result['duration']:.2f}s")
        console.print(f"Total errors: {result['statistics']['total']}")
        
        # Severity breakdown
        if result['statistics']['by_severity']:
            table = Table(title="Errors by Severity")
            table.add_column("Severity", style="cyan")
            table.add_column("Count", style="magenta")
            
            for severity, count in result['statistics']['by_severity'].items():
                table.add_row(severity, str(count))
            
            console.print(table)
        
        # Tool results
        if result['tool_results']:
            table = Table(title="Tool Results")
            table.add_column("Tool", style="cyan")
            table.add_column("Issues Found", style="magenta")
            
            for tool, count in result['tool_results'].items():
                table.add_row(tool, str(count))
            
            console.print(table)
        
        # Show some errors
        if result['errors'][:5]:
            console.print("\n[bold]Top Issues:[/bold]")
            for i, error in enumerate(result['errors'][:5], 1):
                console.print(
                    f"{i}. [{error.severity}] {error.file_path}:{error.line} - {error.message}"
                )
    else:
        # Plain output
        print(f"\nAnalysis Results")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Total errors: {result['statistics']['total']}")
        
        if result['statistics']['by_severity']:
            print("\nErrors by Severity:")
            for severity, count in result['statistics']['by_severity'].items():
                print(f"  {severity}: {count}")
        
        if result['tool_results']:
            print("\nTool Results:")
            for tool, count in result['tool_results'].items():
                print(f"  {tool}: {count}")
        
        if result['errors'][:5]:
            print("\nTop Issues:")
            for i, error in enumerate(result['errors'][:5], 1):
                print(f"  {i}. [{error.severity}] {error.file_path}:{error.line} - {error.message}")


def _run_resolution_interactive(codebase, errors):
    """Run interactive AI resolution."""
    if not HAS_RICH:
        print("Interactive mode requires 'rich' package")
        return
    
    gs_adapter = GraphSitterAdapter(codebase)
    ai_adapter = AutoGenLibAdapter(codebase, gs_adapter)
    
    console.print("\n[bold]AI Resolution (Interactive)[/bold]")
    console.print("Select errors to fix (or 'q' to quit):")
    
    for i, error in enumerate(errors[:10], 1):
        console.print(f"{i}. {error.file_path}:{error.line} - {error.message}")
    
    selection = click.prompt("Enter numbers (comma-separated)", default="1")
    
    if selection.lower() == 'q':
        return
    
    try:
        indices = [int(x.strip()) - 1 for x in selection.split(',')]
        selected_errors = [errors[i] for i in indices if 0 <= i < len(errors)]
        
        if selected_errors:
            fixes = ai_adapter.resolve_multiple_errors(selected_errors)
            _display_fixes(fixes)
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")


def _display_fixes(fixes: list):
    """Display generated fixes."""
    if HAS_RICH and console:
        for i, fix in enumerate(fixes, 1):
            panel = Panel(
                f"[green]Fix {i}[/green]\n"
                f"Confidence: {fix.get('confidence', 0):.1%}\n"
                f"Explanation: {fix.get('explanation', 'N/A')}\n"
                f"Code:\n{fix.get('fix_code', 'N/A')}",
                title=f"Fix #{i}"
            )
            console.print(panel)
    else:
        for i, fix in enumerate(fixes, 1):
            print(f"\nFix {i}:")
            print(f"  Confidence: {fix.get('confidence', 0):.1%}")
            print(f"  Explanation: {fix.get('explanation', 'N/A')}")
            print(f"  Code: {fix.get('fix_code', 'N/A')}")


def _find_repo_root(path: Path) -> Optional[Path]:
    """Find repository root by looking for .git directory."""
    current = path.absolute()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return None


def _generate_html_report(result: dict) -> str:
    """Generate HTML report."""
    html = f"""
    <html>
    <head><title>Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .error {{ color: red; }}
        .warning {{ color: orange; }}
        .info {{ color: blue; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
    </head>
    <body>
    <h1>Analysis Report</h1>
    <p>Duration: {result['duration']:.2f}s</p>
    <p>Total errors: {result['statistics']['total']}</p>
    
    <h2>Errors by Severity</h2>
    <table>
    <tr><th>Severity</th><th>Count</th></tr>
    """
    
    for severity, count in result['statistics'].get('by_severity', {}).items():
        html += f"<tr><td>{severity}</td><td>{count}</td></tr>"
    
    html += "</table></body></html>"
    return html


if __name__ == '__main__':
    cli()
