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
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
            return Codebase(org_repo)
        else:
            # Local path
            return Codebase(self.repo_path)
    
    def analyze(self) -> Dict:
        """
        Perform a comprehensive analysis of the codebase.
        
        Returns:
            Dict containing analysis results
        """
        results = {
            "summary": self._get_summary(),
            "entry_points": self._find_entry_points(),
            "errors": self._find_errors(),
            "top_level_files": self._find_top_level_files(),
        }
        return results
    
    def _get_summary(self) -> Dict:
        """Get a summary of the codebase."""
        return {
            "codebase_summary": get_codebase_summary(self.codebase),
            "total_files": len(list(self.codebase.files)),
            "total_code_files": len([f for f in self.codebase.files if f.is_source_file]),
            "total_doc_files": len([f for f in self.codebase.files if not f.is_source_file]),
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
    
    def _find_errors(self) -> List[Dict[str, Any]]:
        """Find errors in the codebase."""
        errors = []
        
        # Check for functions with potential issues
        for func in self.codebase.functions:
            # Skip functions without a file
            if not hasattr(func, 'file') or not func.file:
                continue
                
            file_path = func.file.path if hasattr(func.file, 'path') else "unknown"
            
            # Check for empty exception handlers
            if hasattr(func, 'content') and func.content:
                if "except:" in func.content and "pass" in func.content:
                    errors.append({
                        "file": file_path,
                        "function": func.name,
                        "error": "Empty exception handler",
                        "context": self._get_error_context(func.content, "except:", "pass")
                    })
            
            # Check for very long functions (over 100 lines)
            if hasattr(func, 'content') and func.content:
                lines = func.content.splitlines()
                if len(lines) > 100:
                    errors.append({
                        "file": file_path,
                        "function": func.name,
                        "error": f"Very long function ({len(lines)} lines)",
                        "context": f"Function spans from line {func.line_range[0]} to {func.line_range[1]}"
                    })
            
            # Check for unused parameters
            if hasattr(func, 'parameters') and func.parameters:
                used_params = set()
                for call in func.function_calls:
                    if hasattr(call, 'args'):
                        for arg in call.args:
                            if hasattr(arg, 'name'):
                                used_params.add(arg.name)
                
                for param in func.parameters:
                    if param.name not in used_params and param.name not in ['self', 'cls', 'kwargs', 'args']:
                        errors.append({
                            "file": file_path,
                            "function": func.name,
                            "error": f"Unused parameter '{param.name}'",
                            "context": f"Parameter '{param.name}' is defined but not used in the function body"
                        })
            
            # Check for too many parameters
            if hasattr(func, 'parameters') and len(func.parameters) > 7:  # Arbitrary threshold
                errors.append({
                    "file": file_path,
                    "function": func.name,
                    "error": f"Too many parameters ({len(func.parameters)})",
                    "context": f"Function has {len(func.parameters)} parameters, which may indicate a design issue"
                })
            
            # Check for missing docstring
            if not hasattr(func, 'docstring') or not func.docstring:
                errors.append({
                    "file": file_path,
                    "function": func.name,
                    "error": "Missing docstring",
                    "context": "Function lacks documentation"
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
        """Find potential entry points to the codebase with parameter flow analysis."""
        entry_points = []
        
        # Look for files with main functions or CLI entry points
        for file in self.codebase.files:
            if not hasattr(file, 'path'):
                continue
                
            file_path = file.path
            
            # Check for common entry point patterns
            if (
                "cli" in file_path or 
                "main.py" in file_path or 
                "app.py" in file_path or
                "__main__.py" in file_path
            ):
                entry_point = {
                    "file": file_path,
                    "type": "potential_entry_point",
                    "functions": [],
                    "inheritance_level": self._calculate_file_inheritance_level(file)
                }
                
                # Check if the file has functions
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
                        
                        entry_point["functions"].append(function_info)
                
                entry_points.append(entry_point)
        
        # Sort by inheritance level
        entry_points.sort(key=lambda x: x["inheritance_level"])
        
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
        
        for file in self.codebase.files:
            if not hasattr(file, 'path') or not file.is_source_file:
                continue
            
            importers = []
            for other_file in self.codebase.files:
                if hasattr(other_file, 'imports'):
                    for imp in other_file.imports:
                        if hasattr(imp, 'imported_symbol') and imp.imported_symbol == file:
                            importers.append(other_file.path if hasattr(other_file, 'path') else "unknown")
            
            # If no other file imports this file, it's a top-level file
            if not importers:
                file_info = {
                    "file": file.path,
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
    args = parser.parse_args()
    
    analyzer = EnhancedCodebaseAnalyzer(args.github_repo)
    results = analyzer.analyze()
    analyzer.print_analysis(results)


if __name__ == "__main__":
    main()

