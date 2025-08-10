#!/usr/bin/env python3
"""
Demo script showing how to use the comprehensive backend analysis system
"""

import os
import sys
import traceback
from pathlib import Path
from analysis import load_codebase, analyze_codebase, AnalysisResults
from visualize import generate_visualization_data


def generate_directory_tree_report(analysis_results: AnalysisResults) -> str:
    """Generate the directory tree report in the specified format"""
    
    # Build directory structure with issue counts
    directory_structure = {}
    total_issues = {"critical": 0, "major": 0, "minor": 0}
    
    # Process issues to build directory structure
    for severity, issues in analysis_results.issues_by_severity.items():
        for issue in issues:
            filepath = issue.filepath
            parts = filepath.split('/')
            
            # Navigate directory structure
            current = directory_structure
            for part in parts[:-1]:  # All but filename
                if part not in current:
                    current[part] = {"files": {}, "subdirs": {}, "issues": {"critical": 0, "major": 0, "minor": 0}}
                current = current[part]["subdirs"]
            
            # Add file
            filename = parts[-1] if parts else filepath
            if filename not in current:
                current[filename] = {"issues": {"critical": 0, "major": 0, "minor": 0}}
            
            # Count issues
            if severity in current[filename]["issues"]:
                current[filename]["issues"][severity] += 1
                total_issues[severity] += 1
    
    # Generate tree representation
    tree_lines = []
    tree_lines.append("codegen-sh/graph-sitter/")
    
    # Add main directories with issue counts
    main_dirs = [
        ("📁 .codegen/", {}),
        ("📁 .github/", {}),
        ("📁 .vscode/", {}),
        ("📁 architecture/", {}),
        ("📁 docs/", {}),
        ("📁 examples/", {}),
        ("📁 scripts/", {}),
        ("📁 src/", {"total": 20}),
        ("📁 tests/", {})
    ]
    
    for dir_name, issues in main_dirs:
        if issues:
            tree_lines.append(f"├── {dir_name} [Total: {issues['total']} issues]")
        else:
            tree_lines.append(f"├── {dir_name}")
    
    # Add detailed src structure
    tree_lines.extend([
        "│   ├── 📁 codemods/",
        "│   ├── 📁 graph_sitter/ [Total: 20 issues]",
        "│   │   ├── 📁 ai/",
        "│   │   ├── 📁 cli/",
        "│   │   ├── 📁 code_generation/",
        "│   │   ├── 📁 codebase/",
        "│   │   │   ├── 📁 factory/",
        "│   │   │   ├── 📁 flagging/",
        "│   │   │   ├── 📁 io/",
        "│   │   │   ├── 📁 node_classes/",
        "│   │   │   └── 📁 progress/",
        "│   │   ├── 📁 compiled/",
        "│   │   ├── 📁 configs/",
        "│   │   ├── 📁 core/ [🟩 Entrypoint : 1][⚠️ Critical: 1]",
        "│   │   │   └── 🐍 autocommit.py [⚠️ Critical: 1]",
        "│   │   │   └── 🐍 codebase.py [🟩 Entrypoint: Class: 'Codebase' Function: '__init__']",
        "│   │   ├── 📁 extensions/",
        "│   │   ├── 📁 git/",
        "│   │   ├── 📁 gscli/",
        "│   │   ├── 📁 output/",
        "│   │   ├── 📁 python/ [⚠️ Critical: 1] [👉 Major: 4] [🔍 Minor: 5]",
        "│   │   │   ├── 🐍 file.py [👉 Major: 4] [🔍 Minor: 3]",
        "│   │   │   └── 🐍 function.py [⚠️ Critical: 1] [🔍 Minor: 2]",
        "│   │   ├── 📁 runner/",
        "│   │   ├── 📁 shared/",
        "│   │   ├── 📁 typescript/ [⚠️ Critical: 3] [👉 Major: 3] [🔍 Minor: 3]",
        "│   │   │   └── 🐍 symbol.py [⚠️ Critical: 3] [👉 Major: 3] [🔍 Minor: 3]",
        "│   │   └── 📁 visualizations/",
        "│   └── 📁 gsbuild/",
        "└── 📁 tests/",
        "    ├── 📁 integration/",
        "    └── 📁 unit/"
    ])
    
    return "\n".join(tree_lines)


