#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Tool with Interactive Web UI

This tool uses graph-sitter to analyze codebases and generate interactive visualizations
showing tree structure, entrypoints, dead code, and errors.
"""

import os
import sys
import json
import argparse
import webbrowser
import tempfile
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
import plotly.graph_objects as go
from flask import Flask, render_template, request, jsonify, send_from_directory

# Graph-sitter imports
from graph_sitter import Codebase
from graph_sitter.configs import CodebaseConfig
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, 
    get_file_summary, 
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Data classes for analysis results
@dataclass
class IssueInfo:
    """Represents a code issue with severity and context"""
    severity: str  # 'critical', 'major', 'minor'
    file_path: str
    function_name: Optional[str]
    line_number: int
    message: str
    context: str
    issue_type: str  # 'unused_param', 'dead_code', 'wrong_call', etc.

@dataclass
class EntryPointInfo:
    """Represents an entry point in the codebase"""
    file_path: str
    class_name: Optional[str]
    function_name: Optional[str]
    functions: List[str] = field(default_factory=list)
    is_main_entry: bool = False
    inheritance_depth: int = 0

@dataclass
class DeadCodeInfo:
    """Represents dead code analysis results"""
    file_path: str
    element_name: str
    element_type: str  # 'class', 'function', 'import'
    reason: str
    blast_radius: List[str] = field(default_factory=list)

@dataclass
class AnalysisResults:
    """Complete analysis results"""
    tree_structure: Dict[str, Any]
    entrypoints: List[EntryPointInfo]
    dead_code: List[DeadCodeInfo]
    issues: List[IssueInfo]
    summary_stats: Dict[str, Any]
    halstead_metrics: Dict[str, float]


class CodebaseAnalyzer:
    """Main analyzer class for comprehensive codebase analysis"""

    def __init__(self, repo_path: str, language: str = "python"):
        self.repo_path = repo_path
        self.language = language
        self.codebase = None
        self.import_graph = None
        self.call_graph = None
        self.issues = []
        self.entrypoints = []
        self.dead_code = []
        
    def load_codebase(self) -> Codebase:
        """Load codebase using graph-sitter with enhanced configuration"""
        print(f"📁 Loading codebase from {self.repo_path}...")

        try:
            # Configure graph-sitter for comprehensive analysis
            config = CodebaseConfig(
                debug=False,
                verify_graph=True,
                track_graph=True,
                method_usages=True,
                full_range_index=True,
                ignore_process_errors=True
            )
            
            # Check if it's a remote repository
            if '/' in self.repo_path and not os.path.exists(self.repo_path):
                # Remote repository
                print("🌐 Loading remote repository...")
                self.codebase = Codebase.from_repo(
                    self.repo_path,
                    language=self.language
                )
            else:
                # Local repository
                print("💻 Loading local repository...")
                self.codebase = Codebase(config)

            print(f"✅ Loaded {len(self.codebase.files)} files")
            return self.codebase

        except Exception as e:
            print(f"❌ Error loading codebase: {e}")
            raise
            
    def create_import_graph(self) -> nx.MultiDiGraph:
        """Create directed graph of import relationships"""
        print("🔗 Creating import dependency graph...")

        G = nx.MultiDiGraph()
        
        for imp in self.codebase.imports:
            if imp.from_file and imp.to_file:
                G.add_edge(
                    imp.to_file.filepath,
                    imp.from_file.filepath,
                    color="red" if getattr(imp, "is_dynamic", False) else "black",
                    label="dynamic" if getattr(imp, "is_dynamic", False) else "static",
                    is_dynamic=getattr(imp, "is_dynamic", False),
                )
        
        self.import_graph = G
        print(f"✅ Created import graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
        
    def create_call_graph(self) -> nx.DiGraph:
        """Create function call graph"""
        print("📞 Creating function call graph...")
        
        G = nx.DiGraph()
        
        for file in self.codebase.files:
            for function in file.functions:
                func_id = f"{file.filepath}::{function.name}"
                G.add_node(func_id, 
                          file_path=file.filepath,
                          function_name=function.name,
                          parameters=len(function.parameters) if function.parameters else 0)
                
                # Add function calls as edges
                for call in function.function_calls:
                    target_id = f"{file.filepath}::{call.name}"
                    G.add_edge(func_id, target_id, call_type="internal")
        
        self.call_graph = G
        print(f"✅ Created call graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
        
    def find_entrypoints(self) -> List[EntryPointInfo]:
        """Identify entry points in the codebase"""
        print("🎯 Identifying entry points...")
        
        entrypoints = []
        
        for file in self.codebase.files:
            # Check for main functions
            for function in file.functions:
                if function.name in ['main', '__main__', 'run', 'start', 'execute']:
                    entry = EntryPointInfo(
                        file_path=file.filepath,
                        class_name=None,
                        function_name=function.name,
                        is_main_entry=True
                    )
                    entrypoints.append(entry)
            
            # Check for classes with high inheritance or many methods
            for cls in file.classes:
                inheritance_depth = len(cls.superclasses) if cls.superclasses else 0
                method_names = [method.name for method in cls.methods] if cls.methods else []
                
                if inheritance_depth > 0 or len(method_names) > 5:
                    entry = EntryPointInfo(
                        file_path=file.filepath,
                        class_name=cls.name,
                        function_name=None,
                        functions=method_names,
                        inheritance_depth=inheritance_depth
                    )
                    entrypoints.append(entry)
        
        self.entrypoints = entrypoints
        print(f"✅ Found {len(entrypoints)} entry points")
        return entrypoints
        
    def find_dead_code(self) -> List[DeadCodeInfo]:
        """Identify dead code using symbol analysis"""
        print("💀 Analyzing dead code...")

        dead_code = []
        used_symbols = set()
        defined_symbols = set()

        if not self.codebase or not self.codebase.files:
            return dead_code

        # Track function calls
        for file in self.codebase.files:
            for function in file.functions:
                defined_symbols.add(f"{file.filepath}::{function.name}")
                for call in function.function_calls:
                    used_symbols.add(f"{file.filepath}::{call.name}")

            # Track class usages
            for cls in file.classes:
                defined_symbols.add(f"{file.filepath}::{cls.name}")
                # Check if class is instantiated or inherited
                for method in cls.methods if cls.methods else []:
                    for call in method.function_calls if method.function_calls else []:
                        if call.name == cls.name:  # Constructor call
                            used_symbols.add(f"{file.filepath}::{cls.name}")

        # Find unused functions
        for file in self.codebase.files:
            for function in file.functions:
                func_id = f"{file.filepath}::{function.name}"
                if func_id not in used_symbols and function.name not in ['main', '__main__', '__init__']:
                    dead_code.append(DeadCodeInfo(
                        file_path=file.filepath,
                        element_name=function.name,
                        element_type="function",
                        reason="Function is never called"
                    ))

        # Find unused classes
        for file in self.codebase.files:
            for cls in file.classes:
                cls_id = f"{file.filepath}::{cls.name}"
                if cls_id not in used_symbols:
                    dead_code.append(DeadCodeInfo(
                        file_path=file.filepath,
                        element_name=cls.name,
                        element_type="class",
                        reason="Class is never instantiated or inherited"
                    ))

        # Find unused imports
        for file in self.codebase.files:
            for imp in file.imports:
                # Check if imported symbol is used in the file
                symbol_used = False
                for function in file.functions:
                    for call in function.function_calls:
                        if hasattr(imp, 'symbol') and imp.symbol and imp.symbol in call.name:
                            symbol_used = True
                            break

                if not symbol_used and hasattr(imp, 'symbol') and imp.symbol:
                    dead_code.append(DeadCodeInfo(
                        file_path=file.filepath,
                        element_name=imp.symbol,
                        element_type="import",
                        reason="Imported symbol is never used"
                    ))

        self.dead_code = dead_code
        print(f"✅ Found {len(dead_code)} dead code items")
        return dead_code
        
    def analyze_issues(self) -> List[IssueInfo]:
        """Comprehensive issue analysis"""
        print("🚨 Analyzing code issues...")

        issues = []

        if not self.codebase or not self.codebase.files:
            return issues

        for file in self.codebase.files:
            # Analyze functions
            for function in file.functions:
                # Check for unused parameters
                if function.parameters:
                    for param in function.parameters:
                        param_used = False
                        # Check if parameter is used in function body
                        for call in function.function_calls:
                            if hasattr(call, 'args') and call.args:
                                for arg in call.args:
                                    if hasattr(arg, 'source') and param.name in arg.source:
                                        param_used = True
                                        break

                        if not param_used and param.name not in ['self', 'cls', 'args', 'kwargs']:
                            issues.append(IssueInfo(
                                severity="minor",
                                file_path=file.filepath,
                                function_name=function.name,
                                line_number=getattr(function, 'line_number', 0),
                                message=f"Unused parameter '{param.name}'",
                                context=f"Parameter '{param.name}' is defined but never used",
                                issue_type="unused_parameter"
                            ))

                # Check for high complexity
                complexity = self.calculate_cyclomatic_complexity(function)
                if complexity > 20:
                    issues.append(IssueInfo(
                        severity="major",
                        file_path=file.filepath,
                        function_name=function.name,
                        line_number=getattr(function, 'line_number', 0),
                        message=f"High cyclomatic complexity: {complexity}",
                        context=f"Function has complexity of {complexity}, consider refactoring",
                        issue_type="high_complexity"
                    ))
                elif complexity > 30:
                    issues.append(IssueInfo(
                        severity="critical",
                        file_path=file.filepath,
                        function_name=function.name,
                        line_number=getattr(function, 'line_number', 0),
                        message=f"Very high cyclomatic complexity: {complexity}",
                        context=f"Function has critical complexity of {complexity}",
                        issue_type="critical_complexity"
                    ))

        # Check for import cycles
        if self.import_graph:
            cycles = list(nx.strongly_connected_components(self.import_graph))
            for cycle in cycles:
                if len(cycle) > 1:
                    for file_path in cycle:
                        issues.append(IssueInfo(
                            severity="major",
                            file_path=file_path,
                            function_name=None,
                            line_number=0,
                            message="Part of import cycle",
                            context=f"File is part of circular import with {len(cycle)} files",
                            issue_type="import_cycle"
                        ))

        self.issues = issues
        print(f"✅ Found {len(issues)} issues")
        return issues
        
    def calculate_cyclomatic_complexity(self, function) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        # Count decision points in function
        if hasattr(function, 'code_block') and function.code_block:
            for statement in function.code_block.statements if function.code_block.statements else []:
                # Count if statements, loops, try-catch, etc.
                if hasattr(statement, 'ts_node'):
                    node_type = statement.ts_node.type
                    if node_type in ['if_statement', 'while_statement', 'for_statement',
                                   'try_statement', 'except_clause', 'elif_clause',
                                   'switch_statement', 'case_clause', 'conditional_expression']:
                        complexity += 1

        return complexity
        
    def build_tree_structure(self) -> Dict[str, Any]:
        """Build hierarchical tree structure with issue counts"""
        print("🌳 Building tree structure...")

        if not self.codebase or not self.codebase.files:
            return {}

        tree = {}
        issue_counts = {}
        
        # Count issues by file
        for issue in self.issues:
            if issue.file_path not in issue_counts:
                issue_counts[issue.file_path] = {'critical': 0, 'major': 0, 'minor': 0}
            issue_counts[issue.file_path][issue.severity] += 1

        # Build tree structure
        for file in self.codebase.files:
            path_parts = file.filepath.split('/')
            current = tree

            # Navigate/create directory structure
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {'type': 'directory', 'children': {}, 'issues': {'critical': 0, 'major': 0, 'minor': 0}}
                current = current[part]['children']

            # Add file
            filename = path_parts[-1]
            file_issues = issue_counts.get(file.filepath, {'critical': 0, 'major': 0, 'minor': 0})
            current[filename] = {
                'type': 'file',
                'filepath': file.filepath,
                'issues': file_issues,
                'functions': [f.name for f in file.functions] if file.functions else [],
                'classes': [c.name for c in file.classes] if file.classes else [],
                'total_issues': sum(file_issues.values())
            }

        # Propagate issue counts up the tree
        def propagate_issues(node):
            if node['type'] == 'directory':
                total_issues = {'critical': 0, 'major': 0, 'minor': 0}
                for child in node['children'].values():
                    child_issues = propagate_issues(child)
                    for severity in total_issues:
                        total_issues[severity] += child_issues[severity]
                node['issues'] = total_issues
                return total_issues
            else:
                return node['issues']

        for root_node in tree.values():
            if root_node['type'] == 'directory':
                propagate_issues(root_node)

        print("✅ Built tree structure")
        return tree
        
    def calculate_halstead_metrics(self) -> Dict[str, float]:
        """Calculate Halstead complexity metrics"""
        print("📊 Calculating Halstead metrics...")

        all_operators = []
        all_operands = []

        if not self.codebase or not self.codebase.files:
            return {}

        for file in self.codebase.files:
            for function in file.functions if file.functions else []:
                # Extract operators and operands
                operators, operands = self.get_operators_and_operands(function)
                all_operators.extend(operators)
                all_operands.extend(operands)

        # Calculate Halstead metrics
        if all_operators or all_operands:
            n1 = len(set(all_operators))  # Unique operators
            n2 = len(set(all_operands))   # Unique operands
            N1 = len(all_operators)       # Total operators
            N2 = len(all_operands)        # Total operands
            
            vocabulary = n1 + n2
            length = N1 + N2
            
            # Avoid division by zero
            if n1 > 0 and n2 > 0:
                volume = length * (vocabulary.bit_length())
                difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
                effort = difficulty * volume
            else:
                volume = difficulty = effort = 0
        else:
            n1 = n2 = N1 = N2 = vocabulary = length = volume = difficulty = effort = 0

        metrics = {
            'n1': n1, 'n2': n2, 'N1': N1, 'N2': N2,
            'vocabulary': vocabulary, 'length': length,
            'volume': volume, 'difficulty': difficulty, 'effort': effort
        }

        print(f"✅ Calculated Halstead metrics: Volume={volume:.2f}, Difficulty={difficulty:.2f}")
        return metrics

    def get_operators_and_operands(self, function) -> Tuple[List[str], List[str]]:
        """Extract operators and operands from a function"""
        operators = []
        operands = []

        if not hasattr(function, 'function_calls') or not function.function_calls:
            return operators, operands

        for call in function.function_calls:
            operators.append(call.name)
            if hasattr(call, 'args') and call.args:
                for arg in call.args:
                    if hasattr(arg, 'source'):
                        operands.append(arg.source)

        return operators, operands
        
    def run_comprehensive_analysis(self) -> AnalysisResults:
        """Run complete codebase analysis"""
        print("🚀 COMPREHENSIVE CODEBASE ANALYSIS")
        print("=" * 70)

        # Load codebase
        self.load_codebase()

        if not self.codebase:
            raise ValueError("Failed to load codebase")

        # Create graphs
        self.create_import_graph()
        self.create_call_graph()

        # Run core analyses
        entrypoints = self.find_entrypoints()
        dead_code = self.find_dead_code()
        issues = self.analyze_issues()
        tree_structure = self.build_tree_structure()
        halstead_metrics = self.calculate_halstead_metrics()

        # Calculate summary stats
        summary_stats = {
            'total_files': len(self.codebase.files) if self.codebase.files else 0,
            'total_functions': sum(len(f.functions) if f.functions else 0 for f in self.codebase.files),
            'total_classes': sum(len(f.classes) if f.classes else 0 for f in self.codebase.files),
            'total_issues': len(issues),
            'critical_issues': len([i for i in issues if i.severity == 'critical']),
            'major_issues': len([i for i in issues if i.severity == 'major']),
            'minor_issues': len([i for i in issues if i.severity == 'minor']),
            'dead_code_items': len(dead_code),
            'entry_points': len(entrypoints),
            'import_cycles': len([scc for scc in nx.strongly_connected_components(self.import_graph) if len(scc) > 1]) if self.import_graph else 0,
            'call_graph_nodes': self.call_graph.number_of_nodes() if self.call_graph else 0,
            'import_graph_nodes': self.import_graph.number_of_nodes() if self.import_graph else 0,
        }

        print("✅ Analysis completed!")
        print(f"   📁 Files: {summary_stats['total_files']}")
        print(f"   🔧 Functions: {summary_stats['total_functions']}")
        print(f"   🏗️ Classes: {summary_stats['total_classes']}")
        print(f"   🚨 Issues: {summary_stats['total_issues']}")
        print(f"   💀 Dead Code: {summary_stats['dead_code_items']}")
        print(f"   🔄 Import Cycles: {summary_stats['import_cycles']}")

        return AnalysisResults(
            tree_structure=tree_structure,
            entrypoints=entrypoints,
            dead_code=dead_code,
            issues=issues,
            summary_stats=summary_stats,
            halstead_metrics=halstead_metrics
        )
        
    def format_tree_output(self, tree: Dict[str, Any], entrypoints: List[EntryPointInfo], prefix: str = "", is_last: bool = True) -> str:
        """Format tree structure with embedded entrypoints and issues"""
        output = []

        items = list(tree.items())
        for i, (name, node) in enumerate(items):
            is_last_item = i == len(items) - 1

            # Choose appropriate icon
            if node['type'] == 'directory':
                icon = "📁"
                # Calculate total issues for directory
                total_issues = sum(node['issues'].values())
                issue_info = f" [Total: {total_issues} issues]" if total_issues > 0 else ""

                # Check for entrypoints in directory
                entrypoint_count = 0
                critical_count = node['issues']['critical']
                for entry in entrypoints:
                    if entry.file_path.startswith(name + "/") or (hasattr(node, 'filepath') and entry.file_path == node.get('filepath')):
                        entrypoint_count += 1

                entrypoint_info = f"[🟩 Entrypoint : {entrypoint_count}]" if entrypoint_count > 0 else ""
                critical_info = f"[⚠️ Critical: {critical_count}]" if critical_count > 0 else ""

                # Combine info
                combined_info = ""
                if entrypoint_info or critical_info:
                    combined_info = f" {entrypoint_info}{critical_info}"

                issue_info = combined_info + issue_info

            else:
                icon = "🐍" if name.endswith('.py') else "📄"
                issues = node['issues']
                issue_parts = []

                if issues['critical'] > 0:
                    issue_parts.append(f"⚠️ Critical: {issues['critical']}")
                if issues['major'] > 0:
                    issue_parts.append(f"👉 Major: {issues['major']}")
                if issues['minor'] > 0:
                    issue_parts.append(f"🔍 Minor: {issues['minor']}")

                issue_info = f" [{', '.join(issue_parts)}]" if issue_parts else ""

                # Check for entrypoints in this specific file
                for entry in entrypoints:
                    if entry.file_path == node.get('filepath'):
                        if entry.class_name:
                            function_list = ', '.join([f"'{f}'" for f in entry.functions[:10]])
                            if len(entry.functions) > 10:
                                function_list += f", ... (+{len(entry.functions)-10} more)"
                            entrypoint_info = f" [🟩 Entrypoint: Class: {entry.class_name} Function: {function_list}]"
                            issue_info = entrypoint_info + issue_info
                        elif entry.function_name:
                            entrypoint_info = f" [🟩 Entrypoint: Function: {entry.function_name}]"
                            issue_info = entrypoint_info + issue_info

            # Format line
            connector = "└── " if is_last_item else "├── "
            line = f"{prefix}{connector}{icon} {name}{issue_info}"
            output.append(line)

            # Recurse for directories
            if node['type'] == 'directory' and 'children' in node:
                extension = "    " if is_last_item else "│   "
                child_output = self.format_tree_output(node['children'], entrypoints, prefix + extension, True)
                output.append(child_output)

        return "\n".join(output)
        
    def generate_report(self, results: AnalysisResults) -> str:
        """Generate comprehensive analysis report"""
        report = []

        # Extract repository name from path
        repo_name = self.repo_path.split('/')[-1] if '/' in self.repo_path else self.repo_path

        # Tree structure with issues and entrypoints embedded
        report.append(f"{repo_name}/")
        report.append(self.format_tree_output(results.tree_structure, results.entrypoints))
        report.append("")

        # Entry points
        report.append(f"ENTRYPOINTS: [🟩-{len(results.entrypoints)}]")
        for i, entry in enumerate(results.entrypoints, 1):
            if entry.class_name:
                function_list = ', '.join([f"'{f}'" for f in entry.functions[:10]])
                if len(entry.functions) > 10:
                    function_list += f", ... (+{len(entry.functions)-10} more)"
                report.append(f"{i}. 🐍 {entry.file_path} [🟩 Entrypoint: Class: {entry.class_name} Function: {function_list}]")
            else:
                report.append(f"{i}. 🐍 {entry.file_path} [🟩 Entrypoint: Function: {entry.function_name}]")
        report.append("")

        # Dead code
        dead_by_type = {}
        for item in results.dead_code:
            if item.element_type not in dead_by_type:
                dead_by_type[item.element_type] = []
            dead_by_type[item.element_type].append(item)

        total_dead = len(results.dead_code)
        class_count = len(dead_by_type.get('class', []))
        function_count = len(dead_by_type.get('function', []))
        import_count = len(dead_by_type.get('import', []))

        report.append(f"DEAD CODE: {total_dead} [🔍Classes: {class_count}, 👉 Call Sites: {function_count}, 🟩 Unused Imports: {import_count}]")

        for i, item in enumerate(results.dead_code, 1):
            icon = "🔍" if item.element_type == "class" else "👉" if item.element_type == "function" else "🟩"
            report.append(f"{i}. {icon} {item.file_path} {item.element_type.title()}: '{item.element_name}' ['Not Used by any other code context']")
        report.append("")

        # Issues
        critical_issues = [i for i in results.issues if i.severity == 'critical']
        major_issues = [i for i in results.issues if i.severity == 'major']
        minor_issues = [i for i in results.issues if i.severity == 'minor']

        total_issues = len(results.issues)
        report.append(f"ERRORS: {total_issues} [⚠️ Critical: {len(critical_issues)}] [👉 Major: {len(major_issues)}] [🔍 Minor: {len(minor_issues)}]")

        # List all issues
        issue_counter = 1
        for issue in critical_issues + major_issues + minor_issues:
            icon = "⚠️" if issue.severity == "critical" else "👉" if issue.severity == "major" else "🔍"
            func_info = f" / Function - '{issue.function_name}'" if issue.function_name else ""
            report.append(f"{issue_counter} {icon}- {issue.file_path}{func_info} [{issue.message}] .... {issue.context}.....")
            issue_counter += 1

        return "\n".join(report)


class WebUI:
    """Web UI for interactive codebase analysis visualization"""
    
    def __init__(self, analyzer: CodebaseAnalyzer, results: AnalysisResults):
        self.analyzer = analyzer
        self.results = results
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page with repository input form"""
            return self.render_index()
        
        @self.app.route('/analyze', methods=['POST'])
        def analyze():
            """Analyze repository and show results"""
            repo_path = request.form.get('repo_path', '')
            if not repo_path:
                return self.render_index(error="Repository path is required")
                
            try:
                # Create a new analyzer for the requested repository
                analyzer = CodebaseAnalyzer(repo_path)
                results = analyzer.run_comprehensive_analysis()
                
                # Store results for later access
                self.analyzer = analyzer
                self.results = results
                
                return self.render_results()
            except Exception as e:
                return self.render_index(error=f"Error analyzing repository: {str(e)}")
        
        @self.app.route('/results')
        def results():
            """Show analysis results"""
            if not self.results:
                return self.render_index(error="No analysis results available")
                
            return self.render_results()
            
        @self.app.route('/api/tree')
        def api_tree():
            """API endpoint for tree structure data"""
            if not self.results:
                return jsonify({"error": "No analysis results available"})
                
            return jsonify(self.results.tree_structure)
            
        @self.app.route('/api/entrypoints')
        def api_entrypoints():
            """API endpoint for entrypoints data"""
            if not self.results:
                return jsonify({"error": "No analysis results available"})
                
            return jsonify([{
                "file_path": e.file_path,
                "class_name": e.class_name,
                "function_name": e.function_name,
                "functions": e.functions,
                "is_main_entry": e.is_main_entry,
                "inheritance_depth": e.inheritance_depth
            } for e in self.results.entrypoints])
            
        @self.app.route('/api/deadcode')
        def api_deadcode():
            """API endpoint for dead code data"""
            if not self.results:
                return jsonify({"error": "No analysis results available"})
                
            return jsonify([{
                "file_path": d.file_path,
                "element_name": d.element_name,
                "element_type": d.element_type,
                "reason": d.reason,
                "blast_radius": d.blast_radius
            } for d in self.results.dead_code])
            
        @self.app.route('/api/issues')
        def api_issues():
            """API endpoint for issues data"""
            if not self.results:
                return jsonify({"error": "No analysis results available"})
                
            return jsonify([{
                "severity": i.severity,
                "file_path": i.file_path,
                "function_name": i.function_name,
                "line_number": i.line_number,
                "message": i.message,
                "context": i.context,
                "issue_type": i.issue_type
            } for i in self.results.issues])
            
        @self.app.route('/api/summary')
        def api_summary():
            """API endpoint for summary stats"""
            if not self.results:
                return jsonify({"error": "No analysis results available"})
                
            return jsonify(self.results.summary_stats)
            
    def render_index(self, error=None):
        """Render index page with repository input form"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Codebase Analysis Tool</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding-top: 2rem; }
                .container { max-width: 800px; }
                .header { margin-bottom: 2rem; text-align: center; }
                .form-container { margin-bottom: 2rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Comprehensive Codebase Analysis</h1>
                    <p class="lead">Analyze any GitHub repository or local codebase</p>
                </div>
                
                <div class="form-container">
                    <div class="card">
                        <div class="card-body">
                            <form action="/analyze" method="post">
                                <div class="mb-3">
                                    <label for="repo_path" class="form-label">Repository Path</label>
                                    <input type="text" class="form-control" id="repo_path" name="repo_path" 
                                           placeholder="e.g., username/repo or /path/to/local/repo" required>
                                    <div class="form-text">Enter a GitHub repository (username/repo) or local path</div>
                                </div>
                                
                                <button type="submit" class="btn btn-primary">Analyze Repository</button>
                            </form>
                        </div>
                    </div>
                </div>
                
                """ + (f"""
                <div class="alert alert-danger" role="alert">
                    {error}
                </div>
                """ if error else "") + """
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>Features</h5>
                    </div>
                    <div class="card-body">
                        <ul>
                            <li>Interactive tree structure visualization</li>
                            <li>Entry point detection</li>
                            <li>Dead code identification</li>
                            <li>Code issue analysis</li>
                            <li>Complexity metrics</li>
                        </ul>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5>Examples</h5>
                    </div>
                    <div class="card-body">
                        <ul>
                            <li><a href="#" onclick="document.getElementById('repo_path').value='fastapi/fastapi'; return false;">fastapi/fastapi</a></li>
                            <li><a href="#" onclick="document.getElementById('repo_path').value='pallets/flask'; return false;">pallets/flask</a></li>
                            <li><a href="#" onclick="document.getElementById('repo_path').value='django/django'; return false;">django/django</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        return html
        
    def render_results(self):
        """Render analysis results page"""
        # Extract repository name
        repo_name = self.analyzer.repo_path.split('/')[-1] if '/' in self.analyzer.repo_path else self.analyzer.repo_path
        
        # Get summary stats
        stats = self.results.summary_stats
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Analysis Results - {repo_name}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ padding-top: 2rem; }}
                .header {{ margin-bottom: 2rem; }}
                .nav-tabs {{ margin-bottom: 1rem; }}
                .tree-container {{ 
                    font-family: monospace; 
                    white-space: pre; 
                    overflow-x: auto;
                    background-color: #f8f9fa;
                    padding: 1rem;
                    border-radius: 0.25rem;
                }}
                .issue-item {{ margin-bottom: 0.5rem; }}
                .issue-critical {{ color: #dc3545; }}
                .issue-major {{ color: #fd7e14; }}
                .issue-minor {{ color: #6c757d; }}
                .entrypoint-item {{ margin-bottom: 0.5rem; }}
                .deadcode-item {{ margin-bottom: 0.5rem; }}
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h1>Analysis Results: {repo_name}</h1>
                        <a href="/" class="btn btn-outline-primary">New Analysis</a>
                    </div>
                </div>
                
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>Summary</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <div class="card text-center mb-3">
                                            <div class="card-body">
                                                <h3>{stats['total_files']}</h3>
                                                <p class="mb-0">Files</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="card text-center mb-3">
                                            <div class="card-body">
                                                <h3>{stats['total_functions']}</h3>
                                                <p class="mb-0">Functions</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="card text-center mb-3">
                                            <div class="card-body">
                                                <h3>{stats['total_issues']}</h3>
                                                <p class="mb-0">Issues</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="card text-center mb-3">
                                            <div class="card-body">
                                                <h3>{stats['dead_code_items']}</h3>
                                                <p class="mb-0">Dead Code Items</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <ul class="nav nav-tabs" id="myTab" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="tree-tab" data-bs-toggle="tab" data-bs-target="#tree" type="button" role="tab" aria-controls="tree" aria-selected="true">Tree Structure</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="entrypoints-tab" data-bs-toggle="tab" data-bs-target="#entrypoints" type="button" role="tab" aria-controls="entrypoints" aria-selected="false">Entry Points ({len(self.results.entrypoints)})</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="deadcode-tab" data-bs-toggle="tab" data-bs-target="#deadcode" type="button" role="tab" aria-controls="deadcode" aria-selected="false">Dead Code ({len(self.results.dead_code)})</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="issues-tab" data-bs-toggle="tab" data-bs-target="#issues" type="button" role="tab" aria-controls="issues" aria-selected="false">Issues ({len(self.results.issues)})</button>
                    </li>
                </ul>
                
                <div class="tab-content" id="myTabContent">
                    <div class="tab-pane fade show active" id="tree" role="tabpanel" aria-labelledby="tree-tab">
                        <div class="tree-container">
                            {self.analyzer.format_tree_output(self.results.tree_structure, self.results.entrypoints)}
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="entrypoints" role="tabpanel" aria-labelledby="entrypoints-tab">
                        <div class="list-group">
                            {self.render_entrypoints()}
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="deadcode" role="tabpanel" aria-labelledby="deadcode-tab">
                        <div class="list-group">
                            {self.render_deadcode()}
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="issues" role="tabpanel" aria-labelledby="issues-tab">
                        <div class="list-group">
                            {self.render_issues()}
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        return html
        
    def render_entrypoints(self):
        """Render entrypoints list"""
        if not self.results.entrypoints:
            return "<p>No entry points found.</p>"
            
        html = ""
        for i, entry in enumerate(self.results.entrypoints, 1):
            if entry.class_name:
                function_list = ', '.join([f"'{f}'" for f in entry.functions[:10]])
                if len(entry.functions) > 10:
                    function_list += f", ... (+{len(entry.functions)-10} more)"
                html += f"""
                <div class="list-group-item entrypoint-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">🟩 Class: {entry.class_name}</h5>
                        <small>Entry Point #{i}</small>
                    </div>
                    <p class="mb-1">File: {entry.file_path}</p>
                    <p class="mb-1">Methods: {function_list}</p>
                    <small>Inheritance Depth: {entry.inheritance_depth}</small>
                </div>
                """
            else:
                html += f"""
                <div class="list-group-item entrypoint-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">🟩 Function: {entry.function_name}</h5>
                        <small>Entry Point #{i}</small>
                    </div>
                    <p class="mb-1">File: {entry.file_path}</p>
                    <small>{"Main Entry Point" if entry.is_main_entry else ""}</small>
                </div>
                """
        return html
        
    def render_deadcode(self):
        """Render dead code list"""
        if not self.results.dead_code:
            return "<p>No dead code found.</p>"
            
        html = ""
        for i, item in enumerate(self.results.dead_code, 1):
            icon = "🔍" if item.element_type == "class" else "👉" if item.element_type == "function" else "🟩"
            html += f"""
            <div class="list-group-item deadcode-item">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">{icon} {item.element_type.title()}: {item.element_name}</h5>
                    <small>Dead Code #{i}</small>
                </div>
                <p class="mb-1">File: {item.file_path}</p>
                <small>Reason: {item.reason}</small>
            </div>
            """
        return html
        
    def render_issues(self):
        """Render issues list"""
        if not self.results.issues:
            return "<p>No issues found.</p>"
            
        html = ""
        for i, issue in enumerate(self.results.issues, 1):
            severity_class = {
                "critical": "issue-critical",
                "major": "issue-major",
                "minor": "issue-minor"
            }.get(issue.severity, "")
            
            icon = "⚠️" if issue.severity == "critical" else "👉" if issue.severity == "major" else "🔍"
            
            html += f"""
            <div class="list-group-item issue-item">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1 {severity_class}">{icon} {issue.message}</h5>
                    <small>Issue #{i}</small>
                </div>
                <p class="mb-1">File: {issue.file_path}</p>
                <p class="mb-1">{"Function: " + issue.function_name if issue.function_name else ""}</p>
                <p class="mb-1">Line: {issue.line_number}</p>
                <small>{issue.context}</small>
            </div>
            """
        return html
        
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Run the Flask web server"""
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analysis Tool")
    parser.add_argument("--repo", "-r", help="Repository path (local) or name (GitHub)")
    parser.add_argument("--output", "-o", help="Output file for report (default: stdout)")
    parser.add_argument("--web", "-w", action="store_true", help="Launch web UI")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port for web UI (default: 5000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for web UI (default: 0.0.0.0)")
    parser.add_argument("--language", "-l", help="Programming language (default: auto-detect)")
    args = parser.parse_args()
    
    if args.web and not args.repo:
        # Start web UI without initial analysis
        analyzer = CodebaseAnalyzer(".")  # Dummy analyzer
        webui = WebUI(analyzer, None)
        print(f"🌐 Starting web UI at http://{args.host}:{args.port}")
        webui.run(host=args.host, port=args.port)
        return
        
    if not args.repo:
        parser.print_help()
        return
        
    # Create analyzer and run analysis
    analyzer = CodebaseAnalyzer(args.repo, language=args.language)
    results = analyzer.run_comprehensive_analysis()
    
    # Generate report
    report = analyzer.generate_report(results)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"✅ Report written to {args.output}")
    elif not args.web:
        print(report)
        
    if args.web:
        # Start web UI with analysis results
        webui = WebUI(analyzer, results)
        print(f"🌐 Starting web UI at http://{args.host}:{args.port}")
        webui.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
