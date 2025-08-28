#!/usr/bin/env python3
"""
Serena analysis module for codebase diagnostics.

This module provides a high-level interface for analyzing codebases using Serena,
with a focus on simplicity and ease of use.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path

# Import from serena_adapter
from serena_adapter import SerenaAdapter, DiagnosticLevel, SerenaIssue, setup_serena_environment

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class SerenaAnalysis:
    """High-level interface for analyzing codebases using Serena."""
    
    def __init__(self, project_path: str):
        """Initialize the SerenaAnalysis.
        
        Args:
            project_path: Path to the project to analyze.
        """
        self.project_path = os.path.abspath(project_path)
        self.adapter = None
        self.errors = None
        self.context = {}
        
        # Check if Serena is installed
        if not setup_serena_environment():
            log.error("Serena environment setup failed")
            return
        
        # Initialize the adapter
        try:
            self.adapter = SerenaAdapter(self.project_path)
            log.info(f"Initialized SerenaAnalysis for project at {self.project_path}")
        except Exception as e:
            log.error(f"Failed to initialize SerenaAnalysis: {e}")
    
    def analyze_codebase(self, 
                        relative_path: str = "", 
                        filter_level: Optional[DiagnosticLevel] = None) -> Dict[str, Any]:
        """Analyze the entire codebase or a subdirectory.
        
        Args:
            relative_path: Optional path to a subdirectory to analyze, relative to the project root.
            filter_level: Optional severity level to filter diagnostics by.
            
        Returns:
            Self for method chaining.
        """
        if not self.adapter:
            log.error("SerenaAnalysis not initialized")
            self.errors = {
                "error": "SerenaAnalysis not initialized",
                "total_issues": 0,
                "summary": {},
                "issues_by_file": {},
            }
            return self
        
        try:
            # Analyze the codebase using the adapter
            self.errors = self.adapter.analyze_codebase(relative_path, filter_level)
            
            # Build context with detailed information
            self._build_context()
            
            return self
        except Exception as e:
            log.error(f"Error analyzing codebase: {e}")
            self.errors = {
                "error": str(e),
                "total_issues": 0,
                "summary": {},
                "issues_by_file": {},
            }
            return self
    
    def _build_context(self):
        """Build context with detailed information about the issues."""
        if not self.errors:
            self.context = {}
            return
        
        # Initialize context
        self.context = {
            "total_issues": self.errors.get("total_issues", 0),
            "summary": self.errors.get("summary", {}),
            "files_with_issues": len(self.errors.get("issues_by_file", {})),
            "issues_by_severity": {},
            "issues_with_context": [],
        }
        
        # Group issues by severity
        for file_path, issues in self.errors.get("issues_by_file", {}).items():
            for issue in issues:
                severity = issue.get("level", "info")
                if severity not in self.context["issues_by_severity"]:
                    self.context["issues_by_severity"][severity] = []
                self.context["issues_by_severity"][severity].append(issue)
        
        # Add issues with context
        for file_path, issues in self.errors.get("issues_by_file", {}).items():
            for issue in issues:
                # Add file context
                issue_with_context = issue.copy()
                issue_with_context["file_context"] = self._get_file_context(
                    file_path, issue.get("line", 0), issue.get("column", 0)
                )
                self.context["issues_with_context"].append(issue_with_context)
    
    def _get_file_context(self, file_path: str, line: int, column: int, context_lines: int = 3) -> Dict[str, Any]:
        """Get context around a specific line in a file.
        
        Args:
            file_path: Path to the file.
            line: Line number (0-based).
            column: Column number (0-based).
            context_lines: Number of lines of context to include before and after.
            
        Returns:
            Dictionary containing file context information.
        """
        try:
            # Get the absolute file path
            abs_file_path = os.path.join(self.project_path, file_path)
            
            # Check if the file exists
            if not os.path.exists(abs_file_path):
                return {
                    "error": f"File not found: {file_path}",
                    "lines": [],
                    "line_numbers": [],
                }
            
            # Read the file
            with open(abs_file_path, 'r', encoding='utf-8', errors='replace') as f:
                file_lines = f.readlines()
            
            # Calculate the range of lines to include
            start_line = max(0, line - context_lines)
            end_line = min(len(file_lines), line + context_lines + 1)
            
            # Extract the lines
            context_lines = file_lines[start_line:end_line]
            line_numbers = list(range(start_line, end_line))
            
            # Get the containing symbol if available
            containing_symbol = None
            if self.adapter:
                try:
                    containing_symbol = self.adapter.get_containing_symbol(file_path, line, column)
                except Exception:
                    pass
            
            return {
                "lines": context_lines,
                "line_numbers": line_numbers,
                "highlight_line": line,
                "containing_symbol": containing_symbol,
            }
        except Exception as e:
            return {
                "error": str(e),
                "lines": [],
                "line_numbers": [],
            }
    
    def get_errors_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get errors filtered by severity.
        
        Args:
            severity: Severity level to filter by (error, warning, info, hint).
            
        Returns:
            List of errors with the specified severity.
        """
        if not self.context:
            return []
        
        return self.context.get("issues_by_severity", {}).get(severity, [])
    
    def get_error_count(self) -> int:
        """Get the total number of errors.
        
        Returns:
            Total number of errors.
        """
        if not self.context:
            return 0
        
        return self.context.get("total_issues", 0)
    
    def get_summary(self) -> Dict[str, int]:
        """Get a summary of errors by severity.
        
        Returns:
            Dictionary mapping severity levels to counts.
        """
        if not self.context:
            return {}
        
        return self.context.get("summary", {})
    
    def get_files_with_issues(self) -> int:
        """Get the number of files with issues.
        
        Returns:
            Number of files with issues.
        """
        if not self.context:
            return 0
        
        return self.context.get("files_with_issues", 0)
    
    def get_issues_with_context(self) -> List[Dict[str, Any]]:
        """Get all issues with context.
        
        Returns:
            List of issues with context.
        """
        if not self.context:
            return []
        
        return self.context.get("issues_with_context", [])
    
    def save_results(self, output_file: str):
        """Save analysis results to a file.
        
        Args:
            output_file: Path to the output file.
        """
        if not self.errors:
            log.error("No analysis results to save")
            return
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.errors, f, indent=2)
            log.info(f"Analysis results saved to {output_file}")
        except Exception as e:
            log.error(f"Error saving results to {output_file}: {e}")
    
    def save_context(self, output_file: str):
        """Save analysis context to a file.
        
        Args:
            output_file: Path to the output file.
        """
        if not self.context:
            log.error("No analysis context to save")
            return
        
        try:
            # Convert context to a serializable format
            serializable_context = self.context.copy()
            
            # Handle file context lines (convert to strings)
            for issue in serializable_context.get("issues_with_context", []):
                if "file_context" in issue and "lines" in issue["file_context"]:
                    issue["file_context"]["lines"] = [
                        line.rstrip() for line in issue["file_context"]["lines"]
                    ]
            
            with open(output_file, 'w') as f:
                json.dump(serializable_context, f, indent=2)
            log.info(f"Analysis context saved to {output_file}")
        except Exception as e:
            log.error(f"Error saving context to {output_file}: {e}")


