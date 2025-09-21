"""Solidlsp - Direct import compatibility module.

This module re-exports solidlsp functionality to allow:
    from solidlsp import SolidLanguageServer

"""

try:
    from graph_sitter.extensions.lsp.solidlsp import *  # noqa: F403, F401
except ImportError as e:
    if "serena" in str(e):
        raise ImportError(
            f"SolidLSP requires the 'serena' dependency which is not installed. "
            f"Original error: {e}"
        ) from e
    else:
        raise