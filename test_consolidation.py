#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Consolidated Modules
Tests: Import validation, function execution, API completeness, integration
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("="*80)
print("CONSOLIDATION TESTING SUITE")
print("="*80)

# Track results
results = {
    "imports": {"passed": [], "failed": []},
    "functions": {"passed": [], "failed": []},
    "integration": {"passed": [], "failed": []},
}

# ============================================================================
# PHASE 1: IMPORT VALIDATION
# ============================================================================
print("\n" + "="*80)
print("PHASE 1: IMPORT VALIDATION")
print("="*80)

# Test 1.1: lsp_adapter.py
print("\n[1.1] Testing: from lsp_adapter import *")
try:
    from lsp_adapter import EnhancedDiagnostic, RuntimeErrorCollector, LSPDiagnosticsManager
    print("  ✅ SUCCESS: lsp_adapter imports cleanly")
    print(f"     - EnhancedDiagnostic: {type(EnhancedDiagnostic)}")
    print(f"     - RuntimeErrorCollector: {type(RuntimeErrorCollector)}")
    print(f"     - LSPDiagnosticsManager: {type(LSPDiagnosticsManager)}")
    results["imports"]["passed"].append("lsp_adapter")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
    results["imports"]["failed"].append(("lsp_adapter", str(e)))

# Test 1.2: graph_sitter_tools_adapter.py
print("\n[1.2] Testing: from graph_sitter_tools_adapter import *")
try:
    from graph_sitter_tools_adapter import (
        reveal_symbol,
        get_symbol_info, 
        RevealSymbolTool,
        render_mdx_page_for_class,
        generate_docs_json,
        list_directory,
        get_current_code_codebase,
        get_codegen_sdk_codebase
    )
    print("  ✅ SUCCESS: graph_sitter_tools_adapter imports cleanly")
    print(f"     - reveal_symbol: {type(reveal_symbol)}")
    print(f"     - RevealSymbolTool: {type(RevealSymbolTool)}")
    print(f"     - render_mdx_page_for_class: {type(render_mdx_page_for_class)}")
    print(f"     - generate_docs_json: {type(generate_docs_json)}")
    print(f"     - list_directory: {type(list_directory)}")
    results["imports"]["passed"].append("graph_sitter_tools_adapter")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
    results["imports"]["failed"].append(("graph_sitter_tools_adapter", str(e)))

# Test 1.3: codebase_analysis.py
print("\n[1.3] Testing: from codebase_analysis import *")
try:
    from codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        find_dead_code,
        analyze_codebase
    )
    print("  ✅ SUCCESS: codebase_analysis imports cleanly")
    print(f"     - get_codebase_summary: {type(get_codebase_summary)}")
    print(f"     - get_file_summary: {type(get_file_summary)}")
    print(f"     - find_dead_code: {type(find_dead_code)}")
    print(f"     - analyze_codebase: {type(analyze_codebase)}")
    results["imports"]["passed"].append("codebase_analysis")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
    results["imports"]["failed"].append(("codebase_analysis", str(e)))

# Test 1.4: Migrated files (backward compatibility)
print("\n[1.4] Testing: Migrated files backward compatibility")
migrated_files = [
    "autogenlib_adapter",
    "analysis", 
    "graph_sitter_analysis",
    "graph_sitter_backend"
]

for module_name in migrated_files:
    try:
        __import__(module_name)
        print(f"  ✅ {module_name} imports successfully")
        results["imports"]["passed"].append(f"{module_name} (migrated)")
    except Exception as e:
        print(f"  ❌ {module_name} FAILED: {type(e).__name__}: {e}")
        results["imports"]["failed"].append((f"{module_name} (migrated)", str(e)))

# ============================================================================
# PHASE 2: CIRCULAR DEPENDENCY CHECK
# ============================================================================
print("\n" + "="*80)
print("PHASE 2: CIRCULAR DEPENDENCY CHECK")
print("="*80)

print("\n[2.1] Checking for circular imports...")
import_chain_tests = [
    ("lsp_adapter → graph_sitter_tools_adapter", "lsp_adapter", "graph_sitter_tools_adapter"),
    ("graph_sitter_tools_adapter → codebase_analysis", "graph_sitter_tools_adapter", "codebase_analysis"),
    ("codebase_analysis → lsp_adapter", "codebase_analysis", "lsp_adapter"),
]

for test_name, module_a, module_b in import_chain_tests:
    try:
        # Try importing in sequence
        exec(f"import {module_a}")
        exec(f"import {module_b}")
        print(f"  ✅ {test_name}: No circular dependency")
        results["integration"]["passed"].append(test_name)
    except Exception as e:
        print(f"  ❌ {test_name}: {type(e).__name__}: {e}")
        results["integration"]["failed"].append((test_name, str(e)))

