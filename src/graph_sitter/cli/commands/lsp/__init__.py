"""
LSP commands for the CLI.
"""

from graph_sitter.cli.commands.lsp.lsp import lsp
from graph_sitter.cli.commands.lsp.diagnostics import diagnostics_command

__all__ = ["lsp", "diagnostics_command"]

