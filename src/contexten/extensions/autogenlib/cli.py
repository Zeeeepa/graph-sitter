"""Command-line interface for AutoGenLib integration."""

import click
import json
import os
from typing import Optional

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from .config import AutoGenLibConfig, load_config
from .integration import init_contexten_autogenlib, get_contexten_autogenlib
from .core import init_autogenlib

logger = get_logger(__name__)


@click.group()
def autogenlib():
    """AutoGenLib integration commands."""
    pass


@autogenlib.command()
@click.option("--config-file", help="Path to configuration file")
def status(config_file: Optional[str]):
    """Show AutoGenLib integration status."""
    try:
        # Load configuration
        if config_file and os.path.exists(config_file):
            # TODO: Implement config file loading
            config = load_config()
        else:
            config = load_config()
        
        # Initialize integration
        integration = init_contexten_autogenlib(config=config)
        status_info = integration.get_status()
        
        click.echo("AutoGenLib Integration Status:")
        click.echo("=" * 40)
        
        # Basic status
        click.echo(f"Initialized: {status_info['initialized']}")
        click.echo(f"Config Valid: {status_info['config_valid']}")
        click.echo(f"Has Codebase: {status_info['has_codebase']}")
        click.echo(f"Has CodegenApp: {status_info['has_codegen_app']}")
        click.echo(f"Cache Enabled: {status_info['cache_enabled']}")
        
        # Available providers
        providers = status_info['available_providers']
        click.echo(f"Available Providers: {', '.join(providers) if providers else 'None'}")
        
        # Codebase stats
        if status_info.get('codebase_stats'):
            stats = status_info['codebase_stats']
            click.echo("\nCodebase Statistics:")
            click.echo(f"  Functions: {stats['functions']}")
            click.echo(f"  Classes: {stats['classes']}")
            click.echo(f"  Files: {stats['files']}")
        
        # Cache info
        if status_info.get('cache_info'):
            cache = status_info['cache_info']
            click.echo("\nCache Information:")
            click.echo(f"  Enabled: {cache['enabled']}")
            click.echo(f"  Cached Modules: {cache['cached_modules']}")
            click.echo(f"  Total Size: {cache.get('total_size_mb', 0)} MB")
        
        # Configuration issues
        issues = config.validate()
        if issues:
            click.echo("\nConfiguration Issues:")
            for issue in issues:
                click.echo(f"  - {issue}")
        
    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)


@autogenlib.command()
@click.option("--repo", help="Repository to analyze (e.g., 'owner/repo')")
@click.option("--description", default="Dynamic code generation library", help="Library description")
@click.option("--enable-cache/--disable-cache", default=False, help="Enable/disable caching")
def init(repo: Optional[str], description: str, enable_cache: bool):
    """Initialize AutoGenLib with optional codebase context."""
    try:
        codebase = None
        
        # Load codebase if repository specified
        if repo:
            click.echo(f"Loading codebase from {repo}...")
            codebase = Codebase.from_repo(repo)
            click.echo(f"Loaded codebase with {len(codebase.functions)} functions")
        
        # Load configuration
        config = load_config()
        config.description = description
        config.enable_caching = enable_cache
        
        # Initialize AutoGenLib
        integration = init_autogenlib(
            description=description,
            codebase=codebase,
            codegen_org_id=config.codegen_org_id,
            codegen_token=config.codegen_token,
            claude_api_key=config.claude_api_key,
            enable_caching=enable_cache
        )
        
        click.echo("AutoGenLib initialized successfully!")
        click.echo(f"Description: {description}")
        click.echo(f"Caching: {'Enabled' if enable_cache else 'Disabled'}")
        click.echo(f"Codebase: {'Loaded' if codebase else 'None'}")
        
    except Exception as e:
        click.echo(f"Error initializing AutoGenLib: {e}", err=True)


