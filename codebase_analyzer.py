#!/usr/bin/env python3
"""
Practical Codebase Analyzer

This script demonstrates how to analyze your codebase for errors, issues, and parameters
using the graph_sitter_ext extension.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Any

def find_python_files(directory: str) -> List[str]:
    """Find all Python files in a directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_file_syntax(file_path: str) -> Dict[str, Any]:
    """Analyze a Python file for syntax errors and basic issues."""
    issues = {
        'syntax_errors': [],
        'import_issues': [],
        'todo_comments': [],
        'long_functions': [],
        'complex_functions': [],
        'unused_imports': [],
        'missing_docstrings': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for syntax errors
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            issues['syntax_errors'].append({
                'line': e.lineno,
                'message': str(e),
                'text': e.text.strip() if e.text else ''
            })
            return issues  # Can't analyze further if syntax is broken
        
        # Check for import issues
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Old import patterns that might be problematic
            if 'from graph_sitter.configs import' in line:
                issues['import_issues'].append({
                    'line': i,
                    'issue': 'Old import path detected',
                    'text': line.strip()
                })
            
            # TODO/FIXME comments
            if 'TODO' in line or 'FIXME' in line or 'XXX' in line:
                issues['todo_comments'].append({
                    'line': i,
                    'text': line.strip()
                })
        
        # Analyze AST for more complex issues
        for node in ast.walk(tree):
            # Check for functions without docstrings
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    issues['missing_docstrings'].append({
                        'function': node.name,
                        'line': node.lineno
                    })
                
                # Check for long functions (>50 lines)
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        issues['long_functions'].append({
                            'function': node.name,
                            'line': node.lineno,
                            'length': func_length
                        })
                
                # Simple complexity check (count if/for/while statements)
                complexity = 1  # Base complexity
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                        complexity += 1
                
                if complexity > 10:
                    issues['complex_functions'].append({
                        'function': node.name,
                        'line': node.lineno,
                        'complexity': complexity
                    })
    
    except Exception as e:
        issues['syntax_errors'].append({
            'line': 0,
            'message': f'File read error: {str(e)}',
            'text': ''
        })
    
    return issues

def analyze_codebase(directory: str) -> Dict[str, Any]:
    """Analyze entire codebase for issues."""
    print(f"🔍 Analyzing codebase in: {directory}")
    print("=" * 60)
    
    python_files = find_python_files(directory)
    print(f"Found {len(python_files)} Python files")
    print()
    
    all_issues = {
        'total_files': len(python_files),
        'files_with_issues': 0,
        'total_issues': 0,
        'by_category': {
            'syntax_errors': 0,
            'import_issues': 0,
            'todo_comments': 0,
            'long_functions': 0,
            'complex_functions': 0,
            'missing_docstrings': 0
        },
        'detailed_issues': {}
    }
    
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, directory)
        issues = analyze_file_syntax(file_path)
        
        # Count issues
        file_issue_count = sum(len(issue_list) for issue_list in issues.values())
        if file_issue_count > 0:
            all_issues['files_with_issues'] += 1
            all_issues['total_issues'] += file_issue_count
            all_issues['detailed_issues'][rel_path] = issues
            
            # Update category counts
            for category, issue_list in issues.items():
                all_issues['by_category'][category] += len(issue_list)
    
    return all_issues

def print_analysis_results(results: Dict[str, Any]):
    """Print analysis results in a readable format."""
    print("📊 ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"Total files analyzed: {results['total_files']}")
    print(f"Files with issues: {results['files_with_issues']}")
    print(f"Total issues found: {results['total_issues']}")
    print()
    
    print("📋 ISSUES BY CATEGORY")
    print("-" * 30)
    for category, count in results['by_category'].items():
        if count > 0:
            emoji = {
                'syntax_errors': '❌',
                'import_issues': '🔗',
                'todo_comments': '📝',
                'long_functions': '📏',
                'complex_functions': '🧠',
                'missing_docstrings': '📚'
            }.get(category, '⚠️')
            print(f"{emoji} {category.replace('_', ' ').title()}: {count}")
    
    if results['total_issues'] == 0:
        print("✅ No issues found! Your codebase looks clean.")
        return
    
    print()
    print("🔍 DETAILED ISSUES BY FILE")
    print("-" * 40)
    
    for file_path, issues in results['detailed_issues'].items():
        print(f"\n📄 {file_path}")
        
        for category, issue_list in issues.items():
            if issue_list:
                category_name = category.replace('_', ' ').title()
                print(f"  {category_name}:")
                
                for issue in issue_list[:3]:  # Show first 3 issues per category
                    if 'line' in issue:
                        print(f"    Line {issue['line']}: {issue.get('message', issue.get('text', str(issue)))}")
                    else:
                        print(f"    {issue}")
                
                if len(issue_list) > 3:
                    print(f"    ... and {len(issue_list) - 3} more")

def main():
    """Main analysis function."""
    print("🚀 CODEBASE ANALYZER")
    print("=" * 60)
    print("This tool analyzes your codebase for:")
    print("• Syntax errors")
    print("• Import issues") 
    print("• TODO/FIXME comments")
    print("• Long functions (>50 lines)")
    print("• Complex functions (>10 complexity)")
    print("• Missing docstrings")
    print()
    
    # Analyze current directory by default
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    try:
        results = analyze_codebase(directory)
        print_analysis_results(results)
        
        print()
        print("💡 RECOMMENDATIONS")
        print("-" * 20)
        
        if results['by_category']['syntax_errors'] > 0:
            print("• Fix syntax errors first - they prevent code execution")
        
        if results['by_category']['import_issues'] > 0:
            print("• Update old import paths to use correct graph_sitter paths")
        
        if results['by_category']['complex_functions'] > 0:
            print("• Consider breaking down complex functions into smaller ones")
        
        if results['by_category']['long_functions'] > 0:
            print("• Long functions are harder to maintain - consider refactoring")
        
        if results['by_category']['missing_docstrings'] > 0:
            print("• Add docstrings to improve code documentation")
        
        if results['total_issues'] == 0:
            print("🎉 Your codebase is in great shape!")
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
