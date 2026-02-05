#!/usr/bin/env python3
"""
Test that consolidated modules can be imported (without full dependencies)
"""

import ast
import sys

print("=" * 80)
print("TESTING CONSOLIDATED FILE IMPORTS (AST-level)")
print("=" * 80)

# Test 1: Parse all consolidated files with AST
consolidated_files = [
    'src/lsp_adapter.py',
    'src/autogenlib_adapter.py',
    'src/codebase_analysis.py',
    'src/graph_sitter_tools_adapter.py'
]

print("\n1. AST PARSING TEST")
print("-" * 80)

all_passed = True

for filepath in consolidated_files:
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source, filepath)
        print(f"✅ {filepath}: Parses successfully")
        
        # Count key elements
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        print(f"   - {len(classes)} classes, {len(functions)} functions")
        
    except SyntaxError as e:
        print(f"❌ {filepath}: Syntax error - {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ {filepath}: Error - {e}")
        all_passed = False

# Test 2: Check for common import issues
print("\n2. IMPORT STATEMENT ANALYSIS")
print("-" * 80)

for filepath in consolidated_files:
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source, filepath)
        
        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Check for imports from deprecated files
        deprecated_imports = []
        deprecated_modules = ['lsp_diagnostics', 'graph_sitter_analysis', 'graph_sitter_backend']
        
        for imp in imports:
            if any(dep in imp for dep in deprecated_modules):
                deprecated_imports.append(imp)
        
        if deprecated_imports:
            print(f"⚠️  {filepath}:")
            for imp in deprecated_imports:
                print(f"   - Imports from deprecated: {imp}")
            all_passed = False
        else:
            print(f"✅ {filepath}: No deprecated imports")
            
    except Exception as e:
        print(f"❌ {filepath}: Could not analyze imports - {e}")
        all_passed = False

# Test 3: Check that deprecated files have warnings
print("\n3. DEPRECATION WARNING CHECK")
print("-" * 80)

deprecated_files = [
    'src/lsp_diagnostics.py',
    'src/graph_sitter_analysis.py',
    'src/graph_sitter_backend.py',
    'src/analysisbig.py'
]

for filepath in deprecated_files:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        if 'DEPRECATION' in content or 'DEPRECATED' in content:
            print(f"✅ {filepath}: Has deprecation warning")
        else:
            print(f"⚠️  {filepath}: Missing deprecation warning")
            
    except Exception as e:
        print(f"⚠️  {filepath}: Could not check - {e}")

# Final result
print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL CONSOLIDATION TESTS PASSED!")
    print("=" * 80)
    sys.exit(0)
else:
    print("⚠️  SOME TESTS FAILED - See details above")
    print("=" * 80)
    sys.exit(1)

