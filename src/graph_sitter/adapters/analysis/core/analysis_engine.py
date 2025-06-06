#!/usr/bin/env python3
"""
Core Analysis Engine for Graph-Sitter Analysis System

This module contains the core analysis functions consolidated from the original
analysis files, providing both AST-based and graph-sitter enhanced analysis capabilities.
"""

import ast
import logging
import math
import os
import re
import sys
import time
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

# Import models
from .models import (
    CodeIssue, DeadCodeItem, FunctionMetrics, ClassMetrics, FileAnalysis,
    ComprehensiveAnalysisResult, AnalysisOptions, AnalysisContext
)

# Try to import graph-sitter dependencies
try:
    from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
    from graph_sitter.core.statements.if_block_statement import IfBlockStatement
    from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
    from graph_sitter.core.statements.while_statement import WhileStatement
    from graph_sitter.core.expressions.binary_expression import BinaryExpression
    from graph_sitter.core.expressions.unary_expression import UnaryExpression
    from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    logger.warning("Graph-sitter not available - using AST-based analysis only")
    GRAPH_SITTER_AVAILABLE = False
    # Create dummy classes for type hints
    ForLoopStatement = None
    IfBlockStatement = None
    TryCatchStatement = None
    WhileStatement = None
    BinaryExpression = None
    UnaryExpression = None
    ComparisonExpression = None


# ============================================================================
# CORE METRICS CALCULATION FUNCTIONS
# ============================================================================

def calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity for AST node (fallback method)."""
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.Try):
            complexity += len(child.handlers)
        elif isinstance(child, (ast.And, ast.Or)):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
    
    return complexity


def calculate_cyclomatic_complexity_graph_sitter(function) -> int:
    """Enhanced cyclomatic complexity calculation using Graph-Sitter."""
    if not GRAPH_SITTER_AVAILABLE or not hasattr(function, 'code_block'):
        return 1
    
    def analyze_statement(statement):
        complexity = 0

        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

        elif isinstance(statement, (ForLoopStatement, WhileStatement)):
            complexity += 1

        elif isinstance(statement, TryCatchStatement):
            complexity += len(getattr(statement, "catch_statements", []))

        # Recursively analyze nested statements
        if hasattr(statement, "statements"):
            for nested_statement in statement.statements:
                complexity += analyze_statement(nested_statement)

        return complexity

    total_complexity = 1  # Base complexity
    
    try:
        if hasattr(function.code_block, "statements"):
            for statement in function.code_block.statements:
                total_complexity += analyze_statement(statement)
    except Exception as e:
        logger.debug(f"Error calculating complexity for {function.name}: {e}")
        return 1

    return total_complexity


def get_operators_and_operands(function) -> Tuple[List[str], List[str]]:
    """Extract operators and operands for Halstead metrics."""
    operators = []
    operands = []
    
    if not hasattr(function, 'source'):
        return operators, operands
    
    try:
        # Parse the function source code
        tree = ast.parse(function.source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                operators.append(type(node.op).__name__)
            elif isinstance(node, ast.UnaryOp):
                operators.append(type(node.op).__name__)
            elif isinstance(node, ast.Compare):
                operators.extend([type(op).__name__ for op in node.ops])
            elif isinstance(node, ast.Name):
                operands.append(node.id)
            elif isinstance(node, ast.Constant):
                operands.append(str(node.value))
            elif isinstance(node, ast.Call):
                if hasattr(node.func, 'id'):
                    operators.append(node.func.id)
                elif hasattr(node.func, 'attr'):
                    operators.append(node.func.attr)
    except Exception as e:
        logger.debug(f"Error extracting operators/operands: {e}")
    
    return operators, operands


def calculate_halstead_volume(operators: List[str], operands: List[str]) -> Tuple[float, int, int, int, int]:
    """Calculate Halstead volume and related metrics."""
    if not operators and not operands:
        return 0.0, 0, 0, 0, 0
    
    # Count unique and total operators/operands
    unique_operators = len(set(operators))
    unique_operands = len(set(operands))
    total_operators = len(operators)
    total_operands = len(operands)
    
    # Calculate vocabulary and length
    vocabulary = unique_operators + unique_operands
    length = total_operators + total_operands
    
    # Calculate volume
    if vocabulary > 0:
        volume = length * math.log2(vocabulary)
    else:
        volume = 0.0
    
    return volume, unique_operators, unique_operands, total_operators, total_operands


def calculate_maintainability_index(volume: float, complexity: int, loc: int) -> int:
    """Calculate maintainability index."""
    if loc == 0:
        return 100
    
    try:
        # Standard maintainability index formula
        mi = 171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc)
        mi = max(0, min(100, mi))  # Clamp between 0 and 100
        return int(mi)
    except (ValueError, ZeroDivisionError):
        return 100


def calculate_doi(cls) -> int:
    """Calculate depth of inheritance for a class."""
    if not hasattr(cls, 'superclasses'):
        return 0
    
    max_depth = 0
    for superclass in cls.superclasses:
        if hasattr(superclass, 'superclasses'):
            depth = 1 + calculate_doi(superclass)
            max_depth = max(max_depth, depth)
        else:
            max_depth = max(max_depth, 1)
    
    return max_depth


def count_lines(source_code: str) -> Tuple[int, int, int, int]:
    """Count different types of lines in source code."""
    if not source_code:
        return 0, 0, 0, 0
    
    lines = source_code.split('\n')
    loc = len(lines)  # Total lines
    sloc = 0  # Source lines (non-empty, non-comment)
    comments = 0  # Comment lines
    
    in_multiline_string = False
    string_delimiter = None
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            continue  # Empty line
        
        # Handle multiline strings/comments
        if in_multiline_string:
            if string_delimiter in stripped:
                in_multiline_string = False
                string_delimiter = None
            comments += 1
            continue
        
        # Check for start of multiline string
        if stripped.startswith('"""') or stripped.startswith("'''"):
            delimiter = stripped[:3]
            if stripped.count(delimiter) == 1:  # Opening delimiter only
                in_multiline_string = True
                string_delimiter = delimiter
            comments += 1
            continue
        
        # Single line comment
        if stripped.startswith('#'):
            comments += 1
            continue
        
        # Source line
        sloc += 1
    
    lloc = sloc  # Logical lines (simplified as source lines)
    
    return loc, lloc, sloc, comments


