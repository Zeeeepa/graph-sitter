"""Main entry point for Contexten application.

This module provides the main entry point and CLI interface for running
the Contexten application with all extensions.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import click

from .contexten_app import ContextenApp
from .config.example_config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContextenRunner:
    """Runner for Contexten application."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize runner.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.app: Optional[ContextenApp] = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the Contexten application."""
        try:
            # Create and configure application
            self.app = ContextenApp(self.config)
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start application
            await self.app.start()
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}", exc_info=True)
            raise
        finally:
            if self.app:
                await self.app.stop()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check.
        
        Returns:
            Health check results
        """
        if not self.app:
            return {"status": "not_running"}
        
        return await self.app.health_check()

@click.group()
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
@click.option('--environment', default='development', help='Environment (development, testing, production)')
@click.option('--log-level', default='INFO', help='Log level')
@click.pass_context
def cli(ctx, config_file, environment, log_level):
    """Contexten - Comprehensive project management and workflow orchestration."""
    # Setup logging
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Load configuration
    if config_file:
        # Load from file (implement file loading logic)
        config = get_config(environment)  # Fallback to default
        logger.info(f"Using configuration file: {config_file}")
    else:
        config = get_config(environment)
        logger.info(f"Using {environment} configuration")
    
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['environment'] = environment

@cli.command()
@click.pass_context
def start(ctx):
    """Start the Contexten application."""
    config = ctx.obj['config']
    environment = ctx.obj['environment']
    
    logger.info(f"Starting Contexten in {environment} mode...")
    
    # Create and run application
    runner = ContextenRunner(config)
    
    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def health(ctx):
    """Check application health."""
    config = ctx.obj['config']
    
    async def check_health():
        runner = ContextenRunner(config)
        health_status = await runner.health_check()
        return health_status
    
    try:
        health_status = asyncio.run(check_health())
        click.echo(f"Health Status: {health_status}")
    except Exception as e:
        click.echo(f"Health check failed: {e}")
        sys.exit(1)

@cli.command()
@click.option('--extension', help='Specific extension to check')
@click.pass_context
def extensions(ctx, extension):
    """List available extensions."""
    config = ctx.obj['config']
    
    async def list_extensions():
        app = ContextenApp(config)
        await app.start()
        
        try:
            extensions_info = {}
            for ext_name in app.extension_registry._extensions:
                ext = app.extension_registry.get_extension(ext_name)
                if ext:
                    health = await ext.health_check()
                    extensions_info[ext_name] = {
                        "status": health.get("status", "unknown"),
                        "metadata": ext.metadata.__dict__
                    }
            
            return extensions_info
        finally:
            await app.stop()
    
    try:
        extensions_info = asyncio.run(list_extensions())
        
        if extension:
            if extension in extensions_info:
                click.echo(f"Extension: {extension}")
                click.echo(f"Status: {extensions_info[extension]['status']}")
                click.echo(f"Metadata: {extensions_info[extension]['metadata']}")
            else:
                click.echo(f"Extension '{extension}' not found")
        else:
            click.echo("Available Extensions:")
            for name, info in extensions_info.items():
                click.echo(f"  {name}: {info['status']}")
                
    except Exception as e:
        click.echo(f"Failed to list extensions: {e}")
        sys.exit(1)

@cli.command()
@click.option('--host', default='127.0.0.1', help='Dashboard host')
@click.option('--port', default=8000, help='Dashboard port')
@click.pass_context
def dashboard(ctx, host, port):
    """Start only the dashboard server."""
    config = ctx.obj['config']
    
    # Override dashboard config
    config['dashboard'] = {
        'host': host,
        'port': port,
        'frontend_path': config.get('dashboard', {}).get('frontend_path')
    }
    
    # Disable other extensions for dashboard-only mode
    config['github'] = {}
    config['linear'] = {}
    config['codegen'] = {}
    config['flows'] = {}
    
    logger.info(f"Starting dashboard server on http://{host}:{port}")
    
    runner = ContextenRunner(config)
    
    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        logger.info("Dashboard server stopped")
    except Exception as e:
        logger.error(f"Dashboard server failed: {e}", exc_info=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def config_example(ctx):
    """Generate example configuration file."""
    environment = ctx.obj['environment']
    config = get_config(environment)
    
    config_content = f"""# Contexten Configuration ({environment})
# Copy this file and modify the values according to your setup

import os

config = {repr(config)}
"""
    
    output_file = f"contexten_config_{environment}.py"
    with open(output_file, 'w') as f:
        f.write(config_content)
    
    click.echo(f"Example configuration written to: {output_file}")

def main():
    """Main entry point."""
    cli()

if __name__ == "__main__":
    main()

