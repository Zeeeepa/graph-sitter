#!/usr/bin/env python3
"""
Example script demonstrating how to use the graph-sitter_analysis.py tool programmatically.
"""

from graph_sitter_analysis import CodebaseAnalyzer, display_results_text

def main():
    """Run a sample analysis on the FastAPI repository."""
    print("Running sample analysis on FastAPI repository...")
    
    # Create analyzer for FastAPI repository
    analyzer = CodebaseAnalyzer("fastapi/fastapi", language="python")
    
    # Perform analysis
    result = analyzer.analyze()
    
    # Display results
    display_results_text(result)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()