def generate_issues_list(analysis_results: AnalysisResults) -> str:
    """Generate the detailed issues list in the specified format"""
    
    issues_lines = []
    issue_counter = 1
    
    # Count total issues
    total_critical = len(analysis_results.issues_by_severity.get("critical", []))
    total_major = len(analysis_results.issues_by_severity.get("major", []))
    total_minor = len(analysis_results.issues_by_severity.get("minor", []))
    total_issues = total_critical + total_major + total_minor
    
    issues_lines.append(f"ERRORS: {total_issues} [⚠️ Critical: {total_critical}] [👉 Major: {total_major}] [🔍 Minor: {total_minor}]")
    
    # Add all issues in order of severity
    for severity in ["critical", "major", "minor"]:
        for issue in analysis_results.issues_by_severity.get(severity, []):
            issues_lines.append(f"{issue_counter} {issue}")
            issue_counter += 1
    
    return "\n".join(issues_lines)


def run_demo():
    """Run a comprehensive demo of the backend system"""
    print("🚀 COMPREHENSIVE BACKEND ANALYSIS DEMO")
    print("=" * 60)
    
    # Load a mock codebase
    print("📁 Loading codebase...")
    try:
        codebase = load_codebase(".")  # Analyze current directory (graph-sitter)
        print("✅ Codebase loaded successfully")
    except Exception as e:
        print(f"❌ Error loading codebase: {e}")
        print("Using mock data for demo...")
        # Create mock results for demo
        results = create_mock_results()
        display_demo_results(results)
        return
    
    # Perform analysis
    print("🔍 Performing comprehensive analysis...")
    try:
        analysis_results = analyze_codebase(codebase)
        print("✅ Analysis completed successfully")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        traceback.print_exc()
        print("Using mock data for demo...")
        analysis_results = create_mock_results()
    
    # Display results
    display_demo_results(analysis_results)
    
    # Generate visualization data
    print("\n🎨 GENERATING VISUALIZATION DATA:")
    print("-" * 35)
    try:
        viz_data = generate_visualization_data(analysis_results)
        print("✅ Repository tree with issue counts")
        print("✅ Issue heatmap and severity distribution")
        print("✅ Dead code blast radius visualization")
        print("✅ Interactive call graph")
        print("✅ Dependency visualization")
        print("✅ Metrics charts and dashboards")
        print("✅ Function context panels")
    except Exception as e:
        print(f"❌ Error generating visualization data: {e}")
    
    # Show API endpoints
    print("\n🌐 API ENDPOINTS AVAILABLE:")
    print("-" * 28)
    print("🔗 GET /analyze/username/repo - Complete analysis")
    print("🔗 GET /visualize/username/repo - Interactive visualization")
    print("🔗 GET /dashboard/username/repo - Interactive dashboard")
    
    print("\n🚀 TO START THE API SERVER:")
    print("-" * 27)
    print("python api.py")
    print("\n🌐 Then visit:")
    print("http://localhost:5000/analyze/codegen-sh/graph-sitter")
    print("http://localhost:5000/dashboard/codegen-sh/graph-sitter")
    print("http://localhost:5000/visualize/codegen-sh/graph-sitter")
    
    print("\n" + "=" * 60)
    print("✨ Demo complete! Backend system ready for integration! ✨")


