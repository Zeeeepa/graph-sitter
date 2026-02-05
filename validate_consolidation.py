#!/usr/bin/env python3
"""
Static validation of consolidation without needing compiled Cython modules
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("STATIC VALIDATION OF CONSOLIDATION")
print("=" * 80)

def analyze_python_file(filepath):
    """Parse Python file and extract key information"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filepath)
        
        classes = []
        functions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return {
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'lines': len(source.split('\n')),
            'compiles': True
        }
    except SyntaxError as e:
        return {
            'classes': [],
            'functions': [],
            'imports': [],
            'lines': 0,
            'compiles': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'classes': [],
            'functions': [],
            'imports': [],
            'lines': 0,
            'compiles': False,
            'error': str(e)
        }

print("\n1. VALIDATING CONSOLIDATED FILES")
print("-" * 80)

consolidated_files = {
    'src/lsp_adapter.py': 'LSP Adapter (from lsp_diagnostics.py)',
    'src/autogenlib_adapter.py': 'AutoGen Adapter',
    'src/codebase_analysis.py': 'Main Analysis (from graph_sitter_analysis.py)',
    'src/graph_sitter_tools_adapter.py': 'Tools Adapter (skeleton)'
}

results = {}

for filepath, description in consolidated_files.items():
    print(f"\n📄 {filepath}")
    print(f"   {description}")
    
    if os.path.exists(filepath):
        info = analyze_python_file(filepath)
        results[filepath] = info
        
        if info['compiles']:
            print(f"   ✅ Compiles successfully")
            print(f"   📊 {info['lines']} lines")
            print(f"   🏛️  {len(info['classes'])} classes: {', '.join(info['classes'][:5])}")
            print(f"   🔧 {len(info['functions'])} functions")
            print(f"   📦 {len(info['imports'])} imports")
        else:
            print(f"   ❌ Syntax error: {info.get('error', 'Unknown')}")
    else:
        print(f"   ❌ File not found")
        results[filepath] = {'compiles': False, 'error': 'File not found'}

print("\n\n2. CHECKING OLD FILES TO DEPRECATE")
print("-" * 80)

old_files = {
    'src/lsp_diagnostics.py': 'Original LSP diagnostics (consolidated into lsp_adapter.py)',
    'src/graph_sitter_analysis.py': 'Original analysis (consolidated into codebase_analysis.py)',
    'src/graph_sitter_backend.py': 'Backend models (to be merged)',
    'src/analysis.py': 'FastAPI server (different purpose)',
    'src/analysisbig.py': 'Broken experimental file'
}

for filepath, description in old_files.items():
    print(f"\n📄 {filepath}")
    print(f"   {description}")
    
    if os.path.exists(filepath):
        info = analyze_python_file(filepath)
        
        if info['compiles']:
            print(f"   ✅ Still compiles ({info['lines']} lines)")
            print(f"   Status: Can be deprecated after validation")
        else:
            print(f"   ❌ Has syntax errors: {info.get('error', 'Unknown')}")
            print(f"   Status: Already broken, safe to mark deprecated")
    else:
        print(f"   ℹ️  File not found (may have been removed)")

print("\n\n3. IMPORT DEPENDENCY ANALYSIS")
print("-" * 80)

print("\nChecking which consolidated files import from old files...")

import_issues = []

for new_file, info in results.items():
    if not info.get('compiles'):
        continue
    
    old_imports = []
    for imp in info.get('imports', []):
        # Check if importing from old files
        if 'lsp_diagnostics' in imp:
            old_imports.append(('lsp_diagnostics', 'Should use lsp_adapter'))
        if 'graph_sitter_analysis' in imp:
            old_imports.append(('graph_sitter_analysis', 'Should use codebase_analysis'))
        if 'graph_sitter_backend' in imp:
            old_imports.append(('graph_sitter_backend', 'Should be consolidated'))
    
    if old_imports:
        print(f"\n⚠️  {new_file}:")
        for old, suggestion in old_imports:
            print(f"   - Imports from '{old}': {suggestion}")
            import_issues.append((new_file, old))

if not import_issues:
    print("\n✅ No imports from old files detected in consolidated files!")

print("\n\n4. CONSOLIDATION SUMMARY")
print("-" * 80)

total_files = len(consolidated_files)
compiling_files = sum(1 for info in results.values() if info.get('compiles'))
total_classes = sum(len(info.get('classes', [])) for info in results.values() if info.get('compiles'))
total_functions = sum(len(info.get('functions', [])) for info in results.values() if info.get('compiles'))
total_lines = sum(info.get('lines', 0) for info in results.values() if info.get('compiles'))

print(f"""
📊 Consolidated Architecture Status:
   Total files: {total_files}
   Compiling: {compiling_files}/{total_files} ({'✅' if compiling_files == total_files else '⚠️'})
   
   Total classes: {total_classes}
   Total functions: {total_functions}
   Total lines: {total_lines:,}
   
   Import issues: {len(import_issues)} {'✅' if len(import_issues) == 0 else '⚠️'}
""")

print("\n5. NEXT STEPS RECOMMENDATION")
print("-" * 80)

if compiling_files == total_files and len(import_issues) == 0:
    print("""
✅ CONSOLIDATION IS STRUCTURALLY SOUND!

Next steps:
1. Fix any remaining import issues in other parts of codebase
2. Add deprecation warnings to old files  
3. Run integration tests
4. Remove old files after validation period
5. Update documentation
""")
else:
    print("""
⚠️  CONSOLIDATION NEEDS FIXES

Issues found:
""")
    if compiling_files < total_files:
        print(f"   - {total_files - compiling_files} file(s) have syntax errors")
    
    if import_issues:
        print(f"   - {len(import_issues)} import(s) need updating")
    
    print("""
Recommended actions:
1. Fix syntax errors in consolidated files
2. Update imports to use new consolidated modules
3. Re-run this validation
""")

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)