class Codebase:
    """Simple interface for analyzing a codebase using Serena."""
    
    def __init__(self, project_path: str):
        """Initialize the Codebase.
        
        Args:
            project_path: Path to the project to analyze.
        """
        self.project_path = os.path.abspath(project_path)
        self.analysis = SerenaAnalysis(self.project_path)
        self.context = {}
    
    def analyze_codebase(self, 
                        relative_path: str = "", 
                        filter_level: Optional[str] = None) -> "Codebase":
        """Analyze the codebase.
        
        Args:
            relative_path: Optional path to a subdirectory to analyze, relative to the project root.
            filter_level: Optional severity level to filter diagnostics by (error, warning, info, hint).
            
        Returns:
            Self for method chaining.
        """
        # Convert string filter_level to DiagnosticLevel enum if provided
        enum_filter_level = None
        if filter_level:
            try:
                enum_filter_level = DiagnosticLevel(filter_level)
            except ValueError:
                log.warning(f"Invalid filter level: {filter_level}")
        
        # Analyze the codebase
        self.analysis.analyze_codebase(relative_path, enum_filter_level)
        
        # Copy context
        self.context = self.analysis.context
        
        return self
    
    def save_results(self, output_file: str):
        """Save analysis results to a file.
        
        Args:
            output_file: Path to the output file.
        """
        self.analysis.save_results(output_file)
    
    def save_context(self, output_file: str):
        """Save analysis context to a file.
        
        Args:
            output_file: Path to the output file.
        """
        self.analysis.save_context(output_file)
    
    def get_error_count(self) -> int:
        """Get the total number of errors.
        
        Returns:
            Total number of errors.
        """
        return self.analysis.get_error_count()
    
    def get_summary(self) -> Dict[str, int]:
        """Get a summary of errors by severity.
        
        Returns:
            Dictionary mapping severity levels to counts.
        """
        return self.analysis.get_summary()
    
    def get_files_with_issues(self) -> int:
        """Get the number of files with issues.
        
        Returns:
            Number of files with issues.
        """
        return self.analysis.get_files_with_issues()
    
    def get_issues_with_context(self) -> List[Dict[str, Any]]:
        """Get all issues with context.
        
        Returns:
            List of issues with context.
        """
        return self.analysis.get_issues_with_context()


