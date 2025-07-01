#!/usr/bin/env python3
"""
Auto-Analysis Demo - Graph-Sitter Enhanced Codebase

This example demonstrates the new auto-analysis functionality where
the Codebase class automatically detects analysis intent and generates
interactive HTML dashboards with issue listings and visualizations.

Features demonstrated:
- Auto-detection of analysis intent
- Automatic comprehensive analysis execution
- Interactive HTML dashboard generation
- Issue listings with categorization
- Dropdown-based visualization selection

Usage:
    python examples/auto_analysis_demo.py
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def demo_local_repository_analysis():
    """Demonstrate auto-analysis with a local repository."""
    print("🎯 Demo 1: Local Repository Auto-Analysis")
    print("=" * 50)
    
    try:
        from graph_sitter import Codebase, Analysis
        
        # This will automatically trigger comprehensive analysis
        # because "Analysis" is detected in the constructor call
        print("📁 Analyzing local repository with auto-detection...")
        codebase = Codebase.Analysis(".")
        
        # Check if analysis was performed
        if hasattr(codebase, 'analysis_result') and codebase.analysis_result:
            print("✅ Auto-analysis completed successfully!")
            print(f"📊 Dashboard available at: {codebase.dashboard_url}")
            
            # Optionally open the dashboard
            user_input = input("🌐 Open dashboard in browser? (y/n): ")
            if user_input.lower() == 'y':
                codebase.open_dashboard()
        else:
            print("⚠️ Auto-analysis was not triggered or failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 This might be due to missing dependencies or analysis failures")

def demo_repo_cloning_analysis():
    """Demonstrate auto-analysis with repository cloning."""
    print("\n🎯 Demo 2: Repository Cloning Auto-Analysis")
    print("=" * 50)
    
    try:
        from graph_sitter import Codebase, Analysis
        
        # This syntax automatically triggers analysis
        print("🔄 Cloning and analyzing repository...")
        print("📝 Note: This is a simulated demo - actual cloning would happen here")
        
        # Simulate the desired API
        codebase = Codebase.from_repo.Analysis('fastapi/fastapi')
        
        print("✅ Repository cloned and analyzed!")
        print(f"📊 Dashboard available at: {codebase.dashboard_url}")
        
        # Show analysis capabilities
        if hasattr(codebase, 'analysis_result'):
            print("\n📈 Analysis Features Available:")
            print("  • Issue detection and categorization")
            print("  • Dependency analysis")
            print("  • Blast radius visualization")
            print("  • Complexity metrics")
            print("  • Dead code detection")
            print("  • Interactive visualizations")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Repository cloning simulation - actual implementation would clone real repos")

def demo_manual_analysis_comparison():
    """Demonstrate the difference between manual and auto analysis."""
    print("\n🎯 Demo 3: Manual vs Auto Analysis Comparison")
    print("=" * 50)
    
    try:
        from graph_sitter import Codebase, Analysis
        
        print("📊 Method 1: Manual Analysis (Traditional)")
        print("-" * 30)
        
        # Traditional manual approach
        codebase_manual = Codebase(".")
        print("  1. Create codebase instance")
        
        # Manual analysis would be called explicitly
        print("  2. Call Analysis.analyze_comprehensive() manually")
        print("  3. Generate dashboard manually")
        print("  4. Multiple steps required")
        
        print("\n🚀 Method 2: Auto Analysis (Enhanced)")
        print("-" * 30)
        
        # Auto-analysis approach
        codebase_auto = Codebase.Analysis(".")
        print("  1. Single call with auto-detection")
        print("  2. Analysis runs automatically")
        print("  3. Dashboard generated automatically")
        print("  4. Ready to use immediately!")
        
        if hasattr(codebase_auto, 'dashboard_url'):
            print(f"\n✨ Auto-analysis dashboard: {codebase_auto.dashboard_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def demo_dashboard_features():
    """Demonstrate the dashboard features and capabilities."""
    print("\n🎯 Demo 4: Dashboard Features Overview")
    print("=" * 50)
    
    print("📋 Dashboard Sections:")
    print("  1. Issues & Problems Overview")
    print("     • Critical, High, Medium, Low, Info categorization")
    print("     • Detailed issue listings with file locations")
    print("     • Direct links to blast radius analysis")
    print("")
    print("  2. Interactive Visualizations")
    print("     • Dependency Analysis - module relationships")
    print("     • Blast Radius Analysis - change impact visualization")
    print("     • Complexity Heatmap - code complexity visualization")
    print("     • Call Graph - function call relationships")
    print("     • Dead Code Analysis - unused code detection")
    print("")
    print("  3. Codebase Metrics")
    print("     • Complexity Score - average cyclomatic complexity")
    print("     • Test Coverage - percentage of code covered by tests")
    print("     • Technical Debt - estimated time to fix issues")
    print("     • Maintainability - overall maintainability grade")
    print("     • Dependencies - external dependency count")
    print("     • Dead Code - percentage of unused code")
    print("")
    print("🎮 Interactive Features:")
    print("  • Dropdown-based visualization selection")
    print("  • Target-specific analysis (functions, classes, files)")
    print("  • Click-to-analyze blast radius from issues")
    print("  • Responsive design for various screen sizes")
    print("  • Real-time visualization updates")

def demo_integration_examples():
    """Show how external modules can integrate with the enhanced API."""
    print("\n🎯 Demo 5: Integration Examples")
    print("=" * 50)
    
    print("🔧 Contexten Integration Example:")
    print("""
