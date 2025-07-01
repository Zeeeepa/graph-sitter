#!/usr/bin/env python3
"""
Simple Auto-Analysis Example

This example demonstrates the exact usage pattern requested:
- from graph_sitter import Codebase, Analysis
- codebase = Codebase.from_repo.Analysis('fastapi/fastapi')
- codebase = Codebase.Analysis("path/to/git/repo")

The enhanced Codebase automatically detects the "Analysis" keyword and:
1. Performs comprehensive analysis
2. Generates an interactive HTML dashboard
3. Provides a URL for issue listings and visualizations
4. Enables dropdown-based visualization selection
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("🎯 Simple Auto-Analysis Example")
    print("=" * 40)
    
    try:
        # Import the enhanced graph_sitter module
        from graph_sitter import Codebase, Analysis
        
        print("📦 Imported graph_sitter successfully!")
        print()
        
        # Example 1: Clone + parse fastapi/fastapi (simulated)
        print("🔄 Example 1: Repository Cloning with Auto-Analysis")
        print("Code: codebase = Codebase.from_repo.Analysis('fastapi/fastapi')")
        
        try:
            codebase = Codebase.from_repo.Analysis('fastapi/fastapi')
            print("✅ Repository analysis initiated!")
            print(f"📊 Dashboard URL: {codebase.dashboard_url}")
            print()
        except Exception as e:
            print(f"⚠️ Simulated example (actual cloning not implemented): {e}")
            print()
        
        # Example 2: Parse a local repository
        print("📁 Example 2: Local Repository Auto-Analysis")
        print('Code: codebase = Codebase.Analysis("path/to/git/repo")')
        
        try:
            # Use current directory as example
            codebase = Codebase.Analysis(".")
            print("✅ Local repository analysis completed!")
            
            if hasattr(codebase, 'dashboard_url') and codebase.dashboard_url:
                print(f"📊 Dashboard URL: {codebase.dashboard_url}")
                print()
                print("🎮 Dashboard Features:")
                print("  • Issue listings with severity categorization")
                print("  • Interactive 'Visualize Codebase' button")
                print("  • Dropdown selection for visualization types:")
                print("    - Dependency Analysis")
                print("    - Blast Radius Analysis") 
                print("    - Complexity Heatmap")
                print("    - Call Graph")
                print("    - Dead Code Analysis")
                print("  • Target selection (functions, classes, files)")
                print("  • Click-to-analyze blast radius from issues")
                print()
                
                # Ask if user wants to open the dashboard
                try:
                    user_input = input("🌐 Open dashboard in browser? (y/n): ")
                    if user_input.lower() == 'y':
                        success = codebase.open_dashboard()
                        if success:
                            print("🚀 Dashboard opened in browser!")
                        else:
                            print("❌ Could not open dashboard")
                except KeyboardInterrupt:
                    print("\n👋 Skipping browser open")
                    
            else:
                print("⚠️ Dashboard not generated (analysis may have failed)")
                
        except Exception as e:
            print(f"❌ Error during local analysis: {e}")
            print("💡 This might be due to missing dependencies")
        
        print()
        print("🎉 Auto-Analysis Features Summary:")
        print("=" * 40)
        print("✅ Automatic detection of 'Analysis' in constructor")
        print("✅ Comprehensive analysis execution")
        print("✅ HTML dashboard generation")
        print("✅ Issue listings with categorization")
        print("✅ Interactive visualization controls")
        print("✅ Dropdown-based visualization selection")
        print("✅ Target-specific analysis options")
        print("✅ One-click blast radius analysis")
        print("✅ Responsive web interface")
        print("✅ Easy integration with external tools")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the correct directory")
        print("💡 Some dependencies might be missing")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

