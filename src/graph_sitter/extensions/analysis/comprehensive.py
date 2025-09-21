#!/usr/bin/env python3
"""
Comprehensive Code Analysis Engine

Main analyzer that orchestrates all analysis tools and provides unified results.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Optional imports with graceful fallbacks
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Graph-sitter integration
try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.codebase.codebase_analysis import get_codebase_summary
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    Codebase = None

# Local imports
from .database import AnalysisError, ErrorDatabase
from .tools.ruff_integration import RuffIntegration
from .tools.traditional import TraditionalToolRunner
from .config import ConfigManager


@dataclass
class ToolConfig:
    """Configuration for a code analysis tool."""
    name: str
    command: str
    enabled: bool = True
    args: List[str] = field(default_factory=list)
    config_file: Optional[str] = None
    timeout: int = 300
    priority: int = 2  # 1=critical, 2=important, 3=optional
    requires_network: bool = False


class GraphSitterAnalysis:
    """Graph-sitter based code analysis wrapper."""

    def __init__(self, target_path: str):
        """Initialize graph-sitter analysis."""
        if not GRAPH_SITTER_AVAILABLE:
            raise ImportError(
                "graph-sitter not available. Install with: pip install graph-sitter"
            )

        self.target_path = target_path
        self.codebase = None
        self._initialize_codebase()

    def _initialize_codebase(self):
        """Initialize the graph-sitter codebase."""
        try:
            config = CodebaseConfig(
                method_usages=True,
                generics=True,
                sync_enabled=True,
                full_range_index=True,
                py_resolve_syspath=True,
                exp_lazy_graph=False,
            )
            self.codebase = Codebase(self.target_path, config=config)
        except Exception as e:
            logging.warning(f"Failed to initialize graph-sitter codebase: {e}")
            self.codebase = None

    def get_codebase_summary(self) -> Dict[str, Any]:
        """Get comprehensive codebase summary."""
        if not self.codebase:
            return {}

        try:
            return get_codebase_summary(self.codebase)
        except Exception as e:
            logging.warning(f"Failed to get codebase summary: {e}")
            return {
                "files": len(getattr(self.codebase, "files", [])),
                "functions": len(getattr(self.codebase, "functions", [])),
                "classes": len(getattr(self.codebase, "classes", [])),
                "imports": len(getattr(self.codebase, "imports", [])),
            }


class ComprehensiveAnalyzer:
    """Main analyzer that orchestrates all analysis tools."""

    # Core tool configuration - essential tools only for initial implementation
    DEFAULT_TOOLS = {
        "ruff": ToolConfig(
            "ruff",
            "ruff",
            args=[
                "check",
                "--output-format=json",
                "--select=E,W,F,I,N",  # Basic rules only initially
            ],
            timeout=180,
            priority=1,
        ),
        "mypy": ToolConfig(
            "mypy",
            "mypy",
            args=[
                "--show-error-codes",
                "--show-column-numbers",
                "--no-error-summary",
            ],
            timeout=300,
            priority=1,
        ),
        "pyflakes": ToolConfig("pyflakes", "pyflakes", timeout=60, priority=2),
        "pycodestyle": ToolConfig(
            "pycodestyle",
            "pycodestyle",
            args=["--statistics", "--count"],
            timeout=120,
            priority=3,
        ),
    }

    def __init__(
        self,
        target_path: str,
        config: Optional[Dict[str, Any]] = None,
        verbose: bool = False,
        profile: Optional[str] = None,
    ):
        self.target_path = target_path
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None

        # Initialize configuration manager
        self.config_manager = ConfigManager(target_path)
        if config:
            self.config_manager._merge_config(config)
        
        # Set profile if specified
        if profile:
            self.config_manager.config["analysis"]["profile"] = profile

        # Get active configuration
        self.profile_config = self.config_manager.get_profile_config()
        self.enabled_tools = self.config_manager.get_enabled_tools()
        
        # Initialize components
        self.graph_sitter = None
        self.ruff_integration = None
        self.error_db = ErrorDatabase()
        self.tool_runner = TraditionalToolRunner()

        # Results storage
        self.last_results = None

        self._initialize_components()

    def _initialize_components(self):
        """Initialize analysis components."""
        try:
            if GRAPH_SITTER_AVAILABLE:
                self.graph_sitter = GraphSitterAnalysis(self.target_path)
                if self.verbose:
                    print("✓ Graph-sitter initialized")
        except Exception as e:
            logging.warning(f"Graph-sitter initialization failed: {e}")

        try:
            self.ruff_integration = RuffIntegration(self.target_path)
            if self.verbose:
                print("✓ Ruff integration initialized")
        except Exception as e:
            logging.warning(f"Ruff integration failed: {e}")

    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Get tool configuration from config manager."""
        tool_config_dict = self.config_manager.get_tool_config(tool_name)
        if not tool_config_dict:
            return None
        
        return ToolConfig(
            name=tool_name,
            command=tool_config_dict.get("command", tool_name),
            enabled=tool_config_dict.get("enabled", True),
            args=tool_config_dict.get("args", []),
            config_file=tool_config_dict.get("config_file"),
            timeout=tool_config_dict.get("timeout", 300),
            priority=tool_config_dict.get("priority", 2),
            requires_network=tool_config_dict.get("requires_network", False)
        )

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis using all available tools and methods."""
        start_time = time.time()
        all_errors = []

        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    "Running comprehensive analysis...", total=None
                )

                # Graph-sitter analysis
                progress.update(task, description="Analyzing codebase structure...")
                graph_sitter_results = self._run_graph_sitter_analysis()

                # Ruff analysis
                progress.update(task, description="Running Ruff analysis...")
                ruff_errors = self._run_ruff_analysis()
                all_errors.extend(ruff_errors)

                # Traditional tools
                progress.update(task, description="Running traditional analysis tools...")
                tool_errors = self._run_traditional_tools()
                all_errors.extend(tool_errors)

                progress.update(task, description="Categorizing and processing errors...")
        else:
            print("Running comprehensive analysis...")
            graph_sitter_results = self._run_graph_sitter_analysis()
            ruff_errors = self._run_ruff_analysis()
            all_errors.extend(ruff_errors)
            tool_errors = self._run_traditional_tools()
            all_errors.extend(tool_errors)

        # Categorize errors
        categorized_errors = self._categorize_errors(all_errors)

        # Calculate metrics
        metrics = self._calculate_metrics(all_errors, graph_sitter_results)

        # Generate summary
        summary = self._generate_summary(all_errors, categorized_errors, metrics)

        end_time = time.time()

        results = {
            "metadata": {
                "target_path": self.target_path,
                "analysis_time": round(end_time - start_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "tools_used": self.enabled_tools,
                "profile": self.profile_config.get("name", "Unknown"),
                "graph_sitter_available": GRAPH_SITTER_AVAILABLE,
            },
            "summary": summary,
            "errors": [error.to_dict() for error in all_errors],
            "categorized_errors": categorized_errors,
            "graph_sitter_results": graph_sitter_results,
            "metrics": metrics,
            "quality_score": self._calculate_quality_score(all_errors, metrics),
        }

        # Store in database
        session_id = self.error_db.create_session(
            self.target_path, results["metadata"]["tools_used"], self.config_manager.config
        )
        self.error_db.store_errors(all_errors, session_id)
        self.error_db.update_session(session_id, len(all_errors))

        self.last_results = results
        return results

    def _run_graph_sitter_analysis(self) -> Dict[str, Any]:
        """Run graph-sitter analysis."""
        if not self.graph_sitter:
            return {}

        try:
            summary = self.graph_sitter.get_codebase_summary()
            return {"summary": summary}
        except Exception as e:
            logging.error(f"Graph-sitter analysis failed: {e}")
            return {}

    def _run_ruff_analysis(self) -> List[AnalysisError]:
        """Run Ruff analysis."""
        if not self.ruff_integration:
            return []

        try:
            return self.ruff_integration.run_analysis()
        except Exception as e:
            logging.error(f"Ruff analysis failed: {e}")
            return []

    def _run_traditional_tools(self) -> List[AnalysisError]:
        """Run traditional analysis tools."""
        errors = []

        # Get enabled tools from configuration
        enabled_tool_names = [name for name in self.enabled_tools if name != "ruff"]
        enabled_tools = []
        
        for tool_name in enabled_tool_names:
            tool_config = self.get_tool_config(tool_name)
            if tool_config and tool_config.enabled:
                enabled_tools.append((tool_name, tool_config))

        if not enabled_tools:
            return errors

        with ThreadPoolExecutor(max_workers=2) as executor:  # Limit concurrency initially
            future_to_tool = {
                executor.submit(self.tool_runner.run_tool, name, config, self.target_path): name
                for name, config in enabled_tools
            }

            for future in as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    tool_errors = future.result()
                    errors.extend(tool_errors)
                except Exception as e:
                    logging.error(f"Tool {tool_name} failed: {e}")

        return errors

    def _categorize_errors(self, errors: List[AnalysisError]) -> Dict[str, List[AnalysisError]]:
        """Categorize errors into comprehensive categories."""
        categories = {
            "syntax_critical": [],
            "type_critical": [],
            "logic_critical": [],
            "style_major": [],
            "import_issues": [],
            "general": [],
        }

        for error in errors:
            # Enhanced categorization based on error type and severity
            if error.severity == "ERROR":
                if "syntax" in error.error_type.lower() or "F" in error.error_type:
                    categories["syntax_critical"].append(error)
                elif "type" in error.error_type.lower() or error.tool_source in ["mypy"]:
                    categories["type_critical"].append(error)
                elif "import" in error.error_type.lower():
                    categories["import_issues"].append(error)
                else:
                    categories["logic_critical"].append(error)
            elif "style" in error.category or "format" in error.category:
                categories["style_major"].append(error)
            else:
                categories["general"].append(error)

        return categories

    def _calculate_metrics(self, errors: List[AnalysisError], graph_sitter_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive code metrics."""
        metrics = {
            "total_errors": len(errors),
            "error_density": 0,
            "by_severity": {
                "ERROR": len([e for e in errors if e.severity == "ERROR"]),
                "WARNING": len([e for e in errors if e.severity == "WARNING"]),
                "INFO": len([e for e in errors if e.severity == "INFO"]),
            },
            "by_tool": {
                tool: len([e for e in errors if e.tool_source == tool])
                for tool in set(e.tool_source for e in errors)
            },
        }

        # Error density calculation
        if graph_sitter_results.get("summary", {}).get("files", 0) > 0:
            metrics["error_density"] = len(errors) / graph_sitter_results["summary"]["files"]

        return metrics

    def _generate_summary(
        self,
        errors: List[AnalysisError],
        categorized_errors: Dict[str, List[AnalysisError]],
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive analysis summary."""
        return {
            "overview": {
                "total_errors": len(errors),
                "critical_errors": len(categorized_errors.get("syntax_critical", [])) +
                                 len(categorized_errors.get("type_critical", [])),
                "by_category": {cat: len(errs) for cat, errs in categorized_errors.items()},
            },
            "quality_metrics": metrics,
        }

    def _calculate_quality_score(self, errors: List[AnalysisError], metrics: Dict[str, Any]) -> float:
        """Calculate overall code quality score (0-100)."""
        if not errors:
            return 100.0

        # Base score
        score = 100.0

        # Deduct points for errors by severity
        for error in errors:
            if error.severity == "ERROR":
                score -= 5.0
            elif error.severity == "WARNING":
                score -= 2.0
            else:
                score -= 0.5

        return max(0.0, min(100.0, score))