#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE CODEBASE ANALYSIS SYSTEM 🚀

A unified, powerful analysis system that consolidates all analysis capabilities:
- Core quality metrics (maintainability, complexity, Halstead, etc.)
- Advanced investigation features (function context, relationships)
- Graph-sitter integration (pre-computed graphs, dependencies)
- Tree-sitter query patterns and visualization
- Import loop detection and circular dependency analysis
- Training data generation for LLMs
- Dead code detection using usage analysis
- AI-powered insights and recommendations

Consolidated from:
- analyze_codebase_enhanced.py
- enhanced_analyzer.py  
- graph_sitter_enhancements.py

Based on successful methodologies from PRs #211-216.
"""

import ast
import argparse
import json
import logging
import math
import os
import sys
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import graph-sitter components
try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    GRAPH_SITTER_AVAILABLE = True
    
    # Try to import NetworkX for graph analysis
    try:
        import networkx as nx
        NETWORKX_AVAILABLE = True
    except ImportError:
        NETWORKX_AVAILABLE = False
        logger.warning("NetworkX not available - graph analysis will be limited")
        
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False
    NETWORKX_AVAILABLE = False
    # Create dummy classes for type hints
    class Codebase: pass
    class CodebaseConfig: pass
    class ExternalModule: pass
    class Import: pass
    class Symbol: pass


# ============================================================================
# DATA CLASSES AND MODELS
# ============================================================================

@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    type: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    file_path: str
    line_number: int
    column: int = 0
    suggestion: str = ""

@dataclass
class DeadCodeItem:
    """Represents unused/dead code."""
    type: str  # 'function', 'class', 'variable', 'import'
    name: str
    file_path: str
    line_number: int
    reason: str

@dataclass
class ImportLoop:
    """Represents a circular import dependency."""
    files: List[str]
    loop_type: str  # 'static', 'dynamic', 'mixed'
    severity: str   # 'critical', 'warning', 'info'
    imports: List[Dict[str, Any]]

@dataclass
class TrainingDataItem:
    """Training data for ML models."""
    function_name: str
    file_path: str
    source_code: str
    dependencies: List[str]
    usages: List[str]
    complexity_metrics: Dict[str, Any]
    context: Dict[str, Any]

@dataclass
class FunctionMetrics:
    """Comprehensive function analysis metrics."""
    name: str
    file_path: str
    line_number: int
    cyclomatic_complexity: int
    halstead_volume: float
    halstead_difficulty: float
    halstead_effort: float
    lines_of_code: int
    maintainability_index: int
    parameters_count: int
    return_statements: int
    docstring_coverage: bool
    issues: List[CodeIssue] = field(default_factory=list)

@dataclass
class ClassMetrics:
    """Comprehensive class analysis metrics."""
    name: str
    file_path: str
    line_number: int
    methods_count: int
    attributes_count: int
    inheritance_depth: int
    coupling_factor: float
    cohesion_factor: float
    lines_of_code: int
    docstring_coverage: bool
    issues: List[CodeIssue] = field(default_factory=list)

@dataclass
class FileAnalysis:
    """File-level analysis results."""
    file_path: str
    lines_of_code: int
    functions: List[FunctionMetrics]
    classes: List[ClassMetrics]
    imports_count: int
    issues: List[CodeIssue]
    dead_code: List[DeadCodeItem]

@dataclass
class GraphAnalysisResult:
    """Graph-based analysis results."""
    total_nodes: int
    total_edges: int
    strongly_connected_components: int
    average_clustering: float
    density: float
    import_loops: List[ImportLoop]

@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis results."""
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    files: List[FileAnalysis]
    issues: List[CodeIssue]
    dead_code: List[DeadCodeItem]
    import_loops: List[ImportLoop]
    training_data: List[TrainingDataItem]
    graph_analysis: Optional[GraphAnalysisResult]
    quality_metrics: Dict[str, Any]
    analysis_time: float
    
    def print_summary(self):
        """Print a comprehensive summary of analysis results."""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE CODEBASE ANALYSIS RESULTS")
        print("="*80)
        
        # Basic metrics
        print(f"\n📊 BASIC METRICS")
        print(f"   📁 Total Files: {self.total_files}")
        print(f"   📝 Total Lines: {self.total_lines:,}")
        print(f"   ⚡ Total Functions: {self.total_functions}")
        print(f"   🏗️  Total Classes: {self.total_classes}")
        
        # Quality metrics
        if self.quality_metrics:
            print(f"\n🎯 QUALITY METRICS")
            for key, value in self.quality_metrics.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
        
        # Issues summary
        if self.issues:
            print(f"\n⚠️  CODE ISSUES ({len(self.issues)} total)")
            issue_counts = Counter(issue.severity for issue in self.issues)
            for severity, count in issue_counts.items():
                print(f"   {severity.upper()}: {count}")
        
        # Dead code summary
        if self.dead_code:
            print(f"\n💀 DEAD CODE ({len(self.dead_code)} items)")
            dead_counts = Counter(item.type for item in self.dead_code)
            for item_type, count in dead_counts.items():
                print(f"   {item_type}: {count}")
        
        # Import loops
        if self.import_loops:
            print(f"\n🔄 IMPORT LOOPS ({len(self.import_loops)} detected)")
            for loop in self.import_loops:
                print(f"   {loop.severity.upper()}: {' -> '.join(loop.files)}")
        
        # Graph analysis
        if self.graph_analysis:
            print(f"\n🕸️  GRAPH ANALYSIS")
            print(f"   Nodes: {self.graph_analysis.total_nodes}")
            print(f"   Edges: {self.graph_analysis.total_edges}")
            print(f"   Density: {self.graph_analysis.density:.3f}")
        
        print(f"\n⏱️  Analysis completed in {self.analysis_time:.2f} seconds")
        print("="*80)

    def save_to_file(self, filepath: str, format_type: str = "json"):
        """Save analysis results to file."""
        if format_type == "json":
            with open(filepath, 'w') as f:
                json.dump(asdict(self), f, indent=2, default=str)
        elif format_type == "html":
            self._save_html_report(filepath)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _save_html_report(self, filepath: str):
        """Generate and save HTML report."""
        html_content = self._generate_html_report()
        with open(filepath, 'w') as f:
            f.write(html_content)

    def _generate_html_report(self) -> str:
        """Generate HTML report with visualizations."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Codebase Analysis Report</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ margin: 10px 0; }}
        .issue {{ background: #ffe6e6; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .warning {{ background: #fff3cd; }}
        .info {{ background: #d1ecf1; }}
        .chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>🚀 Comprehensive Codebase Analysis Report</h1>
    
    <h2>📊 Summary</h2>
    <div class="metric">Total Files: {self.total_files}</div>
    <div class="metric">Total Lines: {self.total_lines:,}</div>
    <div class="metric">Total Functions: {self.total_functions}</div>
    <div class="metric">Total Classes: {self.total_classes}</div>
    
    <h2>⚠️ Issues ({len(self.issues)})</h2>
    {''.join(f'<div class="issue {issue.severity}">{issue.type}: {issue.message} ({issue.file_path}:{issue.line_number})</div>' for issue in self.issues[:20])}
    
    <h2>💀 Dead Code ({len(self.dead_code)})</h2>
    {''.join(f'<div class="issue">{item.type}: {item.name} in {item.file_path}:{item.line_number}</div>' for item in self.dead_code[:20])}
    
    <p><em>Report generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</em></p>
</body>
</html>
        """


