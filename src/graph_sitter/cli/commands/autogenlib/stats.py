"""CLI command for viewing autogenlib statistics and analytics."""

import click
import json
from datetime import datetime, timedelta
from typing import Optional

from graph_sitter.integrations.autogenlib import AutogenLibIntegration, AutogenLibConfig
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@click.group()
def stats_command():
    """View autogenlib integration statistics and analytics."""
    pass


@stats_command.command("overview")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format"
)
def overview(config_file: Optional[str], format: str):
    """Show overview of autogenlib statistics."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Create integration
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            click.echo("❌ AutogenLib integration is not enabled")
            return
            
        # Get statistics
        stats = integration.get_statistics()
        
        if format == "json":
            click.echo(json.dumps(stats, indent=2))
        else:
            # Table format
            click.echo("AutogenLib Integration Statistics")
            click.echo("=" * 40)
            
            click.echo(f"Status: {'✅ Enabled' if stats['enabled'] else '❌ Disabled'}")
            
            if stats.get("config"):
                config_info = stats["config"]
                click.echo("\nConfiguration:")
                click.echo(f"  Graph-Sitter Context: {'✅' if config_info.get('use_graph_sitter_context') else '❌'}")
                click.echo(f"  Caching: {'✅' if config_info.get('enable_caching') else '❌'}")
                click.echo(f"  Max Context Size: {config_info.get('max_context_size', 'N/A')}")
                
            # Generation statistics
            if stats.get("total_generations") is not None:
                click.echo("\nGeneration Statistics:")
                click.echo(f"  Total Generations: {stats.get('total_generations', 0)}")
                click.echo(f"  Successful: {stats.get('successful_generations', 0)}")
                click.echo(f"  Failed: {stats.get('failed_generations', 0)}")
                
                total = stats.get('total_generations', 0)
                if total > 0:
                    success_rate = (stats.get('successful_generations', 0) / total) * 100
                    click.echo(f"  Success Rate: {success_rate:.1f}%")
                    
                avg_time = stats.get('average_generation_time', 0)
                if avg_time > 0:
                    click.echo(f"  Average Generation Time: {avg_time:.2f}s")
                    
            # Cache statistics
            cache_hit_rate = stats.get('cache_hit_rate', 0)
            if cache_hit_rate > 0:
                click.echo(f"\nCache Performance:")
                click.echo(f"  Hit Rate: {cache_hit_rate:.1f}%")
                
            # Popular patterns
            patterns = stats.get('most_common_patterns', [])
            if patterns:
                click.echo(f"\nMost Common Patterns:")
                for i, pattern in enumerate(patterns[:5], 1):
                    click.echo(f"  {i}. {pattern}")
                    
    except Exception as e:
        logger.error(f"Error showing overview: {e}", exc_info=True)
        click.echo(f"❌ Error showing statistics: {e}", err=True)


@stats_command.command("history")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Number of recent generations to show"
)
@click.option(
    "--module",
    "-m",
    help="Filter by module name"
)
@click.option(
    "--success-only",
    is_flag=True,
    help="Show only successful generations"
)
def history(config_file: Optional[str], limit: int, module: Optional[str], success_only: bool):
    """Show generation history."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Create integration
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            click.echo("❌ AutogenLib integration is not enabled")
            return
            
        # Get generation history
        history_data = integration.get_generation_history(limit=limit)
        
        if not history_data:
            click.echo("No generation history found")
            return
            
        # Filter if requested
        if module:
            history_data = [h for h in history_data if module.lower() in h.get('module_name', '').lower()]
            
        if success_only:
            history_data = [h for h in history_data if h.get('success', False)]
            
        click.echo(f"Generation History (showing {len(history_data)} entries)")
        click.echo("=" * 60)
        
        for entry in history_data:
            status = "✅" if entry.get('success') else "❌"
            module_name = entry.get('module_name', 'Unknown')
            function_name = entry.get('function_name', '')
            timestamp = entry.get('created_at', 'Unknown')
            generation_time = entry.get('generation_time', 0)
            
            click.echo(f"{status} {module_name}")
            if function_name:
                click.echo(f"   Function: {function_name}")
            click.echo(f"   Time: {timestamp} ({generation_time:.2f}s)")
            
            if not entry.get('success') and entry.get('error_message'):
                click.echo(f"   Error: {entry['error_message']}")
                
            click.echo()
            
    except Exception as e:
        logger.error(f"Error showing history: {e}", exc_info=True)
        click.echo(f"❌ Error showing history: {e}", err=True)


@stats_command.command("cache")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear the cache"
)
@click.option(
    "--module",
    "-m",
    help="Clear cache for specific module"
)
def cache(config_file: Optional[str], clear: bool, module: Optional[str]):
    """Manage generation cache."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Create integration
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            click.echo("❌ AutogenLib integration is not enabled")
            return
            
        if clear:
            if module:
                integration.clear_cache(module)
                click.echo(f"✅ Cache cleared for module: {module}")
            else:
                if click.confirm("Are you sure you want to clear all cache?"):
                    integration.clear_cache()
                    click.echo("✅ All cache cleared")
        else:
            # Show cache information
            cached_modules = integration.get_cached_modules()
            
            if not cached_modules:
                click.echo("No cached modules found")
                return
                
            click.echo(f"Cached Modules ({len(cached_modules)} total)")
            click.echo("=" * 40)
            
            for cached_module in cached_modules:
                click.echo(f"📦 {cached_module}")
                
    except Exception as e:
        logger.error(f"Error managing cache: {e}", exc_info=True)
        click.echo(f"❌ Error managing cache: {e}", err=True)


@stats_command.command("patterns")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--type",
    "-t",
    help="Filter by pattern type"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=20,
    help="Number of patterns to show"
)
def patterns(config_file: Optional[str], type: Optional[str], limit: int):
    """Show successful generation patterns."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Create integration
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            click.echo("❌ AutogenLib integration is not enabled")
            return
            
        # This would get patterns from the database
        # For now, show placeholder
        click.echo("Generation Patterns")
        click.echo("=" * 30)
        click.echo("(Pattern analysis would be implemented with database integration)")
        
        # Example patterns that would be shown
        example_patterns = [
            {"name": "utility_function", "type": "function", "success_count": 15},
            {"name": "data_class", "type": "class", "success_count": 12},
            {"name": "api_client", "type": "class", "success_count": 8},
            {"name": "test_function", "type": "function", "success_count": 6},
        ]
        
        for pattern in example_patterns:
            if type and pattern["type"] != type:
                continue
                
            click.echo(f"🔄 {pattern['name']} ({pattern['type']})")
            click.echo(f"   Success Count: {pattern['success_count']}")
            click.echo()
            
    except Exception as e:
        logger.error(f"Error showing patterns: {e}", exc_info=True)
        click.echo(f"❌ Error showing patterns: {e}", err=True)


if __name__ == "__main__":
    stats_command()

