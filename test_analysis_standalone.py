#!/usr/bin/env python3
"""
Standalone test script for the analysis functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Test direct import of analysis module
    from graph_sitter.adapters.analysis.analysis import analyze_codebase, format_analysis_results
    
    print("✅ Successfully imported analysis module directly")
    
    # Test the analysis functionality on a small subset
    print("\n🔍 Testing analysis on src/graph_sitter/adapters/analysis...")
    
    result = analyze_codebase("src/graph_sitter/adapters/analysis")
    print(f"📊 Analysis complete!")
    print(f"   Files: {result.total_files}")
    print(f"   Functions: {result.total_functions}")
    print(f"   Classes: {result.total_classes}")
    print(f"   Lines: {result.total_lines}")
    print(f"   Issues: {len(result.issues)}")
    print(f"   Dead code items: {len(result.dead_code_items)}")
    
    # Show formatted results
    print("\n📋 Formatted Results:")
    formatted = format_analysis_results(result)
    print(formatted[:800] + "..." if len(formatted) > 800 else formatted)
    
    print("\n✅ Standalone analysis test passed!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

