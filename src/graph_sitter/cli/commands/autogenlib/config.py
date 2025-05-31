"""CLI command for managing autogenlib configuration."""

import click
import json
import os
from pathlib import Path
from typing import Optional

from graph_sitter.integrations.autogenlib import AutogenLibConfig
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@click.group()
def config_command():
    """Manage autogenlib integration configuration."""
    pass


@config_command.command("show")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(),
    help="Path to configuration file"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format"
)
def show_config(config_file: Optional[str], format: str):
    """Show current autogenlib configuration."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        if format == "json":
            click.echo(json.dumps(config.dict(), indent=2))
        elif format == "yaml":
            import yaml
            click.echo(yaml.dump(config.dict(), default_flow_style=False))
        else:
            # Table format
            click.echo("AutogenLib Configuration:")
            click.echo("=" * 40)
            
            # Core settings
            click.echo("Core Settings:")
            click.echo(f"  Enabled: {config.enabled}")
            click.echo(f"  OpenAI Model: {config.openai_model}")
            click.echo(f"  API Key Set: {'Yes' if config.openai_api_key else 'No'}")
            if config.openai_api_base_url:
                click.echo(f"  API Base URL: {config.openai_api_base_url}")
                
            # Caching settings
            click.echo("\nCaching Settings:")
            click.echo(f"  Enable Caching: {config.enable_caching}")
            if config.cache_directory:
                click.echo(f"  Cache Directory: {config.cache_directory}")
                
            # Integration settings
            click.echo("\nGraph-Sitter Integration:")
            click.echo(f"  Use Graph-Sitter Context: {config.use_graph_sitter_context}")
            click.echo(f"  Max Context Size: {config.max_context_size}")
            click.echo(f"  Include AST Analysis: {config.include_ast_analysis}")
            click.echo(f"  Include Symbol Table: {config.include_symbol_table}")
            
            # Generation settings
            click.echo("\nGeneration Settings:")
            click.echo(f"  Temperature: {config.temperature}")
            if config.max_tokens:
                click.echo(f"  Max Tokens: {config.max_tokens}")
                
            # Security settings
            click.echo("\nSecurity Settings:")
            click.echo(f"  Allowed Namespaces: {', '.join(config.allowed_namespaces)}")
            
    except Exception as e:
        logger.error(f"Error showing config: {e}", exc_info=True)
        click.echo(f"❌ Error showing configuration: {e}", err=True)


@config_command.command("init")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(),
    default="autogenlib_config.json",
    help="Path to create configuration file"
)
@click.option(
    "--openai-api-key",
    help="OpenAI API key"
)
@click.option(
    "--openai-model",
    default="gpt-4",
    help="OpenAI model to use"
)
@click.option(
    "--enable-caching/--disable-caching",
    default=True,
    help="Enable or disable caching"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive configuration setup"
)
def init_config(
    config_file: str,
    openai_api_key: Optional[str],
    openai_model: str,
    enable_caching: bool,
    interactive: bool
):
    """Initialize autogenlib configuration."""
    
    try:
        config_data = {}
        
        if interactive:
            click.echo("🔧 Interactive AutogenLib Configuration Setup")
            click.echo("=" * 50)
            
            # Core settings
            config_data["enabled"] = click.confirm("Enable autogenlib integration?", default=True)
            
            if config_data["enabled"]:
                api_key = click.prompt(
                    "OpenAI API Key",
                    default=os.environ.get("OPENAI_API_KEY", ""),
                    hide_input=True,
                    show_default=False
                )
                if api_key:
                    config_data["openai_api_key"] = api_key
                    
                config_data["openai_model"] = click.prompt(
                    "OpenAI Model",
                    default="gpt-4"
                )
                
                base_url = click.prompt(
                    "OpenAI API Base URL (optional)",
                    default="",
                    show_default=False
                )
                if base_url:
                    config_data["openai_api_base_url"] = base_url
                    
                # Caching settings
                config_data["enable_caching"] = click.confirm(
                    "Enable caching?",
                    default=True
                )
                
                # Integration settings
                config_data["use_graph_sitter_context"] = click.confirm(
                    "Use graph-sitter for enhanced context?",
                    default=True
                )
                
                config_data["max_context_size"] = click.prompt(
                    "Maximum context size (characters)",
                    type=int,
                    default=10000
                )
                
                # Generation settings
                config_data["temperature"] = click.prompt(
                    "Generation temperature (0.0-1.0)",
                    type=float,
                    default=0.1
                )
                
                # Security settings
                namespaces = click.prompt(
                    "Allowed namespaces (comma-separated)",
                    default="autogenlib.generated"
                )
                config_data["allowed_namespaces"] = [ns.strip() for ns in namespaces.split(",")]
                
        else:
            # Non-interactive setup
            config_data = {
                "enabled": True,
                "openai_model": openai_model,
                "enable_caching": enable_caching,
                "use_graph_sitter_context": True,
                "max_context_size": 10000,
                "temperature": 0.1,
                "allowed_namespaces": ["autogenlib.generated"]
            }
            
            if openai_api_key:
                config_data["openai_api_key"] = openai_api_key
                
        # Create configuration file
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        click.echo(f"✅ Configuration saved to: {config_path}")
        
        # Validate the configuration
        config = AutogenLibConfig(**config_data)
        validation = config.dict()  # This will validate the config
        
        click.echo("✅ Configuration validated successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing config: {e}", exc_info=True)
        click.echo(f"❌ Error initializing configuration: {e}", err=True)


@config_command.command("validate")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file to validate"
)
def validate_config(config_file: Optional[str]):
    """Validate autogenlib configuration."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Create integration to validate
        from graph_sitter.integrations.autogenlib import AutogenLibIntegration
        integration = AutogenLibIntegration(config)
        
        validation = integration.validate_configuration()
        
        if validation["valid"]:
            click.echo("✅ Configuration is valid!")
        else:
            click.echo("❌ Configuration validation failed:")
            for error in validation["errors"]:
                click.echo(f"  - {error}")
                
        if validation["warnings"]:
            click.echo("\n⚠️  Warnings:")
            for warning in validation["warnings"]:
                click.echo(f"  - {warning}")
                
    except Exception as e:
        logger.error(f"Error validating config: {e}", exc_info=True)
        click.echo(f"❌ Error validating configuration: {e}", err=True)


@config_command.command("test")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
def test_config(config_file: Optional[str]):
    """Test autogenlib configuration with a simple generation."""
    
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Create integration
        from graph_sitter.integrations.autogenlib import AutogenLibIntegration
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            click.echo("❌ AutogenLib integration is not enabled")
            return
            
        click.echo("🧪 Testing configuration with simple generation...")
        
        # Test with a simple function generation
        result = integration.generate_missing_implementation(
            module_name="autogenlib.test.hello",
            function_name="say_hello",
            description="Create a simple function that returns 'Hello, World!'"
        )
        
        if result.success:
            click.echo("✅ Test generation successful!")
            click.echo(f"Generation time: {result.generation_time:.2f}s")
            click.echo("\nGenerated code preview:")
            click.echo("-" * 30)
            # Show first few lines
            lines = result.code.split('\n')[:10]
            for line in lines:
                click.echo(line)
            if len(result.code.split('\n')) > 10:
                click.echo("...")
        else:
            click.echo(f"❌ Test generation failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Error testing config: {e}", exc_info=True)
        click.echo(f"❌ Error testing configuration: {e}", err=True)


if __name__ == "__main__":
    config_command()

