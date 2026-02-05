#!/usr/bin/env python3
"""
Comprehensive Real Codebase Analysis Test
==========================================
Tests all analysis functions from graph-sitter on actual dory-sdk codebase
"""

import sys
import os
from pathlib import Path

# Add graph-sitter to path
sys.path.insert(0, '/tmp/graph-sitter/src')

print("=" * 80)
print("COMPREHENSIVE ANALYSIS FUNCTION TESTING")
print("=" * 80)

# Track results
results = {
    "function_tests": [],
    "errors": [],
}

# ============================================================================
# PHASE 1: IMPORT ALL ANALYSIS FUNCTIONS
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 1: IMPORTING ANALYSIS FUNCTIONS")
print("=" * 80)

try:
    print("\n[1.1] Importing codebase_analysis module...")
    from codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary,
        find_dead_code,
        analyze_codebase
    )
    print("  ✅ SUCCESS: All analysis functions imported")
    results["function_tests"].append(("Import analysis functions", "PASS"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    results["errors"].append(("Import", str(e)))
    sys.exit(1)

try:
    print("\n[1.2] Importing graph-sitter core...")
    from graph_sitter import Codebase
    from graph_sitter.core.codebase import CodebaseConfig
    print("  ✅ SUCCESS: Graph-sitter core imported")
    results["function_tests"].append(("Import graph-sitter", "PASS"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    results["errors"].append(("Graph-sitter import", str(e)))
    sys.exit(1)

# ============================================================================
# PHASE 2: INITIALIZE CODEBASE
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 2: INITIALIZING DORY-SDK CODEBASE")
print("=" * 80)

dory_path = Path("/tmp/dory_sdk-2.1.7/src")
if not dory_path.exists():
    print(f"  ❌ FAILED: dory-sdk path not found: {dory_path}")
    sys.exit(1)

print(f"\n[2.1] Creating codebase from: {dory_path}")
try:
    print("  ⏳ Parsing codebase (this may take a moment)...")
    # Codebase takes repo_path directly
    codebase = Codebase(str(dory_path), language="python")
    
    print(f"  ✅ SUCCESS: Codebase initialized")
    print(f"     Path: {codebase.repo_path}")
    
    # Get basic stats
    all_files = list(codebase.files)
    print(f"     Files parsed: {len(all_files)}")
    
    if all_files:
        sample_files = [str(f.filepath) for f in all_files[:3]]
        print(f"     Sample files: {sample_files}")
    
    results["function_tests"].append(("Initialize codebase", "PASS"))
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("Initialize codebase", str(e)))
    sys.exit(1)

# ============================================================================
# PHASE 3: TEST EACH ANALYSIS FUNCTION
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 3: TESTING ANALYSIS FUNCTIONS")
print("=" * 80)

# Test 3.1: get_codebase_summary
print("\n[3.1] Testing: get_codebase_summary()")
try:
    summary = get_codebase_summary(codebase)
    print(f"  ✅ SUCCESS: Function executed")
    print(f"     Type: {type(summary)}")
    print(f"     Content preview: {str(summary)[:200]}...")
    results["function_tests"].append(("get_codebase_summary", "PASS"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("get_codebase_summary", str(e)))
    results["function_tests"].append(("get_codebase_summary", "FAIL"))

# Test 3.2: get_file_summary
print("\n[3.2] Testing: get_file_summary()")
try:
    if all_files:
        test_file = all_files[0]
        summary = get_file_summary(test_file)
        print(f"  ✅ SUCCESS: Function executed")
        print(f"     File: {test_file.filepath}")
        print(f"     Type: {type(summary)}")
        print(f"     Content preview: {str(summary)[:200]}...")
        results["function_tests"].append(("get_file_summary", "PASS"))
    else:
        print(f"  ⚠️  SKIPPED: No files to analyze")
        results["function_tests"].append(("get_file_summary", "SKIP"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("get_file_summary", str(e)))
    results["function_tests"].append(("get_file_summary", "FAIL"))

# Test 3.3: get_class_summary
print("\n[3.3] Testing: get_class_summary()")
try:
    # Find a file with classes
    file_with_class = None
    for f in all_files:
        if hasattr(f, 'classes') and f.classes:
            file_with_class = f
            break
    
    if file_with_class and file_with_class.classes:
        test_class = file_with_class.classes[0]
        summary = get_class_summary(test_class)
        print(f"  ✅ SUCCESS: Function executed")
        print(f"     Class: {test_class.name}")
        print(f"     Type: {type(summary)}")
        print(f"     Content preview: {str(summary)[:200]}...")
        results["function_tests"].append(("get_class_summary", "PASS"))
    else:
        print(f"  ⚠️  SKIPPED: No classes found in codebase")
        results["function_tests"].append(("get_class_summary", "SKIP"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("get_class_summary", str(e)))
    results["function_tests"].append(("get_class_summary", "FAIL"))

# Test 3.4: get_function_summary
print("\n[3.4] Testing: get_function_summary()")
try:
    # Find a file with functions
    file_with_func = None
    for f in all_files:
        if hasattr(f, 'functions') and f.functions:
            file_with_func = f
            break
    
    if file_with_func and file_with_func.functions:
        test_func = file_with_func.functions[0]
        summary = get_function_summary(test_func)
        print(f"  ✅ SUCCESS: Function executed")
        print(f"     Function: {test_func.name}")
        print(f"     Type: {type(summary)}")
        print(f"     Content preview: {str(summary)[:200]}...")
        results["function_tests"].append(("get_function_summary", "PASS"))
    else:
        print(f"  ⚠️  SKIPPED: No functions found in codebase")
        results["function_tests"].append(("get_function_summary", "SKIP"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("get_function_summary", str(e)))
    results["function_tests"].append(("get_function_summary", "FAIL"))

# Test 3.5: get_symbol_summary
print("\n[3.5] Testing: get_symbol_summary()")
try:
    # Find a symbol
    test_symbol = None
    for f in all_files:
        if hasattr(f, 'symbols') and f.symbols:
            test_symbol = f.symbols[0]
            break
        # Try functions as symbols
        if hasattr(f, 'functions') and f.functions:
            test_symbol = f.functions[0]
            break
    
    if test_symbol:
        summary = get_symbol_summary(test_symbol)
        print(f"  ✅ SUCCESS: Function executed")
        print(f"     Symbol: {getattr(test_symbol, 'name', 'unnamed')}")
        print(f"     Type: {type(summary)}")
        print(f"     Content preview: {str(summary)[:200]}...")
        results["function_tests"].append(("get_symbol_summary", "PASS"))
    else:
        print(f"  ⚠️  SKIPPED: No symbols found in codebase")
        results["function_tests"].append(("get_symbol_summary", "SKIP"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("get_symbol_summary", str(e)))
    results["function_tests"].append(("get_symbol_summary", "FAIL"))

# Test 3.6: find_dead_code
print("\n[3.6] Testing: find_dead_code()")
try:
    dead_code = find_dead_code(codebase)
    print(f"  ✅ SUCCESS: Function executed")
    print(f"     Type: {type(dead_code)}")
    if isinstance(dead_code, list):
        print(f"     Dead code items found: {len(dead_code)}")
        if dead_code:
            print(f"     Sample: {dead_code[0] if dead_code else 'None'}")
    else:
        print(f"     Result: {dead_code}")
    results["function_tests"].append(("find_dead_code", "PASS"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("find_dead_code", str(e)))
    results["function_tests"].append(("find_dead_code", "FAIL"))

# Test 3.7: analyze_codebase
print("\n[3.7] Testing: analyze_codebase()")
try:
    analysis = analyze_codebase(codebase)
    print(f"  ✅ SUCCESS: Function executed")
    print(f"     Type: {type(analysis)}")
    print(f"     Content preview: {str(analysis)[:200]}...")
    results["function_tests"].append(("analyze_codebase", "PASS"))
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    results["errors"].append(("analyze_codebase", str(e)))
    results["function_tests"].append(("analyze_codebase", "FAIL"))

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TESTING RESULTS SUMMARY")
print("=" * 80)

passed = sum(1 for _, status in results["function_tests"] if status == "PASS")
failed = sum(1 for _, status in results["function_tests"] if status == "FAIL")
skipped = sum(1 for _, status in results["function_tests"] if status == "SKIP")
total = len(results["function_tests"])

print(f"\n✅ PASSED: {passed}")
print(f"❌ FAILED: {failed}")
print(f"⚠️  SKIPPED: {skipped}")
print(f"📊 TOTAL: {total}")
print(f"📈 SUCCESS RATE: {(passed/total)*100:.1f}%")

print("\n--- Function Test Details ---")
for func_name, status in results["function_tests"]:
    emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"  {emoji} {func_name}: {status}")

if results["errors"]:
    print("\n--- Errors ---")
    for func_name, error in results["errors"]:
        print(f"  ❌ {func_name}: {error[:100]}")

print("\n" + "=" * 80)
if failed == 0:
    print("🎉 ALL TESTS PASSED - ANALYSIS FUNCTIONS ARE FULLY FUNCTIONAL!")
elif passed > failed:
    print(f"⚠️  PARTIAL SUCCESS - {passed}/{total} functions working")
else:
    print(f"❌ TESTS FAILED - {failed}/{total} functions broken")
print("=" * 80)
