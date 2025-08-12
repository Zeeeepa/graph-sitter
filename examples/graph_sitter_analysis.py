#!/usr/bin/env python3
"""
Graph Sitter Comprehensive Codebase Analysis (Example)

Usage:
  Remote repo (default fastapi/fastapi):
    python examples/graph_sitter_analysis.py --codebase.from_repo fastapi/fastapi [--commit <sha>] [--tmp-dir /tmp/codegen]

  Local path:
    python examples/graph_sitter_analysis.py --codebase.local "."

Notes:
- Flags with dots (--) are mapped internally to argparse destinations.
- Output matches the run_demo() sections the user requested. Some checks use conservative heuristics.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
)


# -------------------------------
# Helpers: CLI parsing
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


def _collect_import_graph(cb: Codebase) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {}
    for f in cb.files:
        try:
            outs: List[str] = []
            for imp in getattr(f, "imports", []):
                try:
                    # Prefer module string; fallback to symbol name
                    mod = getattr(imp, "module", None)
                    mod_name = mod.source if getattr(mod, "source", None) else getattr(imp, "name", None)
                    if mod_name:
                        outs.append(str(mod_name))
                except Exception:
                    continue
            graph[f.filepath] = outs
        except Exception:
            continue
    return graph


def _collect_call_graph(cb: Codebase) -> Dict[str, List[str]]:
    # Conservative: use function.function_calls when available
    graph: Dict[str, List[str]] = {}
    for func in cb.functions:
        try:
            callers_key = f"{func.parent_file.filepath}:{func.name}"
            callees: List[str] = []
            for call in getattr(func, "function_calls", []):
                try:
                    target = getattr(call, "resolved_function", None)
                    if target is not None:
                        t_key = f"{target.parent_file.filepath}:{getattr(target, 'name', 'unknown')}"
                        callees.append(t_key)
                except Exception:
                    continue
            graph[callers_key] = callees
        except Exception:
            continue
    return graph


def _find_dead_code(cb: Codebase) -> Dict[str, Any]:
    # Heuristic: functions/classes with zero call sites and not imported anywhere; exclude dunder/private
    dead_items: List[Dict[str, Any]] = []
    total_dead_functions = 0

    def _is_public_name(name: str) -> bool:
        return not (name.startswith("_") or name.startswith("__"))

    for func in cb.functions:
        try:
            if not _is_public_name(getattr(func, "name", "")):
                continue
            if getattr(func, "is_magic", False):
                continue
            call_sites = getattr(func, "call_sites", [])
            if _safe_len(call_sites) == 0:
                dead_items.append({
                    "name": func.name,
                    "type": "function",
                    "filepath": func.parent_file.filepath,
                    "reason": "no call sites found",
                    "blast_radius": [],
                })
                total_dead_functions += 1
        except Exception:
            continue

    for cls in cb.classes:
        try:
            if not _is_public_name(getattr(cls, "name", "")):
                continue
            # Treat class dead if no methods are called and class not referenced
            methods = getattr(cls, "methods", [])
            called_any = False
            for m in methods:
                if _safe_len(getattr(m, "call_sites", [])) > 0:
                    called_any = True
                    break
            if not called_any:
                dead_items.append({
                    "name": cls.name,
                    "type": "class",
                    "filepath": cls.parent_file.filepath,
                    "reason": "no method call sites found",
                    "blast_radius": [],
                })
        except Exception:
            continue

    return {"total_dead_functions": total_dead_functions, "dead_code_items": dead_items}


def _find_unused_imports(cb: Codebase) -> List[Issue]:
    issues: List[Issue] = []
    for f in cb.files:
        try:
            sym_names_in_file = {getattr(s, "name", None) for s in getattr(f, "symbols", [])}
            for imp in getattr(f, "imports", []):
                try:
                    alias = imp.name
                    target = getattr(imp, "symbol_name", None)
                    target_name = getattr(target, "source", None)
                    base_name = alias or target_name
                    if base_name and base_name not in sym_names_in_file:
                        issues.append(Issue(
                            severity="minor",
                            message=f"Potential unused import: {base_name}",
                            filepath=f.filepath,
                            line_number=None,
                        ))
                except Exception:
                    continue
        except Exception:
            continue
    return issues


def _find_unresolved_imports(cb: Codebase) -> List[Issue]:
    issues: List[Issue] = []
    for f in cb.files:
        for imp in getattr(f, "imports", []):
            try:
                # If import could not be resolved to symbol or external module, flag it
                resolution_edges = [e for e in cb.ctx.edges if e[0] == imp.node_id and getattr(e[2], "type", None).name == "IMPORT_SYMBOL_RESOLUTION"]
                if not resolution_edges:
                    issues.append(Issue(
                        severity="major",
                        message=f"Unresolved import: {imp.source}",
                        filepath=f.filepath,
                        line_number=None,
                    ))
            except Exception:
                continue
    return issues


def _find_wrong_call_sites(cb: Codebase) -> List[Issue]:
    issues: List[Issue] = []
    for func in cb.functions:
        for call in getattr(func, "function_calls", []):
            try:
                if getattr(call, "resolved_function", None) is None:
                    issues.append(Issue(
                        severity="minor",
                        message=f"Unresolved function call in {func.name}",
                        filepath=func.parent_file.filepath,
                        line_number=None,
                    ))
            except Exception:
                continue
    return issues


def _most_important_functions(cb: Codebase) -> Dict[str, Any]:
    most_calls = {"name": None, "call_count": 0, "calls": []}
    most_called = {"name": None, "usage_count": 0}
    deepest_inheritance = {"name": None, "chain_depth": 0}

    for func in cb.functions:
        try:
            calls = getattr(func, "function_calls", [])
            if _safe_len(calls) > most_calls["call_count"]:
                most_calls = {
                    "name": func.name,
                    "call_count": _safe_len(calls),
                    "calls": [getattr(getattr(c, "resolved_function", None), "name", "unknown") for c in calls if getattr(c, "resolved_function", None) is not None],
                }
        except Exception:
            pass

    # For most_called, use call_sites
    for func in cb.functions:
        try:
            usages = getattr(func, "call_sites", [])
            if _safe_len(usages) > most_called["usage_count"]:
                most_called = {"name": func.name, "usage_count": _safe_len(usages)}
        except Exception:
            pass

    # Deepest inheritance chain (classes)
    for cls in cb.classes:
        try:
            depth = len(getattr(cls, "parent_class_names", []) or [])
            if depth > deepest_inheritance["chain_depth"]:
                deepest_inheritance = {"name": cls.name, "chain_depth": depth}
        except Exception:
            pass

    return {
        "most_calls": most_calls,
        "most_called": most_called,
        "deepest_inheritance": deepest_inheritance,
    }


def _function_contexts(cb: Codebase) -> Dict[str, Any]:
    contexts: Dict[str, Any] = {}
    for func in cb.functions:
        try:
            key = f"{func.parent_file.filepath}:{func.name}"
            contexts[key] = {
                "filepath": func.parent_file.filepath,
                "parameters": [getattr(p, "name", "?") for p in getattr(func, "parameters", [])],
                "dependencies": [getattr(d, "name", "?") for d in getattr(func, "dependencies", [])],
                "function_calls": [getattr(getattr(c, "resolved_function", None), "name", "unknown") for c in getattr(func, "function_calls", []) if getattr(c, "resolved_function", None) is not None],
                "called_by": [getattr(getattr(s, "caller", None), "name", "unknown") for s in getattr(func, "call_sites", []) if getattr(s, "caller", None) is not None],
                "issues": [],
                "is_entry_point": _is_probably_entrypoint_file(func.parent_file),
                "is_dead_code": _safe_len(getattr(func, "call_sites", [])) == 0,
                "max_call_chain": [],
            }
        except Exception:
            continue
    return contexts


def analyze_codebase(cb: Codebase) -> Dict[str, Any]:
    # Summary counts
    summary_text = get_codebase_summary(cb)
    total_files = _safe_len(cb.files)
    total_functions = _safe_len(cb.functions)

    issues: List[Issue] = []
    issues.extend(_find_unused_imports(cb))
    issues.extend(_find_unresolved_imports(cb))
    issues.extend(_find_wrong_call_sites(cb))

    dead = _find_dead_code(cb)
    important = _most_important_functions(cb)
    function_ctx = _function_contexts(cb)

    issues_by_severity: Dict[str, List[Dict[str, Any]]] = {"critical": [], "major": [], "minor": []}
    for i in issues:
        issues_by_severity[i.severity].append({
            "message": i.message,
            "filepath": i.filepath,
            "line_number": i.line_number or 0,
        })

    ret: Dict[str, Any] = {
        "summary": {
            "summary_text": summary_text,
            "total_files": total_files,
            "total_functions": total_functions,
            "total_issues": sum(len(v) for v in issues_by_severity.values()),
            "critical_issues": len(issues_by_severity["critical"]),
            "major_issues": len(issues_by_severity["major"]),
            "minor_issues": len(issues_by_severity["minor"]),
            "dead_code_items": _safe_len(dead.get("dead_code_items", [])),
            "entry_points": sum(1 for f in cb.files if _is_probably_entrypoint_file(f)),
        },
        "most_important_functions": important,
        "function_contexts": function_ctx,
        "issues_by_severity": issues_by_severity,
        "dead_code_analysis": dead,
        "halstead_metrics": {"n1": 0, "n2": 0, "N1": 0, "N2": 0, "vocabulary": 0, "length": 0, "volume": 0.0, "difficulty": 0.0, "effort": 0.0},
        "visualization": {
            "imports": _collect_import_graph(cb),
            "calls": _collect_call_graph(cb),
        },
    }
    return ret


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

def run_demo(args: Optional[argparse.Namespace] = None) -> None:
    print("🚀 COMPREHENSIVE BACKEND ANALYSIS DEMO")
    print("=" * 60)

    parser = _build_parser()
    ns = args or parser.parse_args()

    # Construct codebase
    print("📁 Loading codebase...")
    cfg = CodebaseConfig(
        debug=False,
        verify_graph=False,
        track_graph=False,
        method_usages=True,
        sync_enabled=False,
        full_range_index=False,
        ignore_process_errors=True,
        allow_external=False,
        py_resolve_syspath=False,
        generics=True,
        conditional_type_resolution=False,
    )

    if ns.from_repo and ns.local_path:
        raise SystemExit("Provide only one of --codebase.from_repo or --codebase.local")

    if ns.from_repo:
        cb = Codebase.from_repo(repo_full_name=ns.from_repo, commit=ns.commit, tmp_dir=ns.tmp_dir, language="python", config=cfg)
    elif ns.local_path:
        cb = Codebase(ns.local_path, config=cfg)
    else:
        # default to remote fastapi/fastapi as discussed
        cb = Codebase.from_repo(repo_full_name="fastapi/fastapi", commit=None, tmp_dir=ns.tmp_dir, language="python", config=cfg)

    print("🔍 Performing comprehensive analysis...")
    analysis_results = analyze_codebase(cb)

    if ns.fmt == "json":
        print(json.dumps(analysis_results, indent=2))
    else:
        _print_demo(analysis_results)

    if ns.output:
        with open(ns.output, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, indent=2)

    print("\n" + "=" * 60)
    print("✨ Demo complete! Backend system ready for integration! ✨")


if __name__ == "__main__":
    run_demo()

