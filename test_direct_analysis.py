#!/usr/bin/env python3
"""
Direct test script for the enhanced analysis functionality.
"""

import sys
import os
import importlib.util

def load_analysis_module():
    """Load the analysis module directly."""
    module_path = os.path.join(os.path.dirname(__file__), 'src', 'graph_sitter', 'adapters', 'analysis', 'analysis.py')
    spec = importlib.util.spec_from_file_location("analysis", module_path)
    analysis_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analysis_module)
    return analysis_module

def main():
    """Test the enhanced analysis functionality."""
    print("🔍 Enhanced Code Analysis Test (Direct Import)")
    print("=" * 60)
    
    try:
        # Load the analysis module directly
        analysis = load_analysis_module()
        
        # Test on the analysis directory
        target_path = "src/graph_sitter/adapters/analysis"
        
        print(f"📁 Analyzing: {target_path}")
        print()
        
        # Run analysis
        result = analysis.analyze_codebase(target_path)
        
        # Show key metrics
        print("📊 Enhanced Analysis Results:")
        print(f"  • Total Files: {result.total_files}")
        print(f"  • Total Functions: {result.total_functions}")
        print(f"  • Total Classes: {result.total_classes}")
        print(f"  • Files with Issues: {len(result.files_with_issues)}")
        print(f"  • Top-Level Functions: {len(result.top_level_functions)}")
        print(f"  • Top-Level Classes: {len(result.top_level_classes)}")
        print(f"  • Inheritance Hierarchy: {len(result.inheritance_hierarchy)}")
        print()
        
        # Show files with issues (numbered list as requested)
        if result.files_with_issues:
            print("📁 Files with Issues (Numbered List):")
            for i, file_info in enumerate(result.files_with_issues, 1):
                print(f"  {i}. {file_info.file_path}")
                print(f"     Issues: {file_info.issue_count}")
                if file_info.top_level_functions:
                    funcs = ', '.join(file_info.top_level_functions[:3])
                    if len(file_info.top_level_functions) > 3:
                        funcs += f" ... and {len(file_info.top_level_functions) - 3} more"
                    print(f"     Top-Level Functions: {funcs}")
                if file_info.top_level_classes:
                    classes = ', '.join(file_info.top_level_classes[:3])
                    if len(file_info.top_level_classes) > 3:
                        classes += f" ... and {len(file_info.top_level_classes) - 3} more"
                    print(f"     Top-Level Classes: {classes}")
                print()
        
        # Show top-level symbols (as requested)
        if result.top_level_functions:
            print("🔝 Top-Level Functions:")
            for i, func in enumerate(result.top_level_functions[:10], 1):
                print(f"  {i}. {func}")
            if len(result.top_level_functions) > 10:
                print(f"  ... and {len(result.top_level_functions) - 10} more functions")
            print()
        
        if result.top_level_classes:
            print("🔝 Top-Level Classes (Top Inheritance):")
            for i, cls in enumerate(result.top_level_classes[:10], 1):
                print(f"  {i}. {cls}")
            if len(result.top_level_classes) > 10:
                print(f"  ... and {len(result.top_level_classes) - 10} more classes")
            print()
        
        # Show inheritance hierarchy
        if result.inheritance_hierarchy:
            print("🏗️  Inheritance Hierarchy:")
            sorted_hierarchy = sorted(result.inheritance_hierarchy, key=lambda x: x.inheritance_depth)
            for i, info in enumerate(sorted_hierarchy[:5], 1):
                depth_indicator = "  " * info.inheritance_depth
                print(f"  {i}. {depth_indicator}{info.class_name}")
                print(f"     File: {info.file_path}:{info.line_start}")
                if info.parent_classes:
                    print(f"     Parents: {', '.join(info.parent_classes)}")
                print(f"     Depth: {info.inheritance_depth}")
                print()
        
        # Show sample issues
        if result.issues:
            print(f"⚠️  Sample Issues ({len(result.issues)} total):")
            for i, issue in enumerate(result.issues[:3], 1):
                print(f"  {i}. {issue.message}")
                print(f"     Location: {issue.file_path}:{issue.line_start}")
                print(f"     Severity: {issue.severity}")
                if issue.suggestion:
                    print(f"     Suggestion: {issue.suggestion}")
                print()
        
        print("✅ Enhanced analysis test completed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("  ✓ Numbered list of files with issues")
        print("  ✓ Top-level functions and classes identification")
        print("  ✓ Inheritance hierarchy analysis")
        print("  ✓ Comprehensive issue detection")
        print("  ✓ Enhanced output formatting")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

