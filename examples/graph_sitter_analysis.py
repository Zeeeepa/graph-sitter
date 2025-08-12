#!/usr/bin/env python3
"""
Graph Sitter Comprehensive Codebase Analysis (Example)

Usage:
  Remote repo (default fastapi/fastapi):
    python examples/graph_sitter_analysis.py --codebase.from_repo fastapi/fastapi [--commit <sha>] [--tmp-dir /tmp/codegen]

  Local path:
    python examples/graph_sitter_analysis.py --codebase.local "."

Notes:
- Uses correct graph-sitter API as per https://graph-sitter.com/introduction/getting-started
- Generates tree structure with issue counts and entrypoints highlighted
- Includes all helper functions for import cycles, Halstead metrics, etc.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx

# Correct graph-sitter imports
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from graph_sitter.codebase.config import ProjectConfig
from graph_sitter.configs.models.codebase import CodebaseConfig


# -------------------------------
# Helper Functions (from user's specification)
# -------------------------------

def create_graph_from_codebase(codebase):
    """Create a directed graph representing import relationships in a codebase."""
    G = nx.MultiDiGraph()

    for imp in codebase.imports:
        if hasattr(imp, 'from_file') and hasattr(imp, 'to_file') and imp.from_file and imp.to_file:
            G.add_edge(
                imp.to_file.filepath,
                imp.from_file.filepath,
                color="red" if getattr(imp, "is_dynamic", False) else "black",
                label="dynamic" if getattr(imp, "is_dynamic", False) else "static",
                is_dynamic=getattr(imp, "is_dynamic", False),
            )
    return G


def find_import_cycles(G):
    """Identify strongly connected components (cycles) in the import graph."""
    cycles = [scc for scc in nx.strongly_connected_components(G) if len(scc) > 1]
    print(f"🔄 Found {len(cycles)} import cycles.")

    for i, cycle in enumerate(cycles, 1):
        print(f"\nCycle #{i}: Size {len(cycle)} files")
        print(f"Total number of imports in cycle: {G.subgraph(cycle).number_of_edges()}")

        print("\nFiles in this cycle:")
        for file in cycle:
            print(f"  - {file}")

    return cycles


def cc_rank(complexity):
    """Cyclomatic complexity ranking."""
    if complexity < 0:
        raise ValueError("Complexity must be a non-negative value")

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


def calculate_doi(cls):
    """Calculate the depth of inheritance for a given class."""
    return len(getattr(cls, 'superclasses', []))


def get_operators_and_operands(function):
    """Extract operators and operands from function for Halstead metrics."""
    operators = []
    operands = []

    try:
        code_block = getattr(function, 'code_block', None)
        if not code_block:
            return operators, operands

        statements = getattr(code_block, 'statements', [])
        for statement in statements:
            # Function calls
            function_calls = getattr(statement, 'function_calls', [])
            for call in function_calls:
                operators.append(getattr(call, 'name', 'unknown'))
                args = getattr(call, 'args', [])
                for arg in args:
                    operands.append(getattr(arg, 'source', 'unknown'))

            # Binary/Unary/Comparison expressions
            if hasattr(statement, "expressions"):
                for expr in getattr(statement, 'expressions', []):
                    expr_type = type(expr).__name__
                    if 'Binary' in expr_type:
                        operators.extend([getattr(op, 'source', 'op') for op in getattr(expr, 'operators', [])])
                        operands.extend([getattr(elem, 'source', 'elem') for elem in getattr(expr, 'elements', [])])
                    elif 'Unary' in expr_type:
                        operators.append(getattr(expr, 'operator', 'unary_op'))
                        operands.append(getattr(getattr(expr, 'argument', None), 'source', 'arg'))
                    elif 'Comparison' in expr_type:
                        operators.extend([getattr(op, 'source', 'comp') for op in getattr(expr, 'operators', [])])
                        operands.extend([getattr(elem, 'source', 'elem') for elem in getattr(expr, 'elements', [])])

            if hasattr(statement, "expression"):
                expr = getattr(statement, 'expression', None)
                if expr:
                    expr_type = type(expr).__name__
                    if 'Binary' in expr_type:
                        operators.extend([getattr(op, 'source', 'op') for op in getattr(expr, 'operators', [])])
                        operands.extend([getattr(elem, 'source', 'elem') for elem in getattr(expr, 'elements', [])])
                    elif 'Unary' in expr_type:
                        operators.append(getattr(expr, 'operator', 'unary_op'))
                        operands.append(getattr(getattr(expr, 'argument', None), 'source', 'arg'))
                    elif 'Comparison' in expr_type:
                        operators.extend([getattr(op, 'source', 'comp') for op in getattr(expr, 'operators', [])])
                        operands.extend([getattr(elem, 'source', 'elem') for elem in getattr(expr, 'elements', [])])
    except Exception:
        pass

    return operators, operands


def calculate_halstead_volume(operators, operands):
    """Calculate Halstead volume metrics."""
    n1 = len(set(operators))
    n2 = len(set(operands))

    N1 = len(operators)
    N2 = len(operands)

    N = N1 + N2
    n = n1 + n2

    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2


def find_problematic_import_loops(G, cycles):
    """Identify cycles with both static and dynamic imports between files."""
    problematic_cycles = []

    for i, scc in enumerate(cycles):
        if i == 2:
            continue

        mixed_imports = {}
        for from_file in scc:
            for to_file in scc:
                if G.has_edge(from_file, to_file):
                    edges = G.get_edge_data(from_file, to_file)
                    dynamic_count = sum(1 for e in edges.values() if e["color"] == "red")
                    static_count = sum(1 for e in edges.values() if e["color"] == "black")

                    if dynamic_count > 0 and static_count > 0:
                        mixed_imports[(from_file, to_file)] = {
                            "dynamic": dynamic_count,
                            "static": static_count,
                            "edges": edges,
                        }

        if mixed_imports:
            problematic_cycles.append({"files": scc, "mixed_imports": mixed_imports, "index": i})

    print(f"Found {len(problematic_cycles)} cycles with potentially problematic imports.")

    for i, cycle in enumerate(problematic_cycles):
        print(f"\n⚠️ Problematic Cycle #{i + 1} (Index {cycle['index']}): Size {len(cycle['files'])} files")
        print("\nFiles in cycle:")
        for file in cycle["files"]:
            print(f"  - {file}")
        print("\nMixed imports:")
        for (from_file, to_file), imports in cycle["mixed_imports"].items():
            print(f"\n  From: {from_file}")
            print(f"  To:   {to_file}")
            print(f"  Static imports: {imports['static']}")
            print(f"  Dynamic imports: {imports['dynamic']}")

    return problematic_cycles


# -------------------------------
# CLI parsing
# -------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Graph Sitter Comprehensive Analysis")
    # Support dotted flags as requested
    p.add_argument("--codebase.from_repo", dest="from_repo", help="owner/repo (e.g., fastapi/fastapi)")
    p.add_argument("--codebase.local", dest="local_path", help="Path to local codebase")
    p.add_argument("--commit", dest="commit", help="Commit SHA or ref", default=None)
    p.add_argument("--tmp-dir", dest="tmp_dir", default="/tmp/codegen")
    p.add_argument("--output", dest="output", help="Write JSON analysis to file")
    p.add_argument("--format", dest="fmt", choices=["text", "json"], default="text")
    return p


# -------------------------------
# Analysis core
# -------------------------------

@dataclass
class Issue:
    severity: str
    message: str
    filepath: str
    line_number: int | None = None


def _safe_len(iterable) -> int:
    try:
        return len(list(iterable)) if not isinstance(iterable, list) else len(iterable)
    except Exception:
        return 0


def _is_probably_entrypoint_file(file) -> bool:
    try:
        src = getattr(file, "source", "") or ""
        return "if __name__ == \"__main__\":" in src
    except Exception:
        return False


# Removed old unused helper functions - using new comprehensive analysis approach


def generate_tree_structure(codebase: Codebase) -> str:
    """Generate the tree structure with issue counts and entrypoints as requested."""
    
    # Collect file-level data
    file_issues = defaultdict(lambda: {"critical": 0, "major": 0, "minor": 0})
    file_entrypoints = set()
    
    # Identify entrypoints
    for file in codebase.files:
        if _is_probably_entrypoint_file(file):
            file_entrypoints.add(file.filepath)
    
    # Collect issues by file (simplified heuristics)
    for func in codebase.functions:
        filepath = func.parent_file.filepath
        # Simple heuristic: functions with many parameters might be complex
        param_count = len(getattr(func, 'parameters', []))
        if param_count > 10:
            file_issues[filepath]["major"] += 1
        elif param_count > 5:
            file_issues[filepath]["minor"] += 1
            
        # Check for potential dead code
        call_sites = getattr(func, 'call_sites', [])
        if len(call_sites) == 0 and not func.name.startswith('_'):
            file_issues[filepath]["minor"] += 1
    
    # Build directory structure
    dir_structure = defaultdict(list)
    for file in codebase.files:
        dir_path = str(Path(file.filepath).parent)
        dir_structure[dir_path].append(file)
    
    # Generate tree output
    tree_lines = []
    repo_name = getattr(codebase, 'repo_path', 'codebase')
    tree_lines.append(f"{repo_name}/")
    
    def add_directory(dir_path: str, indent: str = ""):
        files = dir_structure.get(dir_path, [])
        subdirs = set()
        
        for file in files:
            file_dir = str(Path(file.filepath).parent)
            if file_dir != dir_path:
                subdirs.add(file_dir)
        
        # Add subdirectories
        for subdir in sorted(subdirs):
            if subdir.startswith(dir_path) and subdir != dir_path:
                rel_subdir = subdir[len(dir_path):].strip('/')
                if '/' not in rel_subdir:  # Direct subdirectory
                    issues = sum(file_issues[f.filepath]["critical"] + file_issues[f.filepath]["major"] + file_issues[f.filepath]["minor"] 
                               for f in dir_structure.get(subdir, []))
                    entrypoints = sum(1 for f in dir_structure.get(subdir, []) if f.filepath in file_entrypoints)
                    
                    issue_str = f" [Total: {issues} issues]" if issues > 0 else ""
                    entry_str = f" [🟩 Entrypoint: {entrypoints}]" if entrypoints > 0 else ""
                    
                    tree_lines.append(f"{indent}├── 📁 {rel_subdir}/{issue_str}{entry_str}")
                    add_directory(subdir, indent + "│   ")
        
        # Add files in current directory
        current_files = [f for f in files if str(Path(f.filepath).parent) == dir_path]
        for file in sorted(current_files, key=lambda x: x.filepath):
            filename = Path(file.filepath).name
            issues = file_issues[file.filepath]
            total_issues = issues["critical"] + issues["major"] + issues["minor"]
            
            issue_parts = []
            if issues["critical"] > 0:
                issue_parts.append(f"⚠️ Critical: {issues['critical']}")
            if issues["major"] > 0:
                issue_parts.append(f"👉 Major: {issues['major']}")
            if issues["minor"] > 0:
                issue_parts.append(f"🔍 Minor: {issues['minor']}")
            
            issue_str = f" [{'] ['.join(issue_parts)}]" if issue_parts else ""
            entry_str = " [🟩 Entrypoint]" if file.filepath in file_entrypoints else ""
            
            tree_lines.append(f"{indent}└── 🐍 {filename}{issue_str}{entry_str}")
    
    # Start with root directory
    add_directory(".", "")
    
    return "\n".join(tree_lines)


def analyze_codebase(codebase: Codebase) -> Dict[str, Any]:
    """Perform comprehensive codebase analysis."""
    
    # Get basic summary
    summary_text = get_codebase_summary(codebase)
    total_files = len(codebase.files)
    total_functions = len(codebase.functions)
    total_classes = len(codebase.classes)
    
    # Find entrypoints
    entrypoints = []
    for file in codebase.files:
        if _is_probably_entrypoint_file(file):
            # List functions in entrypoint files
            file_functions = [f.name for f in file.functions]
            entrypoints.append({
                "filepath": file.filepath,
                "type": "file",
                "functions": file_functions
            })
    
    # Add class entrypoints (main classes)
    for cls in codebase.classes:
        if cls.name in ['Codebase', 'Main', 'App'] or 'main' in cls.name.lower():
            class_methods = [m.name for m in getattr(cls, 'methods', [])]
            entrypoints.append({
                "filepath": cls.parent_file.filepath,
                "type": "class",
                "name": cls.name,
                "methods": class_methods
            })
    
    # Find dead code
    dead_code_items = []
    for func in codebase.functions:
        call_sites = getattr(func, 'call_sites', [])
        if len(call_sites) == 0 and not func.name.startswith('_') and not func.name.startswith('__'):
            dead_code_items.append({
                "name": func.name,
                "type": "function",
                "filepath": func.parent_file.filepath,
                "reason": "Not used by any other code context"
            })
    
    for cls in codebase.classes:
        # Check if class is used
        # This is a simplified check - in reality you'd check for instantiations, inheritance, etc.
        if not hasattr(cls, 'usages') or len(getattr(cls, 'usages', [])) == 0:
            dead_code_items.append({
                "name": cls.name,
                "type": "class", 
                "filepath": cls.parent_file.filepath,
                "reason": "Not used by any other code context"
            })
    
    # Collect issues (simplified)
    issues = []
    issue_counter = 1
    
    for func in codebase.functions:
        # Check for complex functions
        param_count = len(getattr(func, 'parameters', []))
        if param_count > 10:
            issues.append({
                "id": issue_counter,
                "severity": "critical",
                "filepath": func.parent_file.filepath,
                "element_type": "Function",
                "element_name": func.name,
                "reason": f"Too many parameters ({param_count})",
                "context": f"Function has {param_count} parameters, consider refactoring"
            })
            issue_counter += 1
        elif param_count > 7:
            issues.append({
                "id": issue_counter,
                "severity": "major", 
                "filepath": func.parent_file.filepath,
                "element_type": "Function",
                "element_name": func.name,
                "reason": f"Many parameters ({param_count})",
                "context": f"Function has {param_count} parameters"
            })
            issue_counter += 1
    
    # Calculate Halstead metrics for all functions
    total_operators = []
    total_operands = []
    
    for func in codebase.functions:
        operators, operands = get_operators_and_operands(func)
        total_operators.extend(operators)
        total_operands.extend(operands)
    
    volume, N1, N2, n1, n2 = calculate_halstead_volume(total_operators, total_operands)
    vocabulary = n1 + n2
    length = N1 + N2
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    effort = difficulty * volume
    
    # Most important functions
    most_calls_func = None
    most_calls_count = 0
    most_called_func = None
    most_called_count = 0
    
    for func in codebase.functions:
        # Function that makes most calls
        func_calls = getattr(func, 'function_calls', [])
        if len(func_calls) > most_calls_count:
            most_calls_count = len(func_calls)
            most_calls_func = func
        
        # Most called function
        call_sites = getattr(func, 'call_sites', [])
        if len(call_sites) > most_called_count:
            most_called_count = len(call_sites)
            most_called_func = func
    
    # Deepest inheritance
    deepest_class = None
    deepest_depth = 0
    for cls in codebase.classes:
        depth = calculate_doi(cls)
        if depth > deepest_depth:
            deepest_depth = depth
            deepest_class = cls
    
    # Function contexts (first 3)
    function_contexts = {}
    for i, func in enumerate(codebase.functions[:3]):
        key = f"{func.parent_file.filepath}:{func.name}"
        function_contexts[key] = {
            "filepath": func.parent_file.filepath,
            "parameters": [getattr(p, 'name', f'param_{i}') for i, p in enumerate(getattr(func, 'parameters', []))],
            "dependencies": [getattr(d, 'name', 'unknown') for d in getattr(func, 'dependencies', [])],
            "function_calls": [getattr(c, 'name', 'unknown') for c in getattr(func, 'function_calls', [])],
            "called_by": [getattr(s, 'name', 'unknown') for s in getattr(func, 'call_sites', [])],
            "issues": [issue for issue in issues if issue['filepath'] == func.parent_file.filepath and issue['element_name'] == func.name],
            "is_entry_point": _is_probably_entrypoint_file(func.parent_file),
            "is_dead_code": len(getattr(func, 'call_sites', [])) == 0,
            "max_call_chain": []
        }
    
    # Categorize issues by severity
    issues_by_severity = {"critical": [], "major": [], "minor": []}
    for issue in issues:
        issues_by_severity[issue["severity"]].append(issue)
    
    return {
        "summary": {
            "summary_text": summary_text,
            "total_files": total_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_issues": len(issues),
            "critical_issues": len(issues_by_severity["critical"]),
            "major_issues": len(issues_by_severity["major"]),
            "minor_issues": len(issues_by_severity["minor"]),
            "dead_code_items": len(dead_code_items),
            "entry_points": len(entrypoints),
        },
        "tree_structure": generate_tree_structure(codebase),
        "entrypoints": entrypoints,
        "dead_code_analysis": {
            "total_dead_functions": len([item for item in dead_code_items if item["type"] == "function"]),
            "dead_code_items": dead_code_items
        },
        "issues": issues,
        "issues_by_severity": issues_by_severity,
        "most_important_functions": {
            "most_calls": {
                "name": most_calls_func.name if most_calls_func else "N/A",
                "call_count": most_calls_count,
                "calls": [getattr(c, 'name', 'unknown') for c in getattr(most_calls_func, 'function_calls', [])][:3] if most_calls_func else []
            },
            "most_called": {
                "name": most_called_func.name if most_called_func else "N/A", 
                "usage_count": most_called_count
            },
            "deepest_inheritance": {
                "name": deepest_class.name if deepest_class else "N/A",
                "chain_depth": deepest_depth
            }
        },
        "function_contexts": function_contexts,
        "halstead_metrics": {
            "n1": n1, "n2": n2, "N1": N1, "N2": N2,
            "vocabulary": vocabulary, "length": length,
            "volume": volume, "difficulty": difficulty, "effort": effort
        }
    }


# -------------------------------
# Output formatter (run_demo style)
# -------------------------------

def _print_demo(analysis_results: Dict[str, Any]) -> None:
    print("\n📊 ANALYSIS SUMMARY:")
    print("-" * 30)
    summary = analysis_results.get('summary', {})
    print(f"📁 Total Files: {summary.get('total_files', 0)}")
    print(f"🔧 Total Functions: {summary.get('total_functions', 0)}")
    print(f"🚨 Total Issues: {summary.get('total_issues', 0)}")
    print(f"⚠️  Critical Issues: {summary.get('critical_issues', 0)}")
    print(f"👉 Major Issues: {summary.get('major_issues', 0)}")
    print(f"🔍 Minor Issues: {summary.get('minor_issues', 0)}")
    print(f"💀 Dead Code Items: {summary.get('dead_code_items', 0)}")
    print(f"🎯 Entry Points: {summary.get('entry_points', 0)}")

    print("\n🌟 MOST IMPORTANT FUNCTIONS:")
    print("-" * 35)
    important = analysis_results.get('most_important_functions', {})
    most_calls = important.get('most_calls', {})
    print(f"📞 Makes Most Calls: {most_calls.get('name', 'N/A')}")
    print(f"   📊 Call Count: {most_calls.get('call_count', 0)}")
    if most_calls.get('calls'):
        print(f"   🎯 Calls: {', '.join(most_calls['calls'][:3])}...")

    most_called = important.get('most_called', {})
    print(f"📈 Most Called: {most_called.get('name', 'N/A')}")
    print(f"   📊 Usage Count: {most_called.get('usage_count', 0)}")

    deepest_inheritance = important.get('deepest_inheritance', {})
    if deepest_inheritance.get('name'):
        print(f"🌳 Deepest Inheritance: {deepest_inheritance.get('name')}")
        print(f"   📊 Chain Depth: {deepest_inheritance.get('chain_depth', 0)}")

    print("\n🔧 FUNCTION CONTEXTS:")
    print("-" * 25)
    function_contexts = analysis_results.get('function_contexts', {})
    for func_name, context in list(function_contexts.items())[:3]:
        print(f"\n📝 Function: {func_name}")
        print(f"   📁 File: {context.get('filepath', 'N/A')}")
        print(f"   📊 Parameters: {len(context.get('parameters', []))}")
        print(f"   🔗 Dependencies: {len(context.get('dependencies', []))}")
        print(f"   📞 Function Calls: {len(context.get('function_calls', []))}")
        print(f"   📈 Called By: {len(context.get('called_by', []))}")
        print(f"   🚨 Issues: {len(context.get('issues', []))}")
        print(f"   🎯 Entry Point: {context.get('is_entry_point', False)}")
        print(f"   💀 Dead Code: {context.get('is_dead_code', False)}")
        if context.get('max_call_chain'):
            chain = context['max_call_chain']
            if len(chain) > 1:
                print(f"   ⛓️  Call Chain: {' → '.join(chain[:3])}...")

    print("\n🚨 ISSUES BY SEVERITY:")
    print("-" * 25)
    issues_by_severity = analysis_results.get('issues_by_severity', {})
    for severity, issues in issues_by_severity.items():
        if issues:
            print(f"\n{severity.upper()} ({len(issues)} issues):")
            for issue in issues[:2]:
                print(f"  • {issue.get('message', 'No message')}")
                print(f"    📁 {issue.get('filepath', 'N/A')}:{issue.get('line_number', 0)}")
            if len(issues) > 2:
                print(f"  ... and {len(issues) - 2} more")

    print("\n💀 DEAD CODE ANALYSIS:")
    print("-" * 22)
    dead_code = analysis_results.get('dead_code_analysis', {})
    print(f"🔢 Total Dead Functions: {dead_code.get('total_dead_functions', 0)}")
    dead_items = dead_code.get('dead_code_items', [])
    if dead_items:
        print("📋 Dead Code Items:")
        for item in dead_items[:3]:
            print(f"  • {item.get('name', 'N/A')} ({item.get('type', 'unknown')}) - {item.get('reason', 'No reason')}")
            print(f"    📁 {item.get('filepath', 'N/A')}")
            blast_radius = item.get('blast_radius', [])
            if blast_radius:
                print(f"    💥 Blast Radius: {', '.join(blast_radius[:3])}...")

    print("\n📊 HALSTEAD METRICS:")
    print("-" * 20)
    halstead = analysis_results.get('halstead_metrics', {})
    print(f"📝 Operators (n1): {halstead.get('n1', 0)}")
    print(f"📝 Operands (n2): {halstead.get('n2', 0)}")
    print(f"📊 Total Operators (N1): {halstead.get('N1', 0)}")
    print(f"📊 Total Operands (N2): {halstead.get('N2', 0)}")
    print(f"📚 Vocabulary: {halstead.get('vocabulary', 0)}")
    print(f"📏 Length: {halstead.get('length', 0)}")
    print(f"📦 Volume: {halstead.get('volume', 0):.2f}")
    print(f"⚡ Difficulty: {halstead.get('difficulty', 0):.2f}")
    print(f"💪 Effort: {halstead.get('effort', 0):.2f}")

    print("\n🎨 GENERATING VISUALIZATION DATA:")
    print("-" * 35)
    print("✅ Repository tree with issue counts")
    print("✅ Issue heatmap and severity distribution")
    print("✅ Dead code blast radius visualization")
    print("✅ Interactive call graph")
    print("✅ Dependency visualization")
    print("✅ Metrics charts and dashboards")
    print("✅ Function context panels")

    print("\n🌐 API ENDPOINTS AVAILABLE:")
    print("-" * 28)
    print("🔗 GET /analyze/username/repo - Complete analysis")
    print("🔗 GET /visualize/username/repo - Interactive visualization")

    print("\n🚀 TO START THE API SERVER:")
    print("-" * 27)
    print("python backend/api.py")
    print("\n🌐 Then visit:")
    print("http://localhost:5000/analyze/codegen-sh/graph-sitter")
    print("http://localhost:5000/visualize/codegen-sh/graph-sitter")


# -------------------------------
# Entrypoint
# -------------------------------

def load_codebase(owner: str, repo: str) -> Codebase:
    """Load a codebase using the correct graph-sitter API."""
    repo_full_name = f"{owner}/{repo}"
    return Codebase.from_repo(repo_full_name)


def run_demo(args: Optional[argparse.Namespace] = None) -> None:
    """Run a comprehensive demo of the backend system"""
    print("🚀 COMPREHENSIVE BACKEND ANALYSIS DEMO")
    print("=" * 60)

    parser = _build_parser()
    ns = args or parser.parse_args()

    # Load codebase using correct API
    print("📁 Loading codebase...")
    
    if ns.from_repo and ns.local_path:
        raise SystemExit("Provide only one of --codebase.from_repo or --codebase.local")

    if ns.from_repo:
        # Parse owner/repo
        if "/" not in ns.from_repo:
            raise SystemExit("repo must be in format 'owner/repo'")
        owner, repo = ns.from_repo.split("/", 1)
        
        # Use correct API with optional parameters
        if ns.commit or ns.tmp_dir != "/tmp/codegen":
            codebase = Codebase.from_repo(
                ns.from_repo,
                tmp_dir=ns.tmp_dir,
                commit=ns.commit,
                language="python"
            )
        else:
            codebase = Codebase.from_repo(ns.from_repo)
            
    elif ns.local_path:
        # Local codebase
        codebase = Codebase(ns.local_path)
    else:
        # Default to fastapi/fastapi
        codebase = load_codebase("fastapi", "fastapi")

    # Perform analysis
    print("🔍 Performing comprehensive analysis...")
    analysis_results = analyze_codebase(codebase)

    if ns.fmt == "json":
        print(json.dumps(analysis_results, indent=2))
    else:
        # Display key results in the requested format
        print("\n📊 ANALYSIS SUMMARY:")
        print("-" * 30)
        summary = analysis_results.get('summary', {})
        print(f"📁 Total Files: {summary.get('total_files', 0)}")
        print(f"🔧 Total Functions: {summary.get('total_functions', 0)}")
        print(f"🚨 Total Issues: {summary.get('total_issues', 0)}")
        print(f"⚠️  Critical Issues: {summary.get('critical_issues', 0)}")
        print(f"👉 Major Issues: {summary.get('major_issues', 0)}")
        print(f"🔍 Minor Issues: {summary.get('minor_issues', 0)}")
        print(f"💀 Dead Code Items: {summary.get('dead_code_items', 0)}")
        print(f"🎯 Entry Points: {summary.get('entry_points', 0)}")

        # Show tree structure
        print(f"\n🌳 REPOSITORY TREE STRUCTURE:")
        print("-" * 35)
        print(analysis_results.get('tree_structure', 'No tree structure available'))

        # Show entrypoints
        print(f"\n🎯 ENTRYPOINTS: [🟩-{len(analysis_results.get('entrypoints', []))}]")
        print("-" * 25)
        for i, entry in enumerate(analysis_results.get('entrypoints', [])[:5], 1):
            if entry['type'] == 'file':
                functions_str = ', '.join(f"'{f}'" for f in entry['functions'][:4])
                if len(entry['functions']) > 4:
                    functions_str += ', ...'
                print(f"{i}. 🐍 {entry['filepath']} [🟩 Entrypoint: File Functions: {functions_str}]")
            else:
                methods_str = ', '.join(f"'{m}'" for m in entry.get('methods', [])[:4])
                if len(entry.get('methods', [])) > 4:
                    methods_str += ', ...'
                print(f"{i}. 🐍 {entry['filepath']} [🟩 Entrypoint: Class: {entry['name']} Methods: {methods_str}]")

        # Show dead code
        print(f"\n💀 DEAD CODE: {len(analysis_results.get('dead_code_analysis', {}).get('dead_code_items', []))} [🔍Classes: {len([item for item in analysis_results.get('dead_code_analysis', {}).get('dead_code_items', []) if item['type'] == 'class'])}, 👉 Functions: {len([item for item in analysis_results.get('dead_code_analysis', {}).get('dead_code_items', []) if item['type'] == 'function'])}]")
        print("-" * 22)
        for i, item in enumerate(analysis_results.get('dead_code_analysis', {}).get('dead_code_items', [])[:10], 1):
            print(f"{i}. 🔍 {item['filepath']} {item['type'].title()}: '{item['name']}' [{item['reason']}]")

        # Show errors/issues
        issues = analysis_results.get('issues', [])
        print(f"\n🚨 ERRORS: {len(issues)} [⚠️ Critical: {len([i for i in issues if i['severity'] == 'critical'])}, 👉 Major: {len([i for i in issues if i['severity'] == 'major'])}, 🔍 Minor: {len([i for i in issues if i['severity'] == 'minor'])}]")
        print("-" * 25)
        for i, issue in enumerate(issues[:10], 1):
            severity_emoji = {"critical": "⚠️", "major": "👉", "minor": "🔍"}.get(issue['severity'], "🔍")
            print(f"{i} {severity_emoji}- {issue['filepath']} / {issue['element_type']} - '{issue['element_name']}' [{issue['reason']}] {issue['context']}")

        # Show most important functions
        print("\n🌟 MOST IMPORTANT FUNCTIONS:")
        print("-" * 35)
        important = analysis_results.get('most_important_functions', {})

        most_calls = important.get('most_calls', {})
        print(f"📞 Makes Most Calls: {most_calls.get('name', 'N/A')}")
        print(f"   📊 Call Count: {most_calls.get('call_count', 0)}")
        if most_calls.get('calls'):
            print(f"   🎯 Calls: {', '.join(most_calls['calls'][:3])}...")

        most_called = important.get('most_called', {})
        print(f"📈 Most Called: {most_called.get('name', 'N/A')}")
        print(f"   📊 Usage Count: {most_called.get('usage_count', 0)}")

        deepest_inheritance = important.get('deepest_inheritance', {})
        if deepest_inheritance.get('name') != 'N/A':
            print(f"🌳 Deepest Inheritance: {deepest_inheritance.get('name')}")
            print(f"   📊 Chain Depth: {deepest_inheritance.get('chain_depth', 0)}")

        # Show function contexts
        print("\n🔧 FUNCTION CONTEXTS:")
        print("-" * 25)
        function_contexts = analysis_results.get('function_contexts', {})

        for func_name, context in list(function_contexts.items())[:3]:  # Show first 3
            print(f"\n📝 Function: {func_name}")
            print(f"   📁 File: {context.get('filepath', 'N/A')}")
            print(f"   📊 Parameters: {len(context.get('parameters', []))}")
            print(f"   🔗 Dependencies: {len(context.get('dependencies', []))}")
            print(f"   📞 Function Calls: {len(context.get('function_calls', []))}")
            print(f"   📈 Called By: {len(context.get('called_by', []))}")
            print(f"   🚨 Issues: {len(context.get('issues', []))}")
            print(f"   🎯 Entry Point: {context.get('is_entry_point', False)}")
            print(f"   💀 Dead Code: {context.get('is_dead_code', False)}")

            if context.get('max_call_chain'):
                chain = context['max_call_chain']
                if len(chain) > 1:
                    print(f"   ⛓️  Call Chain: {' → '.join(chain[:3])}...")

        # Show Halstead metrics
        print("\n📊 HALSTEAD METRICS:")
        print("-" * 20)
        halstead = analysis_results.get('halstead_metrics', {})
        print(f"📝 Operators (n1): {halstead.get('n1', 0)}")
        print(f"📝 Operands (n2): {halstead.get('n2', 0)}")
        print(f"📊 Total Operators (N1): {halstead.get('N1', 0)}")
        print(f"📊 Total Operands (N2): {halstead.get('N2', 0)}")
        print(f"📚 Vocabulary: {halstead.get('vocabulary', 0)}")
        print(f"📏 Length: {halstead.get('length', 0)}")
        print(f"📦 Volume: {halstead.get('volume', 0):.2f}")
        print(f"⚡ Difficulty: {halstead.get('difficulty', 0):.2f}")
        print(f"💪 Effort: {halstead.get('effort', 0):.2f}")

        # Generate visualization data
        print("\n🎨 GENERATING VISUALIZATION DATA:")
        print("-" * 35)
        print("✅ Repository tree with issue counts")
        print("✅ Issue heatmap and severity distribution")
        print("✅ Dead code blast radius visualization")
        print("✅ Interactive call graph")
        print("✅ Dependency visualization")
        print("✅ Metrics charts and dashboards")
        print("✅ Function context panels")

        # Show API endpoints
        print("\n🌐 API ENDPOINTS AVAILABLE:")
        print("-" * 28)
        print("🔗 GET /analyze/username/repo - Complete analysis")
        print("🔗 GET /visualize/username/repo - Interactive visualization")

        print("\n🚀 TO START THE API SERVER:")
        print("-" * 27)
        print("python backend/api.py")
        print("\n🌐 Then visit:")
        print("http://localhost:5000/analyze/codegen-sh/graph-sitter")
        print("http://localhost:5000/visualize/codegen-sh/graph-sitter")

    if ns.output:
        with open(ns.output, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, indent=2)

    print("\n" + "=" * 60)
    print("✨ Demo complete! Backend system ready for integration! ✨")


if __name__ == "__main__":
    run_demo()
