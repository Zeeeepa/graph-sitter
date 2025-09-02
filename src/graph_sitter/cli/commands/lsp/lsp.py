import logging

import click

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@click.group(name="lsp")
def lsp():
    """Language Server Protocol commands."""
    pass


@lsp.command(name="start")
def lsp_start():
    """Start the LSP server."""
    try:
        from graph_sitter.extensions.lsp.lsp import server
    except (ImportError, ModuleNotFoundError):
        logger.exception("LSP is not installed. Please install it with `uv tool install graph-sitter[lsp] --prerelease=allow`")
        return
    logging.basicConfig(level=logging.INFO)
    server.start_io()
