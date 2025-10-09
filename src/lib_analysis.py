"""Tool integration library for static analysis.

Provides unified interface for ruff, mypy, pylint, and other analysis tools.
"""

import logging
import subprocess
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .analysis_utils import AnalysisError, ToolConfig, setup_logger
from .protocols import ToolIntegrationProtocol, AnalysisOrchestratorProtocol

logger = setup_logger(__name__)


class BaseToolAnalyzer(ABC):
    """Abstract base class for analysis tool integrations."""
    
    def __init__(self, config: Optional[ToolConfig] = None):
        """Initialize tool analyzer with configuration."""
        self.config = config or ToolConfig(name=self.get_tool_name(), command="")
        self._version_cache: Optional[str] = None
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        pass
    
    @abstractmethod
    def analyze(self, target_path: str) -> List[AnalysisError]:
        """Run analysis on target path."""
        pass
    
    def is_available(self) -> bool:
        """Check if tool is installed and available."""
        try:
            result = subprocess.run(
                [self.config.command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_version(self) -> str:
        """Get tool version string."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(
                [self.config.command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._version_cache = result.stdout.strip()
            return self._version_cache
        except Exception as e:
            logger.error(f"Error getting version for {self.get_tool_name()}: {e}")
            return "unknown"
    
    def supports_auto_fix(self) -> bool:
        """Check if tool supports automatic fixing."""
        return False
    
    def apply_fixes(self, errors: List[AnalysisError]) -> Dict[str, Any]:
        """Apply automatic fixes for fixable errors."""
        return {"applied": 0, "failed": 0, "message": "Auto-fix not supported"}


class RuffAnalyzer(BaseToolAnalyzer):
    """Ruff linter and formatter integration."""
    
    def __init__(self, config: Optional[ToolConfig] = None):
        if not config:
            config = ToolConfig(
                name="ruff",
                command="ruff",
                enabled=True,
                args=["check", "--output-format=json"],
                priority=1
            )
        super().__init__(config)
    
    def get_tool_name(self) -> str:
        return "ruff"
    
    def analyze(self, target_path: str) -> List[AnalysisError]:
        """Run ruff analysis on target."""
        if not self.is_available():
            logger.warning("Ruff not available")
            return []
        
        try:
            # Run ruff check
            cmd = [self.config.command] + self.config.args + [target_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            # Parse JSON output
            if result.stdout:
                ruff_errors = json.loads(result.stdout)
                return self._parse_ruff_output(ruff_errors)
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ruff output: {e}")
            return []
        except subprocess.TimeoutExpired:
            logger.error(f"Ruff timed out after {self.config.timeout}s")
            return []
        except Exception as e:
            logger.error(f"Ruff analysis failed: {e}")
            return []
    
    def _parse_ruff_output(self, ruff_errors: List[Dict]) -> List[AnalysisError]:
        """Parse ruff JSON output to AnalysisError objects."""
        errors = []
        
        for err in ruff_errors:
            error = AnalysisError(
                file_path=err.get("filename", ""),
                line=err.get("location", {}).get("row", 0),
                column=err.get("location", {}).get("column", 0),
                error_type=err.get("code", ""),
                severity=self._map_severity(err.get("code", "")),
                message=err.get("message", ""),
                tool_source="ruff",
                category=self._categorize_code(err.get("code", "")),
                fix_suggestion=err.get("fix", {}).get("message") if err.get("fix") else None
            )
            errors.append(error)
        
        return errors
    
    def _map_severity(self, code: str) -> str:
        """Map ruff error code to severity level."""
        if not code:
            return "info"
        
        prefix = code[0] if code else ""
        severity_map = {
            "E": "error",    # Error
            "W": "warning",  # Warning
            "F": "error",    # Pyflakes
            "C": "warning",  # Complexity
            "N": "info",     # Naming
            "D": "info",     # Docstring
            "I": "info",     # Import sorting
        }
        return severity_map.get(prefix, "info")
    
    def _categorize_code(self, code: str) -> str:
        """Categorize ruff error by code prefix."""
        if not code:
            return "general"
        
        prefix = code[0] if code else ""
        category_map = {
            "E": "style",
            "W": "style",
            "F": "error",
            "C": "complexity",
            "N": "naming",
            "D": "documentation",
            "I": "import",
        }
        return category_map.get(prefix, "general")
    
    def supports_auto_fix(self) -> bool:
        return True
    
    def apply_fixes(self, errors: List[AnalysisError]) -> Dict[str, Any]:
        """Apply ruff auto-fixes."""
        try:
            # Get unique file paths
            files = list(set(e.file_path for e in errors))
            
            applied = 0
            failed = 0
            
            for file_path in files:
                result = subprocess.run(
                    ["ruff", "check", "--fix", file_path],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    applied += 1
                else:
                    failed += 1
            
            return {
                "applied": applied,
                "failed": failed,
                "message": f"Fixed {applied} files, {failed} failed"
            }
            
        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return {"applied": 0, "failed": len(files), "message": str(e)}


class MypyAnalyzer(BaseToolAnalyzer):
    """Mypy type checker integration."""
    
    def __init__(self, config: Optional[ToolConfig] = None):
        if not config:
            config = ToolConfig(
                name="mypy",
                command="mypy",
                enabled=True,
                args=["--show-error-codes", "--no-error-summary"],
                priority=1
            )
        super().__init__(config)
    
    def get_tool_name(self) -> str:
        return "mypy"
    
    def analyze(self, target_path: str) -> List[AnalysisError]:
        """Run mypy type checking."""
        if not self.is_available():
            logger.warning("Mypy not available")
            return []
        
        try:
            cmd = [self.config.command] + self.config.args + [target_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            return self._parse_mypy_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Mypy timed out after {self.config.timeout}s")
            return []
        except Exception as e:
            logger.error(f"Mypy analysis failed: {e}")
            return []
    
    def _parse_mypy_output(self, output: str) -> List[AnalysisError]:
        """Parse mypy text output to AnalysisError objects."""
        errors = []
        
        for line in output.splitlines():
            if not line.strip():
                continue
            
            # Parse: file.py:10:5: error: Message  [error-code]
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            
            file_path = parts[0].strip()
            line_num = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
            col_num = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
            
            # Extract severity and message
            rest = parts[3].strip()
            severity = "error"
            if rest.startswith("error:"):
                severity = "error"
                message = rest[6:].strip()
            elif rest.startswith("warning:"):
                severity = "warning"
                message = rest[8:].strip()
            elif rest.startswith("note:"):
                severity = "info"
                message = rest[5:].strip()
            else:
                message = rest
            
            # Extract error code
            error_code = ""
            if "[" in message and "]" in message:
                start = message.rfind("[")
                end = message.rfind("]")
                error_code = message[start+1:end]
                message = message[:start].strip()
            
            error = AnalysisError(
                file_path=file_path,
                line=line_num,
                column=col_num,
                error_type=error_code or "type-check",
                severity=severity,
                message=message,
                tool_source="mypy",
                category="type_error"
            )
            errors.append(error)
        
        return errors


class PyRightAnalyzer(BaseToolAnalyzer):
    """PyRight type checker integration."""
    
    def __init__(self, config: Optional[ToolConfig] = None):
        if not config:
            config = ToolConfig(
                name="pyright",
                command="pyright",
                enabled=True,
                args=["--outputjson"],
                priority=1
            )
        super().__init__(config)
    
    def get_tool_name(self) -> str:
        return "pyright"
    
    def analyze(self, target_path: str) -> List[AnalysisError]:
        """Run pyright type checking."""
        if not self.is_available():
            logger.warning("PyRight not available")
            return []
        
        try:
            cmd = [self.config.command] + self.config.args + [target_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                return self._parse_pyright_output(data)
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pyright output: {e}")
            return []
        except subprocess.TimeoutExpired:
            logger.error(f"PyRight timed out after {self.config.timeout}s")
            return []
        except Exception as e:
            logger.error(f"PyRight analysis failed: {e}")
            return []
    
    def _parse_pyright_output(self, data: Dict) -> List[AnalysisError]:
        """Parse pyright JSON output."""
        errors = []
        
        for diag in data.get("generalDiagnostics", []):
            error = AnalysisError(
                file_path=diag.get("file", ""),
                line=diag.get("range", {}).get("start", {}).get("line", 0) + 1,
                column=diag.get("range", {}).get("start", {}).get("character", 0),
                error_type=diag.get("rule", "type-check"),
                severity=diag.get("severity", "error"),
                message=diag.get("message", ""),
                tool_source="pyright",
                category="type_error"
            )
            errors.append(error)
        
        return errors


class AnalysisOrchestrator:
    """Orchestrates multiple analysis tools."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.tools: Dict[str, BaseToolAnalyzer] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default analysis tools."""
        self.register_tool(RuffAnalyzer())
        self.register_tool(MypyAnalyzer())
        self.register_tool(PyRightAnalyzer())
    
    def register_tool(self, tool: BaseToolAnalyzer):
        """Register a new analysis tool."""
        self.tools[tool.get_tool_name()] = tool
        logger.info(f"Registered tool: {tool.get_tool_name()}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return [
            name for name, tool in self.tools.items()
            if tool.config.enabled and tool.is_available()
        ]
    
    def enable_tool(self, tool_name: str):
        """Enable a specific tool."""
        if tool_name in self.tools:
            self.tools[tool_name].config.enabled = True
    
    def disable_tool(self, tool_name: str):
        """Disable a specific tool."""
        if tool_name in self.tools:
            self.tools[tool_name].config.enabled = False
    
    def run_analysis(
        self,
        target_path: str,
        tools: Optional[List[str]] = None,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """Run analysis with selected tools."""
        import time
        start_time = time.time()
        
        # Determine which tools to run
        if tools:
            selected_tools = {
                name: tool for name, tool in self.tools.items()
                if name in tools and tool.config.enabled
            }
        else:
            selected_tools = {
                name: tool for name, tool in self.tools.items()
                if tool.config.enabled and tool.is_available()
            }
        
        if not selected_tools:
            logger.warning("No tools available for analysis")
            return {
                "errors": [],
                "statistics": {},
                "tool_results": {},
                "duration": 0.0
            }
        
        # Run tools
        all_errors = []
        tool_results = {}
        
        if parallel and len(selected_tools) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=len(selected_tools)) as executor:
                futures = {
                    executor.submit(tool.analyze, target_path): name
                    for name, tool in selected_tools.items()
                }
                
                for future in as_completed(futures):
                    tool_name = futures[future]
                    try:
                        errors = future.result()
                        tool_results[tool_name] = errors
                        all_errors.extend(errors)
                        logger.info(f"{tool_name}: Found {len(errors)} issues")
                    except Exception as e:
                        logger.error(f"{tool_name} failed: {e}")
                        tool_results[tool_name] = []
        else:
            # Sequential execution
            for name, tool in selected_tools.items():
                try:
                    errors = tool.analyze(target_path)
                    tool_results[name] = errors
                    all_errors.extend(errors)
                    logger.info(f"{name}: Found {len(errors)} issues")
                except Exception as e:
                    logger.error(f"{name} failed: {e}")
                    tool_results[name] = []
        
        # Calculate statistics
        statistics = self._calculate_statistics(all_errors)
        
        duration = time.time() - start_time
        
        return {
            "errors": all_errors,
            "statistics": statistics,
            "tool_results": {k: len(v) for k, v in tool_results.items()},
            "duration": duration
        }
    
    def _calculate_statistics(self, errors: List[AnalysisError]) -> Dict[str, Any]:
        """Calculate statistics from errors."""
        by_severity = {}
        by_category = {}
        by_file = {}
        by_tool = {}
        
        for error in errors:
            by_severity[error.severity] = by_severity.get(error.severity, 0) + 1
            by_category[error.category] = by_category.get(error.category, 0) + 1
            by_file[error.file_path] = by_file.get(error.file_path, 0) + 1
            by_tool[error.tool_source] = by_tool.get(error.tool_source, 0) + 1
        
        return {
            "total": len(errors),
            "by_severity": by_severity,
            "by_category": by_category,
            "by_file": dict(sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_tool": by_tool
        }
