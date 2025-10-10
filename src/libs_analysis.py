#!/usr/bin/env python3
"""External Static Analysis Tools Integration

This module provides integrations with external code analysis tools:
- Ruff: Fast Python linter
- MyPy: Static type checker
- Pylint: Code analysis
- Black/autopep8: Code formatters
- Other external linting and analysis tools

All functions return standardized error/warning formats for unified reporting.
"""

import logging
import subprocess
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LibAnalysisResult:
    """Standardized result from external tool analysis."""
    tool: str
    file_path: str
    line: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    code: str
    message: str
    fix_suggestion: Optional[str] = None


class ExternalToolsAnalyzer:
    """Unified interface for external static analysis tools."""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.available_tools = self._detect_available_tools()
        
    def _detect_available_tools(self) -> Dict[str, bool]:
        """Detect which external tools are available."""
        tools = {}
        for tool in ['ruff', 'mypy', 'pylint', 'black']:
            try:
                subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                tools[tool] = True
                logger.info(f"✓ {tool} available")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                tools[tool] = False
                logger.debug(f"✗ {tool} not available")
        return tools
    
    def run_ruff(self, file_path: Optional[str] = None) -> List[LibAnalysisResult]:
        """Run Ruff linter on file or directory."""
        if not self.available_tools.get('ruff'):
            return []
        
        target = file_path or str(self.workspace_path)
        try:
            result = subprocess.run(
                ['ruff', 'check', target, '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            results = []
            if result.stdout:
                ruff_output = json.loads(result.stdout)
                for issue in ruff_output:
                    results.append(LibAnalysisResult(
                        tool='ruff',
                        file_path=issue.get('filename', target),
                        line=issue.get('location', {}).get('row', 0),
                        column=issue.get('location', {}).get('column', 0),
                        severity='error' if issue.get('level') == 'error' else 'warning',
                        code=issue.get('code', 'RUFF'),
                        message=issue.get('message', ''),
                        fix_suggestion=issue.get('fix', {}).get('message')
                    ))
            return results
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.error(f"Ruff analysis failed: {e}")
            return []
    
    def run_mypy(self, file_path: Optional[str] = None) -> List[LibAnalysisResult]:
        """Run MyPy type checker."""
        if not self.available_tools.get('mypy'):
            return []
        
        target = file_path or str(self.workspace_path)
        try:
            result = subprocess.run(
                ['mypy', target, '--show-column-numbers', '--no-error-summary'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            results = []
            for line in result.stdout.splitlines():
                # Parse mypy output: file.py:line:col: severity: message
                if ':' in line:
                    parts = line.split(':', 4)
                    if len(parts) >= 4:
                        results.append(LibAnalysisResult(
                            tool='mypy',
                            file_path=parts[0],
                            line=int(parts[1]) if parts[1].isdigit() else 0,
                            column=int(parts[2]) if parts[2].isdigit() else 0,
                            severity='error',
                            code='type-check',
                            message=parts[3].strip() if len(parts) > 3 else ''
                        ))
            return results
            
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.error(f"MyPy analysis failed: {e}")
            return []
    
    def run_pylint(self, file_path: Optional[str] = None) -> List[LibAnalysisResult]:
        """Run Pylint code analysis."""
        if not self.available_tools.get('pylint'):
            return []
        
        target = file_path or str(self.workspace_path)
        try:
            result = subprocess.run(
                ['pylint', target, '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            results = []
            if result.stdout:
                pylint_output = json.loads(result.stdout)
                for issue in pylint_output:
                    results.append(LibAnalysisResult(
                        tool='pylint',
                        file_path=issue.get('path', target),
                        line=issue.get('line', 0),
                        column=issue.get('column', 0),
                        severity=issue.get('type', 'warning'),
                        code=issue.get('symbol', 'PYLINT'),
                        message=issue.get('message', '')
                    ))
            return results
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.error(f"Pylint analysis failed: {e}")
            return []
    
    def run_all_tools(self, file_path: Optional[str] = None) -> Dict[str, List[LibAnalysisResult]]:
        """Run all available static analysis tools."""
        return {
            'ruff': self.run_ruff(file_path),
            'mypy': self.run_mypy(file_path),
            'pylint': self.run_pylint(file_path)
        }
    
    def get_aggregated_results(self, file_path: Optional[str] = None) -> List[LibAnalysisResult]:
        """Get combined results from all tools."""
        all_results = self.run_all_tools(file_path)
        combined = []
        for tool_results in all_results.values():
            combined.extend(tool_results)
        return combined


def run_ruff_check(target_path: str) -> List[Dict[str, Any]]:
    """Standalone function to run Ruff check."""
    analyzer = ExternalToolsAnalyzer(target_path)
    results = analyzer.run_ruff()
    return [vars(r) for r in results]


def run_mypy_check(target_path: str) -> List[Dict[str, Any]]:
    """Standalone function to run MyPy check."""
    analyzer = ExternalToolsAnalyzer(target_path)
    results = analyzer.run_mypy()
    return [vars(r) for r in results]


def check_all_linters(target_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Run all available linters and return aggregated results."""
    analyzer = ExternalToolsAnalyzer(target_path)
    all_results = analyzer.run_all_tools()
    return {tool: [vars(r) for r in results] for tool, results in all_results.items()}
