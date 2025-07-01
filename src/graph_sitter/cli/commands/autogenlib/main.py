"""Main CLI command group for autogenlib integration."""

import rich_click as click

from .generate import generate_command
from .config import config_command
from .stats import stats_command


@click.group(name="autogenlib")
def autogenlib_command():
    """Manage autogenlib integration for enhanced code generation."""
    pass


# Add subcommands
autogenlib_command.add_command(generate_command, name="generate")
autogenlib_command.add_command(config_command, name="config")
autogenlib_command.add_command(stats_command, name="stats")


if __name__ == "__main__":
    autogenlib_command()

