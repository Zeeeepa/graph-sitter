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
    python graph-sitter_analysis.py <repo_name> [--output-format=<format>] [--language=<lang>]
    
    repo_name: GitHub repository in the format 'owner/repo' or local path
    --output-format: Output format (text, json, markdown) [default: text]
    --language: Force language detection (python, typescript) [default: auto-detect]

Examples:
    python graph-sitter_analysis.py fastapi/fastapi
    python graph-sitter_analysis.py ./my-local-repo --output-format=json
    python graph-sitter_analysis.py django/django --language=python
"""

import argparse
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
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
from graph_sitter.repo_operator.local_repo_operator import LocalRepoOperator
from graph_sitter.schemas.repo_config import BaseRepoConfig
from graph_sitter.codebase.config import ProjectConfig

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
    
    def __str__(self) -> str:
        return f"🟩 {self.filepath} / {self.type.capitalize()} - '{self.name}' [{self.reason}]"

@dataclass
class DeadCode:
    """Represents dead code found in the codebase."""
    name: str
    filepath: str
    type: str  # "function", "class", "variable", "import"
    reason: str
    
    def __str__(self) -> str:
        return f"💀 {self.filepath} / {self.type.capitalize()} - '{self.name}' [{self.reason}]"

@dataclass
class CodebaseAnalysisResult:
    """Holds the results of a codebase analysis."""
    summary: Dict[str, Any] = field(default_factory=dict)
    issues: List[CodeIssue] = field(default_factory=list)
    entry_points: List[EntryPoint] = field(default_factory=list)
    dead_code: List[DeadCode] = field(default_factory=list)
    file_tree: Dict[str, Any] = field(default_factory=dict)
    
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
        
        # Configure analysis settings
        self.config = CodebaseConfig(
            debug=False,
            verify_graph=True,
            track_graph=True,
            method_usages=True,
            full_range_index=True,
            ignore_process_errors=True,
        )
    
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
            task4 = progress.add_task("[red]Finding issues...", total=100)
            
            # Build file tree
            self._build_file_tree()
            progress.update(task1, completed=100)
            
            # Identify entry points
            self._identify_entry_points()
            progress.update(task2, completed=100)
            
            # Detect dead code
            self._detect_dead_code()
            progress.update(task3, completed=100)
            
            # Find issues
            self._find_issues()
            progress.update(task4, completed=100)
        
        # Update summary with counts
        self.result.summary.update({
            "entry_points": len(self.result.entry_points),
            "dead_code_items": len(self.result.dead_code),
            "total_issues": len(self.result.issues),
            "critical_issues": len(self.result.critical_issues),
            "major_issues": len(self.result.major_issues),
            "minor_issues": len(self.result.minor_issues),
        })
        
        return self.result
    
    def _build_file_tree(self) -> None:
        """Build a tree representation of the codebase files."""
        file_tree = {}
        
        for file in self.codebase.files:
            path_parts = file.filepath.split('/')
            current = file_tree
            
            # Build the tree structure
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    # This is a file
                    current[part] = {
                        "type": "file",
                        "path": file.filepath,
                        "issues": 0,  # Will be updated later
                    }
                else:
                    # This is a directory
                    if part not in current:
                        current[part] = {"type": "directory"}
                    current = current[part]
        
        self.result.file_tree = file_tree
    
    def _identify_entry_points(self) -> None:
        """Identify entry points in the codebase."""
        # Find main functions and scripts
        for func in self.codebase.functions:
            # Skip test files
            if "test" in func.file.filepath.lower():
                continue
                
            # Check for main functions
            if func.name == "main" or func.name == "__main__":
                self.result.entry_points.append(EntryPoint(
                    name=func.name,
                    filepath=func.file.filepath,
                    type="function",
                    reason="Main function"
                ))
                continue
            
            # Check for CLI entry points
            if any(dec.name in ["command", "click.command", "app.command", "cli.command"] 
                   for dec in func.decorators):
                self.result.entry_points.append(EntryPoint(
                    name=func.name,
                    filepath=func.file.filepath,
                    type="function",
                    reason="CLI command"
                ))
                continue
            
            # Check for API endpoints
            if any(dec.name in ["route", "get", "post", "put", "delete", "app.route", "router.get", "router.post"] 
                   for dec in func.decorators):
                self.result.entry_points.append(EntryPoint(
                    name=func.name,
                    filepath=func.file.filepath,
                    type="function",
                    reason="API endpoint"
                ))
                continue
        
        # Find top-level classes (not inherited by others)
        for cls in self.codebase.classes:
            # Skip test files
            if "test" in cls.file.filepath.lower():
                continue
            
            # Check if this class is not inherited by any other class
            is_inherited = False
            for other_cls in self.codebase.classes:
                if cls.name in other_cls.parent_class_names:
                    is_inherited = True
                    break
            
            if not is_inherited and cls.parent_class_names:
                self.result.entry_points.append(EntryPoint(
                    name=cls.name,
                    filepath=cls.file.filepath,
                    type="class",
                    reason="Top inheritance class"
                ))
    
    def _detect_dead_code(self) -> None:
        """Detect dead code in the codebase."""
        # Find unused functions
        for func in self.codebase.functions:
            # Skip test files
            if "test" in func.file.filepath.lower():
                continue
                
            # Skip decorated functions (likely entry points)
            if func.decorators:
                continue
            
            # Check if the function has no usages and no call sites
            if not func.usages and not func.call_sites:
                self.result.dead_code.append(DeadCode(
                    name=func.name,
                    filepath=func.file.filepath,
                    type="function",
                    reason="Not used by any other code"
                ))
        
        # Find unused classes
        for cls in self.codebase.classes:
            # Skip test files
            if "test" in cls.file.filepath.lower():
                continue
            
            # Check if the class has no usages
            if not cls.usages:
                self.result.dead_code.append(DeadCode(
                    name=cls.name,
                    filepath=cls.file.filepath,
                    type="class",
                    reason="Not used by any other code"
                ))
        
        # Find unused imports
        for file in self.codebase.files:
            # Skip test files
            if "test" in file.filepath.lower():
                continue
                
            file_summary = get_file_summary(file)
            
            for imp in file.imports:
                # Check if the imported symbol is used in the file
                if not imp.symbol_usages:
                    self.result.dead_code.append(DeadCode(
                        name=imp.name,
                        filepath=file.filepath,
                        type="import",
                        reason="Imported but never used"
                    ))
    
    def _find_issues(self) -> None:
        """Find issues in the codebase."""
        self._find_unused_parameters()
        self._find_wrong_call_sites()
        self._find_wrong_imports()
        self._find_other_issues()
    
    def _find_unused_parameters(self) -> None:
        """Find unused parameters in functions."""
        for func in self.codebase.functions:
            # Skip test files
            if "test" in func.file.filepath.lower():
                continue
                
            # Skip decorated functions (likely entry points)
            if func.decorators:
                continue
            
            # Get function summary
            func_summary = get_function_summary(func)
            
            # Check each parameter
            for param in func.parameters:
                # Skip self and cls parameters in methods
                if param.name in ["self", "cls"] and func.is_method:
                    continue
                
                # Check if parameter is used in the function body
                is_used = False
                for usage in func.symbol_usages:
                    if usage.name == param.name:
                        is_used = True
                        break
                
                if not is_used:
                    self.result.issues.append(CodeIssue(
                        filepath=func.file.filepath,
                        line_number=func.start_position.line if hasattr(func, 'start_position') else None,
                        issue_type="Unused Parameter",
                        message=f"Parameter '{param.name}' is defined but never used in function '{func.name}'",
                        severity=IssueSeverity.MINOR
                    ))
    
    def _find_wrong_call_sites(self) -> None:
        """Find wrong call sites (incorrect function calls)."""
        for func in self.codebase.functions:
            # Skip test files
            if "test" in func.file.filepath.lower():
                continue
            
            # Check each function call
            for call in func.function_calls:
                # Try to resolve the target function
                target_func = None
                for f in self.codebase.functions:
                    if f.name == call.name:
                        target_func = f
                        break
                
                if target_func:
                    # Check if the number of arguments matches
                    expected_params = len([p for p in target_func.parameters 
                                          if p.name not in ["self", "cls"] or not target_func.is_method])
                    actual_args = len(call.args)
                    
                    # Allow for *args and **kwargs
                    has_var_args = any(p.name.startswith("*") for p in target_func.parameters)
                    
                    if not has_var_args and actual_args > expected_params:
                        self.result.issues.append(CodeIssue(
                            filepath=func.file.filepath,
                            line_number=call.start_position.line if hasattr(call, 'start_position') else None,
                            issue_type="Wrong Call Site",
                            message=f"Function '{call.name}' called with {actual_args} arguments but expects {expected_params}",
                            severity=IssueSeverity.MAJOR
                        ))
    
    def _find_wrong_imports(self) -> None:
        """Find wrong imports (circular, unresolved)."""
        # Create a directed graph for imports
        import_graph = nx.DiGraph()
        
        # Add nodes and edges
        for file in self.codebase.files:
            import_graph.add_node(file.filepath)
            
            for imp in file.imports:
                if hasattr(imp, 'from_file') and imp.from_file:
                    import_graph.add_edge(file.filepath, imp.from_file.filepath)
        
        # Find circular imports (strongly connected components with size > 1)
        for scc in nx.strongly_connected_components(import_graph):
            if len(scc) > 1:
                # This is a circular import
                for filepath in scc:
                    self.result.issues.append(CodeIssue(
                        filepath=filepath,
                        line_number=None,
                        issue_type="Circular Import",
                        message=f"File is part of an import cycle involving {len(scc)} files",
                        severity=IssueSeverity.CRITICAL,
                        context=f"Cycle: {' -> '.join(scc)}"
                    ))
        
        # Find unresolved imports
        for file in self.codebase.files:
            for imp in file.imports:
                if not hasattr(imp, 'imported_symbol') or not imp.imported_symbol:
                    self.result.issues.append(CodeIssue(
                        filepath=file.filepath,
                        line_number=None,
                        issue_type="Unresolved Import",
                        message=f"Import '{imp.name}' could not be resolved",
                        severity=IssueSeverity.MAJOR
                    ))
    
    def _find_other_issues(self) -> None:
        """Find other issues in the codebase."""
        # Find large functions (high cyclomatic complexity)
        for func in self.codebase.functions:
            # Skip test files
            if "test" in func.file.filepath.lower():
                continue
            
            # Estimate complexity by counting branches
            complexity = 0
            if hasattr(func, 'code_block') and hasattr(func.code_block, 'statements'):
                for stmt in func.code_block.statements:
                    if hasattr(stmt, 'type') and stmt.type in ['if_statement', 'for_statement', 'while_statement', 'switch_statement']:
                        complexity += 1
            
            # Add complexity for each return statement
            complexity += len(func.return_statements)
            
            if complexity > 10:
                self.result.issues.append(CodeIssue(
                    filepath=func.file.filepath,
                    line_number=func.start_position.line if hasattr(func, 'start_position') else None,
                    issue_type="High Complexity",
                    message=f"Function '{func.name}' has high cyclomatic complexity ({complexity})",
                    severity=IssueSeverity.MAJOR if complexity > 15 else IssueSeverity.MINOR
                ))
        
        # Find large classes (too many methods/attributes)
        for cls in self.codebase.classes:
            # Skip test files
            if "test" in cls.file.filepath.lower():
                continue
            
            method_count = len(cls.methods)
            attr_count = len(cls.attributes)
            
            if method_count + attr_count > 20:
                self.result.issues.append(CodeIssue(
                    filepath=cls.file.filepath,
                    line_number=cls.start_position.line if hasattr(cls, 'start_position') else None,
                    issue_type="Large Class",
                    message=f"Class '{cls.name}' has too many members ({method_count} methods, {attr_count} attributes)",
                    severity=IssueSeverity.MINOR
                ))

def display_results_text(result: CodebaseAnalysisResult) -> None:
    """Display analysis results in text format."""
    console.print("\n[bold green]CODEBASE ANALYSIS COMPLETE[/]")
    
    # Display summary
    console.print("\n[bold cyan]SUMMARY:[/]")
    console.print(f"Total Files: {result.summary['total_files']}")
    console.print(f"Total Classes: {result.summary['total_classes']}")
    console.print(f"Total Functions: {result.summary['total_functions']}")
    console.print(f"Total Entry Points: {result.summary['entry_points']}")
    console.print(f"Dead Code Items: {result.summary['dead_code_items']}")
    console.print(f"Total Issues: {result.summary['total_issues']}")
    console.print(f"  - Critical Issues: {result.summary['critical_issues']}")
    console.print(f"  - Major Issues: {result.summary['major_issues']}")
    console.print(f"  - Minor Issues: {result.summary['minor_issues']}")
    
    # Display entry points
    if result.entry_points:
        console.print("\n[bold green]ENTRY POINTS:[/]")
        for entry_point in result.entry_points:
            console.print(str(entry_point))
    
    # Display dead code
    if result.dead_code:
        console.print("\n[bold yellow]DEAD CODE:[/]")
        for dead_code in result.dead_code:
            console.print(str(dead_code))
    
    # Display issues
    if result.issues:
        console.print("\n[bold red]ISSUES:[/]")
        
        # Critical issues
        if result.critical_issues:
            console.print("\n[bold red]CRITICAL ISSUES:[/]")
            for issue in result.critical_issues:
                console.print(str(issue))
        
        # Major issues
        if result.major_issues:
            console.print("\n[bold yellow]MAJOR ISSUES:[/]")
            for issue in result.major_issues:
                console.print(str(issue))
        
        # Minor issues
        if result.minor_issues:
            console.print("\n[bold cyan]MINOR ISSUES:[/]")
            for issue in result.minor_issues:
                console.print(str(issue))

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
                "reason": ep.reason
            }
            for ep in result.entry_points
        ],
        "dead_code": [
            {
                "name": dc.name,
                "filepath": dc.filepath,
                "type": dc.type,
                "reason": dc.reason
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
                "context": issue.context
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
    md_output.append("# Codebase Analysis Report\n")
    
    # Summary
    md_output.append("## Summary\n")
    md_output.append(f"- **Total Files:** {result.summary['total_files']}")
    md_output.append(f"- **Total Classes:** {result.summary['total_classes']}")
    md_output.append(f"- **Total Functions:** {result.summary['total_functions']}")
    md_output.append(f"- **Total Entry Points:** {result.summary['entry_points']}")
    md_output.append(f"- **Dead Code Items:** {result.summary['dead_code_items']}")
    md_output.append(f"- **Total Issues:** {result.summary['total_issues']}")
    md_output.append(f"  - Critical Issues: {result.summary['critical_issues']}")
    md_output.append(f"  - Major Issues: {result.summary['major_issues']}")
    md_output.append(f"  - Minor Issues: {result.summary['minor_issues']}\n")
    
    # Entry Points
    if result.entry_points:
        md_output.append("## Entry Points\n")
        for entry_point in result.entry_points:
            md_output.append(f"- **{entry_point.name}** ({entry_point.type})")
            md_output.append(f"  - File: `{entry_point.filepath}`")
            md_output.append(f"  - Reason: {entry_point.reason}\n")
    
    # Dead Code
    if result.dead_code:
        md_output.append("## Dead Code\n")
        for dead_code in result.dead_code:
            md_output.append(f"- **{dead_code.name}** ({dead_code.type})")
            md_output.append(f"  - File: `{dead_code.filepath}`")
            md_output.append(f"  - Reason: {dead_code.reason}\n")
    
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
                    md_output.append(f"  - Context: {issue.context}\n")
                else:
                    md_output.append("")
        
        # Major issues
        if result.major_issues:
            md_output.append("### Major Issues\n")
            for issue in result.major_issues:
                md_output.append(f"- **{issue.issue_type}:** {issue.message}")
                md_output.append(f"  - File: `{issue.filepath}`{f':{issue.line_number}' if issue.line_number else ''}")
                if issue.context:
                    md_output.append(f"  - Context: {issue.context}\n")
                else:
                    md_output.append("")
        
        # Minor issues
        if result.minor_issues:
            md_output.append("### Minor Issues\n")
            for issue in result.minor_issues:
                md_output.append(f"- **{issue.issue_type}:** {issue.message}")
                md_output.append(f"  - File: `{issue.filepath}`{f':{issue.line_number}' if issue.line_number else ''}")
                if issue.context:
                    md_output.append(f"  - Context: {issue.context}\n")
                else:
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

if __name__ == "__main__":
    main()

