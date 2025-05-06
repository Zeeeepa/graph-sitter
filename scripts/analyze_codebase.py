#!/usr/bin/env python
"""
Codebase Analysis Tool for Graph-Sitter

This script analyzes the graph-sitter codebase using its own analysis tools.
It provides a comprehensive overview of the codebase structure, including:
- Total number of files, code files, and documents
- Class hierarchy and inheritance depth
- Function statistics and error detection
- Main entry points and core functionality
- Symbol usage and dependencies

Usage:
    python scripts/analyze_codebase.py [--github-repo REPO_URL]

Options:
    --github-repo    GitHub repository URL to analyze (default: local codebase)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

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
from graph_sitter.enums import SymbolType
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


class CodebaseAnalyzer:
    """Analyzes a codebase using graph-sitter's own analysis tools."""

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the analyzer with a repository path.
        
        Args:
            repo_path: Path to the repository to analyze. If None, uses the current directory.
        """
        self.repo_path = repo_path or os.getcwd()
        self.codebase = self._load_codebase()
        self.errors: List[Tuple[str, str, str]] = []  # (file_path, function_name, error_message)
        
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
            "file_stats": self._get_file_stats(),
            "class_stats": self._get_class_stats(),
            "function_stats": self._get_function_stats(),
            "entry_points": self._find_entry_points(),
            "errors": self.errors
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
    
    def _get_file_stats(self) -> Dict:
        """Get statistics about files in the codebase."""
        source_files = [f for f in self.codebase.files if f.is_source_file]
        
        # Find largest files by line count
        largest_files = sorted(
            [(f, len(f.content.splitlines())) for f in source_files if hasattr(f, 'content')],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Find most complex files by symbol count
        most_complex_files = sorted(
            [(f, len(list(f.symbols))) for f in source_files],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "largest_files": [(f.path, lines) for f, lines in largest_files],
            "most_complex_files": [(f.path, symbols) for f, symbols in most_complex_files],
        }
    
    def _get_class_stats(self) -> Dict:
        """Get statistics about classes in the codebase."""
        classes = list(self.codebase.classes)
        
        # Calculate depth of inheritance for each class
        class_doi = {}
        for cls in classes:
            class_doi[cls.name] = self._calculate_doi(cls)
        
        # Find classes with deepest inheritance
        deepest_inheritance = sorted(
            [(name, depth) for name, depth in class_doi.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Find classes with most methods
        most_methods = sorted(
            [(cls.name, len(cls.methods)) for cls in classes],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "deepest_inheritance": deepest_inheritance,
            "most_methods": most_methods,
        }
    
    def _calculate_doi(self, cls: Class) -> int:
        """Calculate the depth of inheritance for a given class."""
        return len(cls.superclasses)
    
    def _get_function_stats(self) -> Dict:
        """Get statistics about functions in the codebase."""
        functions = list(self.codebase.functions)
        
        # Find functions with most parameters
        most_parameters = sorted(
            [(func.name, len(func.parameters)) for func in functions],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Find functions with most dependencies
        most_dependencies = sorted(
            [(func.name, len(func.dependencies)) for func in functions],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Find functions with potential errors (heuristic-based)
        for func in functions:
            self._check_function_for_errors(func)
        
        return {
            "most_parameters": most_parameters,
            "most_dependencies": most_dependencies,
            "total_functions": len(functions),
            "functions_with_errors": len(self.errors)
        }
    
    def _check_function_for_errors(self, func: Function) -> None:
        """
        Check a function for potential errors using heuristics.
        
        This is a simple demonstration and would need to be expanded for real error detection.
        """
        # Check for empty exception handlers
        if hasattr(func, 'content') and func.content:
            if "except:" in func.content and "pass" in func.content:
                file_path = func.file.path if hasattr(func, 'file') else "unknown"
                self.errors.append((file_path, func.name, "Empty exception handler"))
        
        # Check for very long functions (over 100 lines)
        if hasattr(func, 'content') and func.content:
            lines = func.content.splitlines()
            if len(lines) > 100:
                file_path = func.file.path if hasattr(func, 'file') else "unknown"
                self.errors.append((file_path, func.name, f"Very long function ({len(lines)} lines)"))
    
    def _find_entry_points(self) -> List[Dict]:
        """Find potential entry points to the codebase."""
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
                }
                
                # Check if the file has a main function
                if hasattr(file, 'functions'):
                    main_funcs = [f for f in file.functions if f.name == "main"]
                    if main_funcs:
                        entry_point["main_function"] = main_funcs[0].name
                
                entry_points.append(entry_point)
        
        return entry_points
    
    def print_analysis(self, results: Dict) -> None:
        """Print the analysis results in a readable format."""
        print("\n" + "="*80)
        print(f"GRAPH-SITTER CODEBASE ANALYSIS")
        print("="*80)
        
        # Print summary
        summary = results["summary"]
        print(f"\n## CODEBASE SUMMARY")
        print(f"Total files: {summary['total_files']}")
        print(f"  - Code files: {summary['total_code_files']}")
        print(f"  - Documentation files: {summary['total_doc_files']}")
        print(f"Total classes: {summary['total_classes']}")
        print(f"Total functions: {summary['total_functions']}")
        print(f"Total global variables: {summary['total_global_vars']}")
        
        print("\nProgramming Languages:")
        for lang, count in summary['programming_languages'].items():
            print(f"  - {lang}: {count} files")
        
        # Print entry points
        print(f"\n## MAIN ENTRY POINTS")
        for entry in results["entry_points"]:
            print(f"  - {entry['file']}")
            if "main_function" in entry:
                print(f"    Main function: {entry['main_function']}")
        
        # Print class stats
        print(f"\n## CLASS HIERARCHY")
        print("\nClasses with deepest inheritance:")
        for name, depth in results["class_stats"]["deepest_inheritance"]:
            print(f"  - {name}: {depth} levels")
        
        print("\nClasses with most methods:")
        for name, methods in results["class_stats"]["most_methods"]:
            print(f"  - {name}: {methods} methods")
        
        # Print function stats
        print(f"\n## FUNCTION STATISTICS")
        print("\nFunctions with most parameters:")
        for name, params in results["function_stats"]["most_parameters"]:
            print(f"  - {name}: {params} parameters")
        
        print("\nFunctions with most dependencies:")
        for name, deps in results["function_stats"]["most_dependencies"]:
            print(f"  - {name}: {deps} dependencies")
        
        # Print errors
        print(f"\n## POTENTIAL ISSUES")
        print(f"Found {len(results['errors'])} potential issues:")
        for file_path, func_name, error in results["errors"]:
            print(f"  - {file_path}: {func_name} - {error}")
        
        print("\n" + "="*80)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze a codebase using graph-sitter")
    parser.add_argument("--github-repo", help="GitHub repository URL to analyze", default=None)
    args = parser.parse_args()
    
    analyzer = CodebaseAnalyzer(args.github_repo)
    results = analyzer.analyze()
    analyzer.print_analysis(results)


if __name__ == "__main__":
    main()

