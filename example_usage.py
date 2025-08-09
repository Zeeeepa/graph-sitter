#!/usr/bin/env python3
"""
Example usage of the Comprehensive Codebase Analyzer
"""

from comprehensive_codebase_analyzer import ComprehensiveCodebaseAnalyzer

def analyze_current_repo():
    """Analyze the current graph-sitter repository."""
    print("🔍 Analyzing current graph-sitter repository...")
    
    # Create analyzer for current directory
    analyzer = ComprehensiveCodebaseAnalyzer(".")
    
    # Run comprehensive analysis
    results = analyzer.run_comprehensive_analysis()
    
    # Save results
    analyzer.save_results("graph_sitter_analysis")
    
    print("\n✅ Analysis complete! Check graph_sitter_analysis/ directory for results.")
    return results

def analyze_remote_repo():
    """Example of analyzing a remote repository."""
    print("🔍 Analyzing remote FastAPI repository...")
    
    # Create analyzer for remote repo
    analyzer = ComprehensiveCodebaseAnalyzer("https://github.com/tiangolo/fastapi")
    
    # Run comprehensive analysis
    results = analyzer.run_comprehensive_analysis()
    
    # Save results
    analyzer.save_results("fastapi_analysis")
    
    print("\n✅ Analysis complete! Check fastapi_analysis/ directory for results.")
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "remote":
        # Analyze remote repository
        analyze_remote_repo()
    else:
        # Analyze current repository
        analyze_current_repo()

