#!/usr/bin/env python3
"""
Main CLI entry point for graph-sitter.

This module provides the main command-line interface that integrates
all graph-sitter functionality including the gscli generation commands.
"""

import click
from rich.console import Console
from rich.traceback import install

# Install rich traceback for better error display
install(show_locals=True)

console = Console()

# Import command groups
from graph_sitter.gscli.cli import main as gscli_main


@click.group()
@click.version_option()
def main() -> None:
    """
    Graph-sitter: Scriptable interface to a powerful, multi-lingual language server.
    
    A comprehensive toolkit for code analysis, manipulation, and generation
    built on top of Tree-sitter.
    """
    pass


# Add the gscli command group as a subcommand
main.add_command(gscli_main, name="generate")


# Add other command groups here as they become available
# Example:
# from graph_sitter.cli.commands.analyze import analyze
# main.add_command(analyze)


if __name__ == "__main__":
    main()

