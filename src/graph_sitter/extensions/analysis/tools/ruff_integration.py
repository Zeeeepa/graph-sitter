#!/usr/bin/env python3
"""
Ruff Integration for Comprehensive Analysis

Enhanced Ruff integration with comprehensive rule coverage and error categorization.
"""

import json
import logging
import subprocess
from typing import List

from ..database import AnalysisError


class RuffIntegration:
    """Enhanced Ruff integration for comprehensive error detection."""

    def __init__(self, target_path: str):
        self.target_path = target_path

    def run_analysis(self) -> List[AnalysisError]:
        """Run basic Ruff analysis with essential rules."""
        errors = []

        # Start with essential rule categories
        essential_categories = [
            ("E", "pycodestyle errors"),
            ("W", "pycodestyle warnings"), 
            ("F", "pyflakes"),
            ("I", "isort"),
            ("N", "pep8-naming"),
        ]

        for category, description in essential_categories:
            try:
                cmd = [
                    "ruff",
                    "check",
                    "--select",
                    category,
                    "--output-format",
                    "json",
                    "--no-cache",
                    self.target_path,
                ]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )

                if result.stdout:
                    try:
                        ruff_errors = json.loads(result.stdout)
                        for error in ruff_errors:
                            errors.append(
                                AnalysisError(
                                    file_path=error.get("filename", ""),
                                    line=error.get("location", {}).get("row", 0),
                                    column=error.get("location", {}).get("column", 0),
                                    error_type=error.get("code", ""),
                                    severity=self._map_ruff_severity(error.get("code", "")),
                                    message=error.get("message", ""),
                                    tool_source="ruff",
                                    category=self._categorize_ruff_error(error.get("code", "")),
                                    confidence=0.9,
                                )
                            )
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to parse Ruff JSON output for {category}")

            except subprocess.TimeoutExpired:
                logging.warning(f"Ruff analysis timed out for category {category}")
            except Exception as e:
                logging.warning(f"Ruff analysis failed for category {category}: {e}")

        return errors

    def run_comprehensive_analysis(self) -> List[AnalysisError]:
        """Run comprehensive Ruff analysis with all rule categories."""
        errors = []

        # All Ruff rule categories for comprehensive analysis
        rule_categories = [
            ("E", "pycodestyle errors"),
            ("W", "pycodestyle warnings"),
            ("F", "pyflakes"),
            ("C", "mccabe complexity"),
            ("I", "isort"),
            ("N", "pep8-naming"),
            ("D", "pydocstyle"),
            ("UP", "pyupgrade"),
            ("S", "flake8-bandit"),
            ("B", "flake8-bugbear"),
            ("A", "flake8-builtins"),
            ("COM", "flake8-commas"),
            ("C4", "flake8-comprehensions"),
            ("T20", "flake8-print"),
            ("SIM", "flake8-simplify"),
            ("ARG", "flake8-unused-arguments"),
            ("PTH", "flake8-use-pathlib"),
            ("RUF", "ruff-specific"),
        ]

        for category, description in rule_categories:
            try:
                cmd = [
                    "ruff",
                    "check",
                    "--select",
                    category,
                    "--output-format",
                    "json",
                    "--no-cache",
                    self.target_path,
                ]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )

                if result.stdout:
                    try:
                        ruff_errors = json.loads(result.stdout)
                        for error in ruff_errors:
                            errors.append(
                                AnalysisError(
                                    file_path=error.get("filename", ""),
                                    line=error.get("location", {}).get("row", 0),
                                    column=error.get("location", {}).get("column", 0),
                                    error_type=error.get("code", ""),
                                    severity=self._map_ruff_severity(error.get("code", "")),
                                    message=error.get("message", ""),
                                    tool_source="ruff",
                                    category=self._categorize_ruff_error(error.get("code", "")),
                                    confidence=0.9,
                                )
                            )
                    except json.JSONDecodeError:
                        pass

            except subprocess.TimeoutExpired:
                logging.warning(f"Ruff analysis timed out for category {category}")
            except Exception as e:
                logging.warning(f"Ruff analysis failed for category {category}: {e}")

        return errors

    def _map_ruff_severity(self, code: str) -> str:
        """Map Ruff error codes to severity levels."""
        if code.startswith(("E", "F")):
            return "ERROR"
        elif code.startswith(("W", "C", "N")):
            return "WARNING"
        elif code.startswith(("S", "B")):
            return "SECURITY"
        else:
            return "INFO"

    def _categorize_ruff_error(self, code: str) -> str:
        """Categorize Ruff errors by type."""
        category_map = {
            "E": "syntax_style",
            "W": "style_warning",
            "F": "logic_error",
            "C": "complexity",
            "I": "import_style",
            "N": "naming",
            "D": "documentation",
            "S": "security",
            "B": "bug_risk",
            "A": "builtin_shadow",
            "T": "debug_code",
            "UP": "modernization",
            "COM": "style_formatting",
            "C4": "comprehension",
            "SIM": "simplification",
            "ARG": "unused_argument",
            "PTH": "pathlib_usage",
            "RUF": "ruff_specific",
        }

        prefix = code.split("0")[0] if "0" in code else code[:1]
        return category_map.get(prefix, "general")