#!/usr/bin/env python3
"""
Test script for the new analysis functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter import Codebase
    from graph_sitter.adapters.analysis import analyze_codebase, format_analysis_results
    
    print("✅ Successfully imported graph_sitter and analysis modules")
    
    # Test the analysis functionality
    print("\n🔍 Testing analysis on current repository...")
    
    # Test direct function call
    result = analyze_codebase(".")
    print(f"📊 Analysis complete! Found {result.total_files} files, {result.total_functions} functions, {result.total_classes} classes")
    
    # Test Codebase.Analysis() method
    print("\n🔍 Testing Codebase.Analysis() method...")
    codebase = Codebase(".")
    result2 = codebase.Analysis()
    print(f"📊 Codebase analysis complete! Found {result2.total_files} files, {result2.total_functions} functions, {result2.total_classes} classes")
    
    # Show some sample results
    print("\n📋 Sample Results:")
    print(format_analysis_results(result)[:1000] + "..." if len(format_analysis_results(result)) > 1000 else format_analysis_results(result))
    
    print("\n✅ All tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This might be expected if dependencies are not installed")
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