# ============================================================================
# CORE ANALYSIS FUNCTIONS
# ============================================================================

def calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of an AST node."""
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.And, ast.Or)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    
    return complexity

def calculate_halstead_metrics(node: ast.AST) -> Tuple[float, float, float]:
    """Calculate Halstead complexity metrics."""
    operators = set()
    operands = set()
    operator_count = 0
    operand_count = 0
    
    for child in ast.walk(node):
        if isinstance(child, ast.BinOp):
            operators.add(type(child.op).__name__)
            operator_count += 1
        elif isinstance(child, ast.UnaryOp):
            operators.add(type(child.op).__name__)
            operator_count += 1
        elif isinstance(child, ast.Compare):
            for op in child.ops:
                operators.add(type(op).__name__)
                operator_count += 1
        elif isinstance(child, ast.Name):
            operands.add(child.id)
            operand_count += 1
        elif isinstance(child, ast.Constant):
            operands.add(str(child.value))
            operand_count += 1
    
    n1 = len(operators)  # Number of distinct operators
    n2 = len(operands)   # Number of distinct operands
    N1 = operator_count  # Total number of operators
    N2 = operand_count   # Total number of operands
    
    if n1 == 0 or n2 == 0:
        return 0.0, 0.0, 0.0
    
    # Halstead metrics
    vocabulary = n1 + n2
    length = N1 + N2
    volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    effort = difficulty * volume
    
    return volume, difficulty, effort

def calculate_maintainability_index(halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
    """Calculate maintainability index."""
    if loc == 0 or halstead_volume <= 0:
        return 100
    
    try:
        # Microsoft's maintainability index formula
        mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * cyclomatic_complexity - 16.2 * math.log(loc)
        mi = max(0, mi * 100 / 171)  # Normalize to 0-100 scale
        return int(mi)
    except (ValueError, ZeroDivisionError):
        return 50  # Default maintainability score

def count_lines(source: str) -> int:
    """Count non-empty, non-comment lines."""
    lines = source.split('\n')
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            count += 1
    return count

def analyze_function_ast(func_node: ast.FunctionDef, file_path: str, source_lines: List[str]) -> FunctionMetrics:
    """Analyze a function using AST."""
    start_line = func_node.lineno
    end_line = func_node.end_lineno or start_line
    
    # Get function source
    func_source = '\n'.join(source_lines[start_line-1:end_line])
    
    # Calculate metrics
    complexity = calculate_cyclomatic_complexity(func_node)
    volume, difficulty, effort = calculate_halstead_metrics(func_node)
    loc = count_lines(func_source)
    mi = calculate_maintainability_index(volume, complexity, loc)
    
    # Count parameters and return statements
    params_count = len(func_node.args.args)
    return_count = len([n for n in ast.walk(func_node) if isinstance(n, ast.Return)])
    
    # Check for docstring
    has_docstring = (isinstance(func_node.body[0], ast.Expr) and 
                    isinstance(func_node.body[0].value, ast.Constant) and 
                    isinstance(func_node.body[0].value.value, str)) if func_node.body else False
    
    return FunctionMetrics(
        name=func_node.name,
        file_path=file_path,
        line_number=start_line,
        cyclomatic_complexity=complexity,
        halstead_volume=volume,
        halstead_difficulty=difficulty,
        halstead_effort=effort,
        lines_of_code=loc,
        maintainability_index=mi,
        parameters_count=params_count,
        return_statements=return_count,
        docstring_coverage=has_docstring
    )

def analyze_class_ast(class_node: ast.ClassDef, file_path: str, source_lines: List[str]) -> ClassMetrics:
    """Analyze a class using AST."""
    start_line = class_node.lineno
    end_line = class_node.end_lineno or start_line
    
    # Get class source
    class_source = '\n'.join(source_lines[start_line-1:end_line])
    loc = count_lines(class_source)
    
    # Count methods and attributes
    methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
    attributes = [n for n in ast.walk(class_node) if isinstance(n, ast.Assign)]
    
    # Calculate inheritance depth
    inheritance_depth = len(class_node.bases)
    
    # Check for docstring
    has_docstring = (isinstance(class_node.body[0], ast.Expr) and 
                    isinstance(class_node.body[0].value, ast.Constant) and 
                    isinstance(class_node.body[0].value.value, str)) if class_node.body else False
    
    return ClassMetrics(
        name=class_node.name,
        file_path=file_path,
        line_number=start_line,
        methods_count=len(methods),
        attributes_count=len(attributes),
        inheritance_depth=inheritance_depth,
        coupling_factor=0.0,  # Would need more analysis
        cohesion_factor=0.0,  # Would need more analysis
        lines_of_code=loc,
        docstring_coverage=has_docstring
    )

def detect_code_issues(tree: ast.AST, file_path: str, source_lines: List[str]) -> List[CodeIssue]:
    """Detect various code quality issues."""
    issues = []
    
    for node in ast.walk(tree):
        # Long functions
        if isinstance(node, ast.FunctionDef):
            if node.end_lineno and node.lineno:
                func_length = node.end_lineno - node.lineno
                if func_length > 50:
                    issues.append(CodeIssue(
                        type="long_function",
                        severity="warning",
                        message=f"Function '{node.name}' is {func_length} lines long",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider breaking this function into smaller functions"
                    ))
        
        # Too many parameters
        if isinstance(node, ast.FunctionDef):
            param_count = len(node.args.args)
            if param_count > 7:
                issues.append(CodeIssue(
                    type="too_many_parameters",
                    severity="warning",
                    message=f"Function '{node.name}' has {param_count} parameters",
                    file_path=file_path,
                    line_number=node.lineno,
                    suggestion="Consider using a configuration object or reducing parameters"
                ))
        
        # Nested loops (potential performance issue)
        if isinstance(node, (ast.For, ast.While)):
            nested_loops = [n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)) and n != node]
            if len(nested_loops) >= 2:
                issues.append(CodeIssue(
                    type="nested_loops",
                    severity="info",
                    message="Deeply nested loops detected",
                    file_path=file_path,
                    line_number=node.lineno,
                    suggestion="Consider optimizing nested loops for better performance"
                ))
        
        # Empty except blocks
        if isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append(CodeIssue(
                    type="empty_except",
                    severity="warning",
                    message="Empty except block",
                    file_path=file_path,
                    line_number=node.lineno,
                    suggestion="Add proper exception handling or logging"
                ))
    
    return issues

def detect_dead_code_ast(tree: ast.AST, file_path: str, all_functions: Set[str], all_classes: Set[str]) -> List[DeadCodeItem]:
    """Detect potentially dead code using AST analysis."""
    dead_code = []
    defined_functions = set()
    defined_classes = set()
    used_names = set()
    
    # Collect defined functions and classes
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_functions.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_classes.add(node.name)
        elif isinstance(node, ast.Name):
            used_names.add(node.id)
    
    # Check for unused functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if (node.name not in used_names and 
                not node.name.startswith('_') and 
                node.name not in ['main', '__init__']):
                dead_code.append(DeadCodeItem(
                    type="function",
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    reason="Function appears to be unused"
                ))
    
    return dead_code


# ============================================================================
# GRAPH-SITTER ENHANCED FUNCTIONS
# ============================================================================

def hop_through_imports(imp) -> Union[Symbol, ExternalModule, None]:
    """Hop through imports to find the root symbol source."""
    if not GRAPH_SITTER_AVAILABLE:
        return None
        
    current = imp
    visited = set()
    
    while current and hasattr(current, 'resolved_symbol'):
        if id(current) in visited:
            break
        visited.add(id(current))
        
        resolved = current.resolved_symbol
        if isinstance(resolved, ExternalModule):
            return resolved
        elif hasattr(resolved, 'symbol') and resolved.symbol:
            return resolved.symbol
        elif isinstance(resolved, Import):
            current = resolved
        else:
            return resolved
    
    return current

def detect_import_loops_graph_sitter(codebase) -> List[ImportLoop]:
    """Detect circular import dependencies using graph-sitter."""
    if not GRAPH_SITTER_AVAILABLE or not NETWORKX_AVAILABLE:
        return []
    
    try:
        # Build import dependency graph
        G = nx.DiGraph()
        file_imports = defaultdict(list)
        
        for file in codebase.files:
            for imp in file.imports:
                resolved = hop_through_imports(imp)
                if resolved and hasattr(resolved, 'file') and resolved.file:
                    target_file = resolved.file.filepath
                    if target_file != file.filepath:
                        G.add_edge(file.filepath, target_file)
                        file_imports[file.filepath].append({
                            'module': imp.module,
                            'target': target_file,
                            'line': getattr(imp, 'line_number', 0)
                        })
        
        # Find strongly connected components (cycles)
        cycles = list(nx.simple_cycles(G))
        import_loops = []
        
        for cycle in cycles:
            if len(cycle) > 1:
                # Determine severity based on cycle length
                severity = "critical" if len(cycle) <= 3 else "warning"
                
                # Collect import information for this cycle
                cycle_imports = []
                for i, file_path in enumerate(cycle):
                    next_file = cycle[(i + 1) % len(cycle)]
                    for imp_info in file_imports[file_path]:
                        if imp_info['target'] == next_file:
                            cycle_imports.append(imp_info)
                
                import_loops.append(ImportLoop(
                    files=cycle,
                    loop_type="static",
                    severity=severity,
                    imports=cycle_imports
                ))
        
        return import_loops
    
    except Exception as e:
        logger.warning(f"Error detecting import loops: {e}")
        return []

def detect_dead_code_graph_sitter(codebase) -> List[DeadCodeItem]:
    """Detect dead code using graph-sitter usage analysis."""
    if not GRAPH_SITTER_AVAILABLE:
        return []
    
    dead_code = []
    
    try:
        # Check functions
        for function in codebase.functions:
            if (len(function.usages) == 0 and 
                not function.name.startswith('_') and 
                function.name not in ['main', '__init__', 'test_']):
                dead_code.append(DeadCodeItem(
                    type="function",
                    name=function.name,
                    file_path=function.filepath,
                    line_number=getattr(function, 'line_number', 0),
                    reason="Function has no usages"
                ))
        
        # Check classes
        for cls in codebase.classes:
            if (len(cls.usages) == 0 and 
                not cls.name.startswith('_') and 
                not cls.name.startswith('Test')):
                dead_code.append(DeadCodeItem(
                    type="class",
                    name=cls.name,
                    file_path=cls.filepath,
                    line_number=getattr(cls, 'line_number', 0),
                    reason="Class has no usages"
                ))
        
        return dead_code
    
    except Exception as e:
        logger.warning(f"Error detecting dead code with graph-sitter: {e}")
        return []

def generate_training_data_graph_sitter(codebase) -> List[TrainingDataItem]:
    """Generate training data for ML models using graph-sitter."""
    if not GRAPH_SITTER_AVAILABLE:
        return []
    
    training_data = []
    
    try:
        for function in codebase.functions:
            # Get dependencies
            dependencies = []
            for dep in function.dependencies:
                if hasattr(dep, 'name'):
                    dependencies.append(dep.name)
            
            # Get usages
            usages = []
            for usage in function.usages:
                if hasattr(usage, 'file') and hasattr(usage.file, 'filepath'):
                    usages.append(usage.file.filepath)
            
            # Calculate complexity metrics
            complexity_metrics = {
                'cyclomatic_complexity': getattr(function, 'cyclomatic_complexity', 0),
                'parameters_count': len(getattr(function, 'parameters', [])),
                'lines_of_code': len(function.source.split('\n')) if hasattr(function, 'source') else 0
            }
            
            # Build context
            context = {
                'file_path': function.filepath,
                'class_name': function.parent.name if hasattr(function, 'parent') and function.parent else None,
                'is_async': getattr(function, 'is_async', False),
                'is_private': function.name.startswith('_'),
                'has_docstring': bool(getattr(function, 'docstring', None))
            }
            
            training_data.append(TrainingDataItem(
                function_name=function.name,
                file_path=function.filepath,
                source_code=getattr(function, 'source', ''),
                dependencies=dependencies,
                usages=usages,
                complexity_metrics=complexity_metrics,
                context=context
            ))
        
        return training_data
    
    except Exception as e:
        logger.warning(f"Error generating training data: {e}")
        return []

def analyze_graph_structure(codebase) -> Optional[GraphAnalysisResult]:
    """Analyze the overall graph structure of the codebase."""
    if not GRAPH_SITTER_AVAILABLE or not NETWORKX_AVAILABLE:
        return None
    
    try:
        # Build dependency graph
        G = nx.DiGraph()
        
        # Add nodes for all symbols
        for symbol in codebase.symbols:
            G.add_node(symbol.name)
        
        # Add edges for dependencies
        for symbol in codebase.symbols:
            for dep in symbol.dependencies:
                if hasattr(dep, 'name'):
                    G.add_edge(symbol.name, dep.name)
        
        # Calculate graph metrics
        total_nodes = G.number_of_nodes()
        total_edges = G.number_of_edges()
        
        # Convert to undirected for clustering coefficient
        G_undirected = G.to_undirected()
        avg_clustering = nx.average_clustering(G_undirected) if total_nodes > 0 else 0
        
        # Calculate density
        density = nx.density(G) if total_nodes > 1 else 0
        
        # Find strongly connected components
        scc_count = len(list(nx.strongly_connected_components(G)))
        
        # Detect import loops
        import_loops = detect_import_loops_graph_sitter(codebase)
        
        return GraphAnalysisResult(
            total_nodes=total_nodes,
            total_edges=total_edges,
            strongly_connected_components=scc_count,
            average_clustering=avg_clustering,
            density=density,
            import_loops=import_loops
        )
    
    except Exception as e:
        logger.warning(f"Error analyzing graph structure: {e}")
        return None

# ============================================================================
# ENHANCED ANALYSIS CAPABILITIES - Based on Successful PR Patterns
# ============================================================================

class AdvancedMetricsCalculator:
    """Advanced metrics calculation based on successful PR patterns."""
    
    @staticmethod
    def calculate_cyclomatic_complexity_enhanced(node: ast.AST) -> Tuple[int, str]:
        """Enhanced cyclomatic complexity with ranking (from PR #205/#207)."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        # Rank complexity (A-F scale from successful PRs)
        rank = AdvancedMetricsCalculator.cc_rank(complexity)
        return complexity, rank
    
    @staticmethod
    def cc_rank(complexity: int) -> str:
        """Rank cyclomatic complexity (from successful PRs)."""
        if complexity < 0:
            return "F"
        
        ranks = [
            (1, 5, "A"),
            (6, 10, "B"),
            (11, 20, "C"),
            (21, 30, "D"),
            (31, 40, "E"),
            (41, float("inf"), "F"),
        ]
        for low, high, rank in ranks:
            if low <= complexity <= high:
                return rank
        return "F"
    
    @staticmethod
    def calculate_halstead_metrics_enhanced(node: ast.AST) -> Dict[str, Any]:
        """Enhanced Halstead metrics calculation (from successful PRs)."""
        operators = []
        operands = []
        
        for child in ast.walk(node):
            # Operators
            if isinstance(child, ast.BinOp):
                operators.append(type(child.op).__name__)
            elif isinstance(child, ast.UnaryOp):
                operators.append(type(child.op).__name__)
            elif isinstance(child, ast.Compare):
                operators.extend([type(op).__name__ for op in child.ops])
            elif isinstance(child, ast.BoolOp):
                operators.append(type(child.op).__name__)
            elif isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                operators.append(type(child).__name__)
            elif isinstance(child, ast.FunctionDef):
                operators.append('FunctionDef')
            elif isinstance(child, ast.Return):
                operators.append('Return')
            elif isinstance(child, ast.Assign):
                operators.append('Assign')
            
            # Operands
            elif isinstance(child, ast.Name):
                operands.append(child.id)
            elif isinstance(child, ast.Constant):
                operands.append(str(child.value))
            elif isinstance(child, ast.Attribute):
                operands.append(child.attr)
        
        # Calculate Halstead metrics
        n1 = len(set(operators))  # Number of distinct operators
        n2 = len(set(operands))   # Number of distinct operands
        N1 = len(operators)       # Total number of operators
        N2 = len(operands)        # Total number of operands
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if vocabulary > 0:
            volume = length * math.log2(vocabulary)
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
        else:
            volume = difficulty = effort = 0
        
        return {
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort,
            'n1': n1,
            'n2': n2,
            'N1': N1,
            'N2': N2,
            'vocabulary': vocabulary,
            'length': length
        }

class TrainingDataGenerator:
    """Generate training data for ML models (from successful PRs)."""
    
    def __init__(self, codebase=None):
        self.codebase = codebase
        self.training_items = []
    
    def generate_function_training_data(self, functions: List[FunctionMetrics], 
                                      all_functions: Set[str], 
                                      file_contents: Dict[str, str]) -> List[TrainingDataItem]:
        """Generate training data for functions."""
        training_data = []
        
        for func in functions:
            try:
                # Get function source
                if func.file_path in file_contents:
                    lines = file_contents[func.file_path].split('\n')
                    func_source = '\n'.join(lines[func.line_number-1:func.line_number+func.lines_of_code])
                else:
                    func_source = ""
                
                # Analyze dependencies (simplified)
                dependencies = []
                for other_func in all_functions:
                    if other_func != func.name and other_func in func_source:
                        dependencies.append(other_func)
                
                # Analyze usages (simplified)
                usages = []
                for file_path, content in file_contents.items():
                    if func.name in content and file_path != func.file_path:
                        usages.append(file_path)
                
                # Create training data item
                training_data.append(TrainingDataItem(
                    function_name=func.name,
                    file_path=func.file_path,
                    source_code=func_source,
                    dependencies=dependencies,
                    usages=usages,
                    complexity_metrics={
                        'cyclomatic_complexity': func.cyclomatic_complexity,
                        'halstead_volume': func.halstead_volume,
                        'lines_of_code': func.lines_of_code,
                        'parameters_count': func.parameters_count,
                        'maintainability_index': func.maintainability_index
                    },
                    context={
                        'file_path': func.file_path,
                        'line_number': func.line_number,
                        'is_private': func.name.startswith('_'),
                        'has_docstring': func.docstring_coverage,
                        'return_statements': func.return_statements
                    }
                ))
            except Exception as e:
                logger.warning(f"Error generating training data for {func.name}: {e}")
        
        return training_data

class ImportLoopDetector:
    """Detect circular import dependencies (from successful PRs)."""
    
    def __init__(self):
        self.import_graph = defaultdict(set)
        self.file_imports = defaultdict(list)
    
    def analyze_imports_ast(self, tree: ast.AST, file_path: str) -> None:
        """Analyze imports using AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.import_graph[file_path].add(alias.name)
                    self.file_imports[file_path].append({
                        'module': alias.name,
                        'line': node.lineno,
                        'type': 'import'
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.import_graph[file_path].add(node.module)
                    self.file_imports[file_path].append({
                        'module': node.module,
                        'line': node.lineno,
                        'type': 'from_import'
                    })
    
    def detect_loops(self) -> List[ImportLoop]:
        """Detect circular import loops."""
        if not NETWORKX_AVAILABLE:
            return []
        
        try:
            # Build NetworkX graph
            G = nx.DiGraph()
            
            for file_path, imports in self.import_graph.items():
                for imported_module in imports:
                    # Try to resolve to actual file paths
                    target_file = self._resolve_import_to_file(imported_module, file_path)
                    if target_file and target_file != file_path:
                        G.add_edge(file_path, target_file)
            
            # Find strongly connected components (cycles)
            cycles = list(nx.simple_cycles(G))
            import_loops = []
            
            for cycle in cycles:
                if len(cycle) > 1:
                    # Determine severity based on cycle length
                    severity = "critical" if len(cycle) <= 3 else "warning"
                    
                    # Collect import information for this cycle
                    cycle_imports = []
                    for i, file_path in enumerate(cycle):
                        next_file = cycle[(i + 1) % len(cycle)]
                        for imp_info in self.file_imports[file_path]:
                            # Check if this import could lead to the next file in cycle
                            if self._could_import_lead_to_file(imp_info['module'], next_file):
                                cycle_imports.append(imp_info)
                    
                    import_loops.append(ImportLoop(
                        files=cycle,
                        loop_type="static",
                        severity=severity,
                        imports=cycle_imports
                    ))
            
            return import_loops
        
        except Exception as e:
            logger.warning(f"Error detecting import loops: {e}")
            return []
    
    def _resolve_import_to_file(self, module_name: str, current_file: str) -> Optional[str]:
        """Resolve import to actual file path (simplified)."""
        # This is a simplified resolution - in practice would need more sophisticated logic
        current_dir = os.path.dirname(current_file)
        
        # Try relative import
        potential_file = os.path.join(current_dir, module_name.replace('.', '/') + '.py')
        if os.path.exists(potential_file):
            return potential_file
        
        # Try as package
        potential_init = os.path.join(current_dir, module_name.replace('.', '/'), '__init__.py')
        if os.path.exists(potential_init):
            return potential_init
        
        return None
    
    def _could_import_lead_to_file(self, module_name: str, target_file: str) -> bool:
        """Check if import could lead to target file (simplified)."""
        return module_name in target_file or target_file.endswith(module_name.replace('.', '/') + '.py')

class DeadCodeDetector:
    """Detect dead/unused code (from successful PRs)."""
    
    def __init__(self):
        self.function_definitions = {}
        self.function_calls = set()
        self.class_definitions = {}
        self.class_usages = set()
    
    def analyze_definitions_and_usages(self, tree: ast.AST, file_path: str) -> None:
        """Analyze function/class definitions and usages."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.function_definitions[node.name] = {
                    'file_path': file_path,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'is_private': node.name.startswith('_'),
                    'is_test': node.name.startswith('test_'),
                    'is_main': node.name in ['main', '__main__']
                }
            elif isinstance(node, ast.ClassDef):
                self.class_definitions[node.name] = {
                    'file_path': file_path,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'is_private': node.name.startswith('_')
                }
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.function_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    self.function_calls.add(node.func.attr)
            elif isinstance(node, ast.Name):
                # Could be class usage
                self.class_usages.add(node.id)
    
    def detect_dead_functions(self) -> List[DeadCodeItem]:
        """Detect unused functions."""
        dead_items = []
        
        for func_name, func_info in self.function_definitions.items():
            # Skip special functions
            if (func_info['is_main'] or func_info['is_test'] or 
                func_name.startswith('__') and func_name.endswith('__')):
                continue
            
            # Check if function is called
            if func_name not in self.function_calls:
                confidence = 0.9 if not func_info['is_private'] else 0.7
                
                dead_items.append(DeadCodeItem(
                    type="function",
                    name=func_name,
                    file_path=func_info['file_path'],
                    line_number=func_info['line_start'],
                    reason="Function is defined but never called"
                ))
        
        return dead_items
    
    def detect_dead_classes(self) -> List[DeadCodeItem]:
        """Detect unused classes."""
        dead_items = []
        
        for class_name, class_info in self.class_definitions.items():
            # Skip private classes for now (might be used dynamically)
            if class_info['is_private']:
                continue
            
            # Check if class is used
            if class_name not in self.class_usages:
                dead_items.append(DeadCodeItem(
                    type="class",
                    name=class_name,
                    file_path=class_info['file_path'],
                    line_number=class_info['line_start'],
                    reason="Class is defined but never used"
                ))
        
        return dead_items

