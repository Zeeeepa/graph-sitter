#!/usr/bin/env python3
"""
Analysis CLI Command

Provides comprehensive code analysis through the gs analyze subcommand.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Import analysis components with graceful fallbacks
try:
    from graph_sitter.extensions.analysis import FEATURES
    from graph_sitter.extensions.analysis.comprehensive import ComprehensiveAnalyzer
    from graph_sitter.extensions.analysis.database import ErrorDatabase
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    ANALYSIS_AVAILABLE = False
    IMPORT_ERROR = str(e)

console = Console()


@click.group(name="analyze")
def analyze_command():
    """Comprehensive code analysis using multiple tools and techniques."""
    if not ANALYSIS_AVAILABLE:
        console.print(
            Panel(
                f"[bold red]Analysis features not available[/bold red]\n\n"
                f"Error: {IMPORT_ERROR}\n\n"
                f"Install analysis dependencies with:\n"
                f"[bold green]pip install -e .[analysis][/bold green]\n"
                f"or\n"
                f"[bold green]pip install -e .[full-analysis][/bold green]",
                title="Analysis Not Available",
                border_style="red"
            )
        )
        sys.exit(1)


@analyze_command.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--profile",
    type=click.Choice(["basic", "standard", "comprehensive", "security", "type_checking"]),
    help="Analysis profile to use"
)
@click.option(
    "--comprehensive", 
    is_flag=True, 
    help="Run comprehensive analysis (same as --profile comprehensive)"
)
@click.option(
    "--tools", 
    multiple=True, 
    help="Specific tools to run (ruff, mypy, pyflakes, pycodestyle, lsp)"
)
@click.option(
    "--output", 
    type=click.Choice(["console", "json", "html"]), 
    default="console",
    help="Output format"
)
@click.option(
    "--config", 
    type=click.Path(exists=True),
    help="Configuration file path"
)
@click.option(
    "--save-results", 
    is_flag=True,
    help="Save analysis results to database"
)
@click.option(
    "--verbose", "-v", 
    is_flag=True,
    help="Verbose output"
)
def run(
    path: str,
    profile: Optional[str],
    comprehensive: bool,
    tools: tuple,
    output: str,
    config: Optional[str],
    save_results: bool,
    verbose: bool
):
    """Run code analysis on the specified path."""
    
    # Resolve path
    target_path = Path(path).resolve()
    if not target_path.exists():
        console.print(f"[red]Error: Path {target_path} does not exist[/red]")
        sys.exit(1)
    
    # Build configuration
    config_dict = {}
    if config:
        config_dict["config_file"] = config
    
    # Determine analysis profile
    if comprehensive:
        analysis_profile = "comprehensive"
    elif profile:
        analysis_profile = profile
    else:
        analysis_profile = "standard"  # Default profile
    
    if verbose:
        console.print(f"[blue]Analyzing:[/blue] {target_path}")
        console.print(f"[blue]Profile:[/blue] {analysis_profile}")
    
    try:
        # Initialize analyzer with profile
        analyzer = ComprehensiveAnalyzer(
            target_path=str(target_path),
            config=config_dict,
            verbose=verbose,
            profile=analysis_profile
        )
        
        # Override enabled tools if specific tools requested
        if tools:
            for tool_name in analyzer.config_manager.config.get("tools", {}):
                tool_config = analyzer.config_manager.config["tools"][tool_name]
                tool_config["enabled"] = tool_name in tools
        
        # Run analysis
        results = analyzer.run_comprehensive_analysis()
        
        # Output results
        if output == "json":
            _output_json(results)
        elif output == "html":
            _output_html(results, target_path)
        else:
            _output_console(results, verbose)
        
        # Return appropriate exit code
        error_count = results.get("summary", {}).get("overview", {}).get("total_errors", 0)
        if error_count > 0:
            sys.exit(1)
        else:
            console.print("\n[green]✓ No issues found![/green]")
            
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@analyze_command.command()
@click.option("--limit", default=10, help="Number of recent sessions to show")
@click.option("--detailed", is_flag=True, help="Show detailed session information")
def history(limit: int, detailed: bool):
    """Show analysis history from database."""
    
    try:
        db = ErrorDatabase()
        sessions = db.get_recent_sessions(limit)
        
        if not sessions:
            console.print("[yellow]No analysis sessions found[/yellow]")
            return
        
        table = Table(title="Analysis History")
        table.add_column("ID", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Date", style="blue")
        table.add_column("Tools", style="magenta")
        table.add_column("Errors", style="red")
        
        for session in sessions:
            table.add_row(
                str(session.get("id", "")),
                str(session.get("target_path", "")),
                str(session.get("created_at", "")),
                ", ".join(session.get("tools_used", [])),
                str(session.get("error_count", 0))
            )
        
        console.print(table)
        
        if detailed and sessions:
            # Show details for most recent session
            recent_session = sessions[0]
            console.print(f"\n[bold]Recent Session Details:[/bold]")
            console.print(f"ID: {recent_session.get('id')}")
            console.print(f"Configuration: {recent_session.get('config', {})}")
            
    except Exception as e:
        console.print(f"[red]Failed to retrieve history: {e}[/red]")
        sys.exit(1)


@analyze_command.command()
@click.option("--all", is_flag=True, help="Clear all analysis history")
@click.option("--session-id", type=int, help="Clear specific session")
def clear(all: bool, session_id: Optional[int]):
    """Clear analysis history from database."""
    
    try:
        db = ErrorDatabase()
        
        if session_id:
            db.delete_session(session_id)
            console.print(f"[green]✓ Cleared session {session_id}[/green]")
        elif all:
            # Confirm before clearing all
            if click.confirm("Are you sure you want to clear all analysis history?"):
                db.clear_all_sessions()
                console.print("[green]✓ Cleared all analysis history[/green]")
            else:
                console.print("[yellow]Operation cancelled[/yellow]")
        else:
            console.print("[yellow]Specify --all or --session-id[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Failed to clear history: {e}[/red]")
        sys.exit(1)


@analyze_command.command()
def status():
    """Show analysis system status and available tools."""
    
    console.print("[bold]Analysis System Status[/bold]\n")
    
    # Show feature availability
    features_table = Table(title="Available Features")
    features_table.add_column("Feature", style="cyan")
    features_table.add_column("Status", style="green")
    
    for feature, available in FEATURES.items():
        status_text = "✓ Available" if available else "✗ Not Available"
        style = "green" if available else "red"
        features_table.add_row(feature.replace("_", " ").title(), f"[{style}]{status_text}[/{style}]")
    
    console.print(features_table)
    
    # Tool availability
    console.print("\n[bold]Tool Availability:[/bold]")
    
    tools_to_check = {
        "ruff": "ruff --version",
        "mypy": "mypy --version", 
        "pyflakes": "pyflakes --version",
        "pycodestyle": "pycodestyle --version",
    }
    
    for tool, cmd in tools_to_check.items():
        try:
            import subprocess
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                console.print(f"  [green]✓[/green] {tool}")
            else:
                console.print(f"  [red]✗[/red] {tool} (not working)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            console.print(f"  [red]✗[/red] {tool} (not installed)")
    
    # Database status
    try:
        db = ErrorDatabase()
        session_count = len(db.get_recent_sessions(1000))
        console.print(f"\n[bold]Database:[/bold] {session_count} analysis sessions stored")
    except Exception:
        console.print(f"\n[bold]Database:[/bold] [red]Not accessible[/red]")


def _output_console(results: dict, verbose: bool):
    """Output results to console in rich format."""
    
    metadata = results.get("metadata", {})
    summary = results.get("summary", {})
    errors = results.get("errors", [])
    
    # Header
    console.print(Panel(
        f"[bold]Analysis Results[/bold]\n"
        f"Target: {metadata.get('target_path', 'Unknown')}\n"
        f"Time: {metadata.get('analysis_time', 0)}s\n"
        f"Tools: {', '.join(metadata.get('tools_used', []))}\n"
        f"Quality Score: {results.get('quality_score', 'N/A')}/100",
        title="Graph-Sitter Analysis",
        border_style="blue"
    ))
    
    # Summary
    overview = summary.get("overview", {})
    if overview.get("total_errors", 0) > 0:
        console.print(f"\n[red]Found {overview['total_errors']} issues:[/red]")
        
        # Group errors by category
        categorized = results.get("categorized_errors", {})
        for category, category_errors in categorized.items():
            if category_errors:
                console.print(f"\n[yellow]{category.replace('_', ' ').title()}:[/yellow] {len(category_errors)} issues")
                
                # Show first few errors in each category
                for error in category_errors[:3]:
                    # Handle both dict and AnalysisError objects
                    if hasattr(error, 'file_path'):
                        error_text = f"  {error.file_path}:{error.line} - {error.message}"
                    else:
                        error_text = f"  {error.get('file_path', '')}:{error.get('line', 0)} - {error.get('message', '')}"
                    console.print(f"  [dim]{error_text}[/dim]")
                
                if len(category_errors) > 3:
                    console.print(f"  [dim]... and {len(category_errors) - 3} more[/dim]")
    
    if verbose and errors:
        console.print("\n[bold]All Issues:[/bold]")
        for error in errors[:20]:  # Limit to first 20 in verbose mode
            # Handle both dict and AnalysisError objects
            if hasattr(error, 'file_path'):
                console.print(f"  {error.file_path}:{error.line} [{error.severity}] {error.message}")
            else:
                console.print(f"  {error.get('file_path', '')}:{error.get('line', 0)} [{error.get('severity', 'INFO')}] {error.get('message', '')}")
        
        if len(errors) > 20:
            console.print(f"  [dim]... and {len(errors) - 20} more issues[/dim]")


def _output_json(results: dict):
    """Output results as JSON."""
    print(json.dumps(results, indent=2, default=str))


def _output_html(results: dict, target_path: Path):
    """Output results as HTML report."""
    html_path = target_path.parent / f"analysis_report_{target_path.name}.html"
    
    # Simple HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis Report - {target_path.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .error {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ff6b6b; background: #fff5f5; }}
            .warning {{ border-left-color: #ffd93d; background: #fffbf0; }}
            .info {{ border-left-color: #74c0fc; background: #f0f8ff; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Analysis Report</h1>
            <p><strong>Target:</strong> {results.get('metadata', {}).get('target_path', 'Unknown')}</p>
            <p><strong>Analysis Time:</strong> {results.get('metadata', {}).get('analysis_time', 0)}s</p>
            <p><strong>Tools Used:</strong> {', '.join(results.get('metadata', {}).get('tools_used', []))}</p>
            <p><strong>Quality Score:</strong> {results.get('quality_score', 'N/A')}/100</p>
        </div>
        
        <h2>Issues Found: {results.get('summary', {}).get('overview', {}).get('total_errors', 0)}</h2>
        
        <div class="issues">
    """
    
    # Add errors
    for error in results.get("errors", []):
        severity_class = error.get("severity", "INFO").lower()
        html_content += f"""
            <div class="error {severity_class}">
                <strong>{error.get('file_path', '')}:{error.get('line', 0)}</strong> 
                [{error.get('severity', 'INFO')}] {error.get('message', '')}<br>
                <small>Tool: {error.get('tool_source', 'unknown')} | Category: {error.get('category', 'general')}</small>
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    console.print(f"[green]HTML report saved to: {html_path}[/green]")