@autogenlib.command()
@click.argument("module_name")
@click.option("--description", help="Description of what to generate")
@click.option("--output", help="Output file to save generated code")
def generate(module_name: str, description: Optional[str], output: Optional[str]):
    """Generate code for a specific module."""
    try:
        # Get the integration instance
        integration = get_contexten_autogenlib()
        if not integration or not integration.is_available():
            click.echo("AutoGenLib not initialized. Run 'autogenlib init' first.", err=True)
            return
        
        # Generate the code
        click.echo(f"Generating code for module: {module_name}")
        code = integration.autogenlib.generate_module(
            fullname=module_name,
            description=description
        )
        
        if code:
            if output:
                # Save to file
                with open(output, 'w') as f:
                    f.write(code)
                click.echo(f"Generated code saved to: {output}")
            else:
                # Print to stdout
                click.echo("Generated code:")
                click.echo("=" * 40)
                click.echo(code)
        else:
            click.echo("Failed to generate code", err=True)
            
    except Exception as e:
        click.echo(f"Error generating code: {e}", err=True)


@autogenlib.command()
def clear_cache():
    """Clear the AutoGenLib cache."""
    try:
        integration = get_contexten_autogenlib()
        if integration:
            integration.clear_cache()
            click.echo("Cache cleared successfully")
        else:
            click.echo("AutoGenLib not initialized", err=True)
            
    except Exception as e:
        click.echo(f"Error clearing cache: {e}", err=True)


@autogenlib.command()
def list_cache():
    """List cached modules."""
    try:
        integration = get_contexten_autogenlib()
        if not integration or not integration.is_available():
            click.echo("AutoGenLib not initialized", err=True)
            return
        
        if integration.autogenlib.cache.enabled:
            cached_modules = integration.autogenlib.cache.list_cached()
            if cached_modules:
                click.echo("Cached modules:")
                for module in cached_modules:
                    click.echo(f"  - {module}")
            else:
                click.echo("No modules cached")
        else:
            click.echo("Caching is disabled")
            
    except Exception as e:
        click.echo(f"Error listing cache: {e}", err=True)


@autogenlib.command()
@click.option("--format", "output_format", type=click.Choice(["json", "yaml"]), default="json")
def config(output_format: str):
    """Show current configuration."""
    try:
        config = load_config()
        config_dict = config.to_dict()
        
        if output_format == "json":
            click.echo(json.dumps(config_dict, indent=2))
        else:
            # Simple YAML-like output
            for key, value in config_dict.items():
                click.echo(f"{key}: {value}")
                
    except Exception as e:
        click.echo(f"Error showing config: {e}", err=True)


@autogenlib.command()
@click.argument("module_name")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
def test(module_name: str, interactive: bool):
    """Test code generation for a module."""
    try:
        # Get the integration instance
        integration = get_contexten_autogenlib()
        if not integration or not integration.is_available():
            click.echo("AutoGenLib not initialized. Run 'autogenlib init' first.", err=True)
            return
        
        if interactive:
            # Interactive mode
            description = click.prompt("Enter description for the module")
            
            # Show context if available
            if integration.autogenlib.context_provider:
                click.echo("Gathering context...")
                context = integration.autogenlib.context_provider.get_context(module_name)
                if context.get('related_functions'):
                    click.echo(f"Found {len(context['related_functions'])} related functions")
                if context.get('dependencies'):
                    click.echo(f"Found {len(context['dependencies'])} dependencies")
        else:
            description = f"Generate functionality for {module_name}"
        
        # Generate and display
        click.echo(f"Generating code for: {module_name}")
        click.echo(f"Description: {description}")
        click.echo("=" * 50)
        
        code = integration.autogenlib.generate_module(
            fullname=module_name,
            description=description
        )
        
        if code:
            click.echo(code)
            
            if interactive:
                if click.confirm("Save this code?"):
                    filename = click.prompt("Enter filename", default=f"{module_name.split('.')[-1]}.py")
                    with open(filename, 'w') as f:
                        f.write(code)
                    click.echo(f"Code saved to {filename}")
        else:
            click.echo("Failed to generate code", err=True)
            
    except Exception as e:
        click.echo(f"Error testing generation: {e}", err=True)


if __name__ == "__main__":
    autogenlib()

