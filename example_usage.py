#!/usr/bin/env python3
"""
Example usage of the Serena analysis module.

This script demonstrates how to use the SerenaAnalysis and Codebase classes
to analyze a codebase and retrieve diagnostics.
"""

import os
import sys
from serena_analysis import Codebase, SerenaAnalysis

def example_codebase_usage():
    """Example usage of the Codebase class."""
    print("=== Example Codebase Usage ===")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize the Codebase with the current directory
    codebase = Codebase(current_dir)
    
    # Analyze the codebase
    errors = codebase.analyze_codebase()
    
    # Print the results
    print(f"Total issues found: {errors.get_error_count()}")
    print(f"Issues by severity: {errors.get_summary()}")
    print(f"Issues found in {errors.get_files_with_issues()} files")
    
    # Print some sample issues with context
    issues_with_context = errors.get_issues_with_context()
    for i, issue in enumerate(issues_with_context[:3]):  # Show up to 3 issues
        print(f"\nIssue {i+1}:")
        print(f"  File: {issue['file_path']}")
        print(f"  Line: {issue['line']}:{issue['column']}")
        print(f"  Level: {issue['level'].upper()}")
        print(f"  Message: {issue['message']}")
        
        # Print context if available
        if "file_context" in issue and "lines" in issue["file_context"]:
            print("  Context:")
            for j, (line_num, line_text) in enumerate(zip(
                issue["file_context"]["line_numbers"],
                issue["file_context"]["lines"]
            )):
                prefix = ">" if line_num == issue["line"] else " "
                print(f"    {prefix} {line_num+1}: {line_text.rstrip()}")
    
    if len(issues_with_context) > 3:
        print(f"\n... and {len(issues_with_context) - 3} more issues")
    
    # Save the results to a file
    errors.save_results("codebase_results.json")
    errors.save_context("codebase_context.json")


def example_serena_analysis_usage():
    """Example usage of the SerenaAnalysis class."""
    print("\n=== Example SerenaAnalysis Usage ===")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize the SerenaAnalysis with the current directory
    analysis = SerenaAnalysis(current_dir)
    
    # Analyze the codebase
    analysis.analyze_codebase()
    
    # Print the results
    print(f"Total issues found: {analysis.get_error_count()}")
    print(f"Issues by severity: {analysis.get_summary()}")
    print(f"Issues found in {analysis.get_files_with_issues()} files")
    
    # Get errors by severity
    error_issues = analysis.get_errors_by_severity("error")
    warning_issues = analysis.get_errors_by_severity("warning")
    info_issues = analysis.get_errors_by_severity("info")
    hint_issues = analysis.get_errors_by_severity("hint")
    
    print(f"\nErrors: {len(error_issues)}")
    print(f"Warnings: {len(warning_issues)}")
    print(f"Info: {len(info_issues)}")
    print(f"Hints: {len(hint_issues)}")
    
    # Save the results to a file
    analysis.save_results("analysis_results.json")
    analysis.save_context("analysis_context.json")


if __name__ == "__main__":
    # Run the examples
    example_codebase_usage()
    example_serena_analysis_usage()

