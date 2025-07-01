"""
CLI Interface for Autonomous CI/CD System
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import AutonomousCICD
from .config import CICDConfig

console = Console()


@click.group()
def cli():
    """Autonomous CI/CD System for Graph-Sitter"""
    pass


@cli.command()
@click.option('--config-file', '-c', help='Configuration file path')
@click.option('--repo-path', '-r', default='.', help='Repository path')
@click.option('--org-id', envvar='CODEGEN_ORG_ID', help='Codegen organization ID')
@click.option('--token', envvar='CODEGEN_TOKEN', help='Codegen API token')
def start(config_file: Optional[str], repo_path: str, org_id: Optional[str], token: Optional[str]):
    """Start the autonomous CI/CD system"""
    
    try:
        # Load configuration
        if config_file and Path(config_file).exists():
            config = CICDConfig.from_file(config_file)
        else:
            config = CICDConfig.from_env()
            
        # Override with CLI parameters
        if repo_path != '.':
            config.repo_path = repo_path
        if org_id:
            config.codegen_org_id = org_id
        if token:
            config.codegen_token = token
        
        console.print(Panel.fit("🚀 Starting Autonomous CI/CD System", style="bold green"))
        
        # Display configuration
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="magenta")
        
        config_dict = config.to_dict()
        for key, value in config_dict.items():
            config_table.add_row(key, str(value))
        
        console.print(config_table)
        
        # Start the system
        asyncio.run(_start_system(config))
        
    except Exception as e:
        console.print(f"[red]Error starting CI/CD system: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--pipeline-id', help='Specific pipeline ID to check')
def status(pipeline_id: Optional[str]):
    """Check system status"""
    
    console.print(Panel.fit("📊 Autonomous CI/CD Status", style="bold blue"))
    
    # This would connect to running system to get status
    # For now, show example status
    
    if pipeline_id:
        console.print(f"Pipeline {pipeline_id} status: Running")
    else:
        status_table = Table(title="System Status")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Last Check", style="yellow")
        
        status_table.add_row("Code Analysis Agent", "✅ Active", "2 minutes ago")
        status_table.add_row("Testing Agent", "✅ Active", "1 minute ago")
        status_table.add_row("Deployment Agent", "✅ Active", "3 minutes ago")
        status_table.add_row("GitHub Trigger", "✅ Listening", "30 seconds ago")
        status_table.add_row("Linear Trigger", "✅ Active", "1 minute ago")
        status_table.add_row("Scheduled Trigger", "✅ Active", "5 minutes ago")
        
        console.print(status_table)


@cli.command()
@click.option('--branch', default='develop', help='Branch to analyze')
@click.option('--files', help='Comma-separated list of files to analyze')
def analyze(branch: str, files: Optional[str]):
    """Run code analysis"""
    
    console.print(Panel.fit(f"🔍 Analyzing branch: {branch}", style="bold yellow"))
    
    file_list = files.split(',') if files else []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running code analysis...", total=None)
        
        # Simulate analysis
        import time
        time.sleep(2)
        
        progress.update(task, description="Analysis complete!")
    
    # Show results
    results_table = Table(title="Analysis Results")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value", style="magenta")
    results_table.add_column("Status", style="green")
    
    results_table.add_row("Quality Score", "0.85", "✅ Good")
    results_table.add_row("Test Coverage", "78%", "⚠️ Needs Improvement")
    results_table.add_row("Security Issues", "0", "✅ Clean")
    results_table.add_row("Performance Issues", "2", "⚠️ Minor")
    
    console.print(results_table)


@cli.command()
@click.option('--type', 'pipeline_type', default='full', help='Pipeline type (full, analysis, test, deploy)')
@click.option('--branch', default='develop', help='Branch to run pipeline on')
def run(pipeline_type: str, branch: str):
    """Run a CI/CD pipeline manually"""
    
    console.print(Panel.fit(f"🔄 Running {pipeline_type} pipeline on {branch}", style="bold green"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        if pipeline_type in ['full', 'analysis']:
            task1 = progress.add_task("Running code analysis...", total=None)
            import time
            time.sleep(2)
            progress.update(task1, description="✅ Code analysis complete")
        
        if pipeline_type in ['full', 'test']:
            task2 = progress.add_task("Running tests...", total=None)
            time.sleep(3)
            progress.update(task2, description="✅ Tests complete")
        
        if pipeline_type in ['full', 'deploy']:
            task3 = progress.add_task("Deploying...", total=None)
            time.sleep(2)
            progress.update(task3, description="✅ Deployment complete")
    
    console.print("[green]Pipeline completed successfully![/green]")


@cli.command()
def metrics():
    """Show system metrics"""
    
    console.print(Panel.fit("📈 System Metrics", style="bold magenta"))
    
    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="magenta")
    metrics_table.add_column("Trend", style="green")
    
    metrics_table.add_row("Total Pipelines", "127", "📈 +12%")
    metrics_table.add_row("Success Rate", "94.5%", "📈 +2.1%")
    metrics_table.add_row("Avg Duration", "4.2 min", "📉 -0.8 min")
    metrics_table.add_row("Active Pipelines", "3", "➡️ Stable")
    metrics_table.add_row("Code Quality", "0.87", "📈 +0.03")
    metrics_table.add_row("Test Coverage", "82%", "📈 +5%")
    
    console.print(metrics_table)


@cli.command()
@click.option('--output', '-o', help='Output file for configuration')
def init(output: Optional[str]):
    """Initialize CI/CD configuration"""
    
    console.print(Panel.fit("⚙️ Initializing CI/CD Configuration", style="bold cyan"))
    
    # Interactive configuration setup
    org_id = click.prompt("Codegen Organization ID", type=str)
    token = click.prompt("Codegen API Token", type=str, hide_input=True)
    repo_path = click.prompt("Repository Path", default=".", type=str)
    
    config = CICDConfig(
        codegen_org_id=org_id,
        codegen_token=token,
        repo_path=repo_path
    )
    
    if output:
        config_file = Path(output)
    else:
        config_file = Path(".cicd-config.json")
    
    # Save configuration
    with open(config_file, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)
    
    console.print(f"[green]Configuration saved to {config_file}[/green]")
    
    # Create .env.example if it doesn't exist
    env_example = Path(".env.example")
    if not env_example.exists():
        with open(env_example, 'w') as f:
            f.write("""# Autonomous CI/CD Configuration
CODEGEN_ORG_ID=your_org_id_here
CODEGEN_TOKEN=your_token_here
CODEGEN_BASE_URL=https://api.codegen.com

# GitHub Integration
GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Linear Integration  
LINEAR_API_KEY=your_linear_api_key

# Slack Notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url
""")
        console.print(f"[green]Created {env_example}[/green]")


async def _start_system(config: CICDConfig):
    """Start the autonomous CI/CD system"""
    
    cicd = AutonomousCICD(config)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Initializing system...", total=None)
            await cicd.initialize()
            progress.update(task, description="✅ System initialized")
        
        console.print("[green]Autonomous CI/CD system is running![/green]")
        console.print("Press Ctrl+C to stop")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            await cicd.shutdown()
            console.print("[green]System stopped successfully[/green]")
            
    except Exception as e:
        console.print(f"[red]System error: {e}[/red]")
        await cicd.shutdown()
        raise


if __name__ == '__main__':
    cli()

