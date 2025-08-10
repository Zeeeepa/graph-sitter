#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis System for Graph-Sitter
Provides detailed analysis, error detection, and reporting capabilities.
"""

import os
import sys
import json
import math
import traceback
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum

# Graph-sitter imports
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary
)
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.enums import SymbolType, NodeType, EdgeType
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile


class IssueSeverity(Enum):
    """Issue severity levels for error classification"""
    CRITICAL = "⚠️"
    MAJOR = "👉"
    MINOR = "🔍"


@dataclass
class Issue:
    """Represents a code issue with severity and context"""
    severity: IssueSeverity
    message: str
    filepath: str
    line_number: int = 0
    function_name: str = ""
    class_name: str = ""
    symbol_type: str = ""
    
    def __str__(self) -> str:
        location = f"{self.filepath}"
        if self.function_name:
            location += f" / Function - '{self.function_name}'"
        elif self.class_name:
            location += f" / Class - '{self.class_name}'"
        return f"{self.severity.value}- {location} [{self.message}]"


@dataclass
class AnalysisResults:
    """Container for comprehensive analysis results"""
    summary: Dict[str, Any] = field(default_factory=dict)
    most_important_functions: Dict[str, Any] = field(default_factory=dict)
    function_contexts: Dict[str, Any] = field(default_factory=dict)
    issues_by_severity: Dict[str, List[Issue]] = field(default_factory=dict)
    dead_code_analysis: Dict[str, Any] = field(default_factory=dict)
    halstead_metrics: Dict[str, float] = field(default_factory=dict)
    directory_tree: Dict[str, Any] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)


def load_codebase(repo_path: str, config: Optional[CodebaseConfig] = None) -> Codebase:
    """Load a codebase with proper configuration"""
    if config is None:
        config = CodebaseConfig(exp_lazy_graph=True)
    
    try:
        codebase = Codebase(repo_path, config=config)
        return codebase
    except Exception as e:
        print(f"Error loading codebase: {e}")
        raise


def detect_issues(codebase: Codebase) -> List[Issue]:
    """Detect various code issues and classify by severity"""
    issues = []
    
    try:
        # Analyze functions for issues
        for func in codebase.functions:
            issues.extend(_analyze_function_issues(func))
        
        # Analyze classes for issues
        for cls in codebase.classes:
            issues.extend(_analyze_class_issues(cls))
        
        # Analyze files for issues
        for file in codebase.files:
            issues.extend(_analyze_file_issues(file))
            
    except Exception as e:
        issues.append(Issue(
            severity=IssueSeverity.CRITICAL,
            message=f"Analysis error: {str(e)}",
            filepath="<analysis_system>",
            line_number=0
        ))
    
    return issues


def _analyze_function_issues(func: Function) -> List[Issue]:
    """Analyze a function for potential issues"""
    issues = []
    
    try:
        filepath = getattr(func, 'filepath', 'unknown')
        
        # Check for functions with no return statements
        if len(func.return_statements) == 0 and not func.name.startswith('__'):
            issues.append(Issue(
                severity=IssueSeverity.MINOR,
                message="Function has no return statements",
                filepath=filepath,
                function_name=func.name,
                symbol_type="Function"
            ))
        
        # Check for functions with too many parameters
        if len(func.parameters) > 7:
            issues.append(Issue(
                severity=IssueSeverity.MAJOR,
                message=f"Function has {len(func.parameters)} parameters (>7)",
                filepath=filepath,
                function_name=func.name,
                symbol_type="Function"
            ))
        
        # Check for unused functions (no call sites)
        if len(func.call_sites) == 0 and not func.name.startswith('_'):
            issues.append(Issue(
                severity=IssueSeverity.MINOR,
                message="Function appears to be unused",
                filepath=filepath,
                function_name=func.name,
                symbol_type="Function"
            ))
        
        # Check for functions with many function calls (complexity)
        if len(func.function_calls) > 20:
            issues.append(Issue(
                severity=IssueSeverity.MAJOR,
                message=f"Function has high complexity ({len(func.function_calls)} calls)",
                filepath=filepath,
                function_name=func.name,
                symbol_type="Function"
            ))
            
    except Exception as e:
        issues.append(Issue(
            severity=IssueSeverity.CRITICAL,
            message=f"Error analyzing function: {str(e)}",
            filepath=getattr(func, 'filepath', 'unknown'),
            function_name=getattr(func, 'name', 'unknown'),
            symbol_type="Function"
        ))
    
    return issues


def _analyze_class_issues(cls: Class) -> List[Issue]:
    """Analyze a class for potential issues"""
    issues = []
    
    try:
        filepath = getattr(cls, 'filepath', 'unknown')
        
        # Check for classes with too many methods
        if len(cls.methods) > 20:
            issues.append(Issue(
                severity=IssueSeverity.MAJOR,
                message=f"Class has {len(cls.methods)} methods (>20)",
                filepath=filepath,
                class_name=cls.name,
                symbol_type="Class"
            ))
        
        # Check for classes with no methods
        if len(cls.methods) == 0:
            issues.append(Issue(
                severity=IssueSeverity.MINOR,
                message="Class has no methods",
                filepath=filepath,
                class_name=cls.name,
                symbol_type="Class"
            ))
            
    except Exception as e:
        issues.append(Issue(
            severity=IssueSeverity.CRITICAL,
            message=f"Error analyzing class: {str(e)}",
            filepath=getattr(cls, 'filepath', 'unknown'),
            class_name=getattr(cls, 'name', 'unknown'),
            symbol_type="Class"
        ))
    
    return issues


def _analyze_file_issues(file: SourceFile) -> List[Issue]:
    """Analyze a file for potential issues"""
    issues = []
    
    try:
        filepath = getattr(file, 'filepath', file.name)
        
        # Check for files with too many lines
        source = getattr(file, 'source', '')
        if source:
            line_count = len(source.split('\n'))
            if line_count > 1000:
                issues.append(Issue(
                    severity=IssueSeverity.MAJOR,
                    message=f"File has {line_count} lines (>1000)",
                    filepath=filepath,
                    symbol_type="File"
                ))
        
        # Check for files with too many imports
        if len(file.imports) > 50:
            issues.append(Issue(
                severity=IssueSeverity.MINOR,
                message=f"File has {len(file.imports)} imports (>50)",
                filepath=filepath,
                symbol_type="File"
            ))
            
    except Exception as e:
        issues.append(Issue(
            severity=IssueSeverity.CRITICAL,
            message=f"Error analyzing file: {str(e)}",
            filepath=getattr(file, 'filepath', getattr(file, 'name', 'unknown')),
            symbol_type="File"
        ))
    
    return issues


def calculate_halstead_metrics(codebase: Codebase) -> Dict[str, float]:
    """Calculate Halstead complexity metrics"""
    operators = set()
    operands = set()
    total_operators = 0
    total_operands = 0
    
    try:
        # Simple approximation - count function calls as operators
        # and symbols as operands
        for func in codebase.functions:
            operators.add(func.name)
            total_operators += len(func.function_calls)
            total_operands += len(func.parameters)
        
        for symbol in codebase.symbols:
            operands.add(symbol.name)
            total_operands += len(symbol.symbol_usages)
    
        n1 = len(operators)  # Unique operators
        n2 = len(operands)   # Unique operands
        N1 = total_operators # Total operators
        N2 = total_operands  # Total operands
        
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            'n1': n1,
            'n2': n2,
            'N1': N1,
            'N2': N2,
            'vocabulary': vocabulary,
            'length': length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort
        }
    except Exception as e:
        print(f"Error calculating Halstead metrics: {e}")
        return {}


def find_entry_points(codebase: Codebase) -> List[str]:
    """Find entry point files and functions"""
    entry_points = []
    
    try:
        # Look for main functions
        for func in codebase.functions:
            if func.name in ['main', '__main__', 'run', 'start', 'init']:
                entry_points.append(f"{func.filepath}::{func.name}")
        
        # Look for files with high import usage (likely entry points)
        for file in codebase.files:
            if len(file.imports) > 10:  # Files that import many modules
                entry_points.append(file.filepath if hasattr(file, 'filepath') else file.name)
                
    except Exception as e:
        print(f"Error finding entry points: {e}")
    
    return entry_points


def analyze_codebase(codebase: Codebase) -> AnalysisResults:
    """Perform comprehensive codebase analysis"""
    results = AnalysisResults()
    
    try:
        # Basic summary
        total_files = len(list(codebase.files))
        total_functions = len(list(codebase.functions))
        total_classes = len(list(codebase.classes))
        total_symbols = len(list(codebase.symbols))
        
        # Detect issues
        all_issues = detect_issues(codebase)
        
        # Categorize issues by severity
        issues_by_severity = {
            'critical': [i for i in all_issues if i.severity == IssueSeverity.CRITICAL],
            'major': [i for i in all_issues if i.severity == IssueSeverity.MAJOR],
            'minor': [i for i in all_issues if i.severity == IssueSeverity.MINOR]
        }
        
        # Calculate metrics
        halstead_metrics = calculate_halstead_metrics(codebase)
        entry_points = find_entry_points(codebase)
        
        # Find most important functions
        most_important = _find_most_important_functions(codebase)
        
        # Build results
        results.summary = {
            'total_files': total_files,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_symbols': total_symbols,
            'total_issues': len(all_issues),
            'critical_issues': len(issues_by_severity['critical']),
            'major_issues': len(issues_by_severity['major']),
            'minor_issues': len(issues_by_severity['minor']),
            'entry_points': len(entry_points)
        }
        
        results.issues_by_severity = issues_by_severity
        results.halstead_metrics = halstead_metrics
        results.entry_points = entry_points
        results.most_important_functions = most_important
        
    except Exception as e:
        print(f"Error in comprehensive analysis: {e}")
        traceback.print_exc()
    
    return results


def _find_most_important_functions(codebase: Codebase) -> Dict[str, Any]:
    """Find the most important functions based on usage patterns"""
    try:
        functions = list(codebase.functions)
        if not functions:
            return {}
        
        # Find function with most calls
        most_calls = max(functions, key=lambda f: len(f.function_calls), default=None)
        
        # Find most called function
        most_called = max(functions, key=lambda f: len(f.call_sites), default=None)
        
        return {
            'most_calls': {
                'name': most_calls.name if most_calls else 'N/A',
                'call_count': len(most_calls.function_calls) if most_calls else 0,
                'calls': [call.name for call in most_calls.function_calls[:5]] if most_calls else []
            },
            'most_called': {
                'name': most_called.name if most_called else 'N/A',
                'usage_count': len(most_called.call_sites) if most_called else 0
            }
        }
    except Exception as e:
        print(f"Error finding important functions: {e}")
        return {}


if __name__ == "__main__":
    # Basic test
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
        print(f"Analyzing codebase: {repo_path}")
        
        try:
            codebase = load_codebase(repo_path)
            results = analyze_codebase(codebase)
            
            print("\n🔍 ANALYSIS SUMMARY:")
            print("-" * 30)
            for key, value in results.summary.items():
                print(f"{key}: {value}")
                
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
    else:
        print("Usage: python analysis.py <repo_path>")