# ============================================================================
# FILE ANALYSIS FUNCTIONS
# ============================================================================

def analyze_python_file(file_path: str, options: AnalysisOptions) -> FileAnalysis:
    """Analyze a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return FileAnalysis(
            file_path=file_path,
            lines_of_code=0,
            logical_lines=0,
            source_lines=0,
            comment_lines=0,
            comment_density=0.0
        )
    
    # Count lines
    loc, lloc, sloc, comments = count_lines(source_code)
    comment_density = (comments / loc * 100) if loc > 0 else 0.0
    
    # Parse AST for analysis
    functions = []
    classes = []
    issues = []
    imports = []
    
    try:
        tree = ast.parse(source_code)
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                else:
                    module = node.module or ""
                    imports.extend([f"{module}.{alias.name}" for alias in node.names])
        
        # Analyze functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_metrics = analyze_function_ast(node, file_path, source_code)
                functions.append(func_metrics)
                
                # Check for issues
                if func_metrics.cyclomatic_complexity > options.max_complexity:
                    issues.append(CodeIssue(
                        type="complexity",
                        severity="major",
                        message=f"High cyclomatic complexity: {func_metrics.cyclomatic_complexity}",
                        file_path=file_path,
                        line_start=func_metrics.line_start,
                        line_end=func_metrics.line_end,
                        suggestion=f"Consider breaking down function '{func_metrics.name}' into smaller functions"
                    ))
                
                if func_metrics.maintainability_index < options.min_maintainability:
                    issues.append(CodeIssue(
                        type="maintainability",
                        severity="major",
                        message=f"Low maintainability index: {func_metrics.maintainability_index}",
                        file_path=file_path,
                        line_start=func_metrics.line_start,
                        line_end=func_metrics.line_end,
                        suggestion=f"Improve code quality for function '{func_metrics.name}'"
                    ))
        
        # Analyze classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_metrics = analyze_class_ast(node, file_path)
                classes.append(class_metrics)
    
    except SyntaxError as e:
        issues.append(CodeIssue(
            type="syntax",
            severity="critical",
            message=f"Syntax error: {e.msg}",
            file_path=file_path,
            line_start=e.lineno or 0,
            suggestion="Fix syntax error"
        ))
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        issues.append(CodeIssue(
            type="analysis",
            severity="minor",
            message=f"Analysis error: {str(e)}",
            file_path=file_path,
            line_start=0,
            suggestion="Check file for parsing issues"
        ))
    
    return FileAnalysis(
        file_path=file_path,
        lines_of_code=loc,
        logical_lines=lloc,
        source_lines=sloc,
        comment_lines=comments,
        comment_density=comment_density,
        functions=functions,
        classes=classes,
        issues=issues,
        imports=imports,
        complexity_score=sum(f.cyclomatic_complexity for f in functions) / len(functions) if functions else 0.0
    )


def analyze_function_ast(node: ast.FunctionDef, file_path: str, source_code: str) -> FunctionMetrics:
    """Analyze a function using AST."""
    # Extract function source
    lines = source_code.split('\n')
    func_lines = lines[node.lineno-1:node.end_lineno] if hasattr(node, 'end_lineno') else lines[node.lineno-1:]
    func_source = '\n'.join(func_lines)
    
    # Calculate metrics
    complexity = calculate_cyclomatic_complexity(node)
    
    # Extract operators and operands for Halstead metrics
    operators = []
    operands = []
    for child in ast.walk(node):
        if isinstance(child, ast.BinOp):
            operators.append(type(child.op).__name__)
        elif isinstance(child, ast.Name):
            operands.append(child.id)
        elif isinstance(child, ast.Constant):
            operands.append(str(child.value))
    
    volume, n1, n2, N1, N2 = calculate_halstead_volume(operators, operands)
    
    # Count lines
    func_loc = len(func_lines)
    mi = calculate_maintainability_index(volume, complexity, func_loc)
    
    # Count parameters and return statements
    param_count = len(node.args.args)
    return_count = len([n for n in ast.walk(node) if isinstance(n, ast.Return)])
    
    return FunctionMetrics(
        name=node.name,
        file_path=file_path,
        line_start=node.lineno,
        line_end=getattr(node, 'end_lineno', node.lineno),
        cyclomatic_complexity=complexity,
        halstead_volume=volume,
        maintainability_index=mi,
        lines_of_code=func_loc,
        parameters_count=param_count,
        return_statements=return_count,
        loc=func_loc,
        halstead_n1=n1,
        halstead_n2=n2,
        halstead_N1=N1,
        halstead_N2=N2
    )


def analyze_class_ast(node: ast.ClassDef, file_path: str) -> ClassMetrics:
    """Analyze a class using AST."""
    # Count methods and attributes
    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    attributes = []
    
    # Look for attribute assignments in __init__ and class body
    for child in ast.walk(node):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Attribute):
                    attributes.append(target.attr)
                elif isinstance(target, ast.Name):
                    attributes.append(target.id)
    
    # Calculate depth of inheritance
    doi = len(node.bases)  # Simplified - just count direct bases
    
    return ClassMetrics(
        name=node.name,
        file_path=file_path,
        line_start=node.lineno,
        line_end=getattr(node, 'end_lineno', node.lineno),
        depth_of_inheritance=doi,
        method_count=len(methods),
        attribute_count=len(set(attributes)),
        lines_of_code=getattr(node, 'end_lineno', node.lineno) - node.lineno + 1,
        parent_classes=[base.id for base in node.bases if isinstance(base, ast.Name)]
    )


# ============================================================================
# CODEBASE ANALYSIS FUNCTIONS
# ============================================================================

def analyze_codebase_directory(path: str, options: AnalysisOptions) -> ComprehensiveAnalysisResult:
    """Analyze a complete codebase directory."""
    start_time = time.time()
    
    # Find all Python files
    python_files = []
    extensions = options.extensions or ['.py']
    
    for root, dirs, files in os.walk(path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                python_files.append(os.path.join(root, file))
    
    # Analyze each file
    file_analyses = []
    all_issues = []
    all_functions = []
    all_classes = []
    
    for file_path in python_files:
        file_analysis = analyze_python_file(file_path, options)
        file_analyses.append(file_analysis)
        all_issues.extend(file_analysis.issues)
        all_functions.extend(file_analysis.functions)
        all_classes.extend(file_analysis.classes)
    
    # Calculate aggregate metrics
    total_files = len(file_analyses)
    total_functions = len(all_functions)
    total_classes = len(all_classes)
    total_lines = sum(f.lines_of_code for f in file_analyses)
    total_logical_lines = sum(f.logical_lines for f in file_analyses)
    total_source_lines = sum(f.source_lines for f in file_analyses)
    total_comment_lines = sum(f.comment_lines for f in file_analyses)
    
    # Calculate averages
    avg_maintainability = sum(f.maintainability_index for f in all_functions) / len(all_functions) if all_functions else 0.0
    avg_complexity = sum(f.cyclomatic_complexity for f in all_functions) / len(all_functions) if all_functions else 0.0
    avg_halstead = sum(f.halstead_volume for f in all_functions) / len(all_functions) if all_functions else 0.0
    avg_doi = sum(c.depth_of_inheritance for c in all_classes) / len(all_classes) if all_classes else 0.0
    comment_density = (total_comment_lines / total_lines * 100) if total_lines > 0 else 0.0
    
    # Calculate technical debt ratio (simplified)
    critical_issues = len([i for i in all_issues if i.severity == 'critical'])
    major_issues = len([i for i in all_issues if i.severity == 'major'])
    technical_debt_ratio = (critical_issues * 2 + major_issues) / total_files if total_files > 0 else 0.0
    
    analysis_time = time.time() - start_time
    files_per_second = total_files / analysis_time if analysis_time > 0 else 0.0
    
    return ComprehensiveAnalysisResult(
        total_files=total_files,
        total_functions=total_functions,
        total_classes=total_classes,
        total_lines=total_lines,
        total_logical_lines=total_logical_lines,
        total_source_lines=total_source_lines,
        total_comment_lines=total_comment_lines,
        average_maintainability_index=avg_maintainability,
        average_cyclomatic_complexity=avg_complexity,
        average_halstead_volume=avg_halstead,
        average_depth_of_inheritance=avg_doi,
        comment_density=comment_density,
        technical_debt_ratio=technical_debt_ratio,
        files=file_analyses,
        issues=all_issues,
        function_metrics=all_functions,
        class_metrics=all_classes,
        analysis_time=analysis_time,
        files_per_second=files_per_second
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_complexity_rank(complexity: int) -> str:
    """Get complexity rank based on cyclomatic complexity."""
    if complexity <= 5:
        return "A"
    elif complexity <= 10:
        return "B"
    elif complexity <= 15:
        return "C"
    elif complexity <= 20:
        return "D"
    else:
        return "F"


def calculate_technical_debt_hours(issues: List[CodeIssue]) -> float:
    """Estimate technical debt in hours based on issues."""
    debt_hours = 0.0
    
    for issue in issues:
        if issue.severity == "critical":
            debt_hours += 4.0  # 4 hours per critical issue
        elif issue.severity == "major":
            debt_hours += 2.0  # 2 hours per major issue
        elif issue.severity == "minor":
            debt_hours += 0.5  # 30 minutes per minor issue
        else:
            debt_hours += 0.1  # 6 minutes per info issue
    
    return debt_hours


def generate_summary_statistics(result: ComprehensiveAnalysisResult) -> Dict[str, Any]:
    """Generate summary statistics from analysis results."""
    return {
        "overview": {
            "total_files": result.total_files,
            "total_functions": result.total_functions,
            "total_classes": result.total_classes,
            "total_lines": result.total_lines,
            "analysis_time": f"{result.analysis_time:.2f}s",
            "files_per_second": f"{result.files_per_second:.1f}"
        },
        "quality_metrics": {
            "average_maintainability_index": f"{result.average_maintainability_index:.1f}",
            "average_cyclomatic_complexity": f"{result.average_cyclomatic_complexity:.1f}",
            "average_halstead_volume": f"{result.average_halstead_volume:.1f}",
            "comment_density": f"{result.comment_density:.1f}%",
            "technical_debt_ratio": f"{result.technical_debt_ratio:.2f}"
        },
        "issues_summary": {
            "total_issues": len(result.issues),
            "critical": len([i for i in result.issues if i.severity == "critical"]),
            "major": len([i for i in result.issues if i.severity == "major"]),
            "minor": len([i for i in result.issues if i.severity == "minor"]),
            "info": len([i for i in result.issues if i.severity == "info"]),
            "estimated_debt_hours": calculate_technical_debt_hours(result.issues)
        },
        "complexity_distribution": {
            "functions_by_rank": {
                rank: len([f for f in result.function_metrics if get_complexity_rank(f.cyclomatic_complexity) == rank])
                for rank in ["A", "B", "C", "D", "F"]
            }
        }
    }
