"""
Python Language Server implementation.

This module provides LSP integration for Python using pylsp (Python LSP Server).
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from graph_sitter.shared.logging.get_logger import get_logger
from .base import BaseLanguageServer
from ..protocol.lsp_types import (
    Diagnostic, CompletionItem, CompletionItemKind, Hover, SignatureHelp,
    Position, Range, DiagnosticSeverity, MarkupContent
)

logger = get_logger(__name__)


class PythonLanguageServer(BaseLanguageServer):
    """Python language server implementation using pylsp."""
    
    def __init__(self, workspace_path: str):
        super().__init__(workspace_path, "python")
        self.server_name = "pylsp"
        
    def get_server_command(self) -> List[str]:
        """Get the command to start the Python language server."""
        # Try different possible pylsp installations
        possible_commands = [
            ["pylsp"],
            ["python", "-m", "pylsp"],
            ["python3", "-m", "pylsp"],
            ["pyls"],  # Legacy python-language-server
        ]
        
        for command in possible_commands:
            if shutil.which(command[0]):
                return command
        
        logger.warning("No Python language server found. Install with: pip install python-lsp-server")
        return []
    
    def supports_file(self, file_path: str) -> bool:
        """Check if this server supports the given file."""
        return file_path.endswith('.py')
    
    def _get_mock_completions(self, file_path: str, line: int, character: int) -> List[CompletionItem]:
        """Enhanced Python-specific mock completions."""
        # In a real implementation, this would come from pylsp
        python_completions = [
            CompletionItem(
                label="def",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="Define a function",
                insert_text="def ${1:function_name}(${2:parameters}):\\n    ${3:pass}"
            ),
            CompletionItem(
                label="class",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="Define a class",
                insert_text="class ${1:ClassName}:\\n    ${2:pass}"
            ),
            CompletionItem(
                label="import",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="Import a module"
            ),
            CompletionItem(
                label="from",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="Import from a module"
            ),
            CompletionItem(
                label="if",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="Conditional statement",
                insert_text="if ${1:condition}:\\n    ${2:pass}"
            ),
            CompletionItem(
                label="for",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="For loop",
                insert_text="for ${1:item} in ${2:iterable}:\\n    ${3:pass}"
            ),
            CompletionItem(
                label="while",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="While loop",
                insert_text="while ${1:condition}:\\n    ${2:pass}"
            ),
            CompletionItem(
                label="try",
                kind=CompletionItemKind.KEYWORD,
                detail="Python keyword",
                documentation="Exception handling",
                insert_text="try:\\n    ${1:pass}\\nexcept ${2:Exception} as ${3:e}:\\n    ${4:pass}"
            ),
            CompletionItem(
                label="len",
                kind=CompletionItemKind.FUNCTION,
                detail="len(obj) -> int",
                documentation="Return the length of an object"
            ),
            CompletionItem(
                label="print",
                kind=CompletionItemKind.FUNCTION,
                detail="print(*args, **kwargs)",
                documentation="Print objects to the text stream file"
            ),
            CompletionItem(
                label="range",
                kind=CompletionItemKind.FUNCTION,
                detail="range(start, stop, step) -> range",
                documentation="Create a range object"
            ),
            CompletionItem(
                label="enumerate",
                kind=CompletionItemKind.FUNCTION,
                detail="enumerate(iterable, start=0) -> enumerate",
                documentation="Return an enumerate object"
            ),
            CompletionItem(
                label="zip",
                kind=CompletionItemKind.FUNCTION,
                detail="zip(*iterables) -> zip",
                documentation="Return a zip object"
            ),
            CompletionItem(
                label="list",
                kind=CompletionItemKind.CLASS,
                detail="list(iterable) -> list",
                documentation="Built-in mutable sequence"
            ),
            CompletionItem(
                label="dict",
                kind=CompletionItemKind.CLASS,
                detail="dict(**kwargs) -> dict",
                documentation="Built-in mapping type"
            ),
            CompletionItem(
                label="str",
                kind=CompletionItemKind.CLASS,
                detail="str(object) -> str",
                documentation="Built-in string type"
            ),
            CompletionItem(
                label="int",
                kind=CompletionItemKind.CLASS,
                detail="int(x) -> int",
                documentation="Built-in integer type"
            ),
            CompletionItem(
                label="float",
                kind=CompletionItemKind.CLASS,
                detail="float(x) -> float",
                documentation="Built-in floating point type"
            ),
            CompletionItem(
                label="bool",
                kind=CompletionItemKind.CLASS,
                detail="bool(x) -> bool",
                documentation="Built-in boolean type"
            )
        ]
        
        # Add context-specific completions based on file content
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Add import-specific completions
                if 'import' in content:
                    python_completions.extend([
                        CompletionItem(
                            label="os",
                            kind=CompletionItemKind.MODULE,
                            detail="Standard library module",
                            documentation="Operating system interface"
                        ),
                        CompletionItem(
                            label="sys",
                            kind=CompletionItemKind.MODULE,
                            detail="Standard library module",
                            documentation="System-specific parameters and functions"
                        ),
                        CompletionItem(
                            label="json",
                            kind=CompletionItemKind.MODULE,
                            detail="Standard library module",
                            documentation="JSON encoder and decoder"
                        ),
                        CompletionItem(
                            label="datetime",
                            kind=CompletionItemKind.MODULE,
                            detail="Standard library module",
                            documentation="Date and time handling"
                        ),
                        CompletionItem(
                            label="pathlib",
                            kind=CompletionItemKind.MODULE,
                            detail="Standard library module",
                            documentation="Object-oriented filesystem paths"
                        )
                    ])
                    
        except Exception as e:
            logger.debug(f"Error reading file for context completions: {e}")
        
        return python_completions
    
    def _get_mock_hover(self, file_path: str, line: int, character: int) -> Optional[Hover]:
        """Enhanced Python-specific mock hover."""
        # In a real implementation, this would come from pylsp
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if line < len(lines):
                        current_line = lines[line]
                        
                        # Simple heuristics for Python symbols
                        if 'def ' in current_line:
                            return Hover(
                                contents=MarkupContent(
                                    kind="markdown",
                                    value=f"**Python Function Definition**\\n\\n```python\\n{current_line.strip()}\\n```\\n\\nDefines a Python function."
                                )
                            )
                        elif 'class ' in current_line:
                            return Hover(
                                contents=MarkupContent(
                                    kind="markdown",
                                    value=f"**Python Class Definition**\\n\\n```python\\n{current_line.strip()}\\n```\\n\\nDefines a Python class."
                                )
                            )
                        elif 'import ' in current_line:
                            return Hover(
                                contents=MarkupContent(
                                    kind="markdown",
                                    value=f"**Python Import Statement**\\n\\n```python\\n{current_line.strip()}\\n```\\n\\nImports a Python module or package."
                                )
                            )
        except Exception as e:
            logger.debug(f"Error reading file for hover: {e}")
        
        return Hover(
            contents=MarkupContent(
                kind="markdown",
                value=f"**Python Symbol**\\n\\nFile: `{file_path}`\\nPosition: {line}:{character}\\n\\nPython language server hover information."
            )
        )
    
    def _get_mock_signature_help(self, file_path: str, line: int, character: int) -> Optional[SignatureHelp]:
        """Enhanced Python-specific mock signature help."""
        from ..protocol.lsp_types import SignatureHelp, SignatureInformation, ParameterInformation
        
        # Common Python function signatures
        python_signatures = [
            SignatureInformation(
                label="print(*values, sep=' ', end='\\n', file=sys.stdout, flush=False)",
                documentation="Print objects to the text stream file, separated by sep and followed by end.",
                parameters=[
                    ParameterInformation(
                        label="*values",
                        documentation="Objects to print"
                    ),
                    ParameterInformation(
                        label="sep=' '",
                        documentation="String inserted between values, default is space"
                    ),
                    ParameterInformation(
                        label="end='\\n'",
                        documentation="String appended after the last value, default is newline"
                    ),
                    ParameterInformation(
                        label="file=sys.stdout",
                        documentation="File object to write to, default is sys.stdout"
                    ),
                    ParameterInformation(
                        label="flush=False",
                        documentation="Whether to forcibly flush the stream"
                    )
                ]
            ),
            SignatureInformation(
                label="len(obj)",
                documentation="Return the length (the number of items) of an object.",
                parameters=[
                    ParameterInformation(
                        label="obj",
                        documentation="Object to get the length of"
                    )
                ]
            ),
            SignatureInformation(
                label="range(start, stop, step=1)",
                documentation="Create a sequence of numbers from start to stop by step.",
                parameters=[
                    ParameterInformation(
                        label="start",
                        documentation="Starting value of the sequence"
                    ),
                    ParameterInformation(
                        label="stop",
                        documentation="End value of the sequence (exclusive)"
                    ),
                    ParameterInformation(
                        label="step=1",
                        documentation="Step size of the sequence"
                    )
                ]
            )
        ]
        
        return SignatureHelp(
            signatures=python_signatures,
            active_signature=0,
            active_parameter=0
        )
    
    def _update_diagnostics_cache(self) -> None:
        """Update diagnostics cache with Python-specific diagnostics."""
        # In a real implementation, this would parse diagnostics from pylsp
        # For now, we'll do basic Python syntax checking
        
        try:
            for py_file in self.workspace_path.rglob("*.py"):
                if py_file.is_file():
                    diagnostics = self._check_python_syntax(str(py_file))
                    if diagnostics:
                        self._diagnostics_cache[str(py_file)] = diagnostics
                        
        except Exception as e:
            logger.error(f"Error updating Python diagnostics: {e}")
    
    def _check_python_syntax(self, file_path: str) -> List[Diagnostic]:
        """Basic Python syntax checking."""
        diagnostics = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to compile the Python code
            compile(content, file_path, 'exec')
            
        except SyntaxError as e:
            # Create diagnostic for syntax error
            line = (e.lineno or 1) - 1  # Convert to 0-based
            character = (e.offset or 1) - 1  # Convert to 0-based
            
            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=line, character=character),
                    end=Position(line=line, character=character + 1)
                ),
                message=f"Syntax Error: {e.msg}",
                severity=DiagnosticSeverity.ERROR,
                source="python-syntax"
            )
            diagnostics.append(diagnostic)
            
        except Exception as e:
            logger.debug(f"Error checking Python syntax for {file_path}: {e}")
        
        return diagnostics
    
    def get_status(self) -> Dict[str, Any]:
        """Get Python language server status."""
        status = super().get_status()
        status.update({
            'server_name': self.server_name,
            'python_files': len(list(self.workspace_path.rglob("*.py"))),
            'has_pylsp': bool(shutil.which("pylsp") or shutil.which("pyls"))
        })
        return status

