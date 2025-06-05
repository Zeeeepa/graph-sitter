"""
Comprehensive Code Analysis Module for Graph-sitter

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

import ast
import os
import re
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
import json

try:
    from tree_sitter import Language, Parser, Node
except ImportError:
    # Fallback for environments without tree-sitter
    Language = None
    Parser = None
    Node = None


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    type: str
    severity: str  # 'critical', 'major', 'minor', 'info'
    message: str
    file_path: str
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None


@dataclass
class DeadCodeItem:
    """Represents a dead code item."""
    type: str  # 'function', 'class', 'variable', 'import'
    name: str
    file_path: str
    line_start: int
    line_end: int
    reason: str
    confidence: float  # 0.0 to 1.0


@dataclass
class FunctionMetrics:
    """Metrics for a function."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    lines_of_code: int
    parameters_count: int
    return_statements: int
    nested_depth: int
    cognitive_complexity: int


@dataclass
class ClassMetrics:
    """Metrics for a class."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    methods_count: int
    attributes_count: int
    inheritance_depth: int
    coupling: int
    cohesion: float


@dataclass
class AnalysisResult:
    """Comprehensive analysis result."""
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_lines: int = 0
    
    # Dead code analysis
    dead_code_items: List[DeadCodeItem] = field(default_factory=list)
    
    # Issues found
    issues: List[CodeIssue] = field(default_factory=list)
    
    # Metrics
    function_metrics: List[FunctionMetrics] = field(default_factory=list)
    class_metrics: List[ClassMetrics] = field(default_factory=list)
    
    # File analysis
    file_analysis: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Dependencies
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    
    # Code quality metrics
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    test_coverage_estimate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'summary': {
                'total_files': self.total_files,
                'total_functions': self.total_functions,
                'total_classes': self.total_classes,
                'total_lines': self.total_lines,
                'maintainability_index': self.maintainability_index,
                'technical_debt_ratio': self.technical_debt_ratio,
                'test_coverage_estimate': self.test_coverage_estimate
            },
            'dead_code_items': [
                {
                    'type': item.type,
                    'name': item.name,
                    'location': f"{item.file_path}:{item.line_start}-{item.line_end}",
                    'reason': item.reason,
                    'confidence': item.confidence
                }
                for item in self.dead_code_items
            ],
            'issues': [
                {
                    'type': issue.type,
                    'severity': issue.severity,
                    'message': issue.message,
                    'location': f"{issue.file_path}:{issue.line_start}-{issue.line_end}",
                    'suggestion': issue.suggestion,
                    'rule_id': issue.rule_id
                }
                for issue in self.issues
            ],
            'function_metrics': [
                {
                    'name': metric.name,
                    'file_path': metric.file_path,
                    'location': f"{metric.line_start}-{metric.line_end}",
                    'cyclomatic_complexity': metric.cyclomatic_complexity,
                    'lines_of_code': metric.lines_of_code,
                    'parameters_count': metric.parameters_count,
                    'cognitive_complexity': metric.cognitive_complexity
                }
                for metric in self.function_metrics
            ],
            'class_metrics': [
                {
                    'name': metric.name,
                    'file_path': metric.file_path,
                    'location': f"{metric.line_start}-{metric.line_end}",
                    'methods_count': metric.methods_count,
                    'attributes_count': metric.attributes_count,
                    'inheritance_depth': metric.inheritance_depth,
                    'coupling': metric.coupling,
                    'cohesion': metric.cohesion
                }
                for metric in self.class_metrics
            ],
            'dependencies': self.dependencies,
            'circular_dependencies': self.circular_dependencies,
            'file_analysis': self.file_analysis
        }


class CodeAnalyzer:
    """Comprehensive code analyzer using AST and pattern matching."""
    
    def __init__(self, repo_path: Union[str, Path]):
        self.repo_path = Path(repo_path)
        self.result = AnalysisResult()
        self.file_contents: Dict[str, str] = {}
        self.function_calls: Dict[str, Set[str]] = defaultdict(set)
        self.function_definitions: Dict[str, Tuple[str, int, int]] = {}
        self.class_definitions: Dict[str, Tuple[str, int, int]] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze(self) -> AnalysisResult:
        """Perform comprehensive code analysis."""
        print("🔍 Starting comprehensive code analysis...")
        
        # Discover and analyze files
        python_files = self._discover_python_files()
        self.result.total_files = len(python_files)
        
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        # Analyze each file
        for file_path in python_files:
            self._analyze_file(file_path)
        
        # Perform cross-file analysis
        self._analyze_dependencies()
        self._detect_dead_code()
        self._calculate_quality_metrics()
        self._detect_code_issues()
        
        print("✅ Analysis complete!")
        return self.result
    
    def _discover_python_files(self) -> List[Path]:
        """Discover all Python files in the repository."""
        python_files = []
        
        # Common directories to skip
        skip_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.venv', 'venv', 'env', '.env', 'build', 'dist',
            '.mypy_cache', '.coverage', 'htmlcov'
        }
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        return python_files
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.file_contents[str(file_path)] = content
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.result.issues.append(CodeIssue(
                    type="syntax_error",
                    severity="critical",
                    message=f"Syntax error: {e.msg}",
                    file_path=str(file_path),
                    line_start=e.lineno or 1,
                    line_end=e.lineno or 1,
                    column_start=e.offset or 0,
                    rule_id="E999"
                ))
                return
            
            # Analyze AST
            visitor = ASTAnalysisVisitor(file_path, self)
            visitor.visit(tree)
            
            # Count lines
            lines = content.split('\n')
            self.result.total_lines += len(lines)
            
            # Store file analysis
            self.result.file_analysis[str(file_path)] = {
                'lines_of_code': len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
                'total_lines': len(lines),
                'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
                'blank_lines': len([line for line in lines if not line.strip()]),
                'functions': visitor.functions_found,
                'classes': visitor.classes_found,
                'imports': visitor.imports_found
            }
            
        except Exception as e:
            self.result.issues.append(CodeIssue(
                type="file_error",
                severity="major",
                message=f"Error analyzing file: {str(e)}",
                file_path=str(file_path),
                line_start=1,
                line_end=1,
                rule_id="F999"
            ))
    
    def _analyze_dependencies(self) -> None:
        """Analyze dependencies between modules."""
        # Build dependency graph
        for file_path, imports in self.import_graph.items():
            self.result.dependencies[file_path] = list(imports)
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if cycle not in self.result.circular_dependencies:
                    self.result.circular_dependencies.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.import_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in self.import_graph:
            if node not in visited:
                dfs(node, [])
    
    def _detect_dead_code(self) -> None:
        """Detect potentially dead code."""
        # Find unused functions
        defined_functions = set(self.function_definitions.keys())
        called_functions = set()
        
        for calls in self.function_calls.values():
            called_functions.update(calls)
        
        unused_functions = defined_functions - called_functions
        
        for func_name in unused_functions:
            file_path, line_start, line_end = self.function_definitions[func_name]
            
            # Skip if it's a main function, test function, or special method
            if (func_name in ['main', '__main__'] or 
                func_name.startswith('test_') or 
                func_name.startswith('__') and func_name.endswith('__')):
                continue
            
            self.result.dead_code_items.append(DeadCodeItem(
                type="function",
                name=func_name,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                reason="Function is defined but never called",
                confidence=0.8
            ))
    
    def _calculate_quality_metrics(self) -> None:
        """Calculate overall code quality metrics."""
        if not self.result.function_metrics:
            return
        
        # Calculate maintainability index
        avg_complexity = sum(m.cyclomatic_complexity for m in self.result.function_metrics) / len(self.result.function_metrics)
        avg_loc = sum(m.lines_of_code for m in self.result.function_metrics) / len(self.result.function_metrics)
        
        # Simplified maintainability index calculation
        self.result.maintainability_index = max(0, 171 - 5.2 * avg_complexity - 0.23 * avg_loc)
        
        # Technical debt ratio (based on issues)
        critical_issues = len([i for i in self.result.issues if i.severity == 'critical'])
        major_issues = len([i for i in self.result.issues if i.severity == 'major'])
        total_issues = len(self.result.issues)
        
        if self.result.total_lines > 0:
            self.result.technical_debt_ratio = (critical_issues * 2 + major_issues) / (self.result.total_lines / 1000)
        
        # Estimate test coverage (very basic heuristic)
        test_files = len([f for f in self.result.file_analysis.keys() if 'test' in f.lower()])
        if self.result.total_files > 0:
            self.result.test_coverage_estimate = min(100, (test_files / self.result.total_files) * 100)
    
    def _detect_code_issues(self) -> None:
        """Detect various code quality issues."""
        for file_path, content in self.file_contents.items():
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Long lines
                if len(line) > 120:
                    self.result.issues.append(CodeIssue(
                        type="line_too_long",
                        severity="minor",
                        message=f"Line too long ({len(line)} > 120 characters)",
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        suggestion="Consider breaking this line into multiple lines",
                        rule_id="E501"
                    ))
                
                # TODO comments
                if 'TODO' in line.upper() or 'FIXME' in line.upper():
                    self.result.issues.append(CodeIssue(
                        type="todo_comment",
                        severity="info",
                        message="TODO/FIXME comment found",
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        suggestion="Consider addressing this TODO item",
                        rule_id="T001"
                    ))
                
                # Print statements (potential debugging code)
                if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
                    self.result.issues.append(CodeIssue(
                        type="print_statement",
                        severity="minor",
                        message="Print statement found (potential debugging code)",
                        file_path=file_path,
                        line_start=i,
                        line_end=i,
                        suggestion="Consider using logging instead of print",
                        rule_id="T201"
                    ))


class ASTAnalysisVisitor(ast.NodeVisitor):
    """AST visitor for analyzing Python code structure."""
    
    def __init__(self, file_path: Path, analyzer: CodeAnalyzer):
        self.file_path = file_path
        self.analyzer = analyzer
        self.current_class = None
        self.functions_found = []
        self.classes_found = []
        self.imports_found = []
        self.nesting_level = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        func_name = node.name
        line_start = node.lineno
        line_end = node.end_lineno or line_start
        
        # Store function definition
        full_name = f"{self.current_class}.{func_name}" if self.current_class else func_name
        self.analyzer.function_definitions[full_name] = (str(self.file_path), line_start, line_end)
        self.functions_found.append(func_name)
        
        # Calculate metrics
        metrics = self._calculate_function_metrics(node)
        self.analyzer.result.function_metrics.append(metrics)
        self.analyzer.result.total_functions += 1
        
        # Visit function body
        old_nesting = self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level = old_nesting
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self.visit_FunctionDef(node)  # Treat same as regular function
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        class_name = node.name
        line_start = node.lineno
        line_end = node.end_lineno or line_start
        
        # Store class definition
        self.analyzer.class_definitions[class_name] = (str(self.file_path), line_start, line_end)
        self.classes_found.append(class_name)
        
        # Calculate metrics
        metrics = self._calculate_class_metrics(node)
        self.analyzer.result.class_metrics.append(metrics)
        self.analyzer.result.total_classes += 1
        
        # Visit class body
        old_class = self.current_class
        self.current_class = class_name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            current_func = self.current_class or "global"
            self.analyzer.function_calls[current_func].add(func_name)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
                current_func = self.current_class or "global"
                self.analyzer.function_calls[current_func].add(func_name)
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            self.imports_found.append(alias.name)
            self.analyzer.import_graph[str(self.file_path)].add(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from import statement."""
        if node.module:
            self.imports_found.append(node.module)
            self.analyzer.import_graph[str(self.file_path)].add(node.module)
    
    def _calculate_function_metrics(self, node: ast.FunctionDef) -> FunctionMetrics:
        """Calculate metrics for a function."""
        # Count lines of code (excluding comments and blank lines)
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        
        # Calculate cognitive complexity
        cognitive_complexity = self._calculate_cognitive_complexity(node)
        
        # Count parameters
        params_count = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
        if node.args.vararg:
            params_count += 1
        if node.args.kwarg:
            params_count += 1
        
        # Count return statements
        return_count = len([n for n in ast.walk(node) if isinstance(n, ast.Return)])
        
        return FunctionMetrics(
            name=node.name,
            file_path=str(self.file_path),
            line_start=start_line,
            line_end=end_line,
            cyclomatic_complexity=complexity,
            lines_of_code=end_line - start_line + 1,
            parameters_count=params_count,
            return_statements=return_count,
            nested_depth=self.nesting_level,
            cognitive_complexity=cognitive_complexity
        )
    
    def _calculate_class_metrics(self, node: ast.ClassDef) -> ClassMetrics:
        """Calculate metrics for a class."""
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        attributes = [n for n in ast.walk(node) if isinstance(n, ast.Assign)]
        
        # Calculate inheritance depth
        inheritance_depth = len(node.bases)
        
        return ClassMetrics(
            name=node.name,
            file_path=str(self.file_path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            methods_count=len(methods),
            attributes_count=len(attributes),
            inheritance_depth=inheritance_depth,
            coupling=0,  # Would need more complex analysis
            cohesion=0.0  # Would need more complex analysis
        )
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cognitive complexity (simplified version)."""
        complexity = 0
        nesting_level = 0
        
        def visit_node(n, level):
            nonlocal complexity
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + level
                for child in ast.iter_child_nodes(n):
                    visit_node(child, level + 1)
            elif isinstance(n, ast.ExceptHandler):
                complexity += 1 + level
                for child in ast.iter_child_nodes(n):
                    visit_node(child, level + 1)
            else:
                for child in ast.iter_child_nodes(n):
                    visit_node(child, level)
        
        for child in ast.iter_child_nodes(node):
            visit_node(child, 0)
        
        return complexity


def format_analysis_results(result: AnalysisResult) -> str:
    """Format analysis results for display."""
    output = []
    
    # Summary
    output.append("🔍 Analysis Results:")
    output.append(f"  • Total Files: {result.total_files}")
    output.append(f"  • Total Functions: {result.total_functions}")
    output.append(f"  • Total Classes: {result.total_classes}")
    output.append(f"  • Total Lines: {result.total_lines}")
    output.append(f"  • Maintainability Index: {result.maintainability_index:.1f}/100")
    output.append(f"  • Technical Debt Ratio: {result.technical_debt_ratio:.2f}")
    output.append(f"  • Test Coverage Estimate: {result.test_coverage_estimate:.1f}%")
    output.append("")
    
    # Dead Code
    if result.dead_code_items:
        output.append(f"💀 Dead Code Items: {len(result.dead_code_items)}")
        for item in result.dead_code_items[:10]:  # Show first 10
            location = f"{item.file_path}:{item.line_start}-{item.line_end}"
            output.append(f"  • {item.type.title()}: {item.name}")
            output.append(f"    Location: {location}")
            output.append(f"    Reason: {item.reason}")
            output.append(f"    Confidence: {item.confidence:.1%}")
            output.append("")
        
        if len(result.dead_code_items) > 10:
            output.append(f"  ... and {len(result.dead_code_items) - 10} more items")
            output.append("")
    
    # Issues
    if result.issues:
        output.append(f"⚠️  Issues: {len(result.issues)}")
        
        # Group by severity
        by_severity = defaultdict(list)
        for issue in result.issues:
            by_severity[issue.severity].append(issue)
        
        for severity in ['critical', 'major', 'minor', 'info']:
            if severity in by_severity:
                output.append(f"  {severity.title()}: {len(by_severity[severity])}")
                for issue in by_severity[severity][:5]:  # Show first 5 per severity
                    location = f"{issue.file_path}:{issue.line_start}"
                    output.append(f"    • {issue.message}")
                    output.append(f"      Location: {location}")
                    if issue.suggestion:
                        output.append(f"      Suggestion: {issue.suggestion}")
                    output.append("")
                
                if len(by_severity[severity]) > 5:
                    output.append(f"    ... and {len(by_severity[severity]) - 5} more {severity} issues")
                    output.append("")
    
    # Circular Dependencies
    if result.circular_dependencies:
        output.append(f"🔄 Circular Dependencies: {len(result.circular_dependencies)}")
        for cycle in result.circular_dependencies[:5]:
            output.append(f"  • {' → '.join(cycle)}")
        if len(result.circular_dependencies) > 5:
            output.append(f"  ... and {len(result.circular_dependencies) - 5} more cycles")
        output.append("")
    
    # Top Complex Functions
    if result.function_metrics:
        complex_functions = sorted(result.function_metrics, 
                                 key=lambda x: x.cyclomatic_complexity, 
                                 reverse=True)[:5]
        output.append("🧮 Most Complex Functions:")
        for func in complex_functions:
            output.append(f"  • {func.name} (complexity: {func.cyclomatic_complexity})")
            output.append(f"    Location: {func.file_path}:{func.line_start}-{func.line_end}")
        output.append("")
    
    return "\n".join(output)


# Integration with Codebase class
def add_analysis_method():
    """Add Analysis method to Codebase class."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        def Analysis(self) -> AnalysisResult:
            """
            Perform comprehensive code analysis on the codebase.
            
            Returns:
                AnalysisResult: Comprehensive analysis results including metrics,
                               dead code detection, and issue identification.
            
            Example:
                >>> codebase = Codebase("path/to/repo")
                >>> result = codebase.Analysis()
                >>> print(format_analysis_results(result))
            """
            analyzer = CodeAnalyzer(self.repo_path)
            return analyzer.analyze()
        
        # Add method to Codebase class
        Codebase.Analysis = Analysis
        
        return True
    except ImportError as e:
        # Fallback for when graph_sitter is not available
        print(f"Warning: Could not add Analysis method to Codebase class: {e}")
        return False


# Auto-register the Analysis method when module is imported (with error handling)
try:
    add_analysis_method()
except Exception as e:
    print(f"Warning: Could not auto-register Analysis method: {e}")

# Convenience functions for direct usage
def analyze_codebase(repo_path: Union[str, Path]) -> AnalysisResult:
    """
    Analyze a codebase and return comprehensive results.
    
    Args:
        repo_path: Path to the repository to analyze
        
    Returns:
        AnalysisResult: Comprehensive analysis results
    """
    analyzer = CodeAnalyzer(repo_path)
    return analyzer.analyze()


def analyze_and_print(repo_path: Union[str, Path]) -> AnalysisResult:
    """
    Analyze a codebase and print formatted results.
    
    Args:
        repo_path: Path to the repository to analyze
        
    Returns:
        AnalysisResult: Comprehensive analysis results
    """
    result = analyze_codebase(repo_path)
    print(format_analysis_results(result))
    return result


if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive code analysis")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--output", "-o", help="Output file for JSON results")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                       help="Output format")
    
    args = parser.parse_args()
    
    result = analyze_codebase(args.repo_path)
    
    if args.format == "json":
        output_data = result.to_dict()
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(output_data, indent=2))
    else:
        print(format_analysis_results(result))
        if args.output:
            with open(args.output, 'w') as f:
                f.write(format_analysis_results(result))
            print(f"Results saved to {args.output}")
