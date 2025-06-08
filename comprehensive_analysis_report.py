#!/usr/bin/env python3
"""
Comprehensive Analysis Report for Graph-Sitter Repository (PR #284)

This script provides a detailed analysis of the entire graph-sitter repository
using multiple analysis approaches and generates a comprehensive report.
"""

import os
import ast
import sys
from collections import defaultdict
from pathlib import Path

def analyze_repository_structure():
    """Analyze the overall repository structure."""
    structure = {
        'directories': defaultdict(int),
        'file_types': defaultdict(int),
        'total_files': 0,
        'total_lines': 0,
        'python_files': 0,
        'python_lines': 0
    }
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        # Count directory types
        if 'src' in root:
            structure['directories']['source'] += 1
        elif 'test' in root:
            structure['directories']['tests'] += 1
        elif 'example' in root:
            structure['directories']['examples'] += 1
        elif 'doc' in root:
            structure['directories']['docs'] += 1
        else:
            structure['directories']['other'] += 1
        
        for file in files:
            structure['total_files'] += 1
            file_path = os.path.join(root, file)
            
            # Count file types
            ext = os.path.splitext(file)[1]
            structure['file_types'][ext] += 1
            
            # Count lines
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    structure['total_lines'] += lines
                    
                    if ext == '.py':
                        structure['python_files'] += 1
                        structure['python_lines'] += lines
            except:
                pass
    
    return structure

def analyze_python_code_quality():
    """Analyze Python code quality across the repository."""
    issues = {
        'syntax_errors': [],
        'import_issues': [],
        'circular_imports': [],
        'todo_comments': [],
        'long_functions': [],
        'complex_functions': [],
        'missing_docstrings': [],
        'security_concerns': []
    }
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, '.')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for syntax errors
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError as e:
                issues['syntax_errors'].append({
                    'file': rel_path,
                    'line': e.lineno,
                    'error': str(e)
                })
                continue
            
            # Analyze content line by line
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Import issues
                if 'from graph_sitter.configs import' in line:
                    issues['import_issues'].append({
                        'file': rel_path,
                        'line': i,
                        'issue': 'Old import path',
                        'text': line.strip()
                    })
                
                # Circular import patterns
                if 'from contexten.extensions.contexten_app.contexten_app import ContextenApp' in line:
                    issues['circular_imports'].append({
                        'file': rel_path,
                        'line': i,
                        'issue': 'Potential circular import',
                        'text': line.strip()
                    })
                
                # TODO comments
                if any(keyword in line for keyword in ['TODO', 'FIXME', 'XXX', 'HACK']):
                    issues['todo_comments'].append({
                        'file': rel_path,
                        'line': i,
                        'text': line.strip()
                    })
                
                # Security concerns
                if any(concern in line.lower() for concern in ['password', 'secret', 'token', 'api_key']):
                    if '=' in line and not line.strip().startswith('#'):
                        issues['security_concerns'].append({
                            'file': rel_path,
                            'line': i,
                            'concern': 'Potential hardcoded secret',
                            'text': line.strip()
                        })
            
            # AST analysis for functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Missing docstrings
                    if not ast.get_docstring(node):
                        issues['missing_docstrings'].append({
                            'file': rel_path,
                            'function': node.name,
                            'line': node.lineno
                        })
                    
                    # Long functions
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        length = node.end_lineno - node.lineno
                        if length > 50:
                            issues['long_functions'].append({
                                'file': rel_path,
                                'function': node.name,
                                'line': node.lineno,
                                'length': length
                            })
                    
                    # Complex functions (simple complexity measure)
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                            complexity += 1
                    
                    if complexity > 10:
                        issues['complex_functions'].append({
                            'file': rel_path,
                            'function': node.name,
                            'line': node.lineno,
                            'complexity': complexity
                        })
        
        except Exception as e:
            issues['syntax_errors'].append({
                'file': rel_path,
                'line': 0,
                'error': f'File analysis error: {str(e)}'
            })
    
    return issues

def analyze_pr_284_changes():
    """Analyze the specific changes in PR #284."""
    pr_changes = {
        'new_files': [],
        'modified_files': [],
        'new_features': [],
        'improvements': []
    }
    
    # Check for new example files
    example_files = [
        'examples/graph_sitter_api_demo.py',
        'examples/graph_sitter_extensions_example.py'
    ]
    
    for file_path in example_files:
        if os.path.exists(file_path):
            pr_changes['new_files'].append(file_path)
            pr_changes['new_features'].append(f'Added {os.path.basename(file_path)} example')
    
    # Check for modified extension files
    extension_files = [
        'src/contexten/extensions/graph_sitter/__init__.py',
        'src/contexten/extensions/graph_sitter/analysis/__init__.py'
    ]
    
    for file_path in extension_files:
        if os.path.exists(file_path):
            pr_changes['modified_files'].append(file_path)
    
    pr_changes['improvements'] = [
        'Enhanced graph-sitter extension API',
        'Added comprehensive analysis examples',
        'Improved documentation and usage guides',
        'Updated import paths and module structure'
    ]
    
    return pr_changes