# ============================================================================
# MAIN ANALYZER CLASS
# ============================================================================

class ComprehensiveAnalysisSystem:
    """Main analyzer class that orchestrates all analysis components."""
    
    def __init__(self, use_graph_sitter: bool = True, advanced_config: bool = False):
        """Initialize the comprehensive analysis system.
        
        Args:
            use_graph_sitter: Whether to use graph-sitter features
            advanced_config: Whether to use advanced CodebaseConfig options
        """
        self.use_graph_sitter = use_graph_sitter and GRAPH_SITTER_AVAILABLE
        self.advanced_config = advanced_config
        self.config = self._create_config() if advanced_config and GRAPH_SITTER_AVAILABLE else None
        
        logger.info(f"Initialized ComprehensiveAnalysisSystem (graph-sitter: {self.use_graph_sitter})")
    
    def _create_config(self) -> Optional[CodebaseConfig]:
        """Create advanced CodebaseConfig with enhanced features."""
        if not GRAPH_SITTER_AVAILABLE:
            return None
        
        try:
            return CodebaseConfig(
                exp_lazy_graph=True,
                exp_enable_caching=True,
                exp_parallel_processing=True
            )
        except Exception as e:
            logger.warning(f"Could not create advanced config: {e}")
            return None
    
    def analyze_codebase(self, path: str, extensions: List[str] = None) -> ComprehensiveAnalysisResult:
        """Analyze entire codebase with comprehensive metrics."""
        start_time = time.time()
        
        if extensions is None:
            extensions = ['.py']
        
        logger.info(f"Starting comprehensive analysis of: {path}")
        
        # Use graph-sitter if available
        if self.use_graph_sitter:
            try:
                return self._analyze_with_graph_sitter(path)
            except Exception as e:
                logger.warning(f"Graph-sitter analysis failed: {e}")
                logger.info("Falling back to AST analysis")
        
        # Fallback to AST analysis
        return self._analyze_with_ast(path, extensions, start_time)
    
    def _analyze_with_graph_sitter(self, path: str) -> ComprehensiveAnalysisResult:
        """Analyze using graph-sitter capabilities."""
        start_time = time.time()
        
        # Initialize codebase
        if self.config:
            codebase = Codebase(path, config=self.config)
        else:
            codebase = Codebase(path)
        
        # Collect basic metrics
        total_files = len(codebase.files)
        total_functions = len(codebase.functions)
        total_classes = len(codebase.classes)
        total_lines = sum(len(f.source.split('\n')) for f in codebase.files if hasattr(f, 'source'))
        
        # Analyze files
        files_analysis = []
        all_issues = []
        all_dead_code = []
        
        for file in codebase.files:
            if file.filepath.endswith('.py'):
                file_analysis = self._analyze_file_graph_sitter(file, codebase)
                files_analysis.append(file_analysis)
                all_issues.extend(file_analysis.issues)
                all_dead_code.extend(file_analysis.dead_code)
        
        # Enhanced analysis
        import_loops = detect_import_loops_graph_sitter(codebase)
        training_data = generate_training_data_graph_sitter(codebase)
        graph_analysis = analyze_graph_structure(codebase)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(files_analysis)
        
        analysis_time = time.time() - start_time
        
        return ComprehensiveAnalysisResult(
            total_files=total_files,
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            files=files_analysis,
            issues=all_issues,
            dead_code=all_dead_code,
            import_loops=import_loops,
            training_data=training_data,
            graph_analysis=graph_analysis,
            quality_metrics=quality_metrics,
            analysis_time=analysis_time
        )
    
    def _analyze_file_graph_sitter(self, file, codebase) -> FileAnalysis:
        """Analyze a single file using graph-sitter."""
        functions_metrics = []
        classes_metrics = []
        issues = []
        dead_code = []
        
        # Analyze functions in this file
        file_functions = [f for f in codebase.functions if f.filepath == file.filepath]
        for function in file_functions:
            try:
                # Use graph-sitter enhanced analysis if available
                metrics = self._analyze_function_graph_sitter(function)
                functions_metrics.append(metrics)
            except Exception as e:
                logger.warning(f"Error analyzing function {function.name}: {e}")
        
        # Analyze classes in this file
        file_classes = [c for c in codebase.classes if c.filepath == file.filepath]
        for cls in file_classes:
            try:
                metrics = self._analyze_class_graph_sitter(cls)
                classes_metrics.append(metrics)
            except Exception as e:
                logger.warning(f"Error analyzing class {cls.name}: {e}")
        
        # Detect dead code for this file
        file_dead_code = [dc for dc in detect_dead_code_graph_sitter(codebase) 
                         if dc.file_path == file.filepath]
        dead_code.extend(file_dead_code)
        
        # Count imports
        imports_count = len(file.imports) if hasattr(file, 'imports') else 0
        
        # Count lines
        lines_of_code = len(file.source.split('\n')) if hasattr(file, 'source') else 0
        
        return FileAnalysis(
            file_path=file.filepath,
            lines_of_code=lines_of_code,
            functions=functions_metrics,
            classes=classes_metrics,
            imports_count=imports_count,
            issues=issues,
            dead_code=dead_code
        )
    
    def _analyze_function_graph_sitter(self, function) -> FunctionMetrics:
        """Analyze function using graph-sitter enhanced features."""
        # Get basic metrics
        name = function.name
        file_path = function.filepath
        line_number = getattr(function, 'line_number', 0)
        
        # Calculate complexity (use graph-sitter if available, fallback to estimation)
        complexity = getattr(function, 'cyclomatic_complexity', 1)
        
        # Get source and calculate metrics
        source = getattr(function, 'source', '')
        lines_of_code = len(source.split('\n')) if source else 0
        
        # Parameters count
        params_count = len(getattr(function, 'parameters', []))
        
        # Estimate other metrics
        halstead_volume = lines_of_code * 2.0  # Rough estimation
        halstead_difficulty = complexity * 0.5
        halstead_effort = halstead_volume * halstead_difficulty
        
        # Maintainability index
        mi = calculate_maintainability_index(halstead_volume, complexity, lines_of_code)
        
        # Check for docstring
        has_docstring = bool(getattr(function, 'docstring', None))
        
        # Return statements (rough estimation)
        return_statements = source.count('return') if source else 0
        
        return FunctionMetrics(
            name=name,
            file_path=file_path,
            line_number=line_number,
            cyclomatic_complexity=complexity,
            halstead_volume=halstead_volume,
            halstead_difficulty=halstead_difficulty,
            halstead_effort=halstead_effort,
            lines_of_code=lines_of_code,
            maintainability_index=mi,
            parameters_count=params_count,
            return_statements=return_statements,
            docstring_coverage=has_docstring
        )
    
    def _analyze_class_graph_sitter(self, cls) -> ClassMetrics:
        """Analyze class using graph-sitter enhanced features."""
        name = cls.name
        file_path = cls.filepath
        line_number = getattr(cls, 'line_number', 0)
        
        # Get methods and attributes
        methods_count = len(getattr(cls, 'methods', []))
        attributes_count = len(getattr(cls, 'attributes', []))
        
        # Inheritance depth
        inheritance_depth = len(getattr(cls, 'superclasses', []))
        
        # Get source and calculate metrics
        source = getattr(cls, 'source', '')
        lines_of_code = len(source.split('\n')) if source else 0
        
        # Check for docstring
        has_docstring = bool(getattr(cls, 'docstring', None))
        
        return ClassMetrics(
            name=name,
            file_path=file_path,
            line_number=line_number,
            methods_count=methods_count,
            attributes_count=attributes_count,
            inheritance_depth=inheritance_depth,
            coupling_factor=0.0,  # Would need more analysis
            cohesion_factor=0.0,  # Would need more analysis
            lines_of_code=lines_of_code,
            docstring_coverage=has_docstring
        )
    
    def _analyze_with_ast(self, path: str, extensions: List[str], start_time: float) -> ComprehensiveAnalysisResult:
        """Analyze using AST when graph-sitter is not available."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        files_analysis = []
        all_issues = []
        all_dead_code = []
        all_functions = set()
        all_classes = set()
        
        # Collect all Python files
        if path_obj.is_file():
            python_files = [path_obj] if path_obj.suffix in extensions else []
        else:
            python_files = []
            for ext in extensions:
                python_files.extend(path_obj.rglob(f"*{ext}"))
        
        # Analyze each file
        for file_path in python_files:
            try:
                file_analysis = self._analyze_file_ast(file_path, all_functions, all_classes)
                files_analysis.append(file_analysis)
                all_issues.extend(file_analysis.issues)
                all_dead_code.extend(file_analysis.dead_code)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
        
        # Calculate totals
        total_files = len(files_analysis)
        total_lines = sum(f.lines_of_code for f in files_analysis)
        total_functions = sum(len(f.functions) for f in files_analysis)
        total_classes = sum(len(f.classes) for f in files_analysis)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(files_analysis)
        
        analysis_time = time.time() - start_time
        
        return ComprehensiveAnalysisResult(
            total_files=total_files,
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            files=files_analysis,
            issues=all_issues,
            dead_code=all_dead_code,
            import_loops=[],  # Not available with AST analysis
            training_data=[],  # Not available with AST analysis
            graph_analysis=None,  # Not available with AST analysis
            quality_metrics=quality_metrics,
            analysis_time=analysis_time
        )
    
    def _analyze_file_ast(self, file_path: Path, all_functions: Set[str], all_classes: Set[str]) -> FileAnalysis:
        """Analyze a single file using AST."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        source_lines = source.split('\n')
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                lines_of_code=len(source_lines),
                functions=[],
                classes=[],
                imports_count=0,
                issues=[],
                dead_code=[]
            )
        
        # Analyze functions
        functions_metrics = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                all_functions.add(node.name)
                metrics = analyze_function_ast(node, str(file_path), source_lines)
                functions_metrics.append(metrics)
        
        # Analyze classes
        classes_metrics = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                all_classes.add(node.name)
                metrics = analyze_class_ast(node, str(file_path), source_lines)
                classes_metrics.append(metrics)
        
        # Detect issues
        issues = detect_code_issues(tree, str(file_path), source_lines)
        
        # Detect dead code
        dead_code = detect_dead_code_ast(tree, str(file_path), all_functions, all_classes)
        
        # Count imports
        imports_count = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
        
        return FileAnalysis(
            file_path=str(file_path),
            lines_of_code=len(source_lines),
            functions=functions_metrics,
            classes=classes_metrics,
            imports_count=imports_count,
            issues=issues,
            dead_code=dead_code
        )
    
    def _calculate_quality_metrics(self, files_analysis: List[FileAnalysis]) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        if not files_analysis:
            return {}
        
        # Collect all function metrics
        all_functions = []
        for file_analysis in files_analysis:
            all_functions.extend(file_analysis.functions)
        
        if not all_functions:
            return {}
        
        # Calculate averages
        avg_complexity = sum(f.cyclomatic_complexity for f in all_functions) / len(all_functions)
        avg_maintainability = sum(f.maintainability_index for f in all_functions) / len(all_functions)
        avg_loc_per_function = sum(f.lines_of_code for f in all_functions) / len(all_functions)
        
        # Calculate documentation coverage
        documented_functions = sum(1 for f in all_functions if f.docstring_coverage)
        doc_coverage = (documented_functions / len(all_functions)) * 100 if all_functions else 0
        
        # Calculate issue density
        total_issues = sum(len(f.issues) for f in files_analysis)
        total_lines = sum(f.lines_of_code for f in files_analysis)
        issue_density = (total_issues / total_lines) * 1000 if total_lines > 0 else 0  # Issues per 1000 lines
        
        return {
            'average_cyclomatic_complexity': round(avg_complexity, 2),
            'average_maintainability_index': round(avg_maintainability, 2),
            'average_lines_per_function': round(avg_loc_per_function, 2),
            'documentation_coverage_percent': round(doc_coverage, 2),
            'issue_density_per_1000_lines': round(issue_density, 2),
            'total_functions_analyzed': len(all_functions),
            'total_files_analyzed': len(files_analysis)
        }


