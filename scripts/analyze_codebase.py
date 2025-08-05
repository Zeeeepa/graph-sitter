#!/usr/bin/env python
"""
Enhanced Codebase Analysis Tool for Graph-Sitter

This script provides a comprehensive analysis of the graph-sitter codebase,
focusing on error detection, entry points, and inheritance relationships.

It uses graph-sitter's own analysis capabilities to analyze itself, providing:
- Total number of files, code files, and documentation files
- Class hierarchy and inheritance depth
- Function statistics and detailed error detection
- Main entry points and core functionality with parameter flow analysis
- Symbol usage and dependencies

Usage:
    python scripts/analyze_codebase.py [--github-repo REPO_URL]

Options:
    --github-repo    GitHub repository URL to analyze (default: local codebase)
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import jinja2
except ImportError:
    print("Installing jinja2...")
    os.system("pip install jinja2")
    import jinja2

from graph_sitter.codebase.codebase_analysis import (
    get_class_summary,
    get_codebase_summary,
    get_file_summary,
    get_function_summary,
    get_symbol_summary,
)
from graph_sitter.codebase.codebase_context import CodebaseContext
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.file import SourceFile
from graph_sitter.enums import SymbolType, EdgeType
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


# HTML template for the analysis report
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph-Sitter Codebase Analysis</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        h1 {
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        .section {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .stats {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: space-between;
        }
        .stat-card {
            background-color: #f1f8ff;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 4px;
            flex: 1;
            min-width: 200px;
        }
        .stat-card h3 {
            margin-top: 0;
            color: #3498db;
        }
        .error-list {
            list-style-type: none;
            padding: 0;
        }
        .error-item {
            background-color: #fff8f8;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        .error-title {
            font-weight: bold;
            color: #e74c3c;
        }
        .error-context {
            font-family: monospace;
            background-color: #f9f2f4;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            white-space: pre-wrap;
        }
        .collapsible {
            background-color: #f1f8ff;
            color: #2980b9;
            cursor: pointer;
            padding: 18px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            border-radius: 4px;
            margin-bottom: 5px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .active, .collapsible:hover {
            background-color: #e1f0ff;
        }
        .content {
            padding: 0 18px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
            background-color: white;
            border-radius: 0 0 4px 4px;
        }
        .entry-point {
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid #2ecc71;
        }
        .function-flow {
            margin-left: 20px;
            font-family: monospace;
        }
        .badge {
            background-color: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-left: 10px;
        }
        .language-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .language-badge {
            background-color: #34495e;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 14px;
        }
        .visualization {
            width: 100%;
            height: 500px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 20px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>Graph-Sitter Codebase Analysis</h1>
    
    <div class="section">
        <h2>Codebase Summary</h2>
        <div class="stats">
            <div class="stat-card">
                <h3>Files</h3>
                <p>Total: {{ summary.total_files }}</p>
                <p>Code: {{ summary.total_code_files }}</p>
                <p>Documentation: {{ summary.total_doc_files }}</p>
            </div>
            <div class="stat-card">
                <h3>Components</h3>
                <p>Classes: {{ summary.total_classes }}</p>
                <p>Functions: {{ summary.total_functions }}</p>
                <p>Global Variables: {{ summary.total_global_vars }}</p>
            </div>
            <div class="stat-card">
                <h3>Languages</h3>
                <div class="language-stats">
                    {% for lang, count in summary.programming_languages.items() %}
                    <div class="language-badge">{{ lang }}: {{ count }}</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    {% if errors %}
    <div class="section">
        <h2>Errors Found ({{ errors|length }})</h2>
        <ul class="error-list">
            {% for error in errors %}
            <li class="error-item">
                <div class="error-title">{{ error.file }}[{{ error.function }}] - {{ error.error }}</div>
                <div class="error-context">{{ error.context }}</div>
            </li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="section">
        <h2>Top Level Operator Codefiles/Functions ({{ entry_points|length }})</h2>
        {% for entry in entry_points %}
        <button class="collapsible">{{ entry.file }} <span class="badge">Inheritance {{ entry.inheritance_level }}</span></button>
        <div class="content">
            {% for func in entry.functions %}
            <div class="entry-point">
                <strong>{{ func.name }}</strong>
                <p>Parameters: {{ func.parameters|join(", ") }}</p>
                <div class="function-flow">
                    <p>Call Flow:</p>
                    <ul>
                        {% for call in func.calls %}
                        <li>{{ call.name }}({{ call.args|join(", ") }})</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Top Level Files ({{ top_level_files|length }})</h2>
        {% for file in top_level_files %}
        <button class="collapsible">{{ file.file }}</button>
        <div class="content">
            {% for func in file.functions %}
            <div class="entry-point">
                <strong>{{ func.name }}</strong>
                <p>Parameters: {{ func.parameters|join(", ") }}</p>
                <div class="function-flow">
                    <p>Call Flow:</p>
                    <ul>
                        {% for call in func.calls %}
                        <li>{{ call.name }}({{ call.args|join(", ") }})</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var coll = document.getElementsByClassName("collapsible");
            for (var i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var content = this.nextElementSibling;
                    if (content.style.maxHeight) {
                        content.style.maxHeight = null;
                    } else {
                        content.style.maxHeight = content.scrollHeight + "px";
                    }
                });
            }
        });
    </script>
</body>
</html>
"""


