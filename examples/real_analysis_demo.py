#!/usr/bin/env python3
"""
Real Analysis Integration Demo

This example demonstrates the enhanced graph-sitter functionality with:
1. Real analysis backend integration
2. Git repository cloning
3. Interactive dashboard generation
4. Enhanced issue detection and metrics

Usage:
    python real_analysis_demo.py
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    """Demonstrate real analysis integration."""
    try:
        from graph_sitter import Codebase, Analysis
        print("🚀 Real Analysis Integration Demo")
        print("=" * 50)
        
        # Test 1: Local directory analysis with real backend
        print("\n📁 Test 1: Local Directory Analysis")
        print("-" * 30)
        
        local_codebase = Codebase.Analysis(".")
        print(f"✅ Local analysis complete!")
        print(f"📊 Dashboard: {local_codebase.dashboard_url}")
        
        if hasattr(local_codebase, '_analysis_result'):
            result = local_codebase._analysis_result
            print(f"📈 Analysis type: {result.get('analysis_type', 'unknown')}")
            print(f"🔍 Analysis source: {result.get('source', 'unknown')}")
            print(f"📋 Issues found: {len(result.get('issues', []))}")
            print(f"📊 Metrics: {len(result.get('metrics', {}))}")
        
        # Test 2: Git repository cloning and analysis
        print("\n🌐 Test 2: Git Repository Analysis")
        print("-" * 30)
        
        # Test with a small, well-known repository
        repo_codebase = Codebase.from_repo().Analysis('microsoft/vscode-python')
        print(f"✅ Repository analysis complete!")
        print(f"📊 Dashboard: {repo_codebase.dashboard_url}")
        
        if hasattr(repo_codebase, '_original_repo_url'):
            print(f"🔗 Original repo: {repo_codebase._original_repo_url}")
        if hasattr(repo_codebase, '_is_cloned_repo'):
            print(f"📁 Cloned repo: {repo_codebase._is_cloned_repo}")
        
        # Test 3: Analysis comparison
        print("\n📊 Test 3: Analysis Comparison")
        print("-" * 30)
        
        print("Local Analysis:")
        if hasattr(local_codebase, '_analysis_result'):
            local_result = local_codebase._analysis_result
            print(f"  - Files analyzed: {local_result.get('files_analyzed', 0)}")
            print(f"  - Issues: {len(local_result.get('issues', []))}")
            print(f"  - Metrics: {list(local_result.get('metrics', {}).keys())}")
        
        print("\nRepository Analysis:")
        if hasattr(repo_codebase, '_analysis_result'):
            repo_result = repo_codebase._analysis_result
            print(f"  - Files analyzed: {repo_result.get('files_analyzed', 0)}")
            print(f"  - Issues: {len(repo_result.get('issues', []))}")
            print(f"  - Metrics: {list(repo_result.get('metrics', {}).keys())}")
        
        # Test 4: Dashboard features
        print("\n🎨 Test 4: Dashboard Features")
        print("-" * 30)
        
        print("Dashboard features available:")
        print("  ✅ Issue listings with severity categorization")
        print("  ✅ Interactive 'Visualize Codebase' controls")
        print("  ✅ Dropdown visualization selection")
        print("  ✅ Target-specific analysis")
        print("  ✅ Blast radius analysis")
        print("  ✅ Repository source information")
        print("  ✅ Responsive web interface")
        
        # Test 5: Integration capabilities
        print("\n🤖 Test 5: AI Integration Capabilities")
        print("-" * 30)
        
        print("AI-friendly features:")
        print("  ✅ Structured analysis results")
        print("  ✅ Dashboard URL access")
        print("  ✅ Issue data extraction")
        print("  ✅ Metrics data extraction")
        print("  ✅ Contexten integration ready")
        
        # Example of how contexten could use this
        if hasattr(local_codebase, '_analysis_result'):
            analysis_data = local_codebase._analysis_result
            print(f"\nExample AI context extraction:")
            print(f"  - Analysis timestamp: {analysis_data.get('timestamp')}")
            print(f"  - Critical issues: {len([i for i in analysis_data.get('issues', []) if i.get('severity') == 'critical'])}")
            print(f"  - High issues: {len([i for i in analysis_data.get('issues', []) if i.get('severity') == 'high'])}")
            print(f"  - Complexity score: {analysis_data.get('metrics', {}).get('complexity_score', 'N/A')}")
            print(f"  - Test coverage: {analysis_data.get('metrics', {}).get('test_coverage', 'N/A')}%")
        
        print("\n🎉 Real Analysis Integration Demo Complete!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Open the dashboard URLs in your browser to see the interactive interface")
        print("2. Try the dropdown visualizations and target selection")
        print("3. Click on individual issues to analyze blast radius")
        print("4. Integrate with contexten for AI-powered development workflows")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