if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze a codebase using Serena.")
    parser.add_argument("project_path", help="Path to the project to analyze")
    parser.add_argument(
        "--path", "-p", default="", help="Relative path within the project to analyze"
    )
    parser.add_argument(
        "--output", "-o", help="Output file for analysis results (JSON format)"
    )
    parser.add_argument(
        "--context-output", "-c", help="Output file for analysis context (JSON format)"
    )
    parser.add_argument(
        "--severity", "-s", choices=["error", "warning", "info", "hint"],
        help="Filter diagnostics by severity level"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate project path
    project_path = os.path.abspath(args.project_path)
    if not os.path.exists(project_path):
        log.error(f"Project path does not exist: {project_path}")
        sys.exit(1)
    
    # Initialize and analyze the codebase
    codebase = Codebase(project_path)
    codebase.analyze_codebase(args.path, args.severity)
    
    # Print summary
    log.info(f"Total issues found: {codebase.get_error_count()}")
    log.info(f"Issues by severity: {codebase.get_summary()}")
    log.info(f"Issues found in {codebase.get_files_with_issues()} files")
    
    # Print some sample issues
    issues_with_context = codebase.get_issues_with_context()
    for i, issue in enumerate(issues_with_context[:5]):  # Show up to 5 issues
        log.info(f"\nIssue {i+1}:")
        log.info(f"  File: {issue['file_path']}")
        log.info(f"  Line: {issue['line']}:{issue['column']}")
        log.info(f"  Level: {issue['level'].upper()}")
        log.info(f"  Message: {issue['message']}")
        
        # Print context if available
        if "file_context" in issue and "lines" in issue["file_context"]:
            log.info("  Context:")
            for j, (line_num, line_text) in enumerate(zip(
                issue["file_context"]["line_numbers"],
                issue["file_context"]["lines"]
            )):
                prefix = ">" if line_num == issue["line"] else " "
                log.info(f"    {prefix} {line_num+1}: {line_text.rstrip()}")
    
    if len(issues_with_context) > 5:
        log.info(f"\n... and {len(issues_with_context) - 5} more issues")
    
    # Output results
    if args.output:
        codebase.save_results(args.output)
    
    # Output context
    if args.context_output:
        codebase.save_context(args.context_output)

