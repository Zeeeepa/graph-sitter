#!/usr/bin/env python3
"""
Example demonstrating the refactored Analysis feature in graph-sitter.

This example shows how to use the existing analysis infrastructure
that has been properly moved and integrated.
"""

from graph_sitter import Codebase

def main():
    # Example 1: Analyze a local repository
    print("=== Analyzing Local Repository ===")
    codebase = Codebase.from_files("path/to/local/repo")
    analysis_result = codebase.Analysis(output_dir="analysis_output")
    
    print(f"Analysis completed for codebase: {analysis_result.codebase_id}")
    print(f"Health Score: {analysis_result.health_score}")
    print(f"Issues Found: {len(analysis_result.enhanced_analysis.issues)}")
    
    # Example 2: Direct analysis from path (convenience method)
    print("\n=== Direct Analysis from Path ===")
    analysis_result = Codebase.AnalysisFromPath("path/to/repo", output_dir="analysis_output")
    
    # Access different analysis components
    print(f"Metrics: {analysis_result.metrics_summary}")
    print(f"Dead Code Issues: {len(analysis_result.dead_code_analysis.get('issues', []))}")
    print(f"Dependency Issues: {len(analysis_result.dependency_analysis.get('issues', []))}")
    
    # Access interactive report for dashboard
    if analysis_result.interactive_report:
        print(f"Interactive report available at: {analysis_result.interactive_report.html_path}")
    
    print("\n=== Analysis Complete ===")
    print("Check the analysis_output directory for detailed reports and visualizations.")

if __name__ == "__main__":
    main()

