"""
CLI command for accessing diagnostics from LSP and SolidLSP.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

from graph_sitter.cli.commands.lsp.lsp import lsp
from graph_sitter.extensions.lsp.diagnostics import DiagnosticsManager
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
console = Console()


@lsp.command("diagnostics")
@click.option(
    "--file", "-f",
    help="File to analyze for diagnostics",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "--include-pattern", "-i",
    help="File pattern to include (e.g. '*.py')",
    multiple=True,
)
@click.option(
    "--exclude-pattern", "-e",
    help="File pattern to exclude (e.g. 'test_*.py')",
    multiple=True,
)
@click.option(
    "--severity", "-s",
    help="Filter by severity (error, warning, info, hint)",
    type=click.Choice(["error", "warning", "info", "hint"], case_sensitive=False),
    multiple=True,
)
@click.option(
    "--output", "-o",
    help="Output format (table, json)",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
)
@click.option(
    "--output-file",
    help="File to write output to",
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
)
@click.option(
    "--stats-only", is_flag=True,
    help="Show only statistics, not individual diagnostics",
)
def diagnostics_command(
    file: Optional[str],
    include_pattern: List[str],
    exclude_pattern: List[str],
    severity: List[str],
    output: str,
    output_file: Optional[str],
    stats_only: bool,
) -> None:
    """
    Get diagnostics from LSP and SolidLSP.
    
    This command retrieves diagnostics from both the normal LSP integration
    and SolidLSP's advanced diagnostics capabilities.
    """
    # Get current directory as codebase path
    codebase_path = os.getcwd()
    
    # Run the async function
    asyncio.run(_get_diagnostics(
        codebase_path=codebase_path,
        file_path=file,
        include_patterns=include_pattern,
        exclude_patterns=exclude_pattern,
        severities=severity,
        output_format=output,
        output_file=output_file,
        stats_only=stats_only,
    ))


async def _get_diagnostics(
    codebase_path: str,
    file_path: Optional[str] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    severities: Optional[List[str]] = None,
    output_format: str = "table",
    output_file: Optional[str] = None,
    stats_only: bool = False,
) -> None:
    """Get diagnostics from LSP and SolidLSP."""
    # Initialize diagnostics manager
    diagnostics_manager = DiagnosticsManager(codebase_path)
    
    try:
        # Initialize the manager
        success = await diagnostics_manager.initialize()
        if not success:
            console.print("[bold red]Failed to initialize diagnostics manager[/bold red]")
            return
        
        # Get diagnostics
        if file_path:
            # Analyze a specific file
            diagnostics = await diagnostics_manager.analyze_file(file_path)
            result = {Path(file_path).as_uri(): diagnostics}
        else:
            # Analyze the entire codebase
            result = await diagnostics_manager.analyze_codebase(
                file_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
        
        # Filter by severity if needed
        if severities:
            severity_map = {
                "error": 1,
                "warning": 2,
                "info": 3,
                "hint": 4,
            }
            severity_values = [severity_map[s.lower()] for s in severities]
            
            filtered_result = {}
            for uri, diags in result.items():
                filtered_diags = [d for d in diags if d.severity in severity_values]
                if filtered_diags:
                    filtered_result[uri] = filtered_diags
            
            result = filtered_result
        
        # Get statistics
        total_diagnostics = sum(len(diags) for diags in result.values())
        files_with_diagnostics = len(result)
        
        # Count by severity
        severity_counts = {
            "error": 0,
            "warning": 0,
            "info": 0,
            "hint": 0,
        }
        
        for diags in result.values():
            for diag in diags:
                if diag.severity == 1:
                    severity_counts["error"] += 1
                elif diag.severity == 2:
                    severity_counts["warning"] += 1
                elif diag.severity == 3:
                    severity_counts["info"] += 1
                elif diag.severity == 4:
                    severity_counts["hint"] += 1
        
        # Output statistics
        if output_format == "table":
            # Create statistics table
            stats_table = Table(title="Diagnostics Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Total Diagnostics", str(total_diagnostics))
            stats_table.add_row("Files with Diagnostics", str(files_with_diagnostics))
            stats_table.add_row("Errors", str(severity_counts["error"]))
            stats_table.add_row("Warnings", str(severity_counts["warning"]))
            stats_table.add_row("Information", str(severity_counts["info"]))
            stats_table.add_row("Hints", str(severity_counts["hint"]))
            
            console.print(stats_table)
            
            # Output individual diagnostics if not stats_only
            if not stats_only and total_diagnostics > 0:
                diag_table = Table(title="Diagnostics")
                diag_table.add_column("File", style="blue")
                diag_table.add_column("Line", style="cyan")
                diag_table.add_column("Column", style="cyan")
                diag_table.add_column("Severity", style="magenta")
                diag_table.add_column("Message", style="green")
                
                for uri, diags in result.items():
                    file_path = uri.replace("file://", "")
                    rel_path = os.path.relpath(file_path, codebase_path)
                    
                    for diag in diags:
                        severity_str = "Error"
                        severity_style = "bold red"
                        
                        if diag.severity == 2:
                            severity_str = "Warning"
                            severity_style = "bold yellow"
                        elif diag.severity == 3:
                            severity_str = "Info"
                            severity_style = "bold blue"
                        elif diag.severity == 4:
                            severity_str = "Hint"
                            severity_style = "bold green"
                        
                        diag_table.add_row(
                            rel_path,
                            str(diag.range.start.line + 1),
                            str(diag.range.start.character + 1),
                            f"[{severity_style}]{severity_str}[/{severity_style}]",
                            diag.message
                        )
                
                console.print(diag_table)
        
        elif output_format == "json":
            # Convert to JSON-serializable format
            json_result = {
                "statistics": {
                    "total_diagnostics": total_diagnostics,
                    "files_with_diagnostics": files_with_diagnostics,
                    "severity_counts": severity_counts,
                },
                "diagnostics": {},
            }
            
            if not stats_only:
                for uri, diags in result.items():
                    file_path = uri.replace("file://", "")
                    rel_path = os.path.relpath(file_path, codebase_path)
                    
                    json_result["diagnostics"][rel_path] = []
                    
                    for diag in diags:
                        json_result["diagnostics"][rel_path].append({
                            "line": diag.range.start.line + 1,
                            "column": diag.range.start.character + 1,
                            "severity": diag.severity,
                            "message": diag.message,
                            "source": diag.source,
                        })
            
            # Output JSON
            json_str = json.dumps(json_result, indent=2)
            
            if output_file:
                with open(output_file, "w") as f:
                    f.write(json_str)
                console.print(f"[bold green]Output written to {output_file}[/bold green]")
            else:
                console.print(json_str)
    
    finally:
        # Clean up
        await diagnostics_manager.cleanup()

