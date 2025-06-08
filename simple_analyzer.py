#!/usr/bin/env python3
"""
Simple Codebase Analyzer - Find errors and issues in your codebase
"""

import os
import ast
import sys

def analyze_codebase(directory):
    """Analyze codebase for common issues."""
    print(f"🔍 Analyzing codebase: {directory}")
    print("=" * 50)
    
    issues_found = {
        'syntax_errors': [],
        'import_issues': [],
        'todo_comments': [],
        'long_functions': [],
        'missing_docstrings': []
    }
    
    total_files = 0
    
    # Find all Python files
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                total_files += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for syntax errors
                    try:
                        ast.parse(content, filename=file_path)
                    except SyntaxError as e:
                        issues_found['syntax_errors'].append({
                            'file': rel_path,
                            'line': e.lineno,
                            'error': str(e)
                        })
                        continue  # Skip further analysis if syntax is broken
                    
                    # Check for import issues
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'from graph_sitter.configs import' in line:
                            issues_found['import_issues'].append({
                                'file': rel_path,
                                'line': i,
                                'issue': 'Old import path',
                                'text': line.strip()
                            })
                        
                        if any(keyword in line for keyword in ['TODO', 'FIXME', 'XXX']):
                            issues_found['todo_comments'].append({
                                'file': rel_path,
                                'line': i,
                                'text': line.strip()
                            })
                    
                    # Analyze AST for function issues
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                # Check for missing docstrings
                                if not ast.get_docstring(node):
                                    issues_found['missing_docstrings'].append({
                                        'file': rel_path,
                                        'function': node.name,
                                        'line': node.lineno
                                    })
                                
                                # Check for long functions
                                if hasattr(node, 'end_lineno') and node.end_lineno:
                                    length = node.end_lineno - node.lineno
                                    if length > 50:
                                        issues_found['long_functions'].append({
                                            'file': rel_path,
                                            'function': node.name,
                                            'line': node.lineno,
                                            'length': length
                                        })
                    except:
                        pass  # Skip AST analysis if it fails
                
                except Exception as e:
                    issues_found['syntax_errors'].append({
                        'file': rel_path,
                        'line': 0,
                        'error': f'File read error: {str(e)}'
                    })
    
    # Print results
    print(f"📊 Analyzed {total_files} Python files")
    print()
    
    total_issues = sum(len(issues) for issues in issues_found.values())
    
    if total_issues == 0:
        print("✅ No issues found! Your codebase looks clean.")
        return
    
    print(f"⚠️ Found {total_issues} issues:")
    print()
    
    # Syntax errors (most critical)
    if issues_found['syntax_errors']:
        print(f"❌ SYNTAX ERRORS ({len(issues_found['syntax_errors'])})")
        for issue in issues_found['syntax_errors'][:5]:
            print(f"  {issue['file']}:{issue['line']} - {issue['error']}")
        if len(issues_found['syntax_errors']) > 5:
            print(f"  ... and {len(issues_found['syntax_errors']) - 5} more")
        print()
    
    # Import issues
    if issues_found['import_issues']:
        print(f"🔗 IMPORT ISSUES ({len(issues_found['import_issues'])})")
        for issue in issues_found['import_issues'][:5]:
            print(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
            print(f"    {issue['text']}")
        if len(issues_found['import_issues']) > 5:
            print(f"  ... and {len(issues_found['import_issues']) - 5} more")
        print()
    
    # TODO comments
    if issues_found['todo_comments']:
        print(f"📝 TODO/FIXME COMMENTS ({len(issues_found['todo_comments'])})")
        for issue in issues_found['todo_comments'][:3]:
            print(f"  {issue['file']}:{issue['line']} - {issue['text']}")
        if len(issues_found['todo_comments']) > 3:
            print(f"  ... and {len(issues_found['todo_comments']) - 3} more")
        print()
    
    # Long functions
    if issues_found['long_functions']:
        print(f"📏 LONG FUNCTIONS ({len(issues_found['long_functions'])})")
        for issue in issues_found['long_functions'][:3]:
            print(f"  {issue['file']}:{issue['line']} - {issue['function']} ({issue['length']} lines)")
        if len(issues_found['long_functions']) > 3:
            print(f"  ... and {len(issues_found['long_functions']) - 3} more")
        print()
    
    # Missing docstrings
    if issues_found['missing_docstrings']:
        print(f"📚 MISSING DOCSTRINGS ({len(issues_found['missing_docstrings'])})")
        for issue in issues_found['missing_docstrings'][:3]:
            print(f"  {issue['file']}:{issue['line']} - {issue['function']}()")
        if len(issues_found['missing_docstrings']) > 3:
            print(f"  ... and {len(issues_found['missing_docstrings']) - 3} more")
        print()
    
    print("💡 RECOMMENDATIONS:")
    if issues_found['syntax_errors']:
        print("• Fix syntax errors first - they prevent code execution")
    if issues_found['import_issues']:
        print("• Update import paths to use correct graph_sitter paths")
    if issues_found['long_functions']:
        print("• Consider breaking down long functions for better maintainability")
    if issues_found['missing_docstrings']:
        print("• Add docstrings to improve code documentation")

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    analyze_codebase(directory)

