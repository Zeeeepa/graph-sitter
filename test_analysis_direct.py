#!/usr/bin/env python3
"""
Direct test script for the analysis functionality without main graph_sitter imports.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Import directly from the analysis module file
    sys.path.insert(0, str(Path(__file__).parent / "src" / "graph_sitter" / "adapters" / "analysis"))
    from analysis import analyze_codebase, format_analysis_results, CodeAnalyzer
    
    print("✅ Successfully imported analysis module directly")
    
    # Test the analysis functionality on the analysis folder itself
    print("\n🔍 Testing analysis on src/graph_sitter/adapters/analysis...")
    
    result = analyze_codebase("src/graph_sitter/adapters/analysis")
    print(f"📊 Analysis complete!")
    print(f"   Files: {result.total_files}")
    print(f"   Functions: {result.total_functions}")
    print(f"   Classes: {result.total_classes}")
    print(f"   Lines: {result.total_lines}")
    print(f"   Issues: {len(result.issues)}")
    print(f"   Dead code items: {len(result.dead_code_items)}")
    
    # Test on a simple Python file
    print("\n🔍 Testing analysis on test file itself...")
    result2 = analyze_codebase(__file__)
    print(f"📊 Self-analysis complete!")
    print(f"   Files: {result2.total_files}")
    print(f"   Functions: {result2.total_functions}")
    print(f"   Classes: {result2.total_classes}")
    
    # Show some sample results
    print("\n📋 Sample Results (first 500 chars):")
    formatted = format_analysis_results(result)
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
    
    print("\n✅ Direct analysis test passed!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

