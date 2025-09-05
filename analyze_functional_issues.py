#!/usr/bin/env python3
"""
Analyze functional issues in the graph_sitter codebase - check for broken imports, 
syntax errors, and distinguish between truly broken code vs. legitimately unused code.
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_python_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Parse error: {e}"

def check_imports(file_path: Path) -> Tuple[List[str], List[str]]:
    """Check imports in a file and return broken vs working imports."""
    broken_imports = []
    working_imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        importlib.import_module(alias.name)
                        working_imports.append(alias.name)
                    except ImportError:
                        broken_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        importlib.import_module(node.module)
                        working_imports.append(node.module)
                    except ImportError:
                        broken_imports.append(node.module)
    except Exception as e:
        broken_imports.append(f"Error parsing {file_path}: {e}")
    
    return broken_imports, working_imports

def categorize_unused_functions() -> Dict[str, List[str]]:
    """Categorize unused functions by their likely purpose."""
    
    # Get unused functions from our previous analysis
    try:
        from graph_sitter.core.codebase import Codebase
        from graph_sitter.core.function import Function
        
        graph_sitter_path = Path(__file__).parent / "src" / "graph_sitter"
        codebase = Codebase(str(graph_sitter_path), language="python")
        
        unused_functions = []
        for func in codebase.functions:
            if isinstance(func, Function):
                usages = func.symbol_usages
                if len(usages) == 0:
                    unused_functions.append((func.name, func.file.name))
        
        categories = {
            'cli_commands': [],
            'test_utilities': [],
            'api_endpoints': [],
            'tool_implementations': [],
            'utility_functions': [],
            'analysis_functions': [],
            'authentication': [],
            'file_operations': [],
            'git_operations': [],
            'formatting': [],
            'validation': [],
            'potentially_broken': []
        }
        
        # Categorize based on function names and file locations
        for func_name, file_name in unused_functions:
            if any(keyword in func_name.lower() for keyword in ['command', 'cmd']):
                categories['cli_commands'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['test', 'mock', 'stub']):
                categories['test_utilities'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['health', 'serve', 'api', 'endpoint']):
                categories['api_endpoints'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['tool', 'create_pr', 'linear', 'github']):
                categories['tool_implementations'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['get_', 'format_', 'parse_', 'extract_']):
                categories['utility_functions'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['analyze', 'summary', 'codebase']):
                categories['analysis_functions'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['login', 'auth', 'token']):
                categories['authentication'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['file', 'create_', 'delete_', 'edit_']):
                categories['file_operations'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['git', 'repo', 'clone', 'commit']):
                categories['git_operations'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['format', 'pretty', 'style']):
                categories['formatting'].append(f"{func_name} ({file_name})")
            elif any(keyword in func_name.lower() for keyword in ['validate', 'check']):
                categories['validation'].append(f"{func_name} ({file_name})")
            else:
                categories['potentially_broken'].append(f"{func_name} ({file_name})")
        
        return categories
        
    except Exception as e:
        print(f"Error categorizing functions: {e}")
        return {}

def analyze_file_health(graph_sitter_path: Path) -> Dict[str, any]:
    """Analyze overall health of Python files in the codebase."""
    
    results = {
        'total_files': 0,
        'syntax_errors': [],
        'import_issues': [],
        'healthy_files': 0,
        'broken_imports_by_file': {},
        'common_broken_imports': {}
    }
    
    python_files = list(graph_sitter_path.rglob("*.py"))
    results['total_files'] = len(python_files)
    
    all_broken_imports = []
    
    for py_file in python_files:
        # Check syntax
        is_valid, error = check_python_syntax(py_file)
        if not is_valid:
            results['syntax_errors'].append(f"{py_file.relative_to(graph_sitter_path)}: {error}")
            continue
        
        # Check imports
        broken_imports, working_imports = check_imports(py_file)
        if broken_imports:
            results['broken_imports_by_file'][str(py_file.relative_to(graph_sitter_path))] = broken_imports
            all_broken_imports.extend(broken_imports)
        else:
            results['healthy_files'] += 1
    
    # Count common broken imports
    from collections import Counter
    import_counter = Counter(all_broken_imports)
    results['common_broken_imports'] = dict(import_counter.most_common(10))
    
    return results

def main():
    print("🔍 Analyzing functional issues in graph_sitter codebase...")
    
    graph_sitter_path = Path(__file__).parent / "src" / "graph_sitter"
    
    print("\n" + "="*80)
    print("📁 FILE HEALTH ANALYSIS")
    print("="*80)
    
    health_results = analyze_file_health(graph_sitter_path)
    
    print(f"Total Python files: {health_results['total_files']}")
    print(f"Files with syntax errors: {len(health_results['syntax_errors'])}")
    print(f"Files with import issues: {len(health_results['broken_imports_by_file'])}")
    print(f"Healthy files: {health_results['healthy_files']}")
    
    if health_results['syntax_errors']:
        print(f"\n🔴 SYNTAX ERRORS:")
        for error in health_results['syntax_errors']:
            print(f"  - {error}")
    
    if health_results['broken_imports_by_file']:
        print(f"\n🔴 IMPORT ISSUES BY FILE:")
        for file_path, broken_imports in health_results['broken_imports_by_file'].items():
            print(f"  📁 {file_path}:")
            for imp in broken_imports:
                print(f"    - {imp}")
    
    if health_results['common_broken_imports']:
        print(f"\n🔴 MOST COMMON BROKEN IMPORTS:")
        for imp, count in health_results['common_broken_imports'].items():
            print(f"  - {imp} (appears in {count} files)")
    
    print("\n" + "="*80)
    print("📊 UNUSED FUNCTION CATEGORIZATION")
    print("="*80)
    
    categories = categorize_unused_functions()
    
    for category, functions in categories.items():
        if functions:
            category_name = category.replace('_', ' ').title()
            print(f"\n📋 {category_name} ({len(functions)} functions):")
            for func in functions[:10]:  # Show first 10
                print(f"  - {func}")
            if len(functions) > 10:
                print(f"  ... and {len(functions) - 10} more")
    
    # Summary assessment
    print("\n" + "="*80)
    print("🎯 FUNCTIONAL ASSESSMENT")
    print("="*80)
    
    total_issues = len(health_results['syntax_errors']) + len(health_results['broken_imports_by_file'])
    health_percentage = (health_results['healthy_files'] / health_results['total_files']) * 100
    
    print(f"Overall codebase health: {health_percentage:.1f}%")
    print(f"Files with functional issues: {total_issues}")
    
    if total_issues == 0:
        print("✅ No syntax errors or import issues found!")
        print("✅ All 'unused' functions appear to be legitimately unused (CLI, tools, utilities)")
    else:
        print(f"⚠️  Found {total_issues} files with potential functional issues")
        print("🔧 These should be investigated and fixed")
    
    print(f"\n💡 Recommendation:")
    if total_issues == 0:
        print("   The codebase appears functionally healthy. 'Unused' functions are likely:")
        print("   - CLI commands not called in analysis")
        print("   - Tool implementations used externally") 
        print("   - Utility functions for future use")
        print("   - API endpoints called by external systems")
    else:
        print("   Fix import issues and syntax errors before cleanup")
        print("   Focus on files with broken imports first")

if __name__ == "__main__":
    main()