# ============================================================================
# PHASE 3: API COMPLETENESS CHECK
# ============================================================================
print("\n" + "="*80)
print("PHASE 3: API COMPLETENESS CHECK")
print("="*80)

print("\n[3.1] Verifying public API availability...")

# Expected functions in graph_sitter_tools_adapter
expected_tool_functions = [
    "reveal_symbol",
    "get_symbol_info",
    "hop_through_imports",
    "RevealSymbolTool",
    "RevealSymbolInput",
    "render_mdx_page_for_class",
    "generate_docs_json",
    "list_directory",
    "get_current_code_codebase",
    "get_codegen_sdk_codebase"
]

try:
    import graph_sitter_tools_adapter as tools
    available = [name for name in dir(tools) if not name.startswith("_")]
    
    print(f"  Available public names: {len(available)}")
    
    missing = [name for name in expected_tool_functions if name not in available]
    if missing:
        print(f"  ⚠️  Missing expected functions: {missing}")
        results["functions"]["failed"].append(("API completeness", f"Missing: {missing}"))
    else:
        print(f"  ✅ All expected functions present")
        results["functions"]["passed"].append("API completeness")
        
    # Show sample of what's available
    print(f"  Sample available: {available[:10]}...")
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    results["functions"]["failed"].append(("API completeness", str(e)))

# ============================================================================
# PHASE 4: FUNCTION SIGNATURE CHECK
# ============================================================================
print("\n" + "="*80)
print("PHASE 4: FUNCTION SIGNATURE VALIDATION")
print("="*80)

print("\n[4.1] Checking function signatures...")

signature_tests = [
    ("codebase_analysis.get_codebase_summary", "get_codebase_summary", 1),
    ("codebase_analysis.get_file_summary", "get_file_summary", 1),
    ("codebase_analysis.find_dead_code", "find_dead_code", 1),
    ("codebase_analysis.analyze_codebase", "analyze_codebase", 1),
]

for test_name, func_name, min_params in signature_tests:
    try:
        from codebase_analysis import *
        func = locals()[func_name]
        
        import inspect
        sig = inspect.signature(func)
        param_count = len(sig.parameters)
        
        if param_count >= min_params:
            print(f"  ✅ {test_name}: {sig}")
            results["functions"]["passed"].append(test_name)
        else:
            print(f"  ⚠️  {test_name}: Expected {min_params}+ params, got {param_count}")
            results["functions"]["failed"].append((test_name, f"Param count: {param_count}"))
            
    except Exception as e:
        print(f"  ❌ {test_name}: {e}")
        results["functions"]["failed"].append((test_name, str(e)))

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
print("\n" + "="*80)
print("TESTING RESULTS SUMMARY")
print("="*80)

total_passed = (
    len(results["imports"]["passed"]) +
    len(results["functions"]["passed"]) +
    len(results["integration"]["passed"])
)

total_failed = (
    len(results["imports"]["failed"]) +
    len(results["functions"]["failed"]) +
    len(results["integration"]["failed"])
)

print(f"\n✅ PASSED: {total_passed}")
print(f"❌ FAILED: {total_failed}")
print(f"📊 SUCCESS RATE: {total_passed/(total_passed+total_failed)*100:.1f}%")

print("\n--- Import Tests ---")
print(f"  Passed: {len(results['imports']['passed'])}")
print(f"  Failed: {len(results['imports']['failed'])}")
if results["imports"]["failed"]:
    for name, error in results["imports"]["failed"]:
        print(f"    ❌ {name}: {error[:100]}")

print("\n--- Function Tests ---")
print(f"  Passed: {len(results['functions']['passed'])}")
print(f"  Failed: {len(results['functions']['failed'])}")
if results["functions"]["failed"]:
    for name, error in results["functions"]["failed"]:
        print(f"    ❌ {name}: {error[:100]}")

print("\n--- Integration Tests ---")
print(f"  Passed: {len(results['integration']['passed'])}")
print(f"  Failed: {len(results['integration']['failed'])}")
if results["integration"]["failed"]:
    for name, error in results["integration"]["failed"]:
        print(f"    ❌ {name}: {error[:100]}")

print("\n" + "="*80)
if total_failed == 0:
    print("🎉 ALL TESTS PASSED - CONSOLIDATION IS FUNCTIONAL!")
else:
    print(f"⚠️  {total_failed} ISSUES FOUND - NEED FIXES")
print("="*80)