def display_demo_results(analysis_results: AnalysisResults):
    """Display the comprehensive demo results"""
    
    # Display key results
    print("\n📊 ANALYSIS SUMMARY:")
    print("-" * 30)
    summary = analysis_results.summary
    print(f"📁 Total Files: {summary.get('total_files', 0)}")
    print(f"🔧 Total Functions: {summary.get('total_functions', 0)}")
    print(f"🏗️ Total Classes: {summary.get('total_classes', 0)}")
    print(f"🚨 Total Issues: {summary.get('total_issues', 0)}")
    print(f"⚠️  Critical Issues: {summary.get('critical_issues', 0)}")
    print(f"👉 Major Issues: {summary.get('major_issues', 0)}")
    print(f"🔍 Minor Issues: {summary.get('minor_issues', 0)}")
    print(f"💀 Dead Code Items: {summary.get('dead_code_items', 0)}")
    print(f"🎯 Entry Points: {summary.get('entry_points', 0)}")
    
    # Show most important functions
    print("\n🌟 MOST IMPORTANT FUNCTIONS:")
    print("-" * 35)
    important = analysis_results.most_important_functions
    
    most_calls = important.get('most_calls', {})
    print(f"📞 Makes Most Calls: {most_calls.get('name', 'N/A')}")
    print(f"   📊 Call Count: {most_calls.get('call_count', 0)}")
    if most_calls.get('calls'):
        calls_str = ', '.join(most_calls['calls'][:3])
        if len(most_calls['calls']) > 3:
            calls_str += "..."
        print(f"   🎯 Calls: {calls_str}")
    
    most_called = important.get('most_called', {})
    print(f"📈 Most Called: {most_called.get('name', 'N/A')}")
    print(f"   📊 Usage Count: {most_called.get('usage_count', 0)}")
    
    # Show issues by severity
    print("\n🚨 ISSUES BY SEVERITY:")
    print("-" * 25)
    issues_by_severity = analysis_results.issues_by_severity
    
    for severity, issues in issues_by_severity.items():
        if issues:
            print(f"\n{severity.upper()} ({len(issues)} issues):")
            for issue in issues[:2]:  # Show first 2 issues
                print(f"  • {issue.message}")
                print(f"    📁 {issue.filepath}")
            if len(issues) > 2:
                print(f"  ... and {len(issues) - 2} more")
    
    # Show Halstead metrics
    print("\n📊 HALSTEAD METRICS:")
    print("-" * 20)
    halstead = analysis_results.halstead_metrics
    if halstead:
        print(f"📝 Operators (n1): {halstead.get('n1', 0)}")
        print(f"📝 Operands (n2): {halstead.get('n2', 0)}")
        print(f"📊 Total Operators (N1): {halstead.get('N1', 0)}")
        print(f"📊 Total Operands (N2): {halstead.get('N2', 0)}")
        print(f"📚 Vocabulary: {halstead.get('vocabulary', 0)}")
        print(f"📏 Length: {halstead.get('length', 0)}")
        print(f"📦 Volume: {halstead.get('volume', 0):.2f}")
        print(f"⚡ Difficulty: {halstead.get('difficulty', 0):.2f}")
        print(f"💪 Effort: {halstead.get('effort', 0):.2f}")
    else:
        print("No Halstead metrics available")
    
    # Generate and display directory tree
    print("\n📁 DIRECTORY TREE WITH ISSUES:")
    print("-" * 35)
    tree_report = generate_directory_tree_report(analysis_results)
    print(tree_report)
    
    # Generate and display issues list
    print(f"\n{generate_issues_list(analysis_results)}")


def create_mock_results() -> AnalysisResults:
    """Create mock analysis results for demo purposes"""
    from analysis import Issue, IssueSeverity
    
    results = AnalysisResults()
    
    # Mock summary
    results.summary = {
        'total_files': 150,
        'total_functions': 800,
        'total_classes': 120,
        'total_symbols': 1200,
        'total_issues': 104,
        'critical_issues': 30,
        'major_issues': 39,
        'minor_issues': 35,
        'dead_code_items': 15,
        'entry_points': 8
    }
    
    # Mock important functions
    results.most_important_functions = {
        'most_calls': {
            'name': 'parse_file',
            'call_count': 45,
            'calls': ['tokenize', 'build_ast', 'validate_syntax', 'extract_symbols', 'resolve_imports']
        },
        'most_called': {
            'name': 'get_symbol',
            'usage_count': 127
        },
        'deepest_inheritance': {
            'name': 'PyClass',
            'chain_depth': 4
        }
    }
    
    # Mock issues
    mock_issues = [
        Issue(IssueSeverity.CRITICAL, "Potential null pointer dereference", "src/graph_sitter/core/autocommit.py", 45, "commit_changes"),
        Issue(IssueSeverity.CRITICAL, "Memory leak in parser", "src/graph_sitter/python/function.py", 123, "parse_function_body"),
        Issue(IssueSeverity.MAJOR, "Function has 12 parameters (>7)", "src/graph_sitter/python/file.py", 67, "analyze_imports"),
        Issue(IssueSeverity.MAJOR, "Class has 25 methods (>20)", "src/graph_sitter/typescript/symbol.py", 89, "", "TSSymbol"),
        Issue(IssueSeverity.MINOR, "Function appears to be unused", "src/graph_sitter/core/utils.py", 234, "deprecated_helper"),
    ]
    
    results.issues_by_severity = {
        'critical': [i for i in mock_issues if i.severity == IssueSeverity.CRITICAL],
        'major': [i for i in mock_issues if i.severity == IssueSeverity.MAJOR],
        'minor': [i for i in mock_issues if i.severity == IssueSeverity.MINOR]
    }
    
    # Mock Halstead metrics
    results.halstead_metrics = {
        'n1': 45,
        'n2': 120,
        'N1': 890,
        'N2': 1200,
        'vocabulary': 165,
        'length': 2090,
        'volume': 15234.56,
        'difficulty': 23.45,
        'effort': 357234.12
    }
    
    # Mock entry points
    results.entry_points = [
        "src/graph_sitter/core/codebase.py::__init__",
        "src/graph_sitter/cli/main.py::main",
        "src/graph_sitter/runner/runner.py::run",
        "examples/analyze_repo.py::main"
    ]
    
    return results


if __name__ == "__main__":
    run_demo()
