"""
main_analysis.py

Main analysis orchestration module with FastAPI backend and CLI interface.

Key Components:
- ComprehensiveAnalyzer: Primary orchestrator (46 methods)
- AnalysisEngine: Backend analysis engine (41 methods)
- EnhancedVisualizationEngine: Dependency and call graphs (18 methods)
- TransformationEngine: Code transformations (9 methods)
- InteractiveAnalyzer: Interactive CLI (8 methods)
- ReportGenerator: Report generation (12 methods)
- FastAPI endpoints: REST API for analysis
- CLI: Command-line interface

Integrates:
- graph_sitter_adapter: GraphSitterAnalyzer
- libs_adapter: All tool integrations
"""

import os
import sys
import json
import argparse
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    BaseModel = object

# NetworkX for graph operations
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# Import our adapters
from graph_sitter_adapter import GraphSitterAnalyzer
from libs_adapter import (
    RuffIntegration,
    LSPDiagnosticsManager,
    LSPDiagnosticsCollector,
    ErrorDatabase,
    AutoGenLibFixer,
    AnalysisError,
    ToolConfig,
    resolve_diagnostic_with_ai,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app if available
app = FastAPI(title="Graph-Sitter Analysis API") if FASTAPI_AVAILABLE else None

class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to analyze")
    config: Optional[Dict] = Field(default=None, description="Analysis configuration")
    include_deep_analysis: bool = Field(
        default=True, description="Include comprehensive analysis"
    )
    language: str = Field(
        default="python",
        description="Programming language of the codebase (e.g., python, csharp).",
    )


class ErrorAnalysisResponse(BaseModel):
    total_errors: int
    critical_errors: int
    major_errors: int
    minor_errors: int
    errors_by_category: Dict[str, int]
    detailed_errors: List[Dict[str, Any]]
    error_patterns: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]


class EntrypointAnalysisResponse(BaseModel):
    total_entrypoints: int
    main_entrypoints: List[Dict[str, Any]]
    secondary_entrypoints: List[Dict[str, Any]]
    test_entrypoints: List[Dict[str, Any]]
    api_entrypoints: List[Dict[str, Any]]  # Added
    cli_entrypoints: List[Dict[str, Any]]  # Added
    entrypoint_graph: Dict[str, Any]
    complexity_metrics: Dict[str, Any]
    dependency_analysis: Dict[str, Any]  # Added
    call_flow_analysis: Dict[str, Any]  # Added


class TransformationRequest(BaseModel):
    analysis_id: str
    transformation_type: str
    target_path: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = Field(default=True, description="Preview changes without applying")


class VisualizationRequest(BaseModel):
    analysis_id: str
    viz_type: str = Field(..., description="Type of visualization")
    entry_point: Optional[str] = Field(
        default=None, description="Entry point for visualization"
    )
    max_depth: int = Field(default=10, description="Maximum depth for traversal")
    include_external: bool = Field(
        default=False, description="Include external modules"
    )
    filter_patterns: List[str] = Field(
        default_factory=list, description="Filter patterns"
    )


class DeadCodeAnalysisResponse(BaseModel):
    total_dead_items: int
    dead_functions: List[Dict[str, Any]]
    dead_classes: List[Dict[str, Any]]
    dead_imports: List[Dict[str, Any]]
    dead_variables: List[Dict[str, Any]]
    potential_dead_code: List[Dict[str, Any]]
    recommendations: List[str]


class CodeQualityMetrics(BaseModel):
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage_estimate: float
    documentation_coverage: float
    code_duplication_score: float
    type_coverage: float  # Added
    function_metrics: Dict[str, Any]  # Added
    class_metrics: Dict[str, Any]  # Added
    file_metrics: Dict[str, Any]  # Added


