#!/usr/bin/env python3
"""
🚨 CRITICAL ERRORS ONLY 🚨

This script shows only the most critical errors that need immediate attention.
"""

import sys
import os
import ast
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def find_critical_syntax_errors():
    """Find critical syntax errors that prevent code from running."""
    critical_errors = []
    
    # Focus on main source files, not examples
    main_dirs = ["src/graph_sitter", "src/codegen", "src/contexten"]
    
    for main_dir in main_dirs:
        if not os.path.exists(main_dir):
            continue
            
        for py_file in Path(main_dir).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to parse the file
                ast.parse(content, filename=str(py_file))
                
            except SyntaxError as e:
                critical_errors.append({
                    'file': str(py_file),
                    'line': e.lineno,
                    'column': e.offset,
                    'error': str(e),
                    'type': 'SyntaxError',
                    'severity': 'CRITICAL'
                })
            except Exception as e:
                critical_errors.append({
                    'file': str(py_file),
                    'line': 1,
                    'column': 1,
                    'error': str(e),
                    'type': 'ParseError',
                    'severity': 'CRITICAL'
                })
    
    return critical_errors

def find_missing_core_dependencies():
    """Find missing dependencies that are critical for core functionality."""
    critical_missing = []
    
    # Core dependencies that should be available
    core_deps = {
        'graph_sitter': 'Core graph-sitter library',
        'tree_sitter': 'Tree-sitter parsing library', 
        'tree_sitter_python': 'Python language support',
        'tree_sitter_javascript': 'JavaScript language support',
        'tree_sitter_typescript': 'TypeScript language support',
        'networkx': 'Graph analysis library',
        'jinja2': 'Template engine for HTML generation'
    }
    
    for dep, description in core_deps.items():
        try:
            __import__(dep)
        except ImportError:
            critical_missing.append({
                'dependency': dep,
                'description': description,
                'severity': 'HIGH',
                'impact': 'Core functionality limited'
            })
    
    return critical_missing

def main():
    """Show only critical errors."""
    print("🚨 CRITICAL ERRORS ANALYSIS")
    print("=" * 50)
    
    # 1. Critical syntax errors
    print("\n💥 CRITICAL SYNTAX ERRORS (Must Fix First):")
    syntax_errors = find_critical_syntax_errors()
    if syntax_errors:
        for error in syntax_errors:
            print(f"🔥 {error['file']}:{error['line']}:{error['column']}")
            print(f"   Error: {error['error']}")
            print(f"   Severity: {error['severity']}")
            print()
    else:
        print("✅ No critical syntax errors in main source code!")
    
    # 2. Missing core dependencies
    print("\n📦 MISSING CORE DEPENDENCIES:")
    missing_deps = find_missing_core_dependencies()
    if missing_deps:
        print("To install missing dependencies, run:")
        print("```bash")
        for dep in missing_deps:
            if dep['dependency'] == 'graph_sitter':
                print("pip install graph-sitter")
            elif dep['dependency'].startswith('tree_sitter'):
                print(f"pip install {dep['dependency'].replace('_', '-')}")
            else:
                print(f"pip install {dep['dependency']}")
        print("```")
        print()
        
        for dep in missing_deps:
            print(f"❌ {dep['dependency']}: {dep['description']}")
            print(f"   Impact: {dep['impact']}")
    else:
        print("✅ All core dependencies available!")
    
    # 3. How to run analysis with dependencies
    print(f"\n🚀 HOW TO RUN FULL ANALYSIS:")
    print("=" * 50)
    print("1. Install dependencies:")
    print("   pip install graph-sitter tree-sitter-python tree-sitter-javascript")
    print("   pip install networkx jinja2")
    print()
    print("2. Run comprehensive analysis:")
    print("   python -c \"")
    print("   from src.graph_sitter.adapters.code_analysis import analyze_codebase")
    print("   result = analyze_codebase('.')") 
    print("   print(f'Quality Score: {result.quality_score}/10')")
    print("   print(f'Interactive URL: {result.interactive_url}')")
    print("   \"")
    print()
    print("3. Or run the example:")
    print("   python examples/simple_analysis_example.py")
    
    # 4. Summary
    total_critical = len(syntax_errors)
    total_missing = len(missing_deps)
    
    print(f"\n📊 CRITICAL ISSUES SUMMARY:")
    print("=" * 50)
    print(f"💥 Critical syntax errors: {total_critical}")
    print(f"📦 Missing core dependencies: {total_missing}")
    
    if total_critical == 0 and total_missing == 0:
        print("\n🎉 No critical issues! Your codebase is ready for analysis!")
    elif total_critical > 0:
        print(f"\n🔥 Fix {total_critical} syntax errors first, then install dependencies.")
    else:
        print(f"\n📦 Install {total_missing} missing dependencies to enable full analysis.")

if __name__ == "__main__":
    main()

