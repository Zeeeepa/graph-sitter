"""Extensions for the codegen package."""

# Import serena path setup first
from graph_sitter.extensions._serena_path import *  # noqa: F403, F401

from graph_sitter.extensions.index.code_index import CodeIndex
from graph_sitter.extensions.index.file_index import FileIndex

__all__ = ["CodeIndex", "FileIndex"]
