#!/usr/bin/env python3
"""
Test script for the enhanced analysis functionality.

This script demonstrates the enhanced code analysis capabilities
following the patterns from https://graph-sitter.com/tutorials/at-a-glance
"""

import sys
import os
sys.path.insert(0, 'src')

from graph_sitter.adapters.analysis.analysis import analyze_codebase, format_analysis_results

def test_enhanced_analysis():
    """Test the enhanced analysis functionality."""
    print("🔍 Testing Enhanced Code Analysis")
    print("=" * 50)
    
    # Test on the analysis module itself
    target_path = "src/graph_sitter/adapters/analysis"
    
    print(f"📁 Analyzing: {target_path}")
    print()
    
    try:
        # Run analysis
        result = analyze_codebase(target_path)
        
        # Display results
        formatted_output = format_analysis_results(result)
        print(formatted_output)
        
        # Show JSON output sample
        print("\n" + "=" * 50)
        print("📊 JSON Output Sample:")
        print("=" * 50)
        
        json_data = result.to_dict()
        print(f"Summary: {json_data['summary']}")
        print(f"Top-level functions: {len(json_data['top_level_symbols']['functions'])}")
        print(f"Top-level classes: {len(json_data['top_level_symbols']['classes'])}")
        print(f"Files with issues: {len(json_data['files_with_issues'])}")
        print(f"Inheritance hierarchy: {len(json_data['inheritance_hierarchy'])}")
        
        print("\n✅ Enhanced analysis test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_enhanced_analysis()
    sys.exit(0 if success else 1)

