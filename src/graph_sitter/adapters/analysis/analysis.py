"""
Comprehensive Code Analysis Module for Graph-sitter

This module provides advanced code analysis capabilities following the patterns
from https://graph-sitter.com/tutorials/at-a-glance with enhanced issue detection,
visualization, and interactive analysis features.

Features:
- Tree-sitter query pattern analysis
- Interactive syntax tree visualization
- Advanced code structure analysis
- Pattern-based code search
- Visualization export (JSON, DOT, HTML)

Usage:
    from graph_sitter import Codebase
    
    # Analyze local repository
    codebase = Codebase("path/to/git/repo")
    result = codebase.Analysis()
    
    # Analyze remote repository  
    codebase = Codebase.from_repo("fastapi/fastapi")
    result = codebase.Analysis()
    
    # Advanced analysis with visualization
    result = codebase.Analysis(enable_visualization=True, export_format="html")
"""

import ast
import os
import re
import sys
import json
import html
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
import tempfile
import webbrowser

try:
    from tree_sitter import Language, Parser, Node, Query
    TREE_SITTER_AVAILABLE = True
except ImportError:
    # Fallback for environments without tree-sitter
    Language = type(None)  # type: ignore
    Parser = type(None)    # type: ignore
    Node = type(None)      # type: ignore
    Query = type(None)     # type: ignore
    TREE_SITTER_AVAILABLE = False


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
class FileIssueInfo:
    """Information about a file with issues."""
    file_path: str
    issue_count: int
    issues: List[CodeIssue]
    functions: List[str]
    classes: List[str]
    top_level_functions: List[str]
    top_level_classes: List[str]
    inheritance_info: Dict[str, List[str]]  # class_name -> parent_classes


@dataclass
class InheritanceInfo:
    """Information about class inheritance hierarchy."""
    class_name: str
    file_path: str
    line_start: int
    parent_classes: List[str]
    child_classes: List[str]
    inheritance_depth: int
    is_top_level: bool


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
    files_with_issues: List[FileIssueInfo] = field(default_factory=list)
    inheritance_hierarchy: List[InheritanceInfo] = field(default_factory=list)
    top_level_functions: List[str] = field(default_factory=list)
    top_level_classes: List[str] = field(default_factory=list)
    file_analysis: Dict[str, Any] = field(default_factory=dict)
    
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
            'top_level_symbols': {
                'functions': self.top_level_functions,
                'classes': self.top_level_classes
            },
            'files_with_issues': [
                {
                    'file_path': file_info.file_path,
                    'issue_count': file_info.issue_count,
                    'top_level_functions': file_info.top_level_functions,
                    'top_level_classes': file_info.top_level_classes,
                    'inheritance_info': file_info.inheritance_info
                }
                for file_info in self.files_with_issues
            ],
            'inheritance_hierarchy': [
                {
                    'class_name': info.class_name,
                    'file_path': info.file_path,
                    'line_start': info.line_start,
                    'parent_classes': info.parent_classes,
                    'child_classes': info.child_classes,
                    'inheritance_depth': info.inheritance_depth,
                    'is_top_level': info.is_top_level
                }
                for info in self.inheritance_hierarchy
            ],
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