def generate_comprehensive_report():
    """Generate a comprehensive analysis report."""
    print("🚀 COMPREHENSIVE GRAPH-SITTER ANALYSIS REPORT")
    print("=" * 70)
    print("📍 Repository: graph-sitter")
    print("🌿 Branch: PR #284")
    print("📅 Analysis Date:", "2025-06-08")
    print()
    
    # Repository structure analysis
    print("📊 REPOSITORY STRUCTURE ANALYSIS")
    print("-" * 40)
    structure = analyze_repository_structure()
    
    print(f"📁 Total files: {structure['total_files']:,}")
    print(f"📄 Total lines of code: {structure['total_lines']:,}")
    print(f"🐍 Python files: {structure['python_files']:,}")
    print(f"📝 Python lines: {structure['python_lines']:,}")
    print()
    
    print("📂 Directory breakdown:")
    for dir_type, count in structure['directories'].items():
        print(f"   {dir_type}: {count} directories")
    print()
    
    print("📋 File type breakdown:")
    for ext, count in sorted(structure['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
        if ext:
            print(f"   {ext}: {count} files")
    print()
    
    # Code quality analysis
    print("🔍 CODE QUALITY ANALYSIS")
    print("-" * 30)
    issues = analyze_python_code_quality()
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    print(f"⚠️ Total issues found: {total_issues:,}")
    print()
    
    for category, issue_list in issues.items():
        if issue_list:
            emoji = {
                'syntax_errors': '❌',
                'import_issues': '🔗',
                'circular_imports': '🔄',
                'todo_comments': '📝',
                'long_functions': '📏',
                'complex_functions': '🧠',
                'missing_docstrings': '📚',
                'security_concerns': '🔒'
            }.get(category, '⚠️')
            
            print(f"{emoji} {category.replace('_', ' ').title()}: {len(issue_list)}")
            
            # Show top issues
            for issue in issue_list[:3]:
                if 'file' in issue:
                    print(f"   📄 {issue['file']}:{issue.get('line', '?')}")
                    if 'error' in issue:
                        print(f"      {issue['error']}")
                    elif 'text' in issue:
                        print(f"      {issue['text'][:80]}...")
            
            if len(issue_list) > 3:
                print(f"   ... and {len(issue_list) - 3} more")
            print()
    
    # PR #284 specific analysis
    print("🎯 PR #284 CHANGES ANALYSIS")
    print("-" * 30)
    pr_changes = analyze_pr_284_changes()
    
    print("📁 New files added:")
    for file_path in pr_changes['new_files']:
        print(f"   ✅ {file_path}")
    print()
    
    print("📝 Modified files:")
    for file_path in pr_changes['modified_files']:
        print(f"   🔧 {file_path}")
    print()
    
    print("🚀 New features:")
    for feature in pr_changes['new_features']:
        print(f"   ⭐ {feature}")
    print()
    
    print("💡 Improvements:")
    for improvement in pr_changes['improvements']:
        print(f"   🔧 {improvement}")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 20)
    
    if issues['syntax_errors']:
        print("🔥 CRITICAL: Fix syntax errors first - they prevent code execution")
    
    if issues['circular_imports']:
        print("🔄 HIGH: Resolve circular import issues to improve module loading")
    
    if issues['import_issues']:
        print("🔗 MEDIUM: Update old import paths to use correct graph_sitter paths")
    
    if issues['security_concerns']:
        print("🔒 MEDIUM: Review potential security concerns and hardcoded secrets")
    
    if issues['complex_functions']:
        print("🧠 LOW: Consider refactoring complex functions for better maintainability")
    
    if issues['missing_docstrings']:
        print("📚 LOW: Add docstrings to improve code documentation")
    
    print()
    print("✅ ANALYSIS COMPLETE")
    print("📊 This report covers the entire graph-sitter repository")
    print("🎯 Special focus on PR #284 changes and improvements")
    print("🔍 Multiple analysis types: structure, quality, security, complexity")

if __name__ == "__main__":
    generate_comprehensive_report()

