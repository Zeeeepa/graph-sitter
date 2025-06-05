"""
Analysis module for comprehensive code analysis.

This module provides advanced code analysis capabilities following the patterns
from https://graph-sitter.com/tutorials/at-a-glance with enhanced issue detection
and comprehensive reporting.

Usage:
    from graph_sitter import Codebase
    
    # Analyze local repository
    codebase = Codebase("path/to/git/repo")
    result = codebase.Analysis()
    
    # Analyze remote repository  
    codebase = Codebase.from_repo("fastapi/fastapi")
    result = codebase.Analysis()
"""

from .analysis import (
    # Core classes
    CodeAnalyzer,
    AnalysisResult,
    CodeIssue,
    DeadCodeItem,
    FunctionMetrics,
    ClassMetrics,
    FileIssueInfo,
    InheritanceInfo,
    
    # Main functions
    analyze_codebase,
    analyze_and_print,
    format_analysis_results,
    add_analysis_method,
)

__all__ = [
    # Core classes
    "CodeAnalyzer",
    "AnalysisResult", 
    "CodeIssue",
    "DeadCodeItem",
    "FunctionMetrics",
    "ClassMetrics",
    "FileIssueInfo",
    "InheritanceInfo",
    
    # Main functions
    "analyze_codebase",
    "analyze_and_print", 
    "format_analysis_results",
    "add_analysis_method",
]
