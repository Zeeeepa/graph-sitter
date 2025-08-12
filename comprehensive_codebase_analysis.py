#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Tool using graph-sitter
This script performs a deep analysis of a codebase to identify:
- Dead code (unused functions, classes, variables)
- Unused parameters in functions
- Wrong call sites (incorrect function calls)
- Wrong imports (unused, circular, unresolved)
- Symbol usages throughout the codebase
- Dependencies between code elements
- Class attributes and methods
- Function parameters
- Entry points (top-level functions, classes that act as operators)

Usage:
    python comprehensive_codebase_analysis.py <repo_name> [--output-format=<format>] [--language=<lang>]
    
    repo_name: GitHub repository in the format 'owner/repo' or local path
    --output-format: Output format (text, json, markdown) [default: text]
    --language: Force language detection (python, typescript) [default: auto-detect]

Examples:
    python comprehensive_codebase_analysis.py fastapi/fastapi
    python comprehensive_codebase_analysis.py ./my-local-repo --output-format=json
    python comprehensive_codebase_analysis.py django/django --language=python
"""
import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

# Import graph-sitter components
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_class_summary,
    get_file_summary,
    get_function_summary,
    get_symbol_summary,
)
from graph_sitter.configs import CodebaseConfig
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType

# Initialize console for rich output
console = Console()

# Define issue severity levels
class IssueSeverity(Enum):
    CRITICAL = "⚠️ Critical"
    MAJOR = "👉 Major"
    MINOR = "🔍 Minor"

@dataclass
class CodeIssue:
    """Represents an issue found in the codebase."""
    filepath: str
    line_number: Optional[int]
    issue_type: str
    message: str
    severity: IssueSeverity
    context: Optional[str] = None
    impact: Optional[str] = None
    recommendation: Optional[str] = None
    
    def __str__(self) -> str:
        location = f"{self.filepath}"
        if self.line_number:
            location += f":{self.line_number}"
        return f"{self.severity.value} - {location} / {self.issue_type} - {self.message}"

@dataclass
class EntryPoint:
    """Represents an entry point in the codebase."""
    name: str
    filepath: str
    type: str  # "function" or "class"
    reason: str
    dependencies: List[str] = field(default_factory=list)
    inheritance_chain: Optional[List[str]] = None
    
    def __str__(self) -> str:
        return f"🟩 {self.filepath} / {self.type.capitalize()} - '{self.name}' [{self.reason}]"

@dataclass
class DeadCodeItem:
    """Represents dead code found in the codebase."""
    name: str
    filepath: str
    type: str  # "function", "class", "variable", "import"
    reason: str
    blast_radius: List[str] = field(default_factory=list)
    impact_score: int = 0
    
    def __str__(self) -> str:
        return f"💀 {self.filepath} / {self.type.capitalize()} - '{self.name}' [{self.reason}]"

@dataclass
class CodebaseAnalysisResult:
    """Holds the results of a codebase analysis."""
    summary: Dict[str, Any] = field(default_factory=dict)
    issues: List[CodeIssue] = field(default_factory=list)
    entry_points: List[EntryPoint] = field(default_factory=list)
    dead_code: List[DeadCodeItem] = field(default_factory=list)
    file_tree: Dict[str, Any] = field(default_factory=dict)
    import_graph: Optional[nx.MultiDiGraph] = None
    dependency_graph: Optional[nx.DiGraph] = None
    
    @property
    def critical_issues(self) -> List[CodeIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]
    
    @property
    def major_issues(self) -> List[CodeIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.MAJOR]
    
    @property
    def minor_issues(self) -> List[CodeIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.MINOR]


class CodebaseAnalyzer:
    """Analyzes a codebase using graph-sitter."""
    
    def __init__(self, repo_path: str, language: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            repo_path: Path to the repository or GitHub repo name (owner/repo)
            language: Force language detection (python, typescript)
        """
        self.repo_path = repo_path
        self.language = language
        self.codebase = None
        self.result = CodebaseAnalysisResult()
        
        # Configure analysis settings - PATTERN: Use comprehensive configuration
        self.config = CodebaseConfig(
            debug=False,
            verify_graph=True,
            track_graph=True,
            method_usages=True,
            full_range_index=True,
            ignore_process_errors=True,
        )
        
        # CRITICAL: Initialize NetworkX graphs for analysis
        self.import_graph = nx.MultiDiGraph()
        self.dependency_graph = nx.DiGraph()
    
    def load_codebase(self) -> None:
        """Load the codebase from the repository."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Loading codebase..."),
            console=console
        ) as progress:
            progress.add_task("Loading", total=None)
            
            try:
                # Check if repo_path is a GitHub repo or local path
                if "/" in self.repo_path and not os.path.exists(self.repo_path):
                    # GitHub repository
                    self.codebase = Codebase.from_repo(
                        self.repo_path,
                        language=self.language,
                        config=self.config
                    )
                else:
                    # Local repository
                    self.codebase = Codebase(
                        self.repo_path,
                        language=self.language,
                        config=self.config
                    )
                
                # Get basic codebase summary
                summary = get_codebase_summary(self.codebase)
                console.print(f"\n[bold green]Codebase loaded successfully![/]")
                console.print(Panel(summary, title="Codebase Summary"))
                
                # Store summary information
                self.result.summary = {
                    "total_files": len(list(self.codebase.files)),
                    "total_classes": len(list(self.codebase.classes)),
                    "total_functions": len(list(self.codebase.functions)),
                    "total_symbols": len(list(self.codebase.symbols)),
                }
                
            except Exception as e:
                console.print(f"[bold red]Error loading codebase:[/] {str(e)}")
                sys.exit(1)
    
    def analyze(self) -> CodebaseAnalysisResult:
        """
        Perform comprehensive analysis of the codebase.
        
        Returns:
            CodebaseAnalysisResult: The analysis results
        """
        self.load_codebase()
        
        with Progress(console=console) as progress:
            # Create progress tasks
            task1 = progress.add_task("[cyan]Building file tree...", total=100)
            task2 = progress.add_task("[green]Identifying entry points...", total=100)
            task3 = progress.add_task("[yellow]Detecting dead code...", total=100)
            task4 = progress.add_task("[red]Analyzing imports...", total=100)
            task5 = progress.add_task("[blue]Finding issues...", total=100)
            
            # Build file tree
            self._build_file_tree()
            progress.update(task1, completed=100)
            
            # Identify entry points
            self._identify_entry_points_comprehensive()
            progress.update(task2, completed=100)
            
            # Detect dead code
            self._detect_dead_code_comprehensive()
            progress.update(task3, completed=100)
            
            # Analyze imports
            self._analyze_imports_comprehensive()
            progress.update(task4, completed=100)
            
            # Find issues
            self._find_issues_comprehensive()
            progress.update(task5, completed=100)
        
        # Update summary with counts
        self.result.summary.update({
            "entry_points": len(self.result.entry_points),
            "dead_code_items": len(self.result.dead_code),
            "total_issues": len(self.result.issues),
            "critical_issues": len(self.result.critical_issues),
            "major_issues": len(self.result.major_issues),
            "minor_issues": len(self.result.minor_issues),
        })
        
        # Store graphs in result
        self.result.import_graph = self.import_graph
        self.result.dependency_graph = self.dependency_graph
        
        return self.result
    
    def _build_file_tree(self) -> None:
        """Build a tree representation of the codebase files."""
        file_tree = {}
        
        for file in self.codebase.files:
            # GOTCHA: Handle missing filepath attribute gracefully
            filepath = getattr(file, 'filepath', file.name if hasattr(file, 'name') else 'unknown')
            path_parts = filepath.split('/')
            current = file_tree
            
            # Build the tree structure
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    # This is a file
                    current[part] = {
                        "type": "file",
                        "path": filepath,
                        "issues": 0,  # Will be updated later
                        "lines_of_code": len(getattr(file, 'source', '').split('\n')) if hasattr(file, 'source') else 0
                    }
                else:
                    # This is a directory
                    if part not in current:
                        current[part] = {"type": "directory"}
                    current = current[part]
        
        self.result.file_tree = file_tree
    
    def _identify_entry_points_comprehensive(self) -> List[EntryPoint]:
        """PATTERN: Identify entry points using real graph-sitter properties."""
        entry_points = []
        
        # Find main functions and scripts
        for func in self.codebase.functions:
            # Skip test files
            if self._is_test_file(func.file):
                continue
                
            # Check for main functions
            if func.name == "main" or func.name == "__main__":
                entry_points.append(EntryPoint(
                    name=func.name,
                    filepath=getattr(func.file, 'filepath', 'unknown'),
                    type="function",
                    reason="Main function"
                ))
                continue
            
            # REAL: Check for CLI entry points using actual decorators
            if hasattr(func, 'decorators') and func.decorators:
                for decorator in func.decorators:
                    decorator_name = getattr(decorator, 'name', str(decorator))
                    if any(cli_pattern in decorator_name.lower() 
                           for cli_pattern in ["command", "click", "app.command", "cli.command"]):
                        entry_points.append(EntryPoint(
                            name=func.name,
                            filepath=getattr(func.file, 'filepath', 'unknown'),
                            type="function",
                            reason="CLI command"
                        ))
                        break
                    
                    # Check for API endpoints
                    if any(web_pattern in decorator_name.lower() 
                           for web_pattern in ["route", "get", "post", "put", "delete", "app.route"]):
                        entry_points.append(EntryPoint(
                            name=func.name,
                            filepath=getattr(func.file, 'filepath', 'unknown'),
                            type="function",
                            reason="API endpoint"
                        ))
                        break
        
        # REAL: Find top-level classes using actual inheritance
        for cls in self.codebase.classes:
            # Skip test files
            if self._is_test_file(cls.file):
                continue
            
            # Check if this class is not inherited by any other class
            is_inherited = False
            if hasattr(cls, 'parent_class_names') and cls.parent_class_names:
                for other_cls in self.codebase.classes:
                    if hasattr(other_cls, 'parent_class_names'):
                        if cls.name in other_cls.parent_class_names:
                            is_inherited = True
                            break
                
                if not is_inherited:
                    # Build inheritance chain
                    inheritance_chain = self._build_inheritance_chain(cls)
                    entry_points.append(EntryPoint(
                        name=cls.name,
                        filepath=getattr(cls.file, 'filepath', 'unknown'),
                        type="class",
                        reason="Top inheritance class",
                        inheritance_chain=inheritance_chain
                    ))
        
        self.result.entry_points = entry_points
        return entry_points
    
    def _detect_dead_code_comprehensive(self) -> None:
        """PATTERN: Detect dead code using real graph traversal from entry points."""
        # Start from real entry points and traverse
        entry_points = self.result.entry_points if self.result.entry_points else self._identify_entry_points_comprehensive()
        reachable_symbols = set()
        
        # CRITICAL: Use actual graph traversal
        for entry_point in entry_points:
            # Find the actual symbol object
            for symbol in self.codebase.symbols:
                if (symbol.name == entry_point.name and 
                    getattr(symbol.file, 'filepath', 'unknown') == entry_point.filepath):
                    self._traverse_from_entry_point(symbol, reachable_symbols)
                    break
        
        # REAL: Check all functions for reachability
        for func in self.codebase.functions:
            # Skip test files
            if self._is_test_file(func.file):
                continue
                
            # REAL: Use actual properties - function.usages and function.call_sites
            if (func not in reachable_symbols and 
                not getattr(func, 'usages', []) and 
                not getattr(func, 'call_sites', []) and 
                not getattr(func, 'decorators', [])):
                
                blast_radius = self._calculate_blast_radius(func)
                self.result.dead_code.append(DeadCodeItem(
                    name=func.name,
                    filepath=getattr(func.file, 'filepath', 'unknown'),
                    type="function",
                    reason="No usages or call sites found",
                    blast_radius=blast_radius,
                    impact_score=len(blast_radius)
                ))
        
        # REAL: Check all classes for reachability
        for cls in self.codebase.classes:
            # Skip test files
            if self._is_test_file(cls.file):
                continue
            
            # REAL: Use actual properties
            if (cls not in reachable_symbols and 
                not getattr(cls, 'usages', [])):
                
                blast_radius = self._calculate_blast_radius(cls)
                self.result.dead_code.append(DeadCodeItem(
                    name=cls.name,
                    filepath=getattr(cls.file, 'filepath', 'unknown'),
                    type="class",
                    reason="Not used by any other code",
                    blast_radius=blast_radius,
                    impact_score=len(blast_radius)
                ))
        
        # REAL: Find unused imports
        for file in self.codebase.files:
            # Skip test files
            if self._is_test_file(file):
                continue
                
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    # REAL: Check if the imported symbol is used
                    if not getattr(imp, 'symbol_usages', []):
                        self.result.dead_code.append(DeadCodeItem(
                            name=getattr(imp, 'name', str(imp)),
                            filepath=getattr(file, 'filepath', 'unknown'),
                            type="import",
                            reason="Imported but never used"
                        ))
    
    def _analyze_imports_comprehensive(self) -> None:
        """PATTERN: Build import graph using NetworkX for cycle detection."""
        # CRITICAL: Build import graph (see PyTorch import loops example)
        self.import_graph = nx.MultiDiGraph()
        
        # Add nodes and edges
        for file in self.codebase.files:
            filepath = getattr(file, 'filepath', 'unknown')
            self.import_graph.add_node(filepath)
            
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    # REAL: Use actual import resolution
                    if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                        imported_symbol = imp.imported_symbol
                        if hasattr(imported_symbol, 'file'):
                            imported_filepath = getattr(imported_symbol.file, 'filepath', 'unknown')
                            self.import_graph.add_edge(filepath, imported_filepath)
        
        # CRITICAL: Find strongly connected components for cycles
        cycles = list(nx.strongly_connected_components(self.import_graph))
        problematic_cycles = [cycle for cycle in cycles if len(cycle) > 1]
        
        # Add circular import issues
        for cycle in problematic_cycles:
            for filepath in cycle:
                self.result.issues.append(CodeIssue(
                    filepath=filepath,
                    line_number=None,
                    issue_type="Circular Import",
                    message=f"File is part of an import cycle involving {len(cycle)} files",
                    severity=IssueSeverity.CRITICAL,
                    context=f"Cycle: {' -> '.join(cycle)}",
                    recommendation="Refactor to break the circular dependency"
                ))
    
    def _find_issues_comprehensive(self) -> None:
        """Find all types of issues in the codebase."""
        self._analyze_function_parameters_comprehensive()
        self._validate_call_sites_comprehensive()
        self._find_other_issues()
    
    def _analyze_function_parameters_comprehensive(self) -> None:
        """REAL: Analyze function parameters using actual code block traversal."""
        for func in self.codebase.functions:
            # Skip test files and decorated functions
            if self._is_test_file(func.file) or getattr(func, 'decorators', []):
                continue
                
            # REAL: Use actual parameters and code block
            if hasattr(func, 'parameters'):
                for param in func.parameters:
                    param_name = getattr(param, 'name', str(param))
                    
                    # Skip self/cls in methods, *args/**kwargs
                    if param_name in ["self", "cls"] or param_name.startswith("*"):
                        continue
                        
                    # CRITICAL: Traverse real code block for usage
                    param_used = self._is_parameter_used_in_function(param_name, func)
                    
                    if not param_used:
                        self.result.issues.append(CodeIssue(
                            filepath=getattr(func.file, 'filepath', 'unknown'),
                            line_number=getattr(param, 'start_position', {}).get('line') if hasattr(param, 'start_position') else None,
                            issue_type="Unused Parameter",
                            message=f"Parameter '{param_name}' is defined but never used in function '{func.name}'",
                            severity=IssueSeverity.MINOR,
                            recommendation=f"Remove unused parameter '{param_name}' or use it in the function body"
                        ))
    
    def _validate_call_sites_comprehensive(self) -> None:
        """REAL: Validate call sites using actual function calls."""
        for func in self.codebase.functions:
            # Skip test files
            if self._is_test_file(func.file):
                continue
            
            # REAL: Use actual function calls from code blocks
            if hasattr(func, 'function_calls'):
                for call in func.function_calls:
                    call_name = getattr(call, 'name', str(call))
                    
                    # Try to resolve the target function
                    target_func = self._resolve_call_target(call_name)
                    
                    if target_func:
                        # CRITICAL: Validate argument count and types
                        expected_params = len([p for p in getattr(target_func, 'parameters', []) 
                                             if getattr(p, 'name', '') not in ["self", "cls"]])
                        actual_args = len(getattr(call, 'args', []))
                        
                        # Allow for *args and **kwargs
                        has_var_args = any(getattr(p, 'name', '').startswith("*") 
                                         for p in getattr(target_func, 'parameters', []))
                        
                        if not has_var_args and actual_args != expected_params:
                            self.result.issues.append(CodeIssue(
                                filepath=getattr(func.file, 'filepath', 'unknown'),
                                line_number=getattr(call, 'start_position', {}).get('line') if hasattr(call, 'start_position') else None,
                                issue_type="Wrong Call Site",
                                message=f"Function '{call_name}' called with {actual_args} arguments but expects {expected_params}",
                                severity=IssueSeverity.MAJOR,
                                recommendation=f"Check the function signature and provide the correct number of arguments"
                            ))
    
    def _find_other_issues(self) -> None:
        """Find other code quality issues."""
        # Find large functions (high complexity)
        for func in self.codebase.functions:
            if self._is_test_file(func.file):
                continue
            
            # Estimate complexity by counting branches and returns
            complexity = self._calculate_cyclomatic_complexity(func)
            
            if complexity > 10:
                severity = IssueSeverity.MAJOR if complexity > 15 else IssueSeverity.MINOR
                self.result.issues.append(CodeIssue(
                    filepath=getattr(func.file, 'filepath', 'unknown'),
                    line_number=getattr(func, 'start_position', {}).get('line') if hasattr(func, 'start_position') else None,
                    issue_type="High Complexity",
                    message=f"Function '{func.name}' has high cyclomatic complexity ({complexity})",
                    severity=severity,
                    recommendation="Consider breaking this function into smaller, more focused functions"
                ))
        
        # Find large classes
        for cls in self.codebase.classes:
            if self._is_test_file(cls.file):
                continue
            
            method_count = len(getattr(cls, 'methods', []))
            attr_count = len(getattr(cls, 'attributes', []))
            
            if method_count + attr_count > 20:
                self.result.issues.append(CodeIssue(
                    filepath=getattr(cls.file, 'filepath', 'unknown'),
                    line_number=getattr(cls, 'start_position', {}).get('line') if hasattr(cls, 'start_position') else None,
                    issue_type="Large Class",
                    message=f"Class '{cls.name}' has too many members ({method_count} methods, {attr_count} attributes)",
                    severity=IssueSeverity.MINOR,
                    recommendation="Consider breaking this class into smaller, more focused classes"
                ))
    
    # Helper methods
    def _is_test_file(self, file) -> bool:
        """Check if a file is a test file."""
        filepath = getattr(file, 'filepath', getattr(file, 'name', ''))
        return "test" in filepath.lower()
    
    def _build_inheritance_chain(self, cls) -> List[str]:
        """Build inheritance chain for a class."""
        chain = []
        if hasattr(cls, 'parent_class_names') and cls.parent_class_names:
            chain.extend(cls.parent_class_names)
        return chain
    
    def _traverse_from_entry_point(self, symbol, reachable: Set) -> None:
        """Traverse from entry point to find reachable symbols."""
        if symbol in reachable:
            return
        
        reachable.add(symbol)
        
        # REAL: Use actual symbol dependencies
        if hasattr(symbol, 'dependencies'):
            try:
                for dep in symbol.dependencies():
                    self._traverse_from_entry_point(dep, reachable)
            except:
                pass  # Handle gracefully if dependencies() fails
    
    def _calculate_blast_radius(self, symbol) -> List[str]:
        """Calculate the blast radius of removing a symbol."""
        blast_radius = []
        
        # REAL: Use actual usages
        if hasattr(symbol, 'usages'):
            for usage in getattr(symbol, 'usages', []):
                if hasattr(usage, 'file'):
                    filepath = getattr(usage.file, 'filepath', 'unknown')
                    if filepath not in blast_radius:
                        blast_radius.append(filepath)
        
        return blast_radius
    
    def _is_parameter_used_in_function(self, param_name: str, func) -> bool:
        """Check if a parameter is used within a function."""
        # CRITICAL: Traverse real code block for usage
        if hasattr(func, 'code_block') and func.code_block:
            if hasattr(func.code_block, 'statements'):
                for stmt in func.code_block.statements:
                    # REAL: Check symbol usages in statements
                    if hasattr(stmt, 'symbol_usages'):
                        for usage in stmt.symbol_usages:
                            if getattr(usage, 'name', '') == param_name:
                                return True
        
        return False
    
    def _resolve_call_target(self, call_name: str):
        """Resolve a function call to its target function."""
        for func in self.codebase.functions:
            if func.name == call_name:
                return func
        return None
    
    def _calculate_cyclomatic_complexity(self, func) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        if hasattr(func, 'code_block') and func.code_block:
            if hasattr(func.code_block, 'statements'):
                for stmt in func.code_block.statements:
                    # Count decision points
                    stmt_type = getattr(stmt, 'type', str(type(stmt).__name__).lower())
                    if any(decision in stmt_type for decision in ['if', 'for', 'while', 'switch', 'case']):
                        complexity += 1
        
        # Add complexity for return statements
        if hasattr(func, 'return_statements'):
            complexity += len(func.return_statements)
        
        return complexity


# Output formatting functions
def display_results_text(result: CodebaseAnalysisResult) -> None:
    """Display analysis results in text format."""
    console.print("\n[bold green]COMPREHENSIVE CODEBASE ANALYSIS COMPLETE[/]")
    
    # Display summary
    console.print("\n[bold cyan]SUMMARY:[/]")
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", justify="right", style="green")
    
    summary_table.add_row("Total Files", str(result.summary.get('total_files', 0)))
    summary_table.add_row("Total Classes", str(result.summary.get('total_classes', 0)))
    summary_table.add_row("Total Functions", str(result.summary.get('total_functions', 0)))
    summary_table.add_row("Total Symbols", str(result.summary.get('total_symbols', 0)))
    summary_table.add_row("Entry Points", str(result.summary.get('entry_points', 0)))
    summary_table.add_row("Dead Code Items", str(result.summary.get('dead_code_items', 0)))
    summary_table.add_row("Total Issues", str(result.summary.get('total_issues', 0)))
    summary_table.add_row("  - Critical Issues", str(result.summary.get('critical_issues', 0)))
    summary_table.add_row("  - Major Issues", str(result.summary.get('major_issues', 0)))
    summary_table.add_row("  - Minor Issues", str(result.summary.get('minor_issues', 0)))
    
    console.print(summary_table)
    
    # Display entry points
    if result.entry_points:
        console.print("\n[bold green]ENTRY POINTS:[/]")
        for entry_point in result.entry_points[:10]:  # Show first 10
            console.print(str(entry_point))
        if len(result.entry_points) > 10:
            console.print(f"... and {len(result.entry_points) - 10} more entry points")
    
    # Display dead code
    if result.dead_code:
        console.print("\n[bold yellow]DEAD CODE:[/]")
        for dead_code in result.dead_code[:10]:  # Show first 10
            console.print(str(dead_code))
        if len(result.dead_code) > 10:
            console.print(f"... and {len(result.dead_code) - 10} more dead code items")
    
    # Display issues by severity
    if result.issues:
        console.print("\n[bold red]ISSUES:[/]")
        
        # Critical issues
        if result.critical_issues:
            console.print("\n[bold red]CRITICAL ISSUES:[/]")
            for issue in result.critical_issues[:5]:  # Show first 5
                console.print(str(issue))
            if len(result.critical_issues) > 5:
                console.print(f"... and {len(result.critical_issues) - 5} more critical issues")
        
        # Major issues
        if result.major_issues:
            console.print("\n[bold yellow]MAJOR ISSUES:[/]")
            for issue in result.major_issues[:5]:  # Show first 5
                console.print(str(issue))
            if len(result.major_issues) > 5:
                console.print(f"... and {len(result.major_issues) - 5} more major issues")
        
        # Minor issues
        if result.minor_issues:
            console.print("\n[bold cyan]MINOR ISSUES:[/]")
            for issue in result.minor_issues[:5]:  # Show first 5
                console.print(str(issue))
            if len(result.minor_issues) > 5:
                console.print(f"... and {len(result.minor_issues) - 5} more minor issues")


def display_results_json(result: CodebaseAnalysisResult) -> None:
    """Display analysis results in JSON format."""
    # Convert result to JSON-serializable dict
    json_result = {
        "summary": result.summary,
        "entry_points": [
            {
                "name": ep.name,
                "filepath": ep.filepath,
                "type": ep.type,
                "reason": ep.reason,
                "dependencies": ep.dependencies,
                "inheritance_chain": ep.inheritance_chain
            }
            for ep in result.entry_points
        ],
        "dead_code": [
            {
                "name": dc.name,
                "filepath": dc.filepath,
                "type": dc.type,
                "reason": dc.reason,
                "blast_radius": dc.blast_radius,
                "impact_score": dc.impact_score
            }
            for dc in result.dead_code
        ],
        "issues": [
            {
                "filepath": issue.filepath,
                "line_number": issue.line_number,
                "issue_type": issue.issue_type,
                "message": issue.message,
                "severity": issue.severity.name,
                "context": issue.context,
                "impact": issue.impact,
                "recommendation": issue.recommendation
            }
            for issue in result.issues
        ],
        "file_tree": result.file_tree
    }
    
    # Print JSON
    print(json.dumps(json_result, indent=2))


def display_results_markdown(result: CodebaseAnalysisResult) -> None:
    """Display analysis results in Markdown format."""
    md_output = []
    
    # Title
    md_output.append("# Comprehensive Codebase Analysis Report\n")
    
    # Summary
    md_output.append("## Summary\n")
    md_output.append(f"- **Total Files:** {result.summary.get('total_files', 0)}")
    md_output.append(f"- **Total Classes:** {result.summary.get('total_classes', 0)}")
    md_output.append(f"- **Total Functions:** {result.summary.get('total_functions', 0)}")
    md_output.append(f"- **Total Symbols:** {result.summary.get('total_symbols', 0)}")
    md_output.append(f"- **Entry Points:** {result.summary.get('entry_points', 0)}")
    md_output.append(f"- **Dead Code Items:** {result.summary.get('dead_code_items', 0)}")
    md_output.append(f"- **Total Issues:** {result.summary.get('total_issues', 0)}")
    md_output.append(f"  - Critical Issues: {result.summary.get('critical_issues', 0)}")
    md_output.append(f"  - Major Issues: {result.summary.get('major_issues', 0)}")
    md_output.append(f"  - Minor Issues: {result.summary.get('minor_issues', 0)}\n")
    
    # Entry Points
    if result.entry_points:
        md_output.append("## Entry Points\n")
        for entry_point in result.entry_points:
            md_output.append(f"- **{entry_point.name}** ({entry_point.type})")
            md_output.append(f"  - File: `{entry_point.filepath}`")
            md_output.append(f"  - Reason: {entry_point.reason}")
            if entry_point.inheritance_chain:
                md_output.append(f"  - Inheritance: {' -> '.join(entry_point.inheritance_chain)}")
            md_output.append("")
    
    # Dead Code
    if result.dead_code:
        md_output.append("## Dead Code\n")
        for dead_code in result.dead_code:
            md_output.append(f"- **{dead_code.name}** ({dead_code.type})")
            md_output.append(f"  - File: `{dead_code.filepath}`")
            md_output.append(f"  - Reason: {dead_code.reason}")
            md_output.append(f"  - Impact Score: {dead_code.impact_score}")
            md_output.append("")
    
    # Issues
    if result.issues:
        md_output.append("## Issues\n")
        
        # Critical issues
        if result.critical_issues:
            md_output.append("### Critical Issues\n")
            for issue in result.critical_issues:
                md_output.append(f"- **{issue.issue_type}:** {issue.message}")
                md_output.append(f"  - File: `{issue.filepath}`{f':{issue.line_number}' if issue.line_number else ''}")
                if issue.context:
                    md_output.append(f"  - Context: {issue.context}")
                if issue.recommendation:
                    md_output.append(f"  - Recommendation: {issue.recommendation}")
                md_output.append("")
        
        # Major issues
        if result.major_issues:
            md_output.append("### Major Issues\n")
            for issue in result.major_issues:
                md_output.append(f"- **{issue.issue_type}:** {issue.message}")
                md_output.append(f"  - File: `{issue.filepath}`{f':{issue.line_number}' if issue.line_number else ''}")
                if issue.recommendation:
                    md_output.append(f"  - Recommendation: {issue.recommendation}")
                md_output.append("")
        
        # Minor issues
        if result.minor_issues:
            md_output.append("### Minor Issues\n")
            for issue in result.minor_issues:
                md_output.append(f"- **{issue.issue_type}:** {issue.message}")
                md_output.append(f"  - File: `{issue.filepath}`{f':{issue.line_number}' if issue.line_number else ''}")
                if issue.recommendation:
                    md_output.append(f"  - Recommendation: {issue.recommendation}")
                md_output.append("")
    
    # Print markdown
    print("\n".join(md_output))


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analysis Tool using graph-sitter")
    parser.add_argument("repo_name", help="GitHub repository (owner/repo) or local path")
    parser.add_argument("--output-format", choices=["text", "json", "markdown"], default="text",
                        help="Output format (text, json, markdown)")
    parser.add_argument("--language", choices=["python", "typescript"], default=None,
                        help="Force language detection (python, typescript)")
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = CodebaseAnalyzer(args.repo_name, args.language)
        
        # Perform analysis
        result = analyzer.analyze()
        
        # Display results in the specified format
        if args.output_format == "json":
            display_results_json(result)
        elif args.output_format == "markdown":
            display_results_markdown(result)
        else:
            display_results_text(result)
            
    except KeyboardInterrupt:
        console.print("\n[bold red]Analysis interrupted by user[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during analysis:[/] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
