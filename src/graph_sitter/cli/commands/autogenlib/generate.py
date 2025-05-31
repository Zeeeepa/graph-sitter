"""CLI command for generating code using autogenlib integration."""

import click
import json
from pathlib import Path
from typing import Optional

from graph_sitter.integrations.autogenlib import AutogenLibIntegration, AutogenLibConfig
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@click.command()
@click.option(
    "--module-name",
    "-m",
    required=True,
    help="Name of the module to generate (e.g., 'myproject.utils.helpers')"
)
@click.option(
    "--function-name",
    "-f",
    help="Specific function to generate within the module"
)
@click.option(
    "--description",
    "-d",
    required=True,
    help="Description of what to generate"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (if not specified, prints to stdout)"
)
@click.option(
    "--existing-code",
    "-e",
    type=click.Path(exists=True),
    help="Path to existing code file to extend"
)
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to autogenlib configuration file"
)
@click.option(
    "--template",
    "-t",
    type=click.Choice(["function", "class", "module", "test", "api_client", "data_model", "cli_command"]),
    help="Use a predefined template"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without actually generating"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output"
)
def generate_command(
    module_name: str,
    function_name: Optional[str],
    description: str,
    output: Optional[str],
    existing_code: Optional[str],
    config_file: Optional[str],
    template: Optional[str],
    dry_run: bool,
    verbose: bool
):
    """Generate code using autogenlib integration with graph-sitter context."""
    
    if verbose:
        logger.setLevel("DEBUG")
        
    try:
        # Load configuration
        config = AutogenLibConfig()
        if config_file:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                config = AutogenLibConfig(**config_data)
                
        # Initialize integration
        integration = AutogenLibIntegration(config)
        
        if not integration.is_enabled():
            click.echo("❌ AutogenLib integration is not enabled. Check your configuration.", err=True)
            return
            
        # Validate configuration
        validation = integration.validate_configuration()
        if not validation["valid"]:
            click.echo("❌ Configuration validation failed:", err=True)
            for error in validation["errors"]:
                click.echo(f"  - {error}", err=True)
            return
            
        if validation["warnings"]:
            for warning in validation["warnings"]:
                click.echo(f"⚠️  {warning}")
                
        # Load existing code if specified
        existing_code_content = None
        if existing_code:
            with open(existing_code, 'r') as f:
                existing_code_content = f.read()
                
        if dry_run:
            click.echo("🔍 Dry run mode - showing what would be generated:")
            click.echo(f"Module: {module_name}")
            if function_name:
                click.echo(f"Function: {function_name}")
            click.echo(f"Description: {description}")
            if template:
                click.echo(f"Template: {template}")
            if existing_code_content:
                click.echo(f"Extending existing code ({len(existing_code_content)} characters)")
            return
            
        click.echo("🚀 Generating code...")
        
        # Generate code
        if template:
            # Use template generation
            parameters = {
                "module_name": module_name,
                "function_name": function_name,
                "description": description
            }
            result = integration.generate_template_code(template, parameters)
        else:
            # Use direct generation
            result = integration.generate_missing_implementation(
                module_name=module_name,
                function_name=function_name,
                description=description,
                existing_code=existing_code_content
            )
            
        if result.success:
            click.echo("✅ Code generation successful!")
            
            if verbose:
                click.echo(f"Generation time: {result.generation_time:.2f}s")
                if result.metadata:
                    click.echo(f"Metadata: {json.dumps(result.metadata, indent=2)}")
                    
            # Output the generated code
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(result.code)
                click.echo(f"📝 Code written to: {output_path}")
            else:
                click.echo("\n" + "="*50)
                click.echo("Generated Code:")
                click.echo("="*50)
                click.echo(result.code)
                click.echo("="*50)
                
        else:
            click.echo(f"❌ Code generation failed: {result.error}", err=True)
            if verbose and result.context_used:
                click.echo(f"Context used: {json.dumps(result.context_used, indent=2)}")
                
    except Exception as e:
        logger.error(f"Error in generate command: {e}", exc_info=True)
        click.echo(f"❌ Unexpected error: {e}", err=True)


if __name__ == "__main__":
    generate_command()

