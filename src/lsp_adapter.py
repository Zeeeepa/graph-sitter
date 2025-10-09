"""LSP Adapter for diagnostic retrieval from Language Server Protocol servers.

Integrates functionality from src/graph_sitter/extensions/lsp/solidlsp/
Provides unified interface for retrieving diagnostics from:
- Pyright (type checking)
- Pylsp (Python language server)
- Ruff-lsp (linting and formatting)
"""

import logging
import subprocess
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from .analysis_utils import AnalysisError, setup_logger

logger = setup_logger(__name__)


@dataclass
class LSPDiagnostic:
    """Represents a diagnostic from an LSP server."""
    file_path: str
    line: int
    column: int
    end_line: int
    end_column: int
    severity: str  # "error", "warning", "information", "hint"
    message: str
    code: Optional[str] = None
    source: str = "lsp"  # Which LSP server reported this
    
    def to_analysis_error(self) -> AnalysisError:
        """Convert to AnalysisError format."""
        return AnalysisError(
            file_path=self.file_path,
            line=self.line,
            column=self.column,
            error_type=self.code or "diagnostic",
            severity=self.severity,
            message=self.message,
            tool_source=f"lsp-{self.source}"
        )


class LSPAdapter:
    """Adapter for interacting with Language Server Protocol servers.
    
    Integrated from extensions/lsp/solidlsp/ with focus on diagnostic retrieval.
    """
    
    def __init__(self, codebase_path: str):
        """Initialize LSP adapter.
        
        Args:
            codebase_path: Path to the codebase to analyze
        """
        self.codebase_path = Path(codebase_path)
        self.diagnostics_cache: Dict[str, List[LSPDiagnostic]] = {}
        logger.info(f"Initialized LSPAdapter for {codebase_path}")
    
    def get_pyright_diagnostics(
        self,
        file_path: Optional[str] = None
    ) -> List[LSPDiagnostic]:
        """Get diagnostics from Pyright type checker.
        
        Args:
            file_path: Specific file to check (or None for all files)
            
        Returns:
            List of LSPDiagnostic objects
        """
        try:
            # Build pyright command
            cmd = ["pyright", "--outputjson"]
            if file_path:
                cmd.append(str(file_path))
            else:
                cmd.append(str(self.codebase_path))
            
            # Run pyright
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.codebase_path),
                timeout=60
            )
            
            # Parse JSON output
            if result.stdout:
                data = json.loads(result.stdout)
                diagnostics = []
                
                for general_diag in data.get("generalDiagnostics", []):
                    file = general_diag.get("file", "")
                    range_data = general_diag.get("range", {})
                    start = range_data.get("start", {})
                    end = range_data.get("end", {})
                    
                    diagnostic = LSPDiagnostic(
                        file_path=file,
                        line=start.get("line", 0) + 1,  # LSP is 0-indexed
                        column=start.get("character", 0) + 1,
                        end_line=end.get("line", 0) + 1,
                        end_column=end.get("character", 0) + 1,
                        severity=general_diag.get("severity", "error").lower(),
                        message=general_diag.get("message", ""),
                        code=general_diag.get("rule", None),
                        source="pyright"
                    )
                    diagnostics.append(diagnostic)
                
                logger.info(f"Pyright found {len(diagnostics)} diagnostics")
                return diagnostics
            
            return []
            
        except subprocess.TimeoutExpired:
            logger.warning("Pyright timed out")
            return []
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            logger.error(f"Error running pyright: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_pyright_diagnostics: {e}")
            return []
    
    def get_mypy_diagnostics(
        self,
        file_path: Optional[str] = None
    ) -> List[LSPDiagnostic]:
        """Get diagnostics from mypy type checker.
        
        Args:
            file_path: Specific file to check (or None for all files)
            
        Returns:
            List of LSPDiagnostic objects
        """
        try:
            # Build mypy command
            cmd = ["mypy", "--show-error-codes", "--no-error-summary"]
            if file_path:
                cmd.append(str(file_path))
            else:
                cmd.append(str(self.codebase_path))
            
            # Run mypy
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.codebase_path),
                timeout=60
            )
            
            diagnostics = []
            
            # Parse mypy output (line-by-line format)
            for line in result.stdout.splitlines():
                # Format: file.py:line:col: severity: message [error-code]
                if ":" not in line:
                    continue
                
                parts = line.split(":", 4)
                if len(parts) < 4:
                    continue
                
                file_path_str, line_str, col_str, rest = parts[0], parts[1], parts[2], ":".join(parts[3:])
                
                # Extract severity and message
                if " error:" in rest:
                    severity = "error"
                    message = rest.split(" error:", 1)[1].strip()
                elif " warning:" in rest:
                    severity = "warning"
                    message = rest.split(" warning:", 1)[1].strip()
                elif " note:" in rest:
                    severity = "information"
                    message = rest.split(" note:", 1)[1].strip()
                else:
                    continue
                
                # Extract error code if present
                code = None
                if "[" in message and "]" in message:
                    code_match = message[message.rfind("[") + 1:message.rfind("]")]
                    code = code_match
                    message = message[:message.rfind("[")].strip()
                
                try:
                    diagnostic = LSPDiagnostic(
                        file_path=file_path_str,
                        line=int(line_str),
                        column=int(col_str) if col_str.isdigit() else 1,
                        end_line=int(line_str),
                        end_column=int(col_str) + 1 if col_str.isdigit() else 2,
                        severity=severity,
                        message=message,
                        code=code,
                        source="mypy"
                    )
                    diagnostics.append(diagnostic)
                except ValueError:
                    continue
            
            logger.info(f"Mypy found {len(diagnostics)} diagnostics")
            return diagnostics
            
        except subprocess.TimeoutExpired:
            logger.warning("Mypy timed out")
            return []
        except subprocess.SubprocessError as e:
            logger.error(f"Error running mypy: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_mypy_diagnostics: {e}")
            return []
    
    def get_all_diagnostics(
        self,
        file_path: Optional[str] = None,
        include_pyright: bool = True,
        include_mypy: bool = True
    ) -> List[LSPDiagnostic]:
        """Get diagnostics from all configured LSP servers.
        
        Args:
            file_path: Specific file to check (or None for all files)
            include_pyright: Whether to include Pyright diagnostics
            include_mypy: Whether to include mypy diagnostics
            
        Returns:
            Combined list of LSPDiagnostic objects
        """
        all_diagnostics = []
        
        if include_pyright:
            pyright_diags = self.get_pyright_diagnostics(file_path)
            all_diagnostics.extend(pyright_diags)
        
        if include_mypy:
            mypy_diags = self.get_mypy_diagnostics(file_path)
            all_diagnostics.extend(mypy_diags)
        
        # Cache diagnostics
        cache_key = file_path or "all"
        self.diagnostics_cache[cache_key] = all_diagnostics
        
        logger.info(f"Total diagnostics from LSP servers: {len(all_diagnostics)}")
        return all_diagnostics
    
    def get_diagnostics_by_severity(
        self,
        severity: str,
        file_path: Optional[str] = None
    ) -> List[LSPDiagnostic]:
        """Get diagnostics filtered by severity.
        
        Args:
            severity: "error", "warning", "information", or "hint"
            file_path: Optional file path to filter by
            
        Returns:
            Filtered list of diagnostics
        """
        all_diags = self.get_all_diagnostics(file_path)
        return [d for d in all_diags if d.severity == severity]
    
    def get_errors_only(
        self,
        file_path: Optional[str] = None
    ) -> List[LSPDiagnostic]:
        """Get only error-level diagnostics.
        
        Args:
            file_path: Optional file path to filter by
            
        Returns:
            List of error diagnostics
        """
        return self.get_diagnostics_by_severity("error", file_path)
    
    def convert_to_analysis_errors(
        self,
        diagnostics: Optional[List[LSPDiagnostic]] = None
    ) -> List[AnalysisError]:
        """Convert LSP diagnostics to AnalysisError format.
        
        Args:
            diagnostics: List of diagnostics (or None to use all cached)
            
        Returns:
            List of AnalysisError objects
        """
        if diagnostics is None:
            diagnostics = []
            for diag_list in self.diagnostics_cache.values():
                diagnostics.extend(diag_list)
        
        return [diag.to_analysis_error() for diag in diagnostics]
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """Get a summary of all diagnostics.
        
        Returns:
            Dictionary with diagnostic statistics
        """
        all_diags = []
        for diag_list in self.diagnostics_cache.values():
            all_diags.extend(diag_list)
        
        by_severity = {}
        by_source = {}
        by_file = {}
        
        for diag in all_diags:
            # By severity
            by_severity[diag.severity] = by_severity.get(diag.severity, 0) + 1
            # By source
            by_source[diag.source] = by_source.get(diag.source, 0) + 1
            # By file
            by_file[diag.file_path] = by_file.get(diag.file_path, 0) + 1
        
        return {
            "total": len(all_diags),
            "by_severity": by_severity,
            "by_source": by_source,
            "by_file": by_file,
            "top_files": sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def clear_cache(self):
        """Clear the diagnostics cache."""
        self.diagnostics_cache.clear()
        logger.info("Diagnostics cache cleared")

