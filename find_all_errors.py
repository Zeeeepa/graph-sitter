#!/usr/bin/env python3
"""
🔍 FIND ALL CODE ERRORS SCRIPT 🔍

This script finds all code errors, their locations, and descriptions
in your codebase using the super comprehensive analysis system.
"""

import sys
import os
import ast
import traceback
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def find_syntax_errors(directory="."):
    """Find all Python syntax errors in the codebase."""
    errors = []
    
    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content, filename=str(py_file))
            
        except SyntaxError as e:
            errors.append({
                'file': str(py_file),
                'line': e.lineno,
                'column': e.offset,
                'error': str(e),
                'type': 'SyntaxError'
            })
        except Exception as e:
            errors.append({
                'file': str(py_file),
                'line': 1,
                'column': 1,
                'error': str(e),
                'type': 'ParseError'
            })
    
    return errors

def find_import_errors(directory="."):
    """Find all import errors in the codebase."""
    errors = []
    
    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse and check imports
            tree = ast.parse(content, filename=str(py_file))
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Try to simulate the import
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            try:
                                __import__(alias.name)
                            except ImportError as e:
                                errors.append({
                                    'file': str(py_file),
                                    'line': node.lineno,
                                    'column': node.col_offset,
                                    'error': f"ImportError: {e}",
                                    'type': 'ImportError',
                                    'module': alias.name
                                })
                            except Exception:
                                pass  # Skip other import issues for now
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            try:
                                __import__(node.module)
                            except ImportError as e:
                                errors.append({
                                    'file': str(py_file),
                                    'line': node.lineno,
                                    'column': node.col_offset,
                                    'error': f"ImportError: {e}",
                                    'type': 'ImportError',
                                    'module': node.module
                                })
                            except Exception:
                                pass
                                
        except Exception:
            pass  # Skip files we can't parse
    
    return errors

def find_undefined_variables(directory="."):
    """Find potential undefined variables."""
    errors = []
    
    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(py_file))
            
            # Simple undefined variable detection
            defined_names = set()
            used_names = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        defined_names.add(node.id)
                    elif isinstance(node.ctx, ast.Load):
                        used_names.add((node.id, node.lineno, node.col_offset))
            
            # Check for undefined variables (basic check)
            builtins = {'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'open', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr'}
            
            for name, line, col in used_names:
                if name not in defined_names and name not in builtins and not name.startswith('_'):
                    errors.append({
                        'file': str(py_file),
                        'line': line,
                        'column': col,
                        'error': f"Potentially undefined variable: '{name}'",
                        'type': 'UndefinedVariable',
                        'variable': name
                    })
                    
        except Exception:
            pass
    
    return errors

def run_comprehensive_analysis():
    """Run the super comprehensive analysis if available."""
    try:
        from src.graph_sitter.adapters.code_analysis import analyze_codebase
        
        print("🚀 Running Super Comprehensive Analysis...")
        result = analyze_codebase(".")
        
        print(f"\n📊 COMPREHENSIVE ANALYSIS RESULTS:")
        print(f"📁 Files analyzed: {result.total_files}")
        print(f"🔧 Functions found: {result.total_functions}")
        print(f"📦 Classes found: {result.total_classes}")
        print(f"📝 Lines of code: {result.total_lines}")
        print(f"🔄 Import loops: {result.import_loops}")
        print(f"💀 Dead code items: {result.dead_code_items}")
        print(f"🔒 Security issues: {result.security_issues}")
        print(f"⚡ Performance issues: {result.performance_issues}")
        print(f"🏆 Quality score: {result.quality_score}/10")
        
        if result.interactive_url:
            print(f"🌐 Interactive exploration: {result.interactive_url}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ Comprehensive analysis not available: {e}")
        return None

def main():
    """Main error finding function."""
    print("🔍 FINDING ALL CODE ERRORS IN CODEBASE")
    print("=" * 50)
    
    # 1. Run comprehensive analysis first
    comprehensive_result = run_comprehensive_analysis()
    
    print("\n🔍 DETAILED ERROR ANALYSIS:")
    print("=" * 50)
    
    # 2. Find syntax errors
    print("\n📝 SYNTAX ERRORS:")
    syntax_errors = find_syntax_errors()
    if syntax_errors:
        for error in syntax_errors:
            print(f"❌ {error['file']}:{error['line']}:{error['column']} - {error['error']}")
    else:
        print("✅ No syntax errors found!")
    
    # 3. Find import errors
    print(f"\n📦 IMPORT ERRORS:")
    import_errors = find_import_errors()
    if import_errors:
        for error in import_errors:
            print(f"❌ {error['file']}:{error['line']} - {error['error']}")
    else:
        print("✅ No critical import errors found!")
    
    # 4. Find undefined variables
    print(f"\n🔍 POTENTIAL UNDEFINED VARIABLES:")
    undefined_vars = find_undefined_variables()
    if undefined_vars:
        # Group by file for better readability
        by_file = {}
        for error in undefined_vars:
            file = error['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(error)
        
        for file, errors in by_file.items():
            print(f"\n📁 {file}:")
            for error in errors:
                print(f"  ⚠️  Line {error['line']}: {error['error']}")
    else:
        print("✅ No obvious undefined variables found!")
    
    # 5. Summary
    print(f"\n📊 ERROR SUMMARY:")
    print("=" * 50)
    print(f"📝 Syntax errors: {len(syntax_errors)}")
    print(f"📦 Import errors: {len(import_errors)}")
    print(f"🔍 Potential undefined variables: {len(undefined_vars)}")
    
    if comprehensive_result:
        print(f"🔄 Import loops: {comprehensive_result.import_loops}")
        print(f"💀 Dead code items: {comprehensive_result.dead_code_items}")
        print(f"🔒 Security issues: {comprehensive_result.security_issues}")
        print(f"⚡ Performance issues: {comprehensive_result.performance_issues}")
    
    total_issues = len(syntax_errors) + len(import_errors) + len(undefined_vars)
    if comprehensive_result:
        total_issues += comprehensive_result.import_loops + comprehensive_result.dead_code_items + comprehensive_result.security_issues + comprehensive_result.performance_issues
    
    print(f"\n🎯 TOTAL ISSUES FOUND: {total_issues}")
    
    if total_issues == 0:
        print("🎉 Congratulations! No major issues found in your codebase!")
    else:
        print("🔧 Review the issues above to improve your code quality.")
    
    if comprehensive_result and comprehensive_result.interactive_url:
        print(f"\n🌐 For detailed interactive analysis, visit: {comprehensive_result.interactive_url}")

if __name__ == "__main__":
    main()