# ============================================================================
# CLI INTERFACE AND CONVENIENCE FUNCTIONS
# ============================================================================

class AnalysisPresets:
    """Predefined analysis configurations."""
    
    @staticmethod
    def basic():
        """Basic analysis configuration."""
        return {
            'use_graph_sitter': True,
            'advanced_config': False,
            'extensions': ['.py']
        }
    
    @staticmethod
    def comprehensive():
        """Comprehensive analysis with all features."""
        return {
            'use_graph_sitter': True,
            'advanced_config': True,
            'extensions': ['.py']
        }
    
    @staticmethod
    def quality_focused():
        """Quality-focused analysis."""
        return {
            'use_graph_sitter': True,
            'advanced_config': False,
            'extensions': ['.py']
        }
    
    @staticmethod
    def ast_only():
        """AST-only analysis (no graph-sitter)."""
        return {
            'use_graph_sitter': False,
            'advanced_config': False,
            'extensions': ['.py']
        }

def analyze_codebase(path: str, config: Optional[Dict[str, Any]] = None) -> ComprehensiveAnalysisResult:
    """Convenience function for programmatic analysis.
    
    Args:
        path: Path to analyze
        config: Analysis configuration (uses basic preset if None)
    
    Returns:
        ComprehensiveAnalysisResult with analysis results
    """
    if config is None:
        config = AnalysisPresets.basic()
    
    analyzer = ComprehensiveAnalysisSystem(
        use_graph_sitter=config.get('use_graph_sitter', True),
        advanced_config=config.get('advanced_config', False)
    )
    
    return analyzer.analyze_codebase(
        path=path,
        extensions=config.get('extensions', ['.py'])
    )

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="🚀 Comprehensive Codebase Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/code                    # Basic analysis
  %(prog)s . --comprehensive               # Comprehensive analysis
  %(prog)s . --preset quality              # Quality-focused analysis
  %(prog)s . --export-html report.html     # Generate HTML report
  %(prog)s . --export-json results.json    # Export JSON results
  %(prog)s . --no-graph-sitter             # Use AST-only analysis
  %(prog)s . --advanced-config             # Use advanced graph-sitter config
        """
    )
    
    # Positional arguments
    parser.add_argument(
        'path',
        help='Path to analyze (file or directory)'
    )
    
    # Analysis options
    parser.add_argument(
        '--preset',
        choices=['basic', 'comprehensive', 'quality', 'ast-only'],
        default='basic',
        help='Analysis preset to use (default: basic)'
    )
    
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Enable comprehensive analysis with all features'
    )
    
    parser.add_argument(
        '--no-graph-sitter',
        action='store_true',
        help='Disable graph-sitter and use AST-only analysis'
    )
    
    parser.add_argument(
        '--advanced-config',
        action='store_true',
        help='Use advanced graph-sitter configuration'
    )
    
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.py'],
        help='File extensions to analyze (default: .py)'
    )
    
    # Output options
    parser.add_argument(
        '--export-json',
        metavar='FILE',
        help='Export results to JSON file'
    )
    
    parser.add_argument(
        '--export-html',
        metavar='FILE',
        help='Export results to HTML report'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser

def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine configuration
    if args.comprehensive:
        config = AnalysisPresets.comprehensive()
    elif args.preset == 'comprehensive':
        config = AnalysisPresets.comprehensive()
    elif args.preset == 'quality':
        config = AnalysisPresets.quality_focused()
    elif args.preset == 'ast-only' or args.no_graph_sitter:
        config = AnalysisPresets.ast_only()
    else:
        config = AnalysisPresets.basic()
    
    # Override with command-line options
    if args.no_graph_sitter:
        config['use_graph_sitter'] = False
    
    if args.advanced_config:
        config['advanced_config'] = True
    
    if args.extensions:
        config['extensions'] = args.extensions
    
    try:
        # Run analysis
        print(f"🚀 Starting comprehensive analysis of: {args.path}")
        print(f"📋 Configuration: {args.preset}")
        print(f"🔧 Graph-sitter: {'enabled' if config['use_graph_sitter'] else 'disabled'}")
        print(f"⚙️  Advanced config: {'enabled' if config['advanced_config'] else 'disabled'}")
        print(f"📁 Extensions: {', '.join(config['extensions'])}")
        print()
        
        result = analyze_codebase(args.path, config)
        
        # Print summary
        result.print_summary()
        
        # Export results
        if args.export_json:
            result.save_to_file(args.export_json, 'json')
            print(f"\n💾 Results exported to: {args.export_json}")
        
        if args.export_html:
            result.save_to_file(args.export_html, 'html')
            print(f"\n🌐 HTML report generated: {args.export_html}")
        
        # Exit with appropriate code
        if result.issues:
            critical_issues = [i for i in result.issues if i.severity == 'critical']
            if critical_issues:
                print(f"\n❌ Analysis completed with {len(critical_issues)} critical issues")
                sys.exit(1)
            else:
                print(f"\n⚠️  Analysis completed with {len(result.issues)} issues")
                sys.exit(0)
        else:
            print(f"\n✅ Analysis completed successfully with no issues")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