class EnhancedCodebaseAnalyzer:
    """Enhanced analyzer for the graph-sitter codebase."""

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the analyzer with a repository path.
        
        Args:
            repo_path: Path to the repository to analyze. If None, uses the current directory.
        """
        self.repo_path = repo_path or os.getcwd()
        self.codebase = self._load_codebase()
        self.errors: List[Dict[str, Any]] = []
        
    def _load_codebase(self) -> Codebase:
        """Load the codebase from the repository path."""
        print(f"Loading codebase from {self.repo_path}...")
        
        if self.repo_path.startswith("https://github.com/"):
            # Extract org/repo from URL
            parts = self.repo_path.split("/")
            org_repo = f"{parts[-2]}/{parts[-1]}"
            
            # Create a temporary directory for cloning if needed
            temp_dir = Path(os.path.expanduser("~")) / ".graph-sitter" / "repos"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Clone the repository to a temporary directory
            repo_dir = temp_dir / parts[-2] / parts[-1]
            if not repo_dir.exists():
                print(f"Cloning repository to {repo_dir}...")
                repo_dir.parent.mkdir(parents=True, exist_ok=True)
                os.system(f"git clone {self.repo_path} {repo_dir}")
            
            print(f"Using local repository at {repo_dir}")
            return Codebase(str(repo_dir))
        else:
            # Local path
            return Codebase(self.repo_path)
    
    def analyze(self) -> Dict:
        """
        Perform a comprehensive analysis of the codebase.
        
        Returns:
            Dict containing analysis results
        """
        try:
            results = {
                "summary": self._get_summary(),
                "entry_points": self._find_entry_points(),
                "errors": self._detect_errors(),
                "top_level_files": self._find_top_level_files(),
            }
            return results
        except Exception as e:
            import traceback
            print(f"Error in analyze method: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def _get_summary(self) -> Dict:
        """Get a summary of the codebase."""
        # Helper function to safely get file extension
        def get_file_extension(file):
            if hasattr(file, 'path'):
                path = file.path
                if hasattr(path, 'suffix'):  # Path object
                    return str(path.suffix).lower()
                elif isinstance(path, str):
                    return os.path.splitext(path)[1].lower()
            return ""
        
        # Count files by type
        code_files = []
        doc_files = []
        for f in self.codebase.files:
            ext = get_file_extension(f)
            if ext in ['.py', '.js', '.ts', '.tsx', '.jsx']:
                code_files.append(f)
            elif ext in ['.md', '.rst', '.txt']:
                doc_files.append(f)
        
        return {
            "codebase_summary": get_codebase_summary(self.codebase),
            "total_files": len(list(self.codebase.files)),
            "total_code_files": len(code_files),
            "total_doc_files": len(doc_files),
            "total_classes": len(list(self.codebase.classes)),
            "total_functions": len(list(self.codebase.functions)),
            "total_global_vars": len(list(self.codebase.global_vars)),
            "programming_languages": self._count_languages()
        }
    
    def _count_languages(self) -> Dict[str, int]:
        """Count the number of files per programming language."""
        language_counts = {}
        for file in self.codebase.files:
            if hasattr(file, 'language') and file.language:
                lang = file.language.name if isinstance(file.language, ProgrammingLanguage) else str(file.language)
                language_counts[lang] = language_counts.get(lang, 0) + 1
        return language_counts
    
    def _detect_errors(self) -> List[Dict]:
        """Detect actual errors in the codebase that would cause runtime issues."""
        errors = []
        
        for file in self.codebase.files:
            if not hasattr(file, 'path'):
                continue
                
            # Helper function to safely get file extension
            def get_file_extension(file_path):
                if hasattr(file_path, 'suffix'):  # Path object
                    return str(file_path.suffix).lower()
                elif isinstance(file_path, str):
                    return os.path.splitext(file_path)[1].lower()
                return ""
                
            ext = get_file_extension(file.path)
            if ext not in ['.py', '.js', '.ts', '.tsx', '.jsx']:
                continue
            
            # Check for functions with errors
            if hasattr(file, 'functions'):
                for func in file.functions:
                    # Check for functions that are never called (dead code)
                    if hasattr(func, 'callers') and not func.callers and not func.name.startswith('test_') and not func.name == 'main':
                        # Skip __init__ methods and special methods
                        if func.name not in ['__init__', '__str__', '__repr__', '__eq__', '__hash__', '__call__']:
                            errors.append({
                                "file": str(file.path) if hasattr(file.path, 'parts') else file.path,
                                "function": func.name,
                                "error": "Function is never called (dead code)",
                                "context": f"Function '{func.name}' is defined but never called in the codebase."
                            })
                    
                    # Check for incorrect parameter usage
                    if hasattr(func, 'function_calls'):
                        for call in func.function_calls:
                            if hasattr(call, 'target') and hasattr(call.target, 'parameters'):
                                # Check if the number of arguments matches the number of parameters
                                if hasattr(call, 'args') and len(call.args) != len(call.target.parameters):
                                    # Skip if the function has *args or **kwargs
                                    has_varargs = any(p.name.startswith('*') for p in call.target.parameters)
                                    if not has_varargs:
                                        errors.append({
                                            "file": str(file.path) if hasattr(file.path, 'parts') else file.path,
                                            "function": func.name,
                                            "error": "Incorrect number of arguments",
                                            "context": f"Call to '{call.name}' has {len(call.args)} arguments but the function expects {len(call.target.parameters)} parameters."
                                        })
                    
                    # Check for empty exception handlers (swallowing exceptions)
                    if hasattr(func, 'code_block') and hasattr(func.code_block, 'statements'):
                        for stmt in func.code_block.statements:
                            if hasattr(stmt, 'type') and stmt.type == 'try_statement':
                                if hasattr(stmt, 'except_clauses'):
                                    for except_clause in stmt.except_clauses:
                                        if hasattr(except_clause, 'body') and not except_clause.body.statements:
                                            errors.append({
                                                "file": str(file.path) if hasattr(file.path, 'parts') else file.path,
                                                "function": func.name,
                                                "error": "Empty exception handler",
                                                "context": f"Function '{func.name}' has an empty exception handler which may hide errors."
                                            })
                    
                    # Check for undefined variables
                    if hasattr(func, 'code_block') and hasattr(func.code_block, 'statements'):
                        defined_vars = set()
                        for param in func.parameters if hasattr(func, 'parameters') else []:
                            defined_vars.add(param.name)
                        
                        for stmt in func.code_block.statements:
                            # Add variables defined in assignments
                            if hasattr(stmt, 'type') and stmt.type == 'assignment':
                                if hasattr(stmt, 'targets'):
                                    for target in stmt.targets:
                                        if hasattr(target, 'name'):
                                            defined_vars.add(target.name)
                            
                            # Check variables used in expressions
                            if hasattr(stmt, 'expressions'):
                                for expr in stmt.expressions:
                                    if hasattr(expr, 'type') and expr.type == 'identifier':
                                        if hasattr(expr, 'name') and expr.name not in defined_vars:
                                            # Skip built-in functions and common imports
                                            if expr.name not in ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple']:
                                                errors.append({
                                                    "file": str(file.path) if hasattr(file.path, 'parts') else file.path,
                                                    "function": func.name,
                                                    "error": "Potentially undefined variable",
                                                    "context": f"Variable '{expr.name}' is used but may not be defined in the function scope."
                                                })
        
        return errors
    
    def _get_error_context(self, content: str, *patterns: str) -> str:
        """Get context around an error in the code."""
        lines = content.splitlines()
        context_lines = []
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                if pattern in line:
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context_lines.extend(lines[start:end])
                    context_lines.append("...")
                    break
        
        return "\n".join(context_lines) if context_lines else "Context not available"
    
    def _find_entry_points(self) -> List[Dict]:
        """Find potential entry points to the codebase."""
        entry_points = []
        
        # Find files that are imported by many other files
        file_importers = {}
        for file in self.codebase.files:
            file_path = file.path if hasattr(file, 'path') else "unknown"
            # Convert PosixPath to string if needed
            if hasattr(file_path, 'parts'):  # Check if it's a Path object
                file_path = str(file_path)
                
            importers = self._calculate_file_inheritance_level(file)
            file_importers[file_path] = importers
        
        # Sort files by number of importers (descending)
        sorted_files = sorted(file_importers.items(), key=lambda x: x[1], reverse=True)
        
        # Take the top 20 files as entry points
        for file_path, importers in sorted_files[:20]:
            entry_point = {
                "file": file_path,
                "inheritance_level": importers,
                "functions": []
            }
            
            # Find the file object
            file_obj = None
            for file in self.codebase.files:
                if hasattr(file, 'path'):
                    path = file.path
                    if hasattr(path, 'parts'):  # Path object
                        path = str(path)
                    if path == file_path:
                        file_obj = file
                        break
            
            if file_obj and hasattr(file_obj, 'functions'):
                for func in file_obj.functions:
                    function_info = {
                        "name": func.name,
                        "parameters": [p.name for p in func.parameters] if hasattr(func, 'parameters') else [],
                        "calls": []
                    }
                    
                    # Get function calls
                    if hasattr(func, 'function_calls'):
                        for call in func.function_calls:
                            if hasattr(call, 'name'):
                                call_info = {
                                    "name": call.name,
                                    "args": [arg.source if hasattr(arg, 'source') else str(arg) for arg in call.args] if hasattr(call, 'args') else []
                                }
                                function_info["calls"].append(call_info)
                    
                    entry_point["functions"].append(function_info)
            
            entry_points.append(entry_point)
        
        # Sort by inheritance level
        entry_points.sort(key=lambda x: x["inheritance_level"], reverse=True)
        
        return entry_points
    
    def _calculate_file_inheritance_level(self, file: SourceFile) -> int:
        """Calculate the inheritance level of a file (how many other files import it)."""
        importers = 0
        for other_file in self.codebase.files:
            if hasattr(other_file, 'imports'):
                for imp in other_file.imports:
                    if hasattr(imp, 'imported_symbol') and imp.imported_symbol == file:
                        importers += 1
        
        return importers
    
    def _find_top_level_files(self) -> List[Dict]:
        """Find top-level files that are not imported by other files."""
        top_level_files = []
        
        # Helper function to safely get file extension
        def get_file_extension(file):
            if hasattr(file, 'path'):
                path = file.path
                if hasattr(path, 'suffix'):  # Path object
                    return str(path.suffix).lower()
                elif isinstance(path, str):
                    return os.path.splitext(path)[1].lower()
            return ""
        
        for file in self.codebase.files:
            if not hasattr(file, 'path'):
                continue
                
            ext = get_file_extension(file)
            if ext not in ['.py', '.js', '.ts', '.tsx', '.jsx']:
                continue
            
            importers = []
            for other_file in self.codebase.files:
                if hasattr(other_file, 'imports'):
                    for imp in other_file.imports:
                        if hasattr(imp, 'imported_symbol') and imp.imported_symbol == file:
                            other_file_path = other_file.path if hasattr(other_file, 'path') else "unknown"
                            # Convert PosixPath to string if needed
                            if hasattr(other_file_path, 'parts'):  # Check if it's a Path object
                                other_file_path = str(other_file_path)
                            importers.append(other_file_path)
            
            # If no other file imports this file, it's a top-level file
            if not importers:
                # Convert PosixPath to string if needed
                file_path = file.path
                if hasattr(file_path, 'parts'):  # Check if it's a Path object
                    file_path = str(file_path)
                    
                file_info = {
                    "file": file_path,
                    "functions": [],
                    "operators": self._get_operators_and_operands(file)
                }
                
                # Get functions in the file
                if hasattr(file, 'functions'):
                    for func in file.functions:
                        function_info = {
                            "name": func.name,
                            "parameters": [p.name for p in func.parameters] if hasattr(func, 'parameters') else [],
                            "calls": []
                        }
                        
                        # Get function calls
                        if hasattr(func, 'function_calls'):
                            for call in func.function_calls:
                                if hasattr(call, 'name'):
                                    call_info = {
                                        "name": call.name,
                                        "args": [arg.source if hasattr(arg, 'source') else str(arg) for arg in call.args] if hasattr(call, 'args') else []
                                    }
                                    function_info["calls"].append(call_info)
                        
                        file_info["functions"].append(function_info)
                
                top_level_files.append(file_info)
        
        return top_level_files
    
    def _get_operators_and_operands(self, file: SourceFile) -> Dict[str, List[str]]:
        """Extract operators and operands from a file."""
        operators = []
        operands = []
        
        if hasattr(file, 'functions'):
            for func in file.functions:
                if hasattr(func, 'function_calls'):
                    for call in func.function_calls:
                        if hasattr(call, 'name'):
                            operators.append(call.name)
                        if hasattr(call, 'args'):
                            for arg in call.args:
                                if hasattr(arg, 'source'):
                                    operands.append(arg.source)
        
        return {
            "operators": operators[:10],  # Limit to 10 for brevity
            "operands": operands[:10]     # Limit to 10 for brevity
        }
    
    def _calculate_doi(self, cls: Class) -> int:
        """Calculate the depth of inheritance for a given class."""
        return len(cls.superclasses) if hasattr(cls, 'superclasses') else 0
    
    def generate_html_report(self, results: Dict) -> str:
        """Generate an HTML report from the analysis results."""
        template = jinja2.Template(HTML_TEMPLATE)
        return template.render(
            summary=results["summary"],
            errors=results["errors"],
            entry_points=results["entry_points"],
            top_level_files=results["top_level_files"]
        )
    
    def print_analysis(self, results: Dict) -> None:
        """Print the analysis results in a readable format."""
        print("\n" + "="*80)
        print(f"GRAPH-SITTER CODEBASE ANALYSIS")
        print("="*80)
        
        # Print summary
        summary = results["summary"]
        print(f"\n## CODEBASE SUMMARY")
        print("--------------------------------------")
        print(f"Total files: {summary['total_files']}")
        print(f"  - Code files: {summary['total_code_files']}     - Documentation files: {summary['total_doc_files']}")
        print("--------------------------------------")
        print(f"Total classes: {summary['total_classes']}")
        print("--------------------------------------")
        print(f"Total functions: {summary['total_functions']} / Functions with errors: {len(results['errors'])}")
        print("--------------------------------------")
        
        # Print errors
        if results['errors']:
            for i, error in enumerate(results['errors'], 1):
                print(f"error {i},")
                print(f"{error['file']}[{error['function']}]= Error specifics [{error['error']}] {error['context']}")
            print("--------------------------------------")
        
        print(f"Total global variables: {summary['total_global_vars']}")
        print("Programming Languages:")
        for lang, count in summary['programming_languages'].items():
            print(f"  - {lang}: {count} files")
        print("--------------------------------------")
        
        # Print entry points
        print(f"\n## MAIN ENTRY POINTS")
        print("(Top Level Inheritance Codefile Name List + Their Flow Function lists with parameters used in these flows and codefile locations)- this should create callable tree flows.")
        for entry in results["entry_points"]:
            print(f"  - {entry['file']}")
            for func in entry["functions"]:
                params_str = ", ".join(func["parameters"])
                calls_str = ", ".join([call["name"] for call in func["calls"]])
                print(f"    Main functions: {func['name']} [Parameters callable in/ callable out] [Inheritance {entry['inheritance_level']}/4] - [1.{entry['file']}/method='{func['name']}'{{{params_str}}} - {calls_str}]")
        
        # Print top-level files
        print("\n[ To list ALL top level [Highest inheritance level where noone imports them] = And list all project's codefiles like this. even if there are 50 such codefiles.")
        for file_info in results["top_level_files"]:
            print(f"  - {file_info['file']}")
            for func in file_info["functions"]:
                params_str = ", ".join(func["parameters"])
                print(f"    Main function: {func['name']}[Parameters callable in/ callable out]")
        
        print("\n" + "="*80)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Enhanced analysis of a codebase using graph-sitter")
    parser.add_argument("--github-repo", help="GitHub repository URL to analyze", default=None)
    parser.add_argument("--output", help="Output HTML file path", default="codebase_analysis.html")
    args = parser.parse_args()
    
    try:
        analyzer = EnhancedCodebaseAnalyzer(args.github_repo)
        results = analyzer.analyze()
        
        # Generate HTML report
        html_report = analyzer.generate_html_report(results)
        with open(args.output, "w") as f:
            f.write(html_report)
        
        # Print text report
        analyzer.print_analysis(results)
        
        print(f"\nHTML report generated at: {os.path.abspath(args.output)}")
    except Exception as e:
        print(f"Error analyzing codebase: {str(e)}")
        print("\nUsage examples:")
        print("  # Analyze local codebase")
        print("  python scripts/analyze_codebase.py")
        print("\n  # Analyze GitHub repository")
        print("  python scripts/analyze_codebase.py --github-repo https://github.com/Zeeeepa/graph-sitter")
        print("\nNote: When analyzing GitHub repositories, the script will clone the repository to")
        print("      ~/.graph-sitter/repos/<org>/<repo> directory for analysis.")


if __name__ == "__main__":
    main()