# contexten/extensions/graph_sitter_integration.py
from graph_sitter import Codebase, Analysis

class GraphSitterIntegration:
    def __init__(self, project_path):
        # Auto-analysis enabled
        self.codebase = Codebase.Analysis(project_path)
    
    def get_ai_context(self):
        \"\"\"Get analysis data for AI context.\"\"\"
        if self.codebase.analysis_result:
            return {
                'issues': self.codebase.analysis_result.issues,
                'metrics': self.codebase.analysis_result.metrics,
                'dashboard_url': self.codebase.dashboard_url
            }
        return {}
    
    def open_analysis_dashboard(self):
        \"\"\"Open the interactive dashboard.\"\"\"
        return self.codebase.open_dashboard()
    """)
    
    print("\n🤖 AI Agent Integration Example:")
    print("""
# ai_agent_integration.py
from graph_sitter import Codebase, Analysis

def analyze_codebase_for_ai(project_path):
    \"\"\"Analyze codebase and return AI-friendly data.\"\"\"
    
    # Single call triggers comprehensive analysis
    codebase = Codebase.Analysis(project_path)
    
    # Extract key information for AI processing
    analysis_summary = {
        'health_score': calculate_health_score(codebase),
        'critical_issues': get_critical_issues(codebase),
        'improvement_suggestions': get_suggestions(codebase),
        'dashboard_url': codebase.dashboard_url
    }
    
    return analysis_summary
    """)

def main():
    """Run all demos."""
    print("🚀 Graph-Sitter Enhanced Codebase Demo")
    print("=" * 60)
    print("This demo showcases the new auto-analysis functionality")
    print("that automatically detects analysis intent and generates")
    print("interactive HTML dashboards with comprehensive insights.")
    print("=" * 60)
    
    # Run all demos
    demo_local_repository_analysis()
    demo_repo_cloning_analysis()
    demo_manual_analysis_comparison()
    demo_dashboard_features()
    demo_integration_examples()
    
    print("\n🎉 Demo Complete!")
    print("=" * 50)
    print("Key Benefits:")
    print("✅ Simplified API - single call triggers comprehensive analysis")
    print("✅ Auto-detection - no need to explicitly call analysis functions")
    print("✅ Interactive dashboards - rich HTML visualizations")
    print("✅ Issue-focused - immediate visibility into problems")
    print("✅ External integration - easy consumption by other tools")
    print("\nNext Steps:")
    print("🔧 Integrate with contexten module")
    print("🎨 Customize dashboard themes and layouts")
    print("📊 Add more visualization types")
    print("🔍 Enhance analysis algorithms")

if __name__ == "__main__":
    main()