@dataclass
class TreeVisualization:
    """Tree visualization data structure."""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Result from tree-sitter query pattern matching."""
    pattern: str
    matches: List[Dict[str, Any]] = field(default_factory=list)
    captures: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


@dataclass
class VisualizationConfig:
    """Configuration for visualization features."""
    enable_syntax_tree: bool = False
    enable_call_graph: bool = False
    enable_dependency_graph: bool = False
    export_format: str = "json"  # json, dot, html, svg
    interactive: bool = False
    max_depth: int = 10
    highlight_patterns: List[str] = field(default_factory=list)


# Tree-sitter Query Patterns for Advanced Analysis
ANALYSIS_QUERIES = {
    "python": {
        "functions": """
        (function_definition
          name: (identifier) @function.name
          parameters: (parameters) @function.params
          body: (block) @function.body) @function.def
        """,
        "classes": """
        (class_definition
          name: (identifier) @class.name
          superclasses: (argument_list)? @class.bases
          body: (block) @class.body) @class.def
        """,
        "imports": """
        (import_statement
          name: (dotted_name) @import.module) @import.stmt
        (import_from_statement
          module_name: (dotted_name) @import.from_module
          name: (dotted_name) @import.name) @import.from_stmt
        """,
        "function_calls": """
        (call
          function: (identifier) @call.function
          arguments: (argument_list) @call.args) @call.expr
        """,
        "complexity_patterns": """
        (if_statement) @complexity.if
        (while_statement) @complexity.while
        (for_statement) @complexity.for
        (try_statement) @complexity.try
        (with_statement) @complexity.with
        """,
        "security_patterns": """
        (call
          function: (attribute
            object: (identifier) @security.object
            attribute: (identifier) @security.method)
          arguments: (argument_list) @security.args) @security.call
        (#match? @security.method "^(eval|exec|compile|__import__)$")
        """,
        "dead_code_patterns": """
        (function_definition
          name: (identifier) @dead.function.name) @dead.function
        (class_definition
          name: (identifier) @dead.class.name) @dead.class
        """
    },
    "javascript": {
        "functions": """
        (function_declaration
          name: (identifier) @function.name
          parameters: (formal_parameters) @function.params
          body: (statement_block) @function.body) @function.def
        """,
        "classes": """
        (class_declaration
          name: (identifier) @class.name
          superclass: (class_heritage)? @class.extends
          body: (class_body) @class.body) @class.def
        """,
        "imports": """
        (import_statement
          source: (string) @import.source) @import.stmt
        """,
        "complexity_patterns": """
        (if_statement) @complexity.if
        (while_statement) @complexity.while
        (for_statement) @complexity.for
        (try_statement) @complexity.try
        """
    }
}

class CodeAnalyzer:
    """Comprehensive code analyzer using AST and pattern matching."""
    
    def __init__(self, enable_tree_sitter: bool = True, visualization_config: Optional[VisualizationConfig] = None):
        self.issues: List[CodeIssue] = []
        self.metrics: Dict[str, Any] = {}
        self.symbol_usage: Dict[str, int] = defaultdict(int)
        self.function_definitions: Dict[str, Tuple[str, int, int]] = {}
        self.class_definitions: Dict[str, Tuple[str, int, int]] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.query_results: Dict[str, QueryResult] = {}
        self.tree_visualizations: Dict[str, TreeVisualization] = {}
        self.visualization_config = visualization_config or VisualizationConfig()
        
        # Tree-sitter setup
        self.enable_tree_sitter = enable_tree_sitter and TREE_SITTER_AVAILABLE
        self.tree_sitter_parser: Optional[Parser] = None
        self.tree_sitter_language: Optional[Language] = None
        self.tree_sitter_queries: Dict[str, Query] = {}
        
        if self.enable_tree_sitter:
            self._setup_tree_sitter()
    
    def _setup_tree_sitter(self):
        """Initialize tree-sitter parser and queries."""
        try:
            # Try to load Python language (most common)
            import tree_sitter_python as tspython
            self.tree_sitter_language = Language(tspython.language())
            self.tree_sitter_parser = Parser(self.tree_sitter_language)
            
            # Load query patterns
            for pattern_name, pattern_query in ANALYSIS_QUERIES.get("python", {}).items():
                try:
                    self.tree_sitter_queries[pattern_name] = self.tree_sitter_language.query(pattern_query)
                except Exception as e:
                    print(f"⚠️ Failed to load query pattern '{pattern_name}': {e}")
                    
        except ImportError:
            print("⚠️ tree-sitter-python not available, falling back to AST analysis")
            self.enable_tree_sitter = False
    
    def analyze_with_tree_sitter(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze file using tree-sitter queries."""
        if not self.enable_tree_sitter or not self.tree_sitter_parser:
            return {}
            
        try:
            # Parse the content
            tree = self.tree_sitter_parser.parse(content.encode('utf-8'))
            root_node = tree.root_node
            
            results = {}
            
            # Run all query patterns
            for pattern_name, query in self.tree_sitter_queries.items():
                try:
                    captures = query.captures(root_node)
                    query_result = QueryResult(pattern=pattern_name)
                    
                    for node, capture_name in captures:
                        capture_data = {
                            'name': capture_name,
                            'text': node.text.decode('utf-8') if node.text else '',
                            'start_point': node.start_point,
                            'end_point': node.end_point,
                            'start_byte': node.start_byte,
                            'end_byte': node.end_byte,
                            'type': node.type
                        }
                        
                        if capture_name not in query_result.captures:
                            query_result.captures[capture_name] = []
                        query_result.captures[capture_name].append(capture_data)
                        query_result.matches.append(capture_data)
                    
                    results[pattern_name] = query_result
                    self.query_results[f"{file_path}:{pattern_name}"] = query_result
                    
                except Exception as e:
                    print(f"⚠️ Query pattern '{pattern_name}' failed: {e}")
            
            # Generate syntax tree visualization if enabled
            if self.visualization_config.enable_syntax_tree:
                tree_viz = self._generate_tree_visualization(root_node, file_path)
                self.tree_visualizations[file_path] = tree_viz
            
            return results
            
        except Exception as e:
            print(f"⚠️ Tree-sitter analysis failed for {file_path}: {e}")
            return {}
    
    def _generate_tree_visualization(self, node: Node, file_path: str) -> TreeVisualization:
        """Generate tree visualization data from syntax tree."""
        viz = TreeVisualization()
        viz.metadata = {
            'file_path': file_path,
            'language': 'python',  # TODO: detect language
            'total_nodes': 0
        }
        
        def traverse_node(current_node: Node, parent_id: Optional[str] = None, depth: int = 0):
            if depth > self.visualization_config.max_depth:
                return
                
            node_id = f"node_{len(viz.nodes)}"
            viz.metadata['total_nodes'] += 1
            
            # Create node data
            node_data = {
                'id': node_id,
                'type': current_node.type,
                'text': current_node.text.decode('utf-8')[:100] if current_node.text else '',
                'start_point': current_node.start_point,
                'end_point': current_node.end_point,
                'depth': depth,
                'child_count': current_node.child_count,
                'is_named': current_node.is_named
            }
            viz.nodes.append(node_data)
            
            # Create edge to parent
            if parent_id:
                edge_data = {
                    'source': parent_id,
                    'target': node_id,
                    'type': 'child'
                }
                viz.edges.append(edge_data)
            
            # Traverse children
            for child in current_node.children:
                traverse_node(child, node_id, depth + 1)
        
        traverse_node(node)
        return viz
    
    def export_visualization(self, output_path: str, format_type: str = "html"):
        """Export visualization data in specified format."""
        if format_type == "json":
            self._export_json(output_path)
        elif format_type == "html":
            self._export_html(output_path)
        elif format_type == "dot":
            self._export_dot(output_path)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_json(self, output_path: str):
        """Export visualization data as JSON."""
        export_data = {
            'query_results': {k: {
                'pattern': v.pattern,
                'matches': v.matches,
                'captures': v.captures
            } for k, v in self.query_results.items()},
            'tree_visualizations': {k: {
                'nodes': v.nodes,
                'edges': v.edges,
                'metadata': v.metadata
            } for k, v in self.tree_visualizations.items()},
            'analysis_metadata': {
                'total_files': len(self.tree_visualizations),
                'total_queries': len(self.query_results),
                'export_timestamp': str(os.path.getmtime(__file__))
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_html(self, output_path: str):
        """Export interactive HTML visualization."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Graph-sitter Analysis Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .node {{ fill: #69b3a2; stroke: #333; stroke-width: 2px; }}
        .link {{ stroke: #999; stroke-opacity: 0.6; }}
        .tooltip {{ position: absolute; padding: 10px; background: rgba(0,0,0,0.8); color: white; border-radius: 5px; pointer-events: none; }}
        .query-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .file-section {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🔍 Graph-sitter Analysis Results</h1>
    
    <div id="summary">
        <h2>📊 Analysis Summary</h2>
        <p><strong>Total Files Analyzed:</strong> {len(self.tree_visualizations)}</p>
        <p><strong>Total Query Patterns:</strong> {len(set(qr.pattern for qr in self.query_results.values()))}</p>
        <p><strong>Total Matches:</strong> {sum(len(qr.matches) for qr in self.query_results.values())}</p>
    </div>
    
    <div id="query-results">
        <h2>🔍 Query Pattern Results</h2>
        {self._generate_query_results_html()}
    </div>
    
    <div id="visualization">
        <h2>🌳 Syntax Tree Visualization</h2>
        <svg id="tree-svg" width="800" height="600"></svg>
    </div>
    
    <script>
        // Visualization data
        const queryData = {json.dumps({k: {'pattern': v.pattern, 'matches': v.matches, 'captures': v.captures} for k, v in self.query_results.items()})};
        const treeData = {json.dumps({k: {'nodes': v.nodes, 'edges': v.edges, 'metadata': v.metadata} for k, v in self.tree_visualizations.items()})};
        
        // Simple tree visualization
        if (Object.keys(treeData).length > 0) {{
            const firstFile = Object.keys(treeData)[0];
            const nodes = treeData[firstFile].nodes.slice(0, 50); // Limit for performance
            const links = treeData[firstFile].edges.slice(0, 50);
            
            const svg = d3.select("#tree-svg");
            const width = 800, height = 600;
            
            const simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append("g")
                .selectAll("line")
                .data(links)
                .enter().append("line")
                .attr("class", "link");
            
            const node = svg.append("g")
                .selectAll("circle")
                .data(nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", 5)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            node.append("title")
                .text(d => `${{d.type}}: ${{d.text.substring(0, 50)}}`);
            
            simulation.on("tick", () => {{
                link.attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node.attr("cx", d => d.x)
                    .attr("cy", d => d.y);
            }});
            
            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }}
        }}
    </script>
</body>
</html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_query_results_html(self) -> str:
        """Generate HTML for query results."""
        html_parts = []
        
        # Group results by pattern
        pattern_groups = defaultdict(list)
        for key, result in self.query_results.items():
            pattern_groups[result.pattern].append((key, result))
        
        for pattern, results in pattern_groups.items():
            html_parts.append(f'<div class="query-section">')
            html_parts.append(f'<h3>🔍 Pattern: {html.escape(pattern)}</h3>')
            
            for key, result in results:
                file_path = key.split(':')[0]
                html_parts.append(f'<div class="file-section">')
                html_parts.append(f'<h4>📁 {html.escape(file_path)}</h4>')
                html_parts.append(f'<p><strong>Matches:</strong> {len(result.matches)}</p>')
                
                if result.captures:
                    html_parts.append('<ul>')
                    for capture_name, captures in result.captures.items():
                        html_parts.append(f'<li><strong>{html.escape(capture_name)}:</strong> {len(captures)} matches</li>')
                    html_parts.append('</ul>')
                
                html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _export_dot(self, output_path: str):
        """Export visualization as DOT format for Graphviz."""
        dot_content = ["digraph G {"]
        dot_content.append("  rankdir=TB;")
        dot_content.append("  node [shape=box, style=rounded];")
        
        for file_path, viz in self.tree_visualizations.items():
            # Add file as subgraph
            safe_name = file_path.replace('/', '_').replace('.', '_')
            dot_content.append(f'  subgraph cluster_{safe_name} {{')
            dot_content.append(f'    label="{file_path}";')
            
            # Add nodes
            for node in viz.nodes[:20]:  # Limit for readability
                node_label = f"{node['type']}\\n{node['text'][:20]}"
                dot_content.append(f'    {node["id"]} [label="{node_label}"];')
            
            # Add edges
            for edge in viz.edges[:20]:
                dot_content.append(f'    {edge["source"]} -> {edge["target"]};')
            
            dot_content.append("  }")
        
        dot_content.append("}")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(dot_content))
    
    def analyze(self, repo_path: Union[str, Path]) -> AnalysisResult:
        """Perform comprehensive code analysis."""
        print("🔍 Starting comprehensive code analysis...")
        
        repo_path = Path(repo_path)
        result = AnalysisResult()
        file_contents: Dict[str, str] = {}
        function_calls: Dict[str, Set[str]] = defaultdict(set)
        
        # Collect all Python files
        python_files = list(repo_path.rglob("*.py"))
        if not python_files:
            print("⚠️ No Python files found in the repository")
            return result
        
        print(f"📁 Found {len(python_files)} Python files")
        
        # Analyze each file
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_contents[str(file_path)] = content
                
                # Enhanced analysis with tree-sitter
                tree_sitter_results = self.analyze_with_tree_sitter(str(file_path), content)
                
                # Traditional AST analysis (fallback and complement)
                self._analyze_with_ast(file_path, content, result, function_calls)
                
                # Enhanced analysis with tree-sitter results
                if tree_sitter_results:
                    self._analyze_with_graph_sitter(file_path, content, result, tree_sitter_results)
                
            except Exception as e:
                issue = CodeIssue(
                    type="parse_error",
                    severity="critical",
                    message=f"Failed to parse file: {e}",
                    file_path=str(file_path),
                    line_start=1,
                    line_end=1,
                    suggestion="Check file encoding and syntax"
                )
                result.issues.append(issue)
                print(f"⚠️ Error analyzing {file_path}: {e}")
        
        # Detect dead code using symbol usage analysis
        self._detect_dead_code(result, function_calls, file_contents)
        
        # Calculate summary metrics
        result.total_files = len(python_files)
        result.total_functions = len([issue for issue in result.issues if issue.type == "function_definition"])
        result.total_classes = len([issue for issue in result.issues if issue.type == "class_definition"])
        
        # Enhanced metrics from tree-sitter analysis
        if self.query_results:
            self._calculate_enhanced_metrics(result)
        
        print(f"✅ Analysis complete: {result.total_files} files, {len(result.issues)} issues found")
        return result
    
    def _analyze_with_graph_sitter(self, file_path: Path, content: str, result: AnalysisResult, tree_sitter_results: Dict[str, Any]):
        """Enhanced analysis using tree-sitter query results."""
        
        # Process function analysis
        if "functions" in tree_sitter_results:
            functions_result = tree_sitter_results["functions"]
            for match in functions_result.matches:
                if match['name'] == 'function.name':
                    func_name = match['text']
                    start_line = match['start_point'][0] + 1
                    end_line = match['end_point'][0] + 1
                    
                    # Store function definition
                    self.function_definitions[func_name] = (str(file_path), start_line, end_line)
                    
                    # Add as info issue for tracking
                    issue = CodeIssue(
                        type="function_definition",
                        severity="info",
                        message=f"Function '{func_name}' defined",
                        file_path=str(file_path),
                        line_start=start_line,
                        line_end=end_line
                    )
                    result.issues.append(issue)
        
        # Process class analysis
        if "classes" in tree_sitter_results:
            classes_result = tree_sitter_results["classes"]
            for match in classes_result.matches:
                if match['name'] == 'class.name':
                    class_name = match['text']
                    start_line = match['start_point'][0] + 1
                    end_line = match['end_point'][0] + 1
                    
                    # Store class definition
                    self.class_definitions[class_name] = (str(file_path), start_line, end_line)
                    
                    # Add as info issue for tracking
                    issue = CodeIssue(
                        type="class_definition",
                        severity="info",
                        message=f"Class '{class_name}' defined",
                        file_path=str(file_path),
                        line_start=start_line,
                        line_end=end_line
                    )
                    result.issues.append(issue)
        
        # Process complexity patterns
        if "complexity_patterns" in tree_sitter_results:
            complexity_result = tree_sitter_results["complexity_patterns"]
            complexity_count = len(complexity_result.matches)
            
            if complexity_count > 10:  # High complexity threshold
                issue = CodeIssue(
                    type="high_complexity",
                    severity="major",
                    message=f"High complexity detected: {complexity_count} control flow statements",
                    file_path=str(file_path),
                    line_start=1,
                    line_end=len(content.split('\n')),
                    suggestion="Consider breaking down complex functions"
                )
                result.issues.append(issue)
        
        # Process security patterns
        if "security_patterns" in tree_sitter_results:
            security_result = tree_sitter_results["security_patterns"]
            for match in security_result.matches:
                if match['name'] == 'security.method':
                    method_name = match['text']
                    start_line = match['start_point'][0] + 1
                    
                    issue = CodeIssue(
                        type="security_risk",
                        severity="critical",
                        message=f"Potentially dangerous function call: {method_name}",
                        file_path=str(file_path),
                        line_start=start_line,
                        line_end=start_line,
                        suggestion=f"Review usage of {method_name} for security implications"
                    )
                    result.issues.append(issue)
        
        # Process function calls for usage tracking
        if "function_calls" in tree_sitter_results:
            calls_result = tree_sitter_results["function_calls"]
            for match in calls_result.matches:
                if match['name'] == 'call.function':
                    func_name = match['text']
                    self.symbol_usage[func_name] += 1
    
    def _calculate_enhanced_metrics(self, result: AnalysisResult):
        """Calculate enhanced metrics from tree-sitter analysis."""
        
        # Query pattern statistics
        total_patterns = len(set(qr.pattern for qr in self.query_results.values()))
        total_matches = sum(len(qr.matches) for qr in self.query_results.values())
        
        # Function and class counts from tree-sitter
        function_count = len(self.function_definitions)
        class_count = len(self.class_definitions)
        
        # Update result with enhanced metrics
        result.total_functions = max(result.total_functions, function_count)
        result.total_classes = max(result.total_classes, class_count)
        
        # Add enhanced metrics as info
        enhanced_info = CodeIssue(
            type="enhanced_metrics",
            severity="info",
            message=f"Enhanced analysis: {total_patterns} patterns, {total_matches} matches, {len(self.tree_visualizations)} visualizations",
            file_path="<analysis_summary>",
            line_start=1,
            line_end=1
        )
        result.issues.append(enhanced_info)
    
    def _analyze_with_ast(self, file_path: Path, content: str, result: AnalysisResult, function_calls: Dict[str, Set[str]]):
        """Traditional AST analysis."""
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
    
    def _detect_dead_code(self, result: AnalysisResult, function_calls: Dict[str, Set[str]], file_contents: Dict[str, str]):
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
            
            result.dead_code_items.append(DeadCodeItem(
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
    
    def _analyze_files_with_issues(self) -> None:
        """Analyze files with issues and create FileIssueInfo objects."""
        files_by_path = defaultdict(list)
        
        # Group issues by file
        for issue in self.result.issues:
            files_by_path[issue.file_path].append(issue)
        
        # Create FileIssueInfo for each file with issues
        for file_path, issues in files_by_path.items():
            functions = []
            classes = []
            top_level_functions = []
            top_level_classes = []
            inheritance_info = {}
            
            # Extract functions and classes from this file
            for func_name, (func_file, line_start, line_end) in self.function_definitions.items():
                if func_file == file_path:
                    functions.append(func_name)
                    # Check if it's top-level (not nested)
                    if self._is_top_level_function(func_name, file_path):
                        top_level_functions.append(func_name)
            
            for class_name, (class_file, line_start, line_end) in self.class_definitions.items():
                if class_file == file_path:
                    classes.append(class_name)
                    # Check if it's top-level (no inheritance)
                    if self._is_top_level_class(class_name, file_path):
                        top_level_classes.append(class_name)
                    
                    # Get inheritance info
                    inheritance_info[class_name] = self._get_class_parents(class_name, file_path)
            
            file_issue_info = FileIssueInfo(
                file_path=file_path,
                issue_count=len(issues),
                issues=issues,
                functions=functions,
                classes=classes,
                top_level_functions=top_level_functions,
                top_level_classes=top_level_classes,
                inheritance_info=inheritance_info
            )
            
            self.result.files_with_issues.append(file_issue_info)
    
    def _analyze_inheritance_hierarchy(self) -> None:
        """Analyze inheritance hierarchy for all classes."""
        inheritance_map: Dict[str, Dict[str, Any]] = {}

        # First pass: collect all classes and their basic info
        for class_name, (file_path, line_start, line_end) in self.class_definitions.items():
            inheritance_map[class_name] = {
                'file_path': file_path,
                'line_start': line_start,
                'parent_classes': [],
                'child_classes': [],
                'inheritance_depth': 0
            }

        # Second pass: analyze inheritance relationships using AST
        for file_path in set(info[0] for info in self.class_definitions.values()):
            if file_path in self.file_contents:
                try:
                    tree = ast.parse(self.file_contents[file_path])
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            if class_name in inheritance_map:
                                # Extract parent classes
                                for base in node.bases:
                                    if isinstance(base, ast.Name):
                                        parent_name = base.id
                                        parent_classes = inheritance_map[class_name]['parent_classes']
                                        if isinstance(parent_classes, list):
                                            parent_classes.append(parent_name)
                                        if parent_name in inheritance_map:
                                            child_classes = inheritance_map[parent_name]['child_classes']
                                            if isinstance(child_classes, list):
                                                child_classes.append(class_name)
                except Exception:
                    pass  # Skip files with syntax errors
        
        # Third pass: calculate inheritance depth
        def calculate_depth(class_name, visited=None):
            if visited is None:
                visited = set()
            if class_name in visited:
                return 0  # Circular inheritance
            visited.add(class_name)
            
            if class_name not in inheritance_map:
                return 0
            
            parents = inheritance_map[class_name]['parent_classes']
            if not parents:
                return 0
            
            max_depth = 0
            for parent in parents:
                depth = calculate_depth(parent, visited.copy())
                max_depth = max(max_depth, depth + 1)
            
            return max_depth
        
        # Create InheritanceInfo objects
        for class_name, info in inheritance_map.items():
            depth = calculate_depth(class_name)
            inheritance_info = InheritanceInfo(
                class_name=class_name,
                file_path=str(info['file_path']),
                line_start=int(info['line_start']),
                parent_classes=list(info['parent_classes']),
                child_classes=list(info['child_classes']),
                inheritance_depth=depth,
                is_top_level=(depth == 0)
            )
            self.result.inheritance_hierarchy.append(inheritance_info)
    
    def _identify_top_level_symbols(self) -> None:
        """Identify top-level functions and classes."""
        # Top-level functions (not nested in classes or other functions)
        for func_name, (file_path, line_start, line_end) in self.function_definitions.items():
            if self._is_top_level_function(func_name, file_path):
                self.result.top_level_functions.append(func_name)
        
        # Top-level classes (no inheritance or base classes)
        for inheritance_info in self.result.inheritance_hierarchy:
            if inheritance_info.is_top_level:
                self.result.top_level_classes.append(inheritance_info.class_name)
    
    def _is_top_level_function(self, func_name: str, file_path: str) -> bool:
        """Check if a function is top-level (not nested)."""
        if file_path not in self.file_contents:
            return False
        
        try:
            tree = ast.parse(self.file_contents[file_path])
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # Check if the function is at module level
                    for parent in ast.walk(tree):
                        if hasattr(parent, 'body') and node in parent.body:
                            return isinstance(parent, ast.Module)
            return False
        except Exception:
            return False
    
    def _is_top_level_class(self, class_name: str, file_path: str) -> bool:
        """Check if a class is top-level (no inheritance)."""
        if file_path not in self.file_contents:
            return False
        
        try:
            tree = ast.parse(self.file_contents[file_path])
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    return len(node.bases) == 0
            return False
        except Exception:
            return False
    
    def _get_class_parents(self, class_name: str, file_path: str) -> List[str]:
        """Get parent classes for a given class."""
        if file_path not in self.file_contents:
            return []
        
        try:
            tree = ast.parse(self.file_contents[file_path])
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    parents = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            parents.append(base.id)
                    return parents
            return []
        except Exception:
            return []


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
    output.append("��� Analysis Results:")
    output.append(f"  • Total Files: {result.total_files}")
    output.append(f"  • Total Functions: {result.total_functions}")
    output.append(f"  • Total Classes: {result.total_classes}")
    output.append(f"  • Total Lines: {result.total_lines}")
    output.append(f"  ��� Maintainability Index: {result.maintainability_index:.1f}/100")
    output.append(f"  • Technical Debt Ratio: {result.technical_debt_ratio:.2f}")
    output.append(f"  • Test Coverage Estimate: {result.test_coverage_estimate:.1f}%")
    output.append("")
    
    # Top-Level Symbols
    if result.top_level_functions or result.top_level_classes:
        output.append("🔝 Top-Level Symbols:")
        if result.top_level_functions:
            output.append(f"  • Top-Level Functions ({len(result.top_level_functions)}):")
            for i, func in enumerate(result.top_level_functions[:10], 1):
                output.append(f"    {i}. {func}")
            if len(result.top_level_functions) > 10:
                output.append(f"    ... and {len(result.top_level_functions) - 10} more functions")
        
        if result.top_level_classes:
            output.append(f"  • Top-Level Classes ({len(result.top_level_classes)}):")
            for i, cls in enumerate(result.top_level_classes[:10], 1):
                output.append(f"    {i}. {cls}")
            if len(result.top_level_classes) > 10:
                output.append(f"    ... and {len(result.top_level_classes) - 10} more classes")
        output.append("")
    
    # Files with Issues (Numbered List)
    if result.files_with_issues:
        output.append(f"📁 Files with Issues ({len(result.files_with_issues)}):")
        for i, file_info in enumerate(result.files_with_issues, 1):
            output.append(f"  {i}. {file_info.file_path}")
            output.append(f"     Issues: {file_info.issue_count}")
            if file_info.top_level_functions:
                output.append(f"     Top-Level Functions: {', '.join(file_info.top_level_functions[:5])}")
                if len(file_info.top_level_functions) > 5:
                    output.append(f"       ... and {len(file_info.top_level_functions) - 5} more")
            if file_info.top_level_classes:
                output.append(f"     Top-Level Classes: {', '.join(file_info.top_level_classes[:5])}")
                if len(file_info.top_level_classes) > 5:
                    output.append(f"       ... and {len(file_info.top_level_classes) - 5} more")
            if file_info.inheritance_info:
                output.append(f"     Inheritance: {len(file_info.inheritance_info)} classes with inheritance")
            output.append("")
    
    # Inheritance Hierarchy
    if result.inheritance_hierarchy:
        output.append(f"🏗️  Inheritance Hierarchy ({len(result.inheritance_hierarchy)} classes):")
        # Sort by inheritance depth (top-level first)
        sorted_hierarchy = sorted(result.inheritance_hierarchy, key=lambda x: x.inheritance_depth)
        for i, inheritance_info in enumerate(sorted_hierarchy[:15], 1):
            depth_indicator = "  " * inheritance_info.inheritance_depth
            output.append(f"  {i}. {depth_indicator}{inheritance_info.class_name}")
            output.append(f"     File: {inheritance_info.file_path}:{inheritance_info.line_start}")
            if inheritance_info.parent_classes:
                output.append(f"     Parents: {', '.join(inheritance_info.parent_classes)}")
            if inheritance_info.child_classes:
                output.append(f"     Children: {', '.join(inheritance_info.child_classes[:3])}")
                if len(inheritance_info.child_classes) > 3:
                    output.append(f"       ... and {len(inheritance_info.child_classes) - 3} more")
            output.append(f"     Depth: {inheritance_info.inheritance_depth}")
            output.append("")
        
        if len(result.inheritance_hierarchy) > 15:
            output.append(f"  ... and {len(result.inheritance_hierarchy) - 15} more classes")
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
