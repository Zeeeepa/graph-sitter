#!/usr/bin/env python3
"""
Simple test script for the enhanced analysis functionality.
"""

import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import directly from the analysis module
from graph_sitter.adapters.analysis.analysis import analyze_codebase, format_analysis_results

def main():
    """Test the enhanced analysis functionality."""
    print("🔍 Enhanced Code Analysis Test")
    print("=" * 50)
    
    # Test on a simple directory
    target_path = "src/graph_sitter/adapters/analysis"
    
    print(f"📁 Analyzing: {target_path}")
    print()
    
    try:
        # Run analysis
        result = analyze_codebase(target_path)
        
        # Show key metrics
        print("📊 Key Metrics:")
        print(f"  • Total Files: {result.total_files}")
        print(f"  • Total Functions: {result.total_functions}")
        print(f"  • Total Classes: {result.total_classes}")
        print(f"  • Files with Issues: {len(result.files_with_issues)}")
        print(f"  • Top-Level Functions: {len(result.top_level_functions)}")
        print(f"  • Top-Level Classes: {len(result.top_level_classes)}")
        print(f"  • Inheritance Hierarchy: {len(result.inheritance_hierarchy)}")
        print()
        
        # Show files with issues (numbered list)
        if result.files_with_issues:
            print("📁 Files with Issues:")
            for i, file_info in enumerate(result.files_with_issues, 1):
                print(f"  {i}. {file_info.file_path}")
                print(f"     Issues: {file_info.issue_count}")
                if file_info.top_level_functions:
                    print(f"     Top-Level Functions: {', '.join(file_info.top_level_functions[:3])}")
                if file_info.top_level_classes:
                    print(f"     Top-Level Classes: {', '.join(file_info.top_level_classes[:3])}")
                print()
        
        # Show top-level symbols
        if result.top_level_functions:
            print("🔝 Top-Level Functions:")
            for i, func in enumerate(result.top_level_functions[:5], 1):
                print(f"  {i}. {func}")
            print()
        
        if result.top_level_classes:
            print("🔝 Top-Level Classes:")
            for i, cls in enumerate(result.top_level_classes[:5], 1):
                print(f"  {i}. {cls}")
            print()
        
        print("✅ Enhanced analysis test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

