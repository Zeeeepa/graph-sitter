#!/usr/bin/env python3
"""
Simple usage example matching the user's requested API.

This demonstrates the exact usage pattern requested:
- from graph_sitter import Codebase, Analysis
- Codebase.from_repo.Analysis('fastapi/fastapi')
- Codebase.Analysis("path/to/git/repo")
"""

from graph_sitter import Codebase
import os

def main():
    print("🚀 Graph-Sitter Simple Analysis Usage")
    print("=" * 40)
    
    # Example 1: Analyze a local repository
    print("\n📁 Local Repository Analysis")
    
    # Create a simple test repository
    test_repo = "test_repo"
    os.makedirs(test_repo, exist_ok=True)
    
    with open(f"{test_repo}/main.py", "w") as f:
        f.write('''
def hello_world():
    """A simple greeting function."""
    print("Hello, World!")
    return "success"

class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
''')
    
    # Usage as requested: Codebase.Analysis("path/to/git/repo")
    print(f"Running: Codebase('{test_repo}').Analysis()")
    codebase = Codebase(test_repo)
    result = codebase.Analysis()
    
    print("✅ Analysis completed!")
    print(f"📊 Health Score: {result.enhanced_analysis.health_score:.3f}")
    print(f"📁 Results saved to: analysis_output/")
    
    # Example 2: Remote repository (commented out - requires network)
    print("\n🌐 Remote Repository Analysis (Example)")
    print("# To analyze a remote repository like FastAPI:")
    print("# codebase = Codebase.from_repo('fastapi/fastapi')")
    print("# result = codebase.Analysis()")
    print("#")
    print("# This would:")
    print("# 1. Clone the fastapi/fastapi repository")
    print("# 2. Parse all Python files")
    print("# 3. Run comprehensive analysis")
    print("# 4. Generate HTML reports with issues and visualizations")
    print("# 5. Provide URL for interactive dashboard")
    
    # Show what the analysis provides
    print("\n📋 Analysis Features:")
    print("✓ Full-context analysis of all functions and classes")
    print("✓ Issue detection with severity levels")
    print("✓ Dependency analysis and circular dependency detection")
    print("✓ Dead code identification")
    print("✓ Complexity metrics and risk assessment")
    print("✓ Actionable recommendations")
    print("✓ JSON exports for integration")
    print("✓ Health scoring for quality gates")
    
    # Show analysis results structure
    if hasattr(result, 'export_paths'):
        print(f"\n📄 Generated Reports:")
        for name, path in result.export_paths.items():
            print(f"  • {name.replace('_', ' ').title()}: {path}")

if __name__ == "__main__":
    main()

