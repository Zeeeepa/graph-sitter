#!/usr/bin/env python3
"""
Traditional Analysis Tools Runner

Runner for traditional Python analysis tools like mypy, pyflakes, pycodestyle, etc.
"""

import json
import logging
import os
import subprocess
from typing import List

from ..database import AnalysisError


class TraditionalToolRunner:
    """Runner for traditional analysis tools."""

    def run_tool(self, tool_name: str, tool_config, target_path: str) -> List[AnalysisError]:
        """Run a single analysis tool."""
        errors = []

        try:
            # Build command
            cmd = [tool_config.command] + tool_config.args + [target_path]

            # Run tool
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=tool_config.timeout,
                cwd=os.path.dirname(target_path) or ".",
            )

            # Parse output based on tool
            if tool_name == "mypy" and result.stdout:
                errors.extend(self._parse_mypy_output(result.stdout))
            elif tool_name == "pyflakes" and (result.stdout or result.stderr):
                errors.extend(self._parse_pyflakes_output(result.stdout or result.stderr))
            elif tool_name == "pycodestyle" and result.stdout:
                errors.extend(self._parse_pycodestyle_output(result.stdout))
            elif result.stdout or result.stderr:
                # Generic parsing for other tools
                errors.extend(self._parse_generic_output(tool_name, result))

        except subprocess.TimeoutExpired:
            logging.warning(f"Tool {tool_name} timed out")
        except Exception as e:
            logging.error(f"Tool {tool_name} failed: {e}")

        return errors

    def _parse_mypy_output(self, output: str) -> List[AnalysisError]:
        """Parse MyPy output."""
        errors = []
        
        # Parse text format
        for line in output.split("\n"):
            if ":" in line and ("error:" in line or "warning:" in line):
                parts = line.split(":")
                if len(parts) >= 4:
                    errors.append(
                        AnalysisError(
                            file_path=parts[0],
                            line=int(parts[1]) if parts[1].isdigit() else 0,
                            column=int(parts[2]) if parts[2].isdigit() else 0,
                            error_type="mypy-error",
                            severity="ERROR" if "error:" in line else "WARNING",
                            message=":".join(parts[3:]).strip(),
                            tool_source="mypy",
                            category="type_checking",
                            confidence=0.9,
                        )
                    )
        return errors

    def _parse_pyflakes_output(self, output: str) -> List[AnalysisError]:
        """Parse Pyflakes output."""
        errors = []
        
        for line in output.split("\n"):
            if ":" in line:
                parts = line.split(":")
                if len(parts) >= 3:
                    errors.append(
                        AnalysisError(
                            file_path=parts[0],
                            line=int(parts[1]) if parts[1].isdigit() else 0,
                            column=0,
                            error_type="pyflakes-error",
                            severity="WARNING",
                            message=":".join(parts[2:]).strip(),
                            tool_source="pyflakes",
                            category="logic_error",
                            confidence=0.8,
                        )
                    )
        return errors

    def _parse_pycodestyle_output(self, output: str) -> List[AnalysisError]:
        """Parse pycodestyle output."""
        errors = []
        
        for line in output.split("\n"):
            if ":" in line:
                parts = line.split(":")
                if len(parts) >= 4:
                    errors.append(
                        AnalysisError(
                            file_path=parts[0],
                            line=int(parts[1]) if parts[1].isdigit() else 0,
                            column=int(parts[2]) if parts[2].isdigit() else 0,
                            error_type=parts[3].strip().split()[0] if parts[3].strip() else "style-error",
                            severity="WARNING",
                            message=" ".join(parts[3].strip().split()[1:]) if parts[3].strip() else "Style issue",
                            tool_source="pycodestyle",
                            category="style_formatting",
                            confidence=0.7,
                        )
                    )
        return errors

    def _parse_generic_output(self, tool_name: str, result: subprocess.CompletedProcess) -> List[AnalysisError]:
        """Parse generic tool output."""
        errors = []

        # If tool failed or has output, create a generic error
        if result.returncode != 0 or result.stdout.strip() or result.stderr.strip():
            output = result.stdout or result.stderr

            # Try to extract file:line information
            for line in output.split("\n"):
                if ":" in line and any(
                    keyword in line.lower() for keyword in ["error", "warning", "issue"]
                ):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        errors.append(
                            AnalysisError(
                                file_path=parts[0] if os.path.exists(parts[0]) else "unknown",
                                line=int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                                column=0,
                                error_type=f"{tool_name}-issue",
                                severity="WARNING",
                                message=line.strip(),
                                tool_source=tool_name,
                                category="general",
                                confidence=0.7,
                            )
                        )

        return errors