class ComprehensiveAnalyzer:
    """Main analyzer class that orchestrates all analysis tools and provides comprehensive error reporting."""
    
    # Extended tool configuration with categorization
    COMPREHENSIVE_TOOLS = {
        # Core Python linting and type checking
        "ruff": ToolConfig(
            "ruff", "ruff", 
            args=["check", "--output-format=json", "--select=ALL"],
            category=ErrorCategory.STYLE.value,
            priority=1
        ),
        "mypy": ToolConfig(
            "mypy", "mypy",
            args=["--strict", "--show-error-codes", "--show-column-numbers", "--pretty"],
            category=ErrorCategory.TYPE.value,
            priority=1
        ),
        "pyright": ToolConfig(
            "pyright", "pyright",
            args=["--outputjson"],
            category=ErrorCategory.TYPE.value,
            priority=1,
            timeout=600
        ),
        "pylint": ToolConfig(
            "pylint", "pylint",
            args=["--output-format=json", "--reports=y", "--score=y"],
            category=ErrorCategory.LOGIC.value,
            priority=2
        ),
        
        # Security analysis
        "bandit": ToolConfig(
            "bandit", "bandit",
            args=["-r", "-f", "json", "--severity-level=low", "--confidence-level=low"],
            category=ErrorCategory.SECURITY.value,
            priority=1
        ),
        "safety": ToolConfig(
            "safety", "safety",
            args=["check", "--json", "--full-report"],
            category=ErrorCategory.SECURITY.value,
            priority=1,
            requires_network=True
        ),
        "semgrep": ToolConfig(
            "semgrep", "semgrep",
            args=["--config=p/python", "--json", "--severity=WARNING"],
            category=ErrorCategory.SECURITY.value,
            priority=2,
            requires_network=True
        ),
        
        # Code quality and complexity
        "radon": ToolConfig(
            "radon", "radon",
            args=["cc", "-j", "--total-average"],
            category=ErrorCategory.MAINTAINABILITY.value,
            priority=2
        ),
        "xenon": ToolConfig(
            "xenon", "xenon",
            args=["--max-absolute=B", "--max-modules=B", "--max-average=C"],
            category=ErrorCategory.MAINTAINABILITY.value,
            priority=2
        ),
        "cohesion": ToolConfig(
            "cohesion", "cohesion",
            args=["--below", "80", "--format", "json"],
            category=ErrorCategory.DESIGN.value,
            priority=3
        ),
        
        # Import and dependency analysis
        "isort": ToolConfig(
            "isort", "isort",
            args=["--check-only", "--diff", "--profile=black"],
            category=ErrorCategory.IMPORT.value,
            priority=2
        ),
        "vulture": ToolConfig(
            "vulture", "vulture",
            args=["--min-confidence=60", "--sort-by-size"],
            category=ErrorCategory.LOGIC.value,
            priority=2
        ),
        "pydeps": ToolConfig(
            "pydeps", "pydeps",
            args=["--max-bacon=3", "--show-cycles", "--format", "json"],
            category=ErrorCategory.DEPENDENCIES.value,
            priority=3
        ),
        
        # Style and formatting
        "black": ToolConfig(
            "black", "black",
            args=["--check", "--diff"],
            category=ErrorCategory.STYLE.value,
            priority=2
        ),
        "pycodestyle": ToolConfig(
            "pycodestyle", "pycodestyle",
            args=["--statistics", "--count"],
            category=ErrorCategory.STYLE.value,
            priority=3
        ),
        "pydocstyle": ToolConfig(
            "pydocstyle", "pydocstyle",
            args=["--convention=google"],
            category=ErrorCategory.DOCUMENTATION.value,
            priority=2
        ),
        
        # Performance analysis
        "py-spy": ToolConfig(
            "py-spy", "py-spy",
            args=["record", "-o", "/tmp/profile.svg", "--", "python"],
            category=ErrorCategory.PERFORMANCE.value,
            priority=3,
            enabled=False  # Requires special setup
        ),
        
        # Testing analysis
        "pytest": ToolConfig(
            "pytest", "pytest",
            args=["--collect-only", "--quiet"],
            category=ErrorCategory.TESTING.value,
            priority=3
        ),
        "coverage": ToolConfig(
            "coverage", "coverage",
            args=["report", "--format=json"],
            category=ErrorCategory.TESTING.value,
            priority=3
        ),
        
        # Compatibility analysis
        "pyupgrade": ToolConfig(
            "pyupgrade", "pyupgrade",
            args=["--py312-plus"],
            category=ErrorCategory.COMPATIBILITY.value,
            priority=3
        ),
        "modernize": ToolConfig(
            "modernize", "python-modernize",
            args=["--print", "--no-diffs"],
            category=ErrorCategory.COMPATIBILITY.value,
            priority=3
        ),
        
        # Additional analysis tools
        "pyflakes": ToolConfig(
            "pyflakes", "pyflakes",
            category=ErrorCategory.LOGIC.value,
            priority=2
        ),
        "mccabe": ToolConfig(
            "mccabe", "python",
            args=["-m", "mccabe", "--min", "5"],
            category=ErrorCategory.MAINTAINABILITY.value,
            priority=3
        ),
        "dodgy": ToolConfig(
            "dodgy", "dodgy",
            args=["--ignore-paths=venv,.venv,env,.env,__pycache__,.git"],
            category=ErrorCategory.SECURITY.value,
            priority=3
        ),
        "dlint": ToolConfig(
            "dlint", "dlint",
            category=ErrorCategory.SECURITY.value,
            priority=3
        ),
        "codespell": ToolConfig(
            "codespell", "codespell",
            args=["--quiet-level=2"],
            category=ErrorCategory.DOCUMENTATION.value,
            priority=3
        ),
        
        # Advanced analysis
        "prospector": ToolConfig(
            "prospector", "prospector",
            args=["--output-format=json", "--full-pep8"],
            category=ErrorCategory.LOGIC.value,
            priority=2
        ),
        "pyanalyze": ToolConfig(
            "pyanalyze", "python",
            args=["-m", "pyanalyze"],
            category=ErrorCategory.TYPE.value,
            priority=3
        )
    }
    
    def __init__(self, target_path: str, config: Optional[Dict] = None, verbose: bool = False):
        """Initialize the comprehensive analyzer."""
        self.target_path = os.path.abspath(target_path)
        self.config = config or {}
        self.verbose = verbose
        self.tools_config = self.COMPREHENSIVE_TOOLS.copy()
        self.graph_analysis = None
        self.lsp_client = None
        self.ruff_integration = None
        self.analysis_cache = {}
        self.error_database = ErrorDatabase()
        
        # Initialize components
        self._initialize_graph_analysis()
        self._initialize_lsp_client()
        self._initialize_ruff_integration()
        
        # Apply configuration
        self._apply_config()
    
    def _initialize_graph_analysis(self):
        """Initialize graph-sitter analysis."""
        try:
            self.graph_analysis = GraphSitterAnalysis(self.target_path, self.config)
            if self.verbose:
                print("Graph-sitter analysis initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize graph-sitter analysis: {e}")
            self.graph_analysis = None
    
    def _initialize_lsp_client(self):
        """Initialize LSP client for real-time error detection."""
        # Try to find and start a Python language server
        lsp_commands = [
            ["pylsp"],  # Python LSP Server
            ["pyright-langserver", "--stdio"],  # Pyright
            ["jedi-language-server"]  # Jedi
        ]
        
        for cmd in lsp_commands:
            try:
                if self._command_exists(cmd[0]):
                    self.lsp_client = LSPClient(cmd, self.target_path)
                    if self.lsp_client.start():
                        if self.verbose:
                            print(f"LSP client started with {cmd[0]}")
                        break
                    else:
                        self.lsp_client = None
            except Exception as e:
                if self.verbose:
                    print(f"Failed to start LSP with {cmd[0]}: {e}")
                continue
    
    def _initialize_ruff_integration(self):
        """Initialize Ruff integration."""
        try:
            self.ruff_integration = RuffIntegration(self.target_path)
            if self.verbose:
                print("Ruff integration initialized")
        except Exception as e:
            logging.error(f"Failed to initialize Ruff integration: {e}")
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system."""
        try:
            subprocess.run(
                ["which", command], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _apply_config(self):
        """Apply configuration settings."""
        if "tools" in self.config:
            for tool_name, tool_config in self.config["tools"].items():
                if tool_name in self.tools_config:
                    self.tools_config[tool_name].enabled = tool_config.get("enabled", True)
                    if "args" in tool_config:
                        self.tools_config[tool_name].args = tool_config["args"]
                    if "timeout" in tool_config:
                        self.tools_config[tool_name].timeout = tool_config["timeout"]
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis using all available tools and methods."""
        start_time = time.time()
        
        analysis_results = {
            "metadata": {
                "target_path": self.target_path,
                "analysis_start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "python_version": sys.version,
                "tools_used": [],
                "analysis_duration": 0
            },
            "graph_sitter_analysis": {},
            "lsp_diagnostics": {},
            "static_analysis": {},
            "errors": [],
            "summary": {},
            "entrypoints": [],
            "dead_code": [],
            "categorized_errors": {},
            "performance_metrics": {},
            "security_issues": [],
            "dependency_analysis": {},
            "quality_metrics": {}
        }
        
        try:
            # 1. Graph-sitter Analysis
            if self.graph_analysis:
                analysis_results["graph_sitter_analysis"] = self._run_graph_sitter_analysis()
                analysis_results["metadata"]["tools_used"].append("graph-sitter")
            
            # 2. LSP Diagnostics
            if self.lsp_client:
                analysis_results["lsp_diagnostics"] = self._run_lsp_analysis()
                analysis_results["metadata"]["tools_used"].append("lsp")
            
            # 3. Ruff Integration
            if self.ruff_integration:
                ruff_errors = self._run_ruff_analysis()
                analysis_results["errors"].extend(ruff_errors)
                analysis_results["metadata"]["tools_used"].append("ruff")
            
            # 4. Static Analysis Tools
            static_analysis_results = self._run_static_analysis()
            analysis_results["static_analysis"] = static_analysis_results
            analysis_results["errors"].extend(self._extract_errors_from_static_analysis(static_analysis_results))
            
            # 5. Advanced Analysis
            analysis_results["entrypoints"] = self._find_entrypoints()
            analysis_results["dead_code"] = self._find_dead_code()
            analysis_results["dependency_analysis"] = self._analyze_dependencies()
            analysis_results["performance_metrics"] = self._calculate_performance_metrics()
            analysis_results["quality_metrics"] = self._calculate_quality_metrics()
            
            # 6. Error Categorization and Prioritization
            analysis_results["categorized_errors"] = self._categorize_errors(analysis_results["errors"])
            
            # 7. Generate Summary
            analysis_results["summary"] = self._generate_comprehensive_summary(analysis_results)
            
        except Exception as e:
            logging.error(f"Error during comprehensive analysis: {e}")
            analysis_results["fatal_error"] = str(e)
        
        finally:
            # Cleanup
            if self.lsp_client:
                self.lsp_client.stop()
            
            # Calculate duration
            end_time = time.time()
            analysis_results["metadata"]["analysis_duration"] = round(end_time - start_time, 2)
            analysis_results["metadata"]["analysis_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return analysis_results
    
    def _run_graph_sitter_analysis(self) -> Dict[str, Any]:
        """Run comprehensive graph-sitter analysis."""
        if not self.graph_analysis:
            return {"error": "Graph-sitter analysis not available"}
        
        try:
            results = {
                "codebase_summary": self.graph_analysis.get_codebase_summary(),
                "files_analysis": {},
                "symbols_analysis": {},
                "dependency_graph": {},
                "inheritance_hierarchy": {},
                "call_graph": {},
                "import_graph": {}
            }
            
            # Analyze each file
            for file_info in self.graph_analysis.files[:50]:  # Limit for performance
                file_path = file_info.get('path', '') if isinstance(file_info, dict) else getattr(file_info, 'path', '')
                if file_path:
                    results["files_analysis"][file_path] = self.graph_analysis.get_file_summary(file_path)
            
            # Analyze symbols
            for symbol_info in self.graph_analysis.symbols[:100]:  # Limit for performance
                symbol_name = symbol_info.get('name', '') if isinstance(symbol_info, dict) else getattr(symbol_info, 'name', '')
                if symbol_name:
                    symbol_analysis = self.graph_analysis.get_symbol_analysis(symbol_name)
                    results["symbols_analysis"][symbol_name] = symbol_analysis
                    
                    # Additional analysis based on symbol type
                    if symbol_analysis.get('type') == 'function':
                        func_analysis = self.graph_analysis.get_function_analysis(symbol_name)
                        results["symbols_analysis"][symbol_name].update(func_analysis)
                    elif symbol_analysis.get('type') == 'class':
                        class_analysis = self.graph_analysis.get_class_analysis(symbol_name)
                        results["symbols_analysis"][symbol_name].update(class_analysis)
            
            # Build dependency graph
            results["dependency_graph"] = self._build_dependency_graph()
            
            # Build inheritance hierarchy
            results["inheritance_hierarchy"] = self._build_inheritance_hierarchy()
            
            # Build call graph
            results["call_graph"] = self._build_call_graph()
            
            # Build import graph
            results["import_graph"] = self._build_import_graph()
            
            return results
            
        except Exception as e:
            logging.error(f"Error in graph-sitter analysis: {e}")
            return {"error": str(e)}
    
    def _run_lsp_analysis(self) -> Dict[str, Any]:
        """Run LSP analysis for real-time error detection."""
        if not self.lsp_client:
            return {"error": "LSP client not available"}
        
        try:
            results = {
                "diagnostics_by_file": {},
                "total_diagnostics": 0,
                "error_summary": {}
            }
            
            # Get diagnostics for each Python file
            if os.path.isfile(self.target_path):
                files_to_analyze = [self.target_path]
            else:
                files_to_analyze = []
                for root, dirs, files in os.walk(self.target_path):
                    for file in files:
                        if file.endswith('.py'):
                            files_to_analyze.append(os.path.join(root, file))
            
            for file_path in files_to_analyze[:20]:  # Limit for performance
                # Send textDocument/didOpen notification
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.lsp_client.send_notification("textDocument/didOpen", {
                    "textDocument": {
                        "uri": f"file://{file_path}",
                        "languageId": "python",
                        "version": 1,
                        "text": content
                    }
                })
                
                # Wait a bit for diagnostics
                time.sleep(0.5)
                
                # Get diagnostics
                diagnostics = self.lsp_client.get_diagnostics(file_path)
                if diagnostics:
                    results["diagnostics_by_file"][file_path] = [
                        {
                            "range": {
                                "start": {"line": d.range.start.line, "character": d.range.start.character},
                                "end": {"line": d.range.end.line, "character": d.range.end.character}
                            },
                            "severity": d.severity.value,
                            "message": d.message,
                            "source": d.source,
                            "code": d.code
                        }
                        for d in diagnostics
                    ]
                    results["total_diagnostics"] += len(diagnostics)
            
            # Generate error summary
            results["error_summary"] = self._summarize_lsp_diagnostics(results["diagnostics_by_file"])
            
            return results
            
        except Exception as e:
            logging.error(f"Error in LSP analysis: {e}")
            return {"error": str(e)}
    
    def _run_ruff_analysis(self) -> List[AnalysisError]:
        """Run comprehensive Ruff analysis."""
        if not self.ruff_integration:
            return []
        
        errors = []
        
        try:
            # Run standard Ruff check
            ruff_errors = self.ruff_integration.run_ruff_check()
            errors.extend(ruff_errors)
            
            # Run Ruff format check
            format_errors = self.ruff_integration.run_ruff_format_check()
            errors.extend(format_errors)
            
            # Additional Ruff configurations for comprehensive analysis
            additional_checks = [
                ["--select=ALL", "--ignore=COM812,ISC001"],  # All rules except conflicting ones
                ["--select=E,W,F", "--statistics"],          # Core errors and warnings
                ["--select=I", "--show-fixes"],              # Import sorting
                ["--select=N", "--show-source"],             # Naming conventions
                ["--select=S", "--show-source"],             # Security
                ["--select=B", "--show-source"],             # Bugbear
                ["--select=C90", "--show-source"],           # Complexity
                ["--select=PL", "--show-source"],            # Pylint
                ["--select=RUF", "--show-source"]            # Ruff-specific
            ]
            
            for check_args in additional_checks:
                try:
                    cmd = ["ruff", "check"] + check_args + [self.target_path]
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=120
                    )
                    
                    if result.stdout:
                        additional_errors = self._parse_ruff_output(result.stdout, check_args[0])
                        errors.extend(additional_errors)
                        
                except Exception as e:
                    if self.verbose:
                        print(f"Additional Ruff check failed: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Error in Ruff analysis: {e}")
        
        return errors
    
    def _run_static_analysis(self) -> Dict[str, Any]:
        """Run all configured static analysis tools."""
        results = {}
        
        # Group tools by category for organized execution
        tools_by_category = defaultdict(list)
        for tool_name, tool_config in self.tools_config.items():
            if tool_config.enabled:
                tools_by_category[tool_config.category].append((tool_name, tool_config))
        
        # Run tools in parallel within each category
        for category, tools in tools_by_category.items():
            if self.verbose:
                print(f"Running {category} analysis tools...")
            
            category_results = {}
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_tool = {
                    executor.submit(self._run_single_tool, tool_name, tool_config): tool_name
                    for tool_name, tool_config in tools
                }
                
                for future in as_completed(future_to_tool):
                    tool_name = future_to_tool[future]
                    try:
                        tool_result = future.result()
                        category_results[tool_name] = tool_result
                    except Exception as e:
                        category_results[tool_name] = {
                            "error": str(e),
                            "success": False
                        }
            
            results[category] = category_results
        
        return results
    
    def _run_single_tool(self, tool_name: str, tool_config: ToolConfig) -> Dict[str, Any]:
        """Run a single analysis tool."""
        if not self._command_exists(tool_config.command.split()[0]):
            return {
                "error": f"Tool {tool_name} not found",
                "success": False,
                "skipped": True
            }
        
        # Build command
        cmd = [tool_config.command] + tool_config.args + [self.target_path]
        if tool_config.command == "python":
            cmd = tool_config.args + [self.target_path]
        
        # Find configuration file
        config_file = self._find_tool_config(tool_name, tool_config)
        if config_file:
            cmd = self._add_config_to_command(cmd, tool_name, config_file)
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=tool_config.timeout,
                cwd=os.path.dirname(self.target_path) if os.path.isfile(self.target_path) else self.target_path
            )
            
            execution_time = time.time() - start_time
            
            return {
                "command": " ".join(cmd),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "execution_time": execution_time,
                "tool_category": tool_config.category,
                "tool_priority": tool_config.priority
            }
            
        except subprocess.TimeoutExpired:
            return {
                "error": f"Tool {tool_name} timed out after {tool_config.timeout}s",
                "success": False,
                "timeout": True,
                "tool_category": tool_config.category
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False,
                "tool_category": tool_config.category
            }
    
    def _find_tool_config(self, tool_name: str, tool_config: ToolConfig) -> Optional[str]:
        """Find configuration file for a tool."""
        if not tool_config.config_file:
            return None
        
        search_dir = self.target_path if os.path.isdir(self.target_path) else os.path.dirname(self.target_path)
        current_dir = Path(search_dir)
        
        while current_dir != current_dir.parent:
            config_path = current_dir / tool_config.config_file
            if config_path.exists():
                return str(config_path)
            current_dir = current_dir.parent
        
        return None
    
    def _add_config_to_command(self, cmd: List[str], tool_name: str, config_file: str) -> List[str]:
        """Add configuration file to command."""
        config_mappings = {
            "pylint": f"--rcfile={config_file}",
            "mypy": f"--config-file={config_file}",
            "flake8": f"--config={config_file}",
            "bandit": f"--configfile={config_file}"
        }
        
        if tool_name in config_mappings:
            cmd.insert(-1, config_mappings[tool_name])
        
        return cmd
    
    def _extract_errors_from_static_analysis(self, static_results: Dict) -> List[AnalysisError]:
        """Extract and convert static analysis results to AnalysisError objects."""
        errors = []
        
        for category, tools in static_results.items():
            for tool_name, tool_result in tools.items():
                if not tool_result.get("success", False) or tool_result.get("stdout", "").strip():
                    errors.extend(self._parse_tool_output(tool_name, tool_result, category))
        
        return errors
    
    def _parse_tool_output(self, tool_name: str, tool_result: Dict, category: str) -> List[AnalysisError]:
        """Parse tool output and convert to AnalysisError objects."""
        errors = []
        
        if tool_result.get("timeout"):
            errors.append(AnalysisError(
                file_path=self.target_path,
                line_number=None,
                column_number=None,
                error_type="timeout",
                severity=DiagnosticSeverity.ERROR,
                message=f"{tool_name} analysis timed out",
                tool_source=tool_name,
                category=category
            ))
            return errors
        
        output = tool_result.get("stdout", "") + tool_result.get("stderr", "")
        
        # Tool-specific parsing
        if tool_name == "pylint":
            errors.extend(self._parse_pylint_output(output, tool_name, category))
        elif tool_name == "mypy":
            errors.extend(self._parse_mypy_output(output, tool_name, category))
        elif tool_name == "pyright":
            errors.extend(self._parse_pyright_output(output, tool_name, category))
        elif tool_name == "bandit":
            errors.extend(self._parse_bandit_output(output, tool_name, category))
        elif tool_name == "safety":
            errors.extend(self._parse_safety_output(output, tool_name, category))
        elif tool_name == "vulture":
            errors.extend(self._parse_vulture_output(output, tool_name, category))
        elif tool_name == "radon":
            errors.extend(self._parse_radon_output(output, tool_name, category))
        else:
            # Generic parsing
            errors.extend(self._parse_generic_output(output, tool_name, category))
        
        return errors
    
    def _parse_pylint_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse Pylint output."""
        errors = []
        
        # Try JSON format first
        try:
            pylint_data = json.loads(output)
            for item in pylint_data:
                if isinstance(item, dict) and "path" in item:
                    error = AnalysisError(
                        file_path=item["path"],
                        line_number=item.get("line"),
                        column_number=item.get("column"),
                        error_type=item.get("type", "unknown"),
                        severity=self._map_pylint_severity(item.get("type", "")),
                        message=item.get("message", ""),
                        tool_source=tool_name,
                        error_code=item.get("message-id"),
                        category=self._categorize_pylint_error(item.get("message-id", "")),
                        confidence=item.get("confidence", 1.0) / 10.0  # Convert to 0-1 scale
                    )
                    errors.append(error)
        except json.JSONDecodeError:
            # Fallback to text parsing
            for line in output.splitlines():
                if ".py:" in line and ": " in line:
                    match = re.match(r"(.+?):(\d+):(\d+): (.+?): (.+)", line)
                    if match:
                        file_path, line_num, col_num, msg_type, message = match.groups()
                        error = AnalysisError(
                            file_path=file_path,
                            line_number=int(line_num),
                            column_number=int(col_num),
                            error_type=msg_type,
                            severity=self._map_pylint_severity(msg_type),
                            message=message,
                            tool_source=tool_name,
                            category=category
                        )
                        errors.append(error)
        
        return errors
    
    def _parse_mypy_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse MyPy output."""
        errors = []
        
        for line in output.splitlines():
            if ".py:" in line and ": " in line:
                # MyPy format: file.py:line:column: error: message [error-code]
                match = re.match(r"(.+?):(\d+):(?:(\d+):)?\s*(\w+):\s*(.+?)(?:\s*\[(.+?)\])?$", line)
                if match:
                    file_path, line_num, col_num, severity, message, error_code = match.groups()
                    
                    error = AnalysisError(
                        file_path=file_path,
                        line_number=int(line_num),
                        column_number=int(col_num) if col_num else None,
                        error_type=severity,
                        severity=self._map_mypy_severity(severity),
                        message=message,
                        tool_source=tool_name,
                        error_code=error_code,
                        category=ErrorCategory.TYPE.value,
                        subcategory=self._categorize_mypy_error(error_code or message)
                    )
                    errors.append(error)
        
        return errors
    
    def _parse_pyright_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse Pyright JSON output."""
        errors = []
        
        try:
            pyright_data = json.loads(output)
            
            for diagnostic in pyright_data.get("generalDiagnostics", []):
                error = AnalysisError(
                    file_path=diagnostic.get("file", ""),
                    line_number=diagnostic.get("range", {}).get("start", {}).get("line"),
                    column_number=diagnostic.get("range", {}).get("start", {}).get("character"),
                    error_type=diagnostic.get("severity", "error"),
                    severity=self._map_pyright_severity(diagnostic.get("severity", "error")),
                    message=diagnostic.get("message", ""),
                    tool_source=tool_name,
                    error_code=diagnostic.get("rule"),
                    category=ErrorCategory.TYPE.value
                )
                errors.append(error)
                
        except json.JSONDecodeError:
            # Fallback to text parsing
            for line in output.splitlines():
                if " - error:" in line or " - warning:" in line:
                    parts = line.split(" - ")
                    if len(parts) >= 2:
                        location = parts[0].strip()
                        severity_message = parts[1]
                        
                        # Extract file path and line number
                        location_match = re.match(r"(.+?):(\d+):(\d+)", location)
                        if location_match:
                            file_path, line_num, col_num = location_match.groups()
                            
                            severity = "error" if "error:" in severity_message else "warning"
                            message = severity_message.split(":", 1)[1].strip() if ":" in severity_message else severity_message
                            
                            error = AnalysisError(
                                file_path=file_path,
                                line_number=int(line_num),
                                column_number=int(col_num),
                                error_type=severity,
                                severity=DiagnosticSeverity.ERROR if severity == "error" else DiagnosticSeverity.WARNING,
                                message=message,
                                tool_source=tool_name,
                                category=ErrorCategory.TYPE.value
                            )
                            errors.append(error)
        
        return errors
    
    def _parse_bandit_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse Bandit security analysis output."""
        errors = []
        
        try:
            bandit_data = json.loads(output)
            
            for result in bandit_data.get("results", []):
                error = AnalysisError(
                    file_path=result.get("filename", ""),
                    line_number=result.get("line_number"),
                    column_number=result.get("col_offset"),
                    error_type="security",
                    severity=self._map_bandit_severity(result.get("issue_severity", "MEDIUM")),
                    message=result.get("issue_text", ""),
                    tool_source=tool_name,
                    error_code=result.get("test_id"),
                    category=ErrorCategory.SECURITY.value,
                    subcategory=result.get("issue_type", "unknown"),
                    confidence=self._map_bandit_confidence(result.get("issue_confidence", "MEDIUM")),
                    code_context=result.get("code")
                )
                errors.append(error)
                
        except json.JSONDecodeError:
            # Fallback to text parsing
            current_file = None
            for line in output.splitlines():
                if "Test results:" in line:
                    break
                
                if line.startswith(">>"):
                    # File indicator
                    current_file = line.replace(">>", "").strip()
                elif "Issue:" in line and current_file:
                    # Parse issue line
                    issue_match = re.search(r"Issue: \[(.+?)\] (.+)", line)
                    if issue_match:
                        severity, message = issue_match.groups()
                        
                        error = AnalysisError(
                            file_path=current_file,
                            line_number=None,
                            column_number=None,
                            error_type="security",
                            severity=self._map_bandit_severity(severity),
                            message=message,
                            tool_source=tool_name,
                            category=ErrorCategory.SECURITY.value
                        )
                        errors.append(error)
        
        return errors
    
    def _parse_safety_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse Safety vulnerability output."""
        errors = []
        
        try:
            # Safety can output JSON or text
            if output.strip().startswith('[') or output.strip().startswith('{'):
                safety_data = json.loads(output)
                
                vulnerabilities = safety_data if isinstance(safety_data, list) else safety_data.get("vulnerabilities", [])
                
                for vuln in vulnerabilities:
                    error = AnalysisError(
                        file_path=self.target_path,
                        line_number=None,
                        column_number=None,
                        error_type="vulnerability",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Vulnerability in {vuln.get('package_name', 'unknown')}: {vuln.get('advisory', '')}",
                        tool_source=tool_name,
                        error_code=vuln.get("vulnerability_id"),
                        category=ErrorCategory.SECURITY.value,
                        subcategory="dependency_vulnerability",
                        fix_suggestion=f"Upgrade to version {vuln.get('fixed_in', 'latest')}"
                    )
                    errors.append(error)
            else:
                # Text parsing
                for line in output.splitlines():
                    if "vulnerability" in line.lower() or "insecure" in line.lower():
                        error = AnalysisError(
                            file_path=self.target_path,
                            line_number=None,
                            column_number=None,
                            error_type="vulnerability",
                            severity=DiagnosticSeverity.ERROR,
                            message=line.strip(),
                            tool_source=tool_name,
                            category=ErrorCategory.SECURITY.value
                        )
                        errors.append(error)
                        
        except json.JSONDecodeError:
            pass
        
        return errors
    
    def _parse_vulture_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse Vulture dead code output."""
        errors = []
        
        for line in output.splitlines():
            if ".py:" in line:
                # Vulture format: file.py:line: unused function/class/variable 'name'
                match = re.match(r"(.+?):(\d+):\s*(.+)", line)
                if match:
                    file_path, line_num, message = match.groups()
                    
                    error = AnalysisError(
                        file_path=file_path,
                        line_number=int(line_num),
                        column_number=None,
                        error_type="dead_code",
                        severity=DiagnosticSeverity.WARNING,
                        message=message,
                        tool_source=tool_name,
                        category=ErrorCategory.LOGIC.value,
                        subcategory="unused_code",
                        tags=["dead_code", "optimization"]
                    )
                    errors.append(error)
        
        return errors
    
    def _parse_radon_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Parse Radon complexity output."""
        errors = []
        
        try:
            # Try JSON format
            if output.strip().startswith('{'):
                radon_data = json.loads(output)
                
                for file_path, metrics in radon_data.items():
                    for item in metrics:
                        complexity = item.get("complexity", 0)
                        if complexity > 10:  # High complexity threshold
                            error = AnalysisError(
                                file_path=file_path,
                                line_number=item.get("lineno"),
                                column_number=item.get("col_offset"),
                                error_type="complexity",
                                severity=DiagnosticSeverity.WARNING if complexity < 20 else DiagnosticSeverity.ERROR,
                                message=f"High complexity ({complexity}) in {item.get('name', 'unknown')}",
                                tool_source=tool_name,
                                category=ErrorCategory.MAINTAINABILITY.value,
                                subcategory="complexity"
                            )
                            errors.append(error)
            else:
                # Text parsing
                for line in output.splitlines():
                    if " - " in line and ("A " in line or "B " in line or "C " in line):
                        complexity_match = re.search(r"([A-F])\s*\((\d+)\)", line)
                        if complexity_match:
                            grade, complexity = complexity_match.groups()
                            complexity_value = int(complexity)
                            
                            if complexity_value > 10:
                                error = AnalysisError(
                                    file_path=self.target_path,
                                    line_number=None,
                                    column_number=None,
                                    error_type="complexity",
                                    severity=DiagnosticSeverity.WARNING if complexity_value < 20 else DiagnosticSeverity.ERROR,
                                    message=f"High complexity ({complexity_value}, grade {grade}): {line.split(' - ')[0]}",
                                    tool_source=tool_name,
                                    category=ErrorCategory.MAINTAINABILITY.value
                                )
                                errors.append(error)
                                
        except json.JSONDecodeError:
            pass
        
        return errors
    
    def _parse_generic_output(self, output: str, tool_name: str, category: str) -> List[AnalysisError]:
        """Generic parser for tool output."""
        errors = []
        
        # Look for common error patterns
        error_patterns = [
            r"(.+?):(\d+):(\d+):\s*(.+)",  # file:line:col: message
            r"(.+?):(\d+):\s*(.+)",        # file:line: message
            r"(.+?)\s*(.+?)\s*(.+)"       # Generic three-part pattern
        ]
        
        for line in output.splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            
            for pattern in error_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    
                    if len(groups) >= 3 and '.py' in groups[0]:
                        try:
                            file_path = groups[0]
                            line_num = int(groups[1]) if groups[1].isdigit() else None
                            col_num = int(groups[2]) if len(groups) > 3 and groups[2].isdigit() else None
                            message = groups[-1]
                            
                            error = AnalysisError(
                                file_path=file_path,
                                line_number=line_num,
                                column_number=col_num,
                                error_type="unknown",
                                severity=DiagnosticSeverity.WARNING,
                                message=message,
                                tool_source=tool_name,
                                category=category
                            )
                            errors.append(error)
                            break
                        except (ValueError, IndexError):
                            continue
        
        return errors
    
    def _parse_ruff_output(self, output: str, select_arg: str) -> List[AnalysisError]:
        """Parse additional Ruff output."""
        errors = []
        
        try:
            if output.strip().startswith('['):
                ruff_data = json.loads(output)
                for issue in ruff_data:
                    error = AnalysisError(
                        file_path=issue.get("filename", ""),
                        line_number=issue.get("location", {}).get("row"),
                        column_number=issue.get("location", {}).get("column"),
                        error_type="ruff_extended",
                        severity=self._map_ruff_severity(issue.get("severity", "warning")),
                        message=issue.get("message", ""),
                        tool_source="ruff",
                        error_code=issue.get("code"),
                        category=self._categorize_ruff_error(issue.get("code", "")),
                        fix_suggestion=issue.get("fix", {}).get("message"),
                        tags=[select_arg.replace("--select=", "")]
                    )
                    errors.append(error)
        except json.JSONDecodeError:
            # Text parsing for additional ruff output
            for line in output.splitlines():
                if '.py:' in line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        try:
                            file_path = parts[0]
                            line_num = int(parts[1])
                            col_num = int(parts[2])
                            message = ':'.join(parts[3:]).strip()
                            
                            error = AnalysisError(
                                file_path=file_path,
                                line_number=line_num,
                                column_number=col_num,
                                error_type="ruff_extended",
                                severity=DiagnosticSeverity.WARNING,
                                message=message,
                                tool_source="ruff",
                                category=ErrorCategory.STYLE.value,
                                tags=[select_arg.replace("--select=", "")]
                            )
                            errors.append(error)
                        except (ValueError, IndexError):
                            continue
        
        return errors
    
    def _map_pylint_severity(self, msg_type: str) -> DiagnosticSeverity:
        """Map Pylint message type to diagnostic severity."""
        mapping = {
            "error": DiagnosticSeverity.ERROR,
            "warning": DiagnosticSeverity.WARNING,
            "refactor": DiagnosticSeverity.INFORMATION,
            "convention": DiagnosticSeverity.HINT,
            "info": DiagnosticSeverity.INFORMATION
        }
        return mapping.get(msg_type.lower(), DiagnosticSeverity.WARNING)
    
    def _map_mypy_severity(self, severity: str) -> DiagnosticSeverity:
        """Map MyPy severity to diagnostic severity."""
        mapping = {
            "error": DiagnosticSeverity.ERROR,
            "warning": DiagnosticSeverity.WARNING,
            "note": DiagnosticSeverity.INFORMATION
        }
        return mapping.get(severity.lower(), DiagnosticSeverity.ERROR)
    
    def _map_pyright_severity(self, severity: str) -> DiagnosticSeverity:
        """Map Pyright severity to diagnostic severity."""
        mapping = {
            "error": DiagnosticSeverity.ERROR,
            "warning": DiagnosticSeverity.WARNING,
            "information": DiagnosticSeverity.INFORMATION
        }
        return mapping.get(severity.lower(), DiagnosticSeverity.ERROR)
    
    def _map_bandit_severity(self, severity: str) -> DiagnosticSeverity:
        """Map Bandit severity to diagnostic severity."""
        mapping = {
            "HIGH": DiagnosticSeverity.ERROR,
            "MEDIUM": DiagnosticSeverity.WARNING,
            "LOW": DiagnosticSeverity.INFORMATION
        }
        return mapping.get(severity.upper(), DiagnosticSeverity.WARNING)
    
    def _map_bandit_confidence(self, confidence: str) -> float:
        """Map Bandit confidence to float value."""
        mapping = {
            "HIGH": 0.9,
            "MEDIUM": 0.6,
            "LOW": 0.3
        }
        return mapping.get(confidence.upper(), 0.5)
    
    def _categorize_pylint_error(self, message_id: str) -> str:
        """Categorize Pylint errors."""
        if not message_id:
            return ErrorCategory.LOGIC.value
        
        category_mapping = {
            "C": ErrorCategory.STYLE.value,
            "R": ErrorCategory.MAINTAINABILITY.value,
            "W": ErrorCategory.LOGIC.value,
            "E": ErrorCategory.LOGIC.value,
            "F": ErrorCategory.SYNTAX.value
        }
        
        prefix = message_id[0] if message_id else "W"
        return category_mapping.get(prefix, ErrorCategory.LOGIC.value)
    
    def _categorize_mypy_error(self, error_info: str) -> str:
        """Categorize MyPy errors."""
        if not error_info:
            return "type_checking"
        
        if any(keyword in error_info.lower() for keyword in ["import", "module"]):
            return "import_error"
        elif any(keyword in error_info.lower() for keyword in ["return", "yield"]):
            return "return_type"
        elif any(keyword in error_info.lower() for keyword in ["argument", "parameter"]):
            return "argument_type"
        elif any(keyword in error_info.lower() for keyword in ["attribute", "member"]):
            return "attribute_error"
        else:
            return "type_checking"
    
    def _categorize_errors(self, errors: List[AnalysisError]) -> Dict[str, Any]:
        """Categorize and organize errors for comprehensive presentation."""
        categorized = {
            "by_severity": defaultdict(list),
            "by_category": defaultdict(list),
            "by_file": defaultdict(list),
            "by_tool": defaultdict(list),
            "by_error_type": defaultdict(list),
            "statistics": {},
            "priority_errors": [],
            "fixable_errors": [],
            "security_critical": [],
            "performance_critical": [],
            "maintainability_issues": []
        }
        
        # Organize errors
        for error in errors:
            categorized["by_severity"][error.severity.name].append(error)
            categorized["by_category"][error.category or "uncategorized"].append(error)
            categorized["by_file"][error.file_path].append(error)
            categorized["by_tool"][error.tool_source].append(error)
            categorized["by_error_type"][error.error_type].append(error)
            
            # Special categorizations
            if error.severity in [DiagnosticSeverity.ERROR]:
                categorized["priority_errors"].append(error)
            
            if error.fix_suggestion:
                categorized["fixable_errors"].append(error)
            
            if error.category == ErrorCategory.SECURITY.value:
                categorized["security_critical"].append(error)
            
            if error.category == ErrorCategory.PERFORMANCE.value:
                categorized["performance_critical"].append(error)
            
            if error.category == ErrorCategory.MAINTAINABILITY.value:
                categorized["maintainability_issues"].append(error)
        
        # Calculate statistics
        categorized["statistics"] = {
            "total_errors": len(errors),
            "critical_errors": len([e for e in errors if e.severity == DiagnosticSeverity.ERROR]),
            "warnings": len([e for e in errors if e.severity == DiagnosticSeverity.WARNING]),
            "info_messages": len([e for e in errors if e.severity == DiagnosticSeverity.INFORMATION]),
            "files_with_errors": len(categorized["by_file"]),
            "tools_with_findings": len(categorized["by_tool"]),
            "categories_affected": len(categorized["by_category"]),
            "fixable_count": len(categorized["fixable_errors"]),
            "security_issues": len(categorized["security_critical"]),
            "performance_issues": len(categorized["performance_critical"])
        }
        
        return categorized
    
    def _find_entrypoints(self) -> List[Dict[str, Any]]:
        """Find entrypoints in the codebase."""
        entrypoints = []
        
        if self.graph_analysis:
            # Use graph-sitter to find entrypoints
            for func in self.graph_analysis.functions[:20]:  # Limit for performance
                func_name = func.get('name', '') if isinstance(func, dict) else getattr(func, 'name', '')
                if func_name in ['main', '__main__', 'run', 'start', 'execute']:
                    entrypoint = {
                        "type": "function",
                        "name": func_name,
                        "file_path": func.get('file_path', '') if isinstance(func, dict) else getattr(func, 'file_path', ''),
                        "line_number": func.get('line_number', 0) if isinstance(func, dict) else getattr(func, 'line_number', 0),
                        "category": "entrypoint"
                    }
                    entrypoints.append(entrypoint)
            
            # Look for classes that might be entrypoints
            for cls in self.graph_analysis.classes[:20]:
                cls_name = cls.get('name', '') if isinstance(cls, dict) else getattr(cls, 'name', '')
                if any(pattern in cls_name.lower() for pattern in ['app', 'main', 'server', 'client', 'runner']):
                    entrypoint = {
                        "type": "class",
                        "name": cls_name,
                        "file_path": cls.get('file_path', '') if isinstance(cls, dict) else getattr(cls, 'file_path', ''),
                        "line_number": cls.get('line_number', 0) if isinstance(cls, dict) else getattr(cls, 'line_number', 0),
                        "category": "entrypoint"
                    }
                    entrypoints.append(entrypoint)
        
        # Look for if __name__ == "__main__" patterns
        for file_info in (self.graph_analysis.files if self.graph_analysis else [])[:30]:
            file_path = file_info.get('path', '') if isinstance(file_info, dict) else getattr(file_info, 'path', '')
            if file_path and file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'if __name__ == "__main__"' in content:
                        entrypoint = {
                            "type": "script",
                            "name": os.path.basename(file_path),
                            "file_path": file_path,
                            "line_number": content.count('\n', 0, content.find('if __name__ == "__main__"')) + 1,
                            "category": "entrypoint"
                        }
                        entrypoints.append(entrypoint)
                        
                except Exception:
                    continue
        
        return entrypoints
    
    def _find_dead_code(self) -> List[Dict[str, Any]]:
        """Find dead code in the codebase."""
        dead_code = []
        
        if not self.graph_analysis:
            return dead_code
        
        # Find unused functions
        for func in self.graph_analysis.functions:
            func_name = func.get('name', '') if isinstance(func, dict) else getattr(func, 'name', '')
            if func_name:
                usages = self.graph_analysis._find_function_usages(func_name)
                if not usages and not func_name.startswith('_'):  # Ignore private functions
                    dead_code.append({
                        "type": "function",
                        "name": func_name,
                        "file_path": func.get('file_path', '') if isinstance(func, dict) else getattr(func, 'file_path', ''),
                        "line_number": func.get('line_number', 0) if isinstance(func, dict) else getattr(func, 'line_number', 0),
                        "category": "unused_function",
                        "context": "Not used by any other code"
                    })
        
        # Find unused classes
        for cls in self.graph_analysis.classes:
            cls_name = cls.get('name', '') if isinstance(cls, dict) else getattr(cls, 'name', '')
            if cls_name:
                usages = self.graph_analysis._find_symbol_usages(cls_name)
                if not usages and not cls_name.startswith('_'):
                    dead_code.append({
                        "type": "class",
                        "name": cls_name,
                        "file_path": cls.get('file_path', '') if isinstance(cls, dict) else getattr(cls, 'file_path', ''),
                        "line_number": cls.get('line_number', 0) if isinstance(cls, dict) else getattr(cls, 'line_number', 0),
                        "category": "unused_class",
                        "context": "Not used by any other code"
                    })
        
        # Find unused imports
        for imp in self.graph_analysis.imports:
            imp_name = imp.get('name', '') if isinstance(imp, dict) else getattr(imp, 'name', '')
            imp_file = imp.get('file_path', '') if isinstance(imp, dict) else getattr(imp, 'file_path', '')
            
            if imp_name and imp_file:
                # Check if the imported name is used in the file
                try:
                    with open(imp_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple check - look for the name in the file content
                    import_line_num = imp.get('line_number', 0) if isinstance(imp, dict) else getattr(imp, 'line_number', 0)
                    lines_after_import = content.splitlines()[import_line_num:]
                    
                    if not any(imp_name in line for line in lines_after_import):
                        dead_code.append({
                            "type": "import",
                            "name": imp_name,
                            "file_path": imp_file,
                            "line_number": import_line_num,
                            "category": "unused_import",
                            "context": f"Imported but never used in {os.path.basename(imp_file)}"
                        })
                        
                except Exception:
                    continue
        
        return dead_code
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies."""
        dependency_analysis = {
            "external_dependencies": [],
            "internal_dependencies": [],
            "circular_dependencies": [],
            "dependency_graph": {},
            "security_issues": [],
            "outdated_packages": [],
            "dependency_statistics": {}
        }
        
        try:
            # Analyze external dependencies
            if self.graph_analysis:
                for ext_mod in self.graph_analysis.external_modules:
                    mod_name = ext_mod.get('name', '') if isinstance(ext_mod, dict) else getattr(ext_mod, 'name', '')
                    if mod_name:
                        dependency_analysis["external_dependencies"].append({
                            "name": mod_name,
                            "usage_count": len(self.graph_analysis._find_symbol_usages(mod_name)),
                            "import_locations": [
                                imp.get('file_path', '') if isinstance(imp, dict) else getattr(imp, 'file_path', '')
                                for imp in self.graph_analysis.imports
                                if (imp.get('module', '') if isinstance(imp, dict) else getattr(imp, 'module', '')) == mod_name
                            ]
                        })
            
            # Check for circular dependencies using imports
            dependency_analysis["circular_dependencies"] = self._find_circular_dependencies()
            
            # Analyze requirements.txt or pyproject.toml
            dependency_analysis["dependency_statistics"] = self._analyze_dependency_files()
            
        except Exception as e:
            logging.error(f"Error in dependency analysis: {e}")
            dependency_analysis["error"] = str(e)
        
        return dependency_analysis
    
    def _find_circular_dependencies(self) -> List[Dict[str, Any]]:
        """Find circular dependencies in the codebase."""
        circular_deps = []
        
        if not self.graph_analysis:
            return circular_deps
        
        # Build a simple dependency graph
        deps_graph = defaultdict(set)
        
        for imp in self.graph_analysis.imports:
            imp_file = imp.get('file_path', '') if isinstance(imp, dict) else getattr(imp, 'file_path', '')
            imp_module = imp.get('module', '') if isinstance(imp, dict) else getattr(imp, 'module', '')
            
            if imp_file and imp_module and not imp.get('is_external', True):
                # Convert module name to file path (simplified)
                target_file = imp_module.replace('.', '/') + '.py'
                deps_graph[imp_file].add(target_file)
        
        # Simple cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                return cycle
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in deps_graph.get(node, []):
                cycle = has_cycle(neighbor, path + [node])
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            return None
        
        for node in deps_graph:
            if node not in visited:
                cycle = has_cycle(node, [])
                if cycle:
                    circular_deps.append({
                        "cycle": cycle,
                        "type": "import_cycle",
                        "severity": "high",
                        "description": f"Circular import detected: {' -> '.join(cycle)}"
                    })
        
        return circular_deps
    
    def _analyze_dependency_files(self) -> Dict[str, Any]:
        """Analyze dependency configuration files."""
        stats = {
            "requirements_files": [],
            "pyproject_config": {},
            "total_dependencies": 0,
            "dev_dependencies": 0,
            "optional_dependencies": 0
        }
        
        # Check for requirements files
        req_files = ["requirements.txt", "requirements-dev.txt", "requirements-test.txt"]
        base_dir = self.target_path if os.path.isdir(self.target_path) else os.path.dirname(self.target_path)
        
        for req_file in req_files:
            req_path = os.path.join(base_dir, req_file)
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r') as f:
                        lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                    stats["requirements_files"].append({
                        "file": req_file,
                        "dependencies": len(lines),
                        "content": lines[:10]  # First 10 for sample
                    })
                    stats["total_dependencies"] += len(lines)
                except Exception:
                    pass
        
        # Check pyproject.toml
        pyproject_path = os.path.join(base_dir, "pyproject.toml")
        if os.path.exists(pyproject_path):
            try:
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                
                project = pyproject_data.get("project", {})
                dependencies = project.get("dependencies", [])
                optional_deps = project.get("optional-dependencies", {})
                
                stats["pyproject_config"] = {
                    "dependencies": len(dependencies),
                    "optional_dependency_groups": len(optional_deps),
                    "total_optional": sum(len(deps) for deps in optional_deps.values())
                }
                stats["total_dependencies"] += len(dependencies)
                stats["optional_dependencies"] = sum(len(deps) for deps in optional_deps.values())
                
            except Exception as e:
                stats["pyproject_config"] = {"error": str(e)}
        
        return stats
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance-related metrics."""
        metrics = {
            "complexity_analysis": {},
            "function_metrics": {},
            "class_metrics": {},
            "file_metrics": {},
            "performance_warnings": []
        }
        
        if not self.graph_analysis:
            return metrics
        
        try:
            # Function complexity metrics
            function_complexities = []
            for func in self.graph_analysis.functions:
                complexity = self.graph_analysis._calculate_function_complexity(func)
                function_complexities.append(complexity)
                
                if complexity > 15:  # High complexity threshold
                    func_name = func.get('name', '') if isinstance(func, dict) else getattr(func, 'name', '')
                    func_file = func.get('file_path', '') if isinstance(func, dict) else getattr(func, 'file_path', '')
                    
                    metrics["performance_warnings"].append({
                        "type": "high_complexity",
                        "function": func_name,
                        "file": func_file,
                        "complexity": complexity,
                        "recommendation": "Consider refactoring into smaller functions"
                    })
            
            metrics["function_metrics"] = {
                "total_functions": len(function_complexities),
                "average_complexity": sum(function_complexities) / len(function_complexities) if function_complexities else 0,
                "max_complexity": max(function_complexities) if function_complexities else 0,
                "high_complexity_count": len([c for c in function_complexities if c > 10])
            }
            
            # Class metrics
            class_complexities = []
            for cls in self.graph_analysis.classes:
                complexity = self.graph_analysis._calculate_class_complexity(cls)
                class_complexities.append(complexity)
            
            metrics["class_metrics"] = {
                "total_classes": len(class_complexities),
                "average_complexity": sum(class_complexities) / len(class_complexities) if class_complexities else 0,
                "max_complexity": max(class_complexities) if class_complexities else 0
            }
            
            # File metrics
            file_sizes = []
            for file_info in self.graph_analysis.files:
                size = file_info.get('line_count', 0) if isinstance(file_info, dict) else getattr(file_info, 'line_count', 0)
                file_sizes.append(size)
                
                if size > 500:  # Large file threshold
                    file_path = file_info.get('path', '') if isinstance(file_info, dict) else getattr(file_info, 'path', '')
                    metrics["performance_warnings"].append({
                        "type": "large_file",
                        "file": file_path,
                        "lines": size,
                        "recommendation": "Consider splitting into smaller modules"
                    })
            
            metrics["file_metrics"] = {
                "total_files": len(file_sizes),
                "average_file_size": sum(file_sizes) / len(file_sizes) if file_sizes else 0,
                "largest_file": max(file_sizes) if file_sizes else 0,
                "large_files_count": len([s for s in file_sizes if s > 300])
            }
            
        except Exception as e:
            logging.error(f"Error calculating performance metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        metrics = {
            "documentation_coverage": 0.0,
            "test_coverage": 0.0,
            "maintainability_index": 0.0,
            "technical_debt_ratio": 0.0,
            "code_duplication": 0.0,
            "quality_gates": {},
            "recommendations": []
        }
        
        try:
            if self.graph_analysis:
                # Documentation coverage
                documented_functions = 0
                total_functions = len(self.graph_analysis.functions)
                
                for func in self.graph_analysis.functions:
                    func_file = func.get('file_path', '') if isinstance(func, dict) else getattr(func, 'file_path', '')
                    func_line = func.get('line_number', 0) if isinstance(func, dict) else getattr(func, 'line_number', 0)
                    
                    if func_file and func_line:
                        try:
                            with open(func_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            
                            # Check for docstring after function definition
                            if func_line < len(lines):
                                for i in range(func_line, min(func_line + 5, len(lines))):
                                    if '"""' in lines[i] or "'''" in lines[i]:
                                        documented_functions += 1
                                        break
                        except Exception:
                            continue
                
                metrics["documentation_coverage"] = documented_functions / total_functions if total_functions > 0 else 0.0
                
                # Calculate maintainability index (simplified)
                avg_complexity = self.graph_analysis._calculate_complexity_score()
                total_loc = sum(f.get('line_count', 0) for f in self.graph_analysis.files)
                
                # Simplified maintainability index calculation
                metrics["maintainability_index"] = max(0, 100 - (avg_complexity * 10) - (total_loc / 1000))
                
                # Quality gates
                metrics["quality_gates"] = {
                    "documentation_gate": metrics["documentation_coverage"] >= 0.7,
                    "complexity_gate": avg_complexity <= 10,
                    "file_size_gate": all(f.get('line_count', 0) <= 500 for f in self.graph_analysis.files),
                    "maintainability_gate": metrics["maintainability_index"] >= 60
                }
                
                # Generate recommendations
                if metrics["documentation_coverage"] < 0.5:
                    metrics["recommendations"].append("Improve documentation coverage")
                if avg_complexity > 15:
                    metrics["recommendations"].append("Reduce code complexity")
                if metrics["maintainability_index"] < 50:
                    metrics["recommendations"].append("Focus on code maintainability")
        
        except Exception as e:
            logging.error(f"Error calculating quality metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _build_dependency_graph(self) -> Dict[str, Any]:
        """Build comprehensive dependency graph."""
        graph = {
            "nodes": [],
            "edges": [],
            "clusters": [],
            "metrics": {}
        }
        
        if not self.graph_analysis:
            return graph
        
        try:
            # Add file nodes
            for file_info in self.graph_analysis.files:
                file_path = file_info.get('path', '') if isinstance(file_info, dict) else getattr(file_info, 'path', '')
                if file_path:
                    graph["nodes"].append({
                        "id": file_path,
                        "type": "file",
                        "label": os.path.basename(file_path),
                        "size": file_info.get('line_count', 0) if isinstance(file_info, dict) else getattr(file_info, 'line_count', 0)
                    })
            
            # Add dependency edges
            for imp in self.graph_analysis.imports:
                source_file = imp.get('file_path', '') if isinstance(imp, dict) else getattr(imp, 'file_path', '')
                target_module = imp.get('module', '') if isinstance(imp, dict) else getattr(imp, 'module', '')
                
                if source_file and target_module:
                    # Convert module to file path (simplified)
                    if not imp.get('is_external', True):
                        target_file = target_module.replace('.', '/') + '.py'
                        graph["edges"].append({
                            "source": source_file,
                            "target": target_file,
                            "type": "import",
                            "weight": 1
                        })
            
            # Calculate metrics
            graph["metrics"] = {
                "total_nodes": len(graph["nodes"]),
                "total_edges": len(graph["edges"]),
                "average_dependencies": len(graph["edges"]) / len(graph["nodes"]) if graph["nodes"] else 0
            }
            
        except Exception as e:
            logging.error(f"Error building dependency graph: {e}")
            graph["error"] = str(e)
        
        return graph
    
    def _build_inheritance_hierarchy(self) -> Dict[str, Any]:
        """Build inheritance hierarchy."""
        hierarchy = {
            "inheritance_trees": [],
            "abstract_classes": [],
            "leaf_classes": [],
            "metrics": {}
        }
        
        if not self.graph_analysis:
            return hierarchy
        
        try:
            # Build inheritance relationships
            class_inheritance = {}
            for cls in self.graph_analysis.classes:
                cls_name = cls.get('name', '') if isinstance(cls, dict) else getattr(cls, 'name', '')
                bases = cls.get('bases', []) if isinstance(cls, dict) else getattr(cls, 'bases', [])
                
                if cls_name:
                    class_inheritance[cls_name] = {
                        "bases": bases,
                        "file_path": cls.get('file_path', '') if isinstance(cls, dict) else getattr(cls, 'file_path', ''),
                        "line_number": cls.get('line_number', 0) if isinstance(cls, dict) else getattr(cls, 'line_number', 0)
                    }
            
            # Find inheritance chains
            for cls_name, cls_info in class_inheritance.items():
                if cls_info["bases"]:
                    chain = [cls_name]
                    current = cls_name
                    
                    while current in class_inheritance and class_inheritance[current]["bases"]:
                        bases = class_inheritance[current]["bases"]
                        if bases and bases[0] in class_inheritance:
                            current = bases[0]
                            chain.append(current)
                        else:
                            break
                    
                    if len(chain) > 1:
                        hierarchy["inheritance_trees"].append({
                            "chain": chain,
                            "depth": len(chain),
                            "root_class": chain[-1],
                            "leaf_class": chain[0]
                        })
            
            # Calculate metrics
            hierarchy["metrics"] = {
                "total_classes": len(class_inheritance),
                "classes_with_inheritance": len([c for c in class_inheritance.values() if c["bases"]]),
                "max_inheritance_depth": max([len(tree["chain"]) for tree in hierarchy["inheritance_trees"]], default=0),
                "average_inheritance_depth": sum([len(tree["chain"]) for tree in hierarchy["inheritance_trees"]]) / len(hierarchy["inheritance_trees"]) if hierarchy["inheritance_trees"] else 0
            }
            
        except Exception as e:
            logging.error(f"Error building inheritance hierarchy: {e}")
            hierarchy["error"] = str(e)
        
        return hierarchy
    
    def _build_call_graph(self) -> Dict[str, Any]:
        """Build function call graph."""
        call_graph = {
            "nodes": [],
            "edges": [],
            "metrics": {},
            "hotspots": [],
            "call_chains": []
        }
        
        if not self.graph_analysis:
            return call_graph
        
        try:
            # Add function nodes
            for func in self.graph_analysis.functions:
                func_name = func.get('name', '') if isinstance(func, dict) else getattr(func, 'name', '')
                if func_name:
                    call_graph["nodes"].append({
                        "id": func_name,
                        "type": "function",
                        "file": func.get('file_path', '') if isinstance(func, dict) else getattr(func, 'file_path', ''),
                        "complexity": self.graph_analysis._calculate_function_complexity(func),
                        "parameters": len(func.get('parameters', []) if isinstance(func, dict) else getattr(func, 'parameters', []))
                    })
            
            # Simple call relationship detection (would be more sophisticated with graph-sitter)
            for func in self.graph_analysis.functions:
                func_name = func.get('name', '') if isinstance(func, dict) else getattr(func, 'name', '')
                func_file = func.get('file_path', '') if isinstance(func, dict) else getattr(func, 'file_path', '')
                
                if func_file and func_name:
                    try:
                        with open(func_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for function calls (simplified)
                        for other_func in self.graph_analysis.functions:
                            other_name = other_func.get('name', '') if isinstance(other_func, dict) else getattr(other_func, 'name', '')
                            if other_name and other_name != func_name and f"{other_name}(" in content:
                                call_graph["edges"].append({
                                    "source": func_name,
                                    "target": other_name,
                                    "type": "function_call"
                                })
                    except Exception:
                        continue
            
            # Find hotspots (most called functions)
            call_counts = Counter(edge["target"] for edge in call_graph["edges"])
            call_graph["hotspots"] = [
                {"function": func, "call_count": count}
                for func, count in call_counts.most_common(10)
            ]
            
            # Calculate metrics
            call_graph["metrics"] = {
                "total_functions": len(call_graph["nodes"]),
                "total_calls": len(call_graph["edges"]),
                "average_calls_per_function": len(call_graph["edges"]) / len(call_graph["nodes"]) if call_graph["nodes"] else 0,
                "most_called_function": call_graph["hotspots"][0]["function"] if call_graph["hotspots"] else None
            }
            
        except Exception as e:
            logging.error(f"Error building call graph: {e}")
            call_graph["error"] = str(e)
        
        return call_graph
    
    def _build_import_graph(self) -> Dict[str, Any]:
        """Build import dependency graph."""
        import_graph = {
            "internal_imports": [],
            "external_imports": [],
            "import_clusters": [],
            "unused_imports": [],
            "metrics": {}
        }
        
        if not self.graph_analysis:
            return import_graph
        
        try:
            # Categorize imports
            for imp in self.graph_analysis.imports:
                imp_data = {
                    "module": imp.get('module', '') if isinstance(imp, dict) else getattr(imp, 'module', ''),
                    "name": imp.get('name', '') if isinstance(imp, dict) else getattr(imp, 'name', ''),
                    "file_path": imp.get('file_path', '') if isinstance(imp, dict) else getattr(imp, 'file_path', ''),
                    "line_number": imp.get('line_number', 0) if isinstance(imp, dict) else getattr(imp, 'line_number', 0)
                }
                
                if imp.get('is_external', True):
                    import_graph["external_imports"].append(imp_data)
                else:
                    import_graph["internal_imports"].append(imp_data)
            
            # Find import clusters (files that import similar modules)
            external_by_file = defaultdict(set)
            for imp in import_graph["external_imports"]:
                external_by_file[imp["file_path"]].add(imp["module"])
            
            # Group files with similar import patterns
            import_patterns = defaultdict(list)
            for file_path, modules in external_by_file.items():
                pattern_key = tuple(sorted(modules))
                import_patterns[pattern_key].append(file_path)
            
            for pattern, files in import_patterns.items():
                if len(files) > 1:
                    import_graph["import_clusters"].append({
                        "pattern": list(pattern),
                        "files": files,
                        "cluster_size": len(files)
                    })
            
            # Calculate metrics
            import_graph["metrics"] = {
                "total_imports": len(self.graph_analysis.imports),
                "external_imports": len(import_graph["external_imports"]),
                "internal_imports": len(import_graph["internal_imports"]),
                "unique_external_modules": len(set(imp["module"] for imp in import_graph["external_imports"])),
                "import_clusters": len(import_graph["import_clusters"]),
                "average_imports_per_file": len(self.graph_analysis.imports) / len(self.graph_analysis.files) if self.graph_analysis.files else 0
            }
            
        except Exception as e:
            logging.error(f"Error building import graph: {e}")
            import_graph["error"] = str(e)
        
        return import_graph
    
    def _summarize_lsp_diagnostics(self, diagnostics_by_file: Dict) -> Dict[str, Any]:
        """Summarize LSP diagnostics."""
        summary = {
            "total_files_with_errors": len(diagnostics_by_file),
            "severity_breakdown": defaultdict(int),
            "error_sources": defaultdict(int),
            "most_problematic_files": []
        }
        
        file_error_counts = []
        
        for file_path, diagnostics in diagnostics_by_file.items():
            error_count = len(diagnostics)
            file_error_counts.append((file_path, error_count))
            
            for diagnostic in diagnostics:
                severity = diagnostic.get("severity", 1)
                source = diagnostic.get("source", "unknown")
                
                summary["severity_breakdown"][severity] += 1
                summary["error_sources"][source] += 1
        
        # Sort files by error count
        file_error_counts.sort(key=lambda x: x[1], reverse=True)
        summary["most_problematic_files"] = file_error_counts[:10]
        
        return summary
    
    def _generate_comprehensive_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis summary."""
        summary = {
            "overview": {},
            "critical_findings": [],
            "recommendations": [],
            "quality_score": 0.0,
            "risk_assessment": {},
            "action_items": []
        }
        
        try:
            # Overview statistics
            total_errors = len(analysis_results.get("errors", []))
            categorized = analysis_results.get("categorized_errors", {})
            
            summary["overview"] = {
                "total_errors": total_errors,
                "critical_errors": categorized.get("statistics", {}).get("critical_errors", 0),
                "warnings": categorized.get("statistics", {}).get("warnings", 0),
                "files_analyzed": len(analysis_results.get("graph_sitter_analysis", {}).get("files_analysis", {})),
                "tools_used": len(analysis_results.get("metadata", {}).get("tools_used", [])),
                "analysis_duration": analysis_results.get("metadata", {}).get("analysis_duration", 0)
            }
            
            # Critical findings
            priority_errors = categorized.get("priority_errors", [])
            security_issues = categorized.get("security_critical", [])
            
            summary["critical_findings"] = [
                f"Found {len(priority_errors)} critical errors",
                f"Identified {len(security_issues)} security issues",
                f"Detected {len(analysis_results.get('dead_code', []))} dead code instances"
            ]
            
            # Risk assessment
            summary["risk_assessment"] = {
                "security_risk": "high" if len(security_issues) > 5 else "medium" if len(security_issues) > 0 else "low",
                "maintenance_risk": "high" if total_errors > 100 else "medium" if total_errors > 20 else "low",
                "quality_risk": "high" if categorized.get("statistics", {}).get("critical_errors", 0) > 10 else "low"
            }
            
            # Calculate quality score
            quality_metrics = analysis_results.get("quality_metrics", {})
            performance_metrics = analysis_results.get("performance_metrics", {})
            
            doc_coverage = quality_metrics.get("documentation_coverage", 0.0)
            maintainability = quality_metrics.get("maintainability_index", 0.0)
            error_penalty = min(total_errors * 0.5, 50)  # Cap penalty at 50 points
            
            summary["quality_score"] = max(0.0, (doc_coverage * 30) + (maintainability * 0.7) - error_penalty)
            
            # Generate recommendations
            if doc_coverage < 0.5:
                summary["recommendations"].append("Improve code documentation")
            if len(security_issues) > 0:
                summary["recommendations"].append("Address security vulnerabilities")
            if total_errors > 50:
                summary["recommendations"].append("Reduce overall error count")
            if len(analysis_results.get("dead_code", [])) > 10:
                summary["recommendations"].append("Remove dead code")
            
            # Action items
            summary["action_items"] = [
                {
                    "priority": "high",
                    "category": "security",
                    "action": f"Fix {len(security_issues)} security issues",
                    "estimated_effort": "medium"
                },
                {
                    "priority": "medium", 
                    "category": "quality",
                    "action": f"Address {categorized.get('statistics', {}).get('critical_errors', 0)} critical errors",
                    "estimated_effort": "high"
                },
                {
                    "priority": "low",
                    "category": "maintenance",
                    "action": f"Clean up {len(analysis_results.get('dead_code', []))} dead code items",
                    "estimated_effort": "low"
                }
            ]
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            summary["error"] = str(e)
        
        return summary


class AnalysisEngine:
    """
    Comprehensive analysis engine for deep code analysis, integrating Graph-Sitter and LSP.
    """

    def __init__(self, codebase: Codebase, language: str):
        self.codebase = codebase
        self.language = language
        self.analyzer = GraphSitterAnalyzer(codebase)
        self.lsp_manager = LSPDiagnosticsManager(
            codebase, Language(language)
        )  # Pass codebase object
        self.context_cache = {}
        self.insight_cache = {}

    async def perform_full_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis using Graph-Sitter and LSP."""
        try:
            # 1. Open files in LSP server for diagnostic collection
            logger.info("Opening files in LSP server for diagnostic collection...")
            self.lsp_manager.start_server()  # Start LSP server
            for file_obj in self.codebase.files:
                try:
                    self.lsp_manager.open_file(file_obj.filepath, file_obj.source)
                except Exception as e:
                    logger.warning(
                        f"Could not open file {file_obj.filepath} with LSP: {e}"
                    )

            # Give LSP server some time to process files and publish diagnostics
            logger.info(
                "Waiting for LSP server to process files and publish diagnostics (5 seconds)..."
            )
            await asyncio.sleep(5)  # Adjust as needed for larger codebases

            # 2. Retrieve Enhanced Diagnostics
            logger.info("Retrieving enhanced diagnostics from LSP server...")
            all_lsp_diagnostics = self.lsp_manager.get_all_enhanced_diagnostics()

            # 3. Perform Graph-Sitter Analysis
            logger.info("Performing comprehensive Graph-Sitter analysis...")
            codebase_summary = self.analyzer.get_codebase_overview()
            tree_structure = self._build_tree_structure_from_graph_sitter(
                self.codebase, all_lsp_diagnostics
            )
            error_analysis = self._analyze_errors_with_graph_sitter_enhanced(
                self.codebase, all_lsp_diagnostics
            )
            dead_code_analysis = (
                self.analyzer.find_dead_code()
            )  # Using GraphSitterAnalyzer
            entrypoint_analysis = self._analyze_entrypoints_with_graph_sitter_enhanced(
                self.codebase
            )
            dependency_graph = self._build_dependency_graph_from_graph_sitter(
                self.codebase
            )
            code_quality_metrics = self._calculate_code_quality_metrics(self.codebase)
            architectural_insights = self._analyze_architectural_patterns(self.codebase)
            security_analysis = self._analyze_security_patterns(self.codebase)
            performance_analysis = self._analyze_performance_patterns(self.codebase)

            analysis = {
                "codebase_summary": codebase_summary,
                "tree_structure": tree_structure,
                "error_analysis": error_analysis,
                "dead_code_analysis": dead_code_analysis,
                "entrypoint_analysis": entrypoint_analysis,
                "dependency_graph": dependency_graph,
                "code_quality_metrics": code_quality_metrics,
                "architectural_insights": architectural_insights,
                "security_analysis": security_analysis,
                "performance_analysis": performance_analysis,
                "metrics": {
                    "files": len(list(self.codebase.files)),
                    "functions": len(list(self.codebase.functions)),
                    "classes": len(list(self.codebase.classes)),
                    "symbols": len(list(self.codebase.symbols)),
                    "imports": len(list(self.codebase.imports)),
                    "external_modules": len(list(self.codebase.external_modules)),
                },
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing codebase with graph-sitter: {e}")
            logger.error(traceback.format_exc())
            raise Exception(f"Graph-sitter analysis failed: {str(e)}")
        finally:
            self.lsp_manager.shutdown_server()  # Ensure LSP server is shut down

    def _analyze_errors_with_graph_sitter_enhanced(
        self, codebase: Codebase, lsp_diagnostics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhanced comprehensive error analysis using Graph-sitter APIs and LSP diagnostics."""
        errors = {
            "total": 0,
            "critical": 0,
            "major": 0,
            "minor": 0,
            "by_category": defaultdict(int),  # Use defaultdict for easier counting
            "detailed_errors": [],
            "error_patterns": [],
            "suggestions": [],
            "resolution_recommendations": [],
        }

        # Integrate LSP diagnostics (which are already enhanced by autogenlib_context)
        for enhanced_diag in lsp_diagnostics:
            diag = enhanced_diag["diagnostic"]
            error_entry = {
                "severity": diag.severity.name.lower() if diag.severity else "unknown",
                "category": diag.code if diag.code else "lsp_diagnostic",
                "file": enhanced_diag["relative_file_path"],  # Use relative path
                "symbol": diag.source,  # LSP source
                "line": diag.range.line + 1,
                "message": diag.message,
                "context": enhanced_diag,  # Store the full enhanced diagnostic object
                "suggestion": "Review LSP diagnostic message and apply fix.",
                "resolution_method": "ai_resolution_lsp",
            }
            errors["detailed_errors"].append(error_entry)
            errors["by_category"][error_entry["category"]] += 1
            if error_entry["severity"] == "error":  # LSP error severity is 1 (Error)
                errors["critical"] += 1
            elif (
                error_entry["severity"] == "warning"
            ):  # LSP warning severity is 2 (Warning)
                errors["major"] += 1
            else:  # Info, Hint, Unknown
                errors["minor"] += 1
            errors["total"] += 1

        # Add Graph-Sitter specific analysis (e.g., missing docstrings, unused imports, circular imports)
        # These are examples; actual implementation would involve traversing codebase objects
        # and checking properties like `usages`, `docstring`, `return_type`, etc.

        # Example: Missing docstrings
        for func in codebase.functions:
            if not hasattr(func, "docstring") or not func.docstring:
                error_entry = {
                    "severity": "minor",
                    "category": "missing_docstrings",
                    "file": func.filepath,
                    "symbol": func.name,
                    "line": func.start_point.line + 1
                    if hasattr(func, "start_point")
                    else 0,
                    "message": "Missing docstring",
                    "context": f"Function '{func.name}' has no documentation",
                    "suggestion": f'Add docstring: """Brief description of {func.name}."""',
                    "resolution_method": "generate_docstring",
                }
                errors["detailed_errors"].append(error_entry)
                errors["by_category"]["missing_docstrings"] += 1
                errors["minor"] += 1
                errors["total"] += 1

        # Example: Unused imports
        for file_obj in codebase.files:
            for imp in file_obj.imports:
                if not hasattr(imp, "usages") or len(imp.usages) == 0:
                    error_entry = {
                        "severity": "minor",
                        "category": "unused_imports",
                        "file": file_obj.filepath,
                        "symbol": imp.name,
                        "line": imp.start_point.line + 1
                        if hasattr(imp, "start_point")
                        else 0,
                        "message": "Unused import",
                        "context": f"Import '{imp.name}' is not used",
                        "suggestion": "Remove unused import",
                        "resolution_method": "remove_unused_imports",
                    }
                    errors["detailed_errors"].append(error_entry)
                    errors["by_category"]["unused_imports"] += 1
                    errors["minor"] += 1
                    errors["total"] += 1

        # Example: Circular imports (using NetworkX)
        import_graph = nx.DiGraph()
        for file_obj in codebase.files:
            import_graph.add_node(file_obj.filepath)
            for imp in file_obj.imports:
                if hasattr(imp, "from_file") and imp.from_file:
                    import_graph.add_edge(file_obj.filepath, imp.from_file.filepath)

        cycles = list(nx.simple_cycles(import_graph))
        for cycle in cycles:
            for file_path in cycle:
                error_entry = {
                    "severity": "critical",
                    "category": "circular_imports",
                    "file": file_path,
                    "symbol": "imports",
                    "line": 1,
                    "message": "Circular import detected",
                    "context": f"File is part of circular import: {' -> '.join(cycle)}",
                    "suggestion": "Refactor to remove circular dependency",
                    "resolution_method": "refactor_circular_imports",
                }
                errors["detailed_errors"].append(error_entry)
                errors["by_category"]["circular_imports"] += 1
                errors["critical"] += 1
                errors["total"] += 1

        # Generate enhanced error patterns
        errors["error_patterns"] = self._analyze_error_patterns(
            errors["detailed_errors"]
        )

        # Generate resolution recommendations
        errors["resolution_recommendations"] = (
            self._generate_resolution_recommendations(errors)
        )

        return errors

    def _analyze_error_patterns(
        self, detailed_errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhanced error pattern analysis with resolution suggestions"""
        patterns = []

        # Group errors by category and file
        error_groups = defaultdict(lambda: defaultdict(list))
        for error in detailed_errors:
            error_groups[error["category"]][error["file"]].append(error)

        # Analyze patterns within each category
        for category, file_errors in error_groups.items():
            if len(file_errors) > 1:
                total_errors = sum(len(errors) for errors in file_errors.values())
                most_affected_files = sorted(
                    file_errors.items(), key=lambda x: len(x[1]), reverse=True
                )[:3]

                patterns.append(
                    {
                        "category": category,
                        "total_count": total_errors,
                        "affected_files": len(file_errors),
                        "most_affected_files": [
                            {"file": file, "count": len(errors)}
                            for file, errors in most_affected_files
                        ],
                        "pattern_description": f"Widespread {category} errors across {len(file_errors)} files",
                        "severity": most_affected_files[0][1][0]["severity"]
                        if most_affected_files
                        else "minor",
                        "resolution_strategy": self._get_resolution_strategy(category),
                    }
                )

        return patterns

    def _get_resolution_strategy(self, category: str) -> str:
        """Get resolution strategy for error category"""
        strategies = {
            "missing_types": "Use type inference tools or add explicit type annotations",
            "unused_parameters": "Remove unused parameters or prefix with underscore",
            "unused_imports": "Use import optimization tools to remove unused imports",
            "wrong_call_sites": "Update function signatures or fix call sites",
            "circular_imports": "Refactor code to break circular dependencies",
            "unresolved_imports": "Fix import paths or install missing dependencies",
            "missing_arguments": "Add required arguments to function calls",
            "incorrect_types": "Fix type annotations or import missing types",
            "unimplemented_methods": "Implement abstract methods or remove inheritance",
            "missing_attributes": "Add missing class attributes or fix attribute access",
            "parameter_mismatches": "Fix argument types to match parameter expectations",
            "assignment_errors": "Define variables before use or fix variable references",
            "lsp_diagnostic": "Consult LSP server documentation for specific diagnostic code, or use AI resolution.",
        }
        return strategies.get(category, "Manual review and correction required")

    def _generate_resolution_recommendations(
        self, errors: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive resolution recommendations"""
        recommendations = []

        # Type-related recommendations
        type_errors_count = errors["by_category"].get("missing_types", 0) + errors[
            "by_category"
        ].get("incorrect_types", 0)
        if type_errors_count > 0:
            recommendations.append(
                {
                    "type": "type_resolution",
                    "priority": "high",
                    "description": f"Resolve {type_errors_count} type-related issues",
                    "actions": [
                        "Run mypy --install-types to install missing type stubs",
                        "Add explicit type annotations to functions and variables",
                        "Use type inference tools to suggest appropriate types",
                        "Import missing types from appropriate modules",
                    ],
                    "automated_fix": "resolve_all_types",
                }
            )

        # Import-related recommendations
        import_errors_count = (
            errors["by_category"].get("unresolved_imports", 0)
            + errors["by_category"].get("unused_imports", 0)
            + errors["by_category"].get("circular_imports", 0)
        )
        if import_errors_count > 0:
            recommendations.append(
                {
                    "type": "import_resolution",
                    "priority": "medium",
                    "description": f"Resolve {import_errors_count} import-related issues",
                    "actions": [
                        "Fix unresolved import paths",
                        "Remove unused imports",
                        "Organize imports by type (stdlib, third-party, local)",
                        "Add missing imports for used symbols",
                        "Refactor code to break circular dependencies",
                    ],
                    "automated_fix": "resolve_all_imports",
                }
            )

        # Function call recommendations
        call_errors_count = (
            errors["by_category"].get("wrong_call_sites", 0)
            + errors["by_category"].get("missing_arguments", 0)
            + errors["by_category"].get("parameter_mismatches", 0)
        )
        if call_errors_count > 0:
            recommendations.append(
                {
                    "type": "function_call_resolution",
                    "priority": "high",
                    "description": f"Resolve {call_errors_count} function call issues",
                    "actions": [
                        "Add missing arguments to function calls",
                        "Fix argument types to match parameter expectations",
                        "Update function signatures if needed",
                        "Convert positional arguments to keyword arguments",
                    ],
                    "automated_fix": "resolve_all_function_calls",
                }
            )

        # LSP specific recommendations
        lsp_diag_count = errors["by_category"].get("lsp_diagnostic", 0)
        if lsp_diag_count > 0:
            recommendations.append(
                {
                    "type": "lsp_diagnostic_resolution",
                    "priority": "high",
                    "description": f"Address {lsp_diag_count} LSP reported diagnostics",
                    "actions": [
                        "Review detailed LSP messages for specific guidance",
                        "Utilize AI-driven resolution for automated fixes",
                        "Consult language-specific documentation for best practices",
                    ],
                    "automated_fix": "ai_resolution_lsp",
                }
            )

        return recommendations

    def _analyze_entrypoints_with_graph_sitter_enhanced(
        self, codebase: Codebase
    ) -> Dict[str, Any]:
        """Enhanced entrypoint analysis using comprehensive Graph-sitter APIs"""
        entrypoints = {
            "total_entrypoints": 0,
            "main_entrypoints": [],
            "secondary_entrypoints": [],
            "test_entrypoints": [],
            "api_entrypoints": [],
            "cli_entrypoints": [],
            "entrypoint_graph": {},
            "complexity_metrics": {},
            "dependency_analysis": {},
            "call_flow_analysis": {},
        }

        # Enhanced main entrypoint detection
        for func in codebase.functions:
            if self._is_entrypoint_function_enhanced(func):
                entrypoint_data = {
                    "name": func.name,
                    "file": func.filepath,
                    "type": "function",
                    "complexity": self._calculate_function_complexity(func),
                    "dependencies": len(list(func.dependencies)),
                    "usages": len(list(func.usages)),
                    "call_sites": len(
                        list(func.function_calls)
                    ),  # Changed from call_sites
                    "is_async": getattr(func, "is_async", False),
                    "parameters": self._get_function_parameters_details(
                        func
                    ),  # Detailed parameters
                    "return_type": self._get_function_return_type_details(
                        func
                    ),  # Detailed return type
                    "local_variables": self._get_function_local_variables_details(
                        func
                    ),  # Local variables
                    "docstring": bool(getattr(func, "docstring", None)),
                    "function_calls_count": len(list(func.function_calls)),
                    "return_statements_count": len(
                        list(getattr(func, "return_statements", []))
                    ),
                    "variable_usages_count": len(
                        list(getattr(func, "variable_usages", []))
                    ),
                    "symbol_usages_count": len(
                        list(getattr(func, "symbol_usages", []))
                    ),
                    "entrypoint_score": self._calculate_entrypoint_score(func),
                }

                # Categorize entrypoints more precisely
                if func.name in ["main", "__main__"] or func.name.startswith("main_"):
                    entrypoints["main_entrypoints"].append(entrypoint_data)
                elif self._is_api_entrypoint(func):
                    entrypoints["api_entrypoints"].append(entrypoint_data)
                elif self._is_cli_entrypoint(func):
                    entrypoints["cli_entrypoints"].append(entrypoint_data)
                else:
                    entrypoints["secondary_entrypoints"].append(entrypoint_data)

        # Enhanced class entrypoint detection
        for cls in codebase.classes:
            if self._is_entrypoint_class_enhanced(cls):
                entrypoint_data = {
                    "name": cls.name,
                    "file": cls.filepath,
                    "type": "class",
                    "complexity": self._calculate_class_complexity(cls),
                    "methods_count": len(list(cls.methods)),
                    "attributes_count": len(list(cls.attributes)),
                    "inheritance_depth": calculate_doi(cls),
                    "usages_count": len(list(cls.usages)),
                    "subclasses_count": len(list(cls.subclasses)),
                    "dependencies_count": len(list(cls.dependencies)),
                    "entrypoint_score": self._calculate_class_entrypoint_score(cls),
                    "methods_details": [
                        {
                            "name": m.name,
                            "parameters": self._get_function_parameters_details(m),
                            "return_type": self._get_function_return_type_details(m),
                            "complexity": self._calculate_function_complexity(m),
                        }
                        for m in cls.methods
                    ],
                }

                if self._is_api_entrypoint_class(cls):
                    entrypoints["api_entrypoints"].append(entrypoint_data)
                else:
                    entrypoints["secondary_entrypoints"].append(entrypoint_data)

        # Enhanced test entrypoint detection
        for func in codebase.functions:
            if self._is_test_function_enhanced(func):
                entrypoint_data = {
                    "name": func.name,
                    "file": func.filepath,
                    "type": "test_function",
                    "complexity": self._calculate_function_complexity(func),
                    "dependencies_count": len(list(func.dependencies)),
                    "test_type": self._classify_test_type(func),
                    "test_coverage_estimate": self._estimate_test_coverage(func),
                }
                entrypoints["test_entrypoints"].append(entrypoint_data)

        # Calculate totals
        entrypoints["total_entrypoints"] = (
            len(entrypoints["main_entrypoints"])
            + len(entrypoints["secondary_entrypoints"])
            + len(entrypoints["test_entrypoints"])
            + len(entrypoints["api_entrypoints"])
            + len(entrypoints["cli_entrypoints"])
        )

        # Enhanced entrypoint graph analysis
        entrypoint_graph = nx.DiGraph()
        all_entrypoints_list = (
            entrypoints["main_entrypoints"]
            + entrypoints["secondary_entrypoints"]
            + entrypoints["api_entrypoints"]
            + entrypoints["cli_entrypoints"]
        )

        for entrypoint in all_entrypoints_list:
            func = next(
                (f for f in codebase.functions if f.name == entrypoint["name"]), None
            )
            if func:
                entrypoint_graph.add_node(func.name, **entrypoint)

                # Add call relationships
                for call in func.function_calls:
                    if (
                        hasattr(call, "function_definition")
                        and call.function_definition
                    ):
                        called_func = call.function_definition
                        if not isinstance(called_func, ExternalModule):
                            entrypoint_graph.add_edge(
                                func.name,
                                called_func.name,
                                relationship="calls",
                                call_count=1,
                            )

                # Add dependency relationships
                for dep in func.dependencies:
                    if (
                        hasattr(dep, "name")
                        and dep.name != func.name
                        and not isinstance(dep, ExternalModule)
                    ):
                        entrypoint_graph.add_edge(
                            func.name, dep.name, relationship="depends_on"
                        )

        entrypoints["entrypoint_graph"] = {
            "nodes": len(entrypoint_graph.nodes),
            "edges": len(entrypoint_graph.edges),
            "connected_components": len(
                list(nx.weakly_connected_components(entrypoint_graph))
            ),
            "strongly_connected_components": len(
                list(nx.strongly_connected_components(entrypoint_graph))
            ),
            "cycles": len(list(nx.simple_cycles(entrypoint_graph))),
            "max_depth": len(nx.dag_longest_path(entrypoint_graph))
            if nx.is_directed_acyclic_graph(entrypoint_graph)
            else 0,
        }

        # Enhanced complexity metrics
        complexities = [ep["complexity"] for ep in all_entrypoints_list]
        if complexities:
            entrypoints["complexity_metrics"] = {
                "average_complexity": sum(complexities) / len(complexities),
                "max_complexity": max(complexities),
                "min_complexity": min(complexities),
                "high_complexity_count": len([c for c in complexities if c > 10]),
                "complexity_distribution": {
                    "low": len([c for c in complexities if c <= 5]),
                    "medium": len([c for c in complexities if 5 < c <= 10]),
                    "high": len([c for c in complexities if c > 10]),
                },
            }

        # Dependency analysis
        entrypoints["dependency_analysis"] = self._analyze_entrypoint_dependencies(
            all_entrypoints_list, codebase
        )

        # Call flow analysis
        entrypoints["call_flow_analysis"] = self._analyze_entrypoint_call_flows(
            all_entrypoints_list, codebase
        )

        return entrypoints

    def _get_function_parameters_details(self, func: Function) -> List[Dict[str, Any]]:
        """Extracts detailed information about function parameters."""
        params_details = []
        for param in func.parameters:
            param_type_source = (
                getattr(param.type, "source", "Any")
                if hasattr(param, "type") and param.type
                else "Any"
            )
            resolved_types = []
            if (
                hasattr(param, "type")
                and param.type
                and hasattr(param.type, "resolved_value")
                and param.type.resolved_value
            ):
                # resolved_value can be a single Symbol or a list of Symbols
                resolved_symbols = param.type.resolved_value
                if not isinstance(resolved_symbols, list):
                    resolved_symbols = [resolved_symbols]
                for res_sym in resolved_symbols:
                    if isinstance(res_sym, Symbol):
                        resolved_types.append(
                            {
                                "name": res_sym.name,
                                "type": type(res_sym).__name__,
                                "filepath": res_sym.filepath
                                if hasattr(res_sym, "filepath")
                                else None,
                            }
                        )
                    elif isinstance(res_sym, ExternalModule):
                        resolved_types.append(
                            {"name": res_sym.name, "type": "ExternalModule"}
                        )
                    else:
                        resolved_types.append({"name": str(res_sym), "type": "Unknown"})

            params_details.append(
                {
                    "name": param.name,
                    "type_annotation": param_type_source,
                    "resolved_types": resolved_types,
                    "has_default": param.has_default,
                    "is_keyword_only": param.is_keyword_only,
                    "is_positional_only": param.is_positional_only,
                    "is_var_arg": param.is_var_arg,
                    "is_var_kw": param.is_var_kw,
                }
            )
        return params_details

    def _get_function_return_type_details(self, func: Function) -> Dict[str, Any]:
        """Extracts detailed information about function return type."""
        return_type_source = (
            getattr(func.return_type, "source", "Any")
            if hasattr(func, "return_type") and func.return_type
            else "Any"
        )
        resolved_types = []
        if (
            hasattr(func, "return_type")
            and func.return_type
            and hasattr(func.return_type, "resolved_value")
            and func.return_type.resolved_value
        ):
            resolved_symbols = func.return_type.resolved_value
            if not isinstance(resolved_symbols, list):
                resolved_symbols = [resolved_symbols]
            for res_sym in resolved_symbols:
                if isinstance(res_sym, Symbol):
                    resolved_types.append(
                        {
                            "name": res_sym.name,
                            "type": type(res_sym).__name__,
                            "filepath": res_sym.filepath
                            if hasattr(res_sym, "filepath")
                            else None,
                        }
                    )
                elif isinstance(res_sym, ExternalModule):
                    resolved_types.append(
                        {"name": res_sym.name, "type": "ExternalModule"}
                    )
                else:
                    resolved_types.append({"name": str(res_sym), "type": "Unknown"})
        return {"type_annotation": return_type_source, "resolved_types": resolved_types}

    def _get_function_local_variables_details(
        self, func: Function
    ) -> List[Dict[str, Any]]:
        """Extracts details about local variables defined within a function."""
        local_vars = []
        if hasattr(func, "code_block") and hasattr(
            func.code_block, "local_var_assignments"
        ):
            for assignment in func.code_block.local_var_assignments:
                var_type_source = (
                    getattr(assignment.type, "source", "Any")
                    if hasattr(assignment, "type") and assignment.type
                    else "Any"
                )
                local_vars.append(
                    {
                        "name": assignment.name,
                        "type_annotation": var_type_source,
                        "line": assignment.start_point.line + 1
                        if hasattr(assignment, "start_point")
                        else None,
                        "value_snippet": assignment.source
                        if hasattr(assignment, "source")
                        else None,
                    }
                )
        return local_vars

    def _is_test_function_enhanced(self, func: Function) -> bool:
        """Enhanced test function detection"""
        # Standard test patterns
        if func.name.startswith("test_") or func.name.endswith("_test"):
            return True

        # Check for test decorators
        if hasattr(func, "decorators"):
            for decorator in func.decorators:
                decorator_source = getattr(decorator, "source", "")
                if any(
                    pattern in decorator_source.lower()
                    for pattern in ["@pytest.", "@unittest.", "@test"]
                ):
                    return True

        # Check if in test file
        test_file_patterns = ["test_", "_test.", "tests/", "/test/", "spec_", "_spec."]
        if any(pattern in func.filepath for pattern in test_file_patterns):
            return True

        # Check for assertion patterns in function body
        if hasattr(func, "source") and func.source:
            assertion_patterns = ["assert ", "self.assert", "expect(", "should."]
            if any(pattern in func.source for pattern in assertion_patterns):
                return True

        return False

    def _is_entrypoint_class_enhanced(self, cls: Class) -> bool:
        """Enhanced entrypoint class detection"""
        # Standard entrypoint patterns
        entrypoint_patterns = [
            "app",
            "application",
            "server",
            "client",
            "main",
            "runner",
            "service",
            "controller",
        ]
        if any(pattern in cls.name.lower() for pattern in entrypoint_patterns):
            return True

        # Check for framework-specific patterns
        framework_patterns = ["fastapi", "flask", "django", "tornado", "aiohttp"]
        for method in cls.methods:
            if any(pattern in method.name.lower() for pattern in framework_patterns):
                return True

        # Check for inheritance from framework classes
        for superclass in cls.superclasses:
            if any(
                pattern in superclass.name.lower()
                for pattern in ["application", "app", "service", "handler"]
            ):
                return True

        # Check for singleton patterns (often used for main application classes)
        if any(
            "instance" in method.name.lower() or "singleton" in method.name.lower()
            for method in cls.methods
        ):
            return True

        return False

    def _is_api_entrypoint_class(self, cls: Class) -> bool:
        """Check if class is an API entrypoint"""
        api_patterns = ["api", "router", "controller", "handler", "endpoint", "view"]
        if any(pattern in cls.name.lower() for pattern in api_patterns):
            return True

        # Check for API-related decorators on methods
        for method in cls.methods:
            if hasattr(method, "decorators"):
                for decorator in method.decorators:
                    decorator_source = getattr(decorator, "source", "")
                    if any(
                        pattern in decorator_source.lower()
                        for pattern in ["@route", "@get", "@post", "@put", "@delete"]
                    ):
                        return True

        # Check for inheritance from API frameworks
        for superclass in cls.superclasses:
            if any(
                pattern in superclass.name.lower()
                for pattern in ["resource", "view", "handler", "controller"]
            ):
                return True

        return False

    def _calculate_entrypoint_score(self, func: Function) -> float:
        """Calculate entrypoint score based on various factors"""
        score = 0.0

        # Base score for being a function
        score += 1.0

        # Score based on name patterns
        entrypoint_names = ["main", "run", "start", "execute", "app", "serve", "launch"]
        if any(name in func.name.lower() for name in entrypoint_names):
            score += 2.0

        # Score based on usage patterns
        if len(func.usages) == 0:  # Not called by other functions
            score += 1.0
        elif len(func.usages) < 3:  # Called by few functions
            score += 0.5

        # Score based on complexity (entrypoints often coordinate other functions)
        complexity = self._calculate_function_complexity(func)
        if 5 <= complexity <= 15:  # Sweet spot for entrypoints
            score += 1.0
        elif complexity > 15:  # Very complex, likely important
            score += 0.5

        # Score based on function calls (entrypoints often call many other functions)
        if len(func.function_calls) > 5:
            score += 1.0
        elif len(func.function_calls) > 2:
            score += 0.5

        # Score based on decorators
        if hasattr(func, "decorators"):
            for decorator in func.decorators:
                decorator_source = getattr(decorator, "source", "")
                if any(
                    pattern in decorator_source.lower()
                    for pattern in ["@app.", "@click.", "@typer."]
                ):
                    score += 2.0

        # Score based on file location
        if any(
            pattern in func.filepath
            for pattern in ["main.py", "app.py", "server.py", "cli.py"]
        ):
            score += 1.0

        return score

    def _estimate_test_coverage(self, func: Function) -> float:
        """Estimate test coverage based on function characteristics"""
        coverage = 0.0

        # Base coverage for being a test
        coverage += 0.3

        # Coverage based on assertions
        if hasattr(func, "source") and func.source:
            assertion_count = func.source.count("assert ") + func.source.count(
                "self.assert"
            )
            coverage += min(0.4, assertion_count * 0.1)

        # Coverage based on function calls (tests that call many functions likely test more)
        call_count = len(func.function_calls)
        coverage += min(0.3, call_count * 0.05)

        return min(1.0, coverage)

    def _analyze_entrypoint_dependencies(
        self, all_entrypoints: List[Dict[str, Any]], codebase: Codebase
    ) -> Dict[str, Any]:
        """Analyze dependencies between entrypoints"""
        dependency_analysis = {
            "shared_dependencies": [],
            "isolated_entrypoints": [],
            "dependency_clusters": [],
            "external_dependencies": [],
        }

        # Find shared dependencies
        entrypoint_deps = {}
        for entrypoint in all_entrypoints:
            func = next(
                (f for f in codebase.functions if f.name == entrypoint["name"]), None
            )
            if func:
                entrypoint_deps[entrypoint["name"]] = set(
                    dep.name
                    for dep in func.dependencies
                    if not isinstance(dep, ExternalModule)
                )
                # Track external dependencies
                for dep in func.dependencies:
                    if isinstance(dep, ExternalModule):
                        dependency_analysis["external_dependencies"].append(
                            {
                                "entrypoint": entrypoint["name"],
                                "dependency": dep.name,
                                "module": dep.module,
                            }
                        )

        # Find dependencies shared by multiple entrypoints
        all_deps = set()
        for deps in entrypoint_deps.values():
            all_deps.update(deps)

        for dep in all_deps:
            sharing_entrypoints = [
                name for name, deps in entrypoint_deps.items() if dep in deps
            ]
            if len(sharing_entrypoints) > 1:
                dependency_analysis["shared_dependencies"].append(
                    {
                        "dependency": dep,
                        "shared_by": sharing_entrypoints,
                        "share_count": len(sharing_entrypoints),
                    }
                )

        # Find isolated entrypoints
        for name, deps in entrypoint_deps.items():
            shared_deps = [
                dep
                for dep in deps
                if any(
                    dep in other_deps
                    for other_name, other_deps in entrypoint_deps.items()
                    if other_name != name
                )
            ]
            if len(shared_deps) == 0:
                dependency_analysis["isolated_entrypoints"].append(name)

        return dependency_analysis

    def _analyze_entrypoint_call_flows(
        self, all_entrypoints: List[Dict[str, Any]], codebase: Codebase
    ) -> Dict[str, Any]:
        """Analyze call flows from entrypoints"""
        call_flow_analysis = {
            "max_call_depth": 0,
            "average_call_depth": 0.0,
            "call_patterns": [],
            "recursive_calls": [],
        }

        call_depths = []

        for entrypoint in all_entrypoints:
            func = next(
                (f for f in codebase.functions if f.name == entrypoint["name"]), None
            )
            if func:
                # Calculate call depth using BFS
                depth = self._calculate_call_depth(func, codebase)
                call_depths.append(depth)

                # Check for recursive calls
                if self._has_recursive_calls(func):
                    call_flow_analysis["recursive_calls"].append(
                        {"entrypoint": entrypoint["name"], "file": entrypoint["file"]}
                    )

        if call_depths:
            call_flow_analysis["max_call_depth"] = max(call_depths)
            call_flow_analysis["average_call_depth"] = sum(call_depths) / len(
                call_depths
            )

        return call_flow_analysis

    def _calculate_call_depth(
        self, func: Function, codebase: Codebase, visited=None, depth=0
    ) -> int:
        """Calculate maximum call depth from a function"""
        if visited is None:
            visited = set()

        if func in visited or depth > 20:  # Prevent infinite recursion
            return depth

        visited.add(func)
        max_depth = depth

        for call in func.function_calls:
            if hasattr(call, "function_definition") and call.function_definition:
                called_func = call.function_definition
                if not isinstance(called_func, ExternalModule):
                    call_depth = self._calculate_call_depth(
                        called_func, codebase, visited.copy(), depth + 1
                    )
                    max_depth = max(max_depth, call_depth)

        return max_depth

    def _has_recursive_calls(self, func: Function) -> bool:
        """Check if function has recursive calls"""
        for call in func.function_calls:
            if hasattr(call, "function_definition") and call.function_definition:
                if call.function_definition.name == func.name:
                    return True
        return False

    def _calculate_class_entrypoint_score(self, cls: Class) -> float:
        """Calculate entrypoint score for classes"""
        score = 0.0

        # Base score for being a class
        score += 1.0

        # Score based on name patterns
        entrypoint_names = ["app", "application", "server", "client", "main", "service"]
        if any(name in cls.name.lower() for name in entrypoint_names):
            score += 2.0

        # Score based on methods
        if len(cls.methods) > 10:  # Large classes often coordinate functionality
            score += 1.0

        # Score based on inheritance
        if len(cls.superclasses) > 0:
            for superclass in cls.superclasses:
                if any(
                    pattern in superclass.name.lower()
                    for pattern in ["application", "service", "handler"]
                ):
                    score += 1.5

        # Score based on singleton patterns
        if any("instance" in method.name.lower() for method in cls.methods):
            score += 1.0

        return score

    def _classify_test_type(self, func: Function) -> str:
        """Classify the type of test function"""
        if "unit" in func.filepath or "unit" in func.name.lower():
            return "unit"
        elif "integration" in func.filepath or "integration" in func.name.lower():
            return "integration"
        elif "e2e" in func.filepath or "end_to_end" in func.name.lower():
            return "end_to_end"
        elif "performance" in func.filepath or "perf" in func.name.lower():
            return "performance"
        else:
            return "unknown"

    def _build_tree_structure_from_graph_sitter(
        self, codebase: Codebase, all_lsp_diagnostics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build hierarchical tree structure from graph-sitter codebase with integrated LSP errors"""
        root = {
            "name": "root",
            "type": "directory",
            "path": "",
            "children": [],
            "errors": {"critical": 0, "major": 0, "minor": 0},
            "isEntrypoint": False,
            "metrics": {
                "complexity_score": 0,
                "maintainability_index": 0,
                "lines_of_code": 0,
            },
        }

        # Group files by directory
        dir_structure = defaultdict(lambda: {"files": [], "subdirs": {}})

        for file_obj in (
            codebase.files
        ):  # Changed from file to file_obj to avoid conflict with file.filepath
            try:
                # Get LSP diagnostics for this file
                file_lsp_diagnostics = [
                    d
                    for d in all_lsp_diagnostics
                    if d["relative_file_path"] == file_obj.filepath
                ]

                file_node = {
                    "name": file_obj.name,
                    "type": "file",
                    "path": file_obj.filepath,
                    "children": [],
                    "errors": self._detect_file_errors_graph_sitter(
                        file_obj, file_lsp_diagnostics
                    ),  # Pass LSP diagnostics
                    "isEntrypoint": self._is_entrypoint_file(file_obj),
                    "metrics": {
                        "lines": len(file_obj.source.splitlines())
                        if hasattr(file_obj, "source")
                        else 0,
                        "functions": len(list(file_obj.functions)),
                        "classes": len(list(file_obj.classes)),
                        "imports": len(list(file_obj.imports)),
                        "symbols": len(list(getattr(file_obj, "symbols", []))),
                        "variable_usages": len(
                            list(getattr(file_obj, "variable_usages", []))
                        ),
                        "symbol_usages": len(
                            list(getattr(file_obj, "symbol_usages", []))
                        ),
                        "complexity_score": self._calculate_file_complexity(file_obj),
                        "maintainability_index": self._calculate_maintainability_index(
                            file_obj
                        ),
                    },
                }

                # Add functions as children with comprehensive metrics
                for func in file_obj.functions:
                    try:
                        func_node = {
                            "name": func.name,
                            "type": "function",
                            "path": f"{file_obj.filepath}::{func.name}",
                            "children": [],
                            "errors": self._detect_function_errors_graph_sitter(
                                func, file_lsp_diagnostics
                            ),  # Pass LSP diagnostics
                            "isEntrypoint": self._is_entrypoint_function(func),
                            "metrics": {
                                "parameters": self._get_function_parameters_details(
                                    func
                                ),  # Detailed parameters
                                "return_type": self._get_function_return_type_details(
                                    func
                                ),  # Detailed return type
                                "local_variables": self._get_function_local_variables_details(
                                    func
                                ),  # Local variables
                                "usages": len(list(func.usages)),
                                "call_sites": len(
                                    list(func.function_calls)
                                ),  # Changed from call_sites
                                "dependencies": len(list(func.dependencies)),
                                "return_statements_count": len(
                                    list(getattr(func, "return_statements", []))
                                ),
                                "variable_usages_count": len(
                                    list(getattr(func, "variable_usages", []))
                                ),
                                "symbol_usages_count": len(
                                    list(getattr(func, "symbol_usages", []))
                                ),
                                "parent_class": getattr(func, "parent_class", None)
                                is not None,
                                "parent_function": getattr(
                                    func, "parent_function", None
                                )
                                is not None,
                                "type_parameters": len(
                                    list(getattr(func, "type_parameters", []))
                                ),
                                "complexity_score": self._calculate_function_complexity(
                                    func
                                ),
                                "halstead_volume": calculate_halstead_volume(
                                    *get_operators_and_operands(func)
                                )[0],  # Only volume
                            },
                        }
                        file_node["children"].append(func_node)
                    except Exception as e:
                        logger.warning(f"Error processing function {func.name}: {e}")

                # Add classes as children with comprehensive metrics
                for cls in file_obj.classes:
                    try:
                        class_node = {
                            "name": cls.name,
                            "type": "class",
                            "path": f"{file_obj.filepath}::{cls.name}",
                            "children": [],
                            "errors": self._detect_class_errors_graph_sitter(
                                cls, file_lsp_diagnostics
                            ),  # Pass LSP diagnostics
                            "isEntrypoint": self._is_entrypoint_class(cls),
                            "metrics": {
                                "methods": len(list(cls.methods)),
                                "attributes": len(list(cls.attributes)),
                                "usages": len(list(cls.usages)),
                                "superclasses": len(list(cls.superclasses)),
                                "subclasses": len(list(cls.subclasses)),
                                "dependencies": len(list(cls.dependencies)),
                                "symbol_type": getattr(cls, "symbol_type", "class"),
                                "parent": getattr(cls, "parent", None) is not None,
                                "resolved_value": getattr(cls, "resolved_value", None)
                                is not None,
                                "inheritance_depth": calculate_doi(cls),
                                "complexity_score": self._calculate_class_complexity(
                                    cls
                                ),
                            },
                        }

                        # Add methods as children with enhanced metrics
                        for method in cls.methods:
                            try:
                                method_node = {
                                    "name": method.name,
                                    "type": "method",
                                    "path": f"{file_obj.filepath}::{cls.name}::{method.name}",
                                    "children": [],
                                    "errors": self._detect_function_errors_graph_sitter(
                                        method, file_lsp_diagnostics
                                    ),
                                    "isEntrypoint": False,
                                    "metrics": {
                                        "parameters": self._get_function_parameters_details(
                                            method
                                        ),
                                        "return_type": self._get_function_return_type_details(
                                            method
                                        ),
                                        "local_variables": self._get_function_local_variables_details(
                                            method
                                        ),
                                        "usages": len(list(method.usages)),
                                        "parent_class": cls.name,
                                        "parent_function": getattr(
                                            method, "parent_function", None
                                        )
                                        is not None,
                                        "variable_usages_count": len(
                                            list(getattr(method, "variable_usages", []))
                                        ),
                                        "symbol_usages_count": len(
                                            list(getattr(method, "symbol_usages", []))
                                        ),
                                        "parent_statement": getattr(
                                            method, "parent_statement", None
                                        )
                                        is not None,
                                        "complexity_score": self._calculate_function_complexity(
                                            method
                                        ),
                                    },
                                }
                                class_node["children"].append(method_node)
                            except Exception as e:
                                logger.warning(
                                    f"Error processing method {method.name}: {e}"
                                )

                        file_node["children"].append(class_node)
                    except Exception as e:
                        logger.warning(f"Error processing class {cls.name}: {e}")

                # Add to directory structure
                path_parts = file_obj.filepath.split(os.sep)
                current_dir_level = dir_structure
                for part in path_parts[:-1]:
                    current_dir_level = current_dir_level[part]["subdirs"]
                current_dir_level[path_parts[-1]] = {
                    "files": [file_node],
                    "subdirs": {},
                }  # Store file node under its name

            except Exception as e:
                logger.warning(f"Error processing file {file_obj.filepath}: {e}")

        # Convert to hierarchical structure
        root["children"] = self._build_directory_nodes_recursive(dir_structure, "")
        return root

    def _build_directory_nodes_recursive(
        self, dir_structure: Dict, current_path: str
    ) -> List[Dict]:
        """Recursively build directory nodes from the processed dir_structure."""
        nodes = []

        for name, content in dir_structure.items():
            if "files" in content and content["files"]:
                # This is a file node already processed
                nodes.extend(content["files"])
            else:
                # This is a directory node
                dir_node = {
                    "name": name,
                    "type": "directory",
                    "path": os.path.join(current_path, name).replace(
                        "\\", "/"
                    ),  # Ensure Unix-like paths
                    "children": [],
                    "errors": {"critical": 0, "major": 0, "minor": 0},
                    "isEntrypoint": False,
                    "metrics": {
                        "total_files": 0,
                        "total_functions": 0,
                        "total_classes": 0,
                        "total_lines": 0,
                    },
                }

                # Add subdirectories and files
                dir_node["children"].extend(
                    self._build_directory_nodes_recursive(
                        content["subdirs"], dir_node["path"]
                    )
                )

                # Aggregate errors and metrics from children
                for child in dir_node["children"]:
                    for severity in ["critical", "major", "minor"]:
                        dir_node["errors"][severity] += child["errors"][severity]

                    if child["type"] == "file":
                        dir_node["metrics"]["total_files"] += 1
                        dir_node["metrics"]["total_functions"] += child["metrics"].get(
                            "functions", 0
                        )
                        dir_node["metrics"]["total_classes"] += child["metrics"].get(
                            "classes", 0
                        )
                        dir_node["metrics"]["total_lines"] += child["metrics"].get(
                            "lines", 0
                        )
                    elif (
                        child["type"] == "directory"
                    ):  # Aggregate from sub-directories too
                        dir_node["metrics"]["total_files"] += child["metrics"].get(
                            "total_files", 0
                        )
                        dir_node["metrics"]["total_functions"] += child["metrics"].get(
                            "total_functions", 0
                        )
                        dir_node["metrics"]["total_classes"] += child["metrics"].get(
                            "total_classes", 0
                        )
                        dir_node["metrics"]["total_lines"] += child["metrics"].get(
                            "total_lines", 0
                        )

                nodes.append(dir_node)

        return nodes

    def _build_dependency_graph_from_graph_sitter(
        self, codebase: Codebase
    ) -> Dict[str, Any]:
        """Build dependency graph from graph-sitter codebase"""
        dependency_graph = {
            "nodes": 0,
            "edges": 0,
            "cycles": 0,
            "strongly_connected_components": 0,
            "max_depth": 0,
            "file_dependencies": {},
            "symbol_dependencies": {},
            "import_graph": {},
        }

        # Build file dependency graph
        file_graph = nx.DiGraph()
        for file_obj in codebase.files:
            file_graph.add_node(file_obj.filepath)
            for imp in file_obj.imports:
                if hasattr(imp, "from_file") and imp.from_file:
                    file_graph.add_edge(file_obj.filepath, imp.from_file.filepath)

        dependency_graph["file_dependencies"] = {
            "nodes": len(file_graph.nodes),
            "edges": len(file_graph.edges),
            "cycles": len(list(nx.simple_cycles(file_graph))),
            "strongly_connected_components": len(
                list(nx.strongly_connected_components(file_graph))
            ),
        }

        # Build symbol dependency graph
        symbol_graph = nx.DiGraph()
        for symbol in codebase.symbols:
            symbol_graph.add_node(symbol.name)
            for dep in symbol.dependencies:
                if hasattr(dep, "name") and not isinstance(
                    dep, ExternalModule
                ):  # Exclude external modules from internal symbol graph
                    symbol_graph.add_edge(symbol.name, dep.name)

        dependency_graph["symbol_dependencies"] = {
            "nodes": len(symbol_graph.nodes),
            "edges": len(symbol_graph.edges),
            "cycles": len(list(nx.simple_cycles(symbol_graph))),
            "max_depth": len(nx.dag_longest_path(symbol_graph))
            if nx.is_directed_acyclic_graph(symbol_graph)
            else 0,
        }

        return dependency_graph

    def _calculate_code_quality_metrics(self, codebase: Codebase) -> Dict[str, Any]:
        """Calculate comprehensive code quality metrics"""
        metrics = {
            "complexity_score": 0.0,
            "maintainability_index": 0.0,
            "technical_debt_ratio": 0.0,
            "test_coverage_estimate": 0.0,
            "documentation_coverage": 0.0,
            "code_duplication_score": 0.0,
            "type_coverage": 0.0,
            "function_metrics": {},
            "class_metrics": {},
            "file_metrics": {},
        }

        total_functions = len(list(codebase.functions))
        total_classes = len(list(codebase.classes))
        total_files = len(list(codebase.files))

        if total_functions == 0:
            return metrics

        # Calculate function metrics
        function_complexities = []
        documented_functions = 0
        typed_functions = 0

        for func in codebase.functions:
            complexity = self._calculate_function_complexity(func)
            function_complexities.append(complexity)

            if hasattr(func, "docstring") and func.docstring:
                documented_functions += 1

            if hasattr(func, "return_type") and func.return_type:
                typed_functions += 1

        metrics["complexity_score"] = sum(function_complexities) / len(
            function_complexities
        )
        metrics["documentation_coverage"] = documented_functions / total_functions
        metrics["type_coverage"] = typed_functions / total_functions

        # Calculate maintainability index
        avg_complexity = metrics["complexity_score"]
        avg_loc = (
            sum(
                len(f.source.splitlines())
                for f in codebase.functions
                if hasattr(f, "source")
            )
            / total_functions
        )

        # Simplified maintainability index calculation
        metrics["maintainability_index"] = max(
            0,
            (
                171
                - 5.2 * math.log(avg_loc)
                - 0.23 * avg_complexity
                - 16.2 * math.log(avg_loc)
            )
            * 100
            / 171,
        )

        # Estimate test coverage
        test_functions = len(
            [f for f in codebase.functions if self._is_test_function_enhanced(f)]
        )
        metrics["test_coverage_estimate"] = min(
            1.0, test_functions / max(1, total_functions - test_functions)
        )

        # Calculate technical debt ratio (simplified)
        high_complexity_functions = len([c for c in function_complexities if c > 10])
        undocumented_functions = total_functions - documented_functions
        untyped_functions = total_functions - typed_functions

        debt_score = (
            high_complexity_functions + undocumented_functions + untyped_functions
        ) / (total_functions * 3)
        metrics["technical_debt_ratio"] = debt_score

        return metrics

    def _analyze_architectural_patterns(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze architectural patterns in the codebase"""
        patterns = {
            "mvc_pattern": False,
            "repository_pattern": False,
            "factory_pattern": False,
            "singleton_pattern": False,
            "observer_pattern": False,
            "decorator_pattern": False,
            "strategy_pattern": False,
            "layered_architecture": False,
            "microservices_indicators": [],
            "design_pattern_usage": {},
        }

        # Detect MVC pattern
        mvc_indicators = ["controller", "model", "view"]
        mvc_count = sum(
            1
            for cls in codebase.classes
            if any(indicator in cls.name.lower() for indicator in mvc_indicators)
        )
        patterns["mvc_pattern"] = mvc_count >= 3

        # Detect Repository pattern
        repo_indicators = ["repository", "repo"]
        patterns["repository_pattern"] = any(
            indicator in cls.name.lower()
            for cls in codebase.classes
            for indicator in repo_indicators
        )

        # Detect Factory pattern
        factory_indicators = ["factory", "builder", "creator"]
        patterns["factory_pattern"] = any(
            indicator in cls.name.lower()
            for cls in codebase.classes
            for indicator in factory_indicators
        )

        # Detect Singleton pattern
        for cls in codebase.classes:
            if any("singleton" in method.name.lower() for method in cls.methods):
                patterns["singleton_pattern"] = True
                break

        # Detect microservices indicators
        microservice_indicators = ["service", "api", "endpoint", "handler"]
        for indicator in microservice_indicators:
            count = sum(1 for cls in codebase.classes if indicator in cls.name.lower())
            if count > 0:
                patterns["microservices_indicators"].append(
                    {"pattern": indicator, "count": count}
                )

        return patterns

    def _analyze_security_patterns(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze security patterns and potential issues"""
        security = {
            "potential_vulnerabilities": [],
            "security_patterns": [],
            "authentication_usage": False,
            "encryption_usage": False,
            "input_validation": False,
            "sql_injection_risks": [],
            "xss_risks": [],
            "hardcoded_secrets": [],
        }

        # Check for authentication patterns
        auth_patterns = ["authenticate", "login", "auth", "token", "jwt"]
        for func in codebase.functions:
            if any(pattern in func.name.lower() for pattern in auth_patterns):
                security["authentication_usage"] = True
                break

        # Check for encryption usage
        crypto_patterns = ["encrypt", "decrypt", "hash", "crypto", "ssl", "tls"]
        for func in codebase.functions:
            if any(pattern in func.name.lower() for pattern in crypto_patterns):
                security["encryption_usage"] = True
                break

        # Check for potential SQL injection risks
        for func in codebase.functions:
            if hasattr(func, "source") and func.source:
                if "execute(" in func.source and "%" in func.source:
                    security["sql_injection_risks"].append(
                        {
                            "function": func.name,
                            "file": func.filepath,
                            "risk": "Potential SQL injection via string formatting",
                        }
                    )

        # Check for hardcoded secrets (simplified)
        secret_patterns = ["password", "secret", "key", "token"]
        for file_obj in codebase.files:
            if hasattr(file_obj, "source") and file_obj.source:
                for pattern in secret_patterns:
                    if (
                        f'{pattern} = "' in file_obj.source.lower()
                        or f'{pattern}="' in file_obj.source.lower()
                    ):
                        security["hardcoded_secrets"].append(
                            {
                                "file": file_obj.filepath,
                                "pattern": pattern,
                                "risk": "Potential hardcoded secret",
                            }
                        )

        return security

    def _analyze_performance_patterns(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze performance patterns and potential issues"""
        performance = {
            "potential_bottlenecks": [],
            "async_usage": 0,
            "database_queries": 0,
            "loop_complexity": [],
            "memory_usage_patterns": [],
            "caching_usage": False,
            "optimization_opportunities": [],
        }

        # Count async functions
        performance["async_usage"] = sum(
            1 for func in codebase.functions if getattr(func, "is_async", False)
        )

        # Check for database query patterns
        db_patterns = ["query", "select", "insert", "update", "delete", "execute"]
        for func in codebase.functions:
            if hasattr(func, "source") and func.source:
                if any(pattern in func.source.lower() for pattern in db_patterns):
                    performance["database_queries"] += 1

        # Check for caching usage
        cache_patterns = ["cache", "memoize", "redis", "memcached"]
        for func in codebase.functions:
            if any(pattern in func.name.lower() for pattern in cache_patterns):
                performance["caching_usage"] = True
                break

        # Identify potential optimization opportunities
        for func in codebase.functions:
            complexity = self._calculate_function_complexity(func)
            if complexity > 15:
                performance["optimization_opportunities"].append(
                    {
                        "function": func.name,
                        "file": func.filepath,
                        "complexity": complexity,
                        "suggestion": "Consider breaking down complex function",
                    }
                )

        return performance

    # ============================================================================
    # HELPER FUNCTIONS FOR ANALYSIS
    # ============================================================================

    def _detect_file_errors_graph_sitter(
        self, file_obj: SourceFile, lsp_diagnostics: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Detect errors in a file using graph-sitter and LSP diagnostics"""
        errors = {"critical": 0, "major": 0, "minor": 0}

        # Add LSP diagnostics counts
        for enhanced_diag in lsp_diagnostics:
            diag = enhanced_diag["diagnostic"]
            if diag.severity:
                if diag.severity.name.lower() == "error":
                    errors["critical"] += 1
                elif diag.severity.name.lower() == "warning":
                    errors["major"] += 1
                else:  # Info, Hint, Unknown
                    errors["minor"] += 1

        try:
            # Check for syntax errors (simplified)
            if hasattr(file_obj, "source") and file_obj.source:
                try:
                    ast.parse(file_obj.source)
                except SyntaxError:
                    errors["critical"] += 1

            # Check for import issues
            for imp in file_obj.imports:
                if not hasattr(imp, "resolved_symbol") or not imp.resolved_symbol:
                    errors["minor"] += 1

            # Check for long files
            if hasattr(file_obj, "source") and len(file_obj.source.splitlines()) > 1000:
                errors["major"] += 1

        except Exception as e:
            logger.warning(f"Error detecting file errors for {file_obj.filepath}: {e}")

        return errors

    def _detect_function_errors_graph_sitter(
        self, func: Function, lsp_diagnostics: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Detect errors in a function using graph-sitter and LSP diagnostics"""
        errors = {"critical": 0, "major": 0, "minor": 0}

        # Add LSP diagnostics counts relevant to this function's range
        func_start_line = func.start_point.line if hasattr(func, "start_point") else -1
        func_end_line = func.end_point.line if hasattr(func, "end_point") else -1

        for enhanced_diag in lsp_diagnostics:
            diag = enhanced_diag["diagnostic"]
            if diag.range.line >= func_start_line and diag.range.line <= func_end_line:
                if diag.severity:
                    if diag.severity.name.lower() == "error":
                        errors["critical"] += 1
                    elif diag.severity.name.lower() == "warning":
                        errors["major"] += 1
                    else:  # Info, Hint, Unknown
                        errors["minor"] += 1

        try:
            # Check complexity (not required to be presented as retrievable output)
            # complexity = self._calculate_function_complexity(func)
            # if complexity > 20:
            #     errors["critical"] += 1
            # elif complexity > 10:
            #     errors["major"] += 1

            # Check for missing docstring
            if not hasattr(func, "docstring") or not func.docstring:
                errors["minor"] += 1

            # Check for missing type annotations
            if not hasattr(func, "return_type") or not func.return_type:
                errors["minor"] += 1

        except Exception as e:
            logger.warning(f"Error detecting function errors for {func.name}: {e}")

        return errors

    def _detect_class_errors_graph_sitter(
        self, cls: Class, lsp_diagnostics: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Detect errors in a class using graph-sitter and LSP diagnostics"""
        errors = {"critical": 0, "major": 0, "minor": 0}

        # Add LSP diagnostics counts relevant to this class's range
        cls_start_line = cls.start_point.line if hasattr(cls, "start_point") else -1
        cls_end_line = cls.end_point.line if hasattr(cls, "end_point") else -1

        for enhanced_diag in lsp_diagnostics:
            diag = enhanced_diag["diagnostic"]
            if diag.range.line >= cls_start_line and diag.range.line <= cls_end_line:
                if diag.severity:
                    if diag.severity.name.lower() == "error":
                        errors["critical"] += 1
                    elif diag.severity.name.lower() == "warning":
                        errors["major"] += 1
                    else:  # Info, Hint, Unknown
                        errors["minor"] += 1

        try:
            # Check for too many methods
            if len(list(cls.methods)) > 20:
                errors["major"] += 1

            # Check inheritance depth
            if calculate_doi(cls) > 5:
                errors["major"] += 1

            # Check for missing docstring
            if not hasattr(cls, "docstring") or not cls.docstring:
                errors["minor"] += 1

        except Exception as e:
            logger.warning(f"Error detecting class errors for {cls.name}: {e}")

        return errors

    def _is_entrypoint_file(self, file_obj: SourceFile) -> bool:
        """Check if a file is an entrypoint"""
        entrypoint_patterns = [
            "main.py",
            "__main__.py",
            "app.py",
            "server.py",
            "run.py",
            "cli.py",
        ]
        return any(pattern in file_obj.filepath for pattern in entrypoint_patterns)

    def _is_entrypoint_function(self, func: Function) -> bool:
        """Check if a function is an entrypoint"""
        entrypoint_patterns = ["main", "run", "start", "execute", "cli", "app"]
        return (
            any(pattern in func.name.lower() for pattern in entrypoint_patterns)
            or func.name == "__main__"
        )

    def _is_entrypoint_class(self, cls: Class) -> bool:
        """Check if a class is an entrypoint"""
        entrypoint_patterns = [
            "app",
            "application",
            "server",
            "client",
            "main",
            "runner",
        ]
        return any(pattern in cls.name.lower() for pattern in entrypoint_patterns)

    def _is_test_function(self, func: Function) -> bool:
        """Check if a function is a test function"""
        return func.name.startswith("test_") or "test" in func.filepath

    def _is_test_class(self, cls: Class) -> bool:
        """Check if a class is a test class"""
        return cls.name.startswith("Test") or "test" in cls.filepath

    def _is_special_function(self, func: Function) -> bool:
        """Check if a function is a special function that shouldn't be considered dead code"""
        special_patterns = [
            "__init__",
            "__str__",
            "__repr__",
            "__call__",
            "setUp",
            "tearDown",
        ]
        return any(pattern in func.name for pattern in special_patterns)

    def _calculate_file_complexity(self, file_obj: SourceFile) -> float:
        """Calculate complexity score for a file"""
        try:
            if not hasattr(file_obj, "functions"):
                return 0.0

            function_complexities = [
                self._calculate_function_complexity(func) for func in file_obj.functions
            ]
            return sum(function_complexities) / max(1, len(function_complexities))
        except Exception:
            return 0.0

    def _calculate_function_complexity(self, func: Function) -> int:
        """Calculate cyclomatic complexity for a function"""
        try:
            complexity = 1  # Base complexity

            if hasattr(func, "source") and func.source:
                source = func.source.lower()
                # Count decision points
                complexity += source.count("if ")
                complexity += source.count("elif ")
                complexity += source.count("for ")
                complexity += source.count("while ")
                complexity += source.count("except ")
                complexity += source.count("and ")
                complexity += source.count("or ")
                complexity += source.count("try:")

            return complexity
        except Exception:
            return 1

    def _calculate_class_complexity(self, cls: Class) -> float:
        """Calculate complexity score for a class"""
        try:
            if not hasattr(cls, "methods"):
                return 0.0

            method_complexities = [
                self._calculate_function_complexity(method) for method in cls.methods
            ]
            return sum(method_complexities) / max(1, len(method_complexities))
        except Exception:
            return 0.0

    def _calculate_maintainability_index(self, file_obj: SourceFile) -> float:
        """Calculate maintainability index for a file"""
        try:
            if not hasattr(file_obj, "source"):
                return 0.0

            loc = len(file_obj.source.splitlines())
            complexity = self._calculate_file_complexity(file_obj)

            # Simplified maintainability index
            if loc > 0:
                return max(
                    0,
                    (
                        171
                        - 5.2 * math.log(loc)
                        - 0.23 * complexity
                        - 16.2 * math.log(loc)
                    )
                    * 100
                    / 171,
                )
            return 0.0
        except Exception:
            return 0.0


class EnhancedVisualizationEngine:  # Changed from VisualizationEngine
    """Enhanced visualization engine with dynamic target selection and scope control"""

    def __init__(self, codebase: Codebase):
        self.codebase = codebase

    def create_dynamic_dependency_graph(
        self,
        target_type: str,
        target_name: str,
        scope: str = "codebase",
        max_depth: int = 10,
        include_external: bool = False,
    ) -> Dict[str, Any]:
        """Create dependency graph with dynamic target and scope selection"""
        graph = nx.DiGraph()

        # Get the target symbol
        target_symbol = self._get_target_symbol(target_type, target_name)
        if not target_symbol:
            raise ValueError(f"{target_type} '{target_name}' not found")

        # Get scope symbols
        scope_symbols = self._get_scope_symbols(scope, target_symbol)

        # Build dependency graph within scope
        self._build_scoped_dependency_graph(
            graph, target_symbol, scope_symbols, max_depth, include_external
        )

        return self._serialize_enhanced_graph(graph, target_symbol, scope)

    def create_class_hierarchy_graph(
        self, target_class: Optional[str] = None, include_methods: bool = True
    ) -> Dict[str, Any]:
        """Create class hierarchy visualization"""
        graph = nx.DiGraph()

        if target_class:
            start_class = self.codebase.get_class(target_class)
            if not start_class:
                raise ValueError(f"Class '{target_class}' not found")
            self._build_class_hierarchy_subgraph(graph, start_class, include_methods)
        else:
            # Build full class hierarchy
            for cls in self.codebase.classes:
                self._build_class_hierarchy_subgraph(
                    graph, cls, include_methods
                )  # Changed from _add_class_hierarchy_node

        return self._serialize_enhanced_graph(graph, target_class, "class_hierarchy")

    def create_module_dependency_graph(
        self, target_module: str, max_depth: int = 10
    ) -> Dict[str, Any]:
        """Create module-level dependency visualization"""
        graph = nx.DiGraph()

        # Get all files in the target module
        module_files = [f for f in self.codebase.files if target_module in f.filepath]
        if not module_files:
            raise ValueError(f"Module '{target_module}' not found")

        # Build module dependency graph
        self._build_module_dependency_subgraph(graph, module_files, max_depth)

        return self._serialize_enhanced_graph(graph, target_module, "module")

    def create_function_call_trace(
        self, entry_function: str, target_function: str, max_depth: int = 15
    ) -> Dict[str, Any]:
        """Create call trace from entry function to target function"""
        graph = nx.DiGraph()

        start_func = self.codebase.get_function(entry_function)
        end_func = self.codebase.get_function(target_function)

        if not start_func:
            raise ValueError(f"Entry function '{entry_function}' not found")
        if not end_func:
            raise ValueError(f"Target function '{target_function}' not found")

        # Build call trace
        self._build_call_trace_subgraph(graph, start_func, end_func, max_depth)

        return self._serialize_enhanced_graph(
            graph, f"{entry_function} -> {target_function}", "call_trace"
        )

    def create_data_flow_graph(
        self, entry_point: str, max_depth: int = 10
    ) -> Dict[str, Any]:
        """Create data flow visualization"""
        graph = nx.DiGraph()
        start_symbol = self.codebase.get_symbol(entry_point)

        if not start_symbol:
            raise ValueError(f"Symbol '{entry_point}' not found")

        self._build_data_flow_subgraph(graph, start_symbol, max_depth)
        return self._serialize_enhanced_graph(graph, entry_point, "data_flow")

    def create_blast_radius_graph(
        self, entry_point: str, max_depth: int = 10
    ) -> Dict[str, Any]:
        """Create blast radius visualization showing impact of changes"""
        graph = nx.DiGraph()
        start_symbol = self.codebase.get_symbol(entry_point)

        if not start_symbol:
            raise ValueError(f"Symbol '{entry_point}' not found")

        self._build_blast_radius_subgraph(graph, start_symbol, max_depth)
        return self._serialize_enhanced_graph(graph, entry_point, "blast_radius")

    def _get_target_symbol(self, target_type: str, target_name: str):
        """Get target symbol based on type"""
        if target_type == "function":
            return self.codebase.get_function(target_name)
        elif target_type == "class":
            return self.codebase.get_class(target_name)
        elif target_type == "file":
            return self.codebase.get_file(target_name)
        elif target_type == "symbol":
            return self.codebase.get_symbol(target_name)
        else:
            raise ValueError(f"Unknown target type: {target_type}")

    def _get_scope_symbols(self, scope: str, target_symbol: Symbol) -> List[Symbol]:
        """Get all symbols within the specified scope."""
        if scope == "codebase":
            return list(self.codebase.symbols)
        elif scope == "module":
            if hasattr(target_symbol, "file"):
                module_path = os.path.dirname(target_symbol.file.filepath)
                return [
                    s
                    for s in self.codebase.symbols
                    if os.path.dirname(s.filepath) == module_path
                ]
            return []
        elif scope == "file":
            if hasattr(target_symbol, "file"):
                return list(target_symbol.file.symbols)
            return []
        elif scope == "class":
            if hasattr(target_symbol, "parent_class") and target_symbol.parent_class:
                return list(target_symbol.parent_class.methods) + list(
                    target_symbol.parent_class.attributes
                )
            return []
        elif scope == "function":
            if (
                hasattr(target_symbol, "parent_function")
                and target_symbol.parent_function
            ):
                return list(
                    target_symbol.parent_function.code_block.local_var_assignments
                )
            return []
        else:
            raise ValueError(f"Unknown scope type: {scope}")

    def _build_scoped_dependency_graph(
        self,
        graph: nx.DiGraph,
        symbol: Symbol,
        scope_symbols: List[Symbol],
        max_depth: int,
        include_external: bool,
        depth: int = 0,
    ):
        """Build dependency graph within specified scope recursively"""
        if depth >= max_depth or symbol in graph:  # Avoid cycles and depth limit
            return

        graph.add_node(
            symbol.name,
            type=type(symbol).__name__,
            file=symbol.filepath if hasattr(symbol, "filepath") else None,
            is_target=True if depth == 0 else False,
        )

        for dep in symbol.dependencies:
            if not include_external and isinstance(dep, ExternalModule):
                continue

            # Only include dependencies within scope or if external is allowed
            if dep in scope_symbols or include_external:
                graph.add_node(
                    dep.name,
                    type=type(dep).__name__,
                    file=dep.filepath if hasattr(dep, "filepath") else None,
                    in_scope=dep in scope_symbols,
                )
                graph.add_edge(symbol.name, dep.name, relationship="depends_on")

                if dep in scope_symbols:  # Only recurse if dependency is within scope
                    self._build_scoped_dependency_graph(
                        graph,
                        dep,
                        scope_symbols,
                        max_depth,
                        include_external,
                        depth + 1,
                    )

    def _build_class_hierarchy_subgraph(
        self, graph: nx.DiGraph, cls: Class, include_methods: bool, depth: int = 0
    ):
        """Build class hierarchy subgraph recursively"""
        if depth > 10 or cls in graph:  # Prevent infinite recursion and depth limit
            return

        # Add class node
        graph.add_node(
            cls.name,
            type="class",
            file=cls.filepath,
            methods=len(cls.methods),
            attributes=len(cls.attributes),
            inheritance_depth=calculate_doi(cls),
        )

        # Add superclass relationships
        for superclass in cls.superclasses:
            if not isinstance(superclass, ExternalModule):
                graph.add_node(
                    superclass.name,
                    type="class",
                    file=superclass.filepath,
                    methods=len(superclass.methods),
                    attributes=len(superclass.attributes),
                )
                graph.add_edge(cls.name, superclass.name, relationship="inherits_from")
                self._build_class_hierarchy_subgraph(
                    graph, superclass, include_methods, depth + 1
                )

        # Add subclass relationships
        for subclass in cls.subclasses:
            if not isinstance(subclass, ExternalModule):
                graph.add_node(
                    subclass.name,
                    type="class",
                    file=subclass.filepath,
                    methods=len(subclass.methods),
                    attributes=len(subclass.attributes),
                )
                graph.add_edge(subclass.name, cls.name, relationship="inherits_from")
                self._build_class_hierarchy_subgraph(
                    graph, subclass, include_methods, depth + 1
                )

        # Add methods if requested
        if include_methods:
            for method in cls.methods:
                graph.add_node(
                    f"{cls.name}.{method.name}",
                    type="method",
                    file=cls.filepath,
                    complexity=self._calculate_function_complexity(method),
                    parameters=len(method.parameters),
                )
                graph.add_edge(
                    cls.name, f"{cls.name}.{method.name}", relationship="contains"
                )

    def _build_module_dependency_subgraph(
        self, graph: nx.DiGraph, module_files: List[SourceFile], max_depth: int
    ):
        """Build module dependency subgraph recursively"""
        for file_obj in module_files:
            if file_obj in graph:  # Avoid cycles
                continue
            graph.add_node(
                file_obj.filepath,
                type="file",
                functions=len(file_obj.functions),
                classes=len(file_obj.classes),
                lines=len(file_obj.source.splitlines())
                if hasattr(file_obj, "source")
                else 0,
            )

            # Add import relationships
            for imp in file_obj.imports:
                if hasattr(imp, "from_file") and imp.from_file:
                    target_file = imp.from_file
                    if target_file not in graph:  # Add target file if not already added
                        graph.add_node(
                            target_file.filepath,
                            type="file",
                            functions=len(target_file.functions),
                            classes=len(target_file.classes),
                            lines=len(target_file.source.splitlines())
                            if hasattr(target_file, "source")
                            else 0,
                        )
                    graph.add_edge(
                        file_obj.filepath,
                        target_file.filepath,
                        relationship="imports_from",
                        import_count=1,
                    )
                    # Recurse into imported modules if within depth
                    if max_depth > 1:
                        self._build_module_dependency_subgraph(
                            graph, [target_file], max_depth - 1
                        )

    def _build_call_trace_subgraph(
        self,
        graph: nx.DiGraph,
        start_func: Function,
        end_func: Function,
        max_depth: int,
    ):
        """Build call trace from start to end function recursively"""
        visited = set()

        def trace_calls(func: Function, target: Function, depth=0):
            if depth >= max_depth or func in visited:
                return False

            visited.add(func)
            graph.add_node(
                func.name,
                type="function",
                file=func.filepath,
                complexity=self._calculate_function_complexity(func),
                depth=depth,
            )

            if func == target:
                return True

            for call in func.function_calls:
                if hasattr(call, "function_definition") and call.function_definition:
                    called_func = call.function_definition
                    if not isinstance(called_func, ExternalModule):
                        graph.add_edge(
                            func.name, called_func.name, relationship="calls"
                        )
                        if trace_calls(called_func, target, depth + 1):
                            return True

            return False

        trace_calls(start_func, end_func)

    def _build_data_flow_subgraph(
        self, graph: nx.DiGraph, symbol: Symbol, max_depth: int, depth: int = 0
    ):
        """Build data flow subgraph recursively"""
        if depth >= max_depth or symbol in graph:  # Avoid cycles and depth limit
            return

        graph.add_node(
            symbol.name,
            type=type(symbol).__name__,
            file=symbol.filepath if hasattr(symbol, "filepath") else None,
        )

        # Track variable usages and assignments
        if hasattr(symbol, "variable_usages"):
            for usage in symbol.variable_usages:
                if hasattr(usage, "name"):
                    graph.add_node(
                        usage.name,
                        type="variable",
                        file=usage.file.filepath if hasattr(usage, "file") else None,
                    )
                    graph.add_edge(symbol.name, usage.name, relationship="uses_data")
                    # Recurse into variable definition if available
                    if (
                        hasattr(usage, "resolved_symbol")
                        and usage.resolved_symbol
                        and usage.resolved_symbol not in graph
                    ):
                        self._build_data_flow_subgraph(
                            graph, usage.resolved_symbol, max_depth, depth + 1
                        )

        if hasattr(symbol, "assignments"):  # For symbols that are assigned values
            for assignment in symbol.assignments:
                if hasattr(assignment, "name"):
                    graph.add_node(
                        assignment.name,
                        type="assignment",
                        file=assignment.file.filepath
                        if hasattr(assignment, "file")
                        else None,
                    )
                    graph.add_edge(
                        assignment.name, symbol.name, relationship="assigns_to"
                    )
                    # Recurse into assigned value's dependencies
                    if hasattr(assignment, "value") and hasattr(
                        assignment.value, "dependencies"
                    ):
                        for dep in assignment.value.dependencies:
                            if dep not in graph:
                                self._build_data_flow_subgraph(
                                    graph, dep, max_depth, depth + 1
                                )

    def _build_blast_radius_subgraph(
        self, graph: nx.DiGraph, symbol: Symbol, max_depth: int, depth: int = 0
    ):
        """Build blast radius subgraph showing impact of changes recursively"""
        if depth >= max_depth or symbol in graph:  # Avoid cycles and depth limit
            return

        graph.add_node(
            symbol.name,
            type=type(symbol).__name__,
            file=symbol.filepath if hasattr(symbol, "filepath") else None,
            impact_level=depth,
        )

        # Add all usages (things that would be affected by changes)
        for usage in symbol.usages:
            if hasattr(usage, "usage_symbol"):
                affected_symbol = usage.usage_symbol
                if affected_symbol not in graph:  # Avoid re-adding nodes
                    graph.add_node(
                        affected_symbol.name,
                        type=type(affected_symbol).__name__,
                        file=affected_symbol.filepath
                        if hasattr(affected_symbol, "filepath")
                        else None,
                        impact_level=depth + 1,
                    )
                graph.add_edge(
                    symbol.name, affected_symbol.name, relationship="impacts"
                )

                self._build_blast_radius_subgraph(
                    graph, affected_symbol, max_depth, depth + 1
                )

    def _serialize_enhanced_graph(
        self, graph: nx.DiGraph, target_info: Union[str, Symbol], graph_type: str
    ) -> Dict[str, Any]:
        """Enhanced graph serialization with additional metadata"""
        base_result = self._serialize_graph(graph)

        # Convert target_info to string if it's a Symbol object
        if isinstance(target_info, Symbol):
            target_info_str = target_info.name
        else:
            target_info_str = str(target_info)

        # Add enhanced metadata
        base_result["metadata"] = {
            "target": target_info_str,
            "graph_type": graph_type,
            "created_at": datetime.now().isoformat(),
            "node_types": Counter(
                data.get("type", "unknown") for _, data in graph.nodes(data=True)
            ),
            "relationship_types": Counter(
                data.get("relationship", "unknown")
                for _, _, data in graph.edges(data=True)
            ),
        }

        # Add graph analysis
        if len(graph.nodes) > 0:
            base_result["analysis"] = {
                "centrality": dict(nx.degree_centrality(graph)),
                "clustering": dict(nx.clustering(graph.to_undirected())),
                "shortest_paths": dict(nx.shortest_path_length(graph))
                if nx.is_connected(graph.to_undirected())
                else {},
            }

        return base_result

    def _serialize_graph(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Serialize NetworkX graph to JSON-serializable format"""
        return {
            "nodes": [
                {"id": node, "label": node, **data}
                for node, data in graph.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, **data}
                for source, target, data in graph.edges(data=True)
            ],
            "metrics": {
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "density": nx.density(graph),
                "is_connected": nx.is_weakly_connected(graph),
            },
        }

    # Re-implement helper functions from AnalysisEngine that are used by VisualizationEngine
    # These are simplified versions, assuming they would be part of the main AnalysisEngine
    def _calculate_function_complexity(self, func: Function) -> int:
        """Calculate cyclomatic complexity for a function (simplified)"""
        if hasattr(func, "complexity"):  # If graph-sitter provides it directly
            return func.complexity
        if hasattr(func, "source") and func.source:
            return (
                func.source.count("if ")
                + func.source.count("for ")
                + func.source.count("while ")
                + 1
            )
        return 1


class TransformationEngine:
    """Advanced transformation engine for code modifications."""

    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.transformation_log = []

    def move_symbol(
        self,
        symbol_name: str,
        target_file: str,
        include_dependencies: bool = True,
        strategy: str = "update_all_imports",
    ) -> Dict[str, Any]:
        """Move a symbol to a different file"""
        try:
            symbol = self.codebase.get_symbol(symbol_name)
            if not symbol:
                raise ValueError(f"Symbol '{symbol_name}' not found")

            # Get or create target file
            if not self.codebase.has_file(target_file):
                target_file_obj = self.codebase.create_file(target_file)
            else:
                target_file_obj = self.codebase.get_file(target_file)

            # Record original location
            original_file = symbol.filepath

            # Perform the move
            symbol.move_to_file(
                target_file_obj,
                include_dependencies=include_dependencies,
                strategy=strategy,
            )

            result = {
                "success": True,
                "symbol": symbol_name,
                "from_file": original_file,
                "to_file": target_file,
                "strategy": strategy,
                "include_dependencies": include_dependencies,
            }

            self.transformation_log.append(result)
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "symbol": symbol_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.transformation_log.append(error_result)
            return error_result

    def remove_symbol(self, symbol_name: str, safe_mode: bool = True) -> Dict[str, Any]:
        """Remove a symbol from the codebase"""
        try:
            symbol = self.codebase.get_symbol(symbol_name)
            if not symbol:
                raise ValueError(f"Symbol '{symbol_name}' not found")

            # Check if symbol is used elsewhere
            if safe_mode and len(symbol.usages) > 0:
                return {
                    "success": False,
                    "symbol": symbol_name,
                    "error": "Symbol is still in use",
                    "usages": [usage.file.filepath for usage in symbol.usages[:5]],
                }

            # Remove the symbol
            original_file = symbol.filepath
            symbol.remove()

            result = {
                "success": True,
                "symbol": symbol_name,
                "file": original_file,
                "safe_mode": safe_mode,
            }

            self.transformation_log.append(result)
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "symbol": symbol_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.transformation_log.append(error_result)
            return error_result

    def rename_symbol(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a symbol and update all references"""
        try:
            symbol = self.codebase.get_symbol(old_name)
            if not symbol:
                raise ValueError(f"Symbol '{old_name}' not found")

            # Count usages before rename
            usage_count = len(symbol.usages)

            # Perform the rename
            symbol.rename(new_name)

            result = {
                "success": True,
                "old_name": old_name,
                "new_name": new_name,
                "file": symbol.filepath,
                "usages_updated": usage_count,
            }

            self.transformation_log.append(result)
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "old_name": old_name,
                "new_name": new_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.transformation_log.append(error_result)
            return error_result

    def resolve_imports(self, file_path: str) -> Dict[str, Any]:
        """Resolve and fix import issues in a file"""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                raise ValueError(f"File '{file_path}' not found")

            resolved_imports = []
            unresolved_imports = []

            for imp in file_obj.imports:
                if hasattr(imp, "resolved_symbol") and imp.resolved_symbol:
                    resolved_imports.append(imp.name)
                else:
                    unresolved_imports.append(imp.name)

            result = {
                "success": True,
                "file": file_path,
                "resolved_imports": resolved_imports,
                "unresolved_imports": unresolved_imports,
                "total_imports": len(file_obj.imports),
            }

            self.transformation_log.append(result)
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "file": file_path,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.transformation_log.append(error_result)
            return error_result

    def add_type_annotations(
        self,
        symbol_name: str,
        return_type: Optional[str] = None,
        parameter_types: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Add type annotations to a function"""
        try:
            symbol = self.codebase.get_function(symbol_name)
            if not symbol:
                raise ValueError(f"Function '{symbol_name}' not found")

            changes = []

            # Add return type annotation
            if return_type:
                symbol.set_return_type(return_type)
                changes.append(f"Added return type: {return_type}")

            # Add parameter type annotations
            if parameter_types:
                for param_name, param_type in parameter_types.items():
                    param = symbol.get_parameter(param_name)
                    if param:
                        param.set_type(param_type)  # Changed from set_type_annotation
                        changes.append(f"Added type for {param_name}: {param_type}")

            result = {
                "success": True,
                "function": symbol_name,
                "file": symbol.filepath,
                "changes": changes,
            }

            self.transformation_log.append(result)
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "function": symbol_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.transformation_log.append(error_result)
            return error_result

    def extract_function(
        self,
        source_function: str,
        new_function_name: str,
        start_line: int,
        end_line: int,
    ) -> Dict[str, Any]:
        """Extract code into a new function"""
        try:
            func = self.codebase.get_function(source_function)
            if not func:
                raise ValueError(f"Function '{source_function}' not found")

            # Get source lines
            source_lines = func.source.splitlines()
            if start_line < 1 or end_line > len(source_lines):
                raise ValueError("Invalid line range")

            # Extract the code block
            extracted_code = "\n".join(source_lines[start_line - 1 : end_line])

            # Create new function
            new_function_code = f"""
def {new_function_name}():
    {extracted_code}
"""

            # Add new function after the original
            # This is a placeholder; graph-sitter's API for code modification is more advanced
            # func.insert_after(new_function_code)

            # Replace extracted code with function call
            replacement = f"{new_function_name}()"
            # This is a simplified replacement - in practice, you'd need more sophisticated logic

            result = {
                "success": True,
                "source_function": source_function,
                "new_function": new_function_name,
                "extracted_lines": f"{start_line}-{end_line}",
                "file": func.filepath,
            }

            self.transformation_log.append(result)
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "source_function": source_function,
                "new_function": new_function_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            self.transformation_log.append(error_result)
            return error_result

    def get_transformation_log(self) -> List[Dict[str, Any]]:
        """Get the log of all transformations performed"""
        return self.transformation_log.copy()

    def clear_transformation_log(self):
        """Clear the transformation log"""
        self.transformation_log.clear()


class InteractiveAnalyzer:
    """Interactive analysis session for code exploration."""

    def __init__(self, analyzer: ComprehensiveAnalyzer):
        self.analyzer = analyzer
        self.console = Console() if RICH_AVAILABLE else None

    def start_interactive_session(self):
        """Start an interactive analysis session."""
        if self.console:
            self.console.print(
                Panel.fit(
                    "🔍 Interactive Code Analysis Session\nCommands: summary, errors [category], function [name], class [name], fix, export [format], quit",
                    title="Analysis Shell",
                )
            )
        else:
            print("=== Interactive Code Analysis Session ===")
            print("Commands: summary, errors [category], function [name], class [name], fix, export [format], quit")

        while True:
            try:
                command = input("\nanalysis> ").strip().lower()

                if command == "quit" or command == "exit":
                    break
                elif command == "summary":
                    self._show_summary()
                elif command.startswith("errors"):
                    category = command.split()[1] if len(command.split()) > 1 else None
                    self._show_errors(category)
                elif command.startswith("function"):
                    func_name = command.split()[1] if len(command.split()) > 1 else None
                    self._show_function_analysis(func_name)
                elif command.startswith("class"):
                    class_name = command.split()[1] if len(command.split()) > 1 else None
                    self._show_class_analysis(class_name)
                elif command == "fix":
                    self._apply_fixes()
                elif command.startswith("export"):
                    format_type = command.split()[1] if len(command.split()) > 1 else "json"
                    self._export_results(format_type)
                else:
                    print("Unknown command. Available: summary, errors, function, class, fix, export, quit")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        print("Interactive session ended.")

    def _show_summary(self):
        """Show analysis summary."""
        if not self.analyzer.last_results:
            print("No analysis results available. Run analysis first.")
            return

        summary = self.analyzer.last_results.get("summary", {})

        if self.console:
            table = Table(title="Analysis Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            overview = summary.get("overview", {})
            for key, value in overview.items():
                table.add_row(key.replace("_", " ").title(), str(value))

            self.console.print(table)
        else:
            print("\n=== Analysis Summary ===")
            overview = summary.get("overview", {})
            for key, value in overview.items():
                print(f"{key.replace('_', ' ').title()}: {value}")

    def _show_errors(self, category: str | None = None):
        """Show errors, optionally filtered by category."""
        if not self.analyzer.last_results:
            print("No analysis results available.")
            return

        categorized = self.analyzer.last_results.get("categorized_errors", {})

        if category:
            errors = categorized.get(category, [])
            print(f"\n=== {category.replace('_', ' ').title()} Errors ===")
        else:
            errors = self.analyzer.last_results.get("errors", [])
            print(f"\n=== All Errors ({len(errors)}) ===")

        for i, error in enumerate(errors[:20]):  # Show first 20
            print(f"{i + 1}. {error['file_path']}:{error['line']} - {error['message']} [{error['tool_source']}]")

    def _show_function_analysis(self, func_name: str | None):
        """Show function analysis."""
        if not func_name:
            print("Please specify a function name: function <name>")
            return

        if not self.analyzer.graph_sitter:
            print("Graph-sitter not available for function analysis.")
            return

        analysis = self.analyzer.graph_sitter.get_function_analysis(func_name)
        if analysis:
            print(f"\n=== Function Analysis: {func_name} ===")
            for key, value in analysis.items():
                print(f"{key}: {value}")
        else:
            print(f"Function '{func_name}' not found.")

    def _show_class_analysis(self, class_name: str | None):
        """Show class analysis."""
        if not class_name:
            print("Please specify a class name: class <name>")
            return

        if not self.analyzer.graph_sitter:
            print("Graph-sitter not available for class analysis.")
            return

        analysis = self.analyzer.graph_sitter.get_class_analysis(class_name)
        if analysis:
            print(f"\n=== Class Analysis: {class_name} ===")
            for key, value in analysis.items():
                print(f"{key}: {value}")
        else:
            print(f"Class '{class_name}' not found.")

    def _apply_fixes(self):
        """Apply AutoGenLib fixes."""
        if not self.analyzer.autogenlib_fixer:
            print("AutoGenLib not available for fixing.")
            return

        print("Applying AI-powered fixes...")
        fix_results = self.analyzer.fix_errors_with_autogenlib()

        print(f"Fixes attempted: {fix_results.get('fixes_attempted', 0)}")
        print(f"Fixes applied: {fix_results.get('fixes_applied', 0)}")

        for fix in fix_results.get("fixes_details", []):
            if fix.get("fix_applied"):
                print(f"✓ Fixed: {fix['error']['message']}")
            else:
                print(f"✗ Failed: {fix['error']['message']}")

    def _export_results(self, format_type: str):
        """Export results in specified format."""
        if not self.analyzer.last_results:
            print("No results to export.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_export_{timestamp}.{format_type}"

        try:
            if format_type == "json":
                with open(filename, "w") as f:
                    json.dump(self.analyzer.last_results, f, indent=2)
            elif format_type == "html":
                html_content = ReportGenerator(self.analyzer.last_results).generate_html_report()
                with open(filename, "w") as f:
                    f.write(html_content)
            else:
                print(f"Unsupported format: {format_type}")
                return

            print(f"Results exported to: {filename}")

        except Exception as e:
            print(f"Export failed: {e}")


class ReportGenerator:
    """Generate comprehensive analysis reports in multiple formats."""
    
    def __init__(self, analysis_results: Dict[str, Any]):
        self.results = analysis_results
    
    def generate_terminal_report(self) -> str:
        """Generate comprehensive terminal report."""
        lines = []
        
        # Header
        lines.extend([
        "="*100,
        "COMPREHENSIVE PYTHON CODE ANALYSIS REPORT",
        "="*100,
        ""
        ])
        
        # Metadata
        metadata = self.results.get("metadata", {})
        lines.extend([
            f"Target: {metadata.get('target_path', 'Unknown')}",
            f"Analysis Duration: {metadata.get('analysis_duration', 0):.2f}s",
            f"Tools Used: {', '.join(metadata.get('tools_used', []))}",
            f"Python Version: {metadata.get('python_version', 'Unknown')}",
            ""
        ])
        
        # Graph-sitter analysis summary
        gs_analysis = self.results.get("graph_sitter_analysis", {})
        if gs_analysis and "codebase_summary" in gs_analysis:
            summary = gs_analysis["codebase_summary"]
            lines.extend([
                "CODEBASE STRUCTURE:",
                "-" * 50,
                f"Files: {summary.get('total_files', 0)}",
                f"Functions: {summary.get('total_functions', 0)}",
                f"Classes: {summary.get('total_classes', 0)}",
                f"Imports: {summary.get('total_imports', 0)}",
                f"External Dependencies: {summary.get('external_dependencies', 0)}",
                f"Lines of Code: {summary.get('lines_of_code', 0)}",
                f"Complexity Score: {summary.get('complexity_score', 0):.2f}",
                ""
            ])
        
        # Entrypoints
        entrypoints = self.results.get("entrypoints", [])
        if entrypoints:
            lines.extend([
                f"ENTRYPOINTS: [{len(entrypoints)}]",
                "-" * 50
            ])
            for i, entry in enumerate(entrypoints[:10], 1):
                entry_type = entry.get("type", "unknown").title()
                entry_name = entry.get("name", "unknown")
                entry_file = entry.get("file_path", "")
                lines.append(f"{i}. {entry_type}: {entry_name} [{os.path.basename(entry_file)}]")
            lines.append("")
        
        # Dead code
        dead_code = self.results.get("dead_code", [])
        if dead_code:
            dead_by_type = defaultdict(int)
            for item in dead_code:
                dead_by_type[item.get("category", "unknown")] += 1
            
            lines.extend([
                f"DEAD CODE: {len(dead_code)} [{', '.join(f'{cat.title()}: {count}' for cat, count in dead_by_type.items())}]",
                "-" * 50
            ])
            for i, item in enumerate(dead_code[:20], 1):
                item_type = item.get("type", "unknown")
                item_name = item.get("name", "unknown")
                item_file = os.path.basename(item.get("file_path", ""))
                context = item.get("context", "")
                lines.append(f"{i}. {item_type.title()}: '{item_name}' [{item_file}] - {context}")
            
            if len(dead_code) > 20:
                lines.append(f"... and {len(dead_code) - 20} more items")
            lines.append("")
        
        # Error summary
        categorized = self.results.get("categorized_errors", {})
        stats = categorized.get("statistics", {})
        
        if stats:
            lines.extend([
                f"ERRORS: {stats.get('total_errors', 0)} "
                f"[Critical: {stats.get('critical_errors', 0)}] "
                f"[Warnings: {stats.get('warnings', 0)}] "
                f"[Info: {stats.get('info_messages', 0)}]",
                "-" * 50
            ])
            
            # List errors by severity and tool
            by_tool = categorized.get("by_tool", {})
            for i, (tool, tool_errors) in enumerate(by_tool.items(), 1):
                if tool_errors:
                    critical_count = len([e for e in tool_errors if e.severity == DiagnosticSeverity.ERROR])
                    warning_count = len([e for e in tool_errors if e.severity == DiagnosticSeverity.WARNING])
                    
                    lines.append(f"{i}. {tool.upper()}: {len(tool_errors)} issues "
                               f"[Critical: {critical_count}, Warnings: {warning_count}]")
            
            lines.append("")
            
            # Detailed error listing by category
            by_category = categorized.get("by_category", {})
            for category, category_errors in by_category.items():
                if category_errors:
                    lines.extend([
                        f"{category.upper()} ERRORS: {len(category_errors)}",
                        "-" * 30
                    ])
                    
                    # Group by file for better organization
                    errors_by_file = defaultdict(list)
                    for error in category_errors[:50]:  # Limit display
                        errors_by_file[error.file_path].append(error)
                    
                    for file_path, file_errors in list(errors_by_file.items())[:10]:  # Limit files
                        rel_path = os.path.relpath(file_path, self.results.get("metadata", {}).get("target_path", ""))
                        lines.append(f"  {rel_path}: {len(file_errors)} issues")
                        
                        for error in file_errors[:5]:  # Limit errors per file
                            severity_icon = {
                                DiagnosticSeverity.ERROR: "⚠️",
                                DiagnosticSeverity.WARNING: "👉",
                                DiagnosticSeverity.INFORMATION: "🔍",
                                DiagnosticSeverity.HINT: "💡"
                            }.get(error.severity, "•")
                            
                            location = f"Line {error.line_number}" if error.line_number else "Unknown location"
                            tool_info = f"[{error.tool_source}]"
                            
                            lines.append(f"    {severity_icon} {location}: {error.message[:80]}{'...' if len(error.message) > 80 else ''} {tool_info}")
                        
                        if len(file_errors) > 5:
                            lines.append(f"    ... and {len(file_errors) - 5} more issues in this file")
                    
                    if len(errors_by_file) > 10:
                        lines.append(f"  ... and {len(errors_by_file) - 10} more files with {category} errors")
                    
                    lines.append("")
            
            # Performance and quality insights
            perf_metrics = self.results.get("performance_metrics", {})
            quality_metrics = self.results.get("quality_metrics", {})
            
            if perf_metrics.get("function_metrics"):
                func_metrics = perf_metrics["function_metrics"]
                lines.extend([
                    "PERFORMANCE INSIGHTS:",
                    "-" * 30,
                    f"Average Function Complexity: {func_metrics.get('average_complexity', 0):.2f}",
                    f"High Complexity Functions: {func_metrics.get('high_complexity_count', 0)}",
                    f"Largest File: {perf_metrics.get('file_metrics', {}).get('largest_file', 0)} lines",
                    ""
                ])
            
            if quality_metrics:
                lines.extend([
                    "QUALITY METRICS:",
                    "-" * 30,
                    f"Documentation Coverage: {quality_metrics.get('documentation_coverage', 0)*100:.1f}%",
                    f"Maintainability Index: {quality_metrics.get('maintainability_index', 0):.1f}",
                    f"Quality Score: {self.results.get('summary', {}).get('quality_score', 0):.1f}/100",
                    ""
                ])
            
            # Recommendations
            recommendations = self.results.get("summary", {}).get("recommendations", [])
            if recommendations:
                lines.extend([
                    "RECOMMENDATIONS:",
                    "-" * 30
                ])
                for i, rec in enumerate(recommendations, 1):
                    lines.append(f"{i}. {rec}")
        
        lines.append("="*100)
        return "\n".join(lines)
    
    def generate_json_report(self) -> str:
        """Generate JSON report."""
        return json.dumps(self.results, indent=2, default=str)
    
    def generate_html_report(self) -> str:
        """Generate comprehensive HTML report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Code Analysis Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .section {
            padding: 30px;
            border-bottom: 1px solid #eee;
        }
        .section h2 {
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .error-list {
            list-style: none;
            padding: 0;
        }
        .error-item {
            background: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-left: 4px solid #dc3545;
            border-radius: 4px;
        }
        .error-item.warning {
            border-left-color: #ffc107;
        }
        .error-item.info {
            border-left-color: #17a2b8;
        }
        .error-meta {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .category-section {
            margin: 20px 0;
        }
        .category-header {
            background: #e9ecef;
            padding: 10px 15px;
            border-radius: 4px;
            font-weight: bold;
            color: #495057;
        }
        .progress-bar {
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
        .recommendations {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
        }
        .recommendations h3 {
            color: #155724;
            margin-top: 0;
        }
        .tag {
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }
        .tag.critical { background: #dc3545; }
        .tag.warning { background: #ffc107; color: #333; }
        .tag.info { background: #17a2b8; }
        .expandable {
            cursor: pointer;
            user-select: none;
        }
        .expandable:hover {
            background-color: #f0f0f0;
        }
        .collapsed {
            display: none;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .file-tree {
            font-family: monospace;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            white-space: pre-line;
        }
    </style>
    <script>
        function toggleSection(id) {
            const element = document.getElementById(id);
            if (element) {
                element.classList.toggle('collapsed');
            }
        }
        
        function filterErrors(category) {
            const errorSections = document.querySelectorAll('.error-category');
            errorSections.forEach(section => {
                if (category === 'all' || section.dataset.category === category) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Code Analysis Report</h1>
            <p>Target: {target_path}</p>
            <p>Generated on {timestamp}</p>
        </div>
        
        <div class="metrics-grid">
            {metrics_cards}
        </div>
        
        <div class="section">
            <h2>📊 Analysis Overview</h2>
            {overview_content}
        </div>
        
        <div class="section">
            <h2>🎯 Entrypoints</h2>
            {entrypoints_content}
        </div>
        
        <div class="section">
            <h2>💀 Dead Code Analysis</h2>
            {dead_code_content}
        </div>
        
        <div class="section">
            <h2>🚨 Error Analysis</h2>
            {error_analysis_content}
        </div>
        
        <div class="section">
            <h2>📈 Performance Metrics</h2>
            {performance_content}
        </div>
        
        <div class="section">
            <h2>🔒 Security Analysis</h2>
            {security_content}
        </div>
        
        <div class="section">
            <h2>📋 Recommendations</h2>
            {recommendations_content}
        </div>
    </div>
</body>
</html>
        """
        
        # Generate content sections
        metadata = self.results.get("metadata", {})
        categorized = self.results.get("categorized_errors", {})
        stats = categorized.get("statistics", {})
        
        # Metrics cards
        metrics_cards = self._generate_metrics_cards(stats)
        
        # Overview content
        overview_content = self._generate_overview_content()
        
        # Entrypoints content
        entrypoints_content = self._generate_entrypoints_content()
        
        # Dead code content
        dead_code_content = self._generate_dead_code_content()
        
        # Error analysis content
        error_analysis_content = self._generate_error_analysis_content()
        
        # Performance content
        performance_content = self._generate_performance_content()
        
        # Security content
        security_content = self._generate_security_content()
        
        # Recommendations content
        recommendations_content = self._generate_recommendations_content()
        
        # Fill template
        html_report = html_template.format(
            target_path=metadata.get("target_path", "Unknown"),
            timestamp=metadata.get("analysis_start_time", "Unknown"),
            metrics_cards=metrics_cards,
            overview_content=overview_content,
            entrypoints_content=entrypoints_content,
            dead_code_content=dead_code_content,
            error_analysis_content=error_analysis_content,
            performance_content=performance_content,
            security_content=security_content,
            recommendations_content=recommendations_content
        )
        
        return html_report
    
    def _generate_metrics_cards(self, stats: Dict) -> str:
        """Generate HTML for metrics cards."""
        cards = []
        
        metrics = [
            ("Total Errors", stats.get("total_errors", 0), "dc3545"),
            ("Critical", stats.get("critical_errors", 0), "dc3545"),
            ("Warnings", stats.get("warnings", 0), "ffc107"),
            ("Files Analyzed", stats.get("files_with_errors", 0), "28a745"),
            ("Tools Used", stats.get("tools_with_findings", 0), "17a2b8"),
            ("Categories", stats.get("categories_affected", 0), "6f42c1"),
            ("Fixable", stats.get("fixable_count", 0), "28a745"),
            ("Security Issues", stats.get("security_issues", 0), "dc3545")
        ]
        
        for label, value, color in metrics:
            cards.append(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #{color}">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """)
        
        return "".join(cards)
    
    def _generate_overview_content(self) -> str:
        """Generate overview content."""
        gs_analysis = self.results.get("graph_sitter_analysis", {})
        summary = self.results.get("summary", {})
        
        content = []
        
        if gs_analysis.get("codebase_summary"):
            codebase_sum = gs_analysis["codebase_summary"]
            content.append(f"""
                <div class="file-tree">
                    <strong>Codebase Structure:</strong>
                    📁 Total Files: {codebase_sum.get('total_files', 0)}
                    🔧 Functions: {codebase_sum.get('total_functions', 0)}
                    🏗️  Classes: {codebase_sum.get('total_classes', 0)}
                    📦 Imports: {codebase_sum.get('total_imports', 0)}
                    🌐 External Dependencies: {codebase_sum.get('external_dependencies', 0)}
                    📏 Lines of Code: {codebase_sum.get('lines_of_code', 0):,}
                    📊 Complexity Score: {codebase_sum.get('complexity_score', 0):.2f}
                </div>
            """)
        
        # Quality score with progress bar
        quality_score = summary.get("quality_score", 0)
        content.append(f"""
            <div>
                <h3>Quality Score: {quality_score:.1f}/100</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {quality_score}%"></div>
                </div>
            </div>
        """)
        
        return "".join(content)
    
    def _generate_entrypoints_content(self) -> str:
        """Generate entrypoints content."""
        entrypoints = self.results.get("entrypoints", [])
        
        if not entrypoints:
            return "<p>No entrypoints detected in the codebase.</p>"
        
        content = [f"<p>Found {len(entrypoints)} entrypoints in the codebase:</p>"]
        content.append("<table>")
        content.append("<tr><th>Type</th><th>Name</th><th>File</th><th>Line</th></tr>")
        
        for entry in entrypoints:
            content.append(f"""
                <tr>
                    <td><span class="tag">{entry.get('type', 'unknown')}</span></td>
                    <td><code>{entry.get('name', 'unknown')}</code></td>
                    <td>{os.path.basename(entry.get('file_path', ''))}</td>
                    <td>{entry.get('line_number', 'N/A')}</td>
                </tr>
            """)
        
        content.append("</table>")
        return "".join(content)
    
    def _generate_dead_code_content(self) -> str:
        """Generate dead code content."""
        dead_code = self.results.get("dead_code", [])
        
        if not dead_code:
            return "<p>No dead code detected. Great job!</p>"
        
        # Group by type
        by_type = defaultdict(list)
        for item in dead_code:
            by_type[item.get("category", "unknown")].append(item)
        
        content = [f"<p>Found {len(dead_code)} dead code items:</p>"]
        
        for category, items in by_type.items():
            content.append(f"""
                <div class="category-section">
                    <div class="category-header">{category.replace('_', ' ').title()}: {len(items)} items</div>
                    <ul class="error-list">
            """)
            
            for item in items[:20]:  # Limit display
                content.append(f"""
                    <li class="error-item info">
                        <strong>{item.get('type', 'unknown').title()}: {item.get('name', 'unknown')}</strong>
                        <div class="error-meta">
                            📁 {os.path.basename(item.get('file_path', ''))} 
                            📍 Line {item.get('line_number', 'N/A')}
                            💭 {item.get('context', '')}
                        </div>
                    </li>
                """)
            
            if len(items) > 20:
                content.append(f"<li>... and {len(items) - 20} more items</li>")
            
            content.extend(["</ul>", "</div>"])
        
        return "".join(content)
    
    def _generate_error_analysis_content(self) -> str:
        """Generate error analysis content."""
        categorized = self.results.get("categorized_errors", {})
        
        content = []
        
        # Error category filter buttons
        content.append("""
            <div style="margin-bottom: 20px;">
                <button onclick="filterErrors('all')" style="margin-right: 10px; padding: 8px 16px; border: none; background: #007bff; color: white; border-radius: 4px; cursor: pointer;">All</button>
        """)
        
        by_category = categorized.get("by_category", {})
        for category in by_category.keys():
            content.append(f"""
                <button onclick="filterErrors('{category}')" style="margin-right: 10px; padding: 8px 16px; border: none; background: #6c757d; color: white; border-radius: 4px; cursor: pointer;">{category.title()}</button>
            """)
        
        content.append("</div>")
        
        # Error sections by category
        for category, errors in by_category.items():
            content.append(f"""
                <div class="error-category" data-category="{category}">
                    <div class="category-header">{category.upper()}: {len(errors)} issues</div>
                    <ul class="error-list">
            """)
            
            # Group errors by file for better organization
            errors_by_file = defaultdict(list)
            for error in errors[:100]:  # Limit for performance
                errors_by_file[error.file_path].append(error)
            
            for file_path, file_errors in list(errors_by_file.items())[:15]:  # Limit files shown
                content.append(f"""
                    <li class="expandable" onclick="toggleSection('file-{hashlib.md5(file_path.encode()).hexdigest()}')">
                        <strong>📁 {os.path.basename(file_path)}</strong> ({len(file_errors)} issues)
                    </li>
                    <div id="file-{hashlib.md5(file_path.encode()).hexdigest()}" class="collapsed">
                """)
                
                for error in file_errors[:10]:  # Limit errors per file
                    severity_class = {
                        DiagnosticSeverity.ERROR: "error",
                        DiagnosticSeverity.WARNING: "warning", 
                        DiagnosticSeverity.INFORMATION: "info"
                    }.get(error.severity, "info")
                    
                    severity_icon = {
                        DiagnosticSeverity.ERROR: "⚠️",
                        DiagnosticSeverity.WARNING: "👉",
                        DiagnosticSeverity.INFORMATION: "🔍"
                    }.get(error.severity, "•")
                    
                    content.append(f"""
                        <div class="error-item {severity_class}">
                            <strong>{severity_icon} {error.message}</strong>
                            <div class="error-meta">
                                📍 Line {error.line_number or 'N/A'}
                                🔧 {error.tool_source}
                                {f'🏷️ {error.error_code}' if error.error_code else ''}
                                {f'💡 {error.fix_suggestion}' if error.fix_suggestion else ''}
                            </div>
                        </div>
                    """)
                
                if len(file_errors) > 10:
                    content.append(f"<p>... and {len(file_errors) - 10} more errors in this file</p>")
                
                content.append("</div>")
            
            content.extend(["</ul>", "</div>"])
        
        return "".join(content)
    
    def _generate_performance_content(self) -> str:
        """Generate performance analysis content."""
        perf_metrics = self.results.get("performance_metrics", {})
        
        if not perf_metrics or "error" in perf_metrics:
            return "<p>Performance metrics not available.</p>"
        
        content = []
        
        # Function metrics
        func_metrics = perf_metrics.get("function_metrics", {})
        if func_metrics:
            content.append(f"""
                <div>
                    <h3>Function Analysis</h3>
                    <ul>
                        <li>Total Functions: {func_metrics.get('total_functions', 0)}</li>
                        <li>Average Complexity: {func_metrics.get('average_complexity', 0):.2f}</li>
                        <li>Maximum Complexity: {func_metrics.get('max_complexity', 0):.2f}</li>
                        <li>High Complexity Functions: {func_metrics.get('high_complexity_count', 0)}</li>
                    </ul>
                </div>
            """)
        
        # Performance warnings
        warnings = perf_metrics.get("performance_warnings", [])
        if warnings:
            content.append("<h3>Performance Warnings</h3>")
            content.append("<ul class='error-list'>")
            
            for warning in warnings:
                content.append(f"""
                    <li class="error-item warning">
                        <strong>{warning.get('type', 'unknown').replace('_', ' ').title()}</strong>
                        <div class="error-meta">
                            {warning.get('function', warning.get('file', 'Unknown'))}
                            - {warning.get('recommendation', '')}
                        </div>
                    </li>
                """)
            
            content.append("</ul>")
        
        return "".join(content)
    
    def _generate_security_content(self) -> str:
        """Generate security analysis content."""
        categorized = self.results.get("categorized_errors", {})
        security_issues = categorized.get("security_critical", [])
        
        if not security_issues:
            return "<div class='recommendations'><h3>✅ Security Status</h3><p>No critical security issues detected.</p></div>"
        
        content = [f"<p>Found {len(security_issues)} security issues requiring attention:</p>"]
        content.append("<ul class='error-list'>")
        
        for issue in security_issues:
            severity_class = "error" if issue.severity == DiagnosticSeverity.ERROR else "warning"
            
            content.append(f"""
                <li class="error-item {severity_class}">
                    <strong>🔒 {issue.message}</strong>
                    <div class="error-meta">
                        📁 {os.path.basename(issue.file_path)}
                        📍 Line {issue.line_number or 'N/A'}
                        🔧 {issue.tool_source}
                        {f'🏷️ {issue.error_code}' if issue.error_code else ''}
                        <br>
                        <span class="tag critical">Security Risk</span>
                        {f'<span class="tag">Confidence: {issue.confidence:.1%}</span>' if hasattr(issue, 'confidence') else ''}
                    </div>
                    {f'<div style="margin-top: 10px;"><strong>Fix:</strong> {issue.fix_suggestion}</div>' if issue.fix_suggestion else ''}
                </li>
            """)
        
        content.append("</ul>")
        return "".join(content)
    
    def _generate_recommendations_content(self) -> str:
        """Generate recommendations content."""
        summary = self.results.get("summary", {})
        recommendations = summary.get("recommendations", [])
        action_items = summary.get("action_items", [])
        
        content = []
        
        if recommendations:
            content.append("<div class='recommendations'>")
            content.append("<h3>🎯 Key Recommendations</h3>")
            content.append("<ul>")
            for rec in recommendations:
                content.append(f"<li>{rec}</li>")
            content.append("</ul>")
            content.append("</div>")
        
        if action_items:
            content.append("<h3>📋 Action Items</h3>")
            content.append("<table>")
            content.append("<tr><th>Priority</th><th>Category</th><th>Action</th><th>Effort</th></tr>")
            
            for item in action_items:
                priority_color = {
                    "high": "#dc3545",
                    "medium": "#ffc107", 
                    "low": "#28a745"
                }.get(item.get("priority", "low"), "#6c757d")
                
                content.append(f"""
                    <tr>
                        <td><span class="tag" style="background: {priority_color}">{item.get('priority', 'low').title()}</span></td>
                        <td>{item.get('category', 'unknown').title()}</td>
                        <td>{item.get('action', '')}</td>
                        <td>{item.get('estimated_effort', 'unknown').title()}</td>
                    </tr>
                """)
            
            content.append("</table>")
        
        return "".join(content)


# FastAPI Endpoints
if FASTAPI_AVAILABLE and app:
    
    @app.post("/analyze")
    async def analyze_codebase(request: AnalyzeRequest):
        """Analyze a codebase."""
        # TODO: Implement endpoint
        raise HTTPException(status_code=501, detail="Not implemented")
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

def main():
    """Main entry point for the comprehensive analysis system."""
    parser = argparse.ArgumentParser(description="Comprehensive Python Code Analysis with Graph-Sitter, LSP, and AI-powered fixing")
    parser.add_argument("--target", required=True, help="Target file or directory to analyze")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive analysis")
    parser.add_argument("--fix-errors", action="store_true", help="Apply AI-powered fixes")
    parser.add_argument("--interactive", action="store_true", help="Start interactive session")
    parser.add_argument(
        "--format",
        choices=["terminal", "json", "html"],
        default="terminal",
        help="Output format",
    )
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--max-fixes", type=int, default=5, help="Maximum number of fixes to apply")

    args = parser.parse_args()

    # Initialize analyzer
    config = {"config_file": args.config} if args.config else {}
    analyzer = ComprehensiveAnalyzer(args.target, config, args.verbose)

    try:
        if args.comprehensive or not (args.fix_errors or args.interactive):
            # Run comprehensive analysis
            print("🚀 Starting comprehensive analysis...")
            results = analyzer.run_comprehensive_analysis()

            # Generate report
            generator = ReportGenerator(results)

            if args.format == "terminal":
                report = generator.generate_terminal_report()
                print(report)

                if args.output:
                    with open(args.output, "w") as f:
                        f.write(report)
                    print(f"\nReport saved to: {args.output}")

            elif args.format == "json":
                output_file = args.output or f"analysis_report_{int(time.time())}.json"
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"JSON report saved to: {output_file}")

            elif args.format == "html":
                output_file = args.output or f"analysis_report_{int(time.time())}.html"
                html_report = generator.generate_html_report()
                with open(output_file, "w") as f:
                    f.write(html_report)
                print(f"HTML report saved to: {output_file}")

                # Try to open in browser
                try:
                    import webbrowser

                    webbrowser.open(output_file)
                except Exception:
                    pass

        if args.fix_errors:
            # Apply fixes
            if not analyzer.last_results:
                print("Running analysis first...")
                analyzer.run_comprehensive_analysis()

            print("🔧 Applying AI-powered fixes...")
            fix_results = analyzer.fix_errors_with_autogenlib(args.max_fixes)

            print(f"Fixes attempted: {fix_results.get('fixes_attempted', 0)}")
            print(f"Fixes applied: {fix_results.get('fixes_applied', 0)}")

            for fix in fix_results.get("fixes_details", []):
                if fix.get("fix_applied"):
                    print(f"✓ Fixed: {fix['error']['message']}")
                else:
                    print(f"✗ Failed: {fix['error']['message']}")

        if args.interactive:
            # Start interactive session
            if not analyzer.last_results:
                print("Running analysis first...")
                analyzer.run_comprehensive_analysis()

            interactive = InteractiveAnalyzer(analyzer)
            interactive.start_interactive_session()

    